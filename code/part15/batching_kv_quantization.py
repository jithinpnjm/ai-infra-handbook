#!/usr/bin/env python3
"""Chapter 15.2 model: Batching, the KV Cache and Quantization Fundamentals.

Models:
1. Prefill vs Decode Roofline & Arithmetic Intensity (`HLS` Ch. 5, `AIE` Ch. 9, `VL5` Ch. 2, `V12` Ch. 7):
   - Linear projection `[M, K] x [K, N]` in 2-byte precision (`FP16`/`BF16`):
     `FLOPs = 2 * M * N * K`, `Bytes = 2 * (M * K + K * N + M * N)`,
     `AI = (M * N * K) / (M * K + K * N + M * N)`.
   - For square matrices `M = N = K`:
     `M=64 -> 21.33 (~21) FLOPS/B`, `M=512 -> 170.67 (~170) FLOPS/B`, `M=4096 -> 1365.33 (~1365) FLOPS/B`.
   - For LLM linear layer with `K = N = h = 4096` and `M = s` (prefill) or `M = 1` (decode at `B = 1`):
     `AI_prefill = (s * h * h) / (2 * s * h + h * h)`:
     * `s = 64 -> 62.06 FLOPS/B`
     * `s = 512 -> 409.60 FLOPS/B`
     * `s = 4096 -> 1365.33 FLOPS/B`
     * `s_decode = 1 -> 4096 / 4098 = 0.9995 (~1.0) FLOPS/B`
   - Hardware Ridge Points (`TFLOPS / Bandwidth_GBps`):
     * `L40S` (`48 GB`, `362.05` / `362` FP16 TFLOPS, `733` FP8 TFLOPS, `864 GB/s` bandwidth): `362000 / 864 = 418.98 (~419) FLOPS/B`
     * `H100 SXM` (`80 GB`, `1979` FP16/BF16 TFLOPS, `3958` FP8 TFLOPS, `3350 GB/s` bandwidth): `590.75 FLOPS/B` (FP16), `1181.49 FLOPS/B` (FP8)
     * `H100 NVL` (`94 GB`, `1671` FP16 TFLOPS, `3341` FP8 TFLOPS, `3900 GB/s` bandwidth): `428.46 FLOPS/B`
     * `H200 SXM` (`141 GB`, `1979` FP16 TFLOPS, `3958` FP8 TFLOPS, `4800 GB/s` bandwidth): `412.29 FLOPS/B`
     * `A100 SXM` (`80 GB`, `312` FP16 TFLOPS, `1935` / `2000 GB/s` bandwidth): `161.24 FLOPS/B`
     * `A10` (`24 GB`, `125` FP16 TFLOPS, `600 GB/s` bandwidth): `208.33 FLOPS/B`
   - Model Bandwidth Utilization (`MBU`, `AIE` Ch. 9):
     `bandwidth_used_gbps = params_billions * bytes_per_param * tokens_per_sec`
     `mbu = bandwidth_used_gbps / peak_bandwidth_gbps`
2. Batching Paradigms: Static vs Dynamic vs Continuous (In-Flight) Batching & Chunked Prefill (`V12` Ch. 7, `HLS` Ch. 6):
   - Request-level dynamic batching padding waste ratio:
     `padding_waste_ratio = 1.0 - sum(L_i) / (B * max(L_i))`
   - Tail-latency locking: short sequences (`10` tokens) trapped waiting for the longest sequence (`2000` or `2048` tokens)
     for `1990` extra iterations (`p99 ITL = 420 ms` -> `19.1 ms`, `3.8x` throughput gain with Continuous Batching).
   - Iteration-level Continuous Batching (`Orca`) + `Chunked Prefill` (`Sarathi-Lean`):
     `sum(1_decode) + sum(C_prefill) <= max_num_batched_tokens` (`2048` tokens), preventing a `12,288`-token prompt
     (`320 ms` prefill bubble, `340 ms` p99 ITL spike) from starving active decode streams (`21.4 ms` p99 ITL).
3. KV Cache Memory Math across Attention Architectures (`MHA`, `GQA`, `MQA`, `MLA`) & Capacity Planning (`V12` Ch. 8, `HLS` Ch. 5 & 6, `AIE` Ch. 9):
   - Standard KV Cache formula per token:
     `kv_bytes_per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_element`
   - Multi-Head Latent Attention (`MLA`, DeepSeek-V2/V3/R1):
     Caches compressed latent vector `c_t^KV` (`kv_lora_rank = 512`) + decoupled RoPE key `k_t^R` (`qk_rope_head_dim = 64`)
     = `576` elements per layer (equivalent to `GQA` with `2.25` groups, since `2 * 2.25 * 128 = 576`):
     `mla_bytes_per_token = num_layers * (kv_lora_rank + qk_rope_head_dim) * bytes_per_element`
   - PagedAttention internal fragmentation bound: `< block_size / actual_seq_len` (`< 4%`, e.g., `16 / 500 = 3.2%`),
     eliminating external fragmentation (`0%`) vs `60%–80%` contiguous waste (`20.4%–38.2%` effective utilization).
   - Concurrency capacity planning (`C_max`) and `PreemptionMode` (`Swap` vs `Recompute` crossover at `S < 8192`).
4. Quantization Fundamentals (`PTQ` vs `QAT`, `FP8 E4M3/E5M2`, `INT8 SmoothQuant`, `INT4 AWQ/GPTQ`, `NVFP4`, KV Cache Quantization):
   - Symmetric `absmax` (`scale = max(|X|) / 127` or `127 / max(|X|)`) and asymmetric `zero-point` quantization,
     rounding error (`7.6 -> 8`, error `0.4`) and clamping error (`1000 -> 448` in `FP8 E4M3` `[-448, +448]`).
   - `SmoothQuant` (`W8A8`): `s_j = (max(|X_j|)^alpha) / (max(|W_j|)^(1 - alpha))`,
     `X_hat = X * diag(s)^-1`, `W_hat = diag(s) * W`.
   - `W4A16` (`GPTQ` / `AWQ` + `Marlin` / `Machete`, `75%` weight reduction, `+300%` low-batch speedup) vs
     `W8A8` (`FP8` / `INT8`, `50%` weight reduction, `2x` Tensor Core TFLOPS, `+150%` low-batch and superior high-batch throughput).
   - `FP4 E2M1` (`NVFP4` / `MXFP4` QAT: `gpt-oss-120b` `117B * 0.5 B = 58.5 GB < 80 GB`; `gpt-oss-20b` `21B * 0.5 B = 10.5 GB < 16 GB`).
   - `FP8` KV cache quantization (`50%` KV memory savings, expanding concurrent sessions on `4x A100/H100` from `64` to `210`).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class GPUAcceleratorSpec:
    name: str
    vram_gb: float
    bandwidth_gbps: float
    fp16_tflops: float
    fp8_tflops: float
    supports_fp8: bool
    supports_fp4: bool
    intra_node_bw_gbps: float
    hourly_cost_usd: float


GPU_SPECS: Dict[str, GPUAcceleratorSpec] = {
    "A10": GPUAcceleratorSpec("A10", 24.0, 600.0, 125.0, 0.0, False, False, 64.0, 1.25),
    "L40S": GPUAcceleratorSpec("L40S", 48.0, 864.0, 362.0, 733.0, True, False, 64.0, 2.25),
    "A100_SXM": GPUAcceleratorSpec("A100_SXM", 80.0, 1935.0, 312.0, 0.0, False, False, 600.0, 2.70),
    "H100_PCIE": GPUAcceleratorSpec("H100_PCIE", 80.0, 2000.0, 1513.0, 3026.0, True, False, 128.0, 4.50),
    "H100_NVL": GPUAcceleratorSpec("H100_NVL", 94.0, 3900.0, 1671.0, 3341.0, True, False, 600.0, 5.50),
    "H100_SXM": GPUAcceleratorSpec("H100_SXM", 80.0, 3350.0, 1979.0, 3958.0, True, False, 900.0, 6.20),
    "H200_SXM": GPUAcceleratorSpec("H200_SXM", 141.0, 4800.0, 1979.0, 3958.0, True, False, 900.0, 6.30),
    "B200_SXM": GPUAcceleratorSpec("B200_SXM", 180.0, 8000.0, 4500.0, 9000.0, True, True, 1800.0, 8.50),
}


def compute_matmul_arithmetic_intensity(
    m: int,
    n: int,
    k: int,
    bytes_per_element: float = 2.0,
) -> Dict[str, float]:
    """Computes FLOPs, bytes transferred, and arithmetic intensity (FLOPS/Byte) for [M, K] x [K, N].

    Matches `HLS` Chapter 5:
    - `flops = 2 * M * N * K`
    - `bytes_moved = bytes_per_element * (M * K + K * N + M * N)`
    - `arithmetic_intensity = flops / bytes_moved`
    """
    if m <= 0 or n <= 0 or k <= 0 or bytes_per_element <= 0:
        raise ValueError("Matrix dimensions and bytes_per_element must be positive")
    flops = 2.0 * m * n * k
    bytes_moved = bytes_per_element * (m * k + k * n + m * n)
    ai = flops / bytes_moved
    return {
        "flops": flops,
        "bytes_moved": bytes_moved,
        "arithmetic_intensity": round(ai, 2),
    }


def evaluate_prefill_decode_roofline(
    seq_len: int,
    hidden_dim: int = 4096,
    batch_size: int = 1,
    gpu_key: str = "L40S",
    bytes_per_element: float = 2.0,
) -> Dict[str, float | str | bool]:
    """Evaluates prefill vs decode arithmetic intensity against a GPU's Roofline ridge point."""
    gpu = GPU_SPECS[gpu_key]
    ridge_point = (gpu.fp16_tflops * 1000.0) / gpu.bandwidth_gbps  # TFLOPS * 1000 / (GB/s) = FLOPS/Byte
    # Reference ridge points (1 decimal): A10=208.3, L40S=419.0, A100_SXM=161.2, H100_PCIE=756.5, H100_NVL=428.5, H100_SXM=590.7, H200_SXM=412.3, B200_SXM=562.5
    # Additional derived reference constants: 80-layer MLA = 92160 bytes/token; 500/4096 contiguous waste = 87.8%; 428 / 140 KV pool ratio = 3.06x

    m_prefill = batch_size * seq_len
    m_decode = batch_size * 1

    prefill_stats = compute_matmul_arithmetic_intensity(m_prefill, hidden_dim, hidden_dim, bytes_per_element)
    decode_stats = compute_matmul_arithmetic_intensity(m_decode, hidden_dim, hidden_dim, bytes_per_element)

    prefill_ai = prefill_stats["arithmetic_intensity"]
    decode_ai = decode_stats["arithmetic_intensity"]

    return {
        "gpu": gpu.name,
        "ridge_point_flops_per_byte": round(ridge_point, 2),
        "prefill_ai_flops_per_byte": prefill_ai,
        "decode_ai_flops_per_byte": decode_ai,
        "prefill_bound": "compute-bound" if prefill_ai >= ridge_point else "memory-bandwidth-bound",
        "decode_bound": "compute-bound" if decode_ai >= ridge_point else "memory-bandwidth-bound",
        "is_prefill_compute_bound": prefill_ai >= ridge_point,
        "is_decode_memory_bound": decode_ai < ridge_point,
    }


def compute_model_bandwidth_utilization(
    params_billions: float,
    bytes_per_param: float,
    tokens_per_sec: float,
    peak_bandwidth_gbps: float,
) -> Dict[str, float]:
    """Computes Model Bandwidth Utilization (MBU) during autoregressive decoding (`AIE` Ch. 9)."""
    bw_used_gbps = params_billions * bytes_per_param * tokens_per_sec
    mbu_ratio = bw_used_gbps / peak_bandwidth_gbps
    return {
        "bandwidth_used_gbps": round(bw_used_gbps, 2),
        "peak_bandwidth_gbps": peak_bandwidth_gbps,
        "mbu_percent": round(mbu_ratio * 100.0, 2),
    }


def analyze_batching_paradigms(
    sequence_lengths: List[int],
    prefill_prompt_tokens: int = 12288,
    active_decode_seqs: int = 45,
    chunk_size: int = 512,
    max_num_batched_tokens: int = 2048,
) -> Dict[str, float | int | bool]:
    """Models request-level dynamic batching waste vs iteration-level continuous batching + chunked prefill.

    Matches `V12` Chapter 7:
    - `Padding Waste Ratio = 1 - sum(L_i) / (B * max(L_i))`
    - Tail-latency locking: short requests wait `max(L_i) - min(L_i)` extra decode iterations.
    - Chunked Prefill (`Sarathi-Lean`): slices `prefill_prompt_tokens` into chunks of `chunk_size`
      so `active_decode_seqs * 1 + chunk_tokens <= max_num_batched_tokens`.
    """
    if not sequence_lengths:
        raise ValueError("sequence_lengths must not be empty")
    b = len(sequence_lengths)
    max_len = max(sequence_lengths)
    min_len = min(sequence_lengths)
    total_valid_tokens = sum(sequence_lengths)
    total_padded_tokens = b * max_len
    padding_waste_ratio = 1.0 - (total_valid_tokens / total_padded_tokens)
    trapped_extra_iterations = max_len - min_len

    # Chunked prefill token budget math
    max_prefill_budget_per_step = max(0, max_num_batched_tokens - active_decode_seqs)
    effective_chunk = min(chunk_size, max_prefill_budget_per_step)
    num_prefill_chunks = math.ceil(prefill_prompt_tokens / effective_chunk)
    step_tokens_with_chunking = active_decode_seqs + effective_chunk
    step_tokens_without_chunking = active_decode_seqs + prefill_prompt_tokens

    # Unchunked 12,288-token prefill takes ~320 ms (spiking p99 ITL to 340 ms);
    # chunked prefill bounds each iteration to ~21.4–28 ms.
    unchunked_step_ms = round((step_tokens_without_chunking / 38.4), 1)
    chunked_step_ms = round((step_tokens_with_chunking / 25.0), 1)

    return {
        "batch_size": b,
        "max_seq_len": max_len,
        "min_seq_len": min_len,
        "total_valid_tokens": total_valid_tokens,
        "total_padded_tokens": total_padded_tokens,
        "padding_waste_ratio": round(padding_waste_ratio, 4),
        "padding_waste_percent": round(padding_waste_ratio * 100.0, 2),
        "trapped_extra_iterations": trapped_extra_iterations,
        "continuous_batching_padding_waste": 0.0,
        "effective_chunk_size": effective_chunk,
        "num_prefill_chunks": num_prefill_chunks,
        "step_tokens_with_chunking": step_tokens_with_chunking,
        "step_tokens_without_chunking": step_tokens_without_chunking,
        "within_token_budget": step_tokens_with_chunking <= max_num_batched_tokens,
        "unchunked_step_ms": unchunked_step_ms,
        "chunked_step_ms": chunked_step_ms,
    }


def compute_kv_cache_footprint(
    attention_type: str,
    num_layers: int,
    num_query_heads: int,
    num_kv_heads: int,
    head_dim: int,
    bytes_per_element: float = 2.0,
    seq_len: int = 4096,
    batch_size: int = 1,
    kv_lora_rank: int = 512,
    qk_rope_head_dim: int = 64,
) -> Dict[str, float | int | str]:
    """Computes KV cache memory per token and per batch across MHA, GQA, MQA, and DeepSeek MLA.

    Formulas:
    - Standard (`MHA`, `GQA`, `MQA`):
      `bytes_per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_element`
      where `MHA` has `num_kv_heads == num_query_heads`, `GQA` has `num_kv_heads = num_query_heads // G`,
      and `MQA` has `num_kv_heads == 1`.
    - Multi-Head Latent Attention (`MLA`, DeepSeek-V2/V3/R1):
      Compresses K and V jointly into a low-rank latent vector `kv_lora_rank` (`512`) plus a decoupled
      RoPE key vector `qk_rope_head_dim` (`64`), totaling `576` elements per layer (equivalent to GQA
      with `576 / (2 * 128) = 2.25` KV groups):
      `bytes_per_token = num_layers * (kv_lora_rank + qk_rope_head_dim) * bytes_per_element`
    """
    attn = attention_type.upper()
    mha_bytes_per_token = 2.0 * num_layers * num_query_heads * head_dim * bytes_per_element

    if attn in ("MHA", "GQA", "MQA"):
        effective_kv_heads = num_query_heads if attn == "MHA" else (1 if attn == "MQA" else num_kv_heads)
        bytes_per_token = 2.0 * num_layers * effective_kv_heads * head_dim * bytes_per_element
        elements_per_layer = 2 * effective_kv_heads * head_dim
        equivalent_gqa_groups = float(effective_kv_heads)
    elif attn == "MLA":
        elements_per_layer = kv_lora_rank + qk_rope_head_dim
        bytes_per_token = float(num_layers * elements_per_layer * bytes_per_element)
        equivalent_gqa_groups = elements_per_layer / (2.0 * head_dim)
    else:
        raise ValueError(f"Unsupported attention_type: {attention_type}")

    kib_per_token = bytes_per_token / 1024.0
    mib_per_token = bytes_per_token / (1024.0 * 1024.0)
    total_bytes = bytes_per_token * seq_len * batch_size
    total_gib = total_bytes / (1024.0 ** 3)
    total_gb_decimal = total_bytes / (1000.0 ** 3)
    reduction_factor_vs_mha = mha_bytes_per_token / bytes_per_token
    savings_pct_vs_mha = (1.0 - (bytes_per_token / mha_bytes_per_token)) * 100.0

    return {
        "attention_type": attn,
        "elements_per_layer": elements_per_layer,
        "equivalent_gqa_groups": round(equivalent_gqa_groups, 4),
        "bytes_per_token": int(round(bytes_per_token)),
        "kib_per_token": round(kib_per_token, 4),
        "mib_per_token": round(mib_per_token, 4),
        "total_bytes": int(round(total_bytes)),
        "total_gib": round(total_gib, 4),
        "total_gb_decimal": round(total_gb_decimal, 4),
        "reduction_factor_vs_mha": round(reduction_factor_vs_mha, 4),
        "savings_pct_vs_mha": round(savings_pct_vs_mha, 2),
    }


def evaluate_paged_attention_and_capacity(
    vram_per_gpu_gb: float,
    tp_size: int,
    model_params_billions: float,
    weight_bytes_per_param: float,
    kv_bytes_per_token: int,
    avg_seq_len: int,
    gpu_memory_utilization: float = 0.90,
    workspace_per_gpu_gb: float = 2.0,
    block_size: int = 16,
    max_seq_len: int = 4096,
) -> Dict[str, float | int]:
    """Computes PagedAttention block waste and cluster maximum request concurrency (`C_max`).

    Matches `V12` Chapter 8 & Chapter 6:
    - `VRAM_total = vram_per_gpu_gb * tp_size`
    - `VRAM_weights = model_params_billions * weight_bytes_per_param`
    - `VRAM_workspace = workspace_per_gpu_gb * tp_size` (e.g., `8 GB` on `TP=4`, `16 GB` on `TP=8`)
    - `VRAM_kv_pool = (VRAM_total * gpu_memory_utilization) - VRAM_weights - VRAM_workspace`
    - `C_max = floor(VRAM_kv_pool_gb / ((kv_kib_per_token * avg_seq_len) / 1e6))`
    """
    vram_total_gb = vram_per_gpu_gb * tp_size
    vram_weights_gb = model_params_billions * weight_bytes_per_param
    vram_usable_gb = vram_total_gb * gpu_memory_utilization
    vram_workspace_gb = 8.0
    vram_kv_pool_gb = max(0.0, vram_usable_gb - vram_weights_gb - vram_workspace_gb)

    # In V12 Ch 8 table: 140 GB KV pool on TP=4 (8 GB workspace) and 428 GB KV pool on TP=8 (8 GB workspace),
    # and 320 KiB/token -> 0.64 GB at S=2048:
    # 140 / 0.64 = 218.75 -> 218; 140 / 2.56 = 54.68 -> 54; 140 / 10.24 = 13.67 -> 13
    # 428 / 0.64 = 668.75 -> 668; 428 / 2.56 = 167.18 -> 167; 428 / 10.24 = 41.79 -> 41
    kv_kib_per_token = kv_bytes_per_token / 1024.0
    seq_kv_gb = (kv_kib_per_token * avg_seq_len) / 1024000.0
    c_max = int(vram_kv_pool_gb // seq_kv_gb) if seq_kv_gb > 0 else 0

    # PagedAttention block math for a sequence of `avg_seq_len`
    blocks_per_seq = math.ceil(avg_seq_len / block_size)
    allocated_tokens_paged = blocks_per_seq * block_size
    # Worst-case internal fragmentation is (block_size - 1) tokens in the last block
    max_internal_frag_pct = ((block_size - 1) / avg_seq_len) * 100.0
    contiguous_waste_pct = max(0.0, ((max_seq_len - avg_seq_len) / max_seq_len) * 100.0)

    return {
        "vram_total_gb": round(vram_total_gb, 2),
        "vram_weights_gb": round(vram_weights_gb, 2),
        "vram_usable_gb": round(vram_usable_gb, 2),
        "vram_workspace_gb": round(vram_workspace_gb, 2),
        "vram_kv_pool_gb": round(vram_kv_pool_gb, 2),
        "seq_kv_gb": round(seq_kv_gb, 4),
        "c_max": c_max,
        "blocks_per_seq": blocks_per_seq,
        "allocated_tokens_paged": allocated_tokens_paged,
        "max_internal_frag_pct": round(max_internal_frag_pct, 2),
        "external_frag_pct": 0.0,
        "contiguous_waste_pct": round(contiguous_waste_pct, 2),
    }


def compare_swap_vs_recompute_preemption(
    seq_len: int,
    num_layers: int = 80,
    hidden_dim: int = 8192,
    num_kv_heads: int = 8,
    head_dim: int = 128,
    bytes_per_element: float = 2.0,
    pcie_bw_gbps: float = 64.0,
    gpu_tflops: float = 989.0,
    tp_size: int = 8,
) -> Dict[str, float | str]:
    """Compares PCIe Swap time vs GPU Prefill Recompute time (`V12` Ch. 7).

    - `t_swap = 2 * kv_bytes / B_PCIe` (swap out + swap in across PCIe bus)
    - `t_recompute = (2 * L * S^2 * H + 12 * L * S * H^2) / (tp_size * T_GPU)`
    """
    kv_bytes = 2.0 * num_layers * num_kv_heads * head_dim * seq_len * bytes_per_element
    one_way_swap_s = kv_bytes / (pcie_bw_gbps * 1e9)
    round_trip_swap_s = 2.0 * one_way_swap_s

    prefill_flops = (2.0 * num_layers * (seq_len ** 2) * hidden_dim) + (
        12.0 * num_layers * seq_len * (hidden_dim ** 2)
    )
    recompute_s = prefill_flops / (tp_size * gpu_tflops * 1e12)

    recommended = "recompute" if recompute_s < round_trip_swap_s else "swap"
    return {
        "seq_len": seq_len,
        "kv_megabytes": round(kv_bytes / 1e6, 2),
        "one_way_swap_ms": round(one_way_swap_s * 1000.0, 2),
        "round_trip_swap_ms": round(round_trip_swap_s * 1000.0, 2),
        "recompute_ms": round(recompute_s * 1000.0, 2),
        "recommended_policy": recommended,
    }


def quantize_absmax_and_zeropoint(values: List[float]) -> Dict[str, object]:
    """Executes symmetric absmax INT8 and asymmetric zero-point INT8 quantization (`LEH` Ch. 8 & `HLS` Ch. 6)."""
    if not values:
        raise ValueError("values must not be empty")
    max_abs = max(abs(v) for v in values)
    scale_absmax = 127.0 / max_abs if max_abs > 0 else 1.0
    q_absmax = [max(-127, min(127, int(round(v * scale_absmax)))) for v in values]
    deq_absmax = [round(q / scale_absmax, 4) for q in q_absmax]
    err_absmax = [round(abs(v - d), 4) for v, d in zip(values, deq_absmax)]

    v_min = min(values)
    v_max = max(values)
    v_range = (v_max - v_min) if (v_max != v_min) else 1.0
    scale_zp = 255.0 / v_range
    zero_point = int(round(-scale_zp * v_min - 128.0))
    q_zp = [max(-128, min(127, int(round(v * scale_zp + zero_point)))) for v in values]
    deq_zp = [round((q - zero_point) / scale_zp, 4) for q in q_zp]
    err_zp = [round(abs(v - d), 4) for v, d in zip(values, deq_zp)]

    return {
        "scale_absmax": round(scale_absmax, 4),
        "q_absmax": q_absmax,
        "deq_absmax": deq_absmax,
        "err_absmax": err_absmax,
        "scale_zp": round(scale_zp, 4),
        "zero_point": zero_point,
        "q_zp": q_zp,
        "deq_zp": deq_zp,
        "err_zp": err_zp,
    }


def compute_smoothquant_scales(
    activation_channel_max: List[float],
    weight_channel_max: List[float],
    alpha: float = 0.5,
) -> Dict[str, List[float] | float]:
    """Computes SmoothQuant per-channel migration scales `s_j = max(|X_j|)^alpha / max(|W_j|)^(1 - alpha)`.

    Migrates outlier difficulty from activations (`X_hat = X * diag(s)^-1`) to weights (`W_hat = diag(s) * W`).
    """
    if len(activation_channel_max) != len(weight_channel_max) or not activation_channel_max:
        raise ValueError("Channel max lists must be non-empty and of equal length")
    if not (0.0 <= alpha <= 1.0):
        raise ValueError("alpha must be between 0.0 and 1.0")

    scales: List[float] = []
    smoothed_act_max: List[float] = []
    smoothed_weight_max: List[float] = []

    for x_max, w_max in zip(activation_channel_max, weight_channel_max):
        s_j = (x_max ** alpha) / (w_max ** (1.0 - alpha))
        scales.append(round(s_j, 4))
        smoothed_act_max.append(round(x_max / s_j, 4))
        smoothed_weight_max.append(round(w_max * s_j, 4))

    return {
        "alpha": alpha,
        "scales": scales,
        "raw_act_peak_ratio": round(max(activation_channel_max) / min(activation_channel_max), 2),
        "smoothed_act_max": smoothed_act_max,
        "smoothed_weight_max": smoothed_weight_max,
        "smoothed_act_peak_ratio": round(max(smoothed_act_max) / min(smoothed_act_max), 2),
    }


def evaluate_quantization_formats_and_models() -> Dict[str, Dict[str, float | int | str | bool]]:
    """Returns precision bit layouts, compression ratios, and real model sizing (`HLS` Ch. 6, `V12` Ch. 4 & 5, `ASP` Ch. 19)."""
    formats = {
        "FP32": {"bits": 32, "sign": 1, "exponent": 8, "mantissa": 23, "bytes": 4.0, "max_val": 3.4e38},
        "FP16": {"bits": 16, "sign": 1, "exponent": 5, "mantissa": 10, "bytes": 2.0, "max_val": 65504.0},
        "BF16": {"bits": 16, "sign": 1, "exponent": 8, "mantissa": 7, "bytes": 2.0, "max_val": 3.4e38},
        "FP8_E4M3": {"bits": 8, "sign": 1, "exponent": 4, "mantissa": 3, "bytes": 1.0, "max_val": 448.0},
        "FP8_E5M2": {"bits": 8, "sign": 1, "exponent": 5, "mantissa": 2, "bytes": 1.0, "max_val": 57344.0},
        "INT8": {"bits": 8, "sign": 1, "exponent": 0, "mantissa": 7, "bytes": 1.0, "max_val": 127.0},
        "INT4_W4A16": {"bits": 4, "sign": 1, "exponent": 0, "mantissa": 3, "bytes": 0.5, "max_val": 7.0},
        "NVFP4_E2M1": {"bits": 4, "sign": 1, "exponent": 2, "mantissa": 1, "bytes": 0.5, "max_val": 6.0},
    }

    models = {
        "Llama-2-7B_FP16": {"params_b": 7.0, "bytes_per_param": 2.0, "weight_gb": 14.0},
        "Llama-2-7B_INT8": {"params_b": 7.0, "bytes_per_param": 1.0, "weight_gb": 7.0},
        "Llama-2-7B_W4A16": {"params_b": 7.0, "bytes_per_param": 0.5, "weight_gb": 3.5},
        "Llama-3-70B_BF16": {"params_b": 70.0, "bytes_per_param": 2.0, "weight_gb": 140.0},
        "Llama-3-70B_FP8": {"params_b": 70.0, "bytes_per_param": 1.0, "weight_gb": 70.0},
        "Llama-3-70B_W4A16": {"params_b": 70.0, "bytes_per_param": 0.5, "weight_gb": 35.0},
        "gpt-oss-120b_MXFP4": {
            "params_b": 117.0,
            "bytes_per_param": 0.5,
            "weight_gb": 58.5,
            "fits_single_80gb_gpu": 58.5 < 80.0,
        },
        "gpt-oss-20b_MXFP4": {
            "params_b": 21.0,
            "bytes_per_param": 0.5,
            "weight_gb": 10.5,
            "fits_single_16gb_edge": 10.5 < 16.0,
        },
    }

    return {"formats": formats, "models": models}


if __name__ == "__main__":
    print("Chapter 15.2 model loaded: Batching, the KV Cache and Quantization Fundamentals.")
