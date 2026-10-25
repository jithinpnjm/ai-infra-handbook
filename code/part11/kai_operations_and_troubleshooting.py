#!/usr/bin/env python3
"""Chapter 11.18 model: KAI Operations, Observability, SLIs/SLOs, and Layered Troubleshooting.

Models:
1. KAI Scheduler 6-stage pipeline & microservice fault classifier (pod-grouper,
   queue-controller, kai-scheduler, binder, admission, device-plugin, host/MIG).
2. Volume 11 Chapter 11 & Lab 04 6-layer shared-GPU triage engine (Hardware/Driver ->
   Sharing Mode/Shape -> Registration/Discovery -> Scheduling Policy ->
   Runtime Initialization -> Service SLO & Telemetry Freshness).
3. Volume 11 Chapter 10 Shared-GPU SLI/SLO & Telemetry Freshness evaluator:
   - MIG inference success rate (> 99.5%), p99 latency (< 100 ms target, > 120 ms breach),
   - Time-sliced queue wait p95 (< 30 s) and memory pressure (> 90%),
   - Platform foundation DCGM scrape staleness (> 120 s = UNKNOWN, never healthy).
4. Volume 11 Lab 04 API Admission Quota Denial vs Scheduler 'Insufficient' Event
   classifier and Volume 19 Chapter 2 Game Day fault-injection validator (XID 48,
   IB port disable vs iptables, and control-plane leader-election liveness probe blast radius).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


SIX_TRIAGE_LAYERS: List[Dict[str, str]] = [
    {
        "order": "1",
        "layer": "Hardware/driver",
        "question": "Can the host enumerate the device and is MIG/driver healthy?",
        "evidence": "nvidia-smi -L, nvidia-smi -q, dmesg XID checks",
    },
    {
        "order": "2",
        "layer": "Sharing state",
        "question": "Is the intended MIG layout or time-slicing mode active?",
        "evidence": "nvidia-smi -i 0 --query-gpu=mig.mode.current, nvidia-smi mig -lgi",
    },
    {
        "order": "3",
        "layer": "Registration",
        "question": "Does Kubernetes advertise the expected resource in Capacity/Allocatable?",
        "evidence": "kubectl describe node, status.allocatable, device-plugin logs",
    },
    {
        "order": "4",
        "layer": "Scheduling policy",
        "question": "Can this tenant and PodGroup request and place the resource?",
        "evidence": "PodGroup/BindRequest status, Queue quota, ResourceQuota, taints, selectors",
    },
    {
        "order": "5",
        "layer": "Runtime",
        "question": "Does an assigned container initialize the GPU or reservation pod?",
        "evidence": "BindRequest phase, reservation pod status, container logs (DIAGNOSTIC_GPU_OK)",
    },
    {
        "order": "6",
        "layer": "Service & Telemetry",
        "question": "Is the user-visible SLO met and is DCGM telemetry fresh (<= 120s)?",
        "evidence": "App p99 latency, queue wait p95, dcgm_exporter_scrape_age_seconds",
    },
]


@dataclass(frozen=True)
class SharedGpuSloSnapshot:
    service_class: str  # "mig-inference" or "time-sliced"
    total_requests: int
    successful_requests: int
    p99_latency_ms: float
    queue_wait_p95_seconds: float
    gpu_memory_used_mib: int
    gpu_memory_total_mib: int
    dcgm_scrape_age_seconds: int


def evaluate_shared_gpu_slo(snapshot: SharedGpuSloSnapshot) -> Dict[str, object]:
    """Evaluates Volume 11 Chapter 10 SLI/SLO thresholds and telemetry freshness."""
    telemetry_stale = snapshot.dcgm_scrape_age_seconds > 120
    success_rate_pct = (
        (snapshot.successful_requests / snapshot.total_requests) * 100.0
        if snapshot.total_requests > 0
        else 0.0
    )
    mem_util_pct = (
        (snapshot.gpu_memory_used_mib / snapshot.gpu_memory_total_mib) * 100.0
        if snapshot.gpu_memory_total_mib > 0
        else 0.0
    )

    if telemetry_stale:
        health_state = "UNKNOWN_STALE_TELEMETRY"
    elif snapshot.service_class == "mig-inference":
        if success_rate_pct > 99.5 and snapshot.p99_latency_ms < 100.0:
            health_state = "HEALTHY_SLO_MET"
        elif snapshot.p99_latency_ms > 120.0 or success_rate_pct <= 99.5:
            health_state = "SLO_BREACH"
        else:
            health_state = "SLO_WARNING_100_TO_120MS"
    else:
        # time-sliced best-effort pool: graded on queue_time_p95 < 30s and memory pressure > 90%
        if snapshot.queue_wait_p95_seconds < 30.0 and mem_util_pct <= 90.0:
            health_state = "HEALTHY_BEST_EFFORT"
        elif mem_util_pct > 90.0:
            health_state = "MEMORY_CONTENTION_GT_90PCT"
        else:
            health_state = "QUEUE_WAIT_BREACH_GE_30S"

    return {
        "service_class": snapshot.service_class,
        "telemetry_stale": telemetry_stale,
        "dcgm_scrape_age_seconds": snapshot.dcgm_scrape_age_seconds,
        "success_rate_pct": round(success_rate_pct, 2),
        "p99_latency_ms": snapshot.p99_latency_ms,
        "queue_wait_p95_seconds": snapshot.queue_wait_p95_seconds,
        "memory_utilization_pct": round(mem_util_pct, 1),
        "health_state": health_state,
    }


@dataclass(frozen=True)
class KaiIncidentEvidence:
    host_gpu_enumerated: bool
    mig_mode_enabled: bool
    mig_instances_present: bool
    node_allocatable_count: int
    api_admission_denied_by_quota: bool
    pod_group_created: bool
    queue_over_limit: bool
    mig_geometry_fragmented: bool
    bind_request_stuck: bool
    app_p99_ms: float
    app_slo_target_ms: float
    dcgm_scrape_age_seconds: int


def classify_kai_and_shared_gpu_incident(ev: KaiIncidentEvidence) -> Dict[str, str]:
    """Classifies the first failed boundary using Volume 11 Ch 11 + KAI Scheduler architecture."""
    if ev.dcgm_scrape_age_seconds > 120:
        telemetry_note = "Telemetry stale (> 120s): mark hardware health UNKNOWN until scrape restored"
    else:
        telemetry_note = "Telemetry fresh (<= 120s)"

    if not ev.host_gpu_enumerated:
        return {
            "failed_layer": "Layer 1: Hardware/driver",
            "component": "host-driver-or-gpu",
            "first_safe_action": "Cordon node, preserve dmesg/nvidia-smi -q evidence, follow hardware runbook (do not reboot blindly)",
            "telemetry_note": telemetry_note,
        }
    if ev.mig_mode_enabled and not ev.mig_instances_present:
        return {
            "failed_layer": "Layer 2: Sharing state",
            "component": "mig-manager-or-host-layout",
            "first_safe_action": "Cordon node and reapply approved MIG profile config during maintenance window",
            "telemetry_note": telemetry_note,
        }
    if ev.node_allocatable_count <= 0:
        return {
            "failed_layer": "Layer 3: Registration",
            "component": "nvidia-device-plugin",
            "first_safe_action": "Inspect device-plugin logs and restart device-plugin pod on affected node",
            "telemetry_note": telemetry_note,
        }
    if ev.api_admission_denied_by_quota:
        return {
            "failed_layer": "Layer 4: Scheduling policy (API Admission)",
            "component": "kubernetes-resourcequota",
            "first_safe_action": "Inspect namespace ResourceQuota (Pod denied before creation; node allocatable unchanged)",
            "telemetry_note": telemetry_note,
        }
    if not ev.pod_group_created:
        return {
            "failed_layer": "Layer 4: Scheduling policy (KAI Grouping)",
            "component": "kai-pod-grouper",
            "first_safe_action": "Verify schedulerName: kai-scheduler, kai.scheduler/queue label, and pod-grouper logs",
            "telemetry_note": telemetry_note,
        }
    if ev.queue_over_limit:
        return {
            "failed_layer": "Layer 4: Scheduling policy (KAI Queue Quota)",
            "component": "kai-queue-controller",
            "first_safe_action": "Inspect kubectl get queues and Queue limit/overQuotaWeight; wait for reclamation or adjust quota",
            "telemetry_note": telemetry_note,
        }
    if ev.mig_geometry_fragmented:
        return {
            "failed_layer": "Layer 4: Scheduling policy (MIG Fragmentation)",
            "component": "mig-slice-geometry",
            "first_safe_action": "Route to compatible node pool or schedule controlled drain to defragment MIG slices",
            "telemetry_note": telemetry_note,
        }
    if ev.bind_request_stuck:
        return {
            "failed_layer": "Layer 5: Runtime / KAI Binding",
            "component": "kai-binder",
            "first_safe_action": "Inspect BindRequest CR, integer GPU reservation pod status, and kubelet CDI/device logs",
            "telemetry_note": telemetry_note,
        }
    if ev.app_p99_ms > ev.app_slo_target_ms:
        return {
            "failed_layer": "Layer 6: Service & Telemetry (Workload Contention)",
            "component": "shared-gpu-contention",
            "first_safe_action": "Move protected service to dedicated/MIG pool or reduce shared admission concurrency",
            "telemetry_note": telemetry_note,
        }
    return {
        "failed_layer": "None (Healthy)",
        "component": "healthy",
        "first_safe_action": "No action required",
        "telemetry_note": telemetry_note,
    }


def evaluate_gameday_fault_scenarios() -> Dict[str, Dict[str, object]]:
    """Models Volume 19 Chapter 2 AI Game Day fault injections and architectural fixes."""
    return {
        "xid_48_double_bit_ecc": {
            "xid_code": 48,
            "injection_tool": "dcgmi test --inject",
            "expected_device_plugin_state": "Unhealthy",
            "pod_evicted_and_node_cordoned": True,
        },
        "rdma_network_blackhole": {
            "valid_injection_command": "ibportstate ... disable",
            "iptables_affects_rdma": False,
            "expected_recovery": "NCCL timeout -> orchestrator restarts from async checkpoint",
        },
        "control_plane_master_failover": {
            "claimed_availability_pct": 99.999,
            "target_failover_latency_seconds": 5,
            "root_cause": "Aggressive device-plugin liveness probe restarted on API server leader-election pause, unregistering nvidia.com/gpu",
            "pdb_prevents_kubelet_resource_loss_termination": False,
            "architectural_fix": "Increase GPU Operator / device-plugin liveness probe timeouts and backoffs",
        },
    }
