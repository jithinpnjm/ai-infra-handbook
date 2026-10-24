#!/usr/bin/env python3
"""Day-2 operations rules from BCM 11 Administrator Manual chapters 9 and 14 (and the NVIDIA-DevOps notes, volume 10 chapter 13), as small testable pieces.

Not BCM. Each part names the manual section it follows; my own syntheses are labelled.
"""
import re

class OpsError(ValueError):
    pass

# ---- 9.1.2 version numbers ------------------------------------------------------------------------------------------------------------
def parse_point_release(v):
    """Release 10.0 / 11.0 are the main releases. Point releases: calendar format 10.YY.MM / 11.YY.MM (10.x up to 10.25.03; 11.x up to 11.25.08), then semantic
    format 10.MINOR.PATCH / 11.MINOR.PATCH (11.30.0, 11.31.0 ...). A lower-case letter suffix marks a hotfix of an existing point release."""
    m = re.fullmatch(r"(10|11)\.(\d+)\.(\d+)([a-z]?)", v)
    if not m:
        raise OpsError(f"not a BCM point release: {v}")
    major, a, b, hot = int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)
    last_calendar = (25, 3) if major == 10 else (25, 8)
    if a >= 30:
        scheme = "semantic"
    elif (a, b) <= last_calendar:
        scheme = "calendar"
    else:
        scheme = "unknown"      # the manual gives no scheme between the last calendar release and 30.x
    return {"major": major, "a": a, "b": b, "hotfix": hot or None, "scheme": scheme}

def os_change_supported(frm, to):
    """Upgrading the OS to the next major release (RHEL8 to RHEL9) while keeping BCM is not supported: install BCM again on the new OS. Package updates within a major
    release are supported."""
    fm = re.sub(r"\D", "", frm)[:1]
    tm = re.sub(r"\D", "", to)[:1]
    return fm == tm

def head_update_commands(distro):
    return {"rhel": ["yum update"], "rocky": ["yum update"], "ubuntu": ["apt update", "apt upgrade"], "sles": ["zypper refresh", "zypper up"]}[distro]


# ---- 9.1 & 9.2 package filename anatomy, device packages scale, GPG key, /cm/shared layout (added in gap pass) -----------
BCM_GPG_KEY_ID = "0x5D849C16"
CM_SHARED_SUBDIRS = ("apps", "docs", "etc", "examples", "licenses", "modulefiles")


def parse_bcm_package_filename(filename):
    """9.1 (pp. 521-522):
      RPM: <package>-<version>-<revision>_cm<x.y>_<hash>.<arch>.rpm
      DEB: <package>_<version>-<revision>-cm<x.y>-<hash>_<arch>.deb
    Hash is only present for BCM packages ('cm' marker)."""
    m_rpm = re.fullmatch(r"([A-Za-z0-9_+-]+)-([0-9.]+)-(\d+)_cm([0-9.]+)_([0-9a-f]+)\.([A-Za-z0-9_]+)\.rpm", filename)
    if m_rpm:
        pkg, ver, rev, cm_ver, h, arch = m_rpm.groups()
        return {"format": "rpm", "package": pkg, "version": ver, "revision": int(rev), "cm_version": cm_ver, "hash": h, "arch": arch, "is_bcm": True}
    m_deb = re.fullmatch(r"([A-Za-z0-9_+-]+)_([0-9.]+)-(\d+)-cm([0-9.]+)-([0-9a-f]+)_([A-Za-z0-9_]+)\.deb", filename)
    if m_deb:
        pkg, ver, rev, cm_ver, h, arch = m_deb.groups()
        return {"format": "deb", "package": pkg, "version": ver, "revision": int(rev), "cm_version": cm_ver, "hash": h, "arch": arch, "is_bcm": True}
    return {"is_bcm": False}


def device_packages_all_output_mb(num_nodes, kb_per_node=100):
    """9.1.1 (p. 523): 'packages -a' returns ~100 KB per node (~1000 lines); for 1000 nodes that is ~100 MB (nearly a million lines)."""
    return (num_nodes * kb_per_node) / 1000.0


# ---- 14.1 parallel shells --------------------------------------------------------------------------------------------------------------------
GENDERS = {"all": "every node, head and regular", "category=default": "nodes in the default category", "computenode": "regular nodes", "headnode": "head node(s)"}

def choose_parallel_tool(task):
    """pexec runs from cmsh (CMDaemon); pdsh runs from the OS shell. pdsh is REQUIRED when stopping or restarting CMDaemon on many regular nodes (a command that relies on
    a running CMDaemon on the node cannot safely stop it). Power commands: use cmsh `device power` (it delays between nodes), not pdsh or pexec."""
    if task == "restart cmd on regular nodes":
        return "pdsh"
    if task in ("power reset", "power on", "power off"):
        return "cmsh device power (with its built-in delay)"
    return "pexec or pdsh (administrator's choice)"

def pdsh_flags(skip_down=True, all_nodes=False):
    f = []
    if skip_down:
        f.append("-v")
    if all_nodes:
        f.append("-A" if not skip_down else "-a")
    return f

def cmsh_calls(n_nodes, method):
    """Setting a category for many nodes: a shell loop that starts cmsh and commits per node costs n_nodes cmsh runs; a single piped cmsh session costs 1."""
    return n_nodes if method == "loop" else 1

def bulk_category_script(nodes, category):
    return ["device"] + [f"set {n} category {category}" for n in nodes] + ["commit"]

# ---- 14.2 support ----------------------------------------------------------------------------------------------------------------------------
CM_DIAGNOSE_DEFAULTS = {"limit_mb": 50, "timeout_s": 60}

def support_case(version_major):
    """Support portal: Product Type Software. Product Category: 'Bright Cluster Manager' for versions before BCM 10, 'Base Command Manager' for 10 and later."""
    return {"product_type": "Software", "product_category": "Bright Cluster Manager" if version_major < 10 else "Base Command Manager"}

def cm_diagnose_args(nodes):
    """For larger clusters raise the log limit (default 50 MB) and timeout (default 60 s) so logs are not cropped and commands not killed."""
    if nodes > 100:
        return ["--limit", "100", "--timeout", "240"]
    return []

# ---- 14.3 backups -----------------------------------------------------------------------------------------------------------------------------
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
BACKUP_DIR = "/var/spool/cmd/backup"

def local_backup_names():
    """The CMDaemon database is backed up nightly into a local rotating set of 7 files."""
    return [f"backup-{d}.sql.gz" for d in DAYS]

def cmdaemon_backup_name(prefix=None, stamp=None, day=None):
    """cmdaemon-backup with no argument overwrites the day's default backup (backup-<Day>.sql.gz); with a string it is prefix + timestamp
    YY-MM-DD_HH-MM-SS_<Day>, for example manual-24-08-28_13-19-59_Wed.sql.gz."""
    if prefix is None:
        return f"backup-{day}.sql.gz"
    return f"{prefix}-{stamp}_{day}.sql.gz"

def backup_scope():
    return {"BCM provides a backup facility": False, "back up": ["the full head node filesystem including software images", "the CMDaemon database"],
            "not backed up locally": ["raw monitoring data (very large); only the monitoring configuration inside the database is"],
            "regular node disks": "not needed unless they hold important data"}

def restore_path(ha, mysql_starts=True):
    """Corrupt database handling. If MySQL cannot start, CMDaemon cannot start. HA: `cmha dbreclone <passive>` gives a current CMDaemon and Slurm database but does not
    clone monitoring data. Non-HA: gunzip the local backup and pipe it into MySQL."""
    if not mysql_starts:
        pre = "MySQL cannot start, so CMDaemon cannot start: repair or restore first. "
    else:
        pre = ""
    return pre + ("HA: cmha dbreclone from the healthy head (monitoring data is not cloned)" if ha else "non-HA: restore the latest /var/spool/cmd/backup/backup-<Day>.sql.gz into MySQL")

def corruption_symptoms():
    return ["mysql health check fails", "database runs read-only", "info message in the event viewer", "checksum errors in journalctl -xeu mysql.service"]

# ---- 14.4 image revision control ------------------------------------------------------------------------------------------------------------------
def btrfs_ok_for(distro_major):
    """Btrfs has been removed from RHEL since RHEL 8; SLES 15 supports it. Keep backups of important images on a non-Btrfs filesystem."""
    return distro_major.lower() not in ("rhel8", "rhel9", "rocky8", "rocky9")

def revision_name(parent, n):
    return f"{parent}@{n}", f"/cm/images/{parent}-{n}"

# ---- 14.6 hardware match ------------------------------------------------------------------------------------------------------------------------------
HW_PROFILE = {"reference saved under": "/cm/shared/apps/cmd/hardware-profiles/<name>", "interval_s": 600, "run where": "a category through nodeexecutionfilters"}

def hardware_match(reference, nodes):
    """Compare each node's profile to the reference; a bad reference shows up as most nodes failing."""
    bad = sorted(n for n, p in nodes.items() if p != reference)
    return {"mismatched": bad, "reference_suspect": len(bad) > len(nodes) / 2}

# ---- 14.9 replacement, scaling -------------------------------------------------------------------------------------------------------------------------
def node_replacement_steps(mac_known, same_disk_size=True):
    steps = ["device use <node>"]
    steps.append("set mac <new mac>" if mac_known else "clear mac")
    steps.append("commit")
    if not mac_known:
        steps.append("boot the new machine: at the node installer choose the node name (placeholder identity, chapter 8.4)")
    if not same_disk_size:
        steps.append("the disk layout must match: adjust disksetup (chapter 8.3) or expect a FULL install with the new layout")
    return steps

def ansible_collection(version):
    """From BCM 9.1 the collection name carries the version: brightcomputing.bcm110 for BCM 11."""
    return {"11.0": "brightcomputing.bcm110"}[version]

# ---- MySQL HA for Slurm accounting (14.12) ---------------------------------------------------------------------------------------------------------------
def mysql_failover_command(host, primary_crashed=False, config="/root/mysql-ha-config.conf"):
    cmd = f"cm-slurm-mysql-ha --config {config} failover --host {host}"
    return cmd + (" --force" if primary_crashed else "")

def mysql_remediate_command(primary, target, config="/root/mysql-ha-config.conf"):
    return f"cm-slurm-mysql-ha --config {config} remediate --host {primary} --target {target}"

# ---- a day-2 runbook shape (my synthesis from the above and the notes) -----------------------------------------------------------------------------------
def change_runbook(kind):
    common = ["write down what you will change and how to undo it", "cmdaemon-backup before-change (a named DB backup)"]
    if kind == "image":
        return common + ["clone or lock the image (chapter 8.4)", "change in a chroot", "updateprovisioners", "imageupdate dry run, read synclog, then -w on one node", "roll out in batches; drain first", "verify; keep the old image until the new one has run"]
    if kind == "head package":
        return common + ["HA: active first for cmdaemon and mysql, confirm cmha status, then passive", "restart cmd only after the package manager does it", "verify cmsh, Base View, a provisioning test"]
    if kind == "bios or firmware":
        return common + ["stage in a test node", "one rack at a time", "AC power cycle if the Result column says so (chapter 8.7)", "verify versions and a GPU test"]
    raise OpsError("kind is image, head package, or bios or firmware")
