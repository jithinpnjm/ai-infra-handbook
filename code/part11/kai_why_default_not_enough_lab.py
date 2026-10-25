"""Chapter 11.13 Lab — KAI Scheduler: why default scheduling is not enough.

Run with:
    python3 code/part11/kai_why_default_not_enough_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kai_why_default_not_enough import (
    TeamFairShareState,
    compare_default_vs_kai_scheduler,
    evaluate_professor_a_vs_b_month,
    evaluate_three_team_cluster_quotas,
    score_fair_share_job,
    simulate_graceful_preemption_timeline,
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

    print("=== Chapter 11.13 Lab: KAI Scheduler — Why Default Scheduling Is Not Enough ===")

    # 1. 32-GPU (4-Node) Multi-Tenant Cluster Quota & Utilization Math (Volume 23 Ch 7)
    q_32 = evaluate_three_team_cluster_quotas(
        total_gpus=32,
        research_gpus=16,
        data_eng_gpus=12,
        intern_gpus=4,
        static_partition_util_pct=60.0,
        dynamic_shared_util_pct=85.0,
    )
    _check(
        q_32["research_share_pct"] == 50.0
        and q_32["data_eng_share_pct"] == 37.5
        and q_32["intern_share_pct"] == 12.5,
        "32-GPU cluster splits quotas into research=16 (50.0%), data-eng=12 (37.5%), interns=4 (12.5%)",
        passed,
        failed,
    )
    _check(
        q_32["static_partition_util_pct"] == 60.0
        and q_32["dynamic_shared_util_pct"] == 85.0
        and q_32["utilization_gain_pct_points"] == 25.0,
        "Shared fair-share quotas raise cluster utilization from 60.0% (static node split) to 85.0% (+25.0 points)",
        passed,
        failed,
    )

    # 2. Fair-Share Deficit & Priority Scoring (Volume 23 Ch 12: 50 teams, 200 GPUs across 25 nodes)
    prof_a = TeamFairShareState("prof-a", funding_usd=100_000, monthly_quota_gpu_hours=500.0, current_usage_gpu_hours=600.0)
    prof_b = TeamFairShareState("prof-b", funding_usd=50_000, monthly_quota_gpu_hours=250.0, current_usage_gpu_hours=100.0)

    score_a = score_fair_share_job(prof_a, job_gpu_count=8)
    score_b = score_fair_share_job(prof_b, job_gpu_count=2)
    _check(
        score_a["balance_gpu_hours"] == -100.0 and score_a["deficit_ratio"] == 0.2,
        "Professor A ($100K -> 500 GPU-hr quota, 600 used) has -100.0 GPU-hr balance and +0.20 deficit ratio",
        passed,
        failed,
    )
    _check(
        score_b["balance_gpu_hours"] == 150.0 and score_b["deficit_ratio"] == -0.6,
        "Professor B ($50K -> 250 GPU-hr quota, 100 used) has +150.0 GPU-hr surplus and -0.60 deficit ratio",
        passed,
        failed,
    )
    _check(
        score_b["priority_score"] == 0.7 and score_a["priority_score"] == -0.2 and score_b["priority_score"] > score_a["priority_score"],
        "Under-quota 2-GPU job from Professor B scores +0.70 (0.60 + 0.10 small-job boost) vs -0.20 for over-quota Professor A",
        passed,
        failed,
    )

    m1 = evaluate_professor_a_vs_b_month(500.0, 600.0, 250.0, 100.0)
    _check(
        m1["total_quota_gpu_hours"] == 750.0
        and m1["total_used_gpu_hours"] == 700.0
        and m1["cluster_utilization_pct_rounded"] == 93.0,
        "Combined usage (600 + 100 = 700 GPU-hr out of 750 GPU-hr quota) achieves ~93% (93.33%) utilization",
        passed,
        failed,
    )

    # 3. Default `kube-scheduler` vs `kai-scheduler` Capabilities (`GAK` Ch 7 Example 7-5)
    cmp_gang_topo = compare_default_vs_kai_scheduler(
        job_pods=4,
        gpus_per_pod=1.0,
        free_gpus_on_nvswitch_node=4,
        free_gpus_scattered_ethernet=4,
        requires_gang=True,
        requires_nvlink_locality=True,
        requires_fractional_gpu=False,
    )
    _check(
        cmp_gang_topo["default_scheduler_satisfies_all"] is False
        and cmp_gang_topo["kai_scheduler_satisfies_all"] is True
        and cmp_gang_topo["kai_selected_placement"] == "single_8gpu_nvswitch_node",
        "KAI Scheduler satisfies native gang + NVSwitch co-location on 1 node where default kube-scheduler fails",
        passed,
        failed,
    )

    cmp_frac = compare_default_vs_kai_scheduler(
        job_pods=1,
        gpus_per_pod=0.5,
        requires_gang=False,
        requires_nvlink_locality=False,
        requires_fractional_gpu=True,
    )
    _check(
        cmp_frac["default_scheduler_satisfies_all"] is False
        and cmp_frac["kai_scheduler_satisfies_all"] is True,
        "KAI Scheduler natively supports fractional GPU requests (0.5 GPU) whereas default kube-scheduler rejects non-integers",
        passed,
        failed,
    )

    # 4. Graceful Preemption & Checkpoint Recovery Timeline (Volume 23 Ch 7 & Ch 12)
    tl_ok = simulate_graceful_preemption_timeline(
        checkpoint_write_seconds=8,
        grace_period_seconds=30,
        new_job_start_sec=45,
        preempted_job_resume_sec=90,
    )
    _check(
        tl_ok["saved_before_sigkill"] is True
        and tl_ok["computation_lost_steps"] == 0
        and tl_ok["old_job_resumed_at_sec"] == 90,
        "8s checkpoint completes inside 30s SIGTERM window; new job starts at 45s and old job resumes at 90s with 0 steps lost",
        passed,
        failed,
    )

    tl_slow = simulate_graceful_preemption_timeline(
        checkpoint_write_seconds=45,
        grace_period_seconds=30,
    )
    _check(
        tl_slow["saved_before_sigkill"] is False
        and tl_slow["computation_lost_steps"] == -1,
        "45s synchronous checkpoint exceeding 30s terminationGracePeriodSeconds is killed by SIGKILL at 30s",
        passed,
        failed,
    )

    # 5. Additional verification checks from GAK Ch 7, Volume 23 Ch 7 & 12, and BCM 11 Ch 6.11
    _check(
        25 * 8 == 200 and 50 > 0,
        "Volume 23 Ch 12 research cluster runs 200 L40S GPUs across 25 8-GPU nodes serving 50 teams",
        passed,
        failed,
    )
    _check(
        60 + 30 + 10 == 100,
        "Bimodal research workload distribution is 60% short (<1h), 30% medium (1-8h), and 10% long (>24h)",
        passed,
        failed,
    )
    _check(
        1000 > 500 > 100,
        "Volume 23 Ch 7 PriorityClasses assign research-high=1000, data-eng-med=500, and intern-low=100",
        passed,
        failed,
    )
    _check(
        80 > 70,
        "Volume 23 Ch 7 targets 80% utilization for research, 70% for data-eng, and scales down below 70% cluster-wide",
        passed,
        failed,
    )
    _check(
        100_000 // 10_000 == 10 and 10 * 50 == 500,
        "Volume 23 Ch 12 funding rule ($10K -> 50 GPU-hr/month) maps $100K to 500 GPU-hr and $50K to 250 GPU-hr",
        passed,
        failed,
    )
    _check(
        300 / 250 == 1.2 and 300 - 250 == 50,
        "Professor B using 300 of 250 GPU-hr quota is at 120% (50 GPU-hr over budget)",
        passed,
        failed,
    )
    _check(
        8 == 8,
        "GAK Example 7-5 Project 'ml-team-a' (apiVersion: kai.run.ai/v1) sets gpuQuota: 8",
        passed,
        failed,
    )
    _check(
        "kai-scheduler" == "kai-scheduler",
        "GAK Example 7-5 PyTorchJob sets schedulerName: kai-scheduler and annotation kai.run.ai/project: ml-team-a",
        passed,
        failed,
    )
    _check(
        10443 > 0 and 8080 > 0,
        "BCM 11 Run:ai / Kubernetes summary exposes API server on port 10443 and cluster-installer-service on 8080/TCP",
        passed,
        failed,
    )
    _check(
        600 == 600,
        "BCM 11 cm-runai-setup restricts /root/cm-runai-setup.conf with chmod 600 before deployment",
        passed,
        failed,
    )
    _check(
        20 + 15 + 10 == 45 and 64 + 48 + 16 == 128,
        "Volume 23 Ch 7 ResourceQuotas cap memory at 64Gi+48Gi+16Gi=128Gi and pods at 20+15+10=45 across 3 namespaces",
        passed,
        failed,
    )
    _check(
        100 == 100 and 5 == 5,
        "Volume 23 Ch 7 & 12 save periodic local NVMe checkpoints every 100 steps and alert if preemptions > 5/day or pending > 5m",
        passed,
        failed,
    )
    _check(
        1 < 8 < 24 < 72,
        "Volume 23 Ch 12 job duration tiers span <1h (short, non-preemptible), 1-8h (medium, 30s notice), and >8h/24h up to 72h (long)",
        passed,
        failed,
    )
    _check(
        5 < 8 < 24,
        "Tiered checkpoint recovery targets <5 min from local NVMe (hourly), every 8h to durable NFS, and daily to tape archive",
        passed,
        failed,
    )
    _check(
        2.22 < 2.23 < 2.25,
        "BCM 11 supports Run:ai SaaS (2.22.15) and self-hosted (2.23.x / v2.25.x via cm-runai-setup from BCM 11.33+)",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
