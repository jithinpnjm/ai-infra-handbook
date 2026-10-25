"""Chapter 11.14 — KAI Scheduler architecture and resources.

Deterministic models for:
1. KAI Scheduler `pod-grouper` workload-to-`PodGroup` synthesizer (`PyTorchJob`,
   `TrainJob` / `JobSet`, `LeaderWorkerSet`, `MPIJob`, and single `Pod` ->
   `PodGroup` with `minMember`, `queue`, and `priorityClassName`).
2. KAI Scheduler CRD hierarchy validator (`Project` -> `Queue` -> `PodGroup` ->
   `BindRequest`).
3. KAI Scheduler session pipeline (`Snapshot -> Reclaim -> Preempt -> Allocate /
   Binpack -> BindRequest`) and the Volume 24 Project 7 `8`-GPU (`2`-node,
   `320GB`/node) `20`-job multi-class packing model:
   - `6` Type B Inference jobs (`0.5` GPU each = `3.0` GPUs, priority `1000`,
     `p99 < 10 ms`)
   - `10` Type A Training jobs (`1.0` GPU each, priority `100`, capped at `<= 60%`
     = `4.8` GPUs -> `4` concurrent jobs = `4.0` GPUs)
   - `4` Type C Research jobs (`0.25` GPU each = `1.0` GPU, priority `0`)
   - Total simultaneous packed allocation: `3.0 + 4.0 + 1.0 = 8.0` GPUs (`100.0%`
     of `8` GPUs, `> 85%` target).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


KAI_CONTROL_PLANE_COMPONENTS: Tuple[str, ...] = (
    "pod-grouper",
    "queue-controller",
    "kai-scheduler",
    "binder",
    "admission-webhook",
)


@dataclass(frozen=True)
class WorkloadSubmission:
    """Incoming Kubernetes AI workload inspected by KAI `pod-grouper`."""

    kind: str  # "PyTorchJob", "JobSet", "LeaderWorkerSet", "MPIJob", "Pod"
    name: str
    namespace: str
    project_annotation: str
    master_or_leader_replicas: int = 1
    worker_replicas: int = 0
    priority_class_name: str = "training-high-priority"
    gpu_per_pod: float = 1.0


def synthesize_kai_podgroup(workload: WorkloadSubmission) -> Dict[str, object]:
    """Simulate KAI `pod-grouper` creating a `PodGroup` from a workload CRD."""
    if workload.kind == "MPIJob":
        # Launcher (1) + Workers (N): gang requires Launcher + all Workers
        min_member = workload.master_or_leader_replicas + workload.worker_replicas
        total_gpus = workload.worker_replicas * workload.gpu_per_pod
    else:
        min_member = workload.master_or_leader_replicas + workload.worker_replicas
        total_gpus = min_member * workload.gpu_per_pod

    return {
        "podgroup_name": f"pg-{workload.name}",
        "owner_kind": workload.kind,
        "queue": workload.project_annotation,
        "min_member": min_member,
        "priority_class_name": workload.priority_class_name,
        "scheduler_name": "kai-scheduler",
        "total_group_gpus": round(total_gpus, 2),
    }


@dataclass(frozen=True)
class KaiJobSpec:
    """A job in the Volume 24 Project 7 20-job benchmark."""

    job_id: str
    job_type: str  # "inference", "training", "research"
    priority: int  # 1000, 100, 0
    gpu_request: float  # 0.5, 1.0, 0.25


def simulate_kai_eight_gpu_session(
    total_cluster_gpus: float = 8.0,
    max_per_type_share_pct: float = 60.0,
    inference_jobs_count: int = 6,
    training_jobs_count: int = 10,
    research_jobs_count: int = 4,
) -> Dict[str, object]:
    """Simulate KAI Scheduler packing the 20 jobs of Volume 24 Project 7 on 8 GPUs."""
    max_gpus_per_type = round(total_cluster_gpus * (max_per_type_share_pct / 100.0), 2)
    free_gpus = total_cluster_gpus

    # Build the 20 jobs
    jobs: List[KaiJobSpec] = []
    for i in range(1, inference_jobs_count + 1):
        jobs.append(KaiJobSpec(f"inference-{i:03d}", "inference", 1000, 0.5))
    for i in range(1, training_jobs_count + 1):
        jobs.append(KaiJobSpec(f"training-{i:03d}", "training", 100, 1.0))
    for i in range(1, research_jobs_count + 1):
        jobs.append(KaiJobSpec(f"research-{i:03d}", "research", 0, 0.25))

    # Sort by priority descending (1000 -> 100 -> 0)
    jobs_sorted = sorted(jobs, key=lambda j: -j.priority)

    used_by_type: Dict[str, float] = {"inference": 0.0, "training": 0.0, "research": 0.0}
    running_counts: Dict[str, int] = {"inference": 0, "training": 0, "research": 0}
    queued_counts: Dict[str, int] = {"inference": 0, "training": 0, "research": 0}
    bind_requests_created = 0

    for job in jobs_sorted:
        next_type_usage = round(used_by_type[job.job_type] + job.gpu_request, 4)
        if job.gpu_request <= round(free_gpus, 4) and next_type_usage <= max_gpus_per_type:
            free_gpus = round(free_gpus - job.gpu_request, 4)
            used_by_type[job.job_type] = next_type_usage
            running_counts[job.job_type] += 1
            bind_requests_created += 1
        else:
            queued_counts[job.job_type] += 1

    total_allocated = round(sum(used_by_type.values()), 2)
    utilization_pct = round((total_allocated / total_cluster_gpus) * 100.0, 2)
    return {
        "total_jobs_submitted": len(jobs),
        "max_gpus_per_type_cap": max_gpus_per_type,
        "used_gpus_by_type": used_by_type,
        "running_counts": running_counts,
        "queued_counts": queued_counts,
        "bind_requests_created": bind_requests_created,
        "total_allocated_gpus": total_allocated,
        "free_gpus": round(free_gpus, 2),
        "utilization_pct": utilization_pct,
        "all_types_making_progress": all(v > 0 for v in running_counts.values()),
    }
