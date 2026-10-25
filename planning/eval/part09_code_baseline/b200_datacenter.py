#!/usr/bin/env python3
"""Part 9, Chapter 9.7: DGX B200 SuperPOD data center design model.

Encodes every specification, 3-phase power-provisioning table row, 5-of-6 PSU
redundancy rule, altitude/ASHRAE/ISO-14644-1 Class-8 environmental threshold,
and DAC/AOC 90% cable length rule from:
- Data Center Best Practices with DGX B200 (superpod-b200-dc, pp. 1-24)
"""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


def compute_b200_rack_circuit_row(
    dist_voltage_v: int,
    amps: int,
    breaker_derating: float,
    power_factor: float = 0.95,
    circuits_per_rack: int = 2,
) -> Dict[str, object]:
    """Reproduce any row of the DGX B200 Power Provisioning Table (superpod-b200-dc p. 11).

    Source: superpod-b200-dc pp. 10-11 ("Planning Power and Cooling per Rack" & "Power Provisioning").
    My inference: The table's rounded "Maximum Rack Power Capacity kW*" and tenth-of-a-kW
    "Stranded Capacity at Peak Demand kW**" columns come from the exact 3-phase formula:
      raw_rack_kw = circuits_per_rack * sqrt(3) * dist_voltage_v * amps * power_factor * breaker_derating / 1000
      supported_nodes = 4 if raw_rack_kw >= 57.2 else (2 if raw_rack_kw >= 28.6 else 0)
      peak_demand_kw = supported_nodes * 14.3
      stranded_kw = round(raw_rack_kw - peak_demand_kw, 1)
    """
    if dist_voltage_v <= 0 or amps <= 0 or not (0.0 < breaker_derating <= 1.0):
        raise ValueError("Invalid electrical circuit parameters.")

    raw_rack_kw = (
        circuits_per_rack
        * math.sqrt(3.0)
        * float(dist_voltage_v)
        * float(amps)
        * power_factor
        * breaker_derating
        / 1000.0
    )
    supported_nodes = 4 if raw_rack_kw >= 57.2 else (2 if raw_rack_kw >= 28.6 else 0)
    peak_demand_kw = round(supported_nodes * 14.3, 1)
    stranded_kw = round(raw_rack_kw - peak_demand_kw, 1)

    return {
        "dist_voltage_v": dist_voltage_v,
        "amps": amps,
        "breaker_derating_pct": round(breaker_derating * 100.0, 1),
        "max_rack_capacity_kw_rounded": int(round(raw_rack_kw)),
        "supported_b200_systems": supported_nodes,
        "peak_demand_kw": peak_demand_kw,
        "stranded_capacity_kw": stranded_kw,
        "required_airflow_cfm": supported_nodes * 2145,
        "recommended_rack_ru": 52,
    }


def evaluate_b200_psu_provisioning_model(model_name: str) -> Dict[str, object]:
    """Evaluate the 5 DGX B200 power-provisioning topologies from superpod-b200-dc pp. 12-16.

    Source: superpod-b200-dc pp. 12-16:
    - Hardware rule: DGX B200 has 6 PSUs and requires at least 5 of 6 PSUs energized to operate.
    - Models:
      1. "dual_source_non_interleaved" (p. 12): PDU loss = 50% rack, UPS loss = 50% rack. Recommended for 2 UPS sources.
      2. "single_source_dual_rpdu" (p. 13): PDU loss = 50% rack, UPS loss = 100% rack.
      3. "dual_interleaved" (p. 14): 3 PSUs on Feed A + 3 PSUs on Feed B -> losing EITHER PDU or UPS drops 3 PSUs/node (only 3/6 remain < 5 required), crashing 100% of systems! STOP - NOT RECOMMENDED.
      4. "dual_ups_with_sts" (p. 15): Static Transfer Switch is SPOF and untested/unvalidated by NVIDIA (switchover may damage systems). STOP - NOT RECOMMENDED.
      5. "six_to_make_five" (p. 16): 6 discrete UPS sources and 6 PDUs (1 PSU per source). Losing any 1 PDU or 1 UPS leaves 5 of 6 PSUs energized -> 0% systems impacted. Optimal for High Availability (typically <= 2 systems/rack).
    """
    models: Dict[str, Dict[str, object]] = {
        "dual_source_non_interleaved": {
            "psus_energized_on_single_pdu_loss_node1": 0,
            "psus_energized_on_single_pdu_loss_node2": 6,
            "single_pdu_failure_rack_impact_pct": 50,
            "single_ups_failure_rack_impact_pct": 50,
            "redundancy_achieved": "N",
            "nvidia_recommended": True,
            "stop_warning": False,
        },
        "single_source_dual_rpdu": {
            "psus_energized_on_single_pdu_loss_node1": 0,
            "psus_energized_on_single_pdu_loss_node2": 6,
            "single_pdu_failure_rack_impact_pct": 50,
            "single_ups_failure_rack_impact_pct": 100,
            "redundancy_achieved": "N",
            "nvidia_recommended": False,
            "stop_warning": False,
        },
        "dual_interleaved": {
            "psus_energized_on_single_pdu_loss_node1": 3,
            "psus_energized_on_single_pdu_loss_node2": 3,
            "single_pdu_failure_rack_impact_pct": 100,
            "single_ups_failure_rack_impact_pct": 100,
            "redundancy_achieved": "None (worse than N)",
            "nvidia_recommended": False,
            "stop_warning": True,
        },
        "dual_ups_with_sts": {
            "psus_energized_on_single_pdu_loss_node1": 0,
            "psus_energized_on_single_pdu_loss_node2": 6,
            "single_pdu_failure_rack_impact_pct": 50,
            "single_ups_failure_rack_impact_pct": 0,
            "redundancy_achieved": "N+1 (with STS SPOF risk)",
            "nvidia_recommended": False,
            "stop_warning": True,
        },
        "six_to_make_five": {
            "psus_energized_on_single_pdu_loss_node1": 5,
            "psus_energized_on_single_pdu_loss_node2": 5,
            "single_pdu_failure_rack_impact_pct": 0,
            "single_ups_failure_rack_impact_pct": 0,
            "redundancy_achieved": "N+1",
            "nvidia_recommended": True,
            "stop_warning": False,
        },
    }
    if model_name not in models:
        raise ValueError(f"Unknown power provisioning model: {model_name}")
    return models[model_name]


def check_b200_environmental_compliance(
    altitude_ft: float,
    inlet_temp_c: float,
    relative_humidity_pct: float,
    dew_point_c: float,
    merv_rating: int,
    particles_0_5um_per_m3: int,
    particulate_excursion_minutes: float = 0.0,
) -> Dict[str, object]:
    """Validate altitude-derated temperature, ASHRAE Class A1, MERV 13, and ISO 14644-1 Class 8.

    Sources:
    - superpod-b200-dc p. 4:
      - Max altitude: 10,000 ft (3,048 m).
      - 0 - 1,000 ft: 5°C to 35°C (capped at 30°C for continuous ASHRAE A1 DGX B200 operation on p. 17;
        altitude table on p. 4 states 5-35°C @ 0-1000 ft, 5-30°C @ 1000-5000 ft, 5-25°C @ 5000-10000 ft).
      - Acoustic L_WA,m: 96 dB at <= 25°C, 101 dB at 30°C.
    - superpod-b200-dc p. 17:
      - ASHRAE Recommended ("All A"): 18-27°C, <= 60% RH, <= 15°C dew point.
      - ASHRAE A1 Allowable for DGX B200: up to 30°C (86°F), 20-80% RH, <= 17°C dew point.
      - Filtration >= MERV 13.
      - ISO 14644-1 Class 8 cleanliness: <= 3,520,000 particles/m^3 at >= 0.5 um (excursions > 3,520,000
        must not last longer than 15 minutes).
    """
    violations: List[str] = []

    if altitude_ft < 0 or altitude_ft > 10000:
        violations.append(f"altitude_out_of_range ({altitude_ft} ft > 10,000 ft max)")
        max_alt_temp_c = 25.0
    elif altitude_ft <= 1000:
        max_alt_temp_c = 35.0
    elif altitude_ft <= 5000:
        max_alt_temp_c = 30.0
    else:
        max_alt_temp_c = 25.0

    # Continuous ASHRAE A1 allowable ceiling for DGX B200 is 30.0 C (p. 4 & p. 17)
    effective_max_temp_c = min(30.0, max_alt_temp_c)
    if inlet_temp_c < 5.0 or inlet_temp_c > effective_max_temp_c:
        violations.append(
            f"inlet_temp_violation ({inlet_temp_c}C outside 5.0C..{effective_max_temp_c}C at {altitude_ft} ft)"
        )

    if not (20.0 <= relative_humidity_pct <= 80.0):
        violations.append(f"humidity_violation ({relative_humidity_pct}% RH outside 20%..80% A1 envelope)")

    if dew_point_c > 17.0:
        violations.append(f"dew_point_violation ({dew_point_c}C > 17.0C Class A1 max)")

    if merv_rating < 13:
        violations.append(f"filter_below_merv13 (MERV {merv_rating} < MERV 13 minimum)")

    if particles_0_5um_per_m3 > 3_520_000 and particulate_excursion_minutes > 15.0:
        violations.append(
            f"iso_class8_particulate_violation ({particles_0_5um_per_m3} @ 0.5um for {particulate_excursion_minutes} min > 15 min limit)"
        )

    in_recommended_band = (
        18.0 <= inlet_temp_c <= 27.0 and relative_humidity_pct <= 60.0 and dew_point_c <= 15.0
    )
    acoustic_db = 96 if inlet_temp_c <= 25.0 else 101

    return {
        "compliant": len(violations) == 0,
        "in_ashrae_recommended_band": in_recommended_band,
        "effective_max_temp_c": effective_max_temp_c,
        "estimated_acoustic_db": acoustic_db,
        "violations": violations,
    }


def validate_ib_cable_run(media_type: str, length_meters: float) -> Dict[str, object]:
    """Validate InfiniBand DAC/AOC cable lengths against max standard and 90% design limits.

    Source: superpod-b200-dc pp. 20-21 ("DGX Cabling Types" & "DGX Infrastructure Support"):
    - Passive DAC 100G: max 5.0 m (90% design limit = 4.5 m).
    - Passive DAC 400G: max 3.0 m (90% design limit = 2.7 m).
    - Active Optical Cable (AOC): max 30.0 m (90% design limit = 27.0 m).
    - Rule (p. 21): "Keep cable runs under 90% of the max distance supported for each media type".
    """
    if length_meters <= 0:
        raise ValueError("length_meters must be positive.")

    limits: Dict[str, float] = {
        "DAC-100G": 5.0,
        "DAC-400G": 3.0,
        "AOC": 30.0,
    }
    if media_type not in limits:
        raise ValueError(f"Unknown media_type: {media_type}")

    max_m = limits[media_type]
    design_90pct_m = round(max_m * 0.90, 2)
    within_standard = length_meters <= max_m
    within_90pct_rule = length_meters <= design_90pct_m

    return {
        "media_type": media_type,
        "length_meters": length_meters,
        "max_standard_meters": max_m,
        "max_90pct_design_meters": design_90pct_m,
        "within_standard_max": within_standard,
        "passes_90pct_best_practice": within_90pct_rule,
    }
