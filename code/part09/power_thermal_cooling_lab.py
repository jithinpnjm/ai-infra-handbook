#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.11: Power delivery, thermal design and liquid cooling."""

from __future__ import annotations

import sys

from power_thermal_cooling import (
    OPTICS_POWER_WATTS,
    calculate_monthly_cluster_energy_and_cost,
    calculate_sensible_heat_airflow_cfm,
    calculate_three_phase_circuit_kw,
    select_cooling_architecture,
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

    print("=== Chapter 9.11 Lab: Power Delivery, Thermal Design & Liquid Cooling ===")

    # 1. Three-phase circuit & derating checks (V21 Ch 5 & V6 Lab 02)
    c_208_60 = calculate_three_phase_circuit_kw(208.0, 60.0, derating_factor=0.80)
    check(
        "V21 Ch5: 3-phase 208V 60A circuit is 21.6 kW nameplate and 17.3 kW continuous (80% derated)",
        c_208_60["nameplate_kw"] == 21.6 and c_208_60["continuous_derated_kw"] == 17.3,
        f"got {c_208_60}",
    )

    c_415_32 = calculate_three_phase_circuit_kw(415.0, 32.0, derating_factor=0.80)
    check(
        "3-phase 415V 32A circuit is 23.0 kW nameplate and 18.4 kW continuous (80% derated)",
        c_415_32["nameplate_kw"] == 23.0 and c_415_32["continuous_derated_kw"] == 18.4,
        f"got {c_415_32}",
    )

    c_415_60_pf = calculate_three_phase_circuit_kw(415.0, 60.0, derating_factor=0.80, power_factor=0.95)
    check(
        "SPB200 p.11: Single 3-phase 415V 60A circuit at 0.95 PF and 80% derating == 32.8 kW (65.6 kW for 2 circuits)",
        c_415_60_pf["continuous_derated_kw"] == 32.8,
        f"got {c_415_60_pf}",
    )

    try:
        calculate_three_phase_circuit_kw(0.0, 60.0)
        check("Rejects non-positive voltage in 3-phase calculator", False)
    except ValueError:
        check("Rejects non-positive voltage in 3-phase calculator", True)

    # 2. Sensible heat airflow (CFM = 3.16 * W / dT_F) & BTU/hr checks (V21 Ch 5 & V5 Ch 4)
    af_64gpu = calculate_sensible_heat_airflow_cfm(81_600.0, delta_t_celsius=20.0)
    check(
        "V21 Ch5: 81.6 kW (8x DGX H100) at 20C (36F) rise requires 7,162.7 CFM (~7,160 CFM)",
        af_64gpu["delta_t_fahrenheit"] == 36.0 and af_64gpu["required_airflow_cfm"] == 7162.7,
        f"got {af_64gpu}",
    )

    af_1node = calculate_sensible_heat_airflow_cfm(10_200.0, delta_t_celsius=15.0)
    check(
        "V5 Ch4: Single 10.2 kW DGX H100 generates 34,804 BTU/hr (~34,800 BTU/hr) and >1,000 CFM",
        af_1node["heat_load_btu_hr"] == 34804 and af_1node["required_airflow_cfm"] > 1000.0,
        f"got {af_1node}",
    )

    try:
        calculate_sensible_heat_airflow_cfm(-100.0)
        check("Rejects negative heat load in airflow calculator", False)
    except ValueError:
        check("Rejects negative heat load in airflow calculator", True)

    # 3. 64-GPU Cluster Monthly Energy (kWh) & Cost Schedule checks (V21 Ch 5 Part 1.2)
    eb = calculate_monthly_cluster_energy_and_cost()
    check(
        "V21 Ch5: 16h train (52,800 kWh) + 4h idle (2,400 kWh) + 4h maint (4,800 kWh) == 60,000 kWh/month",
        eb["train_kwh_month"] == 52800.0
        and eb["idle_kwh_month"] == 2400.0
        and eb["maint_kwh_month"] == 4800.0
        and eb["total_kwh_month"] == 60000.0,
        f"got {eb}",
    )
    check(
        "V21 Ch5: 60,000 kWh/month at $0.12/kWh == $7,200/month and $86,400/year",
        eb["monthly_cost_usd"] == 7200.0 and eb["annual_cost_usd"] == 86400.0,
        f"got {eb}",
    )

    try:
        calculate_monthly_cluster_energy_and_cost(train_hours_per_day=20.0, idle_hours_per_day=4.0, maint_hours_per_day=4.0)
        check("Rejects daily schedule not summing to 24.0 hours", False)
    except ValueError:
        check("Rejects daily schedule not summing to 24.0 hours", True)

    # 4. Optical Transceiver Power & PUE checks (AIDC Ch 5)
    check(
        "AIDC Ch5: Optical transceiver max power jumps from 3.2W (QSFP28) to 12W (QSFP56-DD) and 15W (OSFP)",
        OPTICS_POWER_WATTS["QSFP28"] == 3.2
        and OPTICS_POWER_WATTS["QSFP56-DD"] == 12.0
        and OPTICS_POWER_WATTS["OSFP"] == 15.0,
    )
    check(
        "64 OSFP transceivers on a single 64-port switch consume 64 * 15W == 960W (~1 kW) in optics alone",
        64 * OPTICS_POWER_WATTS["OSFP"] == 960.0,
    )

    # 5. Cooling Architecture Selection checks (V1 Ch 6, V5 Ch 4, V21 Ch 5, SPB200, SPGB300)
    cool_30kw = select_cooling_architecture(30.0, system_type="generic_air")
    check(
        "<=40 kW generic rack selects Forced Air Cooling with Hot/Cold Aisle Containment",
        cool_30kw["cooling_method"] == "Forced Air Cooling with Hot/Cold Aisle Containment"
        and cool_30kw["requires_cdu"] is False,
    )

    cool_b200 = select_cooling_architecture(57.2, system_type="DGX-B200")
    check(
        "SPB200 p.10: DGX B200 rack selects high-velocity air containment and marks RDHx unsuitable",
        cool_b200["requires_cdu"] is False and cool_b200["rdhx_suitable"] is False,
    )

    cool_cllc = select_cooling_architecture(50.0, system_type="generic_air", has_facility_chilled_water=False)
    check(
        "50 kW rack without facility chilled water selects Closed-Loop Liquid Cooling (CLLC)",
        "Closed-Loop Liquid Cooling" in cool_cllc["cooling_method"] and cool_cllc["requires_cdu"] is False,
    )

    cool_dlc = select_cooling_architecture(120.0, system_type="DGX-GB200-NVL72", has_facility_chilled_water=True)
    check(
        "120 kW GB200 NVL72 rack requires Direct-to-Chip Liquid Cooling (DLC) with a facility CDU",
        cool_dlc["requires_cdu"] is True and "Direct-to-Chip Liquid Cooling" in cool_dlc["cooling_method"],
    )

    cool_gb300 = select_cooling_architecture(150.0, system_type="DGX-GB300-NVL72")
    check(
        "SPGB300 p.8: 150 kW DGX GB300 NVL72 selects Hybrid DLC + Air Cooling (127.5 kW liquid / 22.5 kW air)",
        cool_gb300["requires_cdu"] is True
        and cool_gb300["estimated_liquid_capture_kw"] == 127.5
        and cool_gb300["estimated_air_rejection_kw"] == 22.5,
        f"got {cool_gb300}",
    )

    try:
        select_cooling_architecture(0.0)
        check("Rejects non-positive rack_power_kw in cooling selector", False)
    except ValueError:
        check("Rejects non-positive rack_power_kw in cooling selector", True)

    # 6. Additional V1 Ch 6 CIO Scenario & PUE checks
    cio_8node_rack_kw = round(8 * 10.2, 1)
    cio_8node_rack_lbs = 8 * 370
    check(
        "V1 Ch6 CIO Scenario: Stacking 8x DGX H100s in 1 rack reaches 81.6 kW (~85 kW w/ switches) and 2,960 lbs",
        cio_8node_rack_kw == 81.6 and cio_8node_rack_lbs == 2960,
    )
    check(
        "V21 Ch5: 81.6 kW IT load * 1.35 PUE == 110.16 kW (~110 kW) total facility power",
        round(81.6 * 1.35, 2) == 110.16,
    )
    check(
        "V21 Ch5 Month 2 forecast: 2 concurrent 64-GPU jobs (220 kW) exceed a 144 kW facility budget",
        2 * 110.0 > 144.0,
    )
    check(
        "V5 Ch4: DGX H100 3+3 PSU redundancy keeps 3 * 3.3 kW == 9.9 kW active on single-feed loss",
        round(3 * 3.3, 1) == 9.9,
    )
    check(
        "SPGB300 p.11: DGX GB300 power shelf has 6 * 5.5 kW == 33.0 kW per shelf (8 shelves/rack = 264.0 kW)",
        round(6 * 5.5, 1) == 33.0 and round(8 * 33.0, 1) == 264.0,
    )
    check(
        "AIDC Ch5: OSFP optics (15W) draw 4.69x more power per port than legacy QSFP28 optics (3.2W)",
        round(OPTICS_POWER_WATTS["OSFP"] / OPTICS_POWER_WATTS["QSFP28"], 2) == 4.69,
    )
    try:
        calculate_monthly_cluster_energy_and_cost(days_per_month=0)
        check("Rejects non-positive days_per_month", False)
    except ValueError:
        check("Rejects non-positive days_per_month", True)

    try:
        calculate_three_phase_circuit_kw(208.0, 60.0, derating_factor=1.5)
        check("Rejects derating_factor > 1.0", False)
    except ValueError:
        check("Rejects derating_factor > 1.0", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
