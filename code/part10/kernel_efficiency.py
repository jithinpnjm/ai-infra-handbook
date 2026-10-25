#!/usr/bin/env python3
"""Chapter 10.15 model: Kernel Efficiency and Arithmetic Intensity.

Encodes the verifiable kernel-fusion byte/FLOP reductions (`fusedL2Norm`),
Thread Block Cluster TMA multicast reuse (4x on 2x2 CTAs, 16x on 16 CTAs),
2:4 structured sparsity & precision shifts (`FP32` 80 TFLOPS vs `B200 NVFP4`
10 PFLOPS vs `B300 NVFP4` 15 PFLOPS, `INT8 DP4A` 75% weight reduction),
`TMEM` 256 KB tile-capacity budgets (`256x512` FP16 = 256 KiB, `256x256` FP32
= 256 KiB), CUTLASS vs hand-tuned MMA comparison (Table 9-1), and inline PTX
(`cp.async.bulk.prefetch.L2.global`, `ld.global.cg.f32`, `%smid`, and
DeepSeek's `ld.global.nc.l1::no_allocate.l2::256b`, Table 9-2) from:
- AI Systems Performance Engineering (ASP) Chapter 9 (pp. 295-326).
"""

from __future__ import annotations

from typing import Dict, Sequence


class KernelEfficiencyError(ValueError):
    """Raised when invalid kernel fusion, tile, precision, or PTX parameters are supplied."""


# Table 9-1: Hand-tuned MMA kernel vs CUTLASS GEMM (ASP Ch 9 p. 316)
TABLE_9_1_CUTLASS_VS_HANDTUNED: Dict[str, Dict[str, object]] = {
    "HAND_TUNED_MMA": {
        "tensor_core_utilization_pct": 98.0,
        "registers_per_thread": 52,
        "shared_memory_kb_per_cta": 2.0,
        "development_effort": "High",
    },
    "CUTLASS_GEMM": {
        "tensor_core_utilization_pct": 98.0,
        "registers_per_thread": 60,
        "shared_memory_kb_per_cta": 4.0,
        "development_effort": "Low",
    },
}

# Table 9-2: Optimized CUDA C++ vs Hand-tuned Inline PTX (ASP Ch 9 p. 320)
TABLE_9_2_INLINE_PTX: Dict[str, Dict[str, float]] = {
    "OPTIMIZED_CPP": {
        "warp_stall_memory_pct": 35.0,
        "issue_ipc": 1.5,
        "kernel_time_ms": 1.07,
        "speedup_x": 1.00,
    },
    "HAND_TUNED_PTX": {
        "warp_stall_memory_pct": 20.0,
        "issue_ipc": 1.6,
        "kernel_time_ms": 1.00,
        "speedup_x": 1.07,
    },
}


def analyze_l2_norm_fusion_and_cluster_multicast(
    unfused_passes: int = 3,
    bytes_per_unfused_pass: int = 12,
    fused_bytes_per_element: int = 12,
    flops_per_element_conservative: float = 3.0,
    flops_per_element_with_norm: float = 4.0,
    cluster_ctas: int = 4,
    non_portable_cluster_allowed: bool = False,
) -> Dict[str, object]:
    """Quantify arithmetic-intensity gains from `fusedL2Norm` and Thread Block Cluster TMA multicast per ASP Ch 9 (pp. 297-302).

    Data points from ASP Ch 9:
    - Single elementwise pass (2 float reads + 1 float write = 12 B, 1 FLOP) has intensity `1 / 12 = 0.0833 FLOPs/B`.
    - Unfused multi-kernel L2 norm (`square -> reduce -> divide`, 3 passes x 12 B = `36 B` per element, `4 FLOPs`)
      has intensity `4 / 36 = 0.1111 FLOPs/B`.
    - Fused `fusedL2Norm` walks each row in registers/SMEM (`12 B` global traffic per element: 2 reads + 1 write):
      - Conservative placement (`3 FLOPs / 12 B`) = `0.25 FLOPs/B`.
      - Including amortized norm (`4 FLOPs / 12 B`) = `0.3333 FLOPs/B` (`3.0x` less HBM traffic than 36 B unfused).
    - Thread Block Cluster TMA multicast:
      - Standard portable cluster (`2 x 2 = 4` CTAs, max portable = `8` CTAs) cuts tile HBM traffic by `4x`.
      - Non-portable cluster on Blackwell (`16` CTAs, enabled via `cudaFuncAttributeNonPortableClusterSizeAllowed`)
        cuts tile HBM traffic by up to `16x`.
    """
    if unfused_passes <= 0 or bytes_per_unfused_pass <= 0 or fused_bytes_per_element <= 0:
        raise KernelEfficiencyError("Byte and pass counts must be positive")
    if cluster_ctas <= 0 or cluster_ctas > 16:
        raise KernelEfficiencyError("cluster_ctas must be in 1..16")
    if cluster_ctas > 8 and not non_portable_cluster_allowed:
        raise KernelEfficiencyError(
            f"cluster_ctas={cluster_ctas} exceeds portable limit of 8; requires cudaFuncAttributeNonPortableClusterSizeAllowed"
        )

    single_pass_ai = 1.0 / bytes_per_unfused_pass
    unfused_total_bytes = unfused_passes * bytes_per_unfused_pass
    unfused_ai = flops_per_element_with_norm / unfused_total_bytes
    fused_conservative_ai = flops_per_element_conservative / fused_bytes_per_element
    fused_full_ai = flops_per_element_with_norm / fused_bytes_per_element
    hbm_traffic_reduction_x = unfused_total_bytes / fused_bytes_per_element

    return {
        "single_pass_1flop_12b_ai": round(single_pass_ai, 3),
        "unfused_total_bytes_per_elem": unfused_total_bytes,
        "unfused_ai_flops_per_byte": round(unfused_ai, 4),
        "fused_bytes_per_elem": fused_bytes_per_element,
        "fused_conservative_ai_flops_per_byte": round(fused_conservative_ai, 4),
        "fused_full_ai_flops_per_byte": round(fused_full_ai, 4),
        "fusion_hbm_traffic_reduction_x": round(hbm_traffic_reduction_x, 2),
        "cluster_ctas": cluster_ctas,
        "cluster_multicast_traffic_reduction_x": float(cluster_ctas),
    }


def evaluate_tmem_and_smem_stage_budgets(
    tile_m: int = 256,
    tile_n: int = 512,
    element_bytes: float = 2.0,
    stage_tile_elems: int = 1024,
    tmem_capacity_kib: float = 256.0,
) -> Dict[str, object]:
    """Calculate Blackwell 256 KB TMEM tile fit and 2-stage (`A0, A1, B0, B1`) SMEM pipeline bytes per ASP Ch 9 (pp. 308-315).

    Rules from ASP Ch 9:
    - Each Blackwell SM has `256 KB` (`262,144` bytes = `256 KiB`) of dedicated Tensor Memory (`TMEM`)
      servicing `tcgen05.mma` instructions:
      - A `256 x 512` tile at `2 B` (`FP16`/`BF16`) occupies `256 * 512 * 2 = 262,144 B = 256.0 KiB` (100% of TMEM).
      - A `256 x 256` tile at `4 B` (`FP32` accumulator) occupies `256 * 256 * 4 = 262,144 B = 256.0 KiB` (100% of TMEM).
      - A `256 x 256` tile at `0.5 B` (`NVFP4`) occupies `256 * 256 * 0.5 = 32,768 B = 32.0 KiB` (12.5% of TMEM).
    - In `two_stage_pipeline.cu` (`stage_ab_tiles`, p. 308), dynamic shared memory allocates 4 buffers
      (`A0, A1, B0, B1`) = `4 * stage_tile_elems * sizeof(float)` bytes, and `stage_tile_elems` must be a
      multiple of `32 * 4 = 128` floats for warp-aligned `float4` vectorization.
    """
    if tile_m <= 0 or tile_n <= 0 or element_bytes <= 0 or stage_tile_elems <= 0 or tmem_capacity_kib <= 0:
        raise KernelEfficiencyError("Tile and capacity parameters must be positive")
    if stage_tile_elems % 128 != 0:
        raise KernelEfficiencyError("tile_elems must be a multiple of 128 (32 threads * 4 floats) for float4 vectorization")

    tile_bytes = tile_m * tile_n * element_bytes
    tile_kib = tile_bytes / 1024.0
    fits_in_tmem = tile_kib <= tmem_capacity_kib
    dynamic_smem_4buf_bytes = 4 * stage_tile_elems * 4

    return {
        "tile_shape": (tile_m, tile_n),
        "element_bytes": element_bytes,
        "tile_bytes": int(tile_bytes),
        "tile_kib": round(tile_kib, 1),
        "tmem_capacity_kib": tmem_capacity_kib,
        "tmem_utilization_pct": round((tile_kib / tmem_capacity_kib) * 100.0, 2),
        "fits_in_tmem": fits_in_tmem,
        "two_stage_ab_dynamic_smem_bytes": dynamic_smem_4buf_bytes,
    }


def evaluate_precision_and_sparsity_scaling(
    b200_fp32_tflops: float = 80.0,
    b200_nvfp4_pflops: float = 10.0,
    b300_nvfp4_pflops: float = 15.0,
    batch_size: int = 128,
    sequence_lengths: Sequence[int] = (128, 512, 256, 1024),
) -> Dict[str, object]:
    """Evaluate precision/sparsity throughput ratios and NestedTensor ragged-batch memory savings per ASP Ch 9 (pp. 303-312).

    Data points from ASP Ch 9:
    1. `B200` dense `NVFP4` (`10 PFLOPS` = `10,000 TFLOPS`) vs `FP32` (`80 TFLOPS`) = `125.0x` (~2 orders of magnitude).
    2. `B300` (Blackwell Ultra) dense `NVFP4` (`15 PFLOPS`) is `1.5x` (`+50%`) higher than `B200` (`10 PFLOPS`).
    3. `INT8` (`1 B` vs `4 B` `FP32`) cuts weight memory traffic by `75.0%` (`4.0x` more weights per byte) and
       executes `4` INT8 MACs per `DP4A` instruction.
    4. `2:4` structured sparsity (`to_sparse_semi_structured()`) zeroes `8` of every `16` elements (`50.0%`
       pruned) for up to `2.0x` speedup when `batch_size >= 128` (whereas `batch_size == 1` fails to amortize
       metadata/index overhead).
    5. PyTorch `NestedTensor` packs variable-length sequences (`sum(sequence_lengths)`) without zero-padding
       to `len(sequence_lengths) * max(sequence_lengths)`.
    """
    if b200_fp32_tflops <= 0 or b200_nvfp4_pflops <= 0 or b300_nvfp4_pflops <= 0 or batch_size <= 0:
        raise KernelEfficiencyError("TFLOPS/PFLOPS and batch_size must be positive")
    if not sequence_lengths or any(s <= 0 for s in sequence_lengths):
        raise KernelEfficiencyError("sequence_lengths must be non-empty and positive")

    b200_fp4_vs_fp32_x = (b200_nvfp4_pflops * 1000.0) / b200_fp32_tflops
    b300_vs_b200_fp4_gain_pct = ((b300_nvfp4_pflops - b200_nvfp4_pflops) / b200_nvfp4_pflops) * 100.0

    padded_tokens = len(sequence_lengths) * max(sequence_lengths)
    nested_tokens = sum(sequence_lengths)
    padding_waste_pct = ((padded_tokens - nested_tokens) / padded_tokens) * 100.0

    return {
        "b200_nvfp4_vs_fp32_speedup_x": round(b200_fp4_vs_fp32_x, 1),
        "b300_vs_b200_nvfp4_gain_pct": round(b300_vs_b200_fp4_gain_pct, 1),
        "int8_weight_traffic_reduction_pct": 75.0,
        "dp4a_macs_per_instruction": 4,
        "sparse_2_4_zeroed_in_16_chunk": 8,
        "sparse_and_fp8_batch_amortized": batch_size >= 128,
        "padded_batch_tokens": padded_tokens,
        "nested_tensor_tokens": nested_tokens,
        "nested_tensor_saved_padding_pct": round(padding_waste_pct, 1),
    }


def inspect_inline_ptx_instruction(ptx_snippet: str) -> Dict[str, object]:
    """Classify and validate an inline PTX micro-optimization snippet per ASP Ch 9 (pp. 318-323).

    Covers:
    1. `cp.async.bulk.prefetch.L2.global` / `cp.async.bulk.prefetch.tensor.L2` (128B L2 prefetch, 16B aligned).
    2. `ld.global.cg.f32` (cache global: caches in L2, bypasses L1 to prevent L1 thrashing vs `.ca`).
    3. `mov.u32 %0, %smid;` (reads hardware `%smid` special register for persistent-kernel SM partitioning).
    4. `ld.global.nc.l1::no_allocate.l2::256b` (DeepSeek `DeepEP` out-of-doc Hopper H800 PTX instruction:
       non-coherent load, bypasses L1 allocation, fetches 256B chunks into L2; requires
       `DISABLE_AGGRESSIVE_PTX_INSTRS=1` fallback flag for portability across future architectures).
    """
    clean = ptx_snippet.strip()
    if not clean:
        raise KernelEfficiencyError("ptx_snippet must be non-empty")

    if "l1::no_allocate.l2::256b" in clean:
        return {
            "category": "DEEPSEEK_DEEPEP_L1_BYPASS_256B_L2",
            "bypasses_l1_allocation": True,
            "l2_fetch_granularity_bytes": 256,
            "official_documented_ptx_isa": False,
            "fallback_build_flag": "DISABLE_AGGRESSIVE_PTX_INSTRS=1",
        }
    if "cp.async.bulk.prefetch" in clean:
        return {
            "category": "L2_ASYNC_BULK_PREFETCH",
            "bypasses_l1_allocation": True,
            "l2_fetch_granularity_bytes": 128,
            "official_documented_ptx_isa": True,
            "fallback_build_flag": None,
        }
    if "ld.global.cg" in clean:
        return {
            "category": "CACHE_GLOBAL_L2_ONLY_LOAD",
            "bypasses_l1_allocation": True,
            "l2_fetch_granularity_bytes": 128,
            "official_documented_ptx_isa": True,
            "fallback_build_flag": None,
        }
    if "%smid" in clean:
        return {
            "category": "SPECIAL_REGISTER_SMID_READ",
            "bypasses_l1_allocation": False,
            "l2_fetch_granularity_bytes": 0,
            "official_documented_ptx_isa": True,
            "fallback_build_flag": None,
        }
    raise KernelEfficiencyError(f"Unrecognized PTX micro-optimization pattern: {ptx_snippet}")
