#!/usr/bin/env python3
"""Node provisioning rules from BCM 11 Administrator Manual chapter 5 (and 9.3, 9.4), as small testable pieces.

Not BCM. Each part names the manual section it follows. Where the manual's text is unclear the code says so.

  5.1   boot protocol and the PXE label
  5.2   provisioning scheduler: slots, node groups, fewest active tasks, deferral, 5 retries, locked images, update timeout
  5.3   kernel modules: node overrides category overrides image, and an override REPLACES the list
  5.4   the install modes, the FULL confirmation (datanode), the 7 identification scenarios, newnodes
  5.5   node states
  5.6   exclude lists for update / install / grab
"""
from dataclasses import dataclass, field

class ProvError(ValueError):
    pass

# ---- 5.1 boot protocol ----------------------------------------------------------------------------------------
def boot_path(protocol="http", arch="x86_64"):
    """5.1.6: bootloaderprotocol default HTTP. On x86_64 the first stage is still TFTP and the switch to HTTP happens when the
    kernel and ramdisk load. HTTPS is rarely supported by hardware. ARMv8 boots over TFTP only (5.8.1) and gets a GRUB binary."""
    protocol = protocol.lower()
    if protocol not in ("http", "https", "tftp"):
        raise ProvError("bootloaderprotocol is one of http, https, tftp")
    if arch == "arm64":
        return {"first_stage": "tftp (grub binary)", "kernel_and_ramdisk": "tftp", "note": "ARMv8 can boot only via TFTP"}
    return {"first_stage": "tftp", "kernel_and_ramdisk": protocol,
            "note": "HTTPS works only for some special hardware" if protocol == "https" else ""}

# ---- 5.2 provisioning scheduler ---------------------------------------------------------------------------------
MAX_RETRIES = 5
LOST_CONNECTIVITY_SECONDS = 180
DEFAULT_SLOTS = 10
DIRTY_AUTO_UPDATE_TIMEOUT = 300

@dataclass
class Provisioner:
    name: str
    slots: int = DEFAULT_SLOTS
    images: set = field(default_factory=lambda: {"default-image"})
    nodegroups: set = field(default_factory=set)
    uptodate: set = field(default_factory=lambda: {"default-image"})
    draining: bool = False
    active: list = field(default_factory=list)

    def serves(self, node_groups, image):
        """nodegroups rule (5.2.1)."""
        if image not in self.images or image not in self.uptodate:
            return False
        if self.nodegroups:
            return bool(self.nodegroups & set(node_groups))
        # a provisioner with no nodegroups can serve only nodes that are in no group or in a group no provisioner lists
        return True

class Scheduler:
    def __init__(self, provisioners, max_threads=None, locked=()):
        self.p = {x.name: x for x in provisioners}
        self.max_threads = max_threads
        self.locked = set(locked)
        self.deferred = []
        self.failures = {}

    def _listed_groups(self):
        return set().union(*[x.nodegroups for x in self.p.values()]) if self.p else set()

    def eligible(self, node, node_groups, image):
        listed = self._listed_groups()
        out = []
        for x in self.p.values():
            if x.draining or len(x.active) >= x.slots or not x.serves(node_groups, image):
                continue
            if not x.nodegroups and (set(node_groups) & listed):
                continue   # nodes in a listed group can only use provisioners that list that group
            out.append(x)
        return out

    def total_active(self):
        return sum(len(x.active) for x in self.p.values())

    def request(self, node, node_groups, image):
        """5.2.4: locked image -> deferred. Cluster-wide cap -> deferred. Else the eligible provisioner with the lowest number of
        already-started tasks. Ties: first in the order given (the manual does not say)."""
        if image in self.locked:
            self.deferred.append((node, node_groups, image)); return None, "deferred: requested software image is locked"
        if self.max_threads is not None and self.total_active() >= self.max_threads:
            self.deferred.append((node, node_groups, image)); return None, "deferred: cluster-wide limit reached"
        cands = self.eligible(node, node_groups, image)
        if not cands:
            self.deferred.append((node, node_groups, image)); return None, "deferred: no provisioner free"
        best = min(cands, key=lambda x: len(x.active))
        best.active.append(node)
        return best.name, "allocated"

    def finish(self, node):
        for x in self.p.values():
            if node in x.active:
                x.active.remove(node)
        retry, self.deferred = self.deferred, []
        return [(n, self.request(n, g, i)) for n, g, i in retry]

    def failed_transfer(self, node):
        """5.2.4: 5 retry attempts, then the request fails."""
        self.failures[node] = self.failures.get(node, 0) + 1
        return "retry" if self.failures[node] <= MAX_RETRIES else "failed"


def lost_connectivity_outcome(seconds_down):
    """5.2.4: requests stay allocated for 180 s from the time connectivity was lost, then they fail."""
    return "still allocated" if seconds_down <= LOST_CONNECTIVITY_SECONDS else "failed"


def provisioner_update(last_update_age, timeout=DIRTY_AUTO_UPDATE_TIMEOUT):
    """5.2.4 dirtyautoupdatetimeout: on a provisioning request the head node triggers a provisioner update only if the last
    update is older than the timeout. Timeout 0 disables it."""
    if timeout == 0:
        return False
    return last_update_age > timeout


def node_gets_new_image(image_changed_age, last_update_age, timeout=DIRTY_AUTO_UPDATE_TIMEOUT, ran_updateprovisioners=False):
    """5.6.4: if the image changed within the timeout, provisioners may not have it yet, so nodes updating from a provisioner do
    not receive it. Running updateprovisioners just before imageupdate fixes that. Ages are seconds since the event."""
    if ran_updateprovisioners:
        return True
    updated_after_change = last_update_age < image_changed_age
    return updated_after_change or provisioner_update(last_update_age, timeout)

# ---- 5.3 kernel modules --------------------------------------------------------------------------------------
def effective_kernel_modules(image, category=None, node=None):
    """5.3.2: node overrides category overrides image, and the override means the higher level is TOTALLY ignored (not merged)."""
    for lst, src in ((node, "node"), (category, "category"), (image, "image")):
        if lst:
            return list(lst), src
    return [], "none"

def ramdisk_needs_regeneration(kernel_changed_outside_cmdaemon):
    """5.8.4: after yum/zypper/apt changes the kernel or modules in an image, the extended ramdisk is NOT updated by the package manager;
    createramdisk must be run or nodes can fail during ramdisk load."""
    return bool(kernel_changed_outside_cmdaemon)

# ---- 5.4 install modes -------------------------------------------------------------------------------------------
MODES = ("AUTO", "FULL", "MAIN", "NOSYNC", "SKIP")

def install_plan(mode, partitions_ok=True, datanode=False, confirmed=False):
    """5.4.4, 5.4.6, 5.4.7. Returns what the node installer does.
      FULL    no check; repartition; full sync; wipes everything
      AUTO    check; healthy -> incremental sync; unhealthy -> FULL
      MAIN    no check; maintenance mode; drive untouched
      NOSYNC  check; healthy -> no sync (cert/key refreshed if missing); unhealthy -> rewrite partitions and full sync
      SKIP    no check; no sync
    datanode: a FULL install (including one triggered by AUTO or NOSYNC) waits for confirmation."""
    mode = mode.upper()
    if mode not in MODES:
        raise ProvError(f"install mode must be one of {MODES}")
    plan = {"mode": mode, "check_disks": False, "repartition": False, "sync": "none", "maintenance": False, "wipes": False, "waits_for_confirmation": False}
    if mode == "FULL":
        plan.update(repartition=True, sync="full", wipes=True)
    elif mode == "AUTO":
        plan["check_disks"] = True
        if partitions_ok:
            plan["sync"] = "sync"
        else:
            plan.update(repartition=True, sync="full", wipes=True)
    elif mode == "MAIN":
        plan["maintenance"] = True
    elif mode == "NOSYNC":
        plan["check_disks"] = True
        if not partitions_ok:
            plan.update(repartition=True, sync="full", wipes=True)
    # SKIP: nothing
    if plan["wipes"] and datanode and not confirmed:
        plan["waits_for_confirmation"] = True
    return plan


def datanode_effective(category_value, node_value):
    """datanode is a Boolean: category OR node (5.4.4)."""
    return bool(category_value or node_value)

# ---- 5.4.2 identification --------------------------------------------------------------------------------------
def identify(known, port_detected, config_for_port, mac_config_has_port=None, same_config=None):
    """The manual's truth table of 7 scenarios. Returns (scenario, outcome) where outcome is 'automatic' (a suggestion that is accepted
    after a timeout) or 'manual' (a dialog loops until someone acts).
      1 new,  port detected, config for port found            -> automatic
      2 new,  port detected, none found                       -> manual
      3 new,  no port                                         -> manual
      4 known, port detected, port config == MAC config       -> automatic
      5 known, port detected, configs differ (port mismatch)  -> manual
      6 known, no port detected, MAC config expects a port    -> manual
      7 known, port detected, MAC config has no port (unset)  -> automatic
    A known node with no port detected and no port expected is not in the manual's table; no ports are involved, so it is treated as
    automatic here (my reading)."""
    if not known:
        if port_detected and config_for_port:
            return 1, "automatic"
        if port_detected:
            return 2, "manual"
        return 3, "manual"
    if port_detected:
        if not mac_config_has_port:
            return 7, "automatic"
        return (4, "automatic") if same_config else (5, "manual")
    if mac_config_has_port:
        return 6, "manual"
    return 0, "automatic"

def newnodes_assign(arrivals, names, offset=0, taken=(), force=False):
    """5.4.2 newnodes -s/-w -n <names> [-o offset] [-f]. arrivals: MACs in order of appearance. Names are assigned in order after skipping
    `offset` arrivals. Fails if a name is already taken unless force."""
    pool = arrivals[offset:]
    if len(names) > len(pool):
        raise ProvError(f"{len(names)} names but only {len(pool)} unassigned MACs after the offset")
    out = {}
    for mac, name in zip(pool, names):
        if name in taken and not force:
            raise ProvError(f"{name} is already taken (use --force, which moves it to the new MAC)")
        out[mac] = name
    return out

# ---- 5.5 node states ----------------------------------------------------------------------------------------------
BOOT_SEQUENCE = ["BOOTING", "INSTALLING", "INSTALLER_CALLINGINIT", "UP"]
PROBLEM_STATES = {"DOWN", "INSTALLER_FAILED", "INSTALLER_UNREACHABLE", "INSTALLER_REBOOTING", "OPENING"}

class NodeState:
    """5.5: state shown as 'UP', 'DOWN', 'DOWN/CLOSED' ... CLOSED is a modifier added by `close`; the only way out is `open`, which passes through
    OPENING (about 5 s, never more than 30 s by default). OPEN is never printed. mute does not change the state."""
    def __init__(self, state="DOWN"):
        self.base, self.closed, self.muted, self.restart_required = state, False, False, False

    def __str__(self):
        s = self.base + ("/CLOSED" if self.closed else "")
        return s + (", muted" if self.muted else "")

    def event(self, ev):
        t = {"power_on": ("DOWN", "BOOTING"), "installer_started": ("BOOTING", "INSTALLING"), "handover": ("INSTALLING", "INSTALLER_CALLINGINIT"),
             "cmdaemon_connected": ("INSTALLER_CALLINGINIT", "UP"), "cmdaemon_lost": ("UP", "DOWN"),
             "installer_error": ("INSTALLING", "INSTALLER_FAILED"), "installer_ping_lost": ("INSTALLING", "INSTALLER_UNREACHABLE"),
             "reboot_for_kernel": ("INSTALLING", "INSTALLER_REBOOTING"), "reboot_too_slow": ("INSTALLER_REBOOTING", "INSTALLER_FAILED"),
             "init_too_slow": ("INSTALLER_CALLINGINIT", "INSTALLER_FAILED")}
        if ev not in t:
            raise ProvError(f"unknown event {ev}")
        frm, to = t[ev]
        if self.base != frm:
            raise ProvError(f"{ev} is not possible from {self.base}")
        self.base = to

    def close(self):
        self.closed = True

    def open(self):
        if not self.closed:
            raise ProvError("node is not closed")
        self.closed = False

    def mute(self):
        self.muted = True

    def unmute(self):
        self.muted = False

def workload_continues(state_closed):
    """5.5.4: CMDaemon stops monitoring a CLOSED node, but the workload manager runs independently, so jobs continue. Drain first (not obligatory)."""
    return True

# ---- 5.4.10 standalone boot ---------------------------------------------------------------------------------------
def standalone_boot_problems(installbootrecord, bios_disk_before_network, bootloader_present, bootif_name):
    """5.4.10: four things must all be true for a node to boot from its own drive."""
    p = []
    if not installbootrecord:
        p.append("installbootrecord is off: no boot record is written to the drive")
    if not bios_disk_before_network:
        p.append("BIOS tries network boot first: PXE is attempted whatever installbootrecord says")
    if not bootloader_present:
        p.append("no working bootloader (default is syslinux; a custom image may need grub)")
    if bootif_name.upper() == "BOOTIF":
        p.append("the interface is still called BOOTIF, which is undefined when booting from the drive: set a kernel name such as eth0")
    return p

# ---- 5.6 exclude lists ---------------------------------------------------------------------------------------------
EXCLUDE_LIST = {"update": ("excludelistupdate", "sync", "image to running node"),
                "install_full": ("excludelistfullinstall", "full", "image to starting node"),
                "install_sync": ("excludelistsyncinstall", "sync", "image to starting node"),
                "grab": ("excludelistgrab", "sync", "running node to image"),
                "grabnew": ("excludelistgrabnew", "full", "running node to image")}
AUTO_EXCLUDED_FS = {"nfs", "lustre", "fuse", "cephfs", "cifs", "panfs", "fhgfs", "beegfs", "glusterfs", "gpfs"}

def _under(path, prefixes):
    return any(path == p.rstrip("/") or path.startswith(p.rstrip("/") + "/") for p in prefixes)

def sync_update(image, node, keep, no_new_files=(), mounts=None):
    """5.6.1 excludelistupdate logic. image and node are dict path->content. `keep` is the first sub-list, `no_new_files` the second.
      path in a list and on the node        -> node content untouched
      path in `keep`, not on the node       -> copied from the image
      path in `no_new_files`, not on node   -> NOT copied
      path in neither list                  -> node content replaced by the image content; node-only files deleted
    mounts: {path: fstype}. Statically imported filesystems of the special list are skipped automatically."""
    skip = [p for p, t in (mounts or {}).items() if t.lower() in AUTO_EXCLUDED_FS]
    out = {}
    for path in set(image) | set(node):
        if _under(path, skip):
            if path in node:
                out[path] = node[path]
            continue
        in_keep, in_nonew = _under(path, keep), _under(path, no_new_files)
        if in_keep or in_nonew:
            if path in node:
                out[path] = node[path]
            elif in_keep and path in image:
                out[path] = image[path]
            continue
        if path in image:
            out[path] = image[path]      # replaced or added; node-only files are not carried over (deleted)
    return out
