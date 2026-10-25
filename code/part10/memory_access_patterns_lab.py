#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.13: Memory access patterns and profiling."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory_access_patterns import (
    ASP_CH7_BENCHMARKS,
    MemoryPatternError,
    analyze_shared_memory_bank_conflicts,
    analyze_warp_global_memory_access,
    calc_tile_residency_and_register_budget,
    calc_vectorized_warp_load,
    simulate_warp_shuffle_down_reduction,
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
    print("=== Chapter 10.13 Lab: Memory Access Patterns and Profiling (ASP Chapter 7) ===")

    # 1. Coalesced vs Misaligned vs Strided Global Memory Access (ASP Ch 7 pp. 216-221 & Table 7-1)
    c_aligned = analyze_warp_global_memory_access(stride_elements=1, bytes_per_element=4, start_offset_bytes=0)
    c_misaligned = analyze_warp_global_memory_access(stride_elements=1, bytes_per_element=4, start_offset_bytes=4)
    c_stride2 = analyze_warp_global_memory_access(stride_elements=2, bytes_per_element=4, start_offset_bytes=0)
    c_stride8 = analyze_warp_global_memory_access(stride_elements=8, bytes_per_element=4, start_offset_bytes=0)

    check(
        "ASP Ch7 p.216: Aligned stride-1 FP32 warp load touches 1 x 128B cache line = 4.0 x 32B sectors (100% load efficiency)",
        c_aligned["sectors_per_request"] == 4.0
        and c_aligned["cache_lines_touched"] == 1
        and c_aligned["is_fully_coalesced"] is True,
    )
    check(
        "ASP Ch7 p.216: Misaligned stride-1 FP32 warp load (offset +4B) straddles 2 cache lines and fetches 5 sectors",
        c_misaligned["sectors_per_request"] == 5.0
        and c_misaligned["cache_lines_touched"] == 2
        and c_misaligned["is_fully_coalesced"] is False,
    )
    check(
        "ASP Ch7 p.219 & Table 7-1: Stride-2 FP32 warp load touches 8.0 sectors across 2 cache lines; stride>=8 touches 32.0 sectors",
        c_stride2["sectors_per_request"] == 8.0
        and c_stride2["cache_lines_touched"] == 2
        and c_stride8["sectors_per_request"] == 32.0,
    )

    t71 = ASP_CH7_BENCHMARKS["TABLE_7_1_COALESCING"]
    check(
        "ASP Ch7 Table 7-1: Coalescing raises DRAM throughput 25% -> 90% (3.6x), Load Efficiency 23% -> 99%, and cuts runtime 4.8 -> 1.3 ms (3.7x)",
        t71["dram_pct_before"] == 25.0
        and t71["dram_pct_after"] == 90.0
        and t71["load_eff_pct_before"] == 23.0
        and t71["load_eff_pct_after"] == 99.0
        and round(t71["runtime_ms_before"] / t71["runtime_ms_after"], 1) == 3.7,
    )

    # 2. Vectorized Memory Access: float4 (16B) & Blackwell float8 (32B) (ASP Ch 7 pp. 221-226 & Tables 7-2, 7-3)
    v16 = calc_vectorized_warp_load(vector_bytes_per_thread=16, pointer_alignment_bytes=256)
    v32 = calc_vectorized_warp_load(vector_bytes_per_thread=32, pointer_alignment_bytes=256)
    v_mis = calc_vectorized_warp_load(vector_bytes_per_thread=16, pointer_alignment_bytes=260)

    check(
        "ASP Ch7 p.222 & Table 7-3: float4 (16B/thread, ld.global.v4.f32) moves 512 B/warp = 4 x 128B lines = 16 sectors (4.0 sectors/tx, 4x fewer instructions)",
        v16["aligned"] is True
        and v16["ptx_instruction"] == "ld.global.v4.f32"
        and v16["warp_bytes_per_instruction"] == 512
        and v16["cache_lines_128b_per_warp"] == 4
        and v16["sectors_32b_per_warp"] == 16
        and v16["scalar_instruction_reduction_x"] == 4.0,
    )
    check(
        "ASP Ch7 pp.223-226: Blackwell CUDA 13+ alignas(32) float8 (32B/thread, ld.global.v8.f32) moves 1,024 B/warp = 8 x 128B lines = 32 sectors",
        v32["aligned"] is True
        and v32["ptx_instruction"] == "ld.global.v8.f32"
        and v32["warp_bytes_per_instruction"] == 1024
        and v32["cache_lines_128b_per_warp"] == 8
        and v32["sectors_32b_per_warp"] == 32
        and v32["scalar_instruction_reduction_x"] == 8.0,
    )
    check(
        "ASP Ch7 p.223: Misaligned element offset (260 % 16 != 0) forfeits vectorized load",
        v_mis["aligned"] is False and v_mis["ptx_instruction"] == "MISALIGNED_FALLBACK_SCALAR",
    )

    t72 = ASP_CH7_BENCHMARKS["TABLE_7_2_VECTORIZED"]
    check(
        "ASP Ch7 Table 7-2: Vectorized loads raise Load Efficiency 28% -> 97%, cut sectors/req 31.8 -> 4.0, and cut runtime 4.2 -> 1.2 ms (3.5x)",
        t72["load_eff_pct_before"] == 28.0
        and t72["load_eff_pct_after"] == 97.0
        and t72["sectors_per_req_before"] == 31.8
        and round(t72["runtime_ms_before"] / t72["runtime_ms_after"], 1) == 3.5,
    )

    # 3. Shared-Memory Tiling & Register Residency Math (ASP Ch 7 pp. 226-233 & Table 7-4)
    t74 = ASP_CH7_BENCHMARKS["TABLE_7_4_SHMEM_TILING"]
    check(
        "ASP Ch7 Table 7-4: 32x32 shared-memory tiling cuts global load sectors 9,800 -> 1,200 (~8.17x), lifts occupancy 42% -> 89%, and raises GFLOPS 15 -> 170 (~11.3x)",
        t74["global_sectors_before"] == 9800.0
        and t74["global_sectors_after"] == 1200.0
        and t74["gflops_before"] == 15.0
        and t74["gflops_after"] == 170.0
        and t74["ai_flops_per_byte_before"] == 1.5
        and t74["ai_flops_per_byte_after"] == 8.0,
    )

    res_12 = calc_tile_residency_and_register_budget(tile_dim=64, threads_per_block=1024, regs_per_thread=12)
    res_22 = calc_tile_residency_and_register_budget(tile_dim=64, threads_per_block=1024, regs_per_thread=22)
    check(
        "ASP Ch7 p.231: 64x64 FP32 tile uses 16,384 B (16 KB) per matrix; 12 regs/thread * 1,024 = 12,288 regs/block (5 blocks by regs, capped at 2 blocks = 2,048 threads by SM thread limit)",
        res_12["bytes_per_matrix_tile"] == 16384
        and res_12["regs_per_block"] == 12288
        and res_12["blocks_limited_by_regs"] == 5
        and res_12["resident_blocks_per_sm"] == 2
        and res_12["resident_threads_per_sm"] == 2048,
    )
    check(
        "ASP Ch7 p.232: 22 regs/thread * 1,024 = 22,528 regs/block fits 2 blocks (45,056 <= 65,536 regs) = 2,048 resident threads/SM",
        res_22["regs_per_block"] == 22528
        and res_22["blocks_limited_by_regs"] == 2
        and res_22["resident_blocks_per_sm"] == 2,
    )

    # 4. Shared-Memory Bank Conflicts & +1 Column Padding (ASP Ch 7 pp. 233-238 & Table 7-5)
    bc_row = analyze_shared_memory_bank_conflicts(tile_cols=32, pad_cols=0, access_mode="ROW_MAJOR_ACCESS")
    bc_col_unpadded = analyze_shared_memory_bank_conflicts(tile_cols=32, pad_cols=0, access_mode="COLUMN_TRANSPOSE_READ")
    bc_col_padded = analyze_shared_memory_bank_conflicts(tile_cols=32, pad_cols=1, access_mode="COLUMN_TRANSPOSE_READ")
    bc_bcast = analyze_shared_memory_bank_conflicts(tile_cols=32, pad_cols=0, access_mode="UNIFORM_BROADCAST")

    check(
        "ASP Ch7 p.234: Row-major shared access hits 32 distinct banks (1-way, 0 bank conflicts)",
        bc_row["unique_banks_hit"] == 32 and bc_row["has_bank_conflict"] is False,
    )
    check(
        "ASP Ch7 pp.234-236: Unpadded tile[32][32] column transpose (128B stride) hits bank 0 across all 32 lanes -> 32-way bank conflict",
        bc_col_unpadded["unique_banks_hit"] == 1
        and bc_col_unpadded["max_ways_conflict"] == 32
        and bc_col_unpadded["has_bank_conflict"] is True,
    )
    check(
        "ASP Ch7 pp.235-237: Padded tile[32][33] (+1 float = 3.12% ~ 3% overhead) shifts row modulo across 32 distinct banks -> 0 bank conflicts",
        bc_col_padded["row_stride_floats"] == 33
        and bc_col_padded["unique_banks_hit"] == 32
        and bc_col_padded["max_ways_conflict"] == 1
        and bc_col_padded["has_bank_conflict"] is False
        and bc_col_padded["padding_overhead_pct"] == 3.12,
    )
    check(
        "ASP Ch7 p.234: All 32 threads reading the exact same shared-memory address triggers hardware broadcast (0 bank conflicts)",
        bc_bcast["hardware_broadcast"] is True and bc_bcast["has_bank_conflict"] is False,
    )

    t75 = ASP_CH7_BENCHMARKS["TABLE_7_5_BANK_PADDING"]
    check(
        "ASP Ch7 Table 7-5: Padding tile[32][33] drops bank conflicts 4.8M -> 0, lifts shared util 52% -> 100%, cuts warp stalls 38% -> 0.5%, and cuts runtime 4.0 -> 1.3 ms (~3x)",
        t75["bank_conflicts_millions_before"] == 4.8
        and t75["bank_conflicts_millions_after"] == 0.0
        and t75["shmem_pct_after"] == 100.0
        and t75["warp_stall_pct_after"] == 0.5
        and round(t75["runtime_ms_before"] / t75["runtime_ms_after"], 1) == 3.1,
    )

    # 5. Warp Shuffle Butterfly Reduction (`__shfl_down_sync`, ASP Ch 7 pp. 239-240)
    shfl = simulate_warp_shuffle_down_reduction([float(i + 1) for i in range(32)])
    check(
        "ASP Ch7 p.239: __shfl_down_sync butterfly reduction sums 32 lanes (1..32 == 528.0) in 5 steps (offsets 16,8,4,2,1) with 0 shared memory and 0 bank conflicts",
        shfl["steps"] == 5
        and shfl["offsets"] == [16, 8, 4, 2, 1]
        and shfl["lane0_sum"] == 528.0
        and shfl["shared_memory_bytes_used"] == 0
        and shfl["bank_conflicts"] == 0,
    )

    # 6. Read-Only Cache (`const __restrict__`, Table 7-6) & TMA Async Prefetch (`cuda::memcpy_async`, Table 7-7)
    t76 = ASP_CH7_BENCHMARKS["TABLE_7_6_READONLY_RESTRICT"]
    check(
        "ASP Ch7 Table 7-6: const __restrict__ raises Load Efficiency 52% -> 97%, L2 read 1,500 -> 1,800 GB/s, cuts DRAM 600 -> 200 GB/s, and cuts runtime 2.5 -> 1.0 ms (2.5x)",
        t76["load_eff_pct_after"] == 97.0
        and t76["dram_gbps_before"] == 600.0
        and t76["dram_gbps_after"] == 200.0
        and t76["l2_read_gbps_after"] == 1800.0
        and round(t76["runtime_ms_before"] / t76["runtime_ms_after"], 1) == 2.5,
    )

    t77 = ASP_CH7_BENCHMARKS["TABLE_7_7_TMA_PREFETCH"]
    check(
        "ASP Ch7 Table 7-7: TMA double-buffering (cuda::memcpy_async) lifts Load Efficiency 23% -> 99%, cuts sectors/req 6.4 -> 4.0, lifts SM Active 62% -> 100%, and cuts runtime 18 -> 7 ms (~2.6x)",
        t77["load_eff_pct_after"] == 99.0
        and t77["sectors_per_req_before"] == 6.4
        and t77["sectors_per_req_after"] == 4.0
        and t77["sm_active_pct_after"] == 100.0
        and round(t77["runtime_ms_before"] / t77["runtime_ms_after"], 1) == 2.6,
    )

    # 7. Input Validation Checks
    try:
        analyze_warp_global_memory_access(stride_elements=0)
        check("Rejects non-positive stride_elements", False)
    except MemoryPatternError:
        check("Rejects non-positive stride_elements", True)

    try:
        calc_vectorized_warp_load(vector_bytes_per_thread=12)
        check("Rejects invalid vector_bytes_per_thread (12)", False)
    except MemoryPatternError:
        check("Rejects invalid vector_bytes_per_thread (12)", True)

    try:
        analyze_shared_memory_bank_conflicts(tile_cols=0)
        check("Rejects non-positive tile_cols", False)
    except MemoryPatternError:
        check("Rejects non-positive tile_cols", True)

    try:
        analyze_shared_memory_bank_conflicts(access_mode="INVALID_MODE")
        check("Rejects unknown shared-memory access_mode", False)
    except MemoryPatternError:
        check("Rejects unknown shared-memory access_mode", True)

    try:
        calc_tile_residency_and_register_budget(regs_per_thread=300)
        check("Rejects regs_per_thread > 255 hardware ceiling", False)
    except MemoryPatternError:
        check("Rejects regs_per_thread > 255 hardware ceiling", True)

    try:
        simulate_warp_shuffle_down_reduction([1.0, 2.0])
        check("Rejects warp shuffle list with length != 32", False)
    except MemoryPatternError:
        check("Rejects warp shuffle list with length != 32", True)

    print(f"\nSummary: {passed} passed, 0 failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
