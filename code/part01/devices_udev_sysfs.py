"""Chapter 1.10 model: Device nodes (major/minor numbers, block vs char vs pipe vs
socket), udev rule evaluation (==/!= conditionals vs =/+=/ := assignments and
lexical non-terminating evaluation), SCSI [host:channel:target:lun] addressing,
PCIe link degradation detection, and nvidia-smi topo -m hop classification.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 3
  ("Devices": /dev major/minor numbers, sysfs /sys/devices hierarchy, dd, device
  name summary sd*/nvme*/sr*/hd*/tty*/ttyS*/lp0/snd, mknod, devtmpfs + systemd-udevd
  rules and udevadm, SCSI 3-layer stack and lsscsi -g generic /dev/sg* nodes).
- Sergey Zhumatiy, Supercomputers for Linux SysAdmins (SCL), Chapter 7 & Chapter 8
  (/proc and sysctl, udev match/assignment operators and %k/%n/%M/%m variables).
"""
from typing import Dict, List, Tuple


TOPO_RANK_FASTEST_TO_SLOWEST: List[str] = ["NV", "PIX", "PXB", "PHB", "NODE", "SYS"]


def parse_lsscsi_tuple(addr: str) -> Dict[str, int]:
    """Parse an lsscsi '[host:channel:target:lun]' address string into its four integer components."""
    clean = addr.strip().strip("[]")
    parts = clean.split(":")
    if len(parts) != 4:
        raise ValueError(f"Invalid SCSI address tuple: {addr}")
    return {
        "host": int(parts[0]),
        "channel": int(parts[1]),
        "target": int(parts[2]),
        "lun": int(parts[3]),
    }


def evaluate_udev_assignments(
    ops: List[Tuple[str, str]],
) -> Dict[str, object]:
    """Evaluate a sequence of udev assignment operators ('=', '+=', ':=') on a property/symlink list."""
    values: List[str] = []
    locked = False
    for op, val in ops:
        if locked:
            continue
        if op == "=":
            values = [val]
        elif op == "+=":
            values.append(val)
        elif op == ":=":
            values = [val]
            locked = True
        else:
            raise ValueError(f"Unsupported udev assignment operator: {op}")
    return {"values": values, "locked": locked}


def check_pcie_link_health(
    cur_speed_gts: float,
    cur_width: int,
    max_speed_gts: float,
    max_width: int,
) -> Dict[str, object]:
    """Compare current_link_speed/width against max_link_speed/width in sysfs."""
    speed_degraded = cur_speed_gts < max_speed_gts
    width_degraded = cur_width < max_width
    ratio = round((cur_speed_gts * cur_width) / (max_speed_gts * max_width), 3)
    return {
        "healthy": not (speed_degraded or width_degraded),
        "speed_degraded": speed_degraded,
        "width_degraded": width_degraded,
        "bandwidth_ratio": ratio,
    }


def compare_gpu_topo_paths(tag_a: str, tag_b: str) -> str:
    """Compare two nvidia-smi topo -m path labels (e.g. 'NV8', 'PIX', 'PHB', 'SYS') and return the faster one."""
    norm_a = "NV" if tag_a.startswith("NV") else tag_a
    norm_b = "NV" if tag_b.startswith("NV") else tag_b
    if norm_a not in TOPO_RANK_FASTEST_TO_SLOWEST or norm_b not in TOPO_RANK_FASTEST_TO_SLOWEST:
        raise ValueError(f"Unknown topology tags: {tag_a}, {tag_b}")
    idx_a = TOPO_RANK_FASTEST_TO_SLOWEST.index(norm_a)
    idx_b = TOPO_RANK_FASTEST_TO_SLOWEST.index(norm_b)
    if idx_a < idx_b:
        return tag_a
    if idx_b < idx_a:
        return tag_b
    return "equal"


def sysctl_key_to_proc_sys_path(key: str) -> str:
    """Convert a dotted sysctl key (e.g. 'net.ipv4.ip_forward') to its /proc/sys path."""
    if not key or "." not in key:
        raise ValueError(f"Invalid sysctl key: {key}")
    return "/proc/sys/" + key.replace(".", "/")
