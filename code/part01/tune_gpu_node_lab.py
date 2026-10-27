#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.28: Putting it together: tuning a Linux node for GPU and HPC work."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tune_gpu_node import (
    compute_synchronous_job_step_time,
    evaluate_node_audit,
    parse_sysfs_cpulist,
    resolve_gpu_numa_node,
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
    # 1. sysfs cpulist parsing (Section 7)
    check("parse_sysfs_cpulist('0-3,8,12-14') expands to [0, 1, 2, 3, 8, 12, 13, 14]",
          parse_sysfs_cpulist("0-3,8,12-14") == [0, 1, 2, 3, 8, 12, 13, 14])
    check("parse_sysfs_cpulist('') returns empty list",
          parse_sysfs_cpulist("") == [])

    # 2. 3-tier GPU-to-NUMA lookup fallback chain (Section 7, ASP Ch. 3)
    r_nvml = resolve_gpu_numa_node(nvml_numa_id=1, sysfs_numa_node=0, cli_topo_numa_id=0)
    check("tier 1 (NVML) takes priority when nvmlDeviceGetNUMANodeId returns 1",
          r_nvml == {"numa_node": 1, "source": "1_nvml"})
    r_sysfs = resolve_gpu_numa_node(nvml_numa_id=None, sysfs_numa_node=1, cli_topo_numa_id=0)
    check("tier 2 (sysfs /sys/bus/pci/devices/<bdf>/numa_node) is used when NVML is unavailable",
          r_sysfs == {"numa_node": 1, "source": "2_sysfs"})
    r_neg = resolve_gpu_numa_node(nvml_numa_id=None, sysfs_numa_node=-1, cli_topo_numa_id=None)
    check("sysfs numa_node == -1 normalizes safely to NUMA node 0",
          r_neg["numa_node"] == 0 and r_neg["source"] == "2_sysfs")
    r_cli = resolve_gpu_numa_node(nvml_numa_id=None, sysfs_numa_node=None, cli_topo_numa_id=2)
    check("tier 3 (CLI nvidia-smi topo -m) is used when NVML and sysfs are unavailable",
          r_cli == {"numa_node": 2, "source": "3_cli_topo"})

    # 3. Section 11 node_audit.sh evaluation
    audit_ok = evaluate_node_audit(
        cmdline_tokens=["console=ttyS0,115200n8", "iommu=pt", "numa_balancing=disable"],
        swappiness=1,
        max_map_count=1048576,
        numa_balancing=0,
        thp_mode="madvise",
        memlock_limit="unlimited",
        governor="performance",
        gpu_count=8,
        expected_gpus=8,
        persistence_enabled=True,
        pcie_all_max=True,
        uncorrected_ecc=0,
        fabric_manager_active=True,
        recent_xid_count=0,
    )
    check("properly tuned 8-GPU HGX node passes all 14 node_audit.sh checks",
          audit_ok["passed"] is True and audit_ok["fail_count"] == 0)

    audit_bad = evaluate_node_audit(
        cmdline_tokens=[],
        swappiness=60,
        max_map_count=65530,
        numa_balancing=1,
        thp_mode="always",
        memlock_limit="64",
        governor="powersave",
        gpu_count=7,
        expected_gpus=8,
        persistence_enabled=False,
        pcie_all_max=False,
        uncorrected_ecc=2,
        fabric_manager_active=False,
        recent_xid_count=1,
    )
    check("drifted/degraded node flags all 14 node_audit.sh failure categories",
          audit_bad["passed"] is False and audit_bad["fail_count"] == 14)

    # 4. Synchronous training straggler penalty (Why this matters & Section 13)
    st = compute_synchronous_job_step_time([100.0] * 63 + [125.0])
    check("1 straggler rank at 125 ms slows all 64 synchronous ranks by 25.0%",
          st["effective_job_step_ms"] == 125.0 and st["straggler_penalty_pct"] == 25.0)

    # 5. Case Study (Section 12, SP Ch. 16: The Unexplained 3 to 4x Win)
    check("SP Ch. 16 Case Study: VM load 85 on 48 CPUs vs container host load 18 on 64 CPUs",
          round(85.0 / 48.0 - 1.0, 2) == 0.77 and 18 < 64)
    check("SP Ch. 16 Case Study: VM IPC 0.57 (30% LLC hit, 33 MB LLC) vs container IPC 1.52 (90% LLC hit, 45 MB LLC)",
          round(1.52 / 0.57, 1) == 2.7 and 30 < 90 and 33 < 45)
    check("SP Ch. 16 Case Study: VM ~2,000,000 cs/s (<10 us on-CPU) vs container ~1,000 cs/s (2-4 ms on-CPU)",
          2000000 // 1000 == 2000)

    # 6. Additional checks from Section 5 & 6
    check("local DRAM ~80 ns vs remote NUMA ~140 ns is 1.75x slower",
          round(140.0 / 80.0, 2) == 1.75)
    check("90-gpu-node.conf sets dirty_background_bytes=1 GiB, dirty_bytes=8 GiB, rmem_max=128 MiB",
          1073741824 == 1 << 30 and 8589934592 == 8 * (1 << 30) and 134217728 == 128 * (1 << 20))
    check("compute_synchronous_job_step_time raises ValueError on empty list",
          _raises(lambda: compute_synchronous_job_step_time([])))

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
