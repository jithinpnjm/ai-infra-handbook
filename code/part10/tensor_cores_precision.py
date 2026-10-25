#!/usr/bin/env python3
"""Chapter 10.4 model: Tensor Cores and Numerical Precision.

Encodes the verifiable format bit-layouts, 128-byte transaction densities,
weight footprints, Blackwell/Hopper Tensor Core & Transformer Engine metrics,
2:4 structured sparsity validators, and TMEM/CUTLASS tile calculations from:
- AI Systems Performance Engineering (ASP) Chapter 2 (pp. 24-30), Chapter 6 (p. 210),
  and Chapter 9 (pp. 295-318, Table 9-1):
  Numerical bit-layouts (FP64, FP32, TF32, FP16, BF16, FP8 E4M3/E5M2, INT8, NVFP4),
  128-byte cache-line element density (32 FP32, 64 FP16/BF16, 128 FP8/INT8, 256 FP4),
  Blackwell B200 dense NVFP4 (10 PFLOPS vs 80 TFLOPS FP32 = 125x) & B300 (15 PFLOPS),
  1.8T MoE inference benchmark (H100 3.4 tok/s/GPU @ >5s TTFT vs GB200 NVL72 150 tok/s/GPU @ 50ms TTFT),
  INT8 DP4A (4 MACs/inst) vs FP32 FMA (1 FMA/inst), 2:4 structured sparsity (2 nonzeros per 4 elements),
  256 KB per-SM TMEM tile sizing (256x512 FP16 = 256 KiB; 256x256 FP32 = 256 KiB),
  and CUTLASS vs hand-tuned MMA (98% Tensor Core utilization, Table 9-1).
- nvidia-devops Volume 02 Chapter 4:
  SM execution engine specialization (CUDA Cores, Tensor Cores, RT Cores, LD/ST, SFU),
  [4096, 4096] weight matrix FP32 (67.1 MB) vs FP16 (33.6 MB) comparison,
  and Tensor Core shape/alignment eligibility checks ([4096, 4097] misalignment fallback).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


class TensorPrecisionError(ValueError):
    """Raised when invalid numerical format, matrix shape, or sparsity input is provided."""


# 1. Numerical Format Bit-Layouts & Properties (ASP Ch 6 p. 210 & Ch 9 pp. 308-311; V2 Ch 1 & Ch 4)
@dataclass(frozen=True)
class NumericalFormatSpec:
    name: str
    sign_bits: int
    exponent_bits: int
    mantissa_bits: int
    active_compute_bits: int
    storage_bits: int
    storage_bytes: float
    elements_per_128b_line: int
    requires_loss_scaling_in_training: bool
    tensor_core_supported: bool


NUMERICAL_FORMATS: Dict[str, NumericalFormatSpec] = {
    "FP64": NumericalFormatSpec("FP64", 1, 11, 52, 64, 64, 8.0, 16, False, True),
    "FP32": NumericalFormatSpec("FP32", 1, 8, 23, 32, 32, 4.0, 32, False, False),
    "TF32": NumericalFormatSpec("TF32", 1, 8, 10, 19, 32, 4.0, 32, False, True),
    "FP16": NumericalFormatSpec("FP16", 1, 5, 10, 16, 16, 2.0, 64, True, True),
    "BF16": NumericalFormatSpec("BF16", 1, 8, 7, 16, 16, 2.0, 64, False, True),
    "FP8_E4M3": NumericalFormatSpec("FP8_E4M3", 1, 4, 3, 8, 8, 1.0, 128, False, True),
    "FP8_E5M2": NumericalFormatSpec("FP8_E5M2", 1, 5, 2, 8, 8, 1.0, 128, False, True),
    "INT8": NumericalFormatSpec("INT8", 1, 0, 7, 8, 8, 1.0, 128, False, True),
    "NVFP4": NumericalFormatSpec("NVFP4", 1, 2, 1, 4, 4, 0.5, 256, False, True),
}

# 2. Execution Engine Specialization inside an SM (nvidia-devops V2 Ch 4)
SM_EXECUTION_ENGINES: Dict[str, str] = {
    "cuda_cores": "Scalar and vector FP32/INT32 arithmetic, comparisons, address calculation, reductions, and unfused elementwise activations",
    "tensor_cores": "Fused matrix multiply-accumulate (D = A * B + C) on matrix tiles across TF32, BF16, FP16, FP8, INT8, and NVFP4",
    "rt_cores": "Ray-tracing Bounding Volume Hierarchy (BVH) traversal and ray-triangle intersection for rendering and digital twins (not AI GEMMs)",
    "ld_st_units": "Memory address generation and load/store transactions to L1/Shared memory, L2, and HBM",
    "sfu": "Special Function Units for transcendental math (sin, cos, exp, rsqrt, rcp)",
}

# 3. Blackwell B200 & B300 Tensor Core & 1.8T MoE Benchmarks (ASP Ch 2 pp. 24-31 & Ch 9 pp. 310-315)
BLACKWELL_TENSOR_BENCHMARKS: Dict[str, float] = {
    "b200_transistors_billions": 208.0,
    "b200_transistors_per_die_billions": 104.0,
    "b200_nv_hbi_bw_tbps": 10.0,
    "b200_hbm3e_physical_gb": 192.0,
    "b200_hbm3e_usable_gb": 180.0,
    "b200_dense_fp32_tflops": 80.0,
    "b200_dense_nvfp4_pflops": 10.0,
    "b300_dense_nvfp4_pflops": 15.0,
    "moe_1_8t_h100_tok_per_s_per_gpu": 3.4,
    "moe_1_8t_h100_ttft_ms": 5000.0,
    "moe_1_8t_gb200_nvl72_tok_per_s_per_gpu": 150.0,
    "moe_1_8t_gb200_nvl72_ttft_ms": 50.0,
    "dp4a_int8_macs_per_inst": 4.0,
    "cutlass_vs_hand_mma_tensor_util_pct": 98.0,
}


def compare_matrix_precision_footprint(
    rows: int,
    cols: int,
    fmt_a: str = "FP32",
    fmt_b: str = "FP16",
) -> Dict[str, float]:
    """Compare matrix byte footprint and 128-byte cache-line transactions across two formats (V2 Ch 4 & ASP Ch 6).

    Worked example in V2 Ch 4:
    - A `[4096, 4096]` matrix has 16,777,216 elements.
    - At `FP32` (4 bytes): `67,108,864 bytes` (`67.11 MB` decimal / `64.0 MiB`).
    - At `FP16` (2 bytes): `33,554,432 bytes` (`33.55 MB` decimal / `32.0 MiB`, 2.0x reduction).
    """
    if rows <= 0 or cols <= 0:
        raise TensorPrecisionError("Matrix dimensions must be positive")
    if fmt_a not in NUMERICAL_FORMATS or fmt_b not in NUMERICAL_FORMATS:
        raise TensorPrecisionError("Unsupported numerical format")

    spec_a = NUMERICAL_FORMATS[fmt_a]
    spec_b = NUMERICAL_FORMATS[fmt_b]
    num_elements = rows * cols
    bytes_a = num_elements * spec_a.storage_bytes
    bytes_b = num_elements * spec_b.storage_bytes

    return {
        "num_elements": num_elements,
        "bytes_a": int(bytes_a),
        "mb_decimal_a": round(bytes_a / 1_000_000.0, 1),
        "bytes_b": int(bytes_b),
        "mb_decimal_b": round(bytes_b / 1_000_000.0, 1),
        "bandwidth_reduction_factor": round(bytes_a / bytes_b, 2),
        "lines_128b_a": int(bytes_a // 128),
        "lines_128b_b": int(bytes_b // 128),
    }


def validate_2_to_4_structured_sparsity(weights: Sequence[float]) -> Dict[str, object]:
    """Validate hardware 2:4 structured sparsity pattern per ASP Chapter 9 (pp. 302-304).

    Rules from ASP Ch 9:
    - Hardware Sparse Tensor Cores require that every group of 4 consecutive weights
      contains at most 2 nonzero values (specifically 2 nonzeros per 4 elements, or
      8 nonzeros per 16-element chunk).
    - Length of `weights` must be a positive multiple of 4.
    """
    n = len(weights)
    if n == 0 or (n % 4) != 0:
        raise TensorPrecisionError("Weight array length for 2:4 sparsity must be a positive multiple of 4")

    violating_groups: List[int] = []
    total_nonzeros = 0
    num_groups = n // 4

    for g in range(num_groups):
        chunk = weights[g * 4 : (g + 1) * 4]
        nz = sum(1 for v in chunk if v != 0.0)
        total_nonzeros += nz
        if nz > 2:
            violating_groups.append(g)

    valid = len(violating_groups) == 0
    density_pct = round((total_nonzeros / n) * 100.0, 1)
    return {
        "num_elements": n,
        "num_quads": num_groups,
        "total_nonzeros": total_nonzeros,
        "density_pct": density_pct,
        "valid_2_to_4": valid,
        "violating_quad_indices": violating_groups,
        "theoretical_sparse_speedup": 2.0 if valid else 1.0,
    }


def calc_tmem_tile_fit(
    tile_m: int,
    tile_n: int,
    bytes_per_element: float,
    tmem_capacity_kib: int = 256,
) -> Dict[str, object]:
    """Check whether a Tensor Core accumulator/operand tile fits in Blackwell's 256 KB per-SM TMEM (ASP Ch 9 p. 314).

    Worked examples in ASP Ch 9 p. 314:
    - `256 x 512` elements at `2 bytes` (FP16/BF16) = `262,144 bytes = 256.0 KiB` (100% of TMEM).
    - `256 x 256` elements at `4 bytes` (FP32 accumulator) = `262,144 bytes = 256.0 KiB` (100% of TMEM).
    - `256 x 256` elements at `0.5 bytes` (NVFP4) = `32,768 bytes = 32.0 KiB` (12.5% of TMEM).
    """
    if tile_m <= 0 or tile_n <= 0 or bytes_per_element <= 0 or tmem_capacity_kib <= 0:
        raise TensorPrecisionError("Tile dimensions, byte width, and TMEM capacity must be positive")

    tile_bytes = tile_m * tile_n * bytes_per_element
    cap_bytes = tmem_capacity_kib * 1024
    fits = tile_bytes <= cap_bytes
    max_concurrent_tiles_in_tmem = int(cap_bytes // tile_bytes) if fits else 0

    return {
        "tile_bytes": int(tile_bytes),
        "tile_kib": round(tile_bytes / 1024.0, 1),
        "fits_in_tmem": fits,
        "utilization_pct": round((tile_bytes / cap_bytes) * 100.0, 2),
        "max_concurrent_tiles_in_tmem": max_concurrent_tiles_in_tmem,
    }


def check_tensor_core_eligibility(
    m: int,
    n: int,
    k: int,
    precision: str,
    sm_utilization_pct: float = 91.0,
    mem_utilization_pct: float = 18.0,
    tensor_pipe_active_pct: float = 0.0,
) -> Dict[str, object]:
    """Diagnose Tensor Core GEMM eligibility and SM pipeline routing (V2 Ch 4 & ASP Ch 9).

    Note: Combining the 16-byte tile alignment rule (`8` elements for 16-bit FP16/BF16,
    `16` elements for 8-bit FP8/INT8, `32` elements for 4-bit NVFP4, `4` elements for TF32)
    with the `nvidia-smi dmon` + `ncu` pipeline diagnostic tree from V2 Ch 4 is an
    authoring synthesis ("my inference").
    """
    if m <= 0 or n <= 0 or k <= 0:
        raise TensorPrecisionError("GEMM dimensions (M, N, K) must be positive")
    if precision not in NUMERICAL_FORMATS:
        raise TensorPrecisionError(f"Unsupported precision: {precision}")

    spec = NUMERICAL_FORMATS[precision]
    reasons: List[str] = []

    if not spec.tensor_core_supported:
        reasons.append(f"{precision} uses scalar CUDA core pipelines; enable TF32, BF16, FP16, FP8, or NVFP4")

    # 16-byte (128-bit) alignment granularity in elements for Tensor Core MMA tiles
    align_elems = max(1, int(16 // spec.storage_bytes))
    misaligned_dims = [
        name for name, val in (("M", m), ("N", n), ("K", k)) if (val % align_elems) != 0
    ]
    if misaligned_dims:
        reasons.append(
            f"Dimensions {misaligned_dims} are not multiples of {align_elems} (16-byte tile boundary for {precision}); risk of fallback to scalar/general GEMM path"
        )

    if m < 32:
        reasons.append(
            f"Small batch/M dimension (M={m}): fixed launch and format conversion overhead may limit Tensor Core / TMEM speedup"
        )

    if tensor_pipe_active_pct < 10.0 and sm_utilization_pct >= 80.0:
        pipeline_diagnosis = "GENERAL_CUDA_CORES_DOMINATE_TENSOR_CORES_IDLE"
    elif tensor_pipe_active_pct >= 50.0 and mem_utilization_pct >= 85.0:
        pipeline_diagnosis = "TENSOR_CORES_ACTIVE_BUT_HBM_BANDWIDTH_STARVED"
    elif tensor_pipe_active_pct >= 50.0:
        pipeline_diagnosis = "TENSOR_CORE_COMPUTE_ENGAGED"
    else:
        pipeline_diagnosis = "LOW_OVERALL_SM_ACTIVITY"

    return {
        "tensor_core_eligible": spec.tensor_core_supported and len(misaligned_dims) == 0,
        "required_element_alignment": align_elems,
        "misaligned_dimensions": misaligned_dims,
        "pipeline_diagnosis": pipeline_diagnosis,
        "reasons": reasons,
    }
