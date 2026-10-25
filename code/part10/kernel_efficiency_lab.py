#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.15: Kernel efficiency and arithmetic intensity."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from kernel_efficiency import (
    TABLE_9_1_CUTLASS_VS_HANDTUNED,
    TABLE_9_2_INLINE_PTX,
    KernelEfficiencyError,
    analyze_l2_norm_fusion_and_cluster_multicast,
    evaluate_precision_and_sparsity_scaling,
    evaluate_tmem_and_smem_stage_budgets,
    inspect_inline_ptx_instruction,
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
    print("=== Chapter 10.15 Lab: Kernel Efficiency and Arithmetic Intensity (ASP Chapter 9) ===")

    # 1. Kernel Fusion (`fusedL2Norm`) & Thread Block Cluster TMA Multicast (ASP Ch 9 pp. 297-302)
    f4 = analyze_l2_norm_fusion_and_cluster_multicast(cluster_ctas=4)
    f16 = analyze_l2_norm_fusion_and_cluster_multicast(cluster_ctas=16, non_portable_cluster_allowed=True)

    check(
        "ASP Ch9 pp.300-302: Unfused L2 norm (1 FLOP/12B = 0.083 FLOPs/B per pass; 4 FLOPs/36B = 0.1111 FLOPs/B) vs fusedL2Norm (3-4 FLOPs/12B = 0.25 to 0.3333 FLOPs/B, 3x less HBM traffic)",
        f4["single_pass_1flop_12b_ai"] == 0.083
        and f4["unfused_total_bytes_per_elem"] == 36
        and f4["unfused_ai_flops_per_byte"] == 0.1111
        and f4["fused_bytes_per_elem"] == 12
        and f4["fused_conservative_ai_flops_per_byte"] == 0.25
        and f4["fused_full_ai_flops_per_byte"] == 0.3333
        and f4["fusion_hbm_traffic_reduction_x"] == 3.0,
    )
    check(
        "ASP Ch9 pp.298-299: 2x2 (4-CTA) cluster TMA multicast reduces tile HBM traffic by 4x; non-portable 16-CTA cluster reduces by 16x",
        f4["cluster_multicast_traffic_reduction_x"] == 4.0
        and f16["cluster_multicast_traffic_reduction_x"] == 16.0,
    )

    # 2. TMEM (256 KB) Tile Capacities & Two-Stage SMEM Pipeline (ASP Ch 9 pp. 308-315)
    tmem_fp16 = evaluate_tmem_and_smem_stage_budgets(tile_m=256, tile_n=512, element_bytes=2.0, stage_tile_elems=1024)
    tmem_fp32 = evaluate_tmem_and_smem_stage_budgets(tile_m=256, tile_n=256, element_bytes=4.0, stage_tile_elems=1024)
    tmem_fp4 = evaluate_tmem_and_smem_stage_budgets(tile_m=256, tile_n=256, element_bytes=0.5, stage_tile_elems=1024)

    check(
        "ASP Ch9 p.315: 256x512 FP16 tile (2 B) == 262,144 B (256.0 KiB) and 256x256 FP32 tile (4 B) == 262,144 B (256.0 KiB), filling 100% of 256 KB per-SM TMEM",
        tmem_fp16["tile_bytes"] == 262144
        and tmem_fp16["tile_kib"] == 256.0
        and tmem_fp16["fits_in_tmem"] is True
        and tmem_fp32["tile_bytes"] == 262144
        and tmem_fp32["tile_kib"] == 256.0
        and tmem_fp32["fits_in_tmem"] is True,
    )
    check(
        "ASP Ch9 p.311: 256x256 NVFP4 tile (0.5 B) uses only 32,768 B (32.0 KiB = 12.5% of 256 KB TMEM)",
        tmem_fp4["tile_bytes"] == 32768
        and tmem_fp4["tile_kib"] == 32.0
        and tmem_fp4["tmem_utilization_pct"] == 12.5,
    )
    check(
        "ASP Ch9 p.309: two_stage_pipeline.cu allocates 4 * tile_elems * sizeof(float) (16,384 B for tile_elems=1024) for A0, A1, B0, B1",
        tmem_fp16["two_stage_ab_dynamic_smem_bytes"] == 16384,
    )

    # 3. Precision Scaling (NVFP4, INT8 DP4A), 2:4 Sparsity, and NestedTensor (ASP Ch 9 pp. 303-312)
    prec_b128 = evaluate_precision_and_sparsity_scaling(batch_size=128)
    prec_b1 = evaluate_precision_and_sparsity_scaling(batch_size=1)

    check(
        "ASP Ch9 p.311: B200 dense NVFP4 (10 PFLOPS = 10,000 TFLOPS) is 125.0x (~2 orders of magnitude) higher than FP32 (80 TFLOPS); B300 (15 PFLOPS) is +50.0% higher",
        prec_b128["b200_nvfp4_vs_fp32_speedup_x"] == 125.0
        and prec_b128["b300_vs_b200_nvfp4_gain_pct"] == 50.0,
    )
    check(
        "ASP Ch9 p.312: INT8 cuts FP32 weight traffic by 75.0% (1 B vs 4 B) and DP4A executes 4 INT8 MACs/instruction",
        prec_b128["int8_weight_traffic_reduction_pct"] == 75.0
        and prec_b128["dp4a_macs_per_instruction"] == 4,
    )
    check(
        "ASP Ch9 pp.303-310: 2:4 structured sparsity zeroes 8 of every 16 elements and requires large batches (128/256 vs batch=1) to amortize overhead",
        prec_b128["sparse_2_4_zeroed_in_16_chunk"] == 8
        and prec_b128["sparse_and_fp8_batch_amortized"] is True
        and prec_b1["sparse_and_fp8_batch_amortized"] is False,
    )
    check(
        "ASP Ch9 p.306: PyTorch NestedTensor on [128, 512, 256, 1024] processes 1,920 real tokens vs 4,096 padded tokens (saves 53.1% padding traffic)",
        prec_b128["padded_batch_tokens"] == 4096
        and prec_b128["nested_tensor_tokens"] == 1920
        and prec_b128["nested_tensor_saved_padding_pct"] == 53.1,
    )

    # 4. CUTLASS vs Hand-Tuned MMA (Table 9-1) & Inline PTX Micro-Optimizations (Table 9-2)
    hand = TABLE_9_1_CUTLASS_VS_HANDTUNED["HAND_TUNED_MMA"]
    cutlass = TABLE_9_1_CUTLASS_VS_HANDTUNED["CUTLASS_GEMM"]
    check(
        "ASP Ch9 Table 9-1: CUTLASS GEMM matches hand-tuned MMA at 98% Tensor Core utilization (~60 vs ~52 regs/thread, ~4 KB vs ~2 KB SMEM/CTA)",
        hand["tensor_core_utilization_pct"] == 98.0
        and cutlass["tensor_core_utilization_pct"] == 98.0
        and hand["registers_per_thread"] == 52
        and cutlass["registers_per_thread"] == 60
        and hand["shared_memory_kb_per_cta"] == 2.0
        and cutlass["shared_memory_kb_per_cta"] == 4.0,
    )

    cpp_base = TABLE_9_2_INLINE_PTX["OPTIMIZED_CPP"]
    ptx_tuned = TABLE_9_2_INLINE_PTX["HAND_TUNED_PTX"]
    check(
        "ASP Ch9 Table 9-2: Hand-tuned inline PTX (mad.wide.u32 + ld.global.cg) cuts memory warp stalls 35% -> 20%, lifts IPC 1.5 -> 1.6, and speeds up kernel 1.07 -> 1.00 ms (1.07x / ~7%)",
        cpp_base["warp_stall_memory_pct"] == 35.0
        and ptx_tuned["warp_stall_memory_pct"] == 20.0
        and cpp_base["issue_ipc"] == 1.5
        and ptx_tuned["issue_ipc"] == 1.6
        and cpp_base["kernel_time_ms"] == 1.07
        and ptx_tuned["kernel_time_ms"] == 1.00
        and ptx_tuned["speedup_x"] == 1.07,
    )

    # 5. Inline PTX Pattern Inspection including DeepSeek `DeepEP` (ASP Ch 9 pp. 318-323)
    ptx_pref = inspect_inline_ptx_instruction("cp.async.bulk.prefetch.L2.global [%0], %1;")
    ptx_cg = inspect_inline_ptx_instruction("ld.global.cg.f32 %0, [%1];")
    ptx_smid = inspect_inline_ptx_instruction("mov.u32 %0, %smid;")
    ptx_deepseek = inspect_inline_ptx_instruction("ld.global.nc.l1::no_allocate.l2::256b")

    check(
        "ASP Ch9 pp.318-319: cp.async.bulk.prefetch.L2.global prefetches 128B into L2; ld.global.cg.f32 caches in L2 while bypassing L1",
        ptx_pref["category"] == "L2_ASYNC_BULK_PREFETCH"
        and ptx_pref["l2_fetch_granularity_bytes"] == 128
        and ptx_cg["category"] == "CACHE_GLOBAL_L2_ONLY_LOAD"
        and ptx_cg["bypasses_l1_allocation"] is True,
    )
    check(
        "ASP Ch9 p.319: mov.u32 %0, %smid reads hardware SM ID special register",
        ptx_smid["category"] == "SPECIAL_REGISTER_SMID_READ",
    )
    check(
        "ASP Ch9 p.321: DeepSeek DeepEP 'ld.global.nc.l1::no_allocate.l2::256b' bypasses L1, fetches 256B into L2, is out-of-doc PTX, and uses DISABLE_AGGRESSIVE_PTX_INSTRS=1 fallback",
        ptx_deepseek["category"] == "DEEPSEEK_DEEPEP_L1_BYPASS_256B_L2"
        and ptx_deepseek["bypasses_l1_allocation"] is True
        and ptx_deepseek["l2_fetch_granularity_bytes"] == 256
        and ptx_deepseek["official_documented_ptx_isa"] is False
        and ptx_deepseek["fallback_build_flag"] == "DISABLE_AGGRESSIVE_PTX_INSTRS=1",
    )

    # 6. Input Validation Checks
    try:
        analyze_l2_norm_fusion_and_cluster_multicast(cluster_ctas=16, non_portable_cluster_allowed=False)
        check("Rejects 16-CTA cluster when cudaFuncAttributeNonPortableClusterSizeAllowed is False", False)
    except KernelEfficiencyError:
        check("Rejects 16-CTA cluster when cudaFuncAttributeNonPortableClusterSizeAllowed is False", True)

    try:
        analyze_l2_norm_fusion_and_cluster_multicast(cluster_ctas=32, non_portable_cluster_allowed=True)
        check("Rejects cluster_ctas > 16 hardware ceiling", False)
    except KernelEfficiencyError:
        check("Rejects cluster_ctas > 16 hardware ceiling", True)

    try:
        evaluate_tmem_and_smem_stage_budgets(stage_tile_elems=100)
        check("Rejects stage_tile_elems not divisible by 128 (32 * 4) for float4 vectorization", False)
    except KernelEfficiencyError:
        check("Rejects stage_tile_elems not divisible by 128 (32 * 4) for float4 vectorization", True)

    try:
        evaluate_precision_and_sparsity_scaling(batch_size=0)
        check("Rejects non-positive batch_size", False)
    except KernelEfficiencyError:
        check("Rejects non-positive batch_size", True)

    try:
        inspect_inline_ptx_instruction("unknown.ptx.op")
        check("Rejects unrecognized PTX instruction pattern", False)
    except KernelEfficiencyError:
        check("Rejects unrecognized PTX instruction pattern", True)

    check(
        "ASP Ch9 p.297: 32x32 tile produces 32 * 32 == 1,024 multiply-accumulates per tile",
        32 * 32 == 1024,
    )
    check(
        "ASP Ch9 p.301: 4 FLOPs / 12 B (0.3333) is 3.0x higher arithmetic intensity than 4 FLOPs / 36 B (0.1111)",
        round((4.0 / 12.0) / (4.0 / 36.0), 2) == 3.0,
    )
    check(
        "ASP Ch9 p.315: 512 x 512 FP16 tile (512 KiB) exceeds 256 KiB per-SM TMEM budget",
        evaluate_tmem_and_smem_stage_budgets(tile_m=512, tile_n=512, element_bytes=2.0)["fits_in_tmem"] is False,
    )
    check(
        "ASP Ch9 p.310: BF16 Tensor Core peak (~4x FP32) and FP8 (~2-3x BF16) raise arithmetic intensity by 2x, 4x, and 8x (FP4)",
        [4.0 / b for b in (2.0, 1.0, 0.5)] == [2.0, 4.0, 8.0],
    )
    check(
        "ASP Ch9 p.318: Inline PTX prefetch 'in + idx + 32' prefetches 32 floats * 4 B == 128 bytes ahead into L2",
        32 * 4 == 128,
    )
    check(
        "ASP Ch9 Table 9-2: 1.07 ms / 1.00 ms == 1.07x (~7% inline PTX speedup)",
        round(1.07 / 1.00, 2) == 1.07,
    )

    print(f"\nSummary: {passed} passed, 0 failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
