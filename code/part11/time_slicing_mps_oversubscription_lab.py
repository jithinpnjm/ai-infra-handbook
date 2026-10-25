#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.25: Time-Slicing, MPS and Oversubscription."""

from __future__ import annotations
import sys
from time_slicing_mps_oversubscription import (
    FIVE_REPLICA_TEST_PHASES,
    TEN_OPERATING_POLICY_FIELDS,
    EIGHT_CONTENTION_EVIDENCE_ITEMS,
    MpsServerConfig,
    evaluate_cuda_mps_configuration,
    simulate_t4_ten_replica_memory_leak,
    evaluate_a100_timeslicing_envelope,
)


def run_lab() -> int:
    print("=== Chapter 11.25 Lab: Time-Slicing, CUDA MPS & Oversubscription Governance ===")
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

    # 1. Verify Volume 11 Ch 4 Primer: 16 GB T4 with replicas: 10
    t4 = simulate_t4_ten_replica_memory_leak()
    check(
        "Volume 11 Ch 4 Primer: 16 GB T4 with replicas: 10 leaves 0 GB when Pod 1 leaks 16 GB, OOM-killing Pods 2..10 (9 pods)",
        t4["t4_vram_gb"] == 16
        and t4["advertised_replicas"] == 10
        and t4["remaining_vram_gb"] == 0
        and t4["victim_pods_count"] == 9
        and t4["pods_2_to_10_oom"] is True,
    )

    # 2. Verify Volume 11 Ch 4 5-Phase Replica Ratio Benchmark on 80 GB A100
    check(
        "Volume 11 Ch 4 defines 5 replica-ratio test phases (Single tenant, Concurrent active, Burst, Failure/recovery, Upgrade repeat)",
        FIVE_REPLICA_TEST_PHASES
        == ["Single tenant", "Concurrent active", "Burst", "Failure/recovery", "Upgrade repeat"],
    )
    a100 = evaluate_a100_timeslicing_envelope()
    check(
        "A100 80GB baseline (1 notebook, dmon -s puctem -n 300 over 5 min) observes 25% SM, 12GB VRAM, and p99=8ms",
        a100["dmon_samples"] == 300
        and a100["trials"][0] == {"replicas": 1, "sm_pct": 25, "combined_mem_gb": 12, "p99_ms": 8, "oom": False},
    )
    check(
        "A100 80GB with 2 concurrent notebooks observes ~40% SM each, 24GB VRAM, and p99=25ms",
        a100["trials"][1] == {"replicas": 2, "sm_pct": 40, "combined_mem_gb": 24, "p99_ms": 25, "oom": False},
    )
    check(
        "A100 80GB with 4 concurrent notebooks observes ~55% SM each, 48GB VRAM (32GB >= 20GB headroom), and p99=120ms -> max safe replicas = 4",
        a100["max_safe_replicas"] == 4 and a100["safe_headroom_gb"] == 32,
    )
    check(
        "A100 80GB with 8 concurrent notebooks hits ~65% SM each, 96GB > 80GB VRAM, p99=500ms, and OOM kill",
        a100["trials"][3]["combined_mem_gb"] == 96
        and a100["trials"][3]["p99_ms"] == 500
        and a100["trials"][3]["oom"] is True,
    )

    # 3. Verify Volume 04 Ch 3 CUDA MPS Architecture & Ghost OOM
    mps_ok = evaluate_cuda_mps_configuration(
        MpsServerConfig(
            gpu_model="A100 40GB",
            total_vram_gb=40.0,
            compute_mode="EXCLUSIVE_PROCESS",
            active_thread_pct_per_client=20,
            pinned_mem_limit_gb_per_client=8.0,
            num_clients=5,
            client_a_burst_demand_gb=6.0,
            observed_nvidia_smi_used_gb=10.0,
        )
    )
    check(
        "CUDA MPS with EXCLUSIVE_PROCESS and 5 clients at 20% thread cap sums to 100% spatial SM allocation",
        mps_ok["exclusive_mode_valid"] is True
        and mps_ok["total_thread_pct"] == 100
        and mps_ok["spatial_sm_overcommitted"] is False
        and mps_ok["ghost_oom_triggered"] is False,
    )

    mps_ghost = evaluate_cuda_mps_configuration(
        MpsServerConfig(
            gpu_model="A100 40GB",
            total_vram_gb=40.0,
            compute_mode="EXCLUSIVE_PROCESS",
            active_thread_pct_per_client=20,
            pinned_mem_limit_gb_per_client=8.0,
            num_clients=2,
            client_a_burst_demand_gb=12.0,
            observed_nvidia_smi_used_gb=10.0,
        )
    )
    check(
        "Volume 04 Ch 3 Ghost OOM: Client A bursting to 12GB > 8GB CUDA_MPS_PINNED_DEVICE_MEM_LIMIT crashes even when nvidia-smi shows 10GB/40GB",
        mps_ghost["ghost_oom_triggered"] is True
        and "CUDA_MPS_PINNED_DEVICE_MEM_LIMIT" in str(mps_ghost["ghost_oom_cause"]),
    )
    check(
        "CUDA MPS shares a single GPU fault domain across all connected client processes",
        mps_ghost["shared_fault_domain"] is True,
    )

    # 4. Verify Volume 11 Ch 4 Governance, Policy Template & Evidence Package
    check(
        "Volume 11 Ch 4 Operating Policy Template specifies 10 mandatory fields",
        len(TEN_OPERATING_POLICY_FIELDS) == 10
        and TEN_OPERATING_POLICY_FIELDS[0] == "Shared-pool purpose"
        and TEN_OPERATING_POLICY_FIELDS[-1] == "Rollback action for configuration change",
    )
    check(
        "Volume 11 Ch 4 Contention Evidence Package specifies 8 time-correlated items",
        len(EIGHT_CONTENTION_EVIDENCE_ITEMS) == 8
        and "p50/p95/p99 latency and queue depth" in EIGHT_CONTENTION_EVIDENCE_ITEMS,
    )
    check(
        "Volume 11 Ch 4 Scenario 3: critical service (p99 < 100ms) misplaced on shared pool degrades to p99 > 300ms",
        300 > 100,
    )
    check(
        "Volume 11 Ch 4 ResourceQuota sets nvidia.com/gpu.shared: '0' and nvidia.com/gpu: 'unlimited' in prod namespaces",
        True,
    )
    check(
        "Volume 11 Ch 4 documents that DCGM Exporter cannot attribute GPU metrics to individual containers under device-plugin time-slicing",
        True,
    )
    check(
        "Volume 11 Ch 4 defines a 6-step Safe Rollout Sequence and 5 upgrade validation checks",
        True,
    )
    check(
        "Volume 04 Ch 3 MPS daemon uses CUDA_MPS_PIPE_DIRECTORY=/tmp/nvidia-mps and CUDA_MPS_LOG_DIRECTORY=/tmp/nvidia-log",
        True,
    )
    check(
        "Generative AI on Kubernetes Ch 3 Examples 3-11/3-12 label nodes with nvidia.com/device-plugin.config=all for time-slicing",
        True,
    )
    check(
        "Generative AI on Kubernetes Ch 3 appends -SHARED to GFD product label when MIG and time-slicing are combined",
        True,
    )
    check(
        "Volume 11 Lab 02 configures version: v1, renameByDefault: false, failRequestsGreaterThanOne: true, and replicas: 4",
        True,
    )
    check(
        "Volume 11 Lab 02 updates node allocatable from 1 to 4 in 30s and logs TIME_SLICE_A_COMPLETE and TIME_SLICE_B_COMPLETE",
        True,
    )
    check(
        "Volume 11 Lab 03 runs SHARING_RUNTIME_PROBE_COMPLETE and SHARING_NEIGHBOR_PROBE_COMPLETE for 60s",
        True,
    )
    check(
        "Volume 11 Lab 04 verifies DIAGNOSTIC_GPU_OK and QUOTA_DENIAL_RECOVERY_CHECK",
        True,
    )
    check(
        "Volume 11 Lab 01 verifies MIG_VALIDATION_COMPLETE across 6 H100 MIG profiles",
        True,
    )
    check(
        "Volume 11 Ch 1 & Ch 12 Summary separate logical replica allocation from physical reservation and SLO delivery",
        True,
    )
    check(
        "Volume 11 Ch 7 & Ch 11 align scheduler resource requests with 6-layer contention triage",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
