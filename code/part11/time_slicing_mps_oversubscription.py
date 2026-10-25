#!/usr/bin/env python3
"""Chapter 11.25 model: Time-Slicing, CUDA MPS, and GPU Oversubscription Governance.

Models:
1. Volume 11 Chapter 4 Time-Slicing & Oversubscription Envelope Evaluator:
   - 16 GB T4 with replicas: 10 ("The Lie" vs "The Reality": 16 GB leak in Pod 1
     OOM-kills Pods 2..10),
   - 5-Phase Replica Ratio Benchmark (Single tenant -> Concurrent active -> Burst ->
     Failure/recovery -> Upgrade repeat) on an 80 GB A100:
     1 notebook (25% SM, 12GB, 8ms p99), 2 notebooks (40% SM, 24GB, 25ms p99),
     4 notebooks (55% SM, 48GB, 32GB>=20GB headroom, 120ms p99 -> SAFE),
     8 notebooks (65% SM, 96GB > 80GB OOM, 500ms p99 -> UNSAFE),
   - Scenario 3 misplacement guard (p99 < 100ms critical service degrades to > 300ms
     on shared pool; prevented via renameByDefault: true -> nvidia.com/gpu.shared: '0'),
   - 10-field Operating Policy Template & 8-item Contention Evidence Package.
2. Volume 04 Chapter 3 CUDA Multi-Process Service (MPS) Architecture & Ghost OOM Analyzer:
   - nvidia-cuda-mps-control -d + nvidia-cuda-mps-server in EXCLUSIVE_PROCESS mode,
   - Spatial SM partitioning via set_default_active_thread_percentage 20,
   - Per-client memory ceiling via CUDA_MPS_PINNED_DEVICE_MEM_LIMIT (explaining the
     Ghost OOM on a 40 GB A100 when nvidia-smi shows only 10 GB used).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


FIVE_REPLICA_TEST_PHASES: List[str] = [
    "Single tenant",
    "Concurrent active",
    "Burst",
    "Failure/recovery",
    "Upgrade repeat",
]

TEN_OPERATING_POLICY_FIELDS: List[str] = [
    "Shared-pool purpose",
    "Eligible and excluded workloads",
    "Advertised shared resource name",
    "Tested replica envelope and date",
    "Memory and latency assumptions",
    "Quota scope and admission behavior",
    "Overload action",
    "Escalation owner",
    "Protected-service escape path",
    "Rollback action for configuration change",
]

EIGHT_CONTENTION_EVIDENCE_ITEMS: List[str] = [
    "Workload version and request rate",
    "p50/p95/p99 latency and queue depth",
    "Pod allocation and placement history",
    "Active-process and memory evidence",
    "Device health, power, thermal, and error events",
    "Node/device-plugin configuration and events",
    "Quota/admission decisions",
    "Actions taken and time to recovery",
]


@dataclass(frozen=True)
class MpsServerConfig:
    gpu_model: str
    total_vram_gb: float
    compute_mode: str  # Must be "EXCLUSIVE_PROCESS"
    active_thread_pct_per_client: int
    pinned_mem_limit_gb_per_client: float
    num_clients: int
    client_a_burst_demand_gb: float
    observed_nvidia_smi_used_gb: float


def evaluate_cuda_mps_configuration(cfg: MpsServerConfig) -> Dict[str, object]:
    """Evaluates Volume 04 Chapter 3 CUDA MPS configuration and Ghost OOM diagnosis."""
    exclusive_mode_valid = cfg.compute_mode == "EXCLUSIVE_PROCESS"
    total_thread_pct = cfg.num_clients * cfg.active_thread_pct_per_client
    spatial_sm_overcommitted = total_thread_pct > 100

    ghost_oom_triggered = (
        cfg.client_a_burst_demand_gb > cfg.pinned_mem_limit_gb_per_client
        and cfg.observed_nvidia_smi_used_gb < cfg.total_vram_gb
    )

    return {
        "exclusive_mode_valid": exclusive_mode_valid,
        "total_thread_pct": total_thread_pct,
        "spatial_sm_overcommitted": spatial_sm_overcommitted,
        "ghost_oom_triggered": ghost_oom_triggered,
        "ghost_oom_cause": (
            f"Client A burst ({cfg.client_a_burst_demand_gb} GB) exceeded CUDA_MPS_PINNED_DEVICE_MEM_LIMIT "
            f"({cfg.pinned_mem_limit_gb_per_client} GB) even though nvidia-smi showed {cfg.observed_nvidia_smi_used_gb}/{cfg.total_vram_gb} GB"
            if ghost_oom_triggered
            else "No per-client cap violation"
        ),
        "shared_fault_domain": True,
    }


def simulate_t4_ten_replica_memory_leak(
    t4_vram_gb: int = 16,
    advertised_replicas: int = 10,
    pod1_leaked_gb: int = 16,
    other_pods_request_gb: int = 1,
) -> Dict[str, object]:
    """Models Volume 11 Chapter 4 Primer: 16 GB T4 with replicas: 10 and Pod 1 memory leak."""
    remaining_vram_gb = max(0, t4_vram_gb - pod1_leaked_gb)
    pods_2_to_10_oom = remaining_vram_gb < other_pods_request_gb

    return {
        "t4_vram_gb": t4_vram_gb,
        "advertised_replicas": advertised_replicas,
        "pod1_leaked_gb": pod1_leaked_gb,
        "remaining_vram_gb": remaining_vram_gb,
        "victim_pods_count": advertised_replicas - 1,
        "pods_2_to_10_oom": pods_2_to_10_oom,
    }


def evaluate_a100_timeslicing_envelope() -> Dict[str, object]:
    """Models Volume 11 Chapter 4 A100 80GB notebook replica ratio measurement."""
    trials = [
        {"replicas": 1, "sm_pct": 25, "combined_mem_gb": 12, "p99_ms": 8, "oom": False},
        {"replicas": 2, "sm_pct": 40, "combined_mem_gb": 24, "p99_ms": 25, "oom": False},
        {"replicas": 4, "sm_pct": 55, "combined_mem_gb": 48, "p99_ms": 120, "oom": False},
        {"replicas": 8, "sm_pct": 65, "combined_mem_gb": 96, "p99_ms": 500, "oom": True},
    ]
    safe_trials = [
        t for t in trials if (80 - t["combined_mem_gb"]) >= 20 and t["p99_ms"] <= 150 and not t["oom"]
    ]
    return {
        "gpu_vram_gb": 80,
        "required_headroom_gb": 20,
        "dmon_samples": 300,
        "dmon_duration_minutes": 5,
        "trials": trials,
        "max_safe_replicas": safe_trials[-1]["replicas"],
        "safe_headroom_gb": 80 - safe_trials[-1]["combined_mem_gb"],
    }
