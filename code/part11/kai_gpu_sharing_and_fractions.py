"""Chapter 11.17 — KAI GPU sharing and fractions.

Deterministic models for:
1. KAI Scheduler fractional GPU bin-packer (`gpu-fraction` and `gpu-memory`
   annotations, packing heterogeneous `0.5 + 0.25 + 0.25 = 1.0` pods onto 1
   physical GPU via a `binder` reservation pod while keeping other GPUs whole).
2. Volume 11 Chapter 4 A100 `80 GB` time-slicing concurrency envelope analyzer
   (`1` notebook: `12 GB`, `25%` SM, `8 ms` p99; `2` notebooks: `24 GB`, `40%` SM,
   `25 ms` p99; `4` notebooks: `48 GB`, `55%` SM, `120 ms` p99 -> safe `replicas: 4`
   with `>= 20 GB` headroom; `8` notebooks: `96 GB > 80 GB` OOM, `500 ms` p99).
3. Volume 24 Project 6 H100 `80 GB` (`989` TFLOPS BF16) MIG multi-tenant partition
   solver (`2g.20gb` `283` TFLOPS for `12.4 GB` LLM training + `1g.10gb` `141` TFLOPS
   for `4 GB` Batch CNN + `1g.10gb` `141` TFLOPS for `<1 GB` Online Embedding =
   `4/7` slices, `40/80 GB` used, `3/7` slices & `40 GB` free).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class PhysicalGpuSlot:
    """State of a single physical GPU managed by KAI Scheduler + binder."""

    gpu_index: int
    total_memory_mib: int = 81920
    used_fraction: float = 0.0
    used_memory_mib: int = 0
    reservation_pod_created: bool = False
    bound_pods: List[str] = field(default_factory=list)

    @property
    def free_fraction(self) -> float:
        return round(1.0 - self.used_fraction, 4)

    @property
    def free_memory_mib(self) -> int:
        return self.total_memory_mib - self.used_memory_mib


def pack_kai_fractional_pods(
    num_physical_gpus: int,
    gpu_memory_mib: int,
    pod_requests: List[Tuple[str, float, int]],  # (pod_name, gpu_fraction, gpu_memory_mib)
) -> Dict[str, object]:
    """Pack fractional and whole-GPU pods onto physical GPUs using MostAllocated bin-packing."""
    gpus = [
        PhysicalGpuSlot(gpu_index=i, total_memory_mib=gpu_memory_mib)
        for i in range(num_physical_gpus)
    ]
    unplaced_pods: List[str] = []

    for pod_name, req_frac, req_mem in pod_requests:
        # Sort candidate GPUs that already have fractional allocations first (bin-packing)
        eligible = [
            g
            for g in gpus
            if g.free_fraction >= round(req_frac, 4) and g.free_memory_mib >= req_mem
        ]
        eligible.sort(key=lambda g: (-g.used_fraction, g.gpu_index))
        if not eligible:
            unplaced_pods.append(pod_name)
            continue
        chosen = eligible[0]
        chosen.used_fraction = round(chosen.used_fraction + req_frac, 4)
        chosen.used_memory_mib += req_mem
        if req_frac < 1.0:
            chosen.reservation_pod_created = True
        chosen.bound_pods.append(pod_name)

    whole_free_gpus = sum(1 for g in gpus if g.used_fraction == 0.0)
    reservation_pods_count = sum(1 for g in gpus if g.reservation_pod_created)
    return {
        "gpus": gpus,
        "whole_free_gpus": whole_free_gpus,
        "reservation_pods_count": reservation_pods_count,
        "unplaced_pods": unplaced_pods,
    }


def evaluate_time_slicing_notebook_envelope(
    gpu_vram_gb: int = 80,
    min_headroom_gb: int = 20,
    max_acceptable_p99_ms: int = 150,
) -> Dict[str, object]:
    """Evaluate the Volume 11 Chapter 4 A100 80GB notebook concurrency benchmark."""
    phases = [
        {"replicas": 1, "sm_pct": 25, "combined_mem_gb": 12, "p99_ms": 8},
        {"replicas": 2, "sm_pct": 40, "combined_mem_gb": 24, "p99_ms": 25},
        {"replicas": 4, "sm_pct": 55, "combined_mem_gb": 48, "p99_ms": 120},
        {"replicas": 8, "sm_pct": 65, "combined_mem_gb": 96, "p99_ms": 500},
    ]
    safe_replicas = 1
    oom_replicas: List[int] = []
    for p in phases:
        mem_ok = p["combined_mem_gb"] <= (gpu_vram_gb - min_headroom_gb)
        lat_ok = p["p99_ms"] <= max_acceptable_p99_ms
        if p["combined_mem_gb"] > gpu_vram_gb:
            oom_replicas.append(p["replicas"])
        if mem_ok and lat_ok:
            safe_replicas = p["replicas"]
    return {
        "safe_replicas": safe_replicas,
        "oom_replicas": oom_replicas,
        "at_4_replicas_free_gb": gpu_vram_gb - 48,
        "at_8_replicas_overflow_gb": 96 - gpu_vram_gb,
    }


def solve_h100_mig_three_workload_capstone() -> Dict[str, object]:
    """Solve Volume 24 Project 6 H100 80GB (989 TFLOPS BF16) MIG partitioning."""
    h100_profiles = {
        "7g.80gb": {"slices": 7, "mem_gb": 80, "tflops": 989},
        "4g.40gb": {"slices": 4, "mem_gb": 40, "tflops": 565},
        "3g.40gb": {"slices": 3, "mem_gb": 40, "tflops": 424},
        "2g.20gb": {"slices": 2, "mem_gb": 20, "tflops": 283},
        "1g.10gb": {"slices": 1, "mem_gb": 10, "tflops": 141},
    }
    chosen_assignment = {
        "research_training_1_3b": "2g.20gb",  # needs 12.4 GB (> 10 GB)
        "batch_cnn_resnet50": "1g.10gb",      # needs 4.0 GB, ~2.56 TFLOP/s
        "online_embedding": "1g.10gb",        # needs <1.0 GB, ~0.1 TFLOP/s
    }
    used_slices = sum(h100_profiles[p]["slices"] for p in chosen_assignment.values())
    used_mem_gb = sum(h100_profiles[p]["mem_gb"] for p in chosen_assignment.values())
    free_slices = 7 - used_slices
    free_mem_gb = 80 - used_mem_gb

    return {
        "profiles_table": h100_profiles,
        "assignment": chosen_assignment,
        "used_slices": used_slices,
        "total_slices": 7,
        "used_mem_gb": used_mem_gb,
        "total_mem_gb": 80,
        "free_slices": free_slices,
        "free_mem_gb": free_mem_gb,
        "can_fit_fourth_3g_40gb_tenant": (free_slices == 3 and free_mem_gb == 40),
    }
