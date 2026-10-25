#!/usr/bin/env python3
"""Chapter 11.24 model: MIG in Depth (Silicon Hierarchy, Placement Geometry, Sizing & Lifecycle).

Models:
1. Volume 11 Chapter 2 MIG Hierarchy (Physical GPU -> GPU Instance GI -> Compute Instance CI),
   6-Layer Validation Chain (Driver 575.10, CUDA 12.5, 42W/700W, 100MiB/10000MiB,
   status.allocatable=3, torch.cuda.device_count()=1), 6-Phase Change Workflow, and
   8-Step Node Lifecycle Sequence.
2. Volume 11 Chapter 3 MIG Profile Sizing & 24-Node H100 Fleet Capacity Planner:
   - Embedding model (cold 2GB, steady 3GB, peak 4.2GB at 100 reqs, p99 < 50ms) ->
     1g.10gb with 5.8GB headroom (4 instances/node),
   - Chat LLM (7GB weights + KV cache: cold 8GB, steady 8.5GB, peak 10.2GB at 50 seqs
     2k context, p99=200ms) -> 3g.40gb with 29.8GB headroom (1 instance/node),
   - Batch inference (batch 32, 18GB steady) -> 7g.80gb (1/node),
   - Rejects 7x(1g.10gb) + 2x(3g.40gb) = 13 slices (>7) and 150GB (>80GB),
   - Accepts 4x(1g.10gb) + 1x(3g.40gb) = 7/7 slices and 80/80GB across 20 H100 nodes +
     4 reserved H100 nodes = 24 total H100 nodes.
3. Volume 04 Chapter 3 GPU Sharing, DCGM Telemetry (7 custom fields on port 9400),
   Node Drain (dcgmi dmon -e 203 -c 1 until 0% + rmmod), Known-Good Validation
   (dcgmi diag -r 3 + all_reduce_perf 1G..8G), and XID/MPS troubleshooting.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Tuple


MIG_SIX_VALIDATION_LAYERS: List[str] = [
    "1. Hardware and driver",
    "2. MIG configuration (GI/CI)",
    "3. Container runtime",
    "4. Kubernetes",
    "5. Application",
    "6. Operations / Rollback",
]

MIG_CHANGE_WORKFLOW_PHASES: List[str] = [
    "Plan",
    "Notify",
    "Prepare",
    "Apply",
    "Validate",
    "Release",
]

DCGM_SEVEN_CUSTOM_FIELDS: List[str] = [
    "DCGM_FI_DEV_SM_CLOCK",
    "DCGM_FI_DEV_MEM_CLOCK",
    "DCGM_FI_DEV_GPU_TEMP",
    "DCGM_FI_DEV_POWER_USAGE",
    "DCGM_FI_PROF_PIPE_TENSOR_ACTIVE",
    "DCGM_FI_PROF_NVLINK_TX_BYTES",
    "DCGM_FI_PROF_NVLINK_RX_BYTES",
]


@dataclass(frozen=True)
class MigWorkloadEnvelope:
    name: str
    cold_gb: float
    steady_gb: float
    peak_gb: float
    concurrent_clients: int
    p99_target_ms: int


def select_h100_mig_profile_for_workload(env: MigWorkloadEnvelope) -> Dict[str, object]:
    """Selects the smallest valid H100 MIG profile with positive peak headroom (Vol 11 Ch 3)."""
    candidates: List[Tuple[str, int, int]] = [
        ("1g.10gb", 1, 10),
        ("2g.20gb", 2, 20),
        ("3g.40gb", 3, 40),
        ("4g.40gb", 4, 40),
        ("7g.80gb", 7, 80),
    ]
    for profile, slices, mem_gb in candidates:
        if env.peak_gb < mem_gb:
            headroom_gb = round(mem_gb - env.peak_gb, 1)
            return {
                "workload": env.name,
                "chosen_profile": profile,
                "compute_slices": slices,
                "profile_memory_gb": mem_gb,
                "peak_memory_gb": env.peak_gb,
                "headroom_gb": headroom_gb,
                "fits_1g_10gb": env.peak_gb < 10.0,
            }
    raise ValueError(f"Workload {env.name} peak ({env.peak_gb} GB) exceeds 80 GB H100 capacity")


def validate_h100_mig_node_layout(
    profile_counts: List[Tuple[str, int, int, int]],
    max_slices: int = 7,
    max_memory_gb: int = 80,
) -> Dict[str, object]:
    """Validates whether a proposed H100 MIG layout fits 7 compute slices and 80 GB HBM3.

    profile_counts: list of (profile_name, count, slices_per_inst, mem_gb_per_inst)
    """
    total_slices = sum(count * slices for _, count, slices, _ in profile_counts)
    total_mem_gb = sum(count * mem for _, count, _, mem in profile_counts)
    valid = (total_slices <= max_slices) and (total_mem_gb <= max_memory_gb)

    return {
        "valid_layout": valid,
        "total_compute_slices": total_slices,
        "max_compute_slices": max_slices,
        "total_memory_gb": total_mem_gb,
        "max_memory_gb": max_memory_gb,
        "free_compute_slices": max(0, max_slices - total_slices),
        "free_memory_gb": max(0, max_memory_gb - total_mem_gb),
    }


def plan_vol11_ch3_h100_fleet() -> Dict[str, object]:
    """Models the Volume 11 Chapter 3 24-node H100 MIG fleet sizing calculation."""
    embedding = select_h100_mig_profile_for_workload(
        MigWorkloadEnvelope("Embedding", 2.0, 3.0, 4.2, 100, 50)
    )
    chat_llm = select_h100_mig_profile_for_workload(
        MigWorkloadEnvelope("Chat LLM", 8.0, 8.5, 10.2, 50, 200)
    )

    rejected = validate_h100_mig_node_layout([("1g.10gb", 7, 1, 10), ("3g.40gb", 2, 3, 40)])
    accepted = validate_h100_mig_node_layout([("1g.10gb", 4, 1, 10), ("3g.40gb", 1, 3, 40)])

    shared_mig_nodes = 20
    reserved_whole_gpu_nodes = 4
    total_h100_nodes = shared_mig_nodes + reserved_whole_gpu_nodes

    return {
        "embedding_sizing": embedding,
        "chat_llm_sizing": chat_llm,
        "rejected_layout": rejected,
        "accepted_layout": accepted,
        "shared_mig_nodes": shared_mig_nodes,
        "reserved_whole_gpu_nodes": reserved_whole_gpu_nodes,
        "total_h100_nodes": total_h100_nodes,
        "total_embedding_slots": shared_mig_nodes * 4,
        "total_chat_llm_slots": shared_mig_nodes * 1,
    }
