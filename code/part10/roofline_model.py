#!/usr/bin/env python3
"""Chapter 10.5 model: The Roofline Model and Performance Modelling.

Encodes the verifiable Roofline formulas, ridge points (machine balance),
worked arithmetic-intensity calculations, precision/fusion/cluster-multicast
shifts, non-contiguous cache bandwidth, and 6-category GPU bottleneck
diagnostics from:
- AI Systems Performance Engineering (ASP) Chapter 6 (pp. 209-212) and
  Chapter 9 (pp. 295-305):
  FP32 vector-add intensity (1 FLOP / 12 B = 0.0833 FLOPs/B, capped at
  0.0833 * 8 TB/s = 0.667 TFLOPS), Blackwell B200 FP32 ridge point
  (80 TFLOPS / 8 TB/s = 10.0 FLOPs/B), precision-driven intensity multipliers
  (FP16 2x = 0.167, FP8 4x = 0.333, FP4 8x = 0.667 FLOPs/B), unfused vs fused
  L2 norm (36 B vs 12 B per element), and Thread Block Cluster TMA multicast
  reuse (up to 4x on 2x2 CTAs, up to 16x on 16 CTAs).
- Parallel and High Performance Computing (PHPC) Chapter 3 (§3.1-3.3) and
  Chapter 9 (§9.3.3-9.3.4):
  Machine Balance in FLOPs/byte and FLOPs/word (8 B FP64 word, 4 B FP32 word;
  236.8 GFLOPS / 34.1 GiB/s * 8 = 55.55 ~ 56 FLOPs/word or 6.94 FLOPs/byte
  theoretical; 264.4 GFLOPS / 22.0 GiB/s * 8 = 96.15 ~ 96 FLOPs/word or
  12.02 FLOPs/byte empirical; CloverLeaf 0.11 to 0.3608 FLOPs/byte),
  non-contiguous cache bandwidth (B_nc = U_cache * B_E), and CloverLeaf
  parallel vs serial energy reduction (28.7% total, 23.2% DRAM).
- nvidia-devops Volume 17 Chapter 3 & Volume 02 Chapters 11-12:
  H100 SXM FP16 Tensor Core ridge point (989 TFLOPS / 3.35 TB/s = 295.2 FLOPs/B),
  Batch Size = 1 MLP/LLM decode intensity vs ridge point (3.35 TFLOPS = 0.34%
  of 989 TFLOPS peak; Batch = 64 reaches 62.06 FLOPs/B and 207.9 TFLOPS),
  6-cause elimination pass, and per-rank collective straggler detection.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


class RooflineModelError(ValueError):
    """Raised when invalid hardware ceilings or workload counters are provided."""


@dataclass(frozen=True)
class HardwareRooflineSpec:
    name: str
    precision: str
    peak_tflops: float
    peak_bw_tbps: float

    @property
    def ridge_point_flops_per_byte(self) -> float:
        return round(self.peak_tflops / self.peak_bw_tbps, 1)


HARDWARE_ROOFLINES: Dict[str, HardwareRooflineSpec] = {
    "B200_FP32_SCALAR": HardwareRooflineSpec("Blackwell B200 (FP32 Scalar)", "FP32", 80.0, 8.0),
    "H100_SXM_FP16_TC": HardwareRooflineSpec("Hopper H100 SXM (FP16/BF16 Tensor Core)", "FP16", 989.0, 3.35),
    "H200_SXM_FP16_TC": HardwareRooflineSpec("Hopper H200 SXM (FP16/BF16 Tensor Core)", "FP16", 989.0, 4.80),
    "B200_BF16_TC": HardwareRooflineSpec("Blackwell B200 (BF16 Tensor Core)", "BF16", 2250.0, 8.0),
    "B200_NVFP4_TC": HardwareRooflineSpec("Blackwell B200 (NVFP4 Tensor Core)", "NVFP4", 10000.0, 8.0),
}


def evaluate_roofline_point(
    flops: float,
    bytes_moved: float,
    peak_tflops: float,
    peak_bw_tbps: float,
    cache_line_utilization: float = 1.0,
) -> Dict[str, object]:
    """Evaluate a workload on the Roofline model per ASP Ch 6 (p. 209), PHPC Ch 3 (§3.1), and V17 Ch 3.

    Rules:
    - Arithmetic Intensity `I = flops / bytes_moved` (FLOPs/byte).
    - Effective Memory Bandwidth `B_eff = cache_line_utilization * peak_bw_tbps` (PHPC Ch 3 §3.1: `B_nc = U_cache * B_E`).
    - Ridge Point `I_ridge = peak_tflops / B_eff` (FLOPs/byte).
    - Attainable Performance `P_max = min(peak_tflops, I * B_eff)` (TFLOPS).
    """
    if flops <= 0 or bytes_moved <= 0 or peak_tflops <= 0 or peak_bw_tbps <= 0:
        raise RooflineModelError("flops, bytes_moved, peak_tflops, and peak_bw_tbps must be positive")
    if not (0.0 < cache_line_utilization <= 1.0):
        raise RooflineModelError("cache_line_utilization must be in (0.0, 1.0]")

    intensity = flops / bytes_moved
    eff_bw_tbps = peak_bw_tbps * cache_line_utilization
    ridge_point = peak_tflops / eff_bw_tbps
    mem_ceiling_tflops = intensity * eff_bw_tbps
    attainable_tflops = min(peak_tflops, mem_ceiling_tflops)
    regime = "MEMORY_BOUND" if intensity < ridge_point else "COMPUTE_BOUND"

    return {
        "arithmetic_intensity_flops_per_byte": round(intensity, 4),
        "effective_bw_tbps": round(eff_bw_tbps, 3),
        "ridge_point_flops_per_byte": round(ridge_point, 1),
        "attainable_tflops": round(attainable_tflops, 3),
        "regime": regime,
        "ratio_to_ridge": round(intensity / ridge_point, 5),
    }


def calc_machine_balance_words(
    peak_gflops: float,
    bw_gib_s: float,
    bytes_per_word: int = 8,
) -> Dict[str, float]:
    """Calculate Machine Balance in FLOPs/byte and FLOPs/word per PHPC Chapter 3 Section 3.2.5 (p. 61).

    Worked examples in PHPC Ch 3 p. 61:
    - Theoretical: `236.8 GFLOPS / 34.1 GiB/s * 8 B/word = 55.55 ≈ 56 FLOPs/word`.
    - Empirical (STREAM): `264.4 GFLOPS / 22.0 GiB/s * 8 B/word = 96.15 ≈ 96 FLOPs/word`.
    """
    if peak_gflops <= 0 or bw_gib_s <= 0 or bytes_per_word not in (4, 8):
        raise RooflineModelError("Invalid machine balance inputs")
    flops_per_byte = peak_gflops / bw_gib_s
    flops_per_word = flops_per_byte * bytes_per_word
    return {
        "flops_per_byte": round(flops_per_byte, 2),
        "flops_per_word": round(flops_per_word, 2),
        "flops_per_word_rounded": round(flops_per_word),
    }


def calc_gemm_arithmetic_intensity(
    batch_m: int,
    in_features_k: int,
    out_features_n: int,
    bytes_per_element: float = 2.0,
) -> Dict[str, float]:
    """Calculate exact and asymptotic GEMM arithmetic intensity I(B, K, N, b).

    Note: Using the symbolic GEMM formula
        FLOPs = 2 * B * K * N
        Bytes = (B * K + K * N + B * N) * bytes_per_element
    to connect the `Batch Size = 1` MLP/LLM scenarios in V17 Ch 3 and V2 Ch 11
    to the GPU ridge point is an authoring synthesis ("my inference").
    When K, N >> B, I ≈ (2 * B) / bytes_per_element.
    """
    if batch_m <= 0 or in_features_k <= 0 or out_features_n <= 0 or bytes_per_element <= 0:
        raise RooflineModelError("All GEMM parameters must be positive")

    total_flops = 2.0 * batch_m * in_features_k * out_features_n
    total_bytes = (
        (batch_m * in_features_k) + (in_features_k * out_features_n) + (batch_m * out_features_n)
    ) * bytes_per_element
    exact_intensity = total_flops / total_bytes
    large_matrix_approx = (2.0 * batch_m) / bytes_per_element

    return {
        "total_flops": total_flops,
        "total_bytes": total_bytes,
        "exact_intensity_flops_per_byte": round(exact_intensity, 2),
        "asymptotic_intensity_flops_per_byte": round(large_matrix_approx, 2),
    }


def compare_kernel_fusion_and_cluster_multicast(
    unfused_passes: int = 3,
    bytes_per_pass_per_elem: int = 12,
    total_flops_per_elem: int = 4,
    cluster_ctas: int = 4,
) -> Dict[str, float]:
    """Evaluate arithmetic-intensity gains from kernel fusion and Thread Block Cluster TMA multicast (ASP Ch 9 pp. 297-301).

    Reproduces:
    - Unfused 3-pass L2 norm (`3 * 12 = 36 bytes`, `4 FLOPs` -> `4 / 36 = 0.1111 FLOPs/B`; single 1-FLOP pass = `1 / 12 = 0.0833 FLOPs/B`).
    - Fused 1-pass `fusedL2Norm` (`12 bytes` = 2 float reads + 1 float write, `3` conservative or `4` total FLOPs -> `0.25` to `0.3333 FLOPs/B`, `3.0x` less HBM traffic).
    - Thread Block Cluster TMA multicast across `cluster_ctas` (`4` CTAs in a `2x2` cluster -> `4.0x` tile traffic reduction; up to `16` CTAs with `cudaFuncAttributeNonPortableClusterSizeAllowed`).
    """
    if unfused_passes <= 0 or bytes_per_pass_per_elem <= 0 or total_flops_per_elem <= 0:
        raise RooflineModelError("Invalid fusion parameters")
    if cluster_ctas <= 0 or cluster_ctas > 16:
        raise RooflineModelError("Blackwell supports at most 16 CTAs per Thread Block Cluster")

    unfused_bytes = unfused_passes * bytes_per_pass_per_elem
    fused_bytes = bytes_per_pass_per_elem
    unfused_intensity = total_flops_per_elem / unfused_bytes
    fused_intensity = total_flops_per_elem / fused_bytes
    conservative_3flop_intensity = 3.0 / fused_bytes

    return {
        "unfused_bytes_per_elem": unfused_bytes,
        "fused_bytes_per_elem": fused_bytes,
        "traffic_reduction_factor": round(unfused_bytes / fused_bytes, 2),
        "unfused_intensity": round(unfused_intensity, 4),
        "fused_conservative_3flop_intensity": round(conservative_3flop_intensity, 4),
        "fused_4flop_intensity": round(fused_intensity, 4),
        "cluster_multicast_reuse_factor": float(cluster_ctas),
        "requires_nonportable_cluster_attr": cluster_ctas > 8,
    }


def classify_gpu_workload_bottleneck(
    gpu_busy_throughout: bool,
    sm_util_pct: float,
    mem_util_pct: float,
    dram_pct_of_peak: float,
    tensor_pipe_pct: float,
    active_throttle_reasons: str = "N/A",
    rank_step_times_ms: Sequence[float] = (),
) -> Dict[str, object]:
    """Classify a workload's primary bottleneck across the 6 system regimes (V2 Ch 11 & Ch 12).

    Note: Encoding the 6-regime elimination tree from `nvidia-devops` Volume 02
    Chapters 11 and 12 into a deterministic Python function is an authoring
    synthesis ("my inference").
    """
    if not (0.0 <= sm_util_pct <= 100.0 and 0.0 <= mem_util_pct <= 100.0 and 0.0 <= dram_pct_of_peak <= 100.0):
        raise RooflineModelError("Percentages must be in 0..100")

    has_straggler = False
    straggler_ratio = 1.0
    if len(rank_step_times_ms) >= 2:
        min_t = min(rank_step_times_ms)
        max_t = max(rank_step_times_ms)
        if min_t <= 0:
            raise RooflineModelError("Rank step times must be positive")
        straggler_ratio = round(max_t / min_t, 2)
        if straggler_ratio >= 1.5:
            has_straggler = True

    if active_throttle_reasons not in ("N/A", "None", ""):
        category = "THERMAL_OR_POWER_THROTTLED"
    elif has_straggler:
        category = "MULTI_GPU_COMMUNICATION_OR_STRAGGLER_BOUND"
    elif not gpu_busy_throughout or (sm_util_pct < 20.0 and mem_util_pct < 20.0):
        category = "HOST_INPUT_OR_LAUNCH_LATENCY_BOUND"
    elif mem_util_pct >= 80.0 and dram_pct_of_peak >= 70.0:
        category = "MEMORY_BANDWIDTH_BOUND"
    elif mem_util_pct >= 80.0 and dram_pct_of_peak < 40.0:
        category = "MEMORY_TRANSACTION_UNCOALESCED_OR_LATENCY_BOUND"
    elif sm_util_pct >= 80.0 and tensor_pipe_pct < 15.0:
        category = "SCALAR_COMPUTE_OR_DIVERGENCE_BOUND_TENSOR_IDLE"
    else:
        category = "TENSOR_COMPUTE_BOUND"

    return {
        "category": category,
        "has_rank_straggler": has_straggler,
        "rank_straggler_ratio": straggler_ratio,
    }
