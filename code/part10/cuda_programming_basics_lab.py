#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.11: CUDA programming basics: kernels, indexing and memory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cuda_programming_basics import (
    BLACKWELL_CUDA_LIMITS,
    CUDABasicsError,
    analyze_memory_and_timing_Lifecycle,
    calc_1d_launch_and_indexing,
    diagnose_cuda_correctness_and_sync,
    evaluate_2d_image_launch,
    evaluate_unified_memory_behavior,
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
    print("=== Chapter 10.11 Lab: CUDA Programming Basics (Kernels, Indexing & Memory) ===")

    # 1. Hardware Thread, Block, SM, and Grid Limits (ASP Ch 6 Tables 6-2, 6-3, 6-4)
    check(
        "ASP Ch6 Tables 6-2 & 6-3: Warp size=32, max threads/block=1024 (32 warps), max resident warps/SM=64 (2048 threads, 32 blocks/SM)",
        BLACKWELL_CUDA_LIMITS.warp_size == 32
        and BLACKWELL_CUDA_LIMITS.max_threads_per_block == 1024
        and BLACKWELL_CUDA_LIMITS.max_warps_per_block == 32
        and BLACKWELL_CUDA_LIMITS.max_resident_warps_per_sm == 64
        and BLACKWELL_CUDA_LIMITS.max_resident_threads_per_sm == 2048
        and BLACKWELL_CUDA_LIMITS.max_active_blocks_per_sm == 32,
    )
    check(
        "ASP Ch6 Table 6-4: Max grid dimensions are X=2,147,483,647, Y=65,535, Z=65,535, and 128 concurrent grids",
        BLACKWELL_CUDA_LIMITS.max_grid_dim_x == 2147483647
        and BLACKWELL_CUDA_LIMITS.max_grid_dim_y == 65535
        and BLACKWELL_CUDA_LIMITS.max_grid_dim_z == 65535
        and BLACKWELL_CUDA_LIMITS.max_concurrent_grids == 128,
    )

    # 2. 1D Indexing, Ceiling vs Truncated Division, and Warp Waste (V3 Ch 3, Ch 4 & Lab 02)
    idx_1m3 = calc_1d_launch_and_indexing(
        element_count=1000003,
        threads_per_block=256,
        sample_block_idx=3,
        sample_thread_idx=5,
        gpu_sm_count=132,
    )
    check(
        "V3 Ch4 §2: Global 1D index for blockIdx.x=3, blockDim.x=256, threadIdx.x=5 == 3*256 + 5 == 773",
        idx_1m3["sample_global_index"] == 773,
    )
    check(
        "V3 Ch4 & Lab 02: N=1,000,003 with 256 threads/block yields 3,907 ceiling blocks (1,000,192 threads, 189 guarded)",
        idx_1m3["blocks_ceiling"] == 3907
        and idx_1m3["launched_threads_ceiling"] == 1000192
        and idx_1m3["guarded_extra_threads"] == 189,
    )
    check(
        "V3 Ch4 & Lab 02 Failure D: Truncated division (N // 256 == 3,906 blocks = 999,936 threads) leaves 67 elements untouched",
        idx_1m3["blocks_truncated"] == 3906
        and idx_1m3["unprocessed_if_truncated"] == 67,
    )

    idx_1m = calc_1d_launch_and_indexing(element_count=1000000, threads_per_block=256)
    check(
        "ASP Ch6 p.186 & V3 Ch4 §3: N=1,000,000 with 256 threads/block yields 3,907 blocks (1,000,192 threads, 192 extra guarded)",
        idx_1m["blocks_ceiling"] == 3907 and idx_1m["guarded_extra_threads"] == 192,
    )

    idx_63 = calc_1d_launch_and_indexing(element_count=63, threads_per_block=64, sample_block_idx=0, sample_thread_idx=0)
    check(
        "ASP Ch6 p.188: N=63 across 2 warps (64 threads) guards 1 out-of-range thread at idx=63",
        idx_63["warps_per_block"] == 2 and idx_63["guarded_extra_threads"] == 1,
    )

    idx_50 = calc_1d_launch_and_indexing(element_count=50, threads_per_block=50, sample_block_idx=0, sample_thread_idx=0)
    check(
        "V3 Ch3 §3: Block size 50 spawns 2 warps (64 lanes) and leaves 14 warp lanes idle (78.12% efficiency)",
        idx_50["warps_per_block"] == 2
        and idx_50["allocated_warp_lanes_per_block"] == 64
        and idx_50["idle_warp_lanes_per_block"] == 14,
    )

    idx_underfill = calc_1d_launch_and_indexing(
        element_count=64 * 256,
        threads_per_block=256,
        gpu_sm_count=132,
    )
    check(
        "V3 Ch3 §Production Troubleshooting: <<<64, 256>>> (64 blocks) on H100 (132 SMs) leaves 68 SMs completely idle",
        idx_underfill["blocks_ceiling"] == 64
        and idx_underfill["idle_sms"] == 68
        and idx_underfill["grid_underfills_gpu"] is True,
    )

    # 3. 2D Image Launch Configuration (V3 Ch 4 Customer Scenario & ASP Ch 6 p. 191)
    img_bad = evaluate_2d_image_launch(width=3840, height=2160, block_x=1, block_y=1)
    img_good = evaluate_2d_image_launch(width=3840, height=2160, block_x=16, block_y=16)
    check(
        "V3 Ch4 Customer Scenario: 4K image (3840x2160) with dim3(1,1) wastes 31 of 32 warp lanes (96.88% ~ 97% waste)",
        img_bad["total_blocks"] == 8294400
        and img_bad["wasted_lanes_per_block"] == 31
        and img_bad["wasted_lane_pct"] == 96.88,
    )
    check(
        "V3 Ch4 Customer Scenario: Reconfiguring 4K image to dim3(16,16) (256 threads = 8 warps) achieves 0 wasted lanes (100% warp fill)",
        img_good["threads_per_block"] == 256
        and img_good["warps_per_block"] == 8
        and img_good["wasted_lanes_per_block"] == 0
        and img_good["active_lane_pct"] == 100.0,
    )

    # 4. Timing & Memory Allocation Lifecycle Ratios (V3 Ch 3, Ch 5 & Lab 02)
    timing = analyze_memory_and_timing_Lifecycle()
    check(
        "V3 Lab 02 Step 4: Copy-in (0.847 ms) + Copy-out (0.412 ms) = 1.259 ms is 13.11x (~13x) larger than 0.096 ms kernel time",
        timing["total_transfer_ms"] == 1.259
        and timing["transfer_to_kernel_ratio_x"] == 13.11,
    )
    check(
        "V3 Ch3 §Production Troubleshooting: Async host timer (0.014 ms) vs CUDA event time (4.812 ms) is a 343.71x (~340x) gap",
        timing["async_timer_error_ratio_x"] == 343.71,
    )
    check(
        "V3 Ch5 §Production Troubleshooting: cudaMalloc (71.2%) + cudaFree (6.4%) = 77.6% of CUDA API time (>8x the 3.8% kernel launch time)",
        timing["alloc_free_api_pct"] == 77.6
        and timing["alloc_to_launch_ratio_x"] > 8.0,
    )

    # 5. Unified Memory Demand Paging, Prefetch, and Oversubscription Cliff (V3 Ch 9)
    um_24 = evaluate_unified_memory_behavior(working_set_gb=24.0, device_capacity_gb=40.0)
    um_36 = evaluate_unified_memory_behavior(working_set_gb=36.0, device_capacity_gb=40.0)
    um_44 = evaluate_unified_memory_behavior(working_set_gb=44.0, device_capacity_gb=40.0)
    check(
        "V3 Ch9: Cold first-touch (812.4 ms) is 19.72x (~20x) slower than warm (41.2 ms), and CPU debug print (96.7 ms) is 23.59x (>23x) the 4.1 ms kernel",
        um_24["cold_vs_warm_ratio_x"] == 19.72
        and um_24["cpu_debug_stall_ratio_x"] == 23.59,
    )
    check(
        "V3 Ch9 Oversubscription Table: 24 GB (60%) = 118 GB/s, 36 GB (90%) = 104 GB/s, 44 GB (110% oversubscribed) collapses to 9 GB/s (thrashing)",
        um_24["effective_bw_gbps"] == 118.0
        and um_36["effective_bw_gbps"] == 104.0
        and um_44["oversubscribed"] is True
        and um_44["effective_bw_gbps"] == 9.0
        and um_44["state"] == "OVERSUBSCRIBED_PAGE_THRASHING",
    )

    # 6. Correctness & Synchronization Diagnostics (V3 Ch 3, Ch 4, Ch 6 & Lab 02)
    clean_diag = diagnose_cuda_correctness_and_sync()
    check("Clean kernel + launch + sync configuration passes correctness audit", clean_diag["correct"] is True)

    d_host_ptr = diagnose_cuda_correctness_and_sync(passed_host_pointer_to_kernel=True)
    check(
        "V3 Ch3 Customer Scenario: Detects passing host malloc() pointer directly into __global__ kernel",
        d_host_ptr["correct"] is False and "HOST_POINTER_IN_KERNEL" in d_host_ptr["defects"][0],
    )

    d_bounds = diagnose_cuda_correctness_and_sync(missing_bounds_check=True)
    check(
        "V3 Ch4 & Lab 02 Failure A: Detects missing 'if (idx < N)' bounds check",
        d_bounds["correct"] is False and "MISSING_BOUNDS_CHECK" in d_bounds["defects"][0],
    )

    d_trunc = diagnose_cuda_correctness_and_sync(used_truncated_block_division=True)
    check(
        "V3 Ch4 & Lab 02 Failure D: Detects truncated integer block division leaving tail elements at 0.0",
        d_trunc["correct"] is False and "TRUNCATED_GRID_UNDERLAUNCH" in d_trunc["defects"][0],
    )

    d_spin = diagnose_cuda_correctness_and_sync(cross_block_spin_wait=True)
    check(
        "V3 Ch6 Customer Scenario: Detects inter-block while(true) spin-wait SM deadlock",
        d_spin["correct"] is False and "INTER_BLOCK_SPIN_DEADLOCK" in d_spin["defects"][0],
    )

    d_race = diagnose_cuda_correctness_and_sync(unprotected_concurrent_reduction=True)
    check(
        "V3 Ch6: Detects non-deterministic reduction data race (missing __syncthreads / atomicAdd)",
        d_race["correct"] is False and "DATA_RACE_NON_DETERMINISTIC" in d_race["defects"][0],
    )

    # 7. Input Validation Checks (`Failure B: threads_per_block = 100000 > 1024`)
    try:
        calc_1d_launch_and_indexing(element_count=1000003, threads_per_block=100000)
        check("V3 Lab 02 Failure B: Rejects threads_per_block = 100000 (> 1024 max) with invalid configuration argument", False)
    except CUDABasicsError as exc:
        check(
            "V3 Lab 02 Failure B: Rejects threads_per_block = 100000 (> 1024 max) with invalid configuration argument",
            "invalid configuration argument" in str(exc),
        )

    try:
        evaluate_2d_image_launch(width=1024, height=1024, block_x=64, block_y=32)
        check("Rejects 2D block_x * block_y > 1024", False)
    except CUDABasicsError:
        check("Rejects 2D block_x * block_y > 1024", True)

    try:
        evaluate_unified_memory_behavior(working_set_gb=0.0)
        check("Rejects non-positive working_set_gb", False)
    except CUDABasicsError:
        check("Rejects non-positive working_set_gb", True)

    print(f"\nSummary: {passed} passed, 0 failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
