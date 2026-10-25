#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.13: Sizing and capacity-planning exercises."""

from __future__ import annotations

import sys

from capacity_planning import (
    bin_pack_gpu_jobs,
    calculate_effective_capacity_and_token_cost,
    calculate_multiyear_fleet_tco,
    evaluate_finops_zombie_reaper,
    forecast_36month_capacity_exercise,
    forecast_saturating_scurve_gpus,
)


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.13 Lab: Sizing and Capacity-Planning Exercises ===")

    # 1. Effective Capacity & Cost per 1M Tokens checks (VL8 Ch 2 & V21 Ch 12)
    # V21 Ch 12 Part 1.2: 408 GPUs serving 2,000 QPS * 150 tok = 300,000 tok/s at $18,012/day ($750.5/hr)
    c_100 = calculate_effective_capacity_and_token_cost(
        nominal_capacity_tps=300_000.0,
        expected_utilization=1.0,
        availability_factor=1.0,
        total_hourly_cost_usd=750.5,
    )
    check(
        "V21 Ch12: 408-GPU fleet (300k tok/s) at $750.5/hr ($18.01K/day) costs $0.695 (~$0.70) per 1M tokens",
        0.69 <= c_100["cost_per_million_tokens_usd"] <= 0.70,
        f"got {c_100}",
    )

    c_40 = calculate_effective_capacity_and_token_cost(
        nominal_capacity_tps=300_000.0,
        expected_utilization=0.40,
        availability_factor=1.0,
        total_hourly_cost_usd=750.5,
    )
    check(
        "V21 Ch12: At 40% utilization, cost per 1M tokens rises 2.5x to $1.7373",
        round(c_40["cost_per_million_tokens_usd"] / c_100["cost_per_million_tokens_usd"], 2) == 2.5,
        f"got {c_40}",
    )

    c_degraded = calculate_effective_capacity_and_token_cost(
        nominal_capacity_tps=100_000.0,
        expected_utilization=0.40,
        availability_factor=0.80,
        total_hourly_cost_usd=320.0,
    )
    check(
        "VL8 Ch2: Effective capacity (100k * 0.40 * 0.80) == 32,000 tok/s (115.2M tok/hr)",
        c_degraded["effective_capacity_tps"] == 32000.0
        and c_degraded["tokens_per_hour_millions"] == 115.2,
    )

    try:
        calculate_effective_capacity_and_token_cost(100_000.0, 1.5, 1.0, 100.0)
        check("Rejects utilization > 1.0", False)
    except ValueError:
        check("Rejects utilization > 1.0", True)

    # 2. FinOps Zombie Reaper Bot checks (V19 Ch 3 §3)
    z_hit = evaluate_finops_zombie_reaper(
        k8s_gpu_allocated=True, dcgm_sm_active_pct=1.2, idle_duration_hours=4.5
    )
    check(
        "V19 Ch3: Allocated GPU with SM_ACTIVE=1.2% (<5%) for 4.5h (>=4h) is evicted as zombie pod",
        z_hit["is_zombie_pod"] is True and z_hit["action"] == "evict_pod_and_notify_slack",
    )

    z_active = evaluate_finops_zombie_reaper(
        k8s_gpu_allocated=True, dcgm_sm_active_pct=42.0, idle_duration_hours=10.0
    )
    check(
        "Active GPU pod (SM_ACTIVE=42%) is kept running",
        z_active["is_zombie_pod"] is False and z_active["action"] == "keep_running",
    )

    z_short = evaluate_finops_zombie_reaper(
        k8s_gpu_allocated=True, dcgm_sm_active_pct=0.0, idle_duration_hours=1.5
    )
    check(
        "Idle GPU pod for 1.5h (< 4.0h grace window) is kept running",
        z_short["is_zombie_pod"] is False,
    )

    # 3. GPU Job Bin-Packing checks (V21 Ch 12 Part 1.1)
    bp = bin_pack_gpu_jobs([8, 4, 4, 8, 4], gpus_per_node=8)
    check(
        "V21 Ch12: Packing [8, 4, 4, 8, 4] (28 GPUs) uses 4 nodes at 87.5% allocation (saves 1 node vs unpacked)",
        bp["total_gpus_requested"] == 28
        and bp["packed_nodes_used"] == 4
        and bp["unpacked_nodes_used"] == 5
        and bp["nodes_saved"] == 1
        and bp["packed_allocation_pct"] == 87.5,
        f"got {bp}",
    )

    try:
        bin_pack_gpu_jobs([16], gpus_per_node=8)
        check("Rejects single-node job request > gpus_per_node", False)
    except ValueError:
        check("Rejects single-node job request > gpus_per_node", True)

    # 4. Multi-Year Hardware Refresh & GPU-Year TCO Amortization checks (V21 Ch 11 §1.2 & Ch 12 Part 3)
    tco_ramp = calculate_multiyear_fleet_tco(
        year1_gpus=464,
        year1_capex_m=13.9,
        year2_added_gpus=60,
        year2_capex_m=2.4,
        year3_added_gpus=100,
        year3_capex_m=3.5,
        annual_opex_m=3.0,
    )
    check(
        "V21 Ch11: 464->524->624 GPU ramp == $19.8M CAPEX + $9.0M OPEX = $28.8M TCO over 1,612 GPU-years ($17.9K/GPU-yr)",
        tco_ramp["total_capex_m"] == 19.8
        and tco_ramp["total_opex_m"] == 9.0
        and tco_ramp["total_3yr_tco_m"] == 28.8
        and tco_ramp["total_gpu_years"] == 1612
        and tco_ramp["cost_per_gpu_year_k_usd"] == 17.9,
        f"got {tco_ramp}",
    )

    tco_1200 = calculate_multiyear_fleet_tco(
        year1_gpus=1200,
        year1_capex_m=44.0,
        year2_added_gpus=0,
        year2_capex_m=0.0,
        year3_added_gpus=0,
        year3_capex_m=0.0,
        annual_opex_m=26.2 / 3.0,
    )
    check(
        "V21 Ch12 Part 3: 1,200-GPU deployment ($44M CAPEX + $26.2M OPEX = $70.2M) == $19.5K/GPU-year over 3,600 GPU-years",
        tco_1200["total_3yr_tco_m"] == 70.2
        and tco_1200["total_gpu_years"] == 3600
        and tco_1200["cost_per_gpu_year_k_usd"] == 19.5,
        f"got {tco_1200}",
    )

    # 5. Volume 21 Lab 04 36-Month Demand Forecast & Facility-Wall checks
    f36 = forecast_36month_capacity_exercise(kw_per_gpu=1.3)
    check(
        "V21 Lab 04: Total GPU demand is 26 (M0), 70 (M6), 98 (M8), 115 (M9), and 136 (M10)",
        f36["month_0_gpus"] == 26
        and f36["month_6_gpus"] == 70
        and f36["month_8_gpus"] == 98
        and f36["month_9_gpus"] == 115
        and f36["month_10_gpus"] == 136,
        f"got {f36}",
    )
    check(
        "V21 Lab 04: 150 kW facility ceiling (~115-117 GPUs) is breached at Month 10, and Month 36 exceeds 11,000 GPUs",
        f36["first_month_exceeding_117_gpus"] == 10 and f36["month_36_gpus"] > 11000,
        f"got {f36}",
    )

    # 6. Saturating S-curve & Seasonal Forecast checks (V21 Ch 11 & Lab 04)
    sc_m0 = forecast_saturating_scurve_gpus(26.0, carrying_capacity_gpus=115.0, monthly_rate=0.25, month=0)
    sc_m36 = forecast_saturating_scurve_gpus(26.0, carrying_capacity_gpus=115.0, monthly_rate=0.25, month=36)
    check(
        "Logistic S-curve starts at 26.0 GPUs (M0) and asymptotes cleanly at 115.0 GPUs (M36) within 150 kW limit",
        sc_m0 == 26.0 and 114.8 <= sc_m36 <= 115.0,
        f"got m0={sc_m0}, m36={sc_m36}",
    )

    try:
        forecast_saturating_scurve_gpus(120.0, carrying_capacity_gpus=100.0, monthly_rate=0.2, month=12)
        check("Rejects carrying_capacity_gpus <= initial_gpus", False)
    except ValueError:
        check("Rejects carrying_capacity_gpus <= initial_gpus", True)

    # Additional Spot vs On-Demand & V19 Ch 3 MIG 7x reclamation checks
    on_demand_gpu_yr = 7.50 * 24 * 300  # $54,000 in V21 Ch 12 Part 2.1
    spot_gpu_yr = 2.63 * 24 * 300       # $18,936 (~$18.9K) in V21 Ch 12 Part 2.1
    check(
        "V21 Ch12 Part 2.1: Spot ($2.63/GPU/hr = $18.9K/300d) saves ~$35.1K/GPU/yr (~65%) vs On-Demand ($7.50/hr = $54K)",
        on_demand_gpu_yr == 54000.0 and round((on_demand_gpu_yr - spot_gpu_yr) / 1000.0, 1) == 35.1,
    )
    check(
        "V19 Ch3 Customer Scenario: Slicing 16x 8-GPU H100 nodes (128 GPUs) into 1g.10gb MIG profiles yields 896 logical instances",
        16 * 8 * 7 == 896,
    )

    # 7. V21 Ch 11 Seasonal Forecast & V21 Ch 12 1,200-GPU PFLOP/QPS Cost checks
    import math
    q0 = round(286.0 * ((1.10) ** 0) * (1.0 + 0.15 * math.sin(2.0 * math.pi * (12 % 12) / 12.0)))
    q6 = round(286.0 * ((1.10) ** 6) * (1.0 + 0.15 * math.sin(2.0 * math.pi * (18 % 12) / 12.0)))
    q11 = round(286.0 * ((1.10) ** 11) * (1.0 + 0.15 * math.sin(2.0 * math.pi * (23 % 12) / 12.0)))
    check(
        "V21 Ch11 Part 1.1: Seasonal forecast from 286 QPS yields 286 (M+0), 507 (M+6), and 755 (M+11) QPS",
        q0 == 286 and q6 == 507 and q11 == 755,
        f"got q0={q0}, q6={q6}, q11={q11}",
    )
    check(
        "V21 Ch11 Part 1.1: At 7.6 QPS/GPU, GPU requirements are 38 (M+0), 67 (M+6), and 99 (M+11) GPUs",
        round(q0 / 7.6) == 38 and round(q6 / 7.6) == 67 and round(q11 / 7.6) == 99,
    )
    check(
        "V21 Ch11 Part 2.1: Upfront 1000 QPS (132 GPUs @ $30K) costs $3.96M vs $2.37M incremental (+79 GPUs)",
        round(132 * 0.03, 2) == 3.96 and round(79 * 0.03, 2) == 2.37,
    )
    check(
        "V21 Ch12 Part 3: 1,200 H100s = 1,186.8 BF16 PFLOPS; at $23.4M/yr, cost per PFLOP-year == $19.7K",
        round(1200 * 0.989, 1) == 1186.8 and round(23400.0 / 1186.8, 1) == 19.7,
    )
    check(
        "V21 Ch12 Part 3: 1,200 H100s = ~9,120 QPS; at $23.4M/yr, cost per 1K QPS capacity == $2.57M (~$2.6M)/yr",
        round(23.4 / 9.1, 1) == 2.6,
    )
    check(
        "ASP Ch2 chunk 8 ROI case study: Replacing 100 H100s (70 kW) with 50 B200s (50 kW) saves 20 kW continuously",
        70 - 50 == 20,
    )
    try:
        calculate_multiyear_fleet_tco(0, 10.0, 0, 0.0, 0, 0.0, 1.0)
        check("Rejects non-positive year1_gpus in TCO calculator", False)
    except ValueError:
        check("Rejects non-positive year1_gpus in TCO calculator", True)

    try:
        forecast_36month_capacity_exercise(initial_qps=-10.0)
        check("Rejects negative initial_qps in 36-month forecaster", False)
    except ValueError:
        check("Rejects negative initial_qps in 36-month forecaster", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
