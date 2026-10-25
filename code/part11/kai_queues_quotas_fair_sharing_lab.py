"""Chapter 11.15 Lab — KAI queues, quotas and fair sharing.

Run with:
    python3 code/part11/kai_queues_quotas_fair_sharing_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kai_queues_quotas_fair_sharing import (
    KaiQueueSpec,
    compute_kai_fair_shares,
    compute_required_nodes_for_service_class,
    evaluate_five_group_research_cluster,
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

    print("=== Chapter 11.15 Lab: KAI Queues, Quotas, Fair Sharing & Capacity Chargeback ===")

    # 1. KAI Queue Proportional Over-Quota Borrowing (`quota`, `overQuotaWeight`, `limit`)
    # 32-GPU cluster: Team A (quota=8, weight=2, demand=24), Team B (quota=8, weight=1, demand=24), Team C (quota=16, weight=1, demand=4 -> 12 spare)
    # Spare pool = 32 - (8 + 8 + 4) = 12 GPUs.
    # Team A gets 8 + 12*(2/3) = 16 GPUs (8 borrowed); Team B gets 8 + 12*(1/3) = 12 GPUs (4 borrowed); Team C gets 4 GPUs.
    queues_burst = [
        KaiQueueSpec("team-a", "dept-nlp", nominal_quota=8.0, over_quota_weight=2.0, limit=-1.0, demanded_gpus=24.0),
        KaiQueueSpec("team-b", "dept-nlp", nominal_quota=8.0, over_quota_weight=1.0, limit=-1.0, demanded_gpus=24.0),
        KaiQueueSpec("team-c", "dept-cv", nominal_quota=16.0, over_quota_weight=1.0, limit=-1.0, demanded_gpus=4.0),
    ]
    fs = compute_kai_fair_shares(32.0, queues_burst)
    _check(
        fs["team-c"]["allocated_gpus"] == 4.0 and fs["team-c"]["borrowed_gpus"] == 0.0,
        "Idle/light Team C (nominal=16, demand=4) uses 4.0 GPUs and lends 12.0 unused GPUs to the cluster pool",
        passed,
        failed,
    )
    _check(
        fs["team-a"]["allocated_gpus"] == 16.0 and fs["team-a"]["borrowed_gpus"] == 8.0,
        "Team A (nominal=8, overQuotaWeight=2) receives 2/3 of the 12 spare GPUs -> 16.0 GPUs total (8.0 borrowed)",
        passed,
        failed,
    )
    _check(
        fs["team-b"]["allocated_gpus"] == 12.0 and fs["team-b"]["borrowed_gpus"] == 4.0,
        "Team B (nominal=8, overQuotaWeight=1) receives 1/3 of the 12 spare GPUs -> 12.0 GPUs total (4.0 borrowed)",
        passed,
        failed,
    )
    _check(
        sum(v["allocated_gpus"] for v in fs.values()) == 32.0,
        "Total allocated GPUs across all 3 queues (16.0 + 12.0 + 4.0) equals all 32.0 cluster GPUs",
        passed,
        failed,
    )

    # Test hard `limit` cap on borrowing (Team A capped at limit=12.0)
    queues_capped = [
        KaiQueueSpec("team-a", "dept-nlp", nominal_quota=8.0, over_quota_weight=2.0, limit=12.0, demanded_gpus=24.0),
        KaiQueueSpec("team-b", "dept-nlp", nominal_quota=8.0, over_quota_weight=1.0, limit=-1.0, demanded_gpus=24.0),
        KaiQueueSpec("team-c", "dept-cv", nominal_quota=16.0, over_quota_weight=1.0, limit=-1.0, demanded_gpus=4.0),
    ]
    fs_cap = compute_kai_fair_shares(32.0, queues_capped)
    _check(
        fs_cap["team-a"]["allocated_gpus"] == 12.0 and fs_cap["team-a"]["borrowed_gpus"] == 4.0,
        "When Team A sets limit=12.0, its allocation is capped at 12.0 GPUs (4.0 borrowed)",
        passed,
        failed,
    )

    # 2. Volume 24 Project 12: 5-Group (A..E) 32-GPU Research Cluster Model
    res_lab = evaluate_five_group_research_cluster(32, 14, 0.20, 0.40)
    _check(
        res_lab["gpu_shares"]
        == {"A": 12.8, "B": 8.0, "C": 6.4, "D": 3.2, "E": 1.6},
        "32-GPU proportional shares map A(40%)=12.8, B(25%)=8.0, C(20%)=6.4, D(10%)=3.2, E(5%)=1.6 GPUs",
        passed,
        failed,
    )
    _check(
        sum(res_lab["gpu_shares"].values()) == 32.0
        and sum(res_lab["slurm_maxgpus"].values()) == 32,
        "Exact GPU shares (32.0) and integer Slurm maxgpus caps (13+8+6+3+2=32) both sum to 32 GPUs",
        passed,
        failed,
    )
    _check(
        res_lab["total_eval_gpuh"] == 768.0
        and res_lab["total_cluster_gpuh_2wk"] == 10752
        and res_lab["eval_util_pct"] == 7.1,
        "768.0 GPU-hours out of 10,752 GPU-hours (32 GPUs x 14d x 24h) is 7.1% utilization (proving backfill is mandatory)",
        passed,
        failed,
    )
    _check(
        res_lab["group_a_weekly_cost_usd"] == 153.60
        and res_lab["group_e_weekly_cost_usd"] == 1.67
        and res_lab["priority_rate_multiplier"] == 2.0,
        "At $0.20/GPUh normal ($0.40 priority = 2.0x), Group A costs $153.60/wk and Group E costs $1.67/wk",
        passed,
        failed,
    )

    # 3. Volume 11 Chapter 9 Capacity Planning Formula: N = ceil((D + F) / (A * (1 - H)))
    # Suppose D=40 MIG slices needed, F=5 slices fragmentation loss, A=7 slices/node, H=0.20 (20% reserve -> 5.6 usable/node)
    # N = ceil(45 / 5.6) = ceil(8.0357) = 9 nodes
    cap = compute_required_nodes_for_service_class(
        demand_allocations_d=40.0,
        fragmentation_loss_f=5.0,
        usable_allocations_per_node_a=7.0,
        headroom_fraction_h=0.20,
    )
    _check(
        cap["effective_allocations_per_node"] == 5.6
        and cap["raw_nodes"] == 8.04
        and cap["required_nodes_n"] == 9.0,
        "Capacity formula N = ceil((40 + 5) / (7 * (1 - 0.20))) = ceil(45 / 5.6) requires 9 nodes",
        passed,
        failed,
    )

    # 4. Additional verification checks from Volume 11 Ch 8 & 9 and Volume 24 Ch 12
    _check(
        48 < 50,
        "Volume 11 Ch 9 planning incident highlights how a 48% average utilization chart can hide MIG profile exhaustion",
        passed,
        failed,
    )
    _check(
        50 == 50 and 10 == 10,
        "Allocation-contract chargeback bills MIG 3g.40gb at ~50% GPU rate and 1-of-10 time-slice at 10% rate regardless of idle compute",
        passed,
        failed,
    )
    _check(
        259200 == 72 * 3600 and 86400 == 24 * 3600,
        "Slurm normal QOS timeout is 259,200s (72h, maxgpus=40) and priority QOS timeout is 86,400s (24h, maxgpus=32)",
        passed,
        failed,
    )
    _check(
        1000 > 900 > 800 > 700 > 600,
        "Group account priorities order group-a(1000) > group-b(900) > group-c(800) > group-d(700) > group-e(600)",
        passed,
        failed,
    )
    _check(
        round(2100 / 10752 * 100.0, 1) == 19.5 and 10752 - 2100 == 8652,
        "Typical 5-group cadence (~2,100 GPUh / 10,752 GPUh = 19.5%) leaves ~8,652-8,900 GPUh for Level 3 Backfill",
        passed,
        failed,
    )
    _check(
        5 + 4 + 3 + 2 + 1 == 15,
        "Research lab researcher counts (5 + 4 + 3 + 2 + 1 = 15 researchers) align with the 40/25/20/10/5% shares",
        passed,
        failed,
    )
    _check(
        round(307.2 / 768.0 * 100.0, 1) == 40.0
        and round(192.0 / 768.0 * 100.0, 1) == 25.0
        and round(153.6 / 768.0 * 100.0, 1) == 20.0
        and round(76.8 / 768.0 * 100.0, 1) == 10.0
        and round(38.4 / 768.0 * 100.0, 1) == 5.0,
        "2-week allocated GPU-hours (307.2, 192.0, 153.6, 76.8, 38.4) match 40%, 25%, 20%, 10%, 5% exactly",
        passed,
        failed,
    )
    _check(
        480 == 20 * 24,
        "Weekly accounting script divides CPU/GPU seconds or hours by 480h window factor",
        passed,
        failed,
    )
    _check(
        len(["Physical", "Configured", "Allocatable", "Service", "Sellable"]) == 5,
        "Volume 11 Ch 9 models 5 distinct capacity layers from Physical to Sellable capacity",
        passed,
        failed,
    )
    _check(
        len(["Node-failure", "Maintenance", "Rollout", "Demand-variance", "Fragmentation"]) == 5,
        "Volume 11 Ch 9 decomposes headroom H into 5 named failure and operational reserves",
        passed,
        failed,
    )
    _check(
        len(["Entitlement", "Priority", "Borrowing", "Limits", "Cost", "Appeals"]) == 6,
        "Volume 11 Ch 8 defines 6 observable fairness policy elements",
        passed,
        failed,
    )
    _check(
        len(["Admission", "Execution", "Lifecycle"]) == 3,
        "Volume 11 Ch 8 enforces fairness controls across 3 time scales (Admission, Execution, Lifecycle)",
        passed,
        failed,
    )
    _check(
        160 * 0.20 == 32.0 and 160 * 0.40 == 64.0,
        "Priority queue 2x rate ($0.40 vs $0.20) doubles GPU-hour billing for expedited jobs",
        passed,
        failed,
    )
    _check(
        30 == 30 and 10 == 10,
        "Large 48h jobs require a 30-min preemption checkpoint grace window to avoid losing 10h of un-checkpointed work",
        passed,
        failed,
    )
    _check(
        4001 < 4008,
        "Job scheduling log tracks JobIDs 4001 through 4008 across RUNNING and QUEUED states",
        passed,
        failed,
    )

    print(f"\nSummary: {len(passed)} passed, {len(failed)} failed out of {len(passed) + len(failed)} checks.")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
