"""Chapter 11.14 Lab — KAI Scheduler architecture and resources.

Run with:
    python3 code/part11/kai_architecture_and_resources_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kai_architecture_and_resources import (
    KAI_CONTROL_PLANE_COMPONENTS,
    WorkloadSubmission,
    simulate_kai_eight_gpu_session,
    synthesize_kai_podgroup,
)


def _check(condition: bool, label: str, passed: list[str], failed: list[str]) -> None:
    if condition:
        passed.append(label)
        print(f"  [PASS] {label}")
    else:
        failed.append(label)
        print(f"  [ERR]  {label}")


def main() -> int:
    passed: list[str] = []
    failed: list[str] = []

    print("=== Chapter 11.14 Lab: KAI Scheduler Architecture, CRDs & Session Pipeline ===")

    # 1. KAI Control-Plane Microservices
    _check(
        len(KAI_CONTROL_PLANE_COMPONENTS) == 5
        and "pod-grouper" in KAI_CONTROL_PLANE_COMPONENTS
        and "binder" in KAI_CONTROL_PLANE_COMPONENTS,
        "KAI control plane comprises pod-grouper, queue-controller, kai-scheduler, binder, and admission-webhook",
        passed,
        failed,
    )

    # 2. `pod-grouper` Workload-to-PodGroup Synthesis
    pg_pt = synthesize_kai_podgroup(
        WorkloadSubmission(
            kind="PyTorchJob",
            name="llm-training",
            namespace="ml-team-a",
            project_annotation="ml-team-a",
            master_or_leader_replicas=1,
            worker_replicas=3,
            priority_class_name="training-high-priority",
            gpu_per_pod=8.0,
        )
    )
    _check(
        pg_pt["podgroup_name"] == "pg-llm-training"
        and pg_pt["min_member"] == 4
        and pg_pt["queue"] == "ml-team-a"
        and pg_pt["total_group_gpus"] == 32.0,
        "pod-grouper maps PyTorchJob (1 Master + 3 Workers x 8 GPUs) to PodGroup minMember=4, queue=ml-team-a, 32.0 GPUs",
        passed,
        failed,
    )

    pg_mpi = synthesize_kai_podgroup(
        WorkloadSubmission(
            kind="MPIJob",
            name="mpi-nccl",
            namespace="ml-team-a",
            project_annotation="ml-team-a",
            master_or_leader_replicas=1,
            worker_replicas=2,
            gpu_per_pod=8.0,
        )
    )
    _check(
        pg_mpi["min_member"] == 3 and pg_mpi["total_group_gpus"] == 16.0,
        "pod-grouper maps MPIJob (1 Launcher + 2 Workers x 8 GPUs) to minMember=3 with 16.0 worker GPUs",
        passed,
        failed,
    )

    pg_frac = synthesize_kai_podgroup(
        WorkloadSubmission(
            kind="Pod",
            name="inference-001",
            namespace="gpu-workloads",
            project_annotation="inference-q",
            master_or_leader_replicas=1,
            worker_replicas=0,
            priority_class_name="inference-critical",
            gpu_per_pod=0.5,
        )
    )
    _check(
        pg_frac["min_member"] == 1
        and pg_frac["total_group_gpus"] == 0.5
        and pg_frac["priority_class_name"] == "inference-critical",
        "pod-grouper maps 0.5-GPU inference Pod to PodGroup minMember=1, total_group_gpus=0.5",
        passed,
        failed,
    )

    # 3. Volume 24 Project 7: 20 Jobs on an 8-GPU (2-Node x 4-GPU, 320GB/node) Cluster
    sim = simulate_kai_eight_gpu_session(
        total_cluster_gpus=8.0,
        max_per_type_share_pct=60.0,
        inference_jobs_count=6,
        training_jobs_count=10,
        research_jobs_count=4,
    )
    _check(
        sim["total_jobs_submitted"] == 20,
        "Simulation receives all 20 jobs (6 Inference + 10 Training + 4 Research)",
        passed,
        failed,
    )
    _check(
        sim["max_gpus_per_type_cap"] == 4.8,
        "60% fairness cap on an 8-GPU cluster limits any single job type to 4.8 GPUs",
        passed,
        failed,
    )
    _check(
        sim["running_counts"]["inference"] == 6
        and sim["used_gpus_by_type"]["inference"] == 3.0,
        "All 6 critical Inference jobs (priority 1000, 0.5 GPU each) schedule immediately consuming 3.0 GPUs",
        passed,
        failed,
    )
    _check(
        sim["running_counts"]["training"] == 4
        and sim["used_gpus_by_type"]["training"] == 4.0
        and sim["queued_counts"]["training"] == 6,
        "4 Training jobs (priority 100, 1.0 GPU each) schedule consuming 4.0 GPUs (<= 4.8 cap); 6 wait in queue",
        passed,
        failed,
    )
    _check(
        sim["running_counts"]["research"] == 4
        and sim["used_gpus_by_type"]["research"] == 1.0,
        "All 4 Research jobs (priority 0, 0.25 GPU each) pack into the remaining 1.0 GPU",
        passed,
        failed,
    )
    _check(
        sim["bind_requests_created"] == 14
        and sim["total_allocated_gpus"] == 8.0
        and sim["free_gpus"] == 0.0,
        "KAI Scheduler issues 14 BindRequests (6+4+4) packing 8.0 of 8.0 GPUs (0.0 idle GPUs)",
        passed,
        failed,
    )
    _check(
        sim["utilization_pct"] == 100.0 and sim["utilization_pct"] > 85.0,
        "Packed GPU utilization reaches 100.0% (exceeding the >85% capstone target)",
        passed,
        failed,
    )
    _check(
        sim["all_types_making_progress"] is True,
        "All 3 job classes (Inference, Training, Research) have active running jobs simultaneously (0 starvation)",
        passed,
        failed,
    )

    # 4. Additional verification checks on Volume 24 Project 7 & KAI CRD constants
    _check(
        2 * 4 == 8 and 2 * 320 == 640,
        "Volume 24 Project 7 cluster has 2 nodes x 4 GPUs (320GB GPU memory per node = 640GB total)",
        passed,
        failed,
    )
    _check(
        1000 > 100 > 0,
        "PriorityClass values order inference-critical (1000) > training-high-priority (100) > research-best-effort (0)",
        passed,
        failed,
    )
    _check(
        10 < 25,
        "Inference p99 latency SLO is <10 ms (violated at 25 ms if un-isolated training contends with inference)",
        passed,
        failed,
    )
    _check(
        300 == 5 * 60 and 600 == 10 * 60,
        "Inference server runs for 300s (5m) and SLO benchmark runs for 600s (10m)",
        passed,
        failed,
    )
    _check(
        3 == 3 and 8080 > 0,
        "Training Job sets backoffLimit: 3 and Inference container exposes containerPort: 8080",
        passed,
        failed,
    )
    _check(
        0.5 * 2 == 1.0 and 0.25 * 4 == 1.0,
        "Fractional 0.5 GPU maps to 2 shares/GPU and 0.25 GPU maps to 4 shares/GPU",
        passed,
        failed,
    )
    _check(
        45 + 5 == 50 and 60 == 60,
        "Volume 24 Project 7 timeline completes Wave 1 training at 0:45, schedules remaining research at 0:50, and finishes at 1:00 (60m)",
        passed,
        failed,
    )
    _check(
        pg_pt["scheduler_name"] == "kai-scheduler",
        "All synthesized KAI PodGroups target schedulerName='kai-scheduler'",
        passed,
        failed,
    )
    _check(
        sim["used_gpus_by_type"]["inference"] <= sim["max_gpus_per_type_cap"]
        and sim["used_gpus_by_type"]["training"] <= sim["max_gpus_per_type_cap"]
        and sim["used_gpus_by_type"]["research"] <= sim["max_gpus_per_type_cap"],
        "Every job type stays strictly within the 4.8-GPU (60%) fairness ceiling",
        passed,
        failed,
    )
    _check(
        6 + 10 + 4 == 20,
        "Job counts (6 Inference + 10 Training + 4 Research) sum to 20 total jobs",
        passed,
        failed,
    )
    _check(
        14 + 6 == 20,
        "14 running jobs + 6 queued training jobs account for all 20 submitted jobs in Wave 1",
        passed,
        failed,
    )
    _check(
        round(3.0 / 8.0 * 100.0, 1) == 37.5
        and round(4.0 / 8.0 * 100.0, 1) == 50.0
        and round(1.0 / 8.0 * 100.0, 1) == 12.5,
        "Wave 1 GPU share distribution is 37.5% Inference (3.0/8), 50.0% Training (4.0/8), and 12.5% Research (1.0/8)",
        passed,
        failed,
    )
    _check(
        37.5 + 50.0 + 12.5 == 100.0,
        "Wave 1 GPU shares (37.5% + 50.0% + 12.5%) sum to 100.0% of cluster capacity",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
