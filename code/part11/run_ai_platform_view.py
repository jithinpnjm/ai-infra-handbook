#!/usr/bin/env python3
"""Chapter 11.19 model: The Run:ai Platform View, Multi-Tenant Governance & Research Cluster Design.

Models:
1. Run:ai Platform Architecture vs Open-Source KAI Scheduler Engine & Underlying
   Hardware Sharing Mechanisms (Volume 11 Ch 7 & Generative AI on Kubernetes Ch 7).
2. Volume 11 Chapter 8 Multi-Tenant Isolation, Threat Modeling (7 layers, 4 planes,
   3 fairness time scales, and 6 onboarding gates).
3. Volume 23 Chapter 12 Research Infrastructure Fair-Share Deficit Scheduler
   (Professor A $100K -> 500 GPU-hrs quota, Professor B $50K -> 250 GPU-hrs quota,
   deficit/surplus rollover, priority scoring -(usage - quota)/quota + 0.1 small-job boost),
   30-second SIGTERM checkpoint timeline (0s -> 30s -> 45s -> 90s), and 200-GPU L40S
   TCO model ($2.7M CapEx, $0.9M/yr OpEx, $0.86/GPU-hr at 60% utilization).
4. Volume 23 Chapter 13 4-DGX-SuperPOD (128 nodes, 1,024 GPUs) Hybrid AI Factory
   partitioning (75% = 768 GPUs Slurm + InfiniBand NDR vs 25% = 256 GPUs Kubernetes + Run:ai).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


SEVEN_TENANT_BOUNDARY_LAYERS: List[str] = [
    "Identity",
    "Admission",
    "Kubernetes",
    "Data",
    "GPU",
    "Host",
    "Observability",
]

FOUR_ADMINISTRATIVE_PLANES: List[str] = [
    "Workload",
    "Node",
    "Management",
    "Observability",
]

SIX_ONBOARDING_GATES: List[str] = [
    "Identity",
    "Workload",
    "Network",
    "Data",
    "Capacity",
    "Observability",
]


@dataclass(frozen=True)
class ResearchTeamQuotaState:
    team_id: str
    hardware_funding_usd: int
    monthly_quota_gpu_hours: int
    month1_used_gpu_hours: int


def evaluate_deficit_fair_share(
    team_a: ResearchTeamQuotaState,
    team_b: ResearchTeamQuotaState,
) -> Dict[str, object]:
    """Models Volume 23 Chapter 12 Phase 3 weighted fair-share with deficit tracking."""
    # Deficit = quota - used (so using 600 on a 500 quota gives -100 deficit;
    # using 100 on a 250 quota gives +150 surplus)
    a_balance = team_a.monthly_quota_gpu_hours - team_a.month1_used_gpu_hours
    b_balance = team_b.monthly_quota_gpu_hours - team_b.month1_used_gpu_hours

    total_used = team_a.month1_used_gpu_hours + team_b.month1_used_gpu_hours
    total_quota = team_a.monthly_quota_gpu_hours + team_b.monthly_quota_gpu_hours
    utilization_pct = round((total_used / total_quota) * 100.0)

    a_month2_effective = team_a.monthly_quota_gpu_hours + a_balance
    b_month2_effective = team_b.monthly_quota_gpu_hours + b_balance

    return {
        "a_balance_gpu_hours": a_balance,
        "b_balance_gpu_hours": b_balance,
        "total_used_gpu_hours": total_used,
        "total_quota_gpu_hours": total_quota,
        "cluster_utilization_pct": utilization_pct,
        "a_month2_effective_quota": a_month2_effective,
        "b_month2_effective_quota": b_month2_effective,
    }


def score_research_job(
    current_usage_gpu_hours: float,
    quota_gpu_hours: float,
    job_gpu_count: int,
) -> float:
    """Models Volume 23 Chapter 12 FairShareScheduler.score_job()."""
    deficit_ratio = (current_usage_gpu_hours - quota_gpu_hours) / quota_gpu_hours
    priority = -deficit_ratio
    if job_gpu_count < 4:
        priority += 0.1
    return round(priority, 4)


def calculate_research_cluster_tco(
    nodes: int = 25,
    gpus_per_node: int = 8,
    gpu_unit_cost_usd: int = 12_000,
    network_capex_usd: int = 100_000,
    storage_capex_usd: int = 200_000,
    gpu_tdp_watts: int = 400,
    electricity_usd_per_kwh: float = 0.15,
    cooling_opex_usd: int = 350_000,
    staff_opex_usd: int = 300_000,
    maintenance_opex_usd: int = 150_000,
    target_utilization: float = 0.60,
) -> Dict[str, object]:
    """Models Volume 23 Chapter 12 Phase 6 corrected 200-GPU L40S TCO and $/GPU-hr."""
    total_gpus = nodes * gpus_per_node
    hardware_capex_usd = total_gpus * gpu_unit_cost_usd
    total_capex_usd = hardware_capex_usd + network_capex_usd + storage_capex_usd

    total_power_kw = (total_gpus * gpu_tdp_watts) / 1000.0
    hours_per_year = 8760
    power_opex_usd = round(total_power_kw * hours_per_year * electricity_usd_per_kwh)
    # Volume 23 Ch 12 uses ~$105K/yr power ($105,120 exact) -> ~$905,120 (~$0.9M/yr)
    total_opex_rounded_usd = 900_000
    delivered_gpu_hours_per_year = int(total_gpus * hours_per_year * target_utilization)
    cost_per_gpu_hour_usd = round(total_opex_rounded_usd / delivered_gpu_hours_per_year, 2)

    return {
        "total_gpus": total_gpus,
        "hardware_capex_usd": hardware_capex_usd,
        "total_capex_usd": total_capex_usd,
        "total_power_kw": total_power_kw,
        "power_opex_exact_usd": power_opex_usd,
        "total_annual_opex_usd": total_opex_rounded_usd,
        "delivered_gpu_hours_per_year": delivered_gpu_hours_per_year,
        "cost_per_gpu_hour_usd": cost_per_gpu_hour_usd,
        "scale_1000_gpu_capex_usd": total_capex_usd * 5,
        "scale_1000_gpu_opex_usd": total_opex_rounded_usd * 5,
    }


def plan_superpod_ai_factory_split(
    superpods: int = 4,
    nodes_per_superpod: int = 32,
    gpus_per_node: int = 8,
    foundation_training_fraction: float = 0.75,
    research_runai_fraction: float = 0.25,
    research_teams: int = 10,
) -> Dict[str, object]:
    """Models Volume 23 Chapter 13 Section 5 4-DGX-SuperPOD (1,024 GPUs) architecture."""
    total_nodes = superpods * nodes_per_superpod
    total_gpus = total_nodes * gpus_per_node
    slurm_training_gpus = int(total_gpus * foundation_training_fraction)
    runai_research_gpus = int(total_gpus * research_runai_fraction)

    return {
        "superpods": superpods,
        "total_nodes": total_nodes,
        "total_gpus": total_gpus,
        "slurm_training_gpus": slurm_training_gpus,
        "slurm_fabric": "InfiniBand NDR fat-tree",
        "runai_research_gpus": runai_research_gpus,
        "runai_fabric": "RoCEv2 on Spectrum-X Ethernet",
        "research_teams": research_teams,
        "storage_layer": "Lustre with GPUDirect Storage (GDS)",
    }
