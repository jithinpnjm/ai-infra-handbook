#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.5: The roofline model and performance modelling."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from roofline_model import (
    HARDWARE_ROOFLINES,
    RooflineModelError,
    calc_gemm_arithmetic_intensity,
    calc_machine_balance_words,
    classify_gpu_workload_bottleneck,
    compare_kernel_fusion_and_cluster_multicast,
    evaluate_roofline_point,
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
    print("=== Chapter 10.5 Lab: The Roofline Model and Performance Modelling ===")

    # 1. Hardware Ridge Points (ASP Ch 6 p. 209 & V2 Ch 11)
    b200_fp32 = HARDWARE_ROOFLINES["B200_FP32_SCALAR"]
    h100_fp16 = HARDWARE_ROOFLINES["H100_SXM_FP16_TC"]
    h200_fp16 = HARDWARE_ROOFLINES["H200_SXM_FP16_TC"]
    b200_fp4 = HARDWARE_ROOFLINES["B200_NVFP4_TC"]
    check(
        "ASP Ch6 p.209: Blackwell B200 FP32 scalar ridge point (80 TFLOPS / 8 TB/s) == 10.0 FLOPs/byte",
        b200_fp32.ridge_point_flops_per_byte == 10.0,
    )
    check(
        "V2 Ch11 worked example: H100 SXM FP16 Tensor Core ridge point (989 TFLOPS / 3.35 TB/s) == 295.2 FLOPs/byte (~295)",
        h100_fp16.ridge_point_flops_per_byte == 295.2,
    )
    check(
        "H200 SXM FP16 ridge point (989 / 4.80 == 206.0) is lower than H100; B200 NVFP4 ridge point (10,000 / 8.0) == 1,250.0 FLOPs/byte",
        h200_fp16.ridge_point_flops_per_byte == 206.0
        and b200_fp4.ridge_point_flops_per_byte == 1250.0,
    )

    # 2. Vector-Add & Precision Shifts on the Roofline (ASP Ch 6 pp. 209-210)
    vec_fp32 = evaluate_roofline_point(1.0, 12.0, 80.0, 8.0)
    vec_fp16 = evaluate_roofline_point(1.0, 6.0, 80.0, 8.0)
    vec_fp8 = evaluate_roofline_point(1.0, 3.0, 80.0, 8.0)
    check(
        "ASP Ch6 p.209: FP32 vector add (1 FLOP / 12 B == 0.0833 FLOPs/B) is MEMORY_BOUND (>100x below 10.0 ridge point)",
        vec_fp32["arithmetic_intensity_flops_per_byte"] == 0.0833
        and vec_fp32["regime"] == "MEMORY_BOUND"
        and vec_fp32["ratio_to_ridge"] < 0.01,
    )
    check(
        "ASP Ch6 p.210: Halving precision from FP32 (12 B) to FP16 (6 B) and FP8 (3 B) doubles and quadruples arithmetic intensity",
        round(vec_fp16["arithmetic_intensity_flops_per_byte"] / vec_fp32["arithmetic_intensity_flops_per_byte"], 1) == 2.0
        and round(vec_fp8["arithmetic_intensity_flops_per_byte"] / vec_fp32["arithmetic_intensity_flops_per_byte"], 1) == 4.0,
    )

    # 3. Non-contiguous Cache Line Utilization (PHPC Ch 3 §3.1 p. 55)
    rf_strided = evaluate_roofline_point(1.0, 1.0, 80.0, 8.0, cache_line_utilization=0.125)
    check(
        "PHPC Ch3 §3.1: Using 1 of 8 cache-line values (12.5%) drops effective bandwidth from 8.0 to 1.0 TB/s and raises ridge point to 80.0",
        rf_strided["effective_bw_tbps"] == 1.0
        and rf_strided["ridge_point_flops_per_byte"] == 80.0,
    )

    # 4. Machine Balance in FLOPs/word (PHPC Ch 3 §3.2.5 p. 61)
    mb_theo = calc_machine_balance_words(236.8, 34.1, 8)
    mb_emp = calc_machine_balance_words(264.4, 22.0, 8)
    check(
        "PHPC Ch3 p.61: Theoretical machine balance (236.8 GFLOPS / 34.1 GiB/s * 8 B) == 56 FLOPs/word; Empirical STREAM == 96 FLOPs/word",
        mb_theo["flops_per_word_rounded"] == 56
        and mb_emp["flops_per_word_rounded"] == 96,
    )

    # 5. GEMM Batch Size vs Ridge Point & Quantization (V17 Ch 3 & V2 Ch 11)
    gemm_b1_fp16 = calc_gemm_arithmetic_intensity(1, 4096, 4096, 2.0)
    gemm_b1_int8 = calc_gemm_arithmetic_intensity(1, 4096, 4096, 1.0)
    gemm_b512_fp16 = calc_gemm_arithmetic_intensity(512, 4096, 4096, 2.0)
    rf_b1 = evaluate_roofline_point(gemm_b1_fp16["total_flops"], gemm_b1_fp16["total_bytes"], 989.0, 3.35)
    rf_b512 = evaluate_roofline_point(gemm_b512_fp16["total_flops"], gemm_b512_fp16["total_bytes"], 989.0, 3.35)
    check(
        "V17 Ch3 & V2 Ch11: Batch=1 [1,4096]x[4096,4096] FP16 GEMM has intensity ~1.0 FLOP/B (MEMORY_BOUND at 3.35 TFLOPS vs 989 peak)",
        gemm_b1_fp16["exact_intensity_flops_per_byte"] == 1.0
        and rf_b1["regime"] == "MEMORY_BOUND"
        and rf_b1["attainable_tflops"] == 3.348,
    )
    check(
        "V17 Ch3 customer scenario: Quantizing Batch=1 weights from FP32 (4B) to INT8 (1B) quadruples arithmetic intensity (~0.5 -> ~2.0 FLOPs/B)",
        calc_gemm_arithmetic_intensity(1, 4096, 4096, 4.0)["exact_intensity_flops_per_byte"] == 0.5
        and gemm_b1_int8["exact_intensity_flops_per_byte"] == 2.0,
    )
    check(
        "Batch=512 [512,4096]x[4096,4096] FP16 GEMM reaches ~409.6 FLOPs/B (>295.2 H100 ridge point -> COMPUTE_BOUND at 989 TFLOPS)",
        gemm_b512_fp16["exact_intensity_flops_per_byte"] == 409.6
        and rf_b512["regime"] == "COMPUTE_BOUND"
        and rf_b512["attainable_tflops"] == 989.0,
    )

    # 6. Kernel Fusion (L2 Norm) & Thread Block Cluster TMA Multicast (ASP Ch 9 pp. 297-301)
    fus_4 = compare_kernel_fusion_and_cluster_multicast(3, 12, 4, cluster_ctas=4)
    fus_16 = compare_kernel_fusion_and_cluster_multicast(3, 12, 4, cluster_ctas=16)
    check(
        "ASP Ch9 pp.299-301: Fusing 3-pass L2 norm cuts global traffic from 36 B to 12 B/elem (3.0x reduction) and lifts intensity to 0.25-0.3333 FLOPs/B",
        fus_4["unfused_bytes_per_elem"] == 36
        and fus_4["fused_bytes_per_elem"] == 12
        and fus_4["traffic_reduction_factor"] == 3.0
        and fus_4["fused_conservative_3flop_intensity"] == 0.25
        and fus_4["fused_4flop_intensity"] == 0.3333,
    )
    check(
        "ASP Ch9 p.297: 2x2 Thread Block Cluster (4 CTAs) gives 4.0x TMA multicast reuse (portable); 16 CTAs gives 16.0x and requires non-portable attr",
        fus_4["cluster_multicast_reuse_factor"] == 4.0
        and fus_4["requires_nonportable_cluster_attr"] is False
        and fus_16["cluster_multicast_reuse_factor"] == 16.0
        and fus_16["requires_nonportable_cluster_attr"] is True,
    )

    # 7. 6-Category GPU Bottleneck Classifier (V2 Ch 11 & Ch 12)
    b_host = classify_gpu_workload_bottleneck(False, 4.0, 2.0, 2.0, 1.0)
    b_mem_bw = classify_gpu_workload_bottleneck(True, 94.0, 91.0, 85.0, 30.0, "N/A")
    b_uncoal = classify_gpu_workload_bottleneck(True, 20.0, 90.0, 22.0, 5.0, "N/A")
    b_scalar = classify_gpu_workload_bottleneck(True, 92.0, 22.0, 20.0, 2.0, "N/A")
    b_compute = classify_gpu_workload_bottleneck(True, 95.0, 55.0, 50.0, 88.0, "N/A")
    b_throt = classify_gpu_workload_bottleneck(True, 95.0, 50.0, 45.0, 80.0, "SW Power Cap")
    b_strag = classify_gpu_workload_bottleneck(
        True, 90.0, 60.0, 55.0, 75.0, "N/A", rank_step_times_ms=(48.0, 51.0, 142.0, 139.0)
    )
    check(
        "V2 Ch12 Case A: sm=4%, mem=2% classifies as HOST_INPUT_OR_LAUNCH_LATENCY_BOUND",
        b_host["category"] == "HOST_INPUT_OR_LAUNCH_LATENCY_BOUND",
    )
    check(
        "V2 Ch11 p.326: sm=94%, mem=91%, dram_peak=85%, throttle=N/A classifies as MEMORY_BANDWIDTH_BOUND",
        b_mem_bw["category"] == "MEMORY_BANDWIDTH_BOUND",
    )
    check(
        "V2 Ch8 & Ch11: High mem% (90%) with low dram_pct_of_peak (22%) classifies as MEMORY_TRANSACTION_UNCOALESCED_OR_LATENCY_BOUND",
        b_uncoal["category"] == "MEMORY_TRANSACTION_UNCOALESCED_OR_LATENCY_BOUND",
    )
    check(
        "V2 Ch4 & Ch11: High sm% (92%) with low tensor_pipe_pct (2%) classifies as SCALAR_COMPUTE_OR_DIVERGENCE_BOUND_TENSOR_IDLE",
        b_scalar["category"] == "SCALAR_COMPUTE_OR_DIVERGENCE_BOUND_TENSOR_IDLE",
    )
    check(
        "High sm% (95%) + high tensor_pipe_pct (88%) classifies as TENSOR_COMPUTE_BOUND; active throttle reason flags THERMAL_OR_POWER_THROTTLED",
        b_compute["category"] == "TENSOR_COMPUTE_BOUND"
        and b_throt["category"] == "THERMAL_OR_POWER_THROTTLED",
    )
    check(
        "V2 Ch11 p.340: Rank step times (48, 51, 142, 139 ms) detect 2.96x straggler and classify as MULTI_GPU_COMMUNICATION_OR_STRAGGLER_BOUND",
        b_strag["has_rank_straggler"] is True
        and b_strag["rank_straggler_ratio"] == 2.96
        and b_strag["category"] == "MULTI_GPU_COMMUNICATION_OR_STRAGGLER_BOUND",
    )

    # 8. Additional energy & negative/boundary checks
    # PHPC Ch 3 p. 64: CloverLeaf parallel vs serial energy reduction
    e_serial = 212747.7787
    e_parallel = 151590.4909
    dram_serial = 49518.7395
    dram_parallel = 37986.9191
    check(
        "PHPC Ch3 p.64: Parallel CloverLeaf reduces total energy by 28.75% (28.7% truncated in book) and DRAM energy by 23.29% (23.2% truncated)",
        round(((e_serial - e_parallel) / e_serial) * 100.0, 2) == 28.75
        and round(((dram_serial - dram_parallel) / dram_serial) * 100.0, 2) == 23.29,
    )

    # B200 BF16 Tensor Core ridge point check (2,250 TFLOPS / 8.0 TB/s == 281.2 FLOPs/B)
    b200_bf16 = HARDWARE_ROOFLINES["B200_BF16_TC"]
    check(
        "B200 BF16 Tensor Core ridge point (2,250 TFLOPS / 8.0 TB/s) == 281.2 FLOPs/byte",
        b200_bf16.ridge_point_flops_per_byte == 281.2,
    )

    raised_cta = False
    try:
        compare_kernel_fusion_and_cluster_multicast(3, 12, 4, cluster_ctas=32)
    except RooflineModelError:
        raised_cta = True
    check("Rejects Thread Block Cluster size > 16 CTAs", raised_cta)

    raised_util = False
    try:
        evaluate_roofline_point(10.0, 10.0, 100.0, 3.0, cache_line_utilization=0.0)
    except RooflineModelError:
        raised_util = True
    check("Rejects zero cache_line_utilization", raised_util)

    raised_pct = False
    try:
        classify_gpu_workload_bottleneck(True, 120.0, 50.0, 50.0, 50.0)
    except RooflineModelError:
        raised_pct = True
    check("Rejects utilization percentage > 100%", raised_pct)

    raised_mb = False
    try:
        calc_machine_balance_words(200.0, 30.0, bytes_per_word=6)
    except RooflineModelError:
        raised_mb = True
    check("Rejects invalid word byte size in machine balance calculator", raised_mb)

    raised_gemm = False
    try:
        calc_gemm_arithmetic_intensity(0, 4096, 4096, 2.0)
    except RooflineModelError:
        raised_gemm = True
    check("Rejects non-positive GEMM batch size", raised_gemm)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
