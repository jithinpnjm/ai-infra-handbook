"""Chapter 1.13 model: LVM extent allocation and dmsetup linear sector mapping,
RAID 0 / 1 / 5 / 6 / 10 usable capacity, fault tolerance, and small-write parity
I/O penalty, NVMe SMART health evaluation (critical_warning, media_errors,
percentage_used), and 50%-target disk capacity scaling.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 4
  (section 4.4 "Logical Volume Manager": PV, VG, PE 4 MiB, LV, devmapper /dev/dm-*
  and /dev/mapper/VG-LV with doubled dashes, dmsetup table linear sector mapping).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 9 ("Disks": RAID levels and read-modify-write penalty, NVMe queues,
  USE method, 50% utilization scaling rule, ioping/fio/biolatency).
- nvidia-devops/volume-01/02-linux-storage-io-masterclass.md and
  nvidia-zero-to-hero/volume-15/chapter-01..03 (8-layer storage-to-GPU path,
  local NVMe epoch caching and checkpoint staging).
"""
import math
from typing import Dict, List, Tuple


def translate_dm_linear_sector(
    logical_sector: int,
    table: List[Tuple[int, int, str, int]],
) -> Dict[str, object]:
    """Translate a logical 512-byte sector through a dmsetup linear mapping table: (start, length, dev, dev_offset)."""
    for start, length, dev, dev_offset in table:
        if start <= logical_sector < start + length:
            phys_sector = dev_offset + (logical_sector - start)
            return {"device": dev, "physical_sector": phys_sector}
    raise ValueError(f"Sector {logical_sector} outside mapped table range")


def compute_raid_geometry(level: str, num_disks: int, disk_tb: float) -> Dict[str, object]:
    """Compute usable capacity (TB), fault tolerance (drives), and small-write I/O ops per logical write."""
    if num_disks < 2 or disk_tb <= 0:
        raise ValueError("num_disks must be >= 2 and disk_tb > 0")
    if level == "RAID0":
        return {"usable_tb": round(num_disks * disk_tb, 2), "fault_tolerance": 0, "small_write_io_penalty": 1}
    if level == "RAID1":
        return {"usable_tb": round(disk_tb, 2), "fault_tolerance": num_disks - 1, "small_write_io_penalty": num_disks}
    if level == "RAID5":
        if num_disks < 3:
            raise ValueError("RAID5 requires at least 3 disks")
        return {"usable_tb": round((num_disks - 1) * disk_tb, 2), "fault_tolerance": 1, "small_write_io_penalty": 4}
    if level == "RAID6":
        if num_disks < 4:
            raise ValueError("RAID6 requires at least 4 disks")
        return {"usable_tb": round((num_disks - 2) * disk_tb, 2), "fault_tolerance": 2, "small_write_io_penalty": 6}
    if level == "RAID10":
        if num_disks < 4 or num_disks % 2 != 0:
            raise ValueError("RAID10 requires an even number of at least 4 disks")
        return {"usable_tb": round((num_disks / 2.0) * disk_tb, 2), "fault_tolerance": 1, "small_write_io_penalty": 2}
    raise ValueError(f"Unsupported RAID level: {level}")


def evaluate_nvme_smart_health(
    critical_warning: int,
    media_errors: int,
    percentage_used: int,
    available_spare_pct: int,
    spare_threshold_pct: int,
) -> Dict[str, object]:
    """Evaluate nvme smart-log fields and return alert reasons."""
    alerts: List[str] = []
    if critical_warning != 0:
        alerts.append("critical_warning_nonzero")
    if media_errors > 0:
        alerts.append("media_errors_detected")
    if percentage_used >= 90:
        alerts.append("endurance_wear_high")
    if available_spare_pct <= spare_threshold_pct:
        alerts.append("available_spare_below_threshold")
    return {"healthy": len(alerts) == 0, "alerts": alerts}


def format_lvm_mapper_name(vg_name: str, lv_name: str) -> str:
    """Format /dev/mapper/VG-LV name by doubling internal hyphens in vg_name and lv_name."""
    vg_escaped = vg_name.replace("-", "--")
    lv_escaped = lv_name.replace("-", "--")
    return f"/dev/mapper/{vg_escaped}-{lv_escaped}"


def size_disks_for_target_utilization(
    required_iops: int,
    single_disk_max_iops: int,
    target_utilization: float = 0.5,
) -> int:
    """Size disk count at 50% target utilization (SP Ch. 9.5.10) to avoid queueing latency spikes."""
    if required_iops <= 0 or single_disk_max_iops <= 0 or not (0.0 < target_utilization <= 1.0):
        raise ValueError("Invalid sizing parameters")
    usable_per_disk = single_disk_max_iops * target_utilization
    return int(math.ceil(required_iops / usable_per_disk))
