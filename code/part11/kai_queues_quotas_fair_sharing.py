"""Chapter 11.15 — KAI queues, quotas and fair sharing.

Deterministic models for:
1. Hierarchical Fair Queuing (`HFQ`) and KAI `Queue` (`quota`, `overQuotaWeight`,
   `limit`) proportional over-quota distribution across a `Department -> Project`
   tree.
2. Volume 24 Project 12 `5`-group (`A..E`) `32`-GPU cluster model:
   - Shares: A=`40%` (`12.8` GPUs, `307.2` GPUh), B=`25%` (`8.0` GPUs, `192.0` GPUh),
     C=`20%` (`6.4` GPUs, `153.6` GPUh), D=`10%` (`3.2` GPUs, `76.8` GPUh),
     E=`5%` (`1.6` GPUs, `38.4` GPUh; total `768.0` GPUh).
   - 2-week capacity: `32 * 14 * 24 = 10,752` GPU-hours (`768 / 10,752 = 7.14%`
     / `7.1%`) and why Level 3 Backfill (`~8,900` GPU-hours) is required to hit
     `> 90%` utilization.
   - Weekly cost accounting (`$0.20`/GPUh normal vs `$0.40`/GPUh priority:
     Group A `2 * 8 * 48 * $0.20 = $153.60/week`, Group E `50 * (10/60) * $0.20 = $1.67/week`).
3. Volume 11 Chapter 9 Capacity Planning Formula:
   `N = ceil((D + F) / (A * (1 - H)))` and allocation-contract chargeback.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class KaiQueueSpec:
    """KAI Scheduler `Queue` (`scheduling.run.ai/v2`) specification."""

    name: str
    parent_department: str
    nominal_quota: float
    over_quota_weight: float
    limit: float  # -1.0 means unlimited borrowing up to cluster capacity
    demanded_gpus: float


def compute_kai_fair_shares(
    total_cluster_gpus: float, queues: List[KaiQueueSpec]
) -> Dict[str, Dict[str, float]]:
    """Compute guaranteed + weighted over-quota fair shares across KAI Queues."""
    allocations: Dict[str, float] = {}
    spare_pool = total_cluster_gpus

    # Step 1: Grant up to nominal_quota for each queue based on demand
    bursting_queues: List[KaiQueueSpec] = []
    for q in queues:
        base_grant = min(q.demanded_gpus, q.nominal_quota)
        allocations[q.name] = base_grant
        spare_pool -= base_grant
        if q.demanded_gpus > q.nominal_quota:
            bursting_queues.append(q)

    # Step 2: Distribute spare_pool proportionally to over_quota_weight among bursting queues
    total_weight = sum(q.over_quota_weight for q in bursting_queues)
    if spare_pool > 0 and total_weight > 0:
        for q in bursting_queues:
            weighted_bonus = spare_pool * (q.over_quota_weight / total_weight)
            desired_total = allocations[q.name] + weighted_bonus
            if q.limit >= 0:
                desired_total = min(desired_total, q.limit)
            desired_total = min(desired_total, q.demanded_gpus)
            allocations[q.name] = round(desired_total, 2)

    results: Dict[str, Dict[str, float]] = {}
    for q in queues:
        total_got = allocations[q.name]
        borrowed = max(0.0, round(total_got - q.nominal_quota, 2))
        results[q.name] = {
            "nominal_quota": q.nominal_quota,
            "allocated_gpus": total_got,
            "borrowed_gpus": borrowed,
        }
    return results


def evaluate_five_group_research_cluster(
    cluster_gpus: int = 32,
    window_days: int = 14,
    normal_rate_usd: float = 0.20,
    priority_rate_usd: float = 0.40,
) -> Dict[str, object]:
    """Evaluate Volume 24 Project 12 5-group (A..E) 32-GPU fair-share and cost model."""
    shares_pct = {"A": 40.0, "B": 25.0, "C": 20.0, "D": 10.0, "E": 5.0}
    gpu_shares = {
        g: round(cluster_gpus * (pct / 100.0), 2) for g, pct in shares_pct.items()
    }
    slurm_maxgpus_rounded = {
        "A": 13,
        "B": 8,
        "C": 6,
        "D": 3,
        "E": 2,
    }
    fair_eval_gpuh = {
        "A": 307.2,
        "B": 192.0,
        "C": 153.6,
        "D": 76.8,
        "E": 38.4,
    }
    total_eval_gpuh = round(sum(fair_eval_gpuh.values()), 2)  # 768.0
    total_cluster_gpuh_2wk = cluster_gpus * window_days * 24  # 10752
    eval_util_pct = round((total_eval_gpuh / total_cluster_gpuh_2wk) * 100.0, 1)

    # Weekly cost examples from Volume 24 Project 12
    # Group A: 2 jobs/wk * 8 GPUs * 48h * $0.20 = $153.60/wk
    group_a_weekly_usd = round(2 * 8 * 48 * normal_rate_usd, 2)
    # Group E: 50 jobs/wk * 1 GPU * (10/60)h * $0.20 = $1.67/wk
    group_e_weekly_usd = round(50 * 1 * (10.0 / 60.0) * normal_rate_usd, 2)

    return {
        "gpu_shares": gpu_shares,
        "slurm_maxgpus": slurm_maxgpus_rounded,
        "total_eval_gpuh": total_eval_gpuh,
        "total_cluster_gpuh_2wk": total_cluster_gpuh_2wk,
        "eval_util_pct": eval_util_pct,
        "group_a_weekly_cost_usd": group_a_weekly_usd,
        "group_e_weekly_cost_usd": group_e_weekly_usd,
        "priority_rate_multiplier": round(priority_rate_usd / normal_rate_usd, 1),
    }


def compute_required_nodes_for_service_class(
    demand_allocations_d: float,
    fragmentation_loss_f: float,
    usable_allocations_per_node_a: float,
    headroom_fraction_h: float,
) -> Dict[str, float]:
    """Compute Volume 11 Chapter 9 capacity formula: N = ceil((D + F) / (A * (1 - H)))."""
    if not (0.0 <= headroom_fraction_h < 1.0):
        raise ValueError("headroom_fraction_h must be in [0.0, 1.0)")
    effective_per_node = usable_allocations_per_node_a * (1.0 - headroom_fraction_h)
    raw_nodes = (demand_allocations_d + fragmentation_loss_f) / effective_per_node
    required_nodes_n = math.ceil(raw_nodes)
    return {
        "effective_allocations_per_node": round(effective_per_node, 2),
        "raw_nodes": round(raw_nodes, 2),
        "required_nodes_n": float(required_nodes_n),
    }
