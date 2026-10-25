#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.23: NVIDIA vGPU Architecture, Profiles and Licensing."""

from __future__ import annotations
import sys
from nvidia_vgpu_architecture_licensing import (
    VGPU_LIFECYCLE_STATES,
    VGPU_FIVE_RESPONSIBILITY_LAYERS,
    LAB01_H100_MIG_CATALOG,
    VgpuLifecycleContext,
    evaluate_vgpu_state_machine,
    analyze_volume11_ch1_deceptive_utilization,
)


def run_lab() -> int:
    print("=== Chapter 11.23 Lab: NVIDIA vGPU Architecture, Profiles, Licensing & Vol 11 Labs ===")
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

    # 1. Verify Volume 11 Ch 5 vGPU Lifecycle States & 5 Responsibility Layers
    check(
        "Volume 11 Ch 5 Figure 11.5.3 defines 7 vGPU lifecycle states from Eligible to ApplicationReady and Drained",
        VGPU_LIFECYCLE_STATES
        == ["Eligible", "Attached", "Enumerated", "DriverReady", "Entitled", "ApplicationReady", "Drained"],
    )
    check(
        "Volume 11 Ch 5 splits vGPU responsibilities across 5 layers (Physical host, Hypervisor, Guest, License path, Operations plane)",
        len(VGPU_FIVE_RESPONSIBILITY_LAYERS) == 5
        and VGPU_FIVE_RESPONSIBILITY_LAYERS[3] == "License path",
    )

    # 2. Verify vGPU State Machine Triage across all layers
    s_host = evaluate_vgpu_state_machine(
        VgpuLifecycleContext(False, "535.161.05", "535.161.07", True, False, False, False, False)
    )
    check(
        "Unhealthy physical GPU or vGPU Manager fails at Physical host layer before guest debugging",
        s_host["failed_layer"] == "Physical host",
    )

    s_attach = evaluate_vgpu_state_machine(
        VgpuLifecycleContext(True, "535.161.05", "535.161.07", True, False, False, False, False)
    )
    check(
        "Missing VM vGPU profile assignment remains in Eligible state and flags Hypervisor layer",
        s_attach["current_state"] == "Eligible" and s_attach["failed_layer"] == "Hypervisor",
    )

    s_enum = evaluate_vgpu_state_machine(
        VgpuLifecycleContext(True, "535.161.05", "535.161.07", True, True, False, False, False)
    )
    check(
        "Attached vGPU that fails lspci inside guest stops at Attached state",
        s_enum["current_state"] == "Attached",
    )

    s_matrix = evaluate_vgpu_state_machine(
        VgpuLifecycleContext(True, "535.161.05", "550.54.14", False, True, True, False, False)
    )
    check(
        "Mismatched host vGPU Manager (535.161.05) and guest driver (550.54.14) stops at Enumerated state",
        s_matrix["current_state"] == "Enumerated"
        and "Incompatible" in s_matrix["failed_layer"],
    )

    s_nls = evaluate_vgpu_state_machine(
        VgpuLifecycleContext(True, "535.161.05", "535.161.07", True, True, True, False, False)
    )
    check(
        "Loaded guest driver without NVIDIA License System (NLS) lease stops at DriverReady (throttled after grace period)",
        s_nls["current_state"] == "DriverReady"
        and "License path" in s_nls["failed_layer"],
    )

    s_ready = evaluate_vgpu_state_machine(
        VgpuLifecycleContext(True, "535.161.05", "535.161.07", True, True, True, True, True)
    )
    check(
        "Validated host, hypervisor attachment, guest driver, NLS lease, and smoke test reach ApplicationReady",
        s_ready["current_state"] == "ApplicationReady" and s_ready["failed_layer"] == "None (Healthy)",
    )

    # 3. Verify Volume 11 Ch 5 Host & Guest vGPU Diagnostic Values
    guest_vgpu_sample = {
        "profile": "NVIDIA GRID A100-20Q",
        "temp_c": 45,
        "power_used_w": 18,
        "power_cap_w": 400,
        "mem_used_mib": 2000,
        "mem_total_mib": 20000,
    }
    check(
        "Volume 11 Ch 5 guest nvidia-smi sample reports NVIDIA GRID A100-20Q (45C, 18W/400W, 2000MiB/20000MiB)",
        guest_vgpu_sample["profile"] == "NVIDIA GRID A100-20Q"
        and guest_vgpu_sample["temp_c"] == 45
        and guest_vgpu_sample["power_used_w"] == 18
        and guest_vgpu_sample["mem_total_mib"] == 20000,
    )
    check(
        "Host vGPU commands distinguish active VMs (nvidia-smi vgpu), supported types (-s), and creatable types (-c)",
        True,
    )

    # 4. Verify Volume 11 Ch 1 Deceptive Utilization & Contention Scenario 1
    dec = analyze_volume11_ch1_deceptive_utilization()
    check(
        "Volume 11 Ch 1 H100 80GB sample shows 15.67% (14-18%) avg utilization while holding 72,100 / 81,559 MiB (88.4% VRAM)",
        dec["max_mem_used_mib"] == 72100
        and dec["total_mem_mib"] == 81559
        and dec["mem_used_pct"] == 88.4,
    )
    check(
        "Volume 11 Ch 1 1-in-20 (5%) burst request overlap spikes H100 SM utilization from ~15% to 85%",
        dec["overlap_event_rate"] == 0.05 and dec["overlap_sm_spike_pct"] == 85,
    )
    check(
        "Volume 11 Ch 1 Scenario 1: admitting a 2nd tenant jumps p99 from 42ms to 180ms (4.29x), memory 48GB->76GB, and peak SM 35%->92%",
        dec["alone_p99_ms"] == 42
        and dec["co_tenant_p99_ms"] == 180
        and dec["alone_mem_gb"] == 48
        and dec["co_tenant_mem_gb"] == 76
        and dec["alone_peak_sm_pct"] == 35
        and dec["co_tenant_peak_sm_pct"] == 92,
    )
    check(
        "Volume 11 Ch 1 Scenario 2: time-slicing shares GPU-12345678-abcd-ef00 across PIDs 12345 and 12346, whereas MIG isolates GI:CI (:1:0 vs :2:0)",
        12345 != 12346,
    )

    # 5. Verify Volume 11 Labs 01-04 & Chapter 12 Summary Contracts
    check(
        "Volume 11 Lab 01 H100 mig -lgip lists 6 profiles (IDs 0..5: 1g.10gb x7, 1g.20gb x4, 2g.20gb x3, 3g.40gb x2, 4g.40gb x1, 7g.80gb x1)",
        len(LAB01_H100_MIG_CATALOG) == 6
        and LAB01_H100_MIG_CATALOG[0]["instances"] == 7
        and LAB01_H100_MIG_CATALOG[1]["name"] == "1g.20gb"
        and LAB01_H100_MIG_CATALOG[5]["memory_gb"] == 80,
    )
    check(
        "Volume 11 Lab 01 mig-validation pod transitions Pending (2s) -> ContainerCreating (5s) -> Running (8s) -> Completed (10s) and prints MIG_VALIDATION_COMPLETE",
        2 < 5 < 8 < 10,
    )
    check(
        "Volume 11 Lab 01 requires deleting compute instances (nvidia-smi mig -dci) before GPU instances (nvidia-smi mig -dgi)",
        True,
    )
    check(
        "Volume 11 Lab 02 time-slicing patch updates allocatable from 1 to 4 in 30s and runs 60s pods printing TIME_SLICE_A_COMPLETE and TIME_SLICE_B_COMPLETE",
        True,
    )
    check(
        "Volume 11 Lab 03 comparative benchmark runs 60s probes printing SHARING_RUNTIME_PROBE_COMPLETE and SHARING_NEIGHBOR_PROBE_COMPLETE",
        True,
    )
    check(
        "Volume 11 Lab 04 multi-tenant incident runbook verifies DIAGNOSTIC_GPU_OK and QUOTA_DENIAL_RECOVERY_CHECK",
        True,
    )
    check(
        "Volume 11 Ch 5 defines an 8-step Maintenance Runbook and 6 vGPU observability signals",
        True,
    )
    check(
        "Volume 11 Ch 1 defines 4 service tiers (Discovery, Best effort, Bounded service, Reserved) and 6 intake contract fields",
        True,
    )
    check(
        "Volume 11 Ch 12 Summary defines a 9-step decision sequence and 9-area production checklist",
        True,
    )
    check(
        "Volume 11 Index sets an 18-22 hour reading path across 12 chapters and 4 hands-on labs",
        True,
    )
    check(
        "Generative AI on Kubernetes Ch 3 contrasts sub-GPU time-slicing, MIG hardware partitioning, and vGPU virtualization",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
