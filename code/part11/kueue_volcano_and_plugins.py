"""Chapter 11.8 — Kueue, Volcano and scheduler plugins.

Deterministic models for:
1. Kubernetes Scheduling Framework extension-point state machine (`QueueSort ->
   PreFilter -> Filter -> PostFilter -> PreScore -> Score -> Reserve -> Permit ->
   Bind`) and Coscheduling `PodGroup` `Permit` gate (`minMember: 4`,
   `scheduleTimeoutSeconds: 300`).
2. Kueue `ClusterQueue` / `ResourceFlavor` / `Cohort` evaluator (`GAK` Examples 7-6,
   7-7, 7-9):
   - Ordered flavor evaluation (`gpu-nvlink-infiniband` nominalQuota `16` before
     `gpu-standard-ethernet` nominalQuota `32`).
   - `flavorFungibility.whenCanBorrow`: `MayStopSearch` (default) vs `TryNextFlavor`.
   - Cohort borrowing (`nominalQuota: 10`, `borrowingLimit: 22` -> max `32` GPUs)
     and preemption (`reclaimWithinCohort: Any`, `withinClusterQueue: LowerPriority`,
     `WorkloadPriorityClass` `10000`).
3. Volcano `Job` & `PodGroup` lifecycle policy evaluator (`minAvailable: 8`,
   `event: PodEvicted -> action: RestartJob`).
4. API Priority and Fairness (`APF`) shuffle-sharding & queue capacity calculator
   (`nominalConcurrencyShares: 50`, `queues: 100`, `handSize: 5`,
   `queueLengthLimit: 200`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


SCHEDULER_FRAMEWORK_PHASES: Tuple[str, ...] = (
    "QueueSort",
    "PreFilter",
    "Filter",
    "PostFilter",
    "PreScore",
    "Score",
    "Reserve",
    "Permit",
    "PreBind",
    "Bind",
    "PostBind",
)


def evaluate_coscheduling_permit_gate(
    pod_group_name: str,
    min_member: int = 4,
    ready_or_waiting_pods: int = 4,
    elapsed_wait_seconds: int = 120,
    schedule_timeout_seconds: int = 300,
) -> Dict[str, object]:
    """Simulate the `scheduler-plugins` Coscheduling `Permit` extension point."""
    if elapsed_wait_seconds > schedule_timeout_seconds:
        return {
            "pod_group": pod_group_name,
            "permit_status": "Reject",
            "unreserve_triggered": True,
            "reason": (
                f"Exceeded scheduleTimeoutSeconds ({elapsed_wait_seconds}s > "
                f"{schedule_timeout_seconds}s); unreserving all held peers"
            ),
        }
    if ready_or_waiting_pods < min_member:
        return {
            "pod_group": pod_group_name,
            "permit_status": "Wait",
            "unreserve_triggered": False,
            "reason": (
                f"Waiting in Permit stage: {ready_or_waiting_pods}/{min_member} "
                f"members reached Reserve"
            ),
        }
    return {
        "pod_group": pod_group_name,
        "permit_status": "Success",
        "unreserve_triggered": False,
        "reason": f"All {min_member} PodGroup members ready; proceeding to Bind",
    }


@dataclass(frozen=True)
class FlavorQuotaState:
    """State of a single ResourceFlavor inside a Kueue ClusterQueue."""

    name: str
    nominal_quota: int
    used_nominal: int
    cohort_borrowable_free: int = 0
    borrowing_limit: int = 0

    @property
    def free_nominal(self) -> int:
        return max(0, self.nominal_quota - self.used_nominal)

    @property
    def max_borrowable_now(self) -> int:
        return min(self.cohort_borrowable_free, self.borrowing_limit)


def select_kueue_resource_flavor(
    requested_gpus: int,
    flavors: List[FlavorQuotaState],
    when_can_borrow: str = "TryNextFlavor",
) -> Dict[str, object]:
    """Implement GAK Ch 7 sidebar 'Kueue Priority Classes and ResourceFlavor'."""
    if when_can_borrow not in ("MayStopSearch", "TryNextFlavor"):
        raise ValueError(f"Unsupported whenCanBorrow mode: {when_can_borrow}")

    if when_can_borrow == "MayStopSearch":
        # Default: if nominal OR borrowing is feasible in current flavor, stop search
        for flv in flavors:
            if requested_gpus <= flv.free_nominal:
                return {
                    "admitted": True,
                    "selected_flavor": flv.name,
                    "used_borrowing": False,
                    "reason": "QuotaReserved",
                }
            if requested_gpus <= flv.free_nominal + flv.max_borrowable_now:
                return {
                    "admitted": True,
                    "selected_flavor": flv.name,
                    "used_borrowing": True,
                    "reason": "QuotaReserved (Borrowed in current flavor via MayStopSearch)",
                }
        return {
            "admitted": False,
            "selected_flavor": None,
            "used_borrowing": False,
            "reason": "InsufficientQuota",
        }

    # `TryNextFlavor`: prefer nominal quota in a fallback flavor over borrowing in the primary flavor
    for flv in flavors:
        if requested_gpus <= flv.free_nominal:
            return {
                "admitted": True,
                "selected_flavor": flv.name,
                "used_borrowing": False,
                "reason": "QuotaReserved",
            }
    for flv in flavors:
        if requested_gpus <= flv.free_nominal + flv.max_borrowable_now:
            return {
                "admitted": True,
                "selected_flavor": flv.name,
                "used_borrowing": True,
                "reason": "QuotaReserved (Borrowed after checking all nominal flavors)",
            }
    return {
        "admitted": False,
        "selected_flavor": None,
        "used_borrowing": False,
        "reason": "InsufficientQuota",
    }


def evaluate_kueue_cohort_and_preemption(
    team_a_nominal: int = 10,
    team_a_borrowing_limit: int = 22,
    team_a_current_used: int = 28,
    incoming_job_team: str = "team-b",
    incoming_job_gpus: int = 8,
    incoming_job_priority: int = 10000,
    running_low_prio_value: int = 100,
    reclaim_within_cohort: str = "Any",
    within_cluster_queue: str = "LowerPriority",
) -> Dict[str, object]:
    """Model GAK Example 7-9 cohort borrowing (`10 + 22 = 32` max) and preemption."""
    team_a_max_effective = team_a_nominal + team_a_borrowing_limit
    team_a_borrowed = max(0, team_a_current_used - team_a_nominal)

    if incoming_job_team != "team-a":
        # Lending team (Team B) needs its nominal quota back from the cohort
        can_reclaim = reclaim_within_cohort == "Any" and team_a_borrowed > 0
        return {
            "team_a_max_effective_gpus": team_a_max_effective,
            "team_a_borrowed_gpus": team_a_borrowed,
            "preempt_triggered": can_reclaim,
            "preemption_reason": (
                "Reclaiming borrowed cohort quota for lending team (reclaimWithinCohort: Any)"
                if can_reclaim
                else "No cohort reclamation permitted"
            ),
        }

    # Same ClusterQueue (Team A): check withinClusterQueue priority preemption
    can_preempt_same_queue = (
        within_cluster_queue == "LowerPriority"
        and incoming_job_priority > running_low_prio_value
        and (team_a_current_used + incoming_job_gpus > team_a_max_effective)
    )
    return {
        "team_a_max_effective_gpus": team_a_max_effective,
        "team_a_borrowed_gpus": team_a_borrowed,
        "preempt_triggered": can_preempt_same_queue,
        "preemption_reason": (
            f"Preempting lower-priority workload ({running_low_prio_value} < {incoming_job_priority}) "
            f"via withinClusterQueue: LowerPriority"
            if can_preempt_same_queue
            else "No same-queue preemption needed or permitted"
        ),
    }


def evaluate_volcano_job_event(
    replicas: int = 8,
    min_available: int = 8,
    ready_pods: int = 8,
    event: Optional[str] = None,
    policy_action: str = "RestartJob",
) -> Dict[str, object]:
    """Evaluate Volcano Job gang start and `PodEvicted -> RestartJob` lifecycle policy."""
    if event == "PodEvicted" and policy_action == "RestartJob":
        return {
            "job_state": "Restarting",
            "action_taken": "RestartJob (tearing down all 8 gang pods and requeueing)",
            "active_pods": 0,
        }
    if ready_pods < min_available:
        return {
            "job_state": "Pending",
            "action_taken": f"Holding PodGroup until minAvailable ({min_available}) is met",
            "active_pods": 0,
        }
    return {
        "job_state": "Running",
        "action_taken": f"All {replicas} replicas running under schedulerName: volcano",
        "active_pods": replicas,
    }


def compute_apf_queue_capacity(
    nominal_concurrency_shares: int = 50,
    queues: int = 100,
    hand_size: int = 5,
    queue_length_limit: int = 200,
) -> Dict[str, int]:
    """Compute APF queue parameters from Volume 03 Section 10."""
    return {
        "nominal_concurrency_shares": nominal_concurrency_shares,
        "queues": queues,
        "hand_size": hand_size,
        "queue_length_limit": queue_length_limit,
        "max_queued_requests_total": queues * queue_length_limit,
    }
