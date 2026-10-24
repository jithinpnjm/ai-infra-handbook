#!/usr/bin/env python3
"""Slurm-under-BCM rules from BCM 11 Administrator Manual chapter 7, as small testable pieces. Not BCM, not Slurm.

Each part names the manual section it follows. Where the manual is silent the code says so.
"""
import re
from bcm_model import Cluster, BcmError

class WlmError(ValueError):
    pass

# ---- 7.2 forcing jobs through the WLM ----------------------------------------------------------------------------
def user_may_ssh_to_node(setting, user, node_has_user_job, in_pam_allow=False):
    """usernodelogin (category level only): always (default) | never | onlywhenjob. root is always allowed. onlywhenjob works through
    pam_bright.so in /etc/pam.d/sshd; users listed in etc/security/pam_bright.d/pam_allow.conf (or pam_allow_group.conf) in the image are allowed anyway.
    An ssh session that is already open is not ended when the job ends."""
    if setting not in ("always", "never", "onlywhenjob"):
        raise WlmError("usernodelogin is always, never or onlywhenjob")
    if user == "root" or setting == "always":
        return True
    if setting == "never":
        return False
    return node_has_user_job or in_pam_allow

# ---- 7.2.4 high availability ---------------------------------------------------------------------------------------------
def default_start_policy(ha_cluster):
    """slurmctldstartpolicy: TAKEOVER is the default on an HA cluster, ALWAYS on a non-HA cluster; ACTIVEONLY is for setups where /cm/shared is
    not mounted on both heads at once."""
    return "TAKEOVER" if ha_cluster else "ALWAYS"

def server_nodes_ok(nodes, heads):
    """The WLM servers can both be on head nodes or both on regular nodes; one head and one regular node is not possible."""
    kinds = {("head" if n in heads else "compute") for n in nodes}
    if len(nodes) == 2 and len(kinds) == 2:
        raise WlmError("a mixed setup (one head node and one regular node) is not possible for WLM servers in HA")
    return True

def compute_takeover_configured(both_in_failover_group):
    """With the Slurm server role on two compute nodes the TAKEOVER policy is configured automatically only when both nodes are in a failover group."""
    return bool(both_in_failover_group)

TAKEOVER_SCRIPT = "/cm/local/apps/cmd/scripts/slurm.takeover.sh"

def active_head_is_slurm_primary_independent():
    """The active cluster head and the active WLM server are not necessarily the same: a passive head can host the active slurmctld."""
    return True

# ---- 7.3 cm-wlm-setup -------------------------------------------------------------------------------------------------------
CM_WLM_DEFAULTS = {"server_nodes": "HEAD", "server_primary": "HEAD", "overlay_priority": 500, "client_categories": "default", "submit_categories": "default",
                   "gpu_overlay_priority": 450, "head_submit_overlay_priority": 600, "min_reboot_timeout": 300}

def wlm_overlay_names(wlm):
    return {"server": f"{wlm}-server", "client": f"{wlm}-client", "submit": f"{wlm}-submit", "accounting": f"{wlm}-accounting", "gpu client": f"{wlm}-client-gpu"}

def cm_wlm_setup_check(wlm, archives_location=None, nvidia_gpus=None, min_reboot_timeout=300, new_object_from_cmsh=False):
    """A WLM object cannot be created or cloned in cmsh or Base View (too many pitfalls): only cm-wlm-setup, the Base View WLM wizard, or the
    initial installation. LSF needs --archives-location. --nvidia-gpus is TYPE:COUNT. --min-reboot-timeout is at least 300."""
    problems = []
    if new_object_from_cmsh:
        problems.append("a WLM object cannot be created or cloned from cmsh or Base View: use cm-wlm-setup or the WLM wizard")
    if wlm not in ("slurm", "lsf"):
        problems.append("--wlm is slurm or lsf")
    if wlm == "lsf" and not archives_location:
        problems.append("LSF needs --archives-location (mandatory)")
    if nvidia_gpus and not re.fullmatch(r"[A-Za-z0-9_-]+:\d+", nvidia_gpus):
        problems.append("--nvidia-gpus looks like A100:4 (type:count)")
    if min_reboot_timeout < 300:
        problems.append("--min-reboot-timeout cannot be below 300 seconds")
    return problems

def accounting_plan(nodes, heads, mysql_overlay_exists=True, mysql_on_several_nodes=False):
    """Slurm accounting (slurmdbd): one or two accounting nodes; all heads or all compute nodes, a mixed choice is rejected. Two nodes -> slurmdbd HA.
    Heads offer 'use accounting node'; compute nodes offer 'select cluster node' (a BCM MySQL overlay is needed; else run cm-mysql-setup) ;
    'external node' is always possible and then the administrator installs the DBMS."""
    if not 1 <= len(nodes) <= 2:
        raise WlmError("one or two accounting nodes")
    kinds = {("head" if n in heads else "compute") for n in nodes}
    if len(kinds) > 1:
        raise WlmError("head nodes and compute nodes cannot be mixed for the accounting nodes")
    kind = kinds.pop()
    plan = {"ha": len(nodes) == 2, "primary": nodes[0], "backup": nodes[1] if len(nodes) == 2 else None,
            "database_options": ["use accounting node", "external node"] if kind == "head" else ["select cluster node", "external node"], "steps": []}
    if kind == "compute":
        if not mysql_overlay_exists:
            plan["steps"].append("no MySQL configuration overlay found: run cm-mysql-setup first")
        if mysql_on_several_nodes:
            plan["steps"].append("mysql-router is installed automatically on all accounting nodes")
    return plan

# ---- GPU roles and overlay priority -------------------------------------------------------------------------------------------
def wlm_cluster(gpu_nodes=("gpu001", "gpu002"), cpu_nodes=("node001", "node002")):
    """Builds the overlays cm-wlm-setup makes: server/submit/accounting at 500, headnode submit at 600, client at 500 for category default, GPU client at 450."""
    c = Cluster()
    c.add_category("gpu")
    for n in cpu_nodes:
        c.add_node(n, "default")
    for n in gpu_nodes:
        c.add_node(n, "gpu")
    c.add_overlay("slurm-client", 500, roles={"slurmclient": {"gpu": False}}, categories={"default"})
    c.add_overlay("slurm-client-gpu", 450, roles={"slurmclient": {"gpu": True}}, categories={"gpu"})
    return c

GPU_AUTODETECT = {"bcm", "none", "nrt", "nvml", "off", "oneapi", "rsmi"}

def gres_autodetect_line(value):
    """GPU auto detect: bcm = values BCM puts in for vendor and GPU count; none = no AutoDetect line in gres.conf; nvml/rsmi/oneapi/nrt/off = that value
    in gres.conf (nrt detects AWS Trainium/Inferentia)."""
    if value not in GPU_AUTODETECT:
        raise WlmError(f"GPU auto detect is one of {sorted(GPU_AUTODETECT)}")
    if value == "none":
        return None
    if value == "bcm":
        return "(BCM writes vendor and GPU count)"
    return f"AutoDetect={value}"

# ---- nodesets, features, queues -----------------------------------------------------------------------------------------------
def slurm_conf_lines(client_nodes, nodesets=None, nodeset_features=None, base_features=None):
    """Manual 7.5 example: nodesets 'ns1' on node001 -> NodeSet=ns1 Nodes=node001. Nodeset features are added to NodeName Features and also give a NodeSet=<f> Feature=<f>."""
    lines = []
    feats = list(base_features or []) + list(nodeset_features or [])
    for n in client_nodes:
        lines.append(f"NodeName={n}" + (f" Features={','.join(feats)}" if feats else ""))
    if nodesets:
        lines.append(f"NodeSet={nodesets} Nodes={','.join(client_nodes)}")
    for f in (nodeset_features or []):
        lines.append(f"NodeSet={f} Feature={f}")
    return lines

def queue_nodes(nodesets=(), nodeset_members=None, overlays=(), categories=(), nodegroups=(), compute_nodes=(), resolve=None):
    """A queue (Slurm partition) gets nodes from: nodesets, overlays, categories, nodegroups, compute nodes. If the queue's nodesets parameter is set,
    BCM does NOT add the nodes of the compute nodes parameter, only the nodesets (PartitionName=... Nodes=<nodesets>)."""
    if nodesets:
        return "Nodes=" + ",".join(nodesets)
    members = set(compute_nodes)
    resolve = resolve or {}
    for kind, names in (("overlay", overlays), ("category", categories), ("nodegroup", nodegroups)):
        for n in names:
            members |= set(resolve.get((kind, n), []))
    return sorted(members)

# ---- Pyxis and Enroot -----------------------------------------------------------------------------------------------------------
PYXIS_OS = "RHEL8-based systems and Ubuntu 20 and beyond"
ENROOT_CONF_DEFAULTS = {"ENROOT_RUNTIME_PATH": "/run/enroot/runtime/$(id -u)", "ENROOT_CACHE_PATH": "/run/enroot/cache/$(id -u)",
                        "ENROOT_DATA_PATH": "/run/enroot/data/$(id -u)", "ENROOT_SQUASH_OPTIONS": "-noI -noD -noF -noX -no-duplicates", "ENROOT_MOUNT_HOME": "yes"}

def pyxis_cache_plan(shared_raw_images, cache_dir_exists=True, group_restricted=False):
    """Sharing raw images: cache dir defaults to ${XDG_CACHE_HOME}/enroot; if it must be created it gets mode 00777 (all users share); the Enroot prolog stops
    creating a per-UID subdirectory. Unshared: prolog makes a UID subdirectory and the epilog cleans it. Restrict sharing afterwards, e.g. mode 00770
    and a group of Pyxis users."""
    if not shared_raw_images:
        return {"uid_subdir": True, "mode": None, "note": "prolog creates /<uid>, epilog cleans it"}
    mode = "00770" if group_restricted else ("existing" if cache_dir_exists else "00777")
    return {"uid_subdir": False, "mode": mode, "note": "shared cache: neither prolog nor epilog touches it"}

def srun_container_options():
    return ["--container-image", "--container-mounts", "--container-workdir", "--container-name", "--container-save", "--container-mount-home",
            "--no-container-mount-home", "--container-remap-root", "--no-container-remap-root", "--container-entrypoint", "--no-container-entrypoint",
            "--container-writable", "--container-readonly"]

# ---- upgrade ---------------------------------------------------------------------------------------------------------------------------
SLURM_MAJORS = ["24.05", "24.11", "25.05", "25.11"]

def upgrade_plan(frm, to, uses_pyxis=False, images=("default-image",)):
    """7.5: drain and wait for jobs; stop slurmctld and slurmdbd; remove the old packages from the head node AND every image that uses them (only one
    Slurm version at a time); install the new ones in both places; set the new version in the wlm cluster; reinstall Pyxis if used.
    Upgrade one major version at a time."""
    if frm not in SLURM_MAJORS or to not in SLURM_MAJORS:
        raise WlmError("versions outside the list modelled here")
    gap = SLURM_MAJORS.index(to) - SLURM_MAJORS.index(frm)
    if gap <= 0:
        raise WlmError("not an upgrade")
    steps = ["drain nodes and wait for running jobs to finish", "stop slurmctld and slurmdbd", f"remove slurm{frm}* on the head node"]
    steps += [f"remove slurm{frm}* in image {i} (cm-chroot-sw-img)" for i in images]
    steps += [f"install slurm{to} packages on the head node"] + [f"install slurm{to}-slurmd and friends in image {i}" for i in images]
    steps += [f"set the Slurm version to {to} in the wlm cluster (cmsh wlm use slurm)", "start services, undrain"]
    if uses_pyxis:
        steps.append("reinstall Pyxis with cm-wlm-setup (it is compiled against the Slurm version)")
    return {"steps": steps, "advice": "one major version at a time" if gap > 1 else "", "gap": gap}

# ---- cgroups --------------------------------------------------------------------------------------------------------------------------------
CGROUP_PLUGINS = ["proctrack/cgroup", "task/cgroup", "jobacct_gather/cgroup"]

def cgroup_conf(params):
    """The part of cgroup.conf that CMDaemon generates from the cgroups submode of the WLM instance. Keys are Slurm's names (ConstrainCores,
    ConstrainRAMSpace, ConstrainSwapSpace, ConstrainDevices, AllowedRAMSpace, ...)."""
    allowed = {"CgroupAutomount", "CgroupMountpoint", "TaskAffinity", "CgroupReleaseAgentDir", "ConstrainCores", "ConstrainRAMSpace", "ConstrainSwapSpace",
               "ConstrainDevices", "AllowedRAMSpace", "AllowedSwapSpace", "MaxRAMPercent", "MaxSwapPercent", "MinRAMSpace"}
    bad = set(params) - allowed
    if bad:
        raise WlmError(f"unknown cgroup.conf parameter(s) {sorted(bad)}")
    return [f"{k}={'yes' if v is True else 'no' if v is False else v}" for k, v in params.items()]

def devices_constrained(params):
    """ConstrainDevices=yes is what keeps a job from using GPUs it was not allocated (GRES-based)."""
    return params.get("ConstrainDevices") is True

# ---- drain -----------------------------------------------------------------------------------------------------------------------------------
class SlurmNode:
    def __init__(self, name):
        self.name, self.drained, self.running, self.actions = name, False, [], []

    def drain(self, actions=()):
        self.drained, self.actions = True, list(actions)

    def undrain(self):
        self.drained = False

    def can_start_job(self):
        return not self.drained

    def job_finished(self, job):
        self.running.remove(job)
        if self.drained and not self.running and "reboot" in self.actions:
            return "reboot"
        return None


# ---- 7.4.3, 7.5, 7.6-7.9, 7.11 WLM monitoring, job cache, power usage, prejob checks, nodecustomizations (added in gap pass) ----
WLM_JOB_POWER_DEFAULTS = {"job_age": "5m", "timeout": "30s", "disabled": False}
JOB_INFO_DIRECTIVE_DEFAULTS = {"JobInformationKeepCount": 8192, "JobInformationKeepCount_max": 65536, "JobInformationKeepDuration_days": 28, "JobInformationMinimalJobDuration": "0s"}


def freeze_wlm_config_directive(wlm, enabled=True):
    """7.5 (p. 387): FreezeChangesTo<workload manager>Config = <true|false> in cmd.conf (Slurm or LSF, default false)."""
    if wlm.lower() not in ("slurm", "lsf"):
        raise WlmError("WLM for FreezeChangesTo<WLM>Config must be Slurm or LSF")
    name = "Slurm" if wlm.lower() == "slurm" else "LSF"
    return f"FreezeChangesTo{name}Config = {'true' if enabled else 'false'}"


class JobCache:
    """7.7.2 (p. 452): models CMDaemon job information cache with JobInformationKeepCount (default 8192, max 65536),
    persistent <job_id> (survives normal eviction), and forget <job_id> (removes immediately even if persistent)."""
    def __init__(self, keep_count=8192):
        if not (1 <= keep_count <= 65536):
            raise WlmError("JobInformationKeepCount must be <= 65536 (p. 452)")
        self.keep_count = keep_count
        self.jobs = {}

    def add(self, job_id, status="COMPLETED"):
        self.jobs[job_id] = {"status": status, "persistent": False}

    def mark_persistent(self, job_id):
        self.jobs[job_id]["persistent"] = True

    def forget(self, job_id):
        """7.7.2: forget removes a job from the cache immediately, regardless of whether it is marked persistent."""
        self.jobs.pop(job_id, None)

    def expire_old(self):
        for jid in [k for k, v in self.jobs.items() if not v["persistent"]]:
            del self.jobs[jid]


def prejob_check_status(hc_prejob_enabled, wlm_enableprejob, check_result="PASS", drain_on_fail=True):
    """7.8.2 (pp. 459-460): if a health check has prejob=yes but no WLM has enableprejob=yes, cmsh warns:
    'warning: Prejob is selected, but no WLM has prejob'. When both are enabled and the check returns FAIL, the job is
    prevented from running on that node (preventing Black Hole Node Syndrome), and if drained by the health check, the node
    is NOT automatically undrained (requires manual undrain)."""
    if hc_prejob_enabled and not wlm_enableprejob:
        return {"runs": False, "warning": "warning: Prejob is selected, but no WLM has prejob", "job_allowed": True, "drained": False, "auto_undrain": False}
    if not (hc_prejob_enabled and wlm_enableprejob):
        return {"runs": False, "warning": "", "job_allowed": True, "drained": False, "auto_undrain": False}
    failed = (check_result == "FAIL")
    return {
        "runs": True,
        "warning": "",
        "job_allowed": not failed,
        "drained": bool(failed and drain_on_fail),
        "auto_undrain": False,  # 7.8.2 p. 459: never automatically undrained
    }


def apply_node_customization(wlm, key, value, enabled=True):
    """7.11 (pp. 465-466): in Slurm, an enabled nodecustomization appends '<KEY>=<VALUE>' to the NodeName line in slurm.conf
    and removes it when disabled/removed. In LSF, it sets the column in lsb.hosts to '<VALUE>' and replaces it with '()' when disabled/removed."""
    wlm = wlm.lower()
    if wlm == "slurm":
        return f"{key}={value}" if enabled else ""
    if wlm == "lsf":
        return str(value) if enabled else "()"
    raise WlmError("wlm must be slurm or lsf")

