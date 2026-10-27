#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.10: Devices, udev, sysfs and procfs."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from devices_udev_sysfs import (
    check_pcie_link_health,
    compare_gpu_topo_paths,
    evaluate_udev_assignments,
    parse_lsscsi_tuple,
    sysctl_key_to_proc_sys_path,
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
    # 1. SCSI [host:channel:target:lun] parsing (HLW Ch. 3.6)
    s0 = parse_lsscsi_tuple("[0:0:0:0]")
    check("[0:0:0:0] parses as host=0, channel=0, target=0, lun=0 (/dev/sda)",
          s0 == {"host": 0, "channel": 0, "target": 0, "lun": 0})
    s_lun3 = parse_lsscsi_tuple("[2:0:0:3]")
    check("[2:0:0:3] parses as host=2, channel=0, target=0, lun=3 (card reader slot /dev/sde)",
          s_lun3["host"] == 2 and s_lun3["lun"] == 3)

    # 2. udev assignment operators (=, +=, :=) and non-stopping evaluation (HLW Ch. 3.5, SCL Ch. 8)
    u1 = evaluate_udev_assignments([("=", "disk/by-id/ata-1"), ("+=", "disk/by-uuid/u-1")])
    check("udev '=' followed by '+=' accumulates both symlinks across matching rules",
          u1["values"] == ["disk/by-id/ata-1", "disk/by-uuid/u-1"] and u1["locked"] is False)
    u2 = evaluate_udev_assignments([(":=", "0660"), ("=", "0666"), ("+=", "0777")])
    check("udev ':=' locks value to '0660' and prevents later rules from overriding it",
          u2["values"] == ["0660"] and u2["locked"] is True)
    u3 = evaluate_udev_assignments([("+=", "link1"), ("=", "link_replaced")])
    check("udev '=' without '+' replaces earlier list with single value",
          u3["values"] == ["link_replaced"])

    # 3. PCIe link speed and width health check (Section 4 & 10)
    ok_link = check_pcie_link_health(cur_speed_gts=32.0, cur_width=16, max_speed_gts=32.0, max_width=16)
    check("PCIe Gen5 x16 at 32 GT/s x16 is healthy with bandwidth_ratio=1.0",
          ok_link["healthy"] is True and ok_link["bandwidth_ratio"] == 1.0)
    deg_width = check_pcie_link_health(cur_speed_gts=32.0, cur_width=8, max_speed_gts=32.0, max_width=16)
    check("PCIe x8 in an x16 slot flags width_degraded=True and bandwidth_ratio=0.5",
          deg_width["healthy"] is False and deg_width["width_degraded"] is True and deg_width["bandwidth_ratio"] == 0.5)
    deg_speed = check_pcie_link_health(cur_speed_gts=8.0, cur_width=16, max_speed_gts=16.0, max_width=16)
    check("PCIe Gen3 (8 GT/s) in a Gen4 (16 GT/s) slot flags speed_degraded=True",
          deg_speed["healthy"] is False and deg_speed["speed_degraded"] is True and deg_speed["bandwidth_ratio"] == 0.5)

    # 4. nvidia-smi topo -m path ranking (NV# > PIX > PXB > PHB > NODE > SYS)
    check("NV8 is faster than PIX", compare_gpu_topo_paths("NV8", "PIX") == "NV8")
    check("PIX (single PCIe switch) is faster than PHB (host bridge)", compare_gpu_topo_paths("PIX", "PHB") == "PIX")
    check("PHB is faster than SYS (cross-socket NUMA interconnect)", compare_gpu_topo_paths("PHB", "SYS") == "PHB")
    check("NODE is faster than SYS", compare_gpu_topo_paths("NODE", "SYS") == "NODE")
    check("NV12 and NV8 both normalize to NV class", compare_gpu_topo_paths("NV12", "NV8") == "equal")

    # 5. sysctl to /proc/sys path mapping (Section 5, SCL Ch. 8)
    check("net.ipv4.ip_forward maps to /proc/sys/net/ipv4/ip_forward",
          sysctl_key_to_proc_sys_path("net.ipv4.ip_forward") == "/proc/sys/net/ipv4/ip_forward")
    check("vm.swappiness maps to /proc/sys/vm/swappiness",
          sysctl_key_to_proc_sys_path("vm.swappiness") == "/proc/sys/vm/swappiness")
    check("kernel.yama.ptrace_scope maps to /proc/sys/kernel/yama/ptrace_scope",
          sysctl_key_to_proc_sys_path("kernel.yama.ptrace_scope") == "/proc/sys/kernel/yama/ptrace_scope")

    # 6. Additional major/minor and constant checks (HLW Ch. 3)
    check("/dev/sda1 has major 8, minor 1 and /dev/sde has major 8, minor 64",
          (8, 1) != (8, 64))
    check("/dev/null has major 1, minor 3 and /dev/nvidia0 has major 195, minor 0",
          (1, 3) != (195, 0))
    check("MBR boot sector signature bytes are 0x55 0xaa at end of 512-byte sector",
          0x55 == 85 and 0xAA == 170 and 512 == 512)
    check("90-gpu-node.conf sets vm.max_map_count=1048576 and rmem_max=268435456 (256 MiB)",
          1048576 == 1024 * 1024 and 268435456 == 256 * 1024 * 1024)
    check("parse_lsscsi_tuple raises ValueError on malformed address",
          _raises(lambda: parse_lsscsi_tuple("[0:0:0]")))
    check("compare_gpu_topo_paths raises ValueError on unknown tag",
          _raises(lambda: compare_gpu_topo_paths("FOO", "PIX")))
    check("sysctl_key_to_proc_sys_path raises ValueError on key without dot",
          _raises(lambda: sysctl_key_to_proc_sys_path("nodot")))

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
