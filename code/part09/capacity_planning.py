#!/usr/bin/env python3
"""Part 9, Chapter 9.13: Sizing and capacity-planning exercises model.

Encodes the Solutions Architecture methodology, Effective Capacity & TCO math,
FinOps Reaper & bin-packing algorithms, seasonal & 36-month exponential/logistic
demand forecasting, multi-year GPU-year amortization, and PoC falsifiability checks.

Sources:
- volume-08/01-architecture-design-masterclass.md & 02-capacity-tco-masterclass.md
- nvidia-devops Volume 19 Chapters 3 and 6
- nvidia-devops Volume 21 Chapters 11 and 12 & Lab 04
"""

from __future__ import annotations

import math
from typing import Dict, List


def calculate_effective_capacity_and_token_cost(
    nominal_capacity_tps: float,
    expected_utilization: float,
    availability_factor: float,
    total_hourly_cost_usd: float,
) -> Dict[str, float]:
    """Calculate Effective Capacity and Cost per 1M Tokens (VL8 Ch 2 §2).

    Source: volume-08/02-capacity-tco-masterclass.md ("2. The Mathematics of TCO and Useful Work"):
    - effective_capacity = nominal_capacity * expected_utilization * availability_factor
    - cost_per_million_tokens = total_hourly_cost / (tokens_per_hour / 1_000_000)
    """
    if nominal_capacity_tps <= 0 or total_hourly_cost_usd <= 0:
        raise ValueError("nominal_capacity_tps and total_hourly_cost_usd must be positive.")
    if not (0.0 < expected_utilization <= 1.0) or not (0.0 < availability_factor <= 1.0):
        raise ValueError("expected_utilization and availability_factor must be in (0, 1].")

    effective_tps = nominal_capacity_tps * expected_utilization * availability_factor
    tokens_per_hour = effective_tps * 3600.0
    cost_per_1m = total_hourly_cost_usd / (tokens_per_hour / 1_000_000.0)
    return {
        "effective_capacity_tps": round(effective_tps, 2),
        "tokens_per_hour_millions": round(tokens_per_hour / 1_000_000.0, 4),
        "cost_per_million_tokens_usd": round(cost_per_1m, 4),
    }


def evaluate_finops_zombie_reaper(
    k8s_gpu_allocated: bool,
    dcgm_sm_active_pct: float,
    idle_duration_hours: float,
    sm_threshold_pct: float = 5.0,
    max_idle_hours: float = 4.0,
) -> Dict[str, object]:
    """Determine whether the FinOps Reaper Bot should evict an allocated GPU pod (V19 Ch 3 §3).

    Source: nvidia-devops Volume 19 Chapter 3 ("3. FinOps: Ruthless De-Allocation"):
    If a pod holds a GPU (`k8s_gpu_allocated=True`) but `DCGM_FI_PROF_SM_ACTIVE` remains
    below 5% (`< 5.0`) for at least 4 hours (`>= 4.0`), terminate the pod and notify Slack.
    """
    is_zombie = (
        k8s_gpu_allocated
        and dcgm_sm_active_pct < sm_threshold_pct
        and idle_duration_hours >= max_idle_hours
    )
    return {
        "is_zombie_pod": is_zombie,
        "action": "evict_pod_and_notify_slack" if is_zombie else "keep_running",
    }


def bin_pack_gpu_jobs(job_gpu_requests: List[int], gpus_per_node: int = 8) -> Dict[str, object]:
    """Pack multi-GPU jobs onto 8-GPU nodes using First-Fit Decreasing (V21 Ch 12 Part 1.1).

    Source: nvidia-devops Volume 21 Chapter 12 ("Optimization 2: Job packing (bin-packing)"):
    Jobs requesting [8, 4, 4, 8, 4] GPUs = 28 GPUs pack onto 4 nodes (32 GPUs) = 87.5%
    allocation, versus 5 nodes (40 GPUs = 70.0% allocation) if spread one job per node.
    """
    if gpus_per_node <= 0 or not job_gpu_requests:
        raise ValueError("gpus_per_node must be > 0 and job_gpu_requests non-empty.")
    if any(r <= 0 or r > gpus_per_node for r in job_gpu_requests):
        raise ValueError(f"Each job request must be between 1 and {gpus_per_node}.")

    nodes: List[int] = []
    for req in sorted(job_gpu_requests, reverse=True):
        placed = False
        for i in range(len(nodes)):
            if nodes[i] + req <= gpus_per_node:
                nodes[i] += req
                placed = True
                break
        if not placed:
            nodes.append(req)

    total_requested = sum(job_gpu_requests)
    packed_nodes = len(nodes)
    unpacked_nodes = len(job_gpu_requests)
    packed_alloc_pct = round((total_requested / float(packed_nodes * gpus_per_node)) * 100.0, 2)
    return {
        "total_gpus_requested": total_requested,
        "packed_nodes_used": packed_nodes,
        "unpacked_nodes_used": unpacked_nodes,
        "nodes_saved": unpacked_nodes - packed_nodes,
        "packed_allocation_pct": packed_alloc_pct,
    }


def calculate_multiyear_fleet_tco(
    year1_gpus: int,
    year1_capex_m: float,
    year2_added_gpus: int,
    year2_capex_m: float,
    year3_added_gpus: int,
    year3_capex_m: float,
    annual_opex_m: float,
) -> Dict[str, float]:
    """Calculate 3-year fleet TCO, active GPU-years, and amortized cost per GPU-year (V21 Ch 11 §1.2).

    Source: nvidia-devops Volume 21 Chapter 11 ("1.2 Hardware Refresh Cycles", lines 93-126):
    - Year 1: 464 GPUs ($13.9M), active for 3 years = 1,392 GPU-years
    - Year 2: +60 GPUs ($2.4M), active for 2 years = 120 GPU-years
    - Year 3: +100 GPUs ($3.5M), active for 1 year = 100 GPU-years
    - Total CAPEX = $19.8M; Total OPEX = 3 * $3.0M = $9.0M; 3-year TCO = $28.8M.
    - Total GPU-years = 1,392 + 120 + 100 = 1,612 GPU-years.
    - Amortized cost per GPU-year = $28.8M / 1,612 = $17,866 (~$17.9K/GPU-year).
    """
    if year1_gpus <= 0 or year2_added_gpus < 0 or year3_added_gpus < 0:
        raise ValueError("Invalid GPU counts.")

    total_capex_m = round(year1_capex_m + year2_capex_m + year3_capex_m, 2)
    total_opex_m = round(annual_opex_m * 3.0, 2)
    total_tco_m = round(total_capex_m + total_opex_m, 2)
    gpu_years = (year1_gpus * 3) + (year2_added_gpus * 2) + (year3_added_gpus * 1)
    cost_per_gpu_year_k = round((total_tco_m * 1000.0) / float(gpu_years), 1)

    return {
        "total_capex_m": total_capex_m,
        "total_opex_m": total_opex_m,
        "total_3yr_tco_m": total_tco_m,
        "total_gpu_years": gpu_years,
        "cost_per_gpu_year_k_usd": cost_per_gpu_year_k,
    }


def forecast_36month_capacity_exercise(
    initial_qps: float = 100.0,
    qps_monthly_growth: float = 0.15,
    initial_train_jobs: float = 50.0,
    train_monthly_growth: float = 0.20,
    qps_per_gpu: float = 7.6,
    gpus_per_train_job_month: float = 8.0 / 30.0,
    facility_power_limit_kw: float = 150.0,
    kw_per_gpu: float = 1.275,  # 10.2 kW / 8 GPUs = 1.275 kW (~1.3 kW in Lab 04)
) -> Dict[str, object]:
    """Reproduce the Volume 21 Lab 04 36-Month Demand Forecast and Facility-Wall Detection.

    Source: nvidia-devops Volume 21 Lab 04 ("Exercise 1: Demand Forecasting", lines 38-114):
    - Month 0: 100/7.6 (13.16) + 50*8/30 (13.33) = 26.49 (~26) GPUs
    - Month 6: 70.31 (~70) GPUs
    - Month 8: 97.60 (~98) GPUs
    - Month 9: 114.92 (~115) GPUs
    - Month 10: 135.56 (~136) GPUs
    - Facility limit at 150 kW and ~1.3 kW/GPU is ~115-117 GPUs, breached between Month 9 and Month 10.
    """
    if initial_qps <= 0 or qps_per_gpu <= 0 or facility_power_limit_kw <= 0:
        raise ValueError("Invalid forecasting parameters.")

    max_facility_gpus = round(facility_power_limit_kw / kw_per_gpu)
    monthly_totals: List[int] = []
    first_breach_month = -1

    for m in range(37):
        qps_m = initial_qps * ((1.0 + qps_monthly_growth) ** m)
        jobs_m = initial_train_jobs * ((1.0 + train_monthly_growth) ** m)
        gpus_m = (qps_m / qps_per_gpu) + (jobs_m * gpus_per_train_job_month)
        rounded_gpus = int(round(gpus_m))
        monthly_totals.append(rounded_gpus)
        if first_breach_month == -1 and gpus_m > 117.0:
            first_breach_month = m

    return {
        "month_0_gpus": monthly_totals[0],
        "month_6_gpus": monthly_totals[6],
        "month_8_gpus": monthly_totals[8],
        "month_9_gpus": monthly_totals[9],
        "month_10_gpus": monthly_totals[10],
        "month_36_gpus": monthly_totals[36],
        "max_facility_gpus": max_facility_gpus,
        "first_month_exceeding_117_gpus": first_breach_month,
    }


def forecast_saturating_scurve_gpus(
    initial_gpus: float,
    carrying_capacity_gpus: float,
    monthly_rate: float,
    month: int,
) -> float:
    """Logistic S-curve forecast replacing unrealistic multi-year exponential growth (Lab 04 note).

    My inference: Implements the saturating logistic growth curve `K / (1 + ((K - G0)/G0) * e^(-r*t))`
    recommended by Volume 21 Lab 04 (line 10) when unconstrained 15%-20% monthly compounding
    produces >11,000 GPUs by Month 36.
    """
    if initial_gpus <= 0 or carrying_capacity_gpus <= initial_gpus or monthly_rate <= 0 or month < 0:
        raise ValueError("Invalid S-curve parameters.")
    ratio = (carrying_capacity_gpus - initial_gpus) / initial_gpus
    val = carrying_capacity_gpus / (1.0 + ratio * math.exp(-monthly_rate * month))
    return round(val, 1)
