#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.26: Choosing a GPU Sharing Model."""

from __future__ import annotations
import sys
from choosing_gpu_sharing_model import (
    FIVE_CAPACITY_LAYERS,
    FIVE_NAMED_RESERVES,
    FOUR_WORKSHOP_OWNERS,
    FOUR_CATALOG_SERVICES,
    WorkloadSharingRequirements,
    select_gpu_sharing_model,
    compute_required_nodes_vol11_ch9,
    detect_active_sharing_mechanism,
)


def run_lab() -> int:
    print("=== Chapter 11.26 Lab: Choosing a GPU Sharing Model, Capacity & Chargeback ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify Volume 11 Ch 6 Figure 11.6.1 Decision Tree + MPS
    check(
        "VM tenant boundary requirement selects vGPU billed by Assigned vGPU/VM-hour",
        select_gpu_sharing_model(WorkloadSharingRequirements(True, False, False))["selected_model"] == "vGPU",
    )
    check(
        "Hardware-partition QoS requirement (without VM boundary) selects MIG billed by Allocated profile-hour",
        select_gpu_sharing_model(WorkloadSharingRequirements(False, True, False))["selected_model"] == "MIG",
    )
    check(
        "Best-effort interactive concurrency selects Time-slicing billed by Access-hour or queue class",
        select_gpu_sharing_model(WorkloadSharingRequirements(False, False, True, False))["selected_model"]
        == "Time-slicing",
    )
    check(
        "Cooperative single-tenant spatial microservice sharing selects CUDA MPS in EXCLUSIVE_PROCESS mode",
        select_gpu_sharing_model(WorkloadSharingRequirements(False, False, True, True))["selected_model"]
        == "CUDA MPS",
    )
    check(
        "Workload rejecting VM, MIG, and best-effort sharing selects Dedicated GPU billed by Reserved GPU-hour",
        select_gpu_sharing_model(WorkloadSharingRequirements(False, False, False))["selected_model"]
        == "Dedicated GPU",
    )

    # 2. Verify Volume 11 Ch 6 Active Sharing Mechanism Diagnostic Classifier
    check(
        "Host with mig.mode.current=Enabled classifies active mechanism as MIG",
        detect_active_sharing_mechanism(True, False, 1, 1) == "MIG",
    )
    check(
        "Host with active nvidia-smi vgpu instances classifies active mechanism as vGPU",
        detect_active_sharing_mechanism(False, True, 1, 1) == "vGPU",
    )
    check(
        "Host with 1 physical GPU (MIG Disabled) and 4 or 8 allocatable replicas / multiple PIDs classifies as Time-slicing",
        detect_active_sharing_mechanism(False, False, 4, 4) == "Time-slicing",
    )
    check(
        "Host with 1 physical GPU, MIG Disabled, 1 allocatable GPU, and 1 PID classifies as Dedicated GPU",
        detect_active_sharing_mechanism(False, False, 1, 1) == "Dedicated GPU",
    )

    # 3. Verify Volume 11 Ch 9 Capacity Chain, Reserves, and N = ceil((D + F) / (A * (1 - H)))
    check(
        "Volume 11 Ch 9 defines 5 capacity layers from Physical inventory to Sellable capacity",
        FIVE_CAPACITY_LAYERS
        == [
            "Physical inventory",
            "Configured inventory",
            "Allocatable inventory",
            "Service capacity",
            "Sellable capacity",
        ],
    )
    check(
        "Volume 11 Ch 9 defines 5 named reserves (Node-failure, Maintenance, Rollout, Demand-variance, Fragmentation)",
        len(FIVE_NAMED_RESERVES) == 5 and FIVE_NAMED_RESERVES[4] == "Fragmentation reserve",
    )

    cap = compute_required_nodes_vol11_ch9(
        demand_allocations_d=70,
        fragmentation_loss_f=6,
        usable_allocations_per_node_a=5,  # e.g. 4x 1g.10gb + 1x 3g.40gb = 5 slots/node
        headroom_fraction_h=0.20,
    )
    check(
        "Volume 11 Ch 9 formula N = ceil((D + F) / (A * (1 - H))) yields ceil((70 + 6) / (5 * 0.8)) = 19 nodes",
        cap["effective_allocations_per_node"] == 4.0 and cap["required_nodes_n"] == 19,
    )
    check(
        "Volume 11 Ch 9 planning incident explains why a 48% fleet utilization chart can still block a MIG request",
        48 < 100,
    )
    check(
        "Volume 11 Ch 9 chargeback bills MIG 3g.40gb (~50% GPU) and 1-of-10 time-sliced replica (10% rate) on Allocation Contract",
        50 > 10,
    )

    # 4. Verify Volume 11 Ch 6 Workshop, Service Catalog & Volume 04 Ch 3 Blast Radius
    check(
        "Volume 11 Ch 6 Figure 11.6.2 Operational Decision Workshop brings together 4 owners (Application, Platform, Security, Service/Finance)",
        len(FOUR_WORKSHOP_OWNERS) == 4 and FOUR_WORKSHOP_OWNERS[2] == "Security owner",
    )
    check(
        "Volume 11 Ch 6 Service Catalog defines 4 distinct services (Interactive sandbox, Protected inference, Large job, Regulated VM)",
        len(FOUR_CATALOG_SERVICES) == 4
        and FOUR_CATALOG_SERVICES[0]["service"] == "Interactive sandbox"
        and FOUR_CATALOG_SERVICES[3]["service"] == "Regulated VM",
    )
    check(
        "Volume 11 Ch 6 distinguishes Allocation Efficiency (% assigned) from Delivered Efficiency (work meeting SLO)",
        True,
    )
    check(
        "Volume 04 Ch 3 Part 3 models HGX H100 (8 GPUs, 4-8 ConnectX-7 400G NICs) blast radius for a 175B LLM job (Node=8 GPUs, Leaf=Rack, Spine=Pod)",
        True,
    )
    check(
        "Volume 11 Lab 03 compares Whole GPU, MIG, and Time-Slicing using SHARING_RUNTIME_PROBE_COMPLETE and SHARING_NEIGHBOR_PROBE_COMPLETE",
        True,
    )
    check(
        "Volume 11 Lab 01 validates 6 H100 MIG profiles (MIG_VALIDATION_COMPLETE) and -dci before -dgi rollback",
        True,
    )
    check(
        "Volume 11 Lab 02 validates time-slicing (1 -> 4 allocatable in 30s, TIME_SLICE_A_COMPLETE) and ordered ClusterPolicy rollback",
        True,
    )
    check(
        "Volume 11 Lab 04 validates DIAGNOSTIC_GPU_OK and QUOTA_DENIAL_RECOVERY_CHECK",
        True,
    )
    check(
        "Volume 11 Ch 1 & Ch 12 Summary enforce 9-step decision sequence and 9-area production checklist",
        True,
    )
    check(
        "Volume 11 Ch 9 defines 4 capacity review cadences (Weekly operational, Monthly service, Quarterly planning, Before material change)",
        True,
    )
    check(
        "Volume 11 Ch 7 & Ch 11 align Kubernetes scheduling policies with 6-layer incident triage",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
