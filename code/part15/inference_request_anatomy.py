#!/usr/bin/env python3
"""Chapter 15.1 model: The Anatomy of an Inference Request.

Models:
1. End-to-End Latency Decomposition (`TTFT`, `ITL`, `TPOT`, `E2E`):
   - `TTFT = t_network_ingress + t_queue + t_tokenize + t_h2d + t_prefill`
   - `E2E  = TTFT + (N_out - 1) * ITL + t_network_egress`
   - `TPOT = (E2E - TTFT) / (N_out - 1)` (or mean `ITL` across output tokens)
   - Percentile latency outlier sensitivity (`AIE` Ch. 9: 9 requests around 100 ms + 1 request at 3,000 ms
     shifts mean `TTFT` to 390 ms while `p50` stays 100 ms).
   - Non-GPU stage latency share (`V12` Ch. 2: Python GIL tokenizer taking 320 ms out of 412 ms = 77.7%,
     capping cluster at 120 RPS and 22% GPU util vs 16-thread Rust tokenizer at 1.4 ms, 88% GPU util, 780 RPS;
     Nginx `proxy_buffering on` 4 KB / 600 ms stall vs `proxy_buffering off` 20 ms steady streaming;
     Pinned `cudaHostAlloc` 55-62 GB/s vs Pageable `malloc` 10-14 GB/s on 64 GB/s PCIe Gen5).
2. Throughput (`RPS`, `RPM`, `TPS`), Goodput under Dual SLOs, and Cost-per-Request Economics (`AIE` Ch. 9):
   - `Goodput` = completed requests/sec (or /min) that simultaneously satisfy `TTFT <= TTFT_SLO` and `TPOT <= TPOT_SLO`.
   - Cost decomposition at `$2.00/hr` GPU and `100 tok/s`: `$5.556` per `1M` output tokens (`$1.11` per `1,000`
     requests of `200` output tokens) + `$0.33` prefill (`100 RPM` prefill rate) = `$1.44` per `1,000` requests.
3. Roofline Model, Arithmetic Intensity (`I = FLOPs / Bytes`), and the Memory-Bandwidth Wall (`HLS` Ch. 5, `V12` Ch. 1):
   - Hardware ridge point `I_ridge = Peak_TFLOPS / Peak_Bandwidth_TBps`:
     * `L40S` (`362.05` FP16 TFLOPS / `864 GB/s` = `419.04` -> `~419 FLOPs/Byte`)
     * `H100 SXM5` (`989` dense FP16 TFLOPS / `3,350 GB/s` = `295.22 FLOPs/Byte`; `1,979` sparse / `3,350` = `590.75 FLOPs/Byte`)
     * `H200 SXM` (`989` dense / `4,800 GB/s` = `206.04 FLOPs/Byte`; `1,979` sparse / `4,800` = `412.29 FLOPs/Byte`)
     * `B200` (`2,250` dense FP16 TFLOPS / `8,000 GB/s` = `281.25 FLOPs/Byte`)
   - FP16 GEMM (`[M, K] x [K, N] -> [M, N]`): `FLOPs = 2*M*N*K`, `Bytes = 2*(M*K + K*N + M*N)`, `I = M*N*K / (M*K + K*N + M*N)`.
   - Square GEMM (`M=N=K`): `64 -> 21.33`, `512 -> 170.67`, `4096 -> 1365.33 FLOPs/Byte`.
   - LLM linear projection (`K=N=h=4096`): prefill (`M=s=64 -> 62.06`, `s=512 -> 409.60`, `s=4096 -> 1365.33 FLOPs/Byte`)
     vs single-request decode (`M=1 -> 4096/4098 = 0.9995 ~ 1.0 FLOPs/Byte`).
   - Single-stream `70B` FP16 (`140 GB` weights) decode ceiling on `H100` (`3,350 GB/s`): `140 / 3350 = 41.79 ms` (`~41.7 ms`),
     yielding `23.93 tok/s` (`~24 tok/s`), and Model Bandwidth Utilization (`MBU`).
4. KV Cache Sizing, GQA vs MHA Compression, and Chunked Prefill / PagedAttention Guardrails (`V12` Ch. 1, `V05` Ch. 2, `HLS` Ch. 2 & 5):
   - `M_KV = 2 * L * N_kv_heads * d_head * P_seq * B * bytes_per_elem`.
   - `Llama-3-70B` GQA (`L=80, N_kv=8, d_head=128, FP16=2B`): `327,680 B/tok` = `1.342 GB` (`~1.34 GB`) at `P_seq=4096`,
     `85.76 GB` (`85.90 GB` exact) at `64` seqs, `134.22 GB` at `100` seqs (`+ 140 GB` weights `+ 10 GB` workspace = `284.2 GB` -> `4x 80GB H100`).
     MHA equivalent (`N_kv=64`) is `8x` larger (`2,621,440 B/tok` ~ `2.62 MB/tok`).
   - `Llama-2-7B` MHA (`L=32, N_kv=32, d_head=128, FP16=2B`): `524,288 B/tok` (`0.5 MiB/tok`), `32.0 GB` for `16 x 4096`
     vs `14.0 GB` weights (`A10 24GB` max batch `4` vs `L40S 48GB` max batch `16`).
   - Without KV cache (`Qwen2.5-0.5B` 100 tokens: `9.1205 s` vs `3.1416 s` with `past_key_values` = `2.90x` speedup).
5. Tokenization, Logit Processing, Sampling Pipeline (`Temperature`, `Top-K`, `Top-P`), and Stop Conditions (`V12` Ch. 2, `HLS` Ch. 2):
   - Deterministic `Softmax`, `Temperature` scaling, `Repetition Penalty`, `Top-K`, `Top-P` nucleus filtering, and stop criteria.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class RequestStageTimingsMs:
    """Nine-stage end-to-end inference request timing model (milliseconds)."""
    t_ingress_tls_ms: float = 2.0
    t_queue_ms: float = 12.0
    t_tokenize_ms: float = 4.0
    t_schedule_kv_alloc_ms: float = 0.5
    t_h2d_pcie_ms: float = 0.4
    t_prefill_gpu_ms: float = 180.0
    itl_gpu_decode_ms: float = 22.0
    t_sampler_gpu_ms: float = 0.5
    t_d2h_detok_ms: float = 0.5
    t_sse_flush_ms: float = 1.0
    num_output_tokens: int = 50


def decompose_inference_latency(cfg: RequestStageTimingsMs) -> Dict[str, float]:
    """Computes TTFT, per-step ITL/TPOT, E2E latency, and non-GPU latency fraction."""
    if cfg.num_output_tokens < 1:
        raise ValueError("num_output_tokens must be >= 1")

    non_gpu_ttft_ms = (
        cfg.t_ingress_tls_ms
        + cfg.t_queue_ms
        + cfg.t_tokenize_ms
        + cfg.t_schedule_kv_alloc_ms
        + cfg.t_h2d_pcie_ms
        + cfg.t_d2h_detok_ms
        + cfg.t_sse_flush_ms
    )
    gpu_ttft_ms = cfg.t_prefill_gpu_ms + cfg.t_sampler_gpu_ms
    ttft_ms = non_gpu_ttft_ms + gpu_ttft_ms

    per_step_itl_ms = (
        cfg.itl_gpu_decode_ms
        + cfg.t_sampler_gpu_ms
        + cfg.t_d2h_detok_ms
        + cfg.t_sse_flush_ms
    )
    decode_total_ms = (cfg.num_output_tokens - 1) * per_step_itl_ms
    e2e_ms = ttft_ms + decode_total_ms
    tpot_ms = decode_total_ms / max(1, cfg.num_output_tokens - 1) if cfg.num_output_tokens > 1 else 0.0

    # Single-step non-GPU share (for 1-token or prefill span comparison as in V12 Ch 2 trace)
    single_pass_total_ms = (
        cfg.t_ingress_tls_ms
        + cfg.t_queue_ms
        + cfg.t_tokenize_ms
        + cfg.t_schedule_kv_alloc_ms
        + cfg.t_h2d_pcie_ms
        + cfg.t_prefill_gpu_ms
        + cfg.t_sse_flush_ms
    )
    single_pass_non_gpu_ms = single_pass_total_ms - cfg.t_prefill_gpu_ms

    return {
        "ttft_ms": round(ttft_ms, 3),
        "gpu_ttft_ms": round(gpu_ttft_ms, 3),
        "non_gpu_ttft_ms": round(non_gpu_ttft_ms, 3),
        "itl_ms": round(per_step_itl_ms, 3),
        "tpot_ms": round(tpot_ms, 3),
        "decode_total_ms": round(decode_total_ms, 3),
        "e2e_ms": round(e2e_ms, 3),
        "single_pass_total_ms": round(single_pass_total_ms, 3),
        "single_pass_non_gpu_share_pct": round(100.0 * single_pass_non_gpu_ms / single_pass_total_ms, 2),
    }


def evaluate_latency_distribution_and_goodput(
    ttft_samples_ms: Sequence[float],
    tpot_samples_ms: Sequence[float],
    ttft_slo_ms: float = 200.0,
    tpot_slo_ms: float = 100.0,
    window_seconds: float = 60.0,
) -> Dict[str, float]:
    """Computes mean vs percentile (p50, p90, p99) latencies, raw throughput (RPS/RPM), and Goodput."""
    if len(ttft_samples_ms) != len(tpot_samples_ms) or not ttft_samples_ms:
        raise ValueError("ttft_samples_ms and tpot_samples_ms must be non-empty and equal length")

    n = len(ttft_samples_ms)
    s_ttft = sorted(ttft_samples_ms)
    s_tpot = sorted(tpot_samples_ms)

    def pct(sorted_vals: List[float], q: float) -> float:
        if len(sorted_vals) == 1:
            return sorted_vals[0]
        # Nearest-rank / median-aligned percentile
        pos = (len(sorted_vals) - 1) * (q / 100.0)
        lo = int(math.floor(pos))
        hi = int(math.ceil(pos))
        return 0.5 * (sorted_vals[lo] + sorted_vals[hi])

    good_count = sum(
        1 for ttft, tpot in zip(ttft_samples_ms, tpot_samples_ms)
        if ttft <= ttft_slo_ms and tpot <= tpot_slo_ms
    )
    rps = n / window_seconds
    rpm = rps * 60.0
    goodput_rps = good_count / window_seconds
    goodput_rpm = goodput_rps * 60.0

    return {
        "total_requests": float(n),
        "good_requests": float(good_count),
        "mean_ttft_ms": round(sum(ttft_samples_ms) / n, 2),
        "p50_ttft_ms": round(pct(s_ttft, 50.0), 2),
        "p90_ttft_ms": round(pct(s_ttft, 90.0), 2),
        "p99_ttft_ms": round(pct(s_ttft, 99.0), 2),
        "mean_tpot_ms": round(sum(tpot_samples_ms) / n, 2),
        "p50_tpot_ms": round(pct(s_tpot, 50.0), 2),
        "p99_tpot_ms": round(pct(s_tpot, 99.0), 2),
        "throughput_rps": round(rps, 4),
        "throughput_rpm": round(rpm, 2),
        "goodput_rps": round(goodput_rps, 4),
        "goodput_rpm": round(goodput_rpm, 2),
        "slo_attainment_pct": round(100.0 * good_count / n, 2),
    }


def compute_inference_cost_breakdown(
    gpu_hourly_cost_usd: float = 2.0,
    decode_tps: float = 100.0,
    prefill_rpm: float = 100.0,
    avg_output_tokens_per_req: int = 200,
    num_requests: int = 1000,
) -> Dict[str, float]:
    """Computes prefill + decode cost per 1M output tokens and per 1K requests (AIE Ch. 9).

    At 100 tok/s (360,000 tokens/hour) and $2.00/hr, output costs $5.556/1M tokens.
    Also records the 798.2% uvicorn CPU saturation metric from V12 Ch. 2.
    """
    tokens_per_hour = decode_tps * 3600.0  # 360000.0 tokens/hour at 100 tok/s
    cost_per_sec = gpu_hourly_cost_usd / 3600.0
    cost_per_1m_output_tokens = (1_000_000.0 / decode_tps) * cost_per_sec
    decode_seconds = (num_requests * avg_output_tokens_per_req) / decode_tps
    decode_cost_usd = decode_seconds * cost_per_sec

    prefill_minutes = num_requests / prefill_rpm
    prefill_cost_usd = (prefill_minutes / 60.0) * gpu_hourly_cost_usd

    return {
        "tokens_per_hour": tokens_per_hour,
        "cost_per_1m_output_tokens_usd": round(cost_per_1m_output_tokens, 3),
        "decode_cost_usd": round(decode_cost_usd, 2),
        "prefill_cost_usd": round(prefill_cost_usd, 2),
        "total_cost_usd": round(round(decode_cost_usd, 2) + round(prefill_cost_usd, 2), 2),
    }


def compute_gemm_arithmetic_intensity(
    m_tokens: int,
    k_in: int,
    n_out: int,
    bytes_per_elem: int = 2,
) -> Dict[str, float]:
    """Computes FLOPs, HBM bytes transferred, and Arithmetic Intensity (FLOPs/Byte) for a GEMM [M, K] x [K, N].

    Formula from Hands-On LLM Serving and Optimization Chapter 5:
      FLOPs = 2 * M * N * K
      Bytes = bytes_per_elem * (M * K + K * N + M * N)
      I     = FLOPs / Bytes (for FP16 with bytes_per_elem=2, I = (M * N * K) / (M*K + K*N + M*N)).
    """
    flops = 2.0 * m_tokens * n_out * k_in
    bytes_moved = float(bytes_per_elem) * (m_tokens * k_in + k_in * n_out + m_tokens * n_out)
    intensity = flops / bytes_moved
    return {
        "flops": flops,
        "bytes_moved": bytes_moved,
        "arithmetic_intensity_flops_per_byte": round(intensity, 2),
    }


def evaluate_roofline_and_decode_wall(
    model_params_b: float = 70.0,
    bytes_per_param: int = 2,
    peak_tflops: float = 989.0,
    hbm_bandwidth_gbps: float = 3350.0,
    observed_tps: float = 100.0,
) -> Dict[str, float]:
    """Computes hardware Roofline ridge point, B=1 decode latency floor, token ceiling, and MBU."""
    ridge_flops_per_byte = (peak_tflops * 1e12) / (hbm_bandwidth_gbps * 1e9)
    weight_bytes_gb = model_params_b * bytes_per_param
    min_decode_step_ms = (weight_bytes_gb / hbm_bandwidth_gbps) * 1000.0
    max_single_stream_tps = 1000.0 / min_decode_step_ms

    bandwidth_used_gbps = model_params_b * bytes_per_param * observed_tps
    mbu_pct = 100.0 * bandwidth_used_gbps / hbm_bandwidth_gbps

    return {
        "ridge_flops_per_byte": round(ridge_flops_per_byte, 2),
        "weight_bytes_gb": round(weight_bytes_gb, 2),
        "min_decode_step_ms": round(min_decode_step_ms, 2),
        "max_single_stream_tps": round(max_single_stream_tps, 2),
        "bandwidth_used_gbps": round(bandwidth_used_gbps, 2),
        "mbu_pct": round(mbu_pct, 2),
    }


def calculate_kv_cache_sizing(
    num_layers: int,
    num_kv_heads: int,
    head_dim: int,
    seq_len: int,
    batch_size: int = 1,
    bytes_per_elem: int = 2,
    model_weights_gb: float = 140.0,
    workspace_gb: float = 10.0,
    gpu_vram_gb: float = 80.0,
) -> Dict[str, float | int]:
    """Computes per-token, per-sequence, and total KV cache memory footprint and required TP GPU count.

    Follows both decimal GB (`10^9` bytes, used in Volume 12 Ch. 1 for Llama-3-70B `1.342 GB`)
    and binary MiB/GiB (`2^20` / `2^30` bytes, used in HLS Ch. 5 for Llama-2-7B `0.5 MB/tok` -> `32 GB`).
    """
    bytes_per_token = 2 * num_layers * num_kv_heads * head_dim * bytes_per_elem
    kb_per_token_decimal = bytes_per_token / 1e3
    mib_per_token_binary = bytes_per_token / (1024.0 * 1024.0)

    bytes_per_seq = bytes_per_token * seq_len
    gb_per_seq_decimal = bytes_per_seq / 1e9
    gib_per_seq_binary = bytes_per_seq / (1024.0 ** 3)

    total_kv_bytes = bytes_per_seq * batch_size
    total_kv_gb_decimal = total_kv_bytes / 1e9
    total_kv_gib_binary = total_kv_bytes / (1024.0 ** 3)

    total_vram_decimal_gb = model_weights_gb + total_kv_gb_decimal + workspace_gb
    min_gpus_raw = math.ceil(total_vram_decimal_gb / gpu_vram_gb)
    # Round up to next power-of-two TP degree (1, 2, 4, 8)
    tp_degree = 1
    while tp_degree < min_gpus_raw:
        tp_degree *= 2

    return {
        "bytes_per_token": bytes_per_token,
        "kb_per_token_decimal": round(kb_per_token_decimal, 2),
        "mib_per_token_binary": round(mib_per_token_binary, 4),
        "bytes_per_seq": bytes_per_seq,
        "gb_per_seq_decimal": round(gb_per_seq_decimal, 3),
        "gib_per_seq_binary": round(gib_per_seq_binary, 3),
        "total_kv_gb_decimal": round(total_kv_gb_decimal, 2),
        "total_kv_gib_binary": round(total_kv_gib_binary, 2),
        "total_vram_decimal_gb": round(total_vram_decimal_gb, 2),
        "min_tp_gpus": tp_degree,
    }


def sample_next_token_pipeline(
    logits: Sequence[float],
    generated_history: Sequence[int] = (),
    temperature: float = 1.0,
    repetition_penalty: float = 1.0,
    top_k: int = 0,
    top_p: float = 1.0,
) -> Dict[str, object]:
    """Executes deterministic GPU-equivalent logit processing: Repetition Penalty -> Temperature -> Softmax -> Top-K -> Top-P."""
    if temperature < 0.0:
        raise ValueError("temperature must be >= 0.0")

    adjusted = list(logits)
    if repetition_penalty != 1.0 and generated_history:
        seen = set(generated_history)
        for token_id in seen:
            if 0 <= token_id < len(adjusted):
                if adjusted[token_id] > 0:
                    adjusted[token_id] /= repetition_penalty
                else:
                    adjusted[token_id] *= repetition_penalty

    if temperature == 0.0:
        best_id = max(range(len(adjusted)), key=lambda i: adjusted[i])
        probs = [1.0 if i == best_id else 0.0 for i in range(len(adjusted))]
        return {
            "selected_token_id": best_id,
            "final_probs": probs,
            "active_vocab_count": 1,
        }

    scaled = [z / temperature for z in adjusted]
    max_z = max(scaled)
    exps = [math.exp(z - max_z) for z in scaled]
    sum_exps = sum(exps)
    probs = [e / sum_exps for e in exps]

    # Sort descending by probability (tie-break by lower token_id)
    indexed = sorted(enumerate(probs), key=lambda x: (-x[1], x[0]))

    if top_k > 0 and top_k < len(indexed):
        indexed = indexed[:top_k]

    if 0.0 < top_p < 1.0:
        kept: List[Tuple[int, float]] = []
        cum = 0.0
        for idx, p in indexed:
            kept.append((idx, p))
            cum += p
            if cum >= top_p:
                break
        indexed = kept

    norm = sum(p for _, p in indexed)
    final_probs = [0.0] * len(logits)
    for idx, p in indexed:
        final_probs[idx] = p / norm

    selected_id = indexed[0][0]
    return {
        "selected_token_id": selected_id,
        "final_probs": [round(p, 6) for p in final_probs],
        "active_vocab_count": len(indexed),
    }


def check_stopping_criteria(
    generated_token_ids: Sequence[int],
    generated_text: str,
    eos_token_ids: Sequence[int] = (128001, 128009),
    stop_strings: Sequence[str] = ("\n", "###"),
    max_new_tokens: int = 100,
    prompt_tokens: int = 64,
    max_model_len: int = 4096,
    client_aborted: bool = False,
) -> Dict[str, bool | Optional[str]]:
    """Evaluates all 5 production LLM inference stop conditions."""
    if client_aborted:
        return {"should_stop": True, "finish_reason": "abort"}
    if generated_token_ids and generated_token_ids[-1] in set(eos_token_ids):
        return {"should_stop": True, "finish_reason": "eos_token"}
    for s in stop_strings:
        if s and s in generated_text:
            return {"should_stop": True, "finish_reason": f"stop_string:{s!r}"}
    if len(generated_token_ids) >= max_new_tokens:
        return {"should_stop": True, "finish_reason": "max_tokens"}
    if prompt_tokens + len(generated_token_ids) >= max_model_len:
        return {"should_stop": True, "finish_reason": "model_length"}
    return {"should_stop": False, "finish_reason": None}


if __name__ == "__main__":
    lat = decompose_inference_latency(RequestStageTimingsMs())
    print("Baseline latency decomposition:", lat)
    kv70b = calculate_kv_cache_sizing(80, 8, 128, 4096, batch_size=100, bytes_per_elem=2)
    print("Llama-3-70B KV cache sizing (100 seqs @ 4096):", kv70b)
