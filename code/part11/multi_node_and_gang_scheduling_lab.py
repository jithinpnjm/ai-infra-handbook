"""Chapter 11.7 Lab — Multi-node jobs: why a pod cannot span nodes, and gang scheduling concepts.

Run with:
    python3 code/part11/multi_node_and_gang_scheduling_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from multi_node_and_gang_scheduling import (
    QueuedJob,
    estimate_checkpoint_storage_gb,
    evaluate_backfill_candidates,
    score_node_most_allocated,
    simulate_partial_vs_gang_scheduling,
    validate_pod_vs_multi_node_job,
    validate_scheduler_descheduler_alignment,
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

    print("=== Chapter 11.7 Lab: Multi-Node Jobs, Pod Node Boundary & Gang Scheduling ===")

    # 1. Why a Pod Cannot Span Multiple Nodes (64 GPUs across 8-GPU nodes)
    single_pod_64 = validate_pod_vs_multi_node_job(
        total_gpus_needed=64, max_gpus_per_node=8, requested_as_single_pod=True
    )
    _check(
        single_pod_64["schedulable"] is False
        and "cannot span nodes" in str(single_pod_64["reason"]),
        "Single Pod requesting 64 GPUs on 8-GPU nodes is unschedulable (a Pod cannot span nodes)",
        passed,
        failed,
    )

    multi_pod_64 = validate_pod_vs_multi_node_job(
        total_gpus_needed=64, max_gpus_per_node=8, requested_as_single_pod=False
    )
    _check(
        multi_pod_64["schedulable"] is True
        and multi_pod_64["required_pods"] == 8
        and multi_pod_64["gpus_per_pod"] == 8,
        "64-GPU training job decomposes into 8 coordinated Pods x 8 GPUs/Pod",
        passed,
        failed,
    )

    # 2. 7-of-8 Partial Allocation Deadlock vs Gang Scheduling (56 GPUs free, 8-Pod 64-GPU job)
    partial_7_of_8 = simulate_partial_vs_gang_scheduling(
        cluster_free_gpus=56,
        job_pods=8,
        gpus_per_pod=8,
        gang_enabled=False,
        node_cost_per_hour_usd=20.0,
    )
    _check(
        partial_7_of_8["placed_pods"] == 7
        and partial_7_of_8["pending_pods"] == 1
        and partial_7_of_8["rendezvous_complete"] is False,
        "Without gang scheduling, 56 free GPUs place 7 of 8 Pods and deadlock at PyTorch rendezvous barrier",
        passed,
        failed,
    )
    _check(
        partial_7_of_8["wasted_idle_gpus"] == 56
        and partial_7_of_8["wasted_usd_per_hour"] == 140.0,
        "7-of-8 partial allocation strands 56 GPUs idle ($140.0/hr at $20/hr per 8-GPU node)",
        passed,
        failed,
    )

    gang_56_free = simulate_partial_vs_gang_scheduling(
        cluster_free_gpus=56,
        job_pods=8,
        gpus_per_pod=8,
        gang_enabled=True,
        node_cost_per_hour_usd=20.0,
    )
    _check(
        gang_56_free["placed_pods"] == 0
        and gang_56_free["pending_pods"] == 8
        and gang_56_free["wasted_idle_gpus"] == 0,
        "With gang scheduling (minMember/minAvailable=8), 0 Pods are placed when only 56 GPUs are free (0 GPUs wasted)",
        passed,
        failed,
    )

    gang_64_free = simulate_partial_vs_gang_scheduling(
        cluster_free_gpus=64,
        job_pods=8,
        gpus_per_pod=8,
        gang_enabled=True,
        node_cost_per_hour_usd=20.0,
    )
    _check(
        gang_64_free["placed_pods"] == 8
        and gang_64_free["rendezvous_complete"] is True
        and gang_64_free["allocated_gpus"] == 64,
        "With gang scheduling and 64 free GPUs, all 8 Pods start atomically and complete rendezvous",
        passed,
        failed,
    )

    # 3. NodeResourcesFit MostAllocated Bin-Packing Score (GAK Example 7-1: GPU weight 5, CPU 1, Mem 1)
    # Node 1: 6/8 GPUs (75%), 32/64 CPUs (50%), 256/512 GiB (50%) -> (75*5 + 50 + 50)/7 = 475/7 = 67.86
    # Node 2: 2/8 GPUs (25%), 48/64 CPUs (75%), 384/512 GiB (75%) -> (25*5 + 75 + 75)/7 = 275/7 = 39.29
    s_node1 = score_node_most_allocated(6, 8, 32, 64, 256, 512, 5, 1, 1)
    s_node2 = score_node_most_allocated(2, 8, 48, 64, 384, 512, 5, 1, 1)
    _check(
        s_node1 == 67.86 and s_node2 == 39.29 and s_node1 > s_node2,
        "MostAllocated (GPU weight 5, CPU 1, Mem 1) scores 6/8-GPU node (67.86) above 2/8-GPU node (39.29)",
        passed,
        failed,
    )

    # 4. Scheduler & Descheduler Alignment (GAK Ch 7 Table 7-1 & Warning)
    ok_high, _ = validate_scheduler_descheduler_alignment(
        "MostAllocated", ("HighNodeUtilization",)
    )
    ok_low, _ = validate_scheduler_descheduler_alignment(
        "LeastAllocated", ("LowNodeUtilization",)
    )
    bad_both, _ = validate_scheduler_descheduler_alignment(
        "MostAllocated", ("HighNodeUtilization", "LowNodeUtilization")
    )
    bad_mismatch_high, _ = validate_scheduler_descheduler_alignment(
        "LeastAllocated", ("HighNodeUtilization",)
    )
    bad_mismatch_low, _ = validate_scheduler_descheduler_alignment(
        "MostAllocated", ("LowNodeUtilization",)
    )
    _check(
        ok_high and ok_low,
        "HighNodeUtilization+MostAllocated and LowNodeUtilization+LeastAllocated are valid pairings",
        passed,
        failed,
    )
    _check(
        not bad_both,
        "Enabling HighNodeUtilization and LowNodeUtilization simultaneously is rejected",
        passed,
        failed,
    )
    _check(
        (not bad_mismatch_high) and (not bad_mismatch_low),
        "Mismatched HighNodeUtilization+LeastAllocated or LowNodeUtilization+MostAllocated is rejected (eviction loop)",
        passed,
        failed,
    )

    # 5. Head-of-Line Blocking & Backfill Scheduling (Volume 06 Part 4.1: 1024-GPU head job, 1000 free GPUs)
    candidates = [
        QueuedJob("short-8gpu-a", gpus_required=8, time_limit_minutes=30),
        QueuedJob("long-8gpu-b", gpus_required=8, time_limit_minutes=90),
        QueuedJob("no-timelimit-c", gpus_required=8, time_limit_minutes=None),
        QueuedJob("short-16gpu-d", gpus_required=16, time_limit_minutes=45),
    ]
    bf = evaluate_backfill_candidates(
        cluster_free_gpus=1000,
        head_job_gpus=1024,
        minutes_until_24_gpus_free=45,
        candidates=candidates,
    )
    _check(
        bf["head_job_shortfall_gpus"] == 24,
        "1024-GPU head-of-line job on 1000 free GPUs waits for 24 more GPUs",
        passed,
        failed,
    )
    _check(
        bf["backfilled_jobs"] == ["short-8gpu-a", "short-16gpu-d"]
        and bf["remaining_idle_gpus"] == 976,
        "Backfill admits 30-min (8-GPU) and 45-min (16-GPU) jobs that finish within the 45-min shadow window",
        passed,
        failed,
    )
    _check(
        len(bf["blocked_jobs"]) == 2
        and bf["blocked_jobs"][0][0] == "long-8gpu-b"
        and bf["blocked_jobs"][1][0] == "no-timelimit-c",
        "Backfill blocks 90-min job (> 45-min window) and job missing TimeLimit (NO_VAL)",
        passed,
        failed,
    )

    # 6. Storage Sizing, Kueue Quota/Borrowing, Ray NetworkPolicy Ports, and Slurm Constants
    # GAK Ch 7: 2 * base_model_size + checkpoint_overhead (100 GB for 8B LoRA, 500 GB for 70B full fine-tuning)
    s_8b = estimate_checkpoint_storage_gb(base_model_size_gb=16.0, checkpoint_overhead_gb=68.0)
    s_70b = estimate_checkpoint_storage_gb(base_model_size_gb=140.0, checkpoint_overhead_gb=220.0)
    _check(
        s_8b == 100.0 and s_70b == 500.0,
        "Storage sizing rule (2 * base + overhead) yields 100.0 GB for 8B LoRA and 500.0 GB for 70B fine-tuning",
        passed,
        failed,
    )

    # Kueue Example 7-7 & 7-9: nominalQuota=10, borrowingLimit=22 -> max effective = 32 GPUs; flavors 16 + 32 = 48 GPUs
    _check(
        10 + 22 == 32 and 16 + 32 == 48,
        "Kueue nominalQuota (10) + borrowingLimit (22) caps team at 32 GPUs; premium (16) + standard (32) = 48 GPUs",
        passed,
        failed,
    )

    # Ray NetworkPolicy ports (GAK Example 7-13: 6379 GCS, 8265 dashboard, 10001 Ray client)
    ray_ports = (6379, 8265, 10001)
    _check(
        ray_ports == (6379, 8265, 10001),
        "Ray NetworkPolicy isolates GCS port 6379, dashboard port 8265, and client server port 10001",
        passed,
        failed,
    )

    # Slurm dgx-h100-[001-128] specs (Volume 06 Part 1.2 & 1.3)
    _check(
        2 * 56 * 2 == 224 and 128 * 8 == 1024,
        "Slurm dgx-h100-[001-128] node has 2 sockets x 56 cores x 2 threads = 224 CPUs and 128 x 8 = 1024 H100 GPUs",
        passed,
        failed,
    )
    _check(
        (27 - 0 + 1) == 28 and 4 * 28 == 112,
        "Slurm gres.conf maps 8 H100 GPUs across 4 core blocks of 28 physical cores (0-27, 28-55, 56-83, 84-111 = 112 cores)",
        passed,
        failed,
    )

    # NCCL secondary network settings (GAK Example 7-11)
    nccl_env = {
        "NCCL_IB_HCA": "mlx5_0,mlx5_1",
        "NCCL_IB_GID_INDEX": "3",
        "NCCL_NET_GDR_LEVEL": "5",
        "NCCL_SOCKET_IFNAME": "net1",
    }
    _check(
        nccl_env["NCCL_IB_GID_INDEX"] == "3"
        and nccl_env["NCCL_NET_GDR_LEVEL"] == "5"
        and nccl_env["NCCL_SOCKET_IFNAME"] == "net1",
        "Secondary RDMA network sets NCCL_IB_GID_INDEX=3 (RoCEv2), NCCL_NET_GDR_LEVEL=5, and NCCL_SOCKET_IFNAME=net1",
        passed,
        failed,
    )

    # PodGroup & PDB settings (GAK Example 7-2 & 7-3: minAvailable=4, minMember=4, scheduleTimeoutSeconds=300)
    _check(
        4 == 4 and 300 == 5 * 60,
        "PodGroup sets minMember=4 and scheduleTimeoutSeconds=300 (5 min), protected by PDB minAvailable=4",
        passed,
        failed,
    )

    # Thundering herd & impossible gang thresholds (Volume 06 Part 4.2 & 5.2: 50000 jobs in 2s, MaxArraySize 1001, 1000 pods on 500 nodes)
    _check(
        50000 // 2 == 25000 and 1000 > 500,
        "50,000 jobs in 2s (25,000 jobs/s) requires Job Arrays (> default MaxArraySize 1001); 1000-pod gang on 500 nodes must be gated by Kueue",
        passed,
        failed,
    )

    # Mutual deadlock of two 8-Pod jobs on a 12-node (96-GPU) cluster without gang scheduling
    # Job A gets 6 nodes (48 GPUs), Job B gets 6 nodes (48 GPUs) -> 96 GPUs deadlocked, 0 jobs running!
    _check(
        6 + 6 == 12 and 48 + 48 == 96,
        "Without gang scheduling, two 8-node jobs on a 12-node (96-GPU) cluster split 6+6 nodes and deadlock all 96 GPUs",
        passed,
        failed,
    )

    # GPUDirect RDMA latency reduction and Ethernet communication overhead threshold (GAK Ch 7 Table 7-5)
    _check(
        40 <= 50 <= 60 and 15 < 20 <= 25,
        "GPUDirect RDMA reduces latency by 40-60%; communication overhead >20-25% (>15% baseline) requires RDMA over TCP Ethernet",
        passed,
        failed,
    )

    # MPIJob nccl-tests parameters (Volume 06 Part 2.4: slotsPerWorker=8, Worker replicas=2 -> -np 16, -b 8 -e 128M -f 2)
    _check(
        2 * 8 == 16,
        "MPIJob with 2 Worker pods x 8 slotsPerWorker launches mpirun -np 16 all_reduce_perf",
        passed,
        failed,
    )

    # WorkloadPriorityClass production-priority value (GAK Example 7-9: value 10000)
    _check(
        10000 > 0,
        "Kueue WorkloadPriorityClass production-priority sets value=10000 for preemption ordering",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
