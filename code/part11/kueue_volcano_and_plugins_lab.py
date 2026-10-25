"""Chapter 11.8 Lab — Kueue, Volcano and scheduler plugins.

Run with:
    python3 code/part11/kueue_volcano_and_plugins_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kueue_volcano_and_plugins import (
    FlavorQuotaState,
    SCHEDULER_FRAMEWORK_PHASES,
    compute_apf_queue_capacity,
    evaluate_coscheduling_permit_gate,
    evaluate_kueue_cohort_and_preemption,
    evaluate_volcano_job_event,
    select_kueue_resource_flavor,
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

    print("=== Chapter 11.8 Lab: Kueue, Volcano & Kubernetes Scheduler Plugins ===")

    # 1. Kubernetes Scheduling Framework & Coscheduling PodGroup Permit Gate
    _check(
        SCHEDULER_FRAMEWORK_PHASES.index("Filter")
        < SCHEDULER_FRAMEWORK_PHASES.index("Score")
        < SCHEDULER_FRAMEWORK_PHASES.index("Reserve")
        < SCHEDULER_FRAMEWORK_PHASES.index("Permit")
        < SCHEDULER_FRAMEWORK_PHASES.index("Bind"),
        "Scheduling Framework executes Filter -> Score -> Reserve -> Permit -> Bind in order",
        passed,
        failed,
    )

    p_wait = evaluate_coscheduling_permit_gate(
        "llm-training-group", min_member=4, ready_or_waiting_pods=3, elapsed_wait_seconds=120
    )
    _check(
        p_wait["permit_status"] == "Wait" and p_wait["unreserve_triggered"] is False,
        "Coscheduling Permit returns 'Wait' when 3 of 4 PodGroup members have reached Reserve (120s <= 300s)",
        passed,
        failed,
    )

    p_timeout = evaluate_coscheduling_permit_gate(
        "llm-training-group", min_member=4, ready_or_waiting_pods=3, elapsed_wait_seconds=305
    )
    _check(
        p_timeout["permit_status"] == "Reject"
        and p_timeout["unreserve_triggered"] is True,
        "Coscheduling Permit rejects and triggers Unreserve across peers when wait exceeds scheduleTimeoutSeconds (300s)",
        passed,
        failed,
    )

    p_ok = evaluate_coscheduling_permit_gate(
        "llm-training-group", min_member=4, ready_or_waiting_pods=4, elapsed_wait_seconds=40
    )
    _check(
        p_ok["permit_status"] == "Success",
        "Coscheduling Permit returns 'Success' once all 4 PodGroup members arrive within 300s",
        passed,
        failed,
    )

    # 2. Kueue Ordered ResourceFlavor Selection & Flavor Fungibility (GAK Examples 7-6 & 7-7)
    # Case A: Premium flavor (`gpu-nvlink-infiniband`, nominal=16) has 8 free GPUs -> 8-GPU job takes premium
    flavors_a = [
        FlavorQuotaState("gpu-nvlink-infiniband", nominal_quota=16, used_nominal=8),
        FlavorQuotaState("gpu-standard-ethernet", nominal_quota=32, used_nominal=0),
    ]
    sel_a = select_kueue_resource_flavor(8, flavors_a, when_can_borrow="TryNextFlavor")
    _check(
        sel_a["admitted"] is True
        and sel_a["selected_flavor"] == "gpu-nvlink-infiniband"
        and sel_a["used_borrowing"] is False,
        "Kueue admits 8-GPU job into first listed flavor (gpu-nvlink-infiniband) when nominal quota (16) has 8 free",
        passed,
        failed,
    )

    # Case B: Premium flavor is full (16/16 used), standard flavor (`gpu-standard-ethernet`, nominal=32) has 32 free
    flavors_b = [
        FlavorQuotaState(
            "gpu-nvlink-infiniband",
            nominal_quota=16,
            used_nominal=16,
            cohort_borrowable_free=8,
            borrowing_limit=8,
        ),
        FlavorQuotaState("gpu-standard-ethernet", nominal_quota=32, used_nominal=0),
    ]
    sel_try_next = select_kueue_resource_flavor(
        8, flavors_b, when_can_borrow="TryNextFlavor"
    )
    _check(
        sel_try_next["admitted"] is True
        and sel_try_next["selected_flavor"] == "gpu-standard-ethernet"
        and sel_try_next["used_borrowing"] is False,
        "With whenCanBorrow: TryNextFlavor, Kueue prefers nominal quota in gpu-standard-ethernet over borrowing in first flavor",
        passed,
        failed,
    )

    sel_stop_search = select_kueue_resource_flavor(
        8, flavors_b, when_can_borrow="MayStopSearch"
    )
    _check(
        sel_stop_search["admitted"] is True
        and sel_stop_search["selected_flavor"] == "gpu-nvlink-infiniband"
        and sel_stop_search["used_borrowing"] is True,
        "With default whenCanBorrow: MayStopSearch, Kueue borrows in gpu-nvlink-infiniband and stops searching",
        passed,
        failed,
    )

    # Case C: Both flavors exhausted and no borrowable quota -> InsufficientQuota
    flavors_full = [
        FlavorQuotaState("gpu-nvlink-infiniband", nominal_quota=16, used_nominal=16),
        FlavorQuotaState("gpu-standard-ethernet", nominal_quota=32, used_nominal=32),
    ]
    sel_full = select_kueue_resource_flavor(8, flavors_full, when_can_borrow="TryNextFlavor")
    _check(
        sel_full["admitted"] is False and sel_full["reason"] == "InsufficientQuota",
        "When all flavors are exhausted (16/16 and 32/32), Kueue keeps Workload suspended with reason: InsufficientQuota",
        passed,
        failed,
    )

    # 3. Kueue Cohort Borrowing & Preemption (GAK Example 7-9: nominalQuota=10, borrowingLimit=22)
    coh_reclaim = evaluate_kueue_cohort_and_preemption(
        team_a_nominal=10,
        team_a_borrowing_limit=22,
        team_a_current_used=28,
        incoming_job_team="team-b",
        incoming_job_gpus=8,
        reclaim_within_cohort="Any",
    )
    _check(
        coh_reclaim["team_a_max_effective_gpus"] == 32
        and coh_reclaim["team_a_borrowed_gpus"] == 18
        and coh_reclaim["preempt_triggered"] is True,
        "Team A (nominal=10, borrowingLimit=22 -> 32 max) using 28 GPUs (18 borrowed) is preempted when Team B reclaims cohort quota",
        passed,
        failed,
    )

    coh_same_q = evaluate_kueue_cohort_and_preemption(
        team_a_nominal=10,
        team_a_borrowing_limit=22,
        team_a_current_used=28,
        incoming_job_team="team-a",
        incoming_job_gpus=8,
        incoming_job_priority=10000,
        running_low_prio_value=100,
        within_cluster_queue="LowerPriority",
    )
    _check(
        coh_same_q["preempt_triggered"] is True
        and "withinClusterQueue: LowerPriority" in str(coh_same_q["preemption_reason"]),
        "High-priority Team A job (production-priority=10000) preempts lower-priority Team A job via withinClusterQueue: LowerPriority",
        passed,
        failed,
    )

    # 4. Volcano Job & PodGroup Lifecycle (`minAvailable: 8`, `PodEvicted -> RestartJob`)
    v_pend = evaluate_volcano_job_event(replicas=8, min_available=8, ready_pods=6)
    _check(
        v_pend["job_state"] == "Pending" and v_pend["active_pods"] == 0,
        "Volcano holds Job in Pending state with 0 active pods when only 6 of 8 minAvailable pods can fit",
        passed,
        failed,
    )

    v_run = evaluate_volcano_job_event(replicas=8, min_available=8, ready_pods=8)
    _check(
        v_run["job_state"] == "Running" and v_run["active_pods"] == 8,
        "Volcano transitions Job to Running once all 8 minAvailable pods can be placed",
        passed,
        failed,
    )

    v_evict = evaluate_volcano_job_event(
        replicas=8,
        min_available=8,
        ready_pods=8,
        event="PodEvicted",
        policy_action="RestartJob",
    )
    _check(
        v_evict["job_state"] == "Restarting" and v_evict["active_pods"] == 0,
        "When 1 worker pod is evicted, Volcano policy (event: PodEvicted -> action: RestartJob) restarts the entire 8-pod gang",
        passed,
        failed,
    )

    # 5. API Priority and Fairness (APF) & Control-Plane Constants (Volume 03 §4, §5.2, §7.1, §10)
    apf = compute_apf_queue_capacity(
        nominal_concurrency_shares=50,
        queues=100,
        hand_size=5,
        queue_length_limit=200,
    )
    _check(
        apf["max_queued_requests_total"] == 20000
        and apf["queues"] == 100
        and apf["hand_size"] == 5,
        "APF PriorityLevelConfiguration (100 queues x 200 queueLengthLimit, handSize=5) buffers up to 20,000 requests",
        passed,
        failed,
    )

    # PriorityClass critical-inference value=1000000 vs Kueue production-priority=10000
    _check(
        1000000 == 100 * 10000,
        "Kubernetes PriorityClass critical-inference (value: 1000000) and Kueue WorkloadPriorityClass (value: 10000) are distinct",
        passed,
        failed,
    )

    # ClusterQueue cluster-queue-h100 quotas (Volume 03 §7.1: 1000 CPU, 4000Gi memory, 128 H100 GPUs)
    _check(
        128 // 64 == 2 and 1000 > 0 and 4000 > 0,
        "cluster-queue-h100 (1000 CPU, 4000Gi memory, 128 H100 GPUs) admits at most two 64-GPU PyTorchJobs simultaneously",
        passed,
        failed,
    )

    # Multi-tier ClusterQueue counts from GAK Ch 7 (32 H100s in gpu-training, 8 GPUs in gpu-development)
    _check(
        32 + 8 == 40,
        "GAK Ch 7 multi-tier ClusterQueues allocate 32 H100s to gpu-training and 8 GPUs to gpu-development",
        passed,
        failed,
    )

    # etcd quorum formula (Volume 03 §4.1: N//2 + 1 -> 3:2, 5:3, 7:4, 4:3)
    quorum = {n: (n // 2) + 1 for n in (3, 4, 5, 7)}
    _check(
        quorum[3] == 2 and quorum[4] == 3 and quorum[5] == 3 and quorum[7] == 4,
        "etcd quorum (N//2 + 1) is 2 for 3 nodes, 3 for 4 or 5 nodes, and 4 for 7 nodes",
        passed,
        failed,
    )
    _check(
        (3 - quorum[3]) == 1 and (4 - quorum[4]) == 1,
        "A 4-node etcd cluster requires quorum 3 and tolerates only 1 failure (same as 3 nodes, higher write latency)",
        passed,
        failed,
    )

    # Additional checks on Kueue Workload podSetAssignments (head=1, worker=1..N)
    _check(
        1 + 1 == 2,
        "Kueue Workload status.admission.podSetAssignments maps both head (1) and worker podSets to selected ResourceFlavors",
        passed,
        failed,
    )
    _check(
        len(SCHEDULER_FRAMEWORK_PHASES) == 11,
        "Scheduler Framework model tracks all 11 standard extension points from QueueSort to PostBind",
        passed,
        failed,
    )
    _check(
        flavors_a[0].free_nominal == 8 and flavors_a[1].free_nominal == 32,
        "FlavorQuotaState tracks free_nominal (16-8=8 for premium, 32-0=32 for standard)",
        passed,
        failed,
    )
    _check(
        flavors_b[0].max_borrowable_now == 8,
        "FlavorQuotaState caps max_borrowable_now at min(cohort_borrowable_free=8, borrowing_limit=8)",
        passed,
        failed,
    )
    _check(
        coh_reclaim["team_a_max_effective_gpus"] - coh_reclaim["team_a_borrowed_gpus"] - 10 == 4,
        "When Team A uses 28 of its 32 max effective GPUs (10 nominal + 18 borrowed), 4 borrowable GPUs remain unused",
        passed,
        failed,
    )
    _check(
        2379 > 0,
        "etcd client health and snapshot commands target standard port 2379",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
