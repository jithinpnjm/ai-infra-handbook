#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.4: Tensor cores and numerical precision."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tensor_cores_precision import (
    BLACKWELL_TENSOR_BENCHMARKS,
    NUMERICAL_FORMATS,
    SM_EXECUTION_ENGINES,
    TensorPrecisionError,
    calc_tmem_tile_fit,
    check_tensor_core_eligibility,
    compare_matrix_precision_footprint,
    validate_2_to_4_structured_sparsity,
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
    print("=== Chapter 10.4 Lab: Tensor Cores and Numerical Precision ===")

    # 1. SM Execution Engine Specialization (nvidia-devops V2 Ch 4)
    check(
        "V2 Ch4: Distinguishes all 5 SM execution engines (CUDA Cores, Tensor Cores, RT Cores, LD/ST, SFU)",
        set(SM_EXECUTION_ENGINES.keys())
        == {"cuda_cores", "tensor_cores", "rt_cores", "ld_st_units", "sfu"},
    )
    check(
        "V2 Ch4: RT Cores target ray-tracing BVH traversal and are not AI GEMM accelerators",
        "BVH" in SM_EXECUTION_ENGINES["rt_cores"] and "not AI GEMMs" in SM_EXECUTION_ENGINES["rt_cores"],
    )

    # 2. Numerical Format Bit-Layouts (ASP Ch 9 pp. 308-311)
    tf32 = NUMERICAL_FORMATS["TF32"]
    fp32 = NUMERICAL_FORMATS["FP32"]
    fp16 = NUMERICAL_FORMATS["FP16"]
    bf16 = NUMERICAL_FORMATS["BF16"]
    check(
        "ASP Ch9 p.308: TF32 has 8-bit exponent (like FP32) and 10-bit mantissa (like FP16) = 19 active bits in 32-bit storage",
        tf32.exponent_bits == fp32.exponent_bits == 8
        and tf32.mantissa_bits == fp16.mantissa_bits == 10
        and tf32.active_compute_bits == 19
        and tf32.storage_bits == 32,
    )
    check(
        "ASP Ch9 p.309: BF16 has 8-bit exponent (matching FP32, no GradScaler needed) vs FP16 5-bit exponent (requires GradScaler)",
        bf16.exponent_bits == 8
        and bf16.mantissa_bits == 7
        and bf16.requires_loss_scaling_in_training is False
        and fp16.exponent_bits == 5
        and fp16.mantissa_bits == 10
        and fp16.requires_loss_scaling_in_training is True,
    )
    check(
        "FP8 E4M3 (4 exp, 3 mantissa) vs E5M2 (5 exp, 2 mantissa) both occupy 1 byte",
        NUMERICAL_FORMATS["FP8_E4M3"].exponent_bits == 4
        and NUMERICAL_FORMATS["FP8_E4M3"].mantissa_bits == 3
        and NUMERICAL_FORMATS["FP8_E5M2"].exponent_bits == 5
        and NUMERICAL_FORMATS["FP8_E5M2"].mantissa_bits == 2,
    )

    # 3. 128-Byte Cache-Line Element Density (ASP Ch 6 p. 210)
    check(
        "ASP Ch6 p.210: 128B memory transaction carries 32 FP32, 64 FP16/BF16, 128 FP8/INT8, or 256 NVFP4 values",
        fp32.elements_per_128b_line == 32
        and fp16.elements_per_128b_line == 64
        and bf16.elements_per_128b_line == 64
        and NUMERICAL_FORMATS["FP8_E4M3"].elements_per_128b_line == 128
        and NUMERICAL_FORMATS["INT8"].elements_per_128b_line == 128
        and NUMERICAL_FORMATS["NVFP4"].elements_per_128b_line == 256,
    )

    # 4. Worked [4096, 4096] Matrix Footprint Comparison (V2 Ch 4)
    m_fp16 = compare_matrix_precision_footprint(4096, 4096, "FP32", "FP16")
    m_fp8 = compare_matrix_precision_footprint(4096, 4096, "FP32", "FP8_E4M3")
    m_fp4 = compare_matrix_precision_footprint(4096, 4096, "FP32", "NVFP4")
    check(
        "V2 Ch4 worked example: [4096, 4096] matrix is 67.1 MB (67,108,864 B) in FP32 vs 33.6 MB (33,554,432 B) in FP16 (2.0x reduction)",
        m_fp16["bytes_a"] == 67_108_864
        and m_fp16["mb_decimal_a"] == 67.1
        and m_fp16["bytes_b"] == 33_554_432
        and m_fp16["mb_decimal_b"] == 33.6
        and m_fp16["bandwidth_reduction_factor"] == 2.0,
    )
    check(
        "ASP Ch9 p.310: [4096, 4096] matrix drops to 16.8 MB in FP8/INT8 (4.0x reduction vs FP32) and 8.4 MB in NVFP4 (8.0x reduction)",
        m_fp8["mb_decimal_b"] == 16.8
        and m_fp8["bandwidth_reduction_factor"] == 4.0
        and m_fp4["mb_decimal_b"] == 8.4
        and m_fp4["bandwidth_reduction_factor"] == 8.0,
    )

    # 5. Blackwell B200/B300 Specifications, NVFP4 Speedup & 1.8T MoE Benchmark (ASP Ch 2 & Ch 9)
    bm = BLACKWELL_TENSOR_BENCHMARKS
    check(
        "ASP Ch2 pp.24-26: Blackwell B200 has 2 x 104B = 208B transistors, 10 TB/s NV-HBI link, and 192 GB physical (180 GB usable) HBM3e",
        bm["b200_transistors_billions"] == 208.0
        and bm["b200_transistors_per_die_billions"] == 104.0
        and bm["b200_nv_hbi_bw_tbps"] == 10.0
        and bm["b200_hbm3e_physical_gb"] == 192.0
        and bm["b200_hbm3e_usable_gb"] == 180.0,
    )
    check(
        "ASP Ch9 p.310: B200 dense NVFP4 is 10 PFLOPS vs 80 TFLOPS dense FP32 (125x); B300 Ultra dense NVFP4 is 15 PFLOPS (1.5x B200)",
        (bm["b200_dense_nvfp4_pflops"] * 1000.0) / bm["b200_dense_fp32_tflops"] == 125.0
        and bm["b300_dense_nvfp4_pflops"] / bm["b200_dense_nvfp4_pflops"] == 1.5,
    )
    check(
        "ASP Ch2 pp.27,31: 1.8T MoE improves from 3.4 tok/s/GPU (>5,000 ms TTFT) on H100 to 150 tok/s/GPU (50 ms TTFT) on GB200 NVL72",
        bm["moe_1_8t_h100_tok_per_s_per_gpu"] == 3.4
        and bm["moe_1_8t_gb200_nvl72_tok_per_s_per_gpu"] == 150.0
        and bm["moe_1_8t_h100_ttft_ms"] / bm["moe_1_8t_gb200_nvl72_ttft_ms"] == 100.0,
    )
    check(
        "ASP Ch9 p.311 & Table 9-1: DP4A executes 4 INT8 MACs/inst; CUTLASS matches hand-tuned MMA at 98% Tensor Core utilization",
        bm["dp4a_int8_macs_per_inst"] == 4.0
        and bm["cutlass_vs_hand_mma_tensor_util_pct"] == 98.0,
    )

    # 6. 2:4 Structured Sparsity Validator (ASP Ch 9 pp. 302-304)
    w_valid_16 = [
        1.2, 0.0, -0.5, 0.0,
        0.0, 2.1, 0.0, 0.8,
        0.0, 0.0, 3.4, -1.1,
        0.7, 0.0, 0.0, 0.9,
    ]
    w_invalid_16 = [
        1.2, 0.3, -0.5, 0.0,  # quad 0 has 3 nonzeros!
        0.0, 2.1, 0.0, 0.8,
        0.0, 0.0, 3.4, -1.1,
        0.7, 0.0, 0.0, 0.9,
    ]
    sp_ok = validate_2_to_4_structured_sparsity(w_valid_16)
    sp_bad = validate_2_to_4_structured_sparsity(w_invalid_16)
    check(
        "ASP Ch9 p.303: Valid 2:4 sparse 16-element chunk has 8 nonzeros (2 per quad, 50% density) and 2.0x Sparse Tensor Core speedup",
        sp_ok["valid_2_to_4"] is True
        and sp_ok["total_nonzeros"] == 8
        and sp_ok["density_pct"] == 50.0
        and sp_ok["theoretical_sparse_speedup"] == 2.0,
    )
    check(
        "ASP Ch9 p.303: Flags quad with 3 of 4 nonzeros as violating 2:4 structured sparsity",
        sp_bad["valid_2_to_4"] is False and sp_bad["violating_quad_indices"] == [0],
    )

    # 7. Blackwell 256 KB per-SM TMEM Tile Sizing (ASP Ch 9 p. 314)
    t_fp16_max = calc_tmem_tile_fit(256, 512, 2.0, 256)
    t_fp32_max = calc_tmem_tile_fit(256, 256, 4.0, 256)
    t_fp4_tile = calc_tmem_tile_fit(256, 256, 0.5, 256)
    t_over = calc_tmem_tile_fit(512, 512, 2.0, 256)
    check(
        "ASP Ch9 p.314: 256x512 FP16 tile (2B) == 256.0 KiB and 256x256 FP32 tile (4B) == 256.0 KiB (100% of 256 KB per-SM TMEM)",
        t_fp16_max["tile_kib"] == 256.0
        and t_fp16_max["fits_in_tmem"] is True
        and t_fp16_max["utilization_pct"] == 100.0
        and t_fp32_max["tile_kib"] == 256.0
        and t_fp32_max["fits_in_tmem"] is True,
    )
    check(
        "ASP Ch9 p.310: 256x256 NVFP4 tile (0.5B) takes only 32.0 KiB (fitting 8 tiles in 256 KB TMEM); 512x512 FP16 exceeds TMEM",
        t_fp4_tile["tile_kib"] == 32.0
        and t_fp4_tile["max_concurrent_tiles_in_tmem"] == 8
        and t_over["fits_in_tmem"] is False,
    )

    # 8. Tensor Core Eligibility & SM Pipeline Routing (V2 Ch 4)
    el_fp32 = check_tensor_core_eligibility(4096, 4096, 4096, "FP32", 92.0, 22.0, 0.0)
    el_misaligned = check_tensor_core_eligibility(32, 4096, 4097, "FP16", 91.0, 18.0, 2.0)
    el_starved = check_tensor_core_eligibility(4096, 4096, 4096, "BF16", 88.0, 94.0, 75.0)
    el_good = check_tensor_core_eligibility(4096, 4096, 4096, "FP8_E4M3", 95.0, 60.0, 88.0)
    check(
        "V2 Ch4: Flags strict FP32 as scalar CUDA Core path when SM is 92% busy and Tensor Pipe is 0%",
        el_fp32["tensor_core_eligible"] is False
        and el_fp32["pipeline_diagnosis"] == "GENERAL_CUDA_CORES_DOMINATE_TENSOR_CORES_IDLE",
    )
    check(
        "V2 Ch4 p.293: Flags odd dimension K=4097 in FP16 as failing 8-element (16-byte) Tensor Core alignment",
        el_misaligned["tensor_core_eligible"] is False
        and el_misaligned["required_element_alignment"] == 8
        and el_misaligned["misaligned_dimensions"] == ["K"],
    )
    check(
        "V2 Ch4 Fig 2.4.1: Distinguishes HBM-starved Tensor Cores (mem=94%) from compute-engaged FP8 Tensor Cores (16-elem aligned)",
        el_starved["pipeline_diagnosis"] == "TENSOR_CORES_ACTIVE_BUT_HBM_BANDWIDTH_STARVED"
        and el_good["tensor_core_eligible"] is True
        and el_good["required_element_alignment"] == 16
        and el_good["pipeline_diagnosis"] == "TENSOR_CORE_COMPUTE_ENGAGED",
    )

    # Additional alignment & CUTLASS resource checks
    el_fp4_align = check_tensor_core_eligibility(64, 4096, 4096, "NVFP4", 95.0, 50.0, 90.0)
    el_tf32_align = check_tensor_core_eligibility(64, 4096, 4096, "TF32", 95.0, 50.0, 90.0)
    check(
        "16-byte tile alignment requires multiples of 4 for TF32 (4B), 8 for FP16/BF16 (2B), 16 for FP8/INT8 (1B), and 32 for NVFP4 (0.5B)",
        el_tf32_align["required_element_alignment"] == 4
        and el_fp4_align["required_element_alignment"] == 32
        and el_fp4_align["tensor_core_eligible"] is True,
    )
    el_small_batch = check_tensor_core_eligibility(1, 4096, 4096, "FP8_E4M3", 40.0, 80.0, 20.0)
    check(
        "ASP Ch9 p.309: Batch size M=1 on FP8 warns that fixed launch/conversion overhead is not amortized",
        any("Small batch/M dimension" in r for r in el_small_batch["reasons"]),
    )

    # 9. Negative / boundary checks
    raised_sp = False
    try:
        validate_2_to_4_structured_sparsity([1.0, 0.0, 2.0])
    except TensorPrecisionError:
        raised_sp = True
    check("Rejects non-multiple-of-4 array length in 2:4 sparsity validator", raised_sp)

    raised_fmt = False
    try:
        compare_matrix_precision_footprint(1024, 1024, "FP32", "FP128")
    except TensorPrecisionError:
        raised_fmt = True
    check("Rejects unknown numerical format", raised_fmt)

    raised_tmem = False
    try:
        calc_tmem_tile_fit(0, 256, 2.0)
    except TensorPrecisionError:
        raised_tmem = True
    check("Rejects non-positive TMEM tile dimensions", raised_tmem)

    raised_gemm = False
    try:
        check_tensor_core_eligibility(-1, 4096, 4096, "FP16")
    except TensorPrecisionError:
        raised_gemm = True
    check("Rejects non-positive GEMM dimensions", raised_gemm)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
