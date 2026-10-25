"""Chapter 11.13 — KAI Scheduler: why default scheduling is not enough.

Deterministic models for:
1. Multi-tenant GPU cluster quota & utilization comparison (`volume-23/chapter-07`:
   `32` GPUs across `4` nodes: `research` `16` GPUs = `50.0%`, `data-eng` `12` GPUs =
   `37.5%`, `interns` `4` GPUs = `12.5%`; static node partitioning `60.0%` utilization
   vs shared fair-share quota `85.0%` utilization).
2. Weighted Fair-Share Deficit & Priority Scorer (`volume-23/chapter-12`:
   `deficit = (current_usage - quota) / quota`, `priority = -deficit + (0.1 if gpu_count < 4 else 0)`,
   Professor A `500` GPU-hr quota using `600` vs Professor B `250` GPU-hr quota using `100`
   -> `700 / 750 = 93.33%` / `~93%` cluster utilization).
3. KAI Scheduler (`kai.run.ai/v1`, `schedulerName: kai-scheduler`, `GAK` Example 7-5)
   capability evaluator vs default `kube-scheduler` (gang scheduling, `Project` quota
   borrowing, NVLink/NVSwitch topology, and fractional GPU allocation).
4. Graceful Preemption & Checkpoint Recovery Timeline (`0s` SIGTERM -> `30s` grace
   -> `45s` new job start -> `90s` resume = `~2` min wall-clock delay, `0` compute lost).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


def evaluate_three_team_cluster_quotas(
    total_gpus: int = 32,
    research_gpus: int = 16,
    data_eng_gpus: int = 12,
    intern_gpus: int = 4,
    static_partition_util_pct: float = 60.0,
    dynamic_shared_util_pct: float = 85.0,
) -> Dict[str, float]:
    """Compute the Volume 23 Ch 7 32-GPU (4-node) multi-tenant quota shares and utilization gain."""
    if research_gpus + data_eng_gpus + intern_gpus != total_gpus:
        raise ValueError("Team GPU quotas must sum to total_gpus")
    return {
        "total_gpus": float(total_gpus),
        "research_share_pct": round((research_gpus / total_gpus) * 100.0, 2),
        "data_eng_share_pct": round((data_eng_gpus / total_gpus) * 100.0, 2),
        "intern_share_pct": round((intern_gpus / total_gpus) * 100.0, 2),
        "static_partition_util_pct": static_partition_util_pct,
        "dynamic_shared_util_pct": dynamic_shared_util_pct,
        "utilization_gain_pct_points": round(
            dynamic_shared_util_pct - static_partition_util_pct, 2
        ),
    }


@dataclass(frozen=True)
class TeamFairShareState:
    """Monthly GPU-hour quota and usage state for a research team (Volume 23 Ch 12)."""

    team_id: str
    funding_usd: int
    monthly_quota_gpu_hours: float
    current_usage_gpu_hours: float


def score_fair_share_job(
    team: TeamFairShareState, job_gpu_count: int
) -> Dict[str, float]:
    """Compute Volume 23 Ch 12 fair-share deficit and priority score."""
    balance_gpu_hours = team.monthly_quota_gpu_hours - team.current_usage_gpu_hours
    deficit_ratio = (
        team.current_usage_gpu_hours - team.monthly_quota_gpu_hours
    ) / team.monthly_quota_gpu_hours
    priority = -deficit_ratio + (0.1 if job_gpu_count < 4 else 0.0)
    return {
        "quota_gpu_hours": team.monthly_quota_gpu_hours,
        "used_gpu_hours": team.current_usage_gpu_hours,
        "balance_gpu_hours": round(balance_gpu_hours, 2),
        "deficit_ratio": round(deficit_ratio, 4),
        "priority_score": round(priority, 4),
    }


def evaluate_professor_a_vs_b_month(
    prof_a_quota: float = 500.0,
    prof_a_used: float = 600.0,
    prof_b_quota: float = 250.0,
    prof_b_used: float = 100.0,
) -> Dict[str, float]:
    """Evaluate the Month 1 -> Month 2 fair-share example from Volume 23 Ch 12."""
    total_quota = prof_a_quota + prof_b_quota
    total_used = prof_a_used + prof_b_used
    util_pct = (total_used / total_quota) * 100.0
    a_balance = prof_a_quota - prof_a_used  # -100
    b_balance = prof_b_quota - prof_b_used  # +150
    return {
        "total_quota_gpu_hours": total_quota,
        "total_used_gpu_hours": total_used,
        "cluster_utilization_pct": round(util_pct, 2),
        "cluster_utilization_pct_rounded": float(round(util_pct)),
        "prof_a_balance_gpu_hours": a_balance,
        "prof_b_balance_gpu_hours": b_balance,
    }


def compare_default_vs_kai_scheduler(
    job_pods: int = 4,
    gpus_per_pod: float = 1.0,
    free_gpus_on_nvswitch_node: int = 4,
    free_gpus_scattered_ethernet: int = 4,
    requires_gang: bool = True,
    requires_nvlink_locality: bool = True,
    requires_fractional_gpu: bool = False,
) -> Dict[str, object]:
    """Compare default `kube-scheduler` against `kai-scheduler` (`GAK` Ch 7 Example 7-5)."""
    default_supports_fractional = False
    default_supports_native_gang = False
    default_supports_nvswitch_auto = False

    kai_supports_fractional = True
    kai_supports_native_gang = True
    kai_supports_nvswitch_auto = True

    default_ok = (
        (not requires_fractional_gpu or default_supports_fractional)
        and (not requires_gang or default_supports_native_gang)
        and (not requires_nvlink_locality or default_supports_nvswitch_auto)
    )
    kai_ok = (
        (not requires_fractional_gpu or kai_supports_fractional)
        and (not requires_gang or kai_supports_native_gang)
        and (not requires_nvlink_locality or kai_supports_nvswitch_auto)
    )
    return {
        "default_scheduler_satisfies_all": default_ok,
        "kai_scheduler_satisfies_all": kai_ok,
        "kai_selected_placement": (
            "single_8gpu_nvswitch_node"
            if free_gpus_on_nvswitch_node >= job_pods * gpus_per_pod
            else "multi_node_infiniband"
        ),
    }


def simulate_graceful_preemption_timeline(
    checkpoint_write_seconds: int = 8,
    grace_period_seconds: int = 30,
    new_job_start_sec: int = 45,
    preempted_job_resume_sec: int = 90,
) -> Dict[str, object]:
    """Simulate Volume 23 Ch 7 & Ch 12 graceful SIGTERM checkpoint preemption."""
    saved_before_sigkill = checkpoint_write_seconds <= grace_period_seconds
    return {
        "sigterm_sent_at_sec": 0,
        "checkpoint_completed_at_sec": checkpoint_write_seconds,
        "sigkill_deadline_sec": grace_period_seconds,
        "saved_before_sigkill": saved_before_sigkill,
        "new_job_running_at_sec": new_job_start_sec,
        "old_job_resumed_at_sec": preempted_job_resume_sec,
        "computation_lost_steps": 0 if saved_before_sigkill else -1,
    }
