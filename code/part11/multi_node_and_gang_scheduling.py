"""Chapter 11.7 — Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts.

Deterministic models for:
1. Single-node Pod boundary validator (`Pod.spec.nodeName` cannot span multiple nodes;
   64-GPU job across 8-GPU nodes must be decomposed into 8 Pods x 8 GPUs/Pod).
2. Standard Per-Pod Scheduling vs Gang Scheduling (Coscheduling) simulator:
   - 7-of-8 partial allocation deadlock (`56` GPUs allocated and idle at PyTorch
     rendezvous barrier while 8th Pod waits in Pending).
   - Mutual gang deadlock when two 8-Pod jobs contend on a 12-node (96-GPU) cluster
     without gang scheduling (`6` Pods + `6` Pods = `96` GPUs deadlocked, `0` jobs running)
     vs with gang scheduling (`1` job runs `8` Pods = `64` GPUs, `1` job waits in queue
     with `0` wasted GPUs).
3. `NodeResourcesFit` `MostAllocated` bin-packing scorer (`nvidia.com/gpu` weight `5`,
   `cpu` weight `1`, `memory` weight `1`) and Descheduler policy alignment validator
   (`HighNodeUtilization` + `MostAllocated` vs `LowNodeUtilization` + `LeastAllocated`).
4. Head-of-Line (HoL) Blocking & Backfill Scheduler (`1024`-GPU head job with `1000`
   free GPUs waiting `24` GPUs; backfill admits `8`-GPU jobs only if runtime <= shadow
   start time) and Checkpoint Storage sizer (`2 * base_model_size + checkpoint_overhead`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


def validate_pod_vs_multi_node_job(
    total_gpus_needed: int,
    max_gpus_per_node: int = 8,
    requested_as_single_pod: bool = False,
) -> Dict[str, object]:
    """Explain why a single Pod requesting > max_gpus_per_node stays Pending."""
    if requested_as_single_pod and total_gpus_needed > max_gpus_per_node:
        return {
            "schedulable": False,
            "reason": (
                f"Single Pod requests {total_gpus_needed} GPUs, exceeding single-node "
                f"capacity ({max_gpus_per_node} GPUs/node); a Pod cannot span nodes"
            ),
            "required_pods": 1,
            "gpus_per_pod": total_gpus_needed,
        }
    pods_needed = (total_gpus_needed + max_gpus_per_node - 1) // max_gpus_per_node
    gpus_per_pod = total_gpus_needed // pods_needed
    return {
        "schedulable": True,
        "reason": f"Decomposed into {pods_needed} coordinated Pods x {gpus_per_pod} GPUs/Pod",
        "required_pods": pods_needed,
        "gpus_per_pod": gpus_per_pod,
    }


def simulate_partial_vs_gang_scheduling(
    cluster_free_gpus: int,
    job_pods: int = 8,
    gpus_per_pod: int = 8,
    gang_enabled: bool = False,
    node_cost_per_hour_usd: float = 20.0,
) -> Dict[str, object]:
    """Compare standard per-pod scheduling vs gang scheduling when free GPUs < job total."""
    total_job_gpus = job_pods * gpus_per_pod
    max_placeable_pods = min(job_pods, cluster_free_gpus // gpus_per_pod)

    if not gang_enabled:
        placed_pods = max_placeable_pods
        allocated_gpus = placed_pods * gpus_per_pod
        rendezvous_complete = placed_pods == job_pods
        wasted_idle_gpus = 0 if rendezvous_complete else allocated_gpus
        wasted_usd_per_hour = (
            0.0 if rendezvous_complete else placed_pods * node_cost_per_hour_usd
        )
        return {
            "gang_enabled": False,
            "placed_pods": placed_pods,
            "pending_pods": job_pods - placed_pods,
            "allocated_gpus": allocated_gpus,
            "rendezvous_complete": rendezvous_complete,
            "wasted_idle_gpus": wasted_idle_gpus,
            "wasted_usd_per_hour": round(wasted_usd_per_hour, 2),
        }

    # Gang scheduling: all-or-nothing (`minMember` / `minAvailable` == job_pods)
    if max_placeable_pods < job_pods:
        return {
            "gang_enabled": True,
            "placed_pods": 0,
            "pending_pods": job_pods,
            "allocated_gpus": 0,
            "rendezvous_complete": False,
            "wasted_idle_gpus": 0,
            "wasted_usd_per_hour": 0.0,
        }
    return {
        "gang_enabled": True,
        "placed_pods": job_pods,
        "pending_pods": 0,
        "allocated_gpus": total_job_gpus,
        "rendezvous_complete": True,
        "wasted_idle_gpus": 0,
        "wasted_usd_per_hour": 0.0,
    }


def score_node_most_allocated(
    allocated_gpus: int,
    total_gpus: int,
    allocated_cpus: int,
    total_cpus: int,
    allocated_mem_gib: int,
    total_mem_gib: int,
    gpu_weight: int = 5,
    cpu_weight: int = 1,
    mem_weight: int = 1,
) -> float:
    """Compute GAK Example 7-1 `MostAllocated` weighted score (0..100 scale)."""
    gpu_ratio = (allocated_gpus / total_gpus) * 100.0
    cpu_ratio = (allocated_cpus / total_cpus) * 100.0
    mem_ratio = (allocated_mem_gib / total_mem_gib) * 100.0
    total_weight = gpu_weight + cpu_weight + mem_weight
    weighted = (
        gpu_ratio * gpu_weight + cpu_ratio * cpu_weight + mem_ratio * mem_weight
    ) / total_weight
    return round(weighted, 2)


def validate_scheduler_descheduler_alignment(
    scheduler_strategy: str,
    enabled_descheduler_plugins: Tuple[str, ...],
) -> Tuple[bool, str]:
    """Validate GAK Ch 7 Table 7-1 & Warning on scheduler/descheduler eviction loops."""
    has_high = "HighNodeUtilization" in enabled_descheduler_plugins
    has_low = "LowNodeUtilization" in enabled_descheduler_plugins
    if has_high and has_low:
        return (
            False,
            "Conflict: HighNodeUtilization and LowNodeUtilization must never be enabled simultaneously",
        )
    if has_high and scheduler_strategy != "MostAllocated":
        return (
            False,
            "Eviction loop: HighNodeUtilization requires MostAllocated (bin packing) scheduler strategy",
        )
    if has_low and scheduler_strategy != "LeastAllocated":
        return (
            False,
            "Eviction loop: LowNodeUtilization requires LeastAllocated (spreading) scheduler strategy",
        )
    return True, "Valid scheduler and descheduler alignment"


@dataclass(frozen=True)
class QueuedJob:
    """A batch GPU job waiting behind the head-of-line job."""

    name: str
    gpus_required: int
    time_limit_minutes: Optional[int]


def evaluate_backfill_candidates(
    cluster_free_gpus: int = 1000,
    head_job_gpus: int = 1024,
    minutes_until_24_gpus_free: int = 45,
    candidates: List[QueuedJob] = (),
) -> Dict[str, object]:
    """Evaluate Volume 06 Part 4.1 backfill scheduling behind a 1024-GPU head job."""
    gpus_shortfall = max(0, head_job_gpus - cluster_free_gpus)
    remaining_free_gpus = cluster_free_gpus
    backfilled_jobs: List[str] = []
    blocked_jobs: List[Tuple[str, str]] = []

    for job in candidates:
        if job.time_limit_minutes is None:
            blocked_jobs.append((job.name, "Rejected: missing TimeLimit (wall time)"))
            continue
        if (
            job.gpus_required <= remaining_free_gpus
            and job.time_limit_minutes <= minutes_until_24_gpus_free
        ):
            backfilled_jobs.append(job.name)
            remaining_free_gpus -= job.gpus_required
        else:
            blocked_jobs.append(
                (
                    job.name,
                    "Cannot backfill: exceeds free GPUs or runs past head job start window",
                )
            )
    return {
        "head_job_shortfall_gpus": gpus_shortfall,
        "backfilled_jobs": backfilled_jobs,
        "blocked_jobs": blocked_jobs,
        "remaining_idle_gpus": remaining_free_gpus,
    }


def estimate_checkpoint_storage_gb(
    base_model_size_gb: float, checkpoint_overhead_gb: float
) -> float:
    """Compute GAK Ch 7 storage sizing rule: 2 * base_model_size + checkpoint_overhead."""
    return round(2.0 * base_model_size_gb + checkpoint_overhead_gb, 2)
