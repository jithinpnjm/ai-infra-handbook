"""Chapter 1.19 model: Linux 8 namespace types and clone(2) flags, PID 1 in-namespace
vs parent-namespace signal delivery, OverlayFS lowerdir/upperdir/whiteout resolution
and copy-up byte accounting, and user-namespace uid_map translation.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 17
  ("Virtualization": hypervisors vs containers, Docker vs Podman, Alpine hlw_test
  build, overlay2 mount, networking, LXC, Kubernetes, pitfalls, test-venv).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 11 ("Cloud Computing": OS virtualization namespaces, struct nsproxy,
  ovl_write_iter, observability traps inside containers).
- nvidia-devops/volume-01/04-linux-systemd-containers-masterclass.md.
"""
from typing import Dict, List, Optional, Tuple


NAMESPACE_CLONE_FLAGS: Dict[str, str] = {
    "mnt": "CLONE_NEWNS",
    "pid": "CLONE_NEWPID",
    "net": "CLONE_NEWNET",
    "uts": "CLONE_NEWUTS",
    "ipc": "CLONE_NEWIPC",
    "user": "CLONE_NEWUSER",
    "cgroup": "CLONE_NEWCGROUP",
    "time": "CLONE_NEWTIME",
}


def evaluate_pid1_signal_delivery(
    signal_name: str,
    sent_from_parent_ns: bool,
    pid1_has_custom_handler: bool,
) -> Dict[str, object]:
    """Model Linux PID-namespace PID 1 signal semantics (pid_namespaces(7))."""
    if signal_name in {"SIGKILL", "SIGSTOP"}:
        delivered = sent_from_parent_ns
        reason = "unblockable_from_parent_ns" if sent_from_parent_ns else "ignored_by_pid1_from_inside_ns"
    else:
        if pid1_has_custom_handler:
            delivered = True
            reason = "custom_handler_invoked"
        else:
            delivered = False
            reason = "pid1_has_no_default_signal_action_for_unhandled_signals"
    return {"signal": signal_name, "delivered": delivered, "reason": reason}


def resolve_overlayfs_lookup(
    filename: str,
    upper_files: Dict[str, str],
    whiteouts: List[str],
    lower_layers_top_to_bottom: List[Dict[str, str]],
) -> Optional[str]:
    """Resolve a file lookup across OverlayFS upperdir, whiteouts, and ordered lowerdirs (leftmost is topmost)."""
    if filename in whiteouts:
        return None
    if filename in upper_files:
        return upper_files[filename]
    for layer in lower_layers_top_to_bottom:
        if filename in layer:
            return layer[filename]
    return None


def compute_overlay_copy_up_bytes(lower_file_bytes: int, first_write_bytes: int) -> Dict[str, int]:
    """Compute bytes written to upperdir when modifying a lower-layer file for the first time."""
    if lower_file_bytes < 0 or first_write_bytes < 0:
        raise ValueError("Byte counts must be non-negative")
    return {
        "copy_up_bytes": lower_file_bytes,
        "total_upper_bytes": lower_file_bytes + first_write_bytes,
    }


def translate_userns_uid(
    inside_uid: int,
    uid_map: List[Tuple[int, int, int]],
) -> int:
    """Translate a container UID to a host UID using /proc/PID/uid_map tuples (inside_start, outside_start, length)."""
    for in_start, out_start, length in uid_map:
        if in_start <= inside_uid < in_start + length:
            return out_start + (inside_uid - in_start)
    raise ValueError(f"UID {inside_uid} is not mapped in uid_map")
