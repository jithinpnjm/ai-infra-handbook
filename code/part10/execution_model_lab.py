#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.2: The execution model — threads, warps, blocks and SMs."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from execution_model import (
    ARCH_LIMITS,
    BLACKWELL_SM_ISSUE_LIMITS,
    COMPUTE_SANITIZER_TOOLS,
    PROGRAMMING_ABSTRACTIONS,
    SCHEDULER_COMPARISON,
    SEQ_VS_PAR_BENCHMARK,
    ExecutionModelError,
    calc_domain_tile_decomposition,
    calc_grid_launch_1d,
    calc_sm_occupancy,
    diagnose_kernel_efficiency_gates,
    validate_launch_bounds,
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
    print("=== Chapter 10.2 Lab: The Execution Model — Threads, Warps, Blocks & SMs ===")

    # 1. Blackwell SM 4-scheduler dual-issue limits (ASP Ch 6 Table 6-1, p. 181)
    check(
        "ASP Ch6 Table 6-1: Blackwell SM has 4 warp schedulers, dual-issuing up to 4 math + 4 mem ops/cycle across 16 LD/ST units",
        BLACKWELL_SM_ISSUE_LIMITS["num_schedulers"] == 4
        and BLACKWELL_SM_ISSUE_LIMITS["max_warps_issued_per_cycle"] == 4
        and BLACKWELL_SM_ISSUE_LIMITS["max_math_ops_issued_per_cycle"] == 4
        and BLACKWELL_SM_ISSUE_LIMITS["max_mem_ops_issued_per_cycle"] == 4
        and BLACKWELL_SM_ISSUE_LIMITS["total_ld_st_units_per_sm"] == 16,
    )

    # 2. Thread, Block, SM, and Grid limits (ASP Ch 6 Tables 6-2, 6-3, 6-4, 6-5; V2 Ch 2)
    b200 = ARCH_LIMITS["B200"]
    h100 = ARCH_LIMITS["H100"]
    check(
        "ASP Ch6 Table 6-2: Warp size == 32, max threads/block == 1,024, max warps/block == 32",
        b200.warp_size == 32
        and b200.max_threads_per_block == 1024
        and b200.max_warps_per_block == 32,
    )
    check(
        "ASP Ch6 Table 6-3: Max resident warps/SM == 64, max resident threads/SM == 2,048, max active blocks/SM == 32",
        b200.max_resident_warps_per_sm == 64
        and b200.max_resident_threads_per_sm == 2048
        and b200.max_active_blocks_per_sm == 32,
    )
    check(
        "ASP Ch6 Table 6-5: 65,536 registers/SM (max 255/thread), 256 KB L1/SMEM (228 KB shared, 227 KB dynamic/block + 1 KB reserved)",
        b200.registers_per_sm == 65536
        and b200.max_registers_per_thread == 255
        and b200.l1_smem_total_kb_per_sm == 256
        and b200.max_shared_mem_kb_per_sm == 228
        and b200.max_dynamic_shared_mem_kb_per_block == 227
        and b200.cuda_reserved_shared_mem_kb_per_block == 1,
    )
    check(
        "ASP Ch6 Table 6-4 & V2 Ch2: L2 cache is 50 MB on H100 and 126 MB on B200; max grid dims (2147483647, 65535, 65535) & 128 concurrent grids",
        h100.l2_cache_mb == 50
        and b200.l2_cache_mb == 126
        and b200.max_grid_dim_x == 2_147_483_647
        and b200.max_grid_dim_y == 65_535
        and b200.max_concurrent_grids == 128,
    )

    # 3. Cross-vendor programming abstraction & scheduler tables (PHPC Ch 10 Tables 10.1 & 10.2)
    check(
        "PHPC Ch10 Table 10.1: OpenCL NDRange/Work Group/Subgroup/Work Item map to CUDA grid/block/warp(32)/thread",
        PROGRAMMING_ABSTRACTIONS["domain"]["cuda"] == "grid"
        and PROGRAMMING_ABSTRACTIONS["group"]["cuda"] == "block or thread block (CTA)"
        and PROGRAMMING_ABSTRACTIONS["subgroup"]["cuda"] == "warp (32)"
        and PROGRAMMING_ABSTRACTIONS["item"]["cuda"] == "thread",
    )
    check(
        "PHPC Ch10 Table 10.2: NVIDIA SM (64 active warps of 32, 32 blocks) vs AMD MI50 CU (40 wavefronts of 64, 40 work groups)",
        SCHEDULER_COMPARISON["NVIDIA_Volta_Ampere_Hopper_Blackwell"]["active_subgroups_per_cu"] == 64
        and SCHEDULER_COMPARISON["AMD_MI50"]["active_subgroups_per_cu"] == 40
        and SCHEDULER_COMPARISON["AMD_MI50"]["subgroup_size"] == 64,
    )

    # 4. 1D Kernel launch geometry & bounds check (ASP Ch 6 pp. 188-191)
    l_1m = calc_grid_launch_1d(1_000_000, 256)
    check(
        "ASP Ch6 p.188: N = 1,000,000 with threadsPerBlock = 256 launches 3,907 blocks (1,000,192 threads, 192 guarded by idx < N)",
        l_1m["blocks_per_grid"] == 3907
        and l_1m["warps_per_block"] == 8
        and l_1m["total_threads_launched"] == 1_000_192
        and l_1m["out_of_bounds_threads"] == 192,
    )
    l_63 = calc_grid_launch_1d(63, 64)
    check(
        "ASP Ch6 p.190: N = 63 on 2 warps (64 threads) leaves 1 out-of-bounds thread requiring if (idx < N) to avoid cudaErrorIllegalAddress",
        l_63["warps_per_block"] == 2
        and l_63["total_threads_launched"] == 64
        and l_63["out_of_bounds_threads"] == 1,
    )
    l_occ = calc_grid_launch_1d(10_000, 256, min_grid_size=600)
    check(
        "ASP Ch6 p.207: gridSize = max(minGridSize, ceil_div(N, bestBlockSize)) honors minGridSize when larger",
        l_occ["blocks_for_n"] == 40 and l_occ["blocks_per_grid"] == 600,
    )

    # 5. 1D/2D/3D Domain tile decomposition (PHPC Ch 10 Table 10.3, p. 320)
    t_1d = calc_domain_tile_decomposition((1_048_576,), (128,))
    t_2d_large = calc_domain_tile_decomposition((1024, 1024), (8, 16))
    t_2d_small = calc_domain_tile_decomposition((1024, 1024), (8, 8))
    t_3d = calc_domain_tile_decomposition((128, 128, 128), (4, 4, 8))
    check(
        "PHPC Ch10 Table 10.3: 1D 1,048,576 / 128 == 8,192 work groups; 2D 1024x1024 / 8x16 == 8,192 work groups (128x64)",
        t_1d["total_work_groups"] == 8192
        and t_2d_large["tile_size"] == 128
        and t_2d_large["num_tiles_per_dim"] == (128, 64)
        and t_2d_large["total_work_groups"] == 8192,
    )
    check(
        "PHPC Ch10 Table 10.3: 2D 1024x1024 / 8x8 == 16,384 work groups; 3D 128^3 / 4x4x8 == 16,384 work groups (32x32x16)",
        t_2d_small["total_work_groups"] == 16384
        and t_3d["tile_size"] == 128
        and t_3d["num_tiles_per_dim"] == (32, 32, 16)
        and t_3d["total_work_groups"] == 16384,
    )

    # 6. Worked SM Occupancy & Residency calculations (V2 Ch 6 & ASP Ch 6)
    occ_40 = calc_sm_occupancy(256, 40, 0)
    check(
        "V2 Ch6 worked example 1: 256 threads/block (8 warps) @ 40 regs/thread -> 6 blocks = 48 warps = 75.0% occupancy (register-limited)",
        occ_40["resident_blocks"] == 6
        and occ_40["resident_warps"] == 48
        and occ_40["occupancy_pct"] == 75.0
        and occ_40["limiting_resource"] == "REGISTERS",
    )
    occ_56 = calc_sm_occupancy(256, 56, 0)
    check(
        "V2 Ch6 worked example 2: 256 threads/block (8 warps) @ 56 regs/thread -> 4 blocks = 32 warps = 50.0% occupancy",
        occ_56["resident_blocks"] == 4
        and occ_56["resident_warps"] == 32
        and occ_56["occupancy_pct"] == 50.0
        and occ_56["limiting_resource"] == "REGISTERS",
    )
    occ_full = calc_sm_occupancy(256, 32, 0)
    check(
        "ASP Ch6 Table 6-3: 256 threads/block @ 32 regs/thread -> 8 blocks = 64 warps (2,048 threads) = 100.0% occupancy",
        occ_full["resident_blocks"] == 8
        and occ_full["resident_warps"] == 64
        and occ_full["resident_threads"] == 2048
        and occ_full["occupancy_pct"] == 100.0,
    )
    occ_1024_heavy = calc_sm_occupancy(1024, 48, 0)
    check(
        "V2 Ch3 customer scenario: 1,024-thread block @ 48 regs/thread fits only 1 block/SM (32 warps = 50.0% occupancy)",
        occ_1024_heavy["resident_blocks"] == 1 and occ_1024_heavy["occupancy_pct"] == 50.0,
    )
    occ_smem = calc_sm_occupancy(256, 24, 64 * 1024)
    check(
        "Shared-memory limit: 256 threads/block requesting 64 KB dynamic SMEM (+1 KB reserved = 65 KB) fits 3 blocks in 228 KB (24 warps = 37.5%)",
        occ_smem["resident_blocks"] == 3
        and occ_smem["resident_warps"] == 24
        and occ_smem["occupancy_pct"] == 37.5
        and occ_smem["limiting_resource"] == "SHARED_MEMORY",
    )
    occ_spill = calc_sm_occupancy(256, 260, 0)
    occ_smem_over = calc_sm_occupancy(256, 32, 228 * 1024)
    check(
        "ASP Ch6 Table 6-5: Flags >255 registers/thread and >227 KB dynamic shared memory/block",
        occ_spill["limiting_resource"] == "REGISTER_SPILL_EXCEEDS_255_PER_THREAD"
        and occ_smem_over["limiting_resource"] == "SHARED_MEM_EXCEEDS_227KB_BLOCK_LIMIT",
    )

    # 7. __launch_bounds__ validation (ASP Ch 6 p. 206)
    lb_warn = validate_launch_bounds(256, 16)
    lb_ok = validate_launch_bounds(256, 8)
    check(
        "ASP Ch6 p.206: __launch_bounds__(256, 16) requests 4,096 threads (>2,048 SM max), emits ptxas warning, and clamps to 8 blocks",
        lb_warn["requested_threads_per_sm"] == 4096
        and lb_warn["exceeds_sm_thread_limit"] is True
        and lb_warn["ptxas_warning_emitted"] is True
        and lb_warn["effective_blocks_per_sm"] == 8
        and lb_warn["effective_threads_per_sm"] == 2048,
    )
    check(
        "__launch_bounds__(256, 8) requests 2,048 threads within SM limit without warning and targets <=32 regs/thread",
        lb_ok["ptxas_warning_emitted"] is False
        and lb_ok["effective_blocks_per_sm"] == 8
        and lb_ok["max_regs_per_thread_target"] == 32,
    )

    # 8. Sequential vs Parallel benchmark & Compute Sanitizer (ASP Ch 6 Table 6-6 & pp. 207-208)
    seq = SEQ_VS_PAR_BENCHMARK["add_sequential"]
    par = SEQ_VS_PAR_BENCHMARK["add_parallel"]
    check(
        "ASP Ch6 Table 6-6: add_parallel (2.17 ms, 95% util, 38.7% occ, 100% warp eff) is 22.2x faster than add_sequential (48.21 ms, 3.1% warp eff)",
        round(seq["exec_time_ms"] / par["exec_time_ms"], 1) == 22.2
        and par["warp_exec_efficiency_pct"] == 100.0
        and seq["warp_exec_efficiency_pct"] == 3.1,
    )
    check(
        "ASP Ch6 pp.207-208: Compute Sanitizer suite includes memcheck, racecheck, initcheck, and synccheck",
        set(COMPUTE_SANITIZER_TOOLS.keys()) == {"memcheck", "racecheck", "initcheck", "synccheck"},
    )

    # 9. Nsight Compute Efficiency Gates: Divergence & Sector Amplification (V2 Ch 9)
    g_leaking = diagnose_kernel_efficiency_gates(19.4, 11.6)
    g_worst = diagnose_kernel_efficiency_gates(16.0, 32.0)
    g_ideal = diagnose_kernel_efficiency_gates(32.0, 4.0)
    check(
        "V2 Ch9 worked example: 19.4 active threads/inst == 60.62% lane efficiency & 11.6 sectors/req == 371.2 B (2.9x amplification; both gates leaking)",
        g_leaking["active_lane_efficiency_pct"] == 60.62
        and g_leaking["ideal_sectors_per_request"] == 4.0
        and g_leaking["transferred_bytes_per_warp"] == 371.2
        and g_leaking["byte_amplification_factor"] == 2.9
        and g_leaking["control_flow_gate_leaking"] is True
        and g_leaking["memory_coalescing_gate_leaking"] is True,
    )
    check(
        "V2 Ch9 worked example: 32 scattered sectors x 32 B transfers 1,024 B for 128 useful B (8.0x amplification) vs 4 coalesced sectors (1.0x)",
        g_worst["transferred_bytes_per_warp"] == 1024.0
        and g_worst["byte_amplification_factor"] == 8.0
        and g_ideal["byte_amplification_factor"] == 1.0
        and g_ideal["control_flow_gate_leaking"] is False
        and g_ideal["memory_coalescing_gate_leaking"] is False,
    )

    # 10. Negative / boundary checks
    raised = False
    try:
        calc_grid_launch_1d(1000, 2048)
    except ExecutionModelError:
        raised = True
    check("Rejects threads_per_block > 1,024 hardware limit", raised)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
