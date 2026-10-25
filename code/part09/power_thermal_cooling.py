#!/usr/bin/env python3
"""Part 9, Chapter 9.11: Power delivery, thermal design and liquid cooling model.

Encodes the electrical distribution formulas, PSU redundancy generations
(DGX H100 3+3 vs DGX B200 5-of-6 N+1 vs DGX GB300 8x33 kW shelves), sensible
heat airflow (CFM = 3.16 * W / dT_F), PUE & monthly kWh budgeting, optical
transceiver power (QSFP28 vs QSFP56-DD vs OSFP), and liquid cooling architectures.

Sources:
- nvidia-devops Volume 05 Chapter 4, Volume 01 Chapter 6, Volume 21 Chapter 5
- Data Center Best Practices with DGX B200 (superpod-b200-dc, pp. 4-18)
- NVIDIA DGX SuperPOD Reference Architecture Featuring DGX GB300 Systems (pp. 5-11)
- AI Data Center Network Design and Technologies, Chapter 5 (lines 1-112)
"""

from __future__ import annotations

import math
from typing import Dict, List


OPTICS_POWER_WATTS: Dict[str, float] = {
    "QSFP28": 3.2,
    "QSFP56-DD": 12.0,
    "OSFP": 15.0,
}


def calculate_three_phase_circuit_kw(
    voltage_v: float,
    current_a: float,
    derating_factor: float = 0.80,
    power_factor: float = 1.0,
) -> Dict[str, float]:
    """Calculate 3-phase nameplate and continuous derated power capacity (kW).

    Source: nvidia-devops Volume 21 Chapter 5 ("3.1 Power Distribution Tiers", lines 164-167):
    Example: 3-phase 208V at 60A is sqrt(3) * 208 * 60 / 1000 = 21.62 kW (~21.6 kW) nameplate,
    and at 80% continuous derating is 21.62 * 0.80 = 17.29 kW (~17.3 kW) continuous.
    """
    if voltage_v <= 0 or current_a <= 0 or not (0.0 < derating_factor <= 1.0) or not (0.0 < power_factor <= 1.0):
        raise ValueError("Invalid 3-phase circuit parameters.")

    nameplate_kw = (math.sqrt(3.0) * voltage_v * current_a * power_factor) / 1000.0
    continuous_kw = nameplate_kw * derating_factor
    return {
        "nameplate_kw": round(nameplate_kw, 1),
        "continuous_derated_kw": round(continuous_kw, 1),
    }


def calculate_sensible_heat_airflow_cfm(
    heat_load_watts: float,
    delta_t_celsius: float = 20.0,
) -> Dict[str, float]:
    """Estimate required cooling airflow (CFM) using the sensible heat equation.

    Source: nvidia-devops Volume 21 Chapter 5 ("2.2 Reference Cooling Design", lines 114-118):
    - delta_t_fahrenheit = delta_t_celsius * 1.8 (for 20 C, delta_t_F = 36 F)
    - CFM = 3.16 * Watts / delta_t_F
    - Worked example: 81,600 W at 20 C (36 F) rise -> 3.16 * 81600 / 36 = 7,161.6 CFM (~7,160 CFM).
    """
    if heat_load_watts <= 0 or delta_t_celsius <= 0:
        raise ValueError("heat_load_watts and delta_t_celsius must be positive.")

    delta_t_fahrenheit = delta_t_celsius * 1.8
    cfm = (3.16 * heat_load_watts) / delta_t_fahrenheit
    btu_per_hr = heat_load_watts * 3.41214
    return {
        "heat_load_kw": round(heat_load_watts / 1000.0, 2),
        "delta_t_celsius": delta_t_celsius,
        "delta_t_fahrenheit": round(delta_t_fahrenheit, 1),
        "required_airflow_cfm": round(cfm, 1),
        "heat_load_btu_hr": round(btu_per_hr),
    }


def calculate_monthly_cluster_energy_and_cost(
    train_hours_per_day: float = 16.0,
    train_facility_kw: float = 110.0,
    idle_hours_per_day: float = 4.0,
    idle_facility_kw: float = 20.0,
    maint_hours_per_day: float = 4.0,
    maint_facility_kw: float = 40.0,
    days_per_month: int = 30,
    cost_per_kwh_usd: float = 0.12,
) -> Dict[str, float]:
    """Reproduce the Volume 21 Chapter 5 64-GPU cluster energy and cost budget.

    Source: nvidia-devops Volume 21 Chapter 5 ("1.2 Cluster-Level Power Budget", lines 66-88):
    - 8 nodes * 10.2 kW = 81.6 kW IT load; at 1.35 PUE = 110.16 kW (~110 kW) facility load.
    - Schedule (24h): 16h training @ 110 kW (52,800 kWh/mo), 4h idle @ 20 kW (2,400 kWh/mo),
      4h maintenance @ 40 kW (4,800 kWh/mo) -> 60,000 kWh/month.
    - At $0.12/kWh: $7,200/month = $86,400/year.
    """
    if round(train_hours_per_day + idle_hours_per_day + maint_hours_per_day, 2) != 24.0:
        raise ValueError("Daily hours (train + idle + maint) must sum to 24.0.")
    if days_per_month <= 0 or cost_per_kwh_usd <= 0:
        raise ValueError("days_per_month and cost_per_kwh_usd must be positive.")

    train_kwh = train_hours_per_day * days_per_month * train_facility_kw
    idle_kwh = idle_hours_per_day * days_per_month * idle_facility_kw
    maint_kwh = maint_hours_per_day * days_per_month * maint_facility_kw
    total_monthly_kwh = train_kwh + idle_kwh + maint_kwh
    monthly_cost = total_monthly_kwh * cost_per_kwh_usd
    annual_cost = monthly_cost * 12.0

    return {
        "train_kwh_month": round(train_kwh, 1),
        "idle_kwh_month": round(idle_kwh, 1),
        "maint_kwh_month": round(maint_kwh, 1),
        "total_kwh_month": round(total_monthly_kwh, 1),
        "monthly_cost_usd": round(monthly_cost, 2),
        "annual_cost_usd": round(annual_cost, 2),
    }


def select_cooling_architecture(
    rack_power_kw: float,
    system_type: str = "generic_air",
    has_facility_chilled_water: bool = True,
) -> Dict[str, object]:
    """Recommend the appropriate cooling architecture for a given rack power density.

    Sources:
    - nvidia-devops Volume 01 Chapter 6, Volume 05 Chapter 4, Volume 21 Chapter 5
    - superpod-b200-dc p. 10 (RDHx / in-row coolers not typically suitable for DGX B200; 4x B200 = 57.2 kW)
    - superpod-gb300-ra p. 8 (DGX GB300 NVL72 uses hybrid direct liquid cooling + air cooling)
    - AI Data Center Network Design and Technologies Chapter 5 (lines 26-74: Cold plate DLC, RDHx,
      Single/Two-Phase Immersion, Sprayed Liquid Cooling)
    """
    if rack_power_kw <= 0:
        raise ValueError("rack_power_kw must be positive.")

    if system_type == "DGX-GB300-NVL72":
        # My inference: illustrative ~85% liquid / ~15% air heat capture split for hybrid DLC+air rack
        return {
            "cooling_method": "Hybrid Direct-to-Chip Liquid Cooling (DLC) + Air Cooling",
            "requires_cdu": True,
            "rdhx_suitable": False,
            "estimated_liquid_capture_kw": round(rack_power_kw * 0.85, 2),
            "estimated_air_rejection_kw": round(rack_power_kw * 0.15, 2),
        }

    if system_type == "DGX-B200":
        return {
            "cooling_method": "High-Velocity Air Cooling with Hot/Cold Aisle Containment (150 CFM/kW)",
            "requires_cdu": False,
            "rdhx_suitable": False,  # Explicitly noted as not typically suitable on SPB200 p. 10
            "estimated_liquid_capture_kw": 0.0,
            "estimated_air_rejection_kw": rack_power_kw,
        }

    if rack_power_kw <= 40.0:
        return {
            "cooling_method": "Forced Air Cooling with Hot/Cold Aisle Containment",
            "requires_cdu": False,
            "rdhx_suitable": True,
            "estimated_liquid_capture_kw": 0.0,
            "estimated_air_rejection_kw": rack_power_kw,
        }

    if rack_power_kw <= 60.0 and not has_facility_chilled_water:
        return {
            "cooling_method": "Closed-Loop Liquid Cooling (CLLC) or Specialized Extreme-Density Air",
            "requires_cdu": False,
            "rdhx_suitable": False,
            "estimated_liquid_capture_kw": 0.0,
            "estimated_air_rejection_kw": rack_power_kw,
        }

    return {
        "cooling_method": "Direct-to-Chip Liquid Cooling (DLC) with Facility CDU (or Immersion)",
        "requires_cdu": True,
        "rdhx_suitable": False,
        "estimated_liquid_capture_kw": round(rack_power_kw * 0.85, 2),
        "estimated_air_rejection_kw": round(rack_power_kw * 0.15, 2),
    }
