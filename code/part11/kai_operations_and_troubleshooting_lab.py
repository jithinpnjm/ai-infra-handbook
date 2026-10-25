#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.18: KAI Operations and Troubleshooting."""

from __future__ import annotations
import sys
from kai_operations_and_troubleshooting import (
    SIX_TRIAGE_LAYERS,
    SharedGpuSloSnapshot,
    KaiIncidentEvidence,
    evaluate_shared_gpu_slo,
    classify_kai_and_shared_gpu_incident,
    evaluate_gameday_fault_scenarios,
)


def run_lab() -> int:
    print("=== Chapter 11.18 Lab: KAI Operations, Observability, SLIs/SLOs & Troubleshooting ===")
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

    # 1. Verify 6-layer triage order from Volume 11 Ch 11 & Lab 04
    check(
        "Volume 11 Ch 11 / Lab 04 defines 6 ordered triage layers from Hardware/driver to Service & Telemetry",
        len(SIX_TRIAGE_LAYERS) == 6
        and SIX_TRIAGE_LAYERS[0]["layer"] == "Hardware/driver"
        and SIX_TRIAGE_LAYERS[5]["layer"] == "Service & Telemetry",
    )
    check(
        "Layer 2 inspects sharing state (mig.mode.current / mig -lgi) before Layer 3 node Allocatable",
        SIX_TRIAGE_LAYERS[1]["layer"] == "Sharing state"
        and SIX_TRIAGE_LAYERS[2]["layer"] == "Registration",
    )
    check(
        "Layer 4 inspects scheduling policy (PodGroup, Queue quota, ResourceQuota) before Layer 5 Runtime",
        SIX_TRIAGE_LAYERS[3]["layer"] == "Scheduling policy"
        and SIX_TRIAGE_LAYERS[4]["layer"] == "Runtime",
    )

    # 2. Verify Volume 11 Ch 10 Shared-GPU SLI/SLO evaluation rules
    mig_ok = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="mig-inference",
            total_requests=10000,
            successful_requests=9980,
            p99_latency_ms=85.0,
            queue_wait_p95_seconds=2.0,
            gpu_memory_used_mib=14000,
            gpu_memory_total_mib=20480,
            dcgm_scrape_age_seconds=15,
        )
    )
    check(
        "Reserved MIG inference with 99.8% (> 99.5%) success and p99=85ms (< 100ms) is HEALTHY_SLO_MET",
        mig_ok["health_state"] == "HEALTHY_SLO_MET" and mig_ok["success_rate_pct"] == 99.8,
    )

    mig_breach = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="mig-inference",
            total_requests=10000,
            successful_requests=9980,
            p99_latency_ms=135.0,
            queue_wait_p95_seconds=2.0,
            gpu_memory_used_mib=14000,
            gpu_memory_total_mib=20480,
            dcgm_scrape_age_seconds=15,
        )
    )
    check(
        "Reserved MIG inference with p99=135ms (> 120ms breach threshold) triggers SLO_BREACH",
        mig_breach["health_state"] == "SLO_BREACH",
    )

    mig_warn = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="mig-inference",
            total_requests=10000,
            successful_requests=9970,
            p99_latency_ms=110.0,
            queue_wait_p95_seconds=2.0,
            gpu_memory_used_mib=14000,
            gpu_memory_total_mib=20480,
            dcgm_scrape_age_seconds=30,
        )
    )
    check(
        "Reserved MIG inference between 100ms and 120ms (110ms) enters SLO_WARNING_100_TO_120MS",
        mig_warn["health_state"] == "SLO_WARNING_100_TO_120MS",
    )

    ts_ok = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="time-sliced",
            total_requests=500,
            successful_requests=500,
            p99_latency_ms=115.0,
            queue_wait_p95_seconds=18.0,
            gpu_memory_used_mib=49152,
            gpu_memory_total_mib=81920,
            dcgm_scrape_age_seconds=20,
        )
    )
    check(
        "Best-effort time-sliced pool with p95 queue wait 18s (< 30s) and 60% (<= 90%) memory is HEALTHY_BEST_EFFORT",
        ts_ok["health_state"] == "HEALTHY_BEST_EFFORT" and ts_ok["memory_utilization_pct"] == 60.0,
    )

    ts_mem_pressure = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="time-sliced",
            total_requests=500,
            successful_requests=500,
            p99_latency_ms=250.0,
            queue_wait_p95_seconds=18.0,
            gpu_memory_used_mib=77824,
            gpu_memory_total_mib=81920,
            dcgm_scrape_age_seconds=20,
        )
    )
    check(
        "Time-sliced pool at 95% (> 90%) memory utilization flags MEMORY_CONTENTION_GT_90PCT",
        ts_mem_pressure["health_state"] == "MEMORY_CONTENTION_GT_90PCT"
        and ts_mem_pressure["memory_utilization_pct"] == 95.0,
    )

    ts_queue_breach = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="time-sliced",
            total_requests=500,
            successful_requests=500,
            p99_latency_ms=115.0,
            queue_wait_p95_seconds=45.0,
            gpu_memory_used_mib=49152,
            gpu_memory_total_mib=81920,
            dcgm_scrape_age_seconds=20,
        )
    )
    check(
        "Time-sliced pool with p95 queue wait 45s (>= 30s) flags QUEUE_WAIT_BREACH_GE_30S",
        ts_queue_breach["health_state"] == "QUEUE_WAIT_BREACH_GE_30S",
    )

    stale = evaluate_shared_gpu_slo(
        SharedGpuSloSnapshot(
            service_class="mig-inference",
            total_requests=10000,
            successful_requests=10000,
            p99_latency_ms=40.0,
            queue_wait_p95_seconds=1.0,
            gpu_memory_used_mib=10000,
            gpu_memory_total_mib=20480,
            dcgm_scrape_age_seconds=180,
        )
    )
    check(
        "DCGM scrape age 180s (> 120s) marks state as UNKNOWN_STALE_TELEMETRY rather than healthy",
        stale["health_state"] == "UNKNOWN_STALE_TELEMETRY" and stale["telemetry_stale"] is True,
    )

    # 3. Verify layered KAI + Shared GPU incident classification
    c_hw = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(False, True, True, 0, False, False, False, False, False, 0.0, 100.0, 15)
    )
    check(
        "Missing host GPU enumeration classifies as Layer 1: Hardware/driver",
        c_hw["failed_layer"] == "Layer 1: Hardware/driver",
    )

    c_mig = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, False, 0, False, False, False, False, False, 0.0, 100.0, 15)
    )
    check(
        "MIG mode enabled with 0 GPU instances classifies as Layer 2: Sharing state",
        c_mig["failed_layer"] == "Layer 2: Sharing state",
    )

    c_dp = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, True, 0, False, False, False, False, False, 0.0, 100.0, 15)
    )
    check(
        "Host MIG instances present but node Allocatable=0 classifies as Layer 3: Registration (nvidia-device-plugin)",
        c_dp["failed_layer"] == "Layer 3: Registration" and c_dp["component"] == "nvidia-device-plugin",
    )

    c_quota = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, True, 4, True, False, False, False, False, 0.0, 100.0, 15)
    )
    check(
        "Lab 04 zero-capacity ResourceQuota denial classifies at API Admission before Pod creation",
        c_quota["failed_layer"] == "Layer 4: Scheduling policy (API Admission)"
        and c_quota["component"] == "kubernetes-resourcequota",
    )

    c_grouper = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, True, 4, False, False, False, False, False, 0.0, 100.0, 15)
    )
    check(
        "Missing PodGroup CR for a pending workload classifies as Layer 4: kai-pod-grouper",
        c_grouper["component"] == "kai-pod-grouper",
    )

    c_queue = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, True, 4, False, True, True, False, False, 0.0, 100.0, 15)
    )
    check(
        "PodGroup blocked by Queue limit classifies as Layer 4: kai-queue-controller",
        c_queue["component"] == "kai-queue-controller",
    )

    c_frag = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, True, 4, False, True, False, True, False, 0.0, 100.0, 15)
    )
    check(
        "Unused MIG slices that cannot form requested profile classify as Layer 4: MIG Fragmentation",
        c_frag["failed_layer"] == "Layer 4: Scheduling policy (MIG Fragmentation)",
    )

    c_binder = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, True, True, 4, False, True, False, False, True, 0.0, 100.0, 15)
    )
    check(
        "Stuck BindRequest CR or reservation pod classifies as Layer 5: kai-binder",
        c_binder["failed_layer"] == "Layer 5: Runtime / KAI Binding"
        and c_binder["component"] == "kai-binder",
    )

    c_contention = classify_kai_and_shared_gpu_incident(
        KaiIncidentEvidence(True, False, False, 4, False, True, False, False, False, 240.0, 100.0, 15)
    )
    check(
        "Running pod with p99=240ms (> 100ms SLO) on healthy GPU classifies as Layer 6: Workload Contention",
        c_contention["failed_layer"] == "Layer 6: Service & Telemetry (Workload Contention)",
    )

    # 4. Verify Volume 19 Ch 2 Game Day fault injections
    gd = evaluate_gameday_fault_scenarios()
    check(
        "Game Day XID 48 (Double-Bit ECC) is injected via dcgmi test --inject and marks GPU Unhealthy",
        gd["xid_48_double_bit_ecc"]["xid_code"] == 48
        and gd["xid_48_double_bit_ecc"]["injection_tool"] == "dcgmi test --inject",
    )
    check(
        "RDMA network blackhole requires switch port disable (ibportstate ... disable) because iptables ignores RDMA",
        gd["rdma_network_blackhole"]["valid_injection_command"] == "ibportstate ... disable"
        and gd["rdma_network_blackhole"]["iptables_affects_rdma"] is False,
    )
    check(
        "5-Nines (99.999%) Game Day hypotheses target < 5 seconds failover degradation",
        gd["control_plane_master_failover"]["claimed_availability_pct"] == 99.999
        and gd["control_plane_master_failover"]["target_failover_latency_seconds"] == 5,
    )
    check(
        "Control-plane master failover exposed aggressive device-plugin liveness probes unregistering nvidia.com/gpu",
        "liveness probe" in str(gd["control_plane_master_failover"]["root_cause"]),
    )
    check(
        "PodDisruptionBudgets do not stop kubelet from terminating pods when extended GPU resources disappear",
        gd["control_plane_master_failover"]["pdb_prevents_kubelet_resource_loss_termination"] is False,
    )
    check(
        "Stale telemetry (> 120s) attaches UNKNOWN warning to incident classification",
        "UNKNOWN" in classify_kai_and_shared_gpu_incident(
            KaiIncidentEvidence(True, False, False, 4, False, True, False, False, False, 50.0, 100.0, 150)
        )["telemetry_note"],
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
