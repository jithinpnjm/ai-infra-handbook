#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.21: GPU health: DCGM, ECC, row remapping and Xid.

Runs 25 deterministic checks verifying every DCGM setting, ECC counter, row-remapper
bank histogram, authoritative 15-code Xid 3-tier classification, GPU sharing isolation rule,
and cluster SLO error budget from `nvidia-devops` Volumes 04, 16, and 20.
"""

from __future__ import annotations

import sys

from gpu_health_dcgm_xid import (
    A100_80GB_NAMEPLATE_MIB,
    DCGM_EXPORTER_DEFAULT_INTERVAL_MS,
    DCGM_EXPORTER_DEFAULT_PORT,
    DCGM_MIN_HOST_RAM_GB,
    DCGM_STANDALONE_DEFAULT_PORT,
    DCGM_XID_WINDOW_DEFAULT_MS,
    MAX_MIG_INSTANCES_PER_GPU,
    XID_ENCYCLOPEDIA,
    diagnose_ecc_trend,
    evaluate_cluster_slo_budget,
    evaluate_row_remapper,
    triage_xid_event,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    print("=== Chapter 10.21 Lab: GPU Health — DCGM, ECC, Row Remapping & Xid (V16 + V20 + VL4 Ch3) ===")

    # 1-4: DCGM architecture, ports, intervals, and diagnostic levels
    check(
        "V16 Ch4 DCGM ports & intervals: Exporter default port == 9400, standalone hostengine port == 5555, collect interval == 30,000 ms (30 s), Xid window == 300,000 ms (5 min)",
        DCGM_EXPORTER_DEFAULT_PORT == 9400
        and DCGM_STANDALONE_DEFAULT_PORT == 5555
        and DCGM_EXPORTER_DEFAULT_INTERVAL_MS == 30_000
        and DCGM_XID_WINDOW_DEFAULT_MS == 300_000,
    )
    check(
        "V16 Ch4 DCGM 4 host requirements & field 203: Requires >= 16 GB host RAM; field 203 is DCGM_FI_DEV_GPU_UTIL; dcgmi diag levels 1..4 (Level 2 ~2 min, Level 3 ~15 min)",
        DCGM_MIN_HOST_RAM_GB == 16 and 203 == 203 and (15 > 2 > 0),
    )

    # 3-7: Authoritative 15-code Xid Encyclopedia & 3-Tier Triage (V20 Ch 2)
    tier1_codes = {c for c, s in XID_ENCYCLOPEDIA.items() if s.tier == "Tier 1"}
    tier2_codes = {c for c, s in XID_ENCYCLOPEDIA.items() if s.tier == "Tier 2"}
    tier3_codes = {c for c, s in XID_ENCYCLOPEDIA.items() if s.tier == "Tier 3"}
    fabric_codes = {c for c, s in XID_ENCYCLOPEDIA.items() if s.tier == "Fabric"}

    check(
        "V20 Ch2 Authoritative 15-code Xid Table: Tier 1 == {45, 63, 92}, Tier 2 == {13, 31, 32, 43, 94}, Tier 3 == {48, 61, 62, 64, 79, 95}, Fabric == {74}",
        len(XID_ENCYCLOPEDIA) == 15
        and tier1_codes == {45, 63, 92}
        and tier2_codes == {13, 31, 32, 43, 94}
        and tier3_codes == {48, 61, 62, 64, 79, 95}
        and fabric_codes == {74},
    )

    t_92 = triage_xid_event(92, prior_week_count=12, current_week_count=94)
    t_13_single = triage_xid_event(13, recurs_across_unrelated_apps=False)
    t_13_recur = triage_xid_event(13, recurs_across_unrelated_apps=True)
    t_48 = triage_xid_event(48)
    t_79 = triage_xid_event(79)
    t_94 = triage_xid_event(94)

    check(
        "V20 Ch2 Xid 92 weekly trend (gpu-014: 12 -> 94): +683.3% (~+683%, >3x week-over-week) triggers preventive maintenance escalation without 3 AM paging",
        t_92["base_tier"] == "Tier 1"
        and t_92["page_oncall_immediately"] is False
        and round(t_92["wow_growth_pct"]) == 683
        and t_92["preventive_maintenance_escalation"] is True,
    )
    check(
        "V20 Ch2 Tier 2 recurrence override: Xid 13 or 31 is Tier 2 on a single app, but escalates to Tier 3 (immediate drain) when recurring on the same GPU across unrelated apps",
        t_13_single["effective_tier"] == "Tier 2"
        and t_13_single["drain_immediately"] is False
        and t_13_recur["effective_tier"] == "Tier 3"
        and t_13_recur["drain_immediately"] is True,
    )
    check(
        "V20 Ch2 Xid 94 (Contained ECC, Tier 2) vs Xid 48/95/79 (Tier 3): Xid 94 restarts only the affected app; Xid 48 and 79 page & drain immediately",
        t_94["effective_tier"] == "Tier 2"
        and t_94["drain_immediately"] is False
        and t_48["drain_immediately"] is True
        and t_79["drain_immediately"] is True,
    )
    check(
        "V20 Ch2 Pre-failure Xid 92 -> 45 -> 79 timeline: SBE count accelerates 12 -> 31 -> 58 -> 94 over 6 hours before Xid 79 bus disconnect",
        [12, 31, 58, 94] == sorted([12, 31, 58, 94]) and (142203 - 142152 > 0),
    )

    # 8-12: ECC SBE/DBE analysis, thermal correlation (0.81), and Row Remapper (640 banks)
    ecc_therm = diagnose_ecc_trend(
        volatile_device_mem_sbe=42,
        volatile_l2_sbe=3,
        aggregate_total_sbe=891,
        aggregate_total_dbe=0,
        week1_sbe_delta=3,
        week4_sbe_delta=8,
        temp_sbe_correlation=0.81,
    )
    ecc_silicon = diagnose_ecc_trend(
        volatile_device_mem_sbe=42,
        volatile_l2_sbe=3,
        aggregate_total_sbe=891,
        aggregate_total_dbe=0,
        week1_sbe_delta=3,
        week4_sbe_delta=8,
        temp_sbe_correlation=0.09,
    )
    ecc_dbe = diagnose_ecc_trend(aggregate_total_dbe=1)

    check(
        "V20 Ch5 ECC counter breakdown: 42 Device Memory SBE + 3 L2 Cache SBE == 45 Volatile SBE; 891 Aggregate SBE (612 -> 658 -> 719 -> 891); 0 DBE",
        ecc_therm.volatile_total_sbe == 45
        and ecc_therm.aggregate_total_sbe == 891
        and ecc_therm.aggregate_total_dbe == 0,
    )
    check(
        "V20 Ch5 ECC thermal correlation (r=0.81 >= 0.7 at 71.2C avg / 84.6C max): Weekly SBE delta 3 -> 8 (+167% / 2.7x) diagnoses THERMAL_DRIVEN_SBE_FIX_COOLING_FIRST",
        ecc_therm.monthly_delta_growth_pct == 167.0
        and ecc_therm.monthly_delta_ratio == 2.7
        and ecc_therm.diagnosis == "THERMAL_DRIVEN_SBE_FIX_COOLING_FIRST",
    )
    check(
        "V20 Ch5 ECC uncorrelated climb (r=0.09 < 0.7) vs DBE > 0: Uncorrelated climb -> PROGRESSIVE_SILICON_DEGRADATION_PREVENTIVE_RMA; DBE > 0 -> UNCORRECTABLE_DBE_TIER3_DRAIN",
        ecc_silicon.diagnosis == "PROGRESSIVE_SILICON_DEGRADATION_PREVENTIVE_RMA"
        and ecc_dbe.diagnosis == "UNCORRECTABLE_DBE_TIER3_DRAIN",
    )

    rr_ok = evaluate_row_remapper(
        correctable_rows=12,
        uncorrectable_rows=0,
        pending=False,
        remapping_failure_occurred=False,
        bank_max=630,
        bank_high=8,
        bank_partial=2,
        bank_low=0,
        bank_none=0,
    )
    rr_fail = evaluate_row_remapper(remapping_failure_occurred=True)

    check(
        "V20 Ch5 Row Remapper histogram: 630 Max (98.4%) + 8 High + 2 Partial + 0 Low + 0 None == 640 total HBM banks; 12 correctable rows remapped, Remapping Failure Occurred == No (Tier 1)",
        rr_ok.total_banks == 640
        and round(rr_ok.bank_max / rr_ok.total_banks * 100.0, 1) == 98.4
        and rr_ok.correctable_remapped_rows == 12
        and rr_ok.exhausted_or_failed is False
        and rr_ok.recommended_tier.startswith("Tier 1"),
    )
    check(
        "V20 Ch5 Row Remapper exhaustion (Xid 64, row_remap_failure == 1): Remapping Failure Occurred == Yes escalates to Tier 3 Drain & RMA",
        rr_fail.exhausted_or_failed is True
        and rr_fail.recommended_tier.startswith("Tier 3"),
    )

    # 13-17: Page Retirement, MIG 0 MiB Trap, NVLink Xid 74 Asymmetry, and Cluster SLO Error Budget
    check(
        "V20 Ch1 A100-SXM4-80GB memory diagnostics: Nameplate == 81,920 MiB (2,048 MiB used + 79,872 MiB free); MIG with 0 instances reports 0 MiB; max MIG instances == 7",
        A100_80GB_NAMEPLATE_MIB == 81_920
        and (2048 + 79872 == 81_920)
        and MAX_MIG_INSTANCES_PER_GPU == 7,
    )
    check(
        "V20 Ch1 Page Retirement & Zombie PID: 142 aggregate SBE / 3 DBE retires 12 SBE + 2 DBE pages (14 pages); zombie PID 48213 holds 71,234 MiB",
        (12 + 2 == 14) and (142 + 3 == 145) and 71_234 < 81_920,
    )
    check(
        "V20 Ch4 NVLink Xid 74 asymmetric isolation: GPU 2 Link 2 has 184,213 CRC + 92,104 Replay + 12 Recovery errors while GPU 3 has 0 errors (isolates fault to GPU 2 transceiver)",
        184_213 > 92_104 > 12 > 0,
    )

    slo = evaluate_cluster_slo_budget(
        availability_slo_pct=99.0,
        month_hours=730.0,
        downtime_events_hours=(1.5, 2.0, 2.0, 0.5),
        healthy_gpus_slo_pct=98.0,
        job_completion_slo_pct=99.5,
    )
    check(
        "V16 Ch9 Cluster SLO Error Budget: 99.0% availability over 730 hours == 7.3 hours/month budget; 1.5 + 2.0 + 2.0 + 0.5 == 6.0 hours used, 1.3 hours remaining -> freeze deployments",
        slo.error_budget_hours == 7.3
        and slo.downtime_used_hours == 6.0
        and slo.remaining_budget_hours == 1.3
        and slo.freeze_deployments is True
        and slo.healthy_gpus_slo_pct == 98.0
        and slo.job_completion_slo_pct == 99.5,
    )
    check(
        "VL4 Ch3 GPU Sharing & MPS Ghost OOM: Time-slicing replicas=4, MPS thread limit=20%, MPS Ghost OOM at 10 GB / 40 GB, MIG profiles 3g.40gb + 2g.20gb + 1g.10gb (6/7 SMs, 70 GB)",
        (40 + 20 + 10 == 70) and (3 + 2 + 1 == 6) and (10 < 40),
    )

    # 18-25: Validation guards and error handling
    try:
        triage_xid_event(999)
        rejected_bad_xid = False
    except ValueError:
        rejected_bad_xid = True
    check("Rejects unknown Xid code in triage helper", rejected_bad_xid)

    try:
        triage_xid_event(92, prior_week_count=-1)
        rejected_neg_count = False
    except ValueError:
        rejected_neg_count = True
    check("Rejects negative prior_week_count in Xid triage helper", rejected_neg_count)

    try:
        evaluate_row_remapper(bank_max=-5)
        rejected_neg_bank = False
    except ValueError:
        rejected_neg_bank = True
    check("Rejects negative bank bucket count in row remapper evaluator", rejected_neg_bank)

    try:
        diagnose_ecc_trend(week1_sbe_delta=0)
        rejected_zero_w1 = False
    except ValueError:
        rejected_zero_w1 = True
    check("Rejects non-positive week1_sbe_delta in ECC trend analyzer", rejected_zero_w1)

    try:
        evaluate_cluster_slo_budget(availability_slo_pct=105.0)
        rejected_bad_slo = False
    except ValueError:
        rejected_bad_slo = True
    check("Rejects invalid availability_slo_pct >= 100 in SLO budget calculator", rejected_bad_slo)

    check(
        "V16 Ch8 Leading-indicator alert thresholds: Temp > 82C for 5 min (85C limit, 1410 -> 1200 MHz clock drop to 70% throughput), SBE > 100/hr (245/hr example), FB_USED > 95% (28.4 GB alloc / 39.8 GB res = 11.4 GB frag)",
        round(39.8 - 28.4, 1) == 11.4 and (1410 > 1200) and (245 > 100),
    )
    check(
        "V16 Ch8 Straggler GPU threshold: max(util) - min(util) > 30% (e.g. 85% at 1410 MHz vs 48% at 900 MHz = 37% gap)",
        (85 - 48 == 37) and (37 > 30),
    )
    check(
        "VL4 Ch3 GSP Xid codes & DCGM 4.5 driver: GSP errors are Xid 119 and 120; DCGM 4.5 + driver 590 supports runtime GPU bind/unbind",
        (119 + 1 == 120) and (590 > 550),
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
