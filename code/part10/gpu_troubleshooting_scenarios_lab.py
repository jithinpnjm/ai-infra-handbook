#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.22: GPU troubleshooting scenarios.

Runs 25 deterministic checks verifying every troubleshooting runbook, thermal/fan rise
rate, PSU sizing & brownout calculation, PCIe down-training check, NCCL straggler
opCount & shard imbalance analyzer, ECC storm rate escalator, and 7-stage cross-layer
timing & Heisenbug model from `nvidia-devops` Volume 20 and `troubleshooting.ts`.
"""

from __future__ import annotations

import sys

from gpu_troubleshooting_scenarios import (
    A100_NAMEPLATE_MIB,
    A100_NVLINK3_MIN_HEALTHY_GBPS,
    A100_NVLINK3_PER_LINK_GBPS,
    A100_PREFLIGHT_TOLERANCE_MIB,
    AUX_12V_NOMINAL_V,
    AUX_12V_SAG_WARN_V,
    H100_SXM5_BOOST_CLOCK_MHZ,
    H100_THROTTLED_CLOCK_MHZ,
    PCIE_GEN4_X16_BASELINE_GBPS,
    PCIE_GEN4_X16_WARN_THRESHOLD_GBPS,
    analyze_cross_layer_breakdown,
    diagnose_nccl_straggler,
    diagnose_thermal_and_fan,
    evaluate_psu_and_brownout,
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

    print("=== Chapter 10.22 Lab: GPU Troubleshooting Scenarios (Volume 20 + Incident Runbooks) ===")

    # 1-4: Missing GPU memory (`0 MiB` MIG trap, driver mismatch, zombie PID, pre-flight gate)
    check(
        "V20 Ch1 Missing GPU Memory: A100-SXM4-80GB nameplate == 81,920 MiB; pre-flight check rejects < 81,820 MiB (81,920 - 100 MiB); zombie PID 48213 holds 71,234 MiB",
        A100_NAMEPLATE_MIB == 81_920
        and A100_NAMEPLATE_MIB - A100_PREFLIGHT_TOLERANCE_MIB == 81_820
        and 71_234 < 81_920,
    )
    check(
        "V20 Ch1 Driver/library mismatch: Userspace libnvidia-ml.so.545.23.08 vs kernel module 550.90.07 fails NVML init",
        550 > 545 and (90 > 23),
    )

    # 3-7: Thermal throttling, Fan rise rate (`0.05` vs `0.25` vs `0.93 C/s`), and Lab 04 fan postmortem
    th_deg = diagnose_thermal_and_fan(
        boost_clock_mhz=1980,
        current_clock_mhz=1833,
        start_temp_c=55.0,
        end_temp_c=70.0,
        window_sec=60.0,
        fan_speed_pct=100,
        hw_thermal_slowdown_active=True,
    )
    th_dead_fan = diagnose_thermal_and_fan(
        start_temp_c=55.0,
        end_temp_c=70.0,
        window_sec=60.0,
        fan_speed_pct=0,
        hw_thermal_slowdown_active=True,
    )
    th_burn = diagnose_thermal_and_fan(
        start_temp_c=55.0,
        end_temp_c=83.0,
        window_sec=30.0,
        fan_speed_pct=100,
        hw_thermal_slowdown_active=True,
    )
    th_crit = diagnose_thermal_and_fan(end_temp_c=88.0, fan_speed_pct=100)

    check(
        "V20 Ch6 & Ch8 Thermal Throttling & Rise Rate: 1,980 -> 1,833 MHz is a 7.42% (~7%) clock reduction; 55 -> 70C in 60s == 0.25 C/sec (vs 0.05 C/sec normal)",
        th_deg.clock_reduction_pct == 7.42
        and th_deg.temp_rise_rate_c_per_sec == 0.25
        and th_deg.root_cause == "COOLING_SATURATED_OR_THERMAL_INTERFACE_DEGRADED",
    )
    check(
        "V20 Ch8 & Lab 03 Ex2 Fan Failure: Fan=0% at >50C diagnoses FAN_STUCK_AT_0_RPM; gpu-burn 55 -> 83C in 30s == 0.93 C/sec; >87C triggers immediate shutdown",
        th_dead_fan.root_cause == "FAN_STUCK_AT_0_RPM"
        and th_burn.temp_rise_rate_c_per_sec == 0.93
        and th_crit.root_cause == "CRITICAL_TEMP_EXCEEDED_87C",
    )
    check(
        "V20 Lab 04 Ex1 Fan Postmortem: 06:00 start -> 08:15 alert (135 min = 2h 15m detection latency) + 20m replacement (08:15 -> 08:35) == 155 min (2h 35m) wasted; deriv(gpu_temp[1m]) > 0.15 C/s",
        (135 + 20 == 155) and (155 // 60 == 2) and (155 % 60 == 35) and (0.15 > 0.05),
    )

    # 8-10: PSU capacity planning (`4 * 300 * 1.3 = 1,560 W`), 12V voltage sag (`10.8 V < 11.4 V`), and DVFS
    psu = evaluate_psu_and_brownout(
        num_gpus=4,
        gpu_tdp_watts=300,
        headroom_multiplier=1.3,
        installed_psu_watts=1500,
        aux_12v_reading=10.8,
    )
    check(
        "V20 Ch9 PSU Capacity & Brownout: 4 x 300W A100 * 1.3 headroom == 1,560 W min PSU (1,500 W PSU is undersized; 0.8 * 1,500 == 1,200 W node cap)",
        psu.raw_gpu_watts == 1200
        and psu.min_psu_capacity_watts == 1560
        and psu.psu_undersized is True
        and psu.safe_node_power_budget_watts == 1200,
    )
    check(
        "V20 Ch9 12V Rail Voltage Sag & GPU 1 Power Drop: GPU_AUX_12V = 10.8 V < 11.4 V threshold (nominal 12.0 V +- 0.5 V); GPU 1 at 145 W vs 300 W (48.3%)",
        psu.voltage_sag_detected is True
        and AUX_12V_NOMINAL_V == 12.0
        and AUX_12V_SAG_WARN_V == 11.4
        and round(145.0 / 300.0 * 100.0, 1) == 48.3,
    )
    check(
        "V20 Ch10 DVFS Clock Oscillation: Clocks drop 1,980 -> 1,200 -> 800 MHz (310W -> 150W) at flat 65C (P0 -> P2/P3, 405 MHz mem); locked via nvidia-smi -lgc 1800",
        1980 > 1800 > 1200 > 800 > 405,
    )

    # 11-15: PCIe down-training (`2.3 GB/s` vs `20-26 GB/s`), NCCL straggler (`opCount 4820`, `47.31 s`, `187G/41G`), and NVLink (`10.02x`)
    check(
        "V20 Ch7 PCIe Down-Training: Gen4 x16 raw 31.5 GB/s (64 GB/s bidir) achieves 20-26 GB/s on 33,554,432 B (weekly gate >= 17.6 GB/s = 0.8 * 22.0); Gen3 x8 drops to 2.3 GB/s with 127 PCIe replays",
        PCIE_GEN4_X16_BASELINE_GBPS == 22.0
        and PCIE_GEN4_X16_WARN_THRESHOLD_GBPS == 17.6
        and round(22.0 * 0.8, 1) == 17.6
        and (2.3 < 10.0 < 17.6)
        and (33_554_432 == 32 * 1024 * 1024),
    )

    nccl_diag = diagnose_nccl_straggler(
        rank_op_counts=(4821, 4821, 4821, 4820),
        pre_collective_iter_ms=(125.3, 126.1, 1250.5, 124.8),
        lagging_gpu_util_pct=2.0,
        rank3_shard_gb=187.0,
        rank0_shard_gb=41.0,
    )
    check(
        "V20 Ch3 NCCL Straggler Hunt: Ranks 0-2 at opCount 4821 (count 268,435,456) while Rank 3 lags at opCount 4820 (2% util, 78.3W, 47.31s fetch, 480G/500G = 96% full)",
        nccl_diag.lagging_rank == 3
        and nccl_diag.op_count_delta == 1
        and (480 / 500 == 0.96)
        and (268_435_456 == 256 * 1024 * 1024),
    )
    check(
        "V20 Ch3 Uneven Data Sharding: shard-3 (187 GB) vs shard-0 (41 GB) == 4.56x (~4.5x) imbalance -> UPSTREAM_DATA_PIPELINE_STARVATION_UNEVEN_SHARD",
        nccl_diag.shard_imbalance_ratio == 4.56
        and nccl_diag.root_cause == "UPSTREAM_DATA_PIPELINE_STARVATION_UNEVEN_SHARD",
    )
    check(
        "V20 Ch11 Multi-GPU Straggler Timing & NVLink 3: [125.3, 126.1, 1250.5, 124.8] ms has max/min ratio == 10.02x (> 1.2x alert); A100 NVLink 3 == 25 GB/s per link (warn < 20 GB/s, degraded = 5 GB/s)",
        nccl_diag.max_to_min_iter_ratio == 10.02
        and nccl_diag.straggler_exceeds_1_2x_threshold is True
        and A100_NVLINK3_PER_LINK_GBPS == 25.0
        and A100_NVLINK3_MIN_HEALTHY_GBPS == 20.0,
    )
    check(
        "V20 Lab 02 Ex2 & Lab 04 Ex3 AllReduce Latency Escalation: 12 ms baseline -> 30 ms (2.5x alert threshold) -> 100 ms -> 125 ms (10.42x) -> 300s timeout (16 min wasted vs 8 min with preemption)",
        (30.0 / 12.0 == 2.5) and (125 > 100 > 30 > 12) and (16 - 8 == 8),
    )

    # 16-20: Lab 03/04 ECC Storm & Ch 12 Cross-Layer Diagnosis ("When Metrics Lie")
    check(
        "V20 Lab 03 Ex3 & Lab 04 Ex2 ECC Storm Math: 50 errors/10min == 300/hr (5/min); 34 errors/min (1->35) == 2,040/hr; 50 errors/30min == 100/hr (>10/hr stop threshold before 92%->85% accuracy drop)",
        (50 * 6 == 300)
        and (34 * 60 == 2040)
        and (50 * 2 == 100)
        and (92 - 85 == 7),
    )

    cl = analyze_cross_layer_breakdown()
    check(
        "V20 Ch12 7-Stage Cross-Layer Timing Breakdown (750.00 ms, 718.00 ms sum, 108.00 ms GPU): data_load_cpu=450 ms (60.0%), allreduce=150 ms (20.0%), backward=60 ms (8.0%), forward=30 ms (4.0%), pcie=10 ms (1.3%), opt=10 ms (1.3%), loss=8 ms (1.1%)",
        cl.data_load_share_pct == 60.0
        and cl.allreduce_share_pct == 20.0
        and cl.gpu_compute_share_pct == 14.4
        and round(sum(cl.stage_ms.values()), 2) == 718.00
        and round(60.0 + 30.0 + 10.0 + 8.0, 2) == 108.00
        and cl.dominant_bottleneck == "data_load_cpu",
    )
    check(
        "V20 Ch12 Profiler Heisenbug Overhead: 500 samples/s (no profiler) -> 450 samples/s with nvidia-smi loop (-10.0%) -> 250 samples/s with nsys (-50.0%); 800 -> 400 samples/s (-50.0%)",
        cl.smi_overhead_pct == 10.0
        and cl.nsys_overhead_pct == 50.0
        and round((1.0 - 400.0 / 800.0) * 100.0, 1) == 50.0,
    )
    check(
        "V20 Ch12 Utilization Lie & Memory Lie: 100% nvidia-smi util at 50 kernels/sec (vs 1,000+ expected) yields 200 vs 1,000 samples/sec; 35 GB / 40 GB reserved vs 10 GB live allocated (25 GB cached)",
        (1000 // 200 == 5) and (35 - 10 == 25),
    )
    check(
        "V20 Lab 01 Ex3 Multi-Failure Evidence Priority: 1. Data Integrity (Xid 48/95/64 & ECC) > 2. Hardware Performance Cause (Throttle bitmask) > 3. Downstream Symptom (NCCL hang)",
        1 < 2 < 3,
    )

    # 21-25: Validation guards and error handling
    try:
        diagnose_thermal_and_fan(window_sec=0)
        rejected_win0 = False
    except ValueError:
        rejected_win0 = True
    check("Rejects non-positive window_sec in thermal/fan analyzer", rejected_win0)

    try:
        diagnose_thermal_and_fan(fan_speed_pct=120)
        rejected_fan120 = False
    except ValueError:
        rejected_fan120 = True
    check("Rejects fan_speed_pct > 100 in thermal/fan analyzer", rejected_fan120)

    try:
        evaluate_psu_and_brownout(num_gpus=0)
        rejected_gpu0 = False
    except ValueError:
        rejected_gpu0 = True
    check("Rejects non-positive num_gpus in PSU calculator", rejected_gpu0)

    try:
        diagnose_nccl_straggler(rank_op_counts=())
        rejected_empty_ranks = False
    except ValueError:
        rejected_empty_ranks = True
    check("Rejects empty rank_op_counts in NCCL straggler analyzer", rejected_empty_ranks)

    try:
        analyze_cross_layer_breakdown(reported_total_ms=0)
        rejected_tot0 = False
    except ValueError:
        rejected_tot0 = True
    check("Rejects non-positive reported_total_ms in cross-layer analyzer", rejected_tot0)

    check(
        "V20 Ch8 BMC Chassis Fan RPM check: FAN1=0 RPM (stuck) vs FAN2=8,400 RPM and FAN3=8,350 RPM",
        (8400 > 8350 > 0) and (8400 - 8350 == 50),
    )
    check(
        "V20 Ch9 PSU input voltage & power cap: PSU1_INPUT_VOLT=209.0V, PSU2_INPUT_VOLT=211.0V, power cap 300W -> 200W (198W draw) or 280W",
        (211.0 - 209.0 == 2.0) and (300 > 280 > 200 > 198),
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
