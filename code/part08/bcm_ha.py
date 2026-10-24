#!/usr/bin/env python3
"""Head node high availability rules from BCM 11 Administrator Manual chapter 15, as small testable pieces. Not BCM.

Each part names the manual section it follows. Where the manual's text is unclear (the failover parameter table is garbled in the text I had) the code says so.
"""

class HaError(ValueError):
    pass

STATES = ("INIT", "FENCING", "ACTIVE", "PASSIVE", "BECOMEACTIVE", "BECOMEPASSIVE", "UNABLETOBECOMEACTIVE", "ERROR")

# Values printed in the manual's `partition failover base; show` example. The text of the table is garbled; this mapping is my reading.
DEFAULTS = {"dead time": 10, "warn time": 5, "init dead": 30, "keep alive": 1, "quorum time": 60, "disable automatic failover": False}

# ---- 15.1.1 naming versus mode --------------------------------------------------------------------------------------------
class HeadPair:
    """Primary/secondary is naming and never changes; active/passive is the mode and does change."""
    def __init__(self):
        self.mode = {"primary": "ACTIVE", "secondary": "PASSIVE"}

    def makeactive(self, node):
        other = "secondary" if node == "primary" else "primary"
        self.mode[node], self.mode[other] = "ACTIVE", "PASSIVE"

    def active(self):
        return [n for n, m in self.mode.items() if m == "ACTIVE"]

    def single_active(self):
        return len(self.active()) == 1

# ---- 15.4.2 cmha status ---------------------------------------------------------------------------------------------------------
def classify_active(status):
    """status: dict with failoverping, ping, status, mysql each 'OK' or 'FAIL'. By default BCM prepares to fail over when ping, failoverping AND status are all not OK:
    'all dead'. If only some failed it is 'mostly dead' (slightly alive) and the failover must be started manually. mysql replication is reported but not part of that test."""
    core = [status[k] != "OK" for k in ("ping", "failoverping", "status")]
    if all(core):
        return "all dead"
    if any(core):
        return "mostly dead"
    return "healthy" if status.get("mysql", "OK") == "OK" else "healthy (mysql replication problem)"

# ---- 15.1.6 quorum ----------------------------------------------------------------------------------------------------------------
def quorum_agrees(cannot_reach_active, responders, total_nodes=None, use_total=False):
    """The passive asks all nodes whether they also cannot reach the active head; if more than half confirm, it proceeds. Nodes that do not answer within Quorum
    time are no longer considered. Whether 'half' is of the responders or of all nodes is ambiguous in the manual's text; responders is the default here (use_total
    switches to all nodes)."""
    denom = total_nodes if (use_total and total_nodes) else responders
    return cannot_reach_active * 2 > denom

# ---- 15.1.6, 15.1.7, 15.2.4 failover decision ------------------------------------------------------------------------------------------
def failover_decision(active_state, event="crash", auto_enabled=True, power_control_ok=True, bmc_reachable=True, quorum_ok=True):
    """What the passive does.
      event 'graceful shutdown' or 'reboot' -> nothing (assumed intentional; an administrator uses `cmha makeactive`)
      'sluggish' (mostly dead) -> nothing automatic; an administrator decides
      'crash' with all dead -> quorum; STONITH (power off + verify); then become active
      cable pulled / BMC unreachable -> no automatic failover (cannot tell a dead head from a network failure): manual confirmation
    Automatic failover also needs power control on both heads and not being disabled."""
    if event in ("graceful shutdown", "reboot"):
        return "nothing: assumed intentional (run cmha makeactive to switch)"
    if active_state == "healthy":
        return "nothing: the active is fine"
    if active_state == "mostly dead":
        return "nothing automatic: mostly dead, an administrator must decide (and may power it off)"
    if not auto_enabled or not power_control_ok:
        return "manual: an administrator must confirm the active is off and run cmha makeactive"
    if not bmc_reachable:
        return "manual: BMC unreachable (power cable pulled?), cannot verify power-off"
    if not quorum_ok:
        return "nothing: quorum says the active is still reachable by most nodes (passive may be the isolated one)"
    return "fence, power off the active (STONITH), verify, become active"

def test_outcome(kind):
    """15.2.4 how to test."""
    return {"power off": "failover happens: the BMC stays up so the power state can be verified",
            "pull power cable": "no automatic failover: the BMC goes down too, so a dead head cannot be told from a network failure",
            "graceful shutdown": "no failover: assumed intentional",
            "kernel crash (echo c > /proc/sysrq-trigger)": "failover happens; the crashed head may later show FAILED database replication and need dbreclone"}[kind]

# ---- timers --------------------------------------------------------------------------------------------------------------------------------
def silence_level(seconds_silent, just_started=False, p=None):
    """Warn time: log a warning. Dead time: the active is considered dead and a quorum starts. At CMDaemon start-up Init dead is used instead of Dead time."""
    p = p or DEFAULTS
    dead = p["init dead"] if just_started else p["dead time"]
    if seconds_silent > dead:
        return "dead"
    if seconds_silent > p["warn time"]:
        return "warn"
    return "ok"

def heartbeat_checks(has_failover_network):
    """With a dedicated failover network 3 separate heartbeat checks are carried out (ping, failoverping, status); keep alive is the interval."""
    return 3 if has_failover_network else 2

# ---- 15.1.3 replication scope ------------------------------------------------------------------------------------------------------------
SYSTEM_DBS = {"mysql", "information_schema", "performance_schema", "sys"}
DEFAULT_REPLICATED = {"cmdaemon", "slurm_acct_db"}

def replicated_databases(existing, replicate_all=False, extradbclone=()):
    """Default: only cmdaemon and slurm_acct_db (plus names listed in extradbclone.xml). From BCM 11.34 the option 'Replicate all non-system MySQL databases?'
    (express: --replicate-all-databases) replicates every non-system database and the users/grants. System databases are never replicated."""
    if replicate_all:
        return sorted(set(existing) - SYSTEM_DBS)
    return sorted((DEFAULT_REPLICATED | set(extradbclone)) & set(existing))

def missing_after_failover(existing, replicate_all=False, extradbclone=()):
    return sorted((set(existing) - SYSTEM_DBS) - set(replicated_databases(existing, replicate_all, extradbclone)))

# ---- shared storage, services -----------------------------------------------------------------------------------------------------------
SERVICES_ON_BOTH = ["CMDaemon", "DHCP", "TFTP", "LDAP", "MySQL", "NTP", "DNS"]
SERVICES_THAT_MIGRATE = ["NFS", "User Portal", "slurmdbd", "LSF mbatchd/elim/eauth/mbschd"]
SHARED_DIRS = ["/home", "/cm/shared"]

def storage_script_ok(unmount_exit_code, problems_present):
    """The unmount (pre-failover) script must return non-zero if unmounting has problems, or the storage may end up mounted twice during the post-failover stage."""
    if problems_present and unmount_exit_code == 0:
        return False, "the script reported success despite a problem: risk of a double mount and corruption"
    return True, "ok"

def passive_shows_old_contents():
    """Shared filesystems are mounted only on the active head; on the passive the old local contents are visible. Tell users to log in through the shared IP."""
    return True

# ---- setup prerequisites ------------------------------------------------------------------------------------------------------------------
def ha_setup_problems(license_macs, external_ips_static, power_control_both, failover_link, shared_storage):
    """License: HA needs an HA-enabled license (two MAC addresses in verify-license info). External head node addresses must be static (DHCP will not work).
    Power control on both heads is needed for automatic failover. The failover network should be a direct cable (no switch). BCM 11 uses NAS for shared storage;
    DAS is no longer suggested."""
    p = []
    if license_macs < 2:
        p.append("the license is not HA-enabled (an HA license shows two MAC addresses)")
    if not external_ips_static:
        p.append("external head node addresses must be static: DHCP does not work for HA")
    if not power_control_both:
        p.append("no power control on both heads: failover will be manual only")
    if failover_link == "switch":
        p.append("the failover network goes through a switch: a switch reset breaks the heartbeat; use a direct cable")
    if shared_storage == "DAS":
        p.append("direct attached storage is no longer suggested from BCM 11: use NAS")
    return p

def update_order(package):
    """CMDaemon and MySQL packages: active head first, confirm `cmha status`, then the passive (a CMDaemon update can carry a MySQL schema migration). DHCP, LDAP, NTP,
    DNS: any order. Migrating services (NFS, sgemaster): update the passive, make it active with cmha makeactive, then update the former active."""
    if package in ("cmdaemon", "mysql"):
        return ["active", "confirm cmha status OK", "passive"]
    if package in ("dhcp", "ldap", "ntp", "dns"):
        return ["both at about the same time"]
    if package in ("nfs", "sgemaster"):
        return ["passive", "cmha makeactive on the passive", "former active"]
    raise HaError("package not modelled")

def things_to_sync_by_hand():
    return ["RPM installations and updates on the head node", "locally installed applications", "files in /cm/node-installer/ used by initialize and finalize scripts",
            "any other configuration outside the shared filesystems"]

def regular_node_ha_differences():
    return {"setup tool": "installed by the administrator (not cmha-setup)", "config submode": "failovergroups", "passive nodes": "several, defined by failover groups",
            "heartbeat": "regular node network, no failover network", "power control": "needed for automatic failover"}


# ---- 15.3 express cmha-setup, 15.4.8 clone exclude lists, 15.5.4 regular node failover sequence, 15.6 job continuation (added in gap pass) ----
EXPRESS_DEFAULT_CONFIG = "/cm/local/apps/cluster-tools/ha/conf/failoverconf.xml"
CLONE_EXCLUDE_FILES = {"normal": "/cm/excludelistnormal", "failover": "/cm/excludelistfailover"}


def cmha_express_commands(config_file=EXPRESS_DEFAULT_CONFIG, mysql_password=None, replicate_all_dbs=False, finalize_reboot=True, storage_type="nas"):
    """15.3.2 & 15.3.3 (pp. 816-817): express non-ncurses cmha-setup (-x) workflow."""
    pw = f" -p {mysql_password}" if mysql_password else ""
    all_db = " -a" if replicate_all_dbs else ""
    reb = " -r" if finalize_reboot else ""
    return [
        f"cmha-setup -x -c {config_file} -i{pw}{all_db}",
        "/cm/cm-clone-install --failover  # on the PXE-booted passive head",
        f"cmha-setup -x -c {config_file} -f{reb}{pw}",
        f"cmha-setup -x -c {config_file} -s {storage_type}",
    ]


def clone_install_exclude_file(failover=True):
    """15.4.8 (p. 828): cm-clone-install reads /cm/excludelistfailover when --failover is passed, and /cm/excludelistnormal otherwise.
    Neither file is maintained by CMDaemon or modified by excludelistmanipulatescript."""
    return CLONE_EXCLUDE_FILES["failover" if failover else "normal"]


def regular_node_failover_sequence(unmount_exit_code=0, stonith_triggered=False):
    """15.5.4 (p. 834): sequence of events when making another HA regular node active.
    - If active umount script returns non-zero (exit_code > 0), all remaining actions are skipped.
    - If STONITH powers off the initial active node, the old-active sequence is aborted and passive takeover proceeds."""
    steps = ["all: run pre-failover script"]
    if stonith_triggered:
        steps.append("active: aborted by STONITH power-off")
    else:
        steps.append("active: stop service")
        steps.append("active: run umount script")
        if unmount_exit_code != 0:
            return {"steps": steps, "aborted_on_umount_error": True, "completed": False}
        steps.extend(["active: stop active IP", "active: start passive IP", "active: start passive services (now passive)"])
    steps.extend([
        "passive: stop service",
        "passive: run mount script",
        "passive: stop passive IP",
        "passive: start active IP",
        "passive: start service (now active)",
        "all: run post-failover script",
    ])
    return {"steps": steps, "aborted_on_umount_error": False, "completed": True}


def wlm_jobs_continue_across_failover(installed_via_bcm_or_cm_wlm_setup, storage_type, wlm, job_tolerates_brief_fs_unavailability):
    """15.6 (pp. 834-835): three conditions for running WLM jobs to continue through a failover handover:
    (1) WLM set up at initial install or via cm-wlm-setup, (2) HA storage supports job continuity (NAS for Slurm and LSF),
    (3) job code does not fail during the brief window when shared storage is unavailable."""
    storage_ok = (storage_type.upper() == "NAS" and wlm.lower() in ("slurm", "lsf"))
    return bool(installed_via_bcm_or_cm_wlm_setup and storage_ok and job_tolerates_brief_fs_unavailability)

