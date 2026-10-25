#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.7: DGX B200 SuperPOD data center design."""

from __future__ import annotations

import sys

from b200_datacenter import (
    check_b200_environmental_compliance,
    compute_b200_rack_circuit_row,
    evaluate_b200_psu_provisioning_model,
    validate_ib_cable_run,
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

    print("=== Chapter 9.7 Lab: DGX B200 SuperPOD Data Center Design ===")

    # 1. All 10 rows of the Power Provisioning Table (superpod-b200-dc p. 11)
    expected_rows = [
        # (dist_v, amps, derating, max_kw, nodes, demand_kw, stranded_kw, cfm)
        (380, 32, 0.80, 32, 2, 28.6, 3.4, 4290),
        (400, 32, 0.80, 34, 2, 28.6, 5.1, 4290),
        (415, 32, 0.80, 35, 2, 28.6, 6.4, 4290),
        (415, 60, 0.80, 66, 4, 57.2, 8.4, 8580),
        (415, 63, 0.80, 69, 4, 57.2, 11.6, 8580),
        (380, 32, 1.00, 40, 2, 28.6, 11.4, 4290),
        (400, 32, 1.00, 42, 2, 28.6, 13.5, 4290),
        (415, 32, 1.00, 44, 2, 28.6, 15.1, 4290),
        (415, 60, 1.00, 82, 4, 57.2, 24.7, 4 * 2145),
        (415, 63, 1.00, 86, 4, 57.2, 28.8, 4 * 2145),
    ]
    for v, a, d, m_kw, n, dem, str_kw, cfm in expected_rows:
        r = compute_b200_rack_circuit_row(v, a, d)
        check(
            f"SPB200 p.11 row 3-phase {v}V {a}A ({int(d*100)}%): {m_kw} kW max, {n} nodes ({dem} kW), {str_kw} kW stranded, {cfm} CFM",
            r["max_rack_capacity_kw_rounded"] == m_kw
            and r["supported_b200_systems"] == n
            and r["peak_demand_kw"] == dem
            and r["stranded_capacity_kw"] == str_kw
            and r["required_airflow_cfm"] == cfm,
            f"got {r}",
        )

    try:
        compute_b200_rack_circuit_row(0, 32, 0.80)
        check("Rejects invalid voltage in circuit calculator", False)
    except ValueError:
        check("Rejects invalid voltage in circuit calculator", True)

    # 2. Five Power Provisioning Topologies & 5-of-6 PSU Rule checks (superpod-b200-dc pp. 12-16)
    m_non_int = evaluate_b200_psu_provisioning_model("dual_source_non_interleaved")
    check(
        "SPB200 p.12: Non-interleaved dual source impacts only 50% of systems on PDU or UPS loss (Recommended)",
        m_non_int["single_pdu_failure_rack_impact_pct"] == 50
        and m_non_int["single_ups_failure_rack_impact_pct"] == 50
        and m_non_int["nvidia_recommended"] is True,
    )

    m_single = evaluate_b200_psu_provisioning_model("single_source_dual_rpdu")
    check(
        "SPB200 p.13: Single UPS source with dual rPDU loses 100% of systems on UPS failure",
        m_single["single_pdu_failure_rack_impact_pct"] == 50
        and m_single["single_ups_failure_rack_impact_pct"] == 100,
    )

    m_interleaved = evaluate_b200_psu_provisioning_model("dual_interleaved")
    check(
        "SPB200 p.14 STOP: Dual interleaved (3+3 PSUs) drops to 3/6 PSUs (<5 required) and crashes 100% of rack on PDU/UPS loss",
        m_interleaved["psus_energized_on_single_pdu_loss_node1"] == 3
        and m_interleaved["single_pdu_failure_rack_impact_pct"] == 100
        and m_interleaved["single_ups_failure_rack_impact_pct"] == 100
        and m_interleaved["stop_warning"] is True,
    )

    m_sts = evaluate_b200_psu_provisioning_model("dual_ups_with_sts")
    check(
        "SPB200 p.15 STOP: Static Transfer Switch (STS) is unvalidated by NVIDIA and flagged with STOP warning",
        m_sts["nvidia_recommended"] is False and m_sts["stop_warning"] is True,
    )

    m_6to5 = evaluate_b200_psu_provisioning_model("six_to_make_five")
    check(
        "SPB200 p.16: '6 to make 5' (6 discrete UPS/PDUs) keeps 5/6 PSUs energized (0% rack impact, N+1 HA)",
        m_6to5["psus_energized_on_single_pdu_loss_node1"] == 5
        and m_6to5["single_pdu_failure_rack_impact_pct"] == 0
        and m_6to5["single_ups_failure_rack_impact_pct"] == 0
        and m_6to5["redundancy_achieved"] == "N+1"
        and m_6to5["nvidia_recommended"] is True,
    )

    # 3. Altitude Derating, ASHRAE Class A1, MERV 13, and ISO 14644-1 Class 8 checks (pp. 4, 17)
    env_ok = check_b200_environmental_compliance(
        altitude_ft=500.0,
        inlet_temp_c=24.0,
        relative_humidity_pct=45.0,
        dew_point_c=12.0,
        merv_rating=13,
        particles_0_5um_per_m3=1_500_000,
    )
    check(
        "Sea-level 24C, 45% RH, 12C DP, MERV 13, 1.5M particles passes recommended band at 96 dB",
        env_ok["compliant"] is True
        and env_ok["in_ashrae_recommended_band"] is True
        and env_ok["estimated_acoustic_db"] == 96,
    )

    env_30c = check_b200_environmental_compliance(
        altitude_ft=2000.0,
        inlet_temp_c=29.5,
        relative_humidity_pct=70.0,
        dew_point_c=16.5,
        merv_rating=14,
        particles_0_5um_per_m3=3_000_000,
    )
    check(
        "29.5C at 2,000 ft passes ASHRAE A1 allowable envelope and increases acoustic power to 101 dB",
        env_30c["compliant"] is True
        and env_30c["in_ashrae_recommended_band"] is False
        and env_30c["estimated_acoustic_db"] == 101,
    )

    env_high_alt = check_b200_environmental_compliance(
        altitude_ft=7500.0,  # 5,000 - 10,000 ft derates max temp to 25.0C (p. 4)
        inlet_temp_c=28.0,
        relative_humidity_pct=50.0,
        dew_point_c=12.0,
        merv_rating=13,
        particles_0_5um_per_m3=1_000_000,
    )
    check(
        "SPB200 p.4: 28C inlet at 7,500 ft fails altitude derating ceiling (max 25C at 5,000-10,000 ft)",
        env_high_alt["compliant"] is False
        and env_high_alt["effective_max_temp_c"] == 25.0
        and any("inlet_temp_violation" in v for v in env_high_alt["violations"]),
        f"got {env_high_alt}",
    )

    env_merv = check_b200_environmental_compliance(
        altitude_ft=500.0,
        inlet_temp_c=22.0,
        relative_humidity_pct=45.0,
        dew_point_c=11.0,
        merv_rating=8,
        particles_0_5um_per_m3=1_000_000,
    )
    check(
        "SPB200 p.17: Flags air filter below MERV 13 (MERV 8 rejected)",
        any("filter_below_merv13" in v for v in env_merv["violations"]),
    )

    env_iso8_short = check_b200_environmental_compliance(
        altitude_ft=500.0,
        inlet_temp_c=22.0,
        relative_humidity_pct=45.0,
        dew_point_c=11.0,
        merv_rating=13,
        particles_0_5um_per_m3=4_000_000,
        particulate_excursion_minutes=10.0,  # <= 15 minutes allowed
    )
    check(
        "SPB200 p.17: Particulate excursion >3,520,000 @ 0.5um for 10 min (<=15 min) is tolerated",
        env_iso8_short["compliant"] is True,
    )

    env_iso8_long = check_b200_environmental_compliance(
        altitude_ft=500.0,
        inlet_temp_c=22.0,
        relative_humidity_pct=45.0,
        dew_point_c=11.0,
        merv_rating=13,
        particles_0_5um_per_m3=4_000_000,
        particulate_excursion_minutes=20.0,  # > 15 minutes violates ISO Class 8 rule
    )
    check(
        "SPB200 p.17: Particulate excursion >3,520,000 @ 0.5um for >15 min fails ISO 14644-1 Class 8",
        env_iso8_long["compliant"] is False
        and any("iso_class8_particulate_violation" in v for v in env_iso8_long["violations"]),
    )

    # 4. Cabling media & 90% length rule checks (superpod-b200-dc pp. 20-21)
    c_dac400_ok = validate_ib_cable_run("DAC-400G", 2.5)
    check(
        "SPB200 pp.20-21: 2.5 m 400G Passive DAC passes both 3.0 m standard max and 2.7 m (90%) design rule",
        c_dac400_ok["within_standard_max"] is True
        and c_dac400_ok["passes_90pct_best_practice"] is True,
    )

    c_dac400_warn = validate_ib_cable_run("DAC-400G", 2.9)
    check(
        "SPB200 p.21: 2.9 m 400G Passive DAC is within 3.0 m spec but fails the <90% (2.7 m) design rule",
        c_dac400_warn["within_standard_max"] is True
        and c_dac400_warn["passes_90pct_best_practice"] is False,
    )

    c_dac100_ok = validate_ib_cable_run("DAC-100G", 4.5)
    check(
        "SPB200 p.20: 100G Passive DAC max is 5.0 m (90% limit == 4.5 m)",
        c_dac100_ok["max_standard_meters"] == 5.0
        and c_dac100_ok["max_90pct_design_meters"] == 4.5
        and c_dac100_ok["passes_90pct_best_practice"] is True,
    )

    c_aoc_ok = validate_ib_cable_run("AOC", 25.0)
    c_aoc_over = validate_ib_cable_run("AOC", 28.5)
    check(
        "SPB200 p.20-21: AOC max is 30.0 m and 90% design limit is 27.0 m (25m passes, 28.5m fails 90% rule)",
        c_aoc_ok["passes_90pct_best_practice"] is True
        and c_aoc_over["within_standard_max"] is True
        and c_aoc_over["passes_90pct_best_practice"] is False,
    )

    c_aoc_exceed = validate_ib_cable_run("AOC", 32.0)
    check(
        "SPB200 p.20: 32.0 m AOC fails 30.0 m standard max",
        c_aoc_exceed["within_standard_max"] is False,
    )

    env_over_alt = check_b200_environmental_compliance(
        altitude_ft=11000.0,
        inlet_temp_c=20.0,
        relative_humidity_pct=45.0,
        dew_point_c=10.0,
        merv_rating=13,
        particles_0_5um_per_m3=1_000_000,
    )
    check(
        "SPB200 p.4: Flags altitude > 10,000 ft (3,048 m) maximum",
        any("altitude_out_of_range" in v for v in env_over_alt["violations"]),
    )

    env_bad_rh_dp = check_b200_environmental_compliance(
        altitude_ft=500.0,
        inlet_temp_c=25.0,
        relative_humidity_pct=85.0,
        dew_point_c=18.5,
        merv_rating=13,
        particles_0_5um_per_m3=1_000_000,
    )
    check(
        "SPB200 p.17: Flags relative humidity > 80% and dew point > 17.0C (62.6F)",
        any("humidity_violation" in v for v in env_bad_rh_dp["violations"])
        and any("dew_point_violation" in v for v in env_bad_rh_dp["violations"]),
    )

    try:
        evaluate_b200_psu_provisioning_model("unknown_model")
        check("Rejects unknown PSU provisioning model", False)
    except ValueError:
        check("Rejects unknown PSU provisioning model", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
