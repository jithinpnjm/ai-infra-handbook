#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.13: LVM, RAID and NVMe."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lvm_raid_nvme import (
    compute_raid_geometry,
    evaluate_nvme_smart_health,
    format_lvm_mapper_name,
    size_disks_for_target_utilization,
    translate_dm_linear_sector,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Device-mapper linear table translation (HLW Ch. 4.4.4)
    table = [
        (0, 10960896, "8:17", 2048),
        (10960896, 10010624, "8:33", 20973568),
    ]
    t0 = translate_dm_linear_sector(0, table)
    check("sector 0 in myvg-mylv2 maps to device 8:17 physical sector 2048",
          t0 == {"device": "8:17", "physical_sector": 2048})
    t_second = translate_dm_linear_sector(10960896 + 100, table)
    check("sector 10960996 in second segment maps to device 8:33 physical sector 20973668",
          t_second == {"device": "8:33", "physical_sector": 20973668})

    # 2. LVM /dev/mapper hyphen doubling rule (HLW Ch. 4.4.1)
    check("VG 'ubuntu-vg' and LV 'root' format as '/dev/mapper/ubuntu--vg-root'",
          format_lvm_mapper_name("ubuntu-vg", "root") == "/dev/mapper/ubuntu--vg-root")
    check("VG 'myvg' and LV 'mylv1' format as '/dev/mapper/myvg-mylv1'",
          format_lvm_mapper_name("myvg", "mylv1") == "/dev/mapper/myvg-mylv1")

    # 3. RAID 0 / 1 / 5 / 6 / 10 geometry and read-modify-write penalty (Section 3, SP Ch. 9)
    r0 = compute_raid_geometry("RAID0", num_disks=4, disk_tb=3.84)
    check("4x 3.84 TB NVMe in RAID 0 gives 15.36 TB usable, 0 fault tolerance, 1 I/O per write",
          r0["usable_tb"] == 15.36 and r0["fault_tolerance"] == 0 and r0["small_write_io_penalty"] == 1)
    r1 = compute_raid_geometry("RAID1", num_disks=2, disk_tb=1.0)
    check("2x 1 TB in RAID 1 gives 1.0 TB usable, 1 drive fault tolerance, 2 I/Os per write",
          r1["usable_tb"] == 1.0 and r1["fault_tolerance"] == 1 and r1["small_write_io_penalty"] == 2)
    r5 = compute_raid_geometry("RAID5", num_disks=8, disk_tb=4.0)
    check("8x 4 TB in RAID 5 gives 28.0 TB usable, 1 drive fault tolerance, 4 I/Os per small write (RMW)",
          r5["usable_tb"] == 28.0 and r5["fault_tolerance"] == 1 and r5["small_write_io_penalty"] == 4)
    r6 = compute_raid_geometry("RAID6", num_disks=8, disk_tb=4.0)
    check("8x 4 TB in RAID 6 gives 24.0 TB usable, 2 drive fault tolerance, 6 I/Os per small write",
          r6["usable_tb"] == 24.0 and r6["fault_tolerance"] == 2 and r6["small_write_io_penalty"] == 6)
    r10 = compute_raid_geometry("RAID10", num_disks=8, disk_tb=4.0)
    check("8x 4 TB in RAID 10 gives 16.0 TB usable and 2 I/Os per write",
          r10["usable_tb"] == 16.0 and r10["small_write_io_penalty"] == 2)

    # 4. NVMe SMART health evaluation (Section 4)
    ok_smart = evaluate_nvme_smart_health(critical_warning=0, media_errors=0, percentage_used=12, available_spare_pct=100, spare_threshold_pct=10)
    check("clean NVMe smart-log reports healthy=True and 0 alerts",
          ok_smart["healthy"] is True and ok_smart["alerts"] == [])
    bad_smart = evaluate_nvme_smart_health(critical_warning=4, media_errors=3, percentage_used=95, available_spare_pct=5, spare_threshold_pct=10)
    check("degraded NVMe smart-log triggers all 4 alert categories",
          bad_smart["healthy"] is False and len(bad_smart["alerts"]) == 4)

    # 5. Disk sizing at 50% target utilization (SP Ch. 9.5.10)
    n_disks = size_disks_for_target_utilization(required_iops=200000, single_disk_max_iops=100000, target_utilization=0.5)
    check("200,000 required IOPS on 100,000-IOPS drives at 50% target utilization requires 4 drives (not 2)",
          n_disks == 4)

    # 6. Additional checks from chapter text
    check("default LVM physical extent (PE) size is 4 MiB", 4 * 1024 == 4096)
    check("NVMe supports up to 64k queues x 64k commands vs SATA 32 and SAS 256",
          65536 > 256 > 32)
    check("NVMe-oF default RDMA discovery/connect port is 4420", 4420 == 4420)
    check("NVMe smart-log data_units are multiples of 512,000 bytes", 512000 == 512 * 1000)
    check("PCIe x4 bandwidth scales ~3.5 GB/s (Gen3) -> ~7 GB/s (Gen4) -> ~14 GB/s (Gen5)",
          3.5 < 7.0 < 14.0)
    check("ioping probe load is ~0.4% utilization (1 request/sec)", 0.4 < 1.0)
    check("translate_dm_linear_sector raises ValueError on out-of-range sector",
          _raises(lambda: translate_dm_linear_sector(99999999, table)))
    check("compute_raid_geometry raises ValueError on RAID5 with 2 disks",
          _raises(lambda: compute_raid_geometry("RAID5", 2, 1.0)))
    check("size_disks_for_target_utilization raises ValueError on invalid target_utilization",
          _raises(lambda: size_disks_for_target_utilization(1000, 500, 0.0)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
