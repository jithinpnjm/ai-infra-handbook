#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.18: Scheduling in depth: kube-scheduler, affinity, taints, priority and preemption."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu_scheduler_simulator import (
    allocate_dra_same_pcie_root,
    evaluate_kueue_cohort_gang_admission,
    simulate_gpu_placement_and_fragmentation,
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
    # 1. Section 1 & 2: LeastAllocated (spread) fragments 2x8-GPU nodes so an 8-GPU pod is Pending, whereas MostAllocated (bin-pack) fits all
    # Two 8-GPU nodes (16 GPUs total); schedule two 4-GPU inference pods, then one 8-GPU training pod
    res_spread = simulate_gpu_placement_and_fragmentation([8, 8], [4, 4, 8], strategy="LeastAllocated")
    res_binpack = simulate_gpu_placement_and_fragmentation([8, 8], [4, 4, 8], strategy="MostAllocated")
    check(
        "LeastAllocated spreads two 4-GPU pods across both 8-GPU nodes (leaving 8-GPU pod Pending), whereas MostAllocated bin-packs them on Node 0 and schedules the 8-GPU pod on Node 1",
        res_spread["unschedulable_pods"] == 1
        and res_spread["free_per_node"] == [4, 4]
        and res_binpack["unschedulable_pods"] == 0
        and res_binpack["free_per_node"] == [0, 0],
    )

    # 2. Section 5: Kueue ClusterQueue cohort borrowing & gang admission
    ok_admit, _ = evaluate_kueue_cohort_gang_admission(
        nominal_quota=128,
        borrowing_limit=64,
        current_used=96,
        cohort_lendable_free=48,
        workload_total_gpus=64,  # 96 + 64 = 160 -> borrows 32 <= 64 limit & <= 48 cohort free
    )
    ok_reject, _ = evaluate_kueue_cohort_gang_admission(
        nominal_quota=128,
        borrowing_limit=64,
        current_used=96,
        cohort_lendable_free=16,  # cohort only has 16 free, needs 32 -> queued!
        workload_total_gpus=64,
    )
    check(
        "Kueue admits 64-GPU gang workload when cohort has 48 lendable GPUs and holds it suspended when cohort only has 16",
        ok_admit is True and ok_reject is False,
    )

    # 3. Section 6: DRA ResourceClaimTemplate same-pcieRoot constraint
    devices = [
        {"name": "gpu0", "productName": "NVIDIA H100 80GB HBM3", "pcieRoot": "pci0000:00", "free": True},
        {"name": "gpu1", "productName": "NVIDIA H100 80GB HBM3", "pcieRoot": "pci0000:00", "free": True},
        {"name": "gpu2", "productName": "NVIDIA H100 80GB HBM3", "pcieRoot": "pci0000:80", "free": True},
        {"name": "gpu3", "productName": "NVIDIA H100 80GB HBM3", "pcieRoot": "pci0000:80", "free": True},
        {"name": "gpu4", "productName": "NVIDIA H100 80GB HBM3", "pcieRoot": "pci0000:80", "free": True},
        {"name": "gpu5", "productName": "NVIDIA H100 80GB HBM3", "pcieRoot": "pci0000:80", "free": True},
    ]
    allocated = allocate_dra_same_pcie_root(devices, required_count=4)
    check(
        "allocate_dra_same_pcie_root selects 4 H100 GPUs sharing pcieRoot 'pci0000:80' (gpu2..gpu5)",
        allocated == ["gpu2", "gpu3", "gpu4", "gpu5"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
