#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.8: Operating GPU Nodes: nvidia-smi, Topology, Clocks, and Throttling."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_node_ops import (
    GPUOpsError,
    analyze_pytorch_memory_state,
    audit_gpu_node_operational_health,
    classify_temperature_headroom,
    decode_throttle_reasons_bitmask,
    evaluate_utilization_regime,
    classify_clock_stability,
    classify_xid,
    diagnose_busy_but_slow,
    minimum_psu_watts,
    triage_slowdown,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 10.8 Lab: Operating GPU Nodes (nvidia-smi, Clocks & Throttling) ===")

    # 1. Throttle Reason Bitmask Decoding (V16 Ch 3 & V2 Lab 02)
    reasons_none = decode_throttle_reasons_bitmask(0x0000000000000000)
    reasons_idle = decode_throttle_reasons_bitmask(0x0000000000000001)
    reasons_thermal = decode_throttle_reasons_bitmask(0x0000000000000020)
    reasons_hw_slowdown = decode_throttle_reasons_bitmask(0x0000000000000008)
    reasons_multi = decode_throttle_reasons_bitmask(0x0000000000000024)  # SW_POWER_CAP (0x4) + SW_THERMAL (0x20)

    check(
        "Bitmask 0x0 decodes to ['NOT_THROTTLED']",
        reasons_none == ["NOT_THROTTLED"],
    )
    check(
        "Bitmask 0x1 decodes to ['GPU_IDLE']",
        reasons_idle == ["GPU_IDLE"],
    )
    check(
        "Bitmask 0x20 decodes to ['SW_THERMAL_SLOWDOWN']",
        reasons_thermal == ["SW_THERMAL_SLOWDOWN"],
    )
    check(
        "Bitmask 0x8 decodes to ['HW_SLOWDOWN']",
        reasons_hw_slowdown == ["HW_SLOWDOWN"],
    )
    check(
        "Bitmask 0x24 decodes to combined SW_POWER_CAP and SW_THERMAL_SLOWDOWN",
        "SW_POWER_CAP" in reasons_multi and "SW_THERMAL_SLOWDOWN" in reasons_multi,
    )

    # 2. Utilization vs Memory Bandwidth Regimes (V16 Ch 1 & Ch 3)
    regime_mem = evaluate_utilization_regime(sm_util_pct=85.0, mem_bw_util_pct=82.0, samples_per_sec=2048.0)
    check(
        "V16 Ch3: 85% SM util + 82% mem BW util identifies healthy MEMORY_BOUND execution",
        regime_mem["regime"] == "MEMORY_BOUND",
    )

    regime_compute = evaluate_utilization_regime(sm_util_pct=85.0, mem_bw_util_pct=15.0, samples_per_sec=2000.0)
    check(
        "V16 Ch3: 85% SM util + 15% mem BW util with 2000 samples/sec identifies COMPUTE_BOUND execution",
        regime_compute["regime"] == "COMPUTE_BOUND",
    )

    regime_spin = evaluate_utilization_regime(sm_util_pct=85.0, mem_bw_util_pct=2.0, samples_per_sec=0.0)
    check(
        "V16 Ch1 & Ch3: 85% SM util + 2% mem BW util with 0 samples/sec detects SPINNING_OR_STALLED kernel bug",
        regime_spin["regime"] == "SPINNING_OR_STALLED",
    )

    regime_idle = evaluate_utilization_regime(sm_util_pct=4.0, mem_bw_util_pct=1.0)
    check(
        "Low SM util (<10%) evaluates to IDLE",
        regime_idle["regime"] == "IDLE",
    )

    # 3. PyTorch Memory Allocator vs Driver VRAM (V16 Ch 3)
    pyt_mem = analyze_pytorch_memory_state(total_vram_gb=40.0, allocated_gb=28.4, reserved_gb=30.2)
    check(
        "V16 Ch3: 28.4 GB allocated of 30.2 GB reserved yields 1.8 GB reusable cache and 9.8 GB free from driver",
        pyt_mem["reusable_cache_gb"] == 1.8
        and pyt_mem["free_from_driver_gb"] == 9.8
        and pyt_mem["true_available_gb"] == 11.6,
    )
    check(
        "V16 Ch3: Reserved fraction is 75.5% and active usage ratio is 94.0%",
        pyt_mem["reserved_fraction_pct"] == 75.5
        and pyt_mem["active_usage_pct"] == 94.0
        and pyt_mem["is_oom_imminent"] is False,
    )

    pyt_oom = analyze_pytorch_memory_state(total_vram_gb=80.0, allocated_gb=79.5, reserved_gb=79.8)
    check(
        "Flags is_oom_imminent when total free headroom is less than 1.0 GB",
        pyt_oom["is_oom_imminent"] is True,
    )

    # 4. Temperature Headroom Bands (V16 Ch 3)
    temp_healthy = classify_temperature_headroom(55.0)
    temp_normal = classify_temperature_headroom(70.0)
    temp_caution = classify_temperature_headroom(80.0)
    temp_threshold = classify_temperature_headroom(84.0)
    temp_crit = classify_temperature_headroom(89.0)

    check(
        "V16 Ch3: 55C is HEALTHY (30C headroom) and 70C is NORMAL (15C headroom)",
        temp_healthy["band"] == "HEALTHY"
        and temp_healthy["headroom_to_limit_c"] == 30.0
        and temp_normal["band"] == "NORMAL",
    )
    check(
        "V16 Ch3: 80C is CAUTION (5C headroom), 84C is THROTTLE_THRESHOLD, and 89C is CRITICAL_THROTTLING",
        temp_caution["band"] == "CAUTION"
        and temp_threshold["band"] == "THROTTLE_THRESHOLD"
        and temp_crit["band"] == "CRITICAL_THROTTLING"
        and temp_crit["headroom_to_limit_c"] == 0.0,
    )

    # 5. Node Operational Health Auditing (V2 Lab 02 & V16 Ch 1-3)
    healthy_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=True,
        temp_celsius=68.0,
        throttle_bitmask=0x0,
        power_draw_watts=350.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=1800.0,
        max_sm_clock_mhz=1980.0,
    )
    check(
        "Healthy node with persistence mode enabled, 68C temp, and 1800 MHz clocks passes audit",
        healthy_audit["healthy"] is True and len(healthy_audit["issues"]) == 0,
    )

    pm_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=False,
        temp_celsius=65.0,
        throttle_bitmask=0x0,
        power_draw_watts=200.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=1800.0,
        max_sm_clock_mhz=1980.0,
    )
    check(
        "V2 Lab 02 Step 2: Flags disabled Persistence Mode (start-up delay per job launch)",
        pm_audit["healthy"] is False
        and any("Persistence Mode is DISABLED" in issue for issue in pm_audit["issues"]),
    )

    thermal_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=True,
        temp_celsius=87.0,
        throttle_bitmask=0x20,  # SW_THERMAL_SLOWDOWN
        power_draw_watts=450.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=1200.0,
        max_sm_clock_mhz=1980.0,
    )
    check(
        "V16 Ch3: Detects 87C temperature and SW_THERMAL_SLOWDOWN bitmask with reduced clocks",
        thermal_audit["healthy"] is False
        and any("SW_THERMAL_SLOWDOWN" in issue for issue in thermal_audit["issues"]),
    )

    power_brake_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=True,
        temp_celsius=72.0,
        throttle_bitmask=0x80,  # HW_POWER_BRAKE_SLOWDOWN (NVML header value; not in corpus)
        power_draw_watts=300.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=900.0,
        max_sm_clock_mhz=1980.0,
    )
    check(
        "Detects external HW_POWER_BRAKE_SLOWDOWN (e.g. facility power brake or PSU failure)",
        power_brake_audit["healthy"] is False
        and any("HW_POWER_BRAKE_SLOWDOWN" in issue for issue in power_brake_audit["issues"]),
    )

    pwr_cap_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=True,
        temp_celsius=74.0,
        throttle_bitmask=0x04,  # SW_POWER_CAP
        power_draw_watts=698.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=1550.0,
        max_sm_clock_mhz=1980.0,
    )
    check(
        "V2 Lab 02: Detects active SW_POWER_CAP when drawing 698W at 700W ceiling",
        pwr_cap_audit["healthy"] is False
        and any("Power capping active" in issue for issue in pwr_cap_audit["issues"]),
    )

    ecc_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=True,
        temp_celsius=65.0,
        throttle_bitmask=0x0,
        power_draw_watts=350.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=1800.0,
        max_sm_clock_mhz=1980.0,
        ecc_uncorrected_volatile=2,
    )
    check(
        "V16 Ch1: Detects uncorrected volatile ECC memory errors and recommends node cordoning",
        ecc_audit["healthy"] is False
        and any("uncorrected volatile ECC" in issue for issue in ecc_audit["issues"]),
    )

    locked_clocks_audit = audit_gpu_node_operational_health(
        persistence_mode_enabled=True,
        temp_celsius=68.0,
        throttle_bitmask=0x0,
        power_draw_watts=400.0,
        power_limit_watts=700.0,
        current_sm_clock_mhz=1200.0,
        max_sm_clock_mhz=1980.0,
        locked_clocks_range=(1500.0, 1500.0),
    )
    check(
        "V2 Lab 02 Step 7: Flags clock frequency deviating from configured locked range [1500, 1500] MHz",
        locked_clocks_audit["healthy"] is False
        and any("outside configured locked range" in issue for issue in locked_clocks_audit["issues"]),
    )

    # 6. Error Handling
    try:
        decode_throttle_reasons_bitmask(-1)
        check("Rejects negative throttle bitmask", False)
    except GPUOpsError:
        check("Rejects negative throttle bitmask", True)

    try:
        evaluate_utilization_regime(sm_util_pct=105.0, mem_bw_util_pct=50.0)
        check("Rejects sm_util_pct > 100", False)
    except GPUOpsError:
        check("Rejects sm_util_pct > 100", True)

    try:
        analyze_pytorch_memory_state(total_vram_gb=40.0, allocated_gb=45.0, reserved_gb=30.0)
        check("Rejects allocated_gb > reserved_gb", False)
    except GPUOpsError:
        check("Rejects allocated_gb > reserved_gb", True)

    try:
        classify_temperature_headroom(-10.0)
        check("Rejects negative temperature", False)
    except GPUOpsError:
        check("Rejects negative temperature", True)

    # 7. Volume 20 / Volume 19 field-triage rules (added after review)
    x79 = classify_xid(79); x92 = classify_xid(92); x45 = classify_xid(45); x13 = classify_xid(13)
    check("V20 Ch2: Xid 79 (fell off the bus) is Tier 3 and says stop scheduling", x79["tier"] == 3 and "stop scheduling" in x79["action"])
    check("V20 Ch2: Xid 92 and 45 are Tier 1 (informational / self-healing)", x92["tier"] == 1 and x45["tier"] == 1)
    check("V20 Ch2: Xid 13 is Tier 2 but becomes Tier 3 when it recurs on one GPU across unrelated apps",
          x13["tier"] == 2 and classify_xid(13, True)["tier"] == 3)
    check("V20 Ch2: Xid 94 (contained ECC) is Tier 2 and Xid 95 (uncontained ECC) is Tier 3",
          classify_xid(94)["tier"] == 2 and classify_xid(95)["tier"] == 3)
    check("V20 Ch2: Xid 74 (NVLink) has no fixed tier and an unknown code is not guessed",
          classify_xid(74)["tier"] == 0 and classify_xid(999)["tier"] is None)
    t1 = triage_slowdown(0x20, 85.0, 700.0, 700.0, True)
    check("V20 Ch6: SW thermal slowdown reason at 85C triages as thermal", t1["cause"] == "thermal")
    check("V20 Ch10: bare HW_SLOWDOWN (0x08) is reported as thermal-or-power, not guessed as one of them",
          triage_slowdown(0x08, 70.0, 700.0, 700.0, True)["cause"] == "hardware_slowdown_thermal_or_power")
    t2 = triage_slowdown(0x04, 70.0, 200.0, 300.0, True)
    check("V20 Ch9: SW power cap with limit 200W below default 300W triages as power_cap and notes who set the limit",
          t2["cause"] == "power_cap" and any("below the default" in n for n in t2["notes"]))
    t3 = triage_slowdown(0x80, 70.0, 700.0, 700.0, True)
    check("V20 Ch9: HW power brake reason triages as power_brake", t3["cause"] == "power_brake")
    t4 = triage_slowdown(0x02, 65.0, 700.0, 700.0, True)
    check("V20 Ch10: applications-clocks setting with a cool GPU triages as a leftover operator clock lock",
          t4["cause"] == "clock_lock_set_by_operator" and any("-rgc" in n for n in t4["notes"]))
    t5 = triage_slowdown(0x0, 65.0, 700.0, 700.0, True)
    check("V20 Ch10: no throttle reason, 65C and clocks below max triages as workload_or_dvfs", t5["cause"] == "workload_or_dvfs")
    check("V20 Ch10: unique-clock test: 1 and 3 values are stable, 4 is borderline, 6 is oscillating",
          classify_clock_stability(1) == "STABLE" and classify_clock_stability(3) == "STABLE"
          and classify_clock_stability(4) == "BORDERLINE" and classify_clock_stability(6) == "OSCILLATING")
    check("V20 Ch9: PSU planning rule 4 x 300W x 1.3 == 1,560W", minimum_psu_watts(4, 300.0) == 1560.0)
    check("V19 Ch4: 100% util with TENSOR_ACTIVE 5% and no throttle is a software issue; 60% means check network/dataloader",
          diagnose_busy_but_slow(5.0, False) == "SOFTWARE_ISSUE_GPU_BUSY_ON_OVERHEAD"
          and diagnose_busy_but_slow(60.0, False) == "GPU_HEALTHY_CHECK_NETWORK_OR_DATALOADER")
    check("V19 Ch4: hardware slowdown reason wins over Tensor activity", diagnose_busy_but_slow(60.0, True) == "HARDWARE_THERMAL_OR_POWER_LIMIT")
    try:
        minimum_psu_watts(0, 300.0)
        check("Rejects non-positive gpu_count in PSU rule", False)
    except GPUOpsError:
        check("Rejects non-positive gpu_count in PSU rule", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
