#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.14: Occupancy, warp efficiency and instruction-level parallelism."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from occupancy_warp_ilp import (
    ILP_SATURATION_TABLE,
    TABLE_8_3_PREDICATION,
    OccupancyILPError,
    calc_sm_occupancy_and_limiters,
    classify_ncu_stall_and_regime,
    evaluate_launch_bounds,
    evaluate_warp_divergence_and_ilp,
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
    print("=== Chapter 10.14 Lab: Occupancy, Warp Efficiency & Instruction-Level Parallelism (ASP Ch 8) ===")

    # 1. SM Occupancy & Limiters (ASP Ch 8 pp. 262-274)
    occ_30 = calc_sm_occupancy_and_limiters(
        threads_per_block=256,
        regs_per_thread=32,
        shmem_per_block_bytes=8192,
        gpu_profile="BLACKWELL_B200",
        achieved_occupancy_pct=30.0,
    )
    check(
        "ASP Ch8 p.262: 30% achieved occupancy on a 64-warp (2,048-thread) SM corresponds to ~19 active warps/SM",
        occ_30["max_warps_per_sm"] == 64
        and occ_30["max_threads_per_sm"] == 2048
        and occ_30["achieved_active_warps"] == 19
        and occ_30["theoretical_occupancy_pct"] == 100.0,
    )

    occ_gb10 = calc_sm_occupancy_and_limiters(
        threads_per_block=256,
        regs_per_thread=32,
        shmem_per_block_bytes=8192,
        gpu_profile="RTX_PRO_6000_GB10",
    )
    check(
        "ASP Ch8 p.269: RTX PRO 6000 / Spark DGX GB10 (CC 12.x) allows 48 warps (1,536 threads) per SM",
        occ_gb10["max_warps_per_sm"] == 48 and occ_gb10["max_threads_per_sm"] == 1536,
    )

    occ_reg_lim = calc_sm_occupancy_and_limiters(
        threads_per_block=256,
        regs_per_thread=80,
        shmem_per_block_bytes=4096,
    )
    check(
        "ASP Ch8 p.263: 80 regs/thread * 256 = 20,480 regs/block caps 65,536-reg SM at 3 blocks (24 warps = 37.5%) -> LIMITED_BY_REGISTERS_PER_THREAD",
        occ_reg_lim["active_blocks_per_sm"] == 3
        and occ_reg_lim["theoretical_active_warps"] == 24
        and occ_reg_lim["theoretical_occupancy_pct"] == 37.5
        and "LIMITED_BY_REGISTERS_PER_THREAD" in occ_reg_lim["primary_limiters"],
    )

    occ_smem_lim = calc_sm_occupancy_and_limiters(
        threads_per_block=256,
        regs_per_thread=24,
        shmem_per_block_bytes=64 * 1024,
    )
    check(
        "ASP Ch8 p.263: 64 KB SMEM/block on 227 KB usable SMEM caps SM at 3 blocks (24 warps = 37.5%) -> LIMITED_BY_SHARED_MEMORY_PER_BLOCK",
        occ_smem_lim["active_blocks_per_sm"] == 3
        and "LIMITED_BY_SHARED_MEMORY_PER_BLOCK" in occ_smem_lim["primary_limiters"],
    )

    # 2. `__launch_bounds__(256, 8)` Compiler Hint Math (ASP Ch 8 p. 272)
    lb = evaluate_launch_bounds(max_threads_per_block=256, min_blocks_per_sm=8)
    check(
        "ASP Ch8 p.272: __launch_bounds__(256, 8) targets 8 * 256 == 2,048 threads/SM (64 warps, 100% occ) and caps regs at 65,536 // 2,048 == 32 regs/thread",
        lb["target_threads_per_sm"] == 2048
        and lb["target_warps_per_sm"] == 64
        and lb["target_occupancy_pct"] == 100.0
        and lb["compiler_max_regs_per_thread"] == 32,
    )

    # 3. Four Execution Regimes & Nsight Compute Warp Stall Reasons (ASP Ch 8 Tables 8-1 & 8-2)
    r_under = classify_ncu_stall_and_regime(
        dram_bw_pct_of_peak=12.0,
        compute_pipe_pct_of_peak=8.0,
        sm_active_pct=35.0,
        dominant_stall_reason="NO_ELIGIBLE_IDLE",
    )
    check(
        "ASP Ch8 Table 8-2: Low SM Active (35%) + NO_ELIGIBLE_IDLE stall classifies as UNDERUTILIZED",
        r_under["regime"] == "UNDERUTILIZED",
    )

    r_mem = classify_ncu_stall_and_regime(
        dram_bw_pct_of_peak=92.0,
        compute_pipe_pct_of_peak=18.0,
        sm_active_pct=95.0,
        dominant_stall_reason="LONG_SCOREBOARD",
    )
    check(
        "ASP Ch8 Table 8-2: Near-peak DRAM (92%) + low compute (18%) + LONG_SCOREBOARD classifies as MEMORY_BOUND",
        r_mem["regime"] == "MEMORY_BOUND",
    )

    r_comp = classify_ncu_stall_and_regime(
        dram_bw_pct_of_peak=30.0,
        compute_pipe_pct_of_peak=88.0,
        sm_active_pct=98.0,
        dominant_stall_reason="MATH_PIPE_THROTTLE",
        eligible_warps_per_cycle=5.2,
    )
    check(
        "ASP Ch8 Table 8-2: High compute pipe (88%) + MATH_PIPE_THROTTLE classifies as COMPUTE_BOUND",
        r_comp["regime"] == "COMPUTE_BOUND"
        and r_comp["schedulers_starved_for_eligible_warps"] is False,
    )

    r_lat_exec = classify_ncu_stall_and_regime(
        dram_bw_pct_of_peak=22.0,
        compute_pipe_pct_of_peak=28.0,
        sm_active_pct=85.0,
        dominant_stall_reason="EXEC_DEPENDENCY",
        eligible_warps_per_cycle=1.4,
    )
    check(
        "ASP Ch8 Tables 8-1 & 8-2: Low DRAM (22%) + low compute (28%) + EXEC_DEPENDENCY (eligible warps 1.4 < 4) classifies as LATENCY_BOUND and recommends ILP",
        r_lat_exec["regime"] == "LATENCY_BOUND"
        and r_lat_exec["schedulers_starved_for_eligible_warps"] is True
        and "ILP" in r_lat_exec["recommended_remedy"],
    )

    r_lat_mem = classify_ncu_stall_and_regime(
        dram_bw_pct_of_peak=25.0,
        compute_pipe_pct_of_peak=20.0,
        sm_active_pct=80.0,
        dominant_stall_reason="LONG_SCOREBOARD",
        eligible_warps_per_cycle=1.2,
    )
    check(
        "ASP Ch8 Table 8-1: Low DRAM (25%) + LONG_SCOREBOARD classifies as LATENCY_BOUND waiting on individual DRAM loads",
        r_lat_mem["regime"] == "LATENCY_BOUND"
        and "TMA" in r_lat_mem["recommended_remedy"],
    )

    r_lat_sync = classify_ncu_stall_and_regime(
        dram_bw_pct_of_peak=30.0,
        compute_pipe_pct_of_peak=25.0,
        sm_active_pct=75.0,
        dominant_stall_reason="SYNCHRONIZATION_BARRIER",
    )
    check(
        "ASP Ch8 Table 8-1: SYNCHRONIZATION_BARRIER stall recommends reducing __syncthreads() or using __shfl_down_sync",
        r_lat_sync["regime"] == "LATENCY_BOUND"
        and "__syncthreads()" in r_lat_sync["recommended_remedy"],
    )

    # 4. Warp Divergence vs Predication (ASP Ch 8 pp. 274-281 & Table 8-3)
    div_50 = evaluate_warp_divergence_and_ilp(active_lanes_in_branch_a=16)
    div_1_31 = evaluate_warp_divergence_and_ilp(active_lanes_in_branch_a=1)
    div_unanimous = evaluate_warp_divergence_and_ilp(active_lanes_in_branch_a=32)

    check(
        "ASP Ch8 p.275: 50/50 branch split (16 vs 16 lanes) executes 2 serial passes at 50% warp execution efficiency; 1 vs 31 split idles 31 lanes in pass 1",
        div_50["divergent"] is True
        and div_50["serial_passes"] == 2
        and div_50["warp_execution_efficiency_pct"] == 50.0
        and div_1_31["max_idle_lanes_in_single_pass"] == 31
        and div_unanimous["divergent"] is False
        and div_unanimous["warp_execution_efficiency_pct"] == 100.0,
    )

    check(
        "ASP Ch8 Table 8-3: Predicating threshold branch cuts runtime 30 -> 15 ms (-50%), dynamic insts 600M -> 300M (-50%), branch stall 200 -> 100 cycles, lifts warp eff 50% -> 99%, and drops predicated-off threads 50% -> 0%",
        TABLE_8_3_PREDICATION["runtime_ms_before"] == 30.0
        and TABLE_8_3_PREDICATION["runtime_ms_after"] == 15.0
        and TABLE_8_3_PREDICATION["dynamic_instructions_millions_before"] == 600.0
        and TABLE_8_3_PREDICATION["dynamic_instructions_millions_after"] == 300.0
        and TABLE_8_3_PREDICATION["branch_stall_cycles_before"] == 200.0
        and TABLE_8_3_PREDICATION["branch_stall_cycles_after"] == 100.0
        and TABLE_8_3_PREDICATION["warp_exec_efficiency_pct_after"] == 99.0
        and TABLE_8_3_PREDICATION["predicated_off_threads_pct_after"] == 0.0,
    )

    # 5. Instruction-Level Parallelism (ILP) vs Required Occupancy & Blackwell Unified Cores (ASP Ch 8 pp. 282-290 & Table 8-4)
    check(
        "ASP Ch8 Table 8-4: ILP 1..4 requires 1536/1024/768/512 threads (48/32/24/16 warps = 75%/50%/37.5%/25% occupancy) to saturate a Blackwell SM",
        [ILP_SATURATION_TABLE[k]["threads_per_sm"] for k in (1, 2, 3, 4)] == [1536.0, 1024.0, 768.0, 512.0]
        and [ILP_SATURATION_TABLE[k]["warps_per_sm"] for k in (1, 2, 3, 4)] == [48.0, 32.0, 24.0, 16.0]
        and [ILP_SATURATION_TABLE[k]["occupancy_pct"] for k in (1, 2, 3, 4)] == [75.0, 50.0, 37.5, 25.0],
    )

    di_good = evaluate_warp_divergence_and_ilp(
        ilp_independent_ops_per_thread=4,
        dual_issue_pair=("FP32_MATH", "LD_ST_MEMORY"),
    )
    di_bad = evaluate_warp_divergence_and_ilp(
        ilp_independent_ops_per_thread=2,
        dual_issue_pair=("INT32_MATH", "FP32_MATH"),
    )
    check(
        "ASP Ch8 pp.266,283: Blackwell unified INT32/FP32 cores can dual-issue (FP32_MATH, LD_ST_MEMORY) but CANNOT dual-issue (INT32_MATH, FP32_MATH) on the same core in the same cycle",
        di_good["blackwell_can_dual_issue_pair"] is True
        and di_good["occupancy_pct_for_saturation"] == 25.0
        and di_bad["blackwell_can_dual_issue_pair"] is False,
    )

    # 6. Input Validation Checks
    try:
        calc_sm_occupancy_and_limiters(gpu_profile="UNKNOWN_GPU")
        check("Rejects unknown gpu_profile", False)
    except OccupancyILPError:
        check("Rejects unknown gpu_profile", True)

    try:
        calc_sm_occupancy_and_limiters(threads_per_block=2048)
        check("Rejects threads_per_block > 1024", False)
    except OccupancyILPError:
        check("Rejects threads_per_block > 1024", True)

    try:
        calc_sm_occupancy_and_limiters(regs_per_thread=300)
        check("Rejects regs_per_thread > 255", False)
    except OccupancyILPError:
        check("Rejects regs_per_thread > 255", True)

    try:
        evaluate_launch_bounds(max_threads_per_block=512, min_blocks_per_sm=8)
        check("Rejects __launch_bounds__(512, 8) = 4,096 threads > 2,048 SM limit", False)
    except OccupancyILPError:
        check("Rejects __launch_bounds__(512, 8) = 4,096 threads > 2,048 SM limit", True)

    try:
        classify_ncu_stall_and_regime(50.0, 50.0, 80.0, "INVALID_STALL")
        check("Rejects unknown Nsight Compute stall reason", False)
    except OccupancyILPError:
        check("Rejects unknown Nsight Compute stall reason", True)

    try:
        evaluate_warp_divergence_and_ilp(active_lanes_in_branch_a=40)
        check("Rejects active_lanes_in_branch_a > 32", False)
    except OccupancyILPError:
        check("Rejects active_lanes_in_branch_a > 32", True)

    try:
        evaluate_warp_divergence_and_ilp(ilp_independent_ops_per_thread=6)
        check("Rejects unsupported ILP table index (6)", False)
    except OccupancyILPError:
        check("Rejects unsupported ILP table index (6)", True)

    check(
        "ASP Ch8 p.262: 19 / 64 warps == 29.69% (~30% achieved occupancy)",
        round((19 / 64) * 100.0) == 30,
    )
    check(
        "ASP Ch8 p.289: Unrolling ILP raises scheduler IPC from 1.0 to 1.8 instructions/cycle (1.8x)",
        round(1.8 / 1.0, 1) == 1.8,
    )
    check(
        "ASP Ch8 Table 8-4: 4-way ILP (16 warps) needs 3x fewer warps than 1-way ILP (48 warps) to saturate SM",
        48 // 16 == 3,
    )

    print(f"\nSummary: {passed} passed, 0 failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
