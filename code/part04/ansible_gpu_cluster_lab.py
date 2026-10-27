#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.17: Ansible for GPU nodes and clusters."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ansible_gpu_cluster import (
    evaluate_gpu_health_sweep,
    parse_and_gate_nccl_busbw,
    validate_bringup_role_order,
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
    # 1. Section 1 & 2: GPU node bring-up dependency order validation
    good_order = [
        "gpu_facts",
        "base_os",
        "kernel_tuning",
        "mofed",
        "nvidia_driver",
        "fabric_manager",
        "gpu_tuning",
        "dcgm",
        "container_toolkit",
        "gpu_validate",
        "slurm_client",
    ]
    bad_order = [
        "gpu_facts",
        "base_os",
        "nvidia_driver",
        "mofed",  # wrong: mofed after nvidia_driver breaks nvidia-peermem!
        "slurm_client",
        "gpu_validate",  # wrong: scheduler started before validation!
    ]
    v_bad = validate_bringup_role_order(bad_order)
    check(
        "validate_bringup_role_order accepts valid bring-up order and flags mofed-after-driver and scheduler-before-validate",
        validate_bringup_role_order(good_order) == []
        and "mofed must run before nvidia_driver" in v_bad
        and "gpu_validate must run before slurm_client" in v_bad,
    )

    # 2. Section 6: Fleet GPU health-sweep outlier detection (missing GPU, PCIe Gen4x8 degradation, uncorrected ECC)
    healthy_row = "0, NVIDIA H100, 550.90.07, 42, 310.5, 0x0000000000000000, 0, 5, 16"
    sweep = {
        "gpu001": [healthy_row.replace("0, NVIDIA", f"{i}, NVIDIA") for i in range(8)],
        "gpu002": [healthy_row.replace("0, NVIDIA", f"{i}, NVIDIA") for i in range(7)],  # 7 GPUs (1 fallen off bus!)
        "gpu003": [
            *[healthy_row.replace("0, NVIDIA", f"{i}, NVIDIA") for i in range(7)],
            "7, NVIDIA H100, 550.90.07, 48, 320.0, 0x0000000000000000, 2, 4, 8",  # ECC=2 & PCIe Gen4x8!
        ],
    }
    outliers = evaluate_gpu_health_sweep(sweep, expected_gpus=8)
    check(
        "evaluate_gpu_health_sweep passes healthy gpu001 and flags gpu002 (7 GPUs) and gpu003 (uncorrected ECC & PCIe Gen4x8)",
        "gpu001" not in outliers
        and outliers["gpu002"] == ["gpu_count=7 (expected 8)"]
        and len(outliers["gpu003"]) == 2,
    )

    # 3. Section 5: nccl-tests all_reduce_perf Avg bus bandwidth parser and gate
    sample_nccl = "# Out of bounds values : 0 OK\n# Avg bus bandwidth    : 342.85 \n"
    ok_bw, bw = parse_and_gate_nccl_busbw(sample_nccl, min_busbw_gbps=320.0)
    fail_bw, _ = parse_and_gate_nccl_busbw(sample_nccl, min_busbw_gbps=360.0)
    check(
        "parse_and_gate_nccl_busbw extracts 342.85 GB/s, passing >=320 GB/s floor and failing >=360 GB/s floor",
        ok_bw is True and bw == 342.85 and fail_bw is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
