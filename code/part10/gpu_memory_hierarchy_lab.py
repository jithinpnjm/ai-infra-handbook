#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.3: The GPU memory hierarchy."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from gpu_memory_hierarchy import (
    ASP_CH7_BENCHMARKS,
    BLACKWELL_MEMORY_TIERS,
    POINTS_OF_COHERENCY,
    MemoryHierarchyError,
    audit_host_device_memory_config,
    calc_effective_bandwidth_utilization,
    calc_register_spill_traffic,
    calc_shared_mem_bank_conflict,
    calc_warp_coalescing_and_vector_loads,
    evaluate_capacity_vs_decode_floor,
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
    print("=== Chapter 10.3 Lab: The GPU Memory Hierarchy ===")

    # 1. Blackwell 7-tier memory hierarchy & Points of Coherency (ASP Ch 6 Table 6-5 & Fig 6-15)
    check(
        "ASP Ch6 Table 6-5: Tracks all 7 Blackwell memory tiers (Registers, Shared/L1, TMEM, Constant, L2 126MB, Local, Global HBM3e)",
        set(BLACKWELL_MEMORY_TIERS.keys())
        == {
            "registers",
            "shared_l1",
            "tmem",
            "constant_cache",
            "l2_cache",
            "local_memory",
            "global_hbm",
        },
    )
    check(
        "ASP Ch6 p.194: TMEM is 256 KB per SM dedicated to Tensor Cores (~10 cycles) and is not directly pointer-addressable in C++",
        BLACKWELL_MEMORY_TIERS["tmem"].directly_pointer_addressable is False
        and "256 KB" in BLACKWELL_MEMORY_TIERS["tmem"].capacity_desc
        and "~10 cycles" in BLACKWELL_MEMORY_TIERS["tmem"].latency_cycles_approx,
    )
    check(
        "ASP Ch6 p.196 & V2 Ch7: Local memory is thread-scoped logical spill space backed by off-chip HBM DRAM",
        BLACKWELL_MEMORY_TIERS["local_memory"].scope == "thread"
        and "HBM DRAM" in BLACKWELL_MEMORY_TIERS["local_memory"].backed_by,
    )
    check(
        "ASP Ch6 Fig 6-15: 5 Points of Coherency (thread, thread_block_cta, thread_block_cluster, device, system)",
        len(POINTS_OF_COHERENCY) == 5 and "thread_block_cluster" in POINTS_OF_COHERENCY,
    )

    # 2. Capacity vs Bandwidth decode latency floor (V2 Ch 5 worked example)
    cap_13b = evaluate_capacity_vs_decode_floor(13.0, 2.0, 80.0, 3350.0)
    check(
        "V2 Ch5 worked example: 13B FP16 model == 26.0 GB (fits in 80 GB H100 with 54 GB free), weight-read floor == 7.76 ms/token (~7.8 ms)",
        cap_13b["weight_gb"] == 26.0
        and cap_13b["fits_in_vram"] is True
        and cap_13b["free_vram_gb"] == 54.0
        and cap_13b["min_token_latency_ms"] == 7.76,
    )

    # 3. Register spilling traffic calculation (V2 Ch 7 worked example)
    spill = calc_register_spill_traffic(8, 256, 256)
    check(
        "V2 Ch7 worked example: 2 spilled floats (8B) across 65,536 threads (256x256) == 1,048,576 B (1.05 MB decimal / 1.0 MiB) HBM traffic",
        spill["total_threads"] == 65536
        and spill["total_spill_bytes"] == 1_048_576
        and spill["total_spill_mb_decimal"] == 1.05
        and spill["total_spill_mib"] == 1.0,
    )

    # 4. Effective HBM bandwidth utilization check (V2 Ch 8 worked example)
    bw_good = calc_effective_bandwidth_utilization(8.0, 8.0, 6.0, 3350.0)
    bw_bad = calc_effective_bandwidth_utilization(1.5, 1.5, 6.0, 3350.0)
    check(
        "V2 Ch8 worked example: 8 GB read + 8 GB write in 6 ms == 2,666.7 GB/s (79.6% ~ 80% of 3,350 GB/s H100 peak)",
        bw_good["total_gb"] == 16.0
        and bw_good["achieved_gbps"] == 2666.7
        and bw_good["pct_of_peak"] == 79.6,
    )
    check(
        "V2 Ch8 worked example: 500 GB/s achieved on 3,350 GB/s H100 == 14.9% (~15% of peak, indicating uncoalesced access)",
        bw_bad["achieved_gbps"] == 500.0 and bw_bad["pct_of_peak"] == 14.9,
    )

    # 5. Global memory coalescing & 128B cache-line / 32B sector math (ASP Ch 7 pp. 217-226)
    c_aligned = calc_warp_coalescing_and_vector_loads(4, stride_elements=1, base_offset_bytes=0)
    c_misaligned = calc_warp_coalescing_and_vector_loads(4, stride_elements=1, base_offset_bytes=4)
    c_stride2 = calc_warp_coalescing_and_vector_loads(4, stride_elements=2, base_offset_bytes=0)
    c_stride8 = calc_warp_coalescing_and_vector_loads(4, stride_elements=8, base_offset_bytes=0)
    check(
        "ASP Ch7 p.217: Aligned contiguous 4B warp load == 128 B across 4 sectors (1 128B line, 100.0% load efficiency)",
        c_aligned["useful_bytes"] == 128
        and c_aligned["unique_32b_sectors"] == 4
        and c_aligned["unique_128b_lines"] == 1
        and c_aligned["load_efficiency_pct"] == 100.0,
    )
    check(
        "ASP Ch7 p.217: Misaligned contiguous 4B warp load (+4B offset) spans 2 128B lines and fetches 5 sectors (80.0% efficiency)",
        c_misaligned["unique_128b_lines"] == 2
        and c_misaligned["unique_32b_sectors"] == 5
        and c_misaligned["load_efficiency_pct"] == 80.0,
    )
    check(
        "ASP Ch7 Table 7-1: Stride-2 4B warp load fetches 8 sectors across 2 128B lines (50.0% efficiency); stride-8+ fetches 32 sectors (12.5%)",
        c_stride2["unique_32b_sectors"] == 8
        and c_stride2["unique_128b_lines"] == 2
        and c_stride2["load_efficiency_pct"] == 50.0
        and c_stride8["unique_32b_sectors"] == 32
        and c_stride8["load_efficiency_pct"] == 12.5,
    )

    # 6. Vectorized memory loads: float4 (16B) vs Blackwell 32B (ASP Ch 7 pp. 223-226)
    v_16b = calc_warp_coalescing_and_vector_loads(16, stride_elements=1, base_offset_bytes=0)
    v_32b = calc_warp_coalescing_and_vector_loads(32, stride_elements=1, base_offset_bytes=0)
    check(
        "ASP Ch7 p.224: Vectorized float4 (16B/thread) moves 512 B/warp across 4 128B lines (16 sectors, 100% efficiency)",
        v_16b["useful_bytes"] == 512
        and v_16b["unique_128b_lines"] == 4
        and v_16b["unique_32b_sectors"] == 16
        and v_16b["load_efficiency_pct"] == 100.0,
    )
    check(
        "ASP Ch7 p.225: Blackwell 256-bit (32B/thread) vector load moves 1,024 B/warp across 8 128B lines (32 sectors, 100% efficiency)",
        v_32b["useful_bytes"] == 1024
        and v_32b["unique_128b_lines"] == 8
        and v_32b["unique_32b_sectors"] == 32
        and v_32b["load_efficiency_pct"] == 100.0,
    )

    # 7. Shared-memory 32-bank conflict math & [32][33] padding (ASP Ch 7 pp. 235-241)
    b_row = calc_shared_mem_bank_conflict(1)
    b_col_unpadded = calc_shared_mem_bank_conflict(32)
    b_col_padded = calc_shared_mem_bank_conflict(33)
    b_stride2 = calc_shared_mem_bank_conflict(2)
    b_stride16 = calc_shared_mem_bank_conflict(16)
    b_bcast = calc_shared_mem_bank_conflict(0, all_threads_same_word=True)
    check(
        "ASP Ch7 p.235: Stride-1 row access hits 32 banks (conflict-free); stride-32 column access in tile[32][32] hits 1 bank (32-way conflict!)",
        b_row["unique_banks_touched"] == 32
        and b_row["conflict_way"] == 1
        and b_col_unpadded["unique_banks_touched"] == 1
        and b_col_unpadded["conflict_way"] == 32
        and b_col_unpadded["is_conflict_free"] is False,
    )
    check(
        "ASP Ch7 p.237: Padded tile[32][33] (stride 33) hits all 32 banks with 0 conflicts (conflict_way == 1)",
        b_col_padded["unique_banks_touched"] == 32
        and b_col_padded["conflict_way"] == 1
        and b_col_padded["is_conflict_free"] is True,
    )
    check(
        "ASP Ch7 Fig 7-5 & p.236: Stride-2 causes 2-way bank conflict; stride-16 causes 16-way conflict; uniform same-word read broadcasts in 1 cycle",
        b_stride2["conflict_way"] == 2
        and b_stride16["conflict_way"] == 16
        and b_bcast["broadcast"] is True
        and b_bcast["is_conflict_free"] is True,
    )

    # 8. ASP Chapter 7 Before/After Benchmark Tables (Tables 7-1, 7-4, 7-5, 7-6, 7-7)
    t71 = ASP_CH7_BENCHMARKS["table_7_1_coalescing"]
    t74 = ASP_CH7_BENCHMARKS["table_7_4_shared_mem_tiling"]
    t75 = ASP_CH7_BENCHMARKS["table_7_5_bank_conflict_padding"]
    t76 = ASP_CH7_BENCHMARKS["table_7_6_readonly_restrict"]
    t77 = ASP_CH7_BENCHMARKS["table_7_7_tma_async_prefetch"]
    check(
        "ASP Ch7 Table 7-1: Coalescing improves DRAM peak from 25% to 90% (3.6x), load eff 23% to 99%, and runtime 4.8 ms to 1.3 ms (3.7x)",
        round(t71["coalesced_dram_pct"] / t71["uncoalesced_dram_pct"], 1) == 3.6
        and round(t71["uncoalesced_time_ms"] / t71["coalesced_time_ms"], 1) == 3.7,
    )
    check(
        "ASP Ch7 Table 7-4: 32x32 shared-memory tiling cuts global load sectors 9,800 -> 1,200, raises GFLOPS 15 -> 170 (11.3x), and intensity 1.5 -> 8.0",
        t74["naive_global_sectors"] == 9800.0
        and t74["tiled_global_sectors"] == 1200.0
        and round(t74["tiled_gflops"] / t74["naive_gflops"], 1) == 11.3
        and t74["tiled_arith_intensity"] == 8.0,
    )
    check(
        "ASP Ch7 Table 7-5: [32][33] padding eliminates 4.8M bank conflicts -> 0, lifts SMEM util 52% -> 100%, and speeds transpose 4.0 -> 1.3 ms (3.1x)",
        t75["unpadded_bank_conflicts"] == 4_800_000.0
        and t75["padded_bank_conflicts"] == 0.0
        and round(t75["unpadded_time_ms"] / t75["padded_time_ms"], 1) == 3.1,
    )
    check(
        "ASP Ch7 Table 7-6: const __restrict__ read-only cache cuts DRAM 600 -> 200 GB/s, raises L2 1,500 -> 1,800 GB/s, and speeds lookup 2.5 -> 1.0 ms (2.5x)",
        t76["before_dram_gbps"] == 600.0
        and t76["after_dram_gbps"] == 200.0
        and t76["before_time_ms"] / t76["after_time_ms"] == 2.5,
    )
    check(
        "ASP Ch7 Table 7-7: TMA cuda::memcpy_async double-buffering lifts SM Active 62% -> 100% and speeds execution 18 -> 7 ms (2.6x)",
        t77["after_sm_active_pct"] == 100.0
        and round(t77["before_time_ms"] / t77["after_time_ms"], 1) == 2.6,
    )

    # 9. Host-Device memory config auditor: BAR1 ReBAR, Pinned Memory, cudaMallocAsync, Unified Memory (VL4 Ch 1 & ASP Ch 6)
    cfg_ok = audit_host_device_memory_config(81920, 81920, True, True, True, True)
    cfg_legacy_bar = audit_host_device_memory_config(81920, 256, True, True, False, False)
    cfg_bad_all = audit_host_device_memory_config(81920, 256, False, False, True, False)
    check(
        "VL4 Ch1 §3.4: 80 GB GPU with BAR1 == 81,920 MiB passes ReBAR check; BAR1 == 256 MiB flags legacy PCIe aperture bottleneck",
        cfg_ok["rebar_enabled"] is True
        and cfg_ok["healthy"] is True
        and cfg_legacy_bar["rebar_enabled"] is False
        and len(cfg_legacy_bar["issues"]) == 1,
    )
    check(
        "ASP Ch6 & VL4 Ch1: Flags pageable host memory, synchronous cudaMalloc in loop, and unprefetched Unified Memory",
        len(cfg_bad_all["issues"]) == 4,
    )

    # 10. Negative / boundary checks
    raised = False
    try:
        calc_warp_coalescing_and_vector_loads(12)
    except MemoryHierarchyError:
        raised = True
    check("Rejects invalid per-thread vector byte width", raised)

    raised_bar = False
    try:
        audit_host_device_memory_config(0, 256, True, True)
    except MemoryHierarchyError:
        raised_bar = True
    check("Rejects non-positive VRAM / BAR1 capacity", raised_bar)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
