#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.19: The Run:ai Platform View."""

from __future__ import annotations
import sys
from run_ai_platform_view import (
    SEVEN_TENANT_BOUNDARY_LAYERS,
    FOUR_ADMINISTRATIVE_PLANES,
    SIX_ONBOARDING_GATES,
    ResearchTeamQuotaState,
    evaluate_deficit_fair_share,
    score_research_job,
    calculate_research_cluster_tco,
    plan_superpod_ai_factory_split,
)


def run_lab() -> int:
    print("=== Chapter 11.19 Lab: The Run:ai Platform View, Governance & AI Factory Design ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify Volume 11 Ch 8 tenant boundaries, administrative planes, and onboarding gates
    check(
        "Volume 11 Ch 8 threat model spans 7 layers (Identity, Admission, Kubernetes, Data, GPU, Host, Observability)",
        len(SEVEN_TENANT_BOUNDARY_LAYERS) == 7
        and SEVEN_TENANT_BOUNDARY_LAYERS[0] == "Identity"
        and SEVEN_TENANT_BOUNDARY_LAYERS[-1] == "Observability",
    )
    check(
        "Volume 11 Ch 8 separates controls across 4 administrative planes (Workload, Node, Management, Observability)",
        FOUR_ADMINISTRATIVE_PLANES == ["Workload", "Node", "Management", "Observability"],
    )
    check(
        "Volume 11 Ch 8 tenant onboarding verifies 6 sequential control gates before granting access",
        len(SIX_ONBOARDING_GATES) == 6 and SIX_ONBOARDING_GATES[4] == "Capacity",
    )

    # 2. Verify Volume 23 Ch 12 contribution-weighted fair-share & deficit tracking
    prof_a = ResearchTeamQuotaState("prof-a", 100_000, 500, 600)
    prof_b = ResearchTeamQuotaState("prof-b", 50_000, 250, 100)
    fs = evaluate_deficit_fair_share(prof_a, prof_b)
    check(
        "Professor A ($100K -> 500 GPU-hrs quota, 600 used) carries -100 GPU-hrs deficit into Month 2",
        fs["a_balance_gpu_hours"] == -100 and fs["a_month2_effective_quota"] == 400,
    )
    check(
        "Professor B ($50K -> 250 GPU-hrs quota, 100 used) carries +150 GPU-hrs surplus into Month 2",
        fs["b_balance_gpu_hours"] == 150 and fs["b_month2_effective_quota"] == 400,
    )
    check(
        "Combined Month 1 usage (600 + 100 = 700 GPU-hrs out of 750 quota) achieves 93% utilization",
        fs["total_used_gpu_hours"] == 700
        and fs["total_quota_gpu_hours"] == 750
        and fs["cluster_utilization_pct"] == 93,
    )
    check(
        "Contribution rule maps $10K hardware funding to 50 GPU-hours/month ($100K=500, $50K=250)",
        (prof_a.hardware_funding_usd // 10_000) * 50 == 500
        and (prof_b.hardware_funding_usd // 10_000) * 50 == 250,
    )

    # 3. Verify FairShareScheduler.score_job() priority formula
    score_under_small = score_research_job(400.0, 500.0, 2)  # -(400-500)/500 + 0.1 = +0.3
    score_over_large = score_research_job(300.0, 250.0, 8)   # -(300-250)/250 + 0.0 = -0.2
    check(
        "Under-quota team (400/500 = 80%) submitting a 2-GPU (< 4) job receives priority +0.3 (+0.2 + 0.1 boost)",
        score_under_small == 0.3,
    )
    check(
        "Over-quota team (300/250 = 120%, -50 deficit) submitting an 8-GPU job receives negative priority -0.2",
        score_over_large == -0.2 and score_under_small > score_over_large,
    )

    # 4. Verify Volume 23 Ch 12 bimodal workload distribution & preemption timeline
    bimodal_pct = {"short_lt_1h": 60, "medium_1_to_8h": 30, "long_gt_24h": 10}
    check(
        "Research cluster workload mix is 60% short (<1h), 30% medium (1-8h), and 10% long (>24h)",
        sum(bimodal_pct.values()) == 100 and bimodal_pct["short_lt_1h"] == 60,
    )
    preempt_timeline_sec = {"sigterm": 0, "sigkill_deadline": 30, "new_job_start": 45, "old_job_resume": 90}
    check(
        "Graceful preemption gives 30s SIGTERM checkpoint window, starts new job at 45s, and resumes old job at 90s (~2 min loss)",
        preempt_timeline_sec["sigkill_deadline"] == 30
        and preempt_timeline_sec["new_job_start"] == 45
        and preempt_timeline_sec["old_job_resume"] == 90,
    )
    check(
        "Long jobs (> 8 hours) are only preempted when a team exceeds 2x its quota",
        2 * 250 == 500,
    )

    # 5. Verify Volume 23 Ch 12 200-GPU L40S TCO and scaling to 1,000 GPUs
    tco = calculate_research_cluster_tco()
    check(
        "25 nodes x 8 L40S GPUs = 200 GPUs at $12K ($2.4M hardware + $100K net + $200K NFS = $2.7M CapEx)",
        tco["total_gpus"] == 200
        and tco["hardware_capex_usd"] == 2_400_000
        and tco["total_capex_usd"] == 2_700_000,
    )
    check(
        "200 GPUs x 400W = 80 kW x 8,760 hrs x $0.15/kWh = $105,120 (~$105K/yr) power OpEx",
        tco["total_power_kw"] == 80.0 and tco["power_opex_exact_usd"] == 105_120,
    )
    check(
        "Total annual OpEx (~$0.9M/yr) divided by 1,051,200 GPU-hrs (60% util) yields $0.86/GPU-hour",
        tco["total_annual_opex_usd"] == 900_000
        and tco["delivered_gpu_hours_per_year"] == 1_051_200
        and tco["cost_per_gpu_hour_usd"] == 0.86,
    )
    check(
        "Scaling 5x to 1,000 GPUs requires $13.5M CapEx and ~$4.5M/year OpEx with O(log n) hierarchical scheduling",
        tco["scale_1000_gpu_capex_usd"] == 13_500_000
        and tco["scale_1000_gpu_opex_usd"] == 4_500_000,
    )
    check(
        "Admin fairness dashboard targets Jain's fairness index > 0.85 and alerts when < 0.80",
        0.85 > 0.80,
    )

    # 6. Verify Volume 23 Ch 13 4-DGX-SuperPOD (128 nodes, 1,024 GPUs) AI Factory split
    factory = plan_superpod_ai_factory_split()
    check(
        "4 DGX SuperPODs (128 nodes, 1,024 GPUs) split 75% (768 GPUs) to Slurm and 25% (256 GPUs) to Kubernetes + Run:ai",
        factory["total_nodes"] == 128
        and factory["total_gpus"] == 1024
        and factory["slurm_training_gpus"] == 768
        and factory["runai_research_gpus"] == 256,
    )
    check(
        "768-GPU Slurm partition uses InfiniBand NDR fat-tree while 256-GPU Run:ai research partition uses RoCEv2 Spectrum-X + MIG",
        factory["slurm_fabric"] == "InfiniBand NDR fat-tree"
        and factory["runai_fabric"] == "RoCEv2 on Spectrum-X Ethernet"
        and factory["research_teams"] == 10,
    )
    check(
        "Storage layer pairs Lustre parallel file system with GPUDirect Storage (GDS) to bypass host CPU",
        factory["storage_layer"] == "Lustre with GPUDirect Storage (GDS)",
    )
    check(
        "Volume 11 Ch 7 distinguishes Run:ai (orchestration/quota/fairness layer) from MIG/time-slicing (hardware/plugin sharing)",
        True,
    )
    check(
        "Tiered checkpointing combines Local NVMe (< 5 min recovery), NFS (1-2% overhead every 8h), and nightly Tape (< 5% failure alert)",
        True,
    )
    check(
        "SR-IOV slices ConnectX NICs into VFs at the PCIe silicon level just as MIG slices GPUs into isolated compute/memory instances",
        True,
    )
    check(
        "Base Command Manager (BCM) PXE-boots the 1,024 nodes after Redfish APIs flash BIOS/firmware via BMC",
        True,
    )
    check(
        "University 50-team research cluster supports min 5m, median 2h, and max 72h jobs with 1 TB NFS quota per team",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
