#!/usr/bin/env python3
"""Chapter 15.14 model: Benchmarking: genai-perf, latency percentiles and goodput.

Models:
1. LLM Inference Latency Decomposition, Throughput Metrics, and Percentile Distributions:
   - Deconstructs request latency (`V12` Ch. 10, `DAI` Ch. 10, `AIE` Ch. 9):
     - `TTFT = t_queue + t_preprocess + t_prefill_compute` (`O(N^2)` compute-bound prefill; `< 200 ms` p95 chat
       SLO, `< 1,000 ms` RAG SLO)
     - `ITL_i = t_token_i - t_token_{i-1}` and `TPOT = (E2E - TTFT) / (N_out - 1)` (memory-bandwidth-bound
       decode; `< 25-30 ms` p95 SLO = `> 33.3-40.0 tok/s`; `1` output token has the latency impact of `~100`
       input tokens and costs `2x-4x` more)
     - `E2E = TTFT + (N_out - 1) * ITL + t_network` (a `500`-token response requires `501` forward passes:
       `1` prefill pass + `500` decode passes; two `5.0 s` E2E essays differ drastically when System 1 stalls
       `4.9 s` then dumps `1,000` words in `0.1 s` vs System 2 emitting token 1 at `0.2 s` [`200 ms`] and
       streaming over `4.8 s`)
   - Quantifies `RPS`, `Input_TPS`, `Output_TPS (GTPS)`, and `Total_TPS` on the `vllm benchmark_serving.py`
     `Llama-3-70B` ShareGPT run (`1,000` prompts at `15.0 req/s` in `71.24 s`: `241,042` input tokens,
     `189,410` output tokens, `14.04 req/s`, `2,658.76` output tok/s, `3,383.52` input tok/s, `6,042.27`
     total tok/s; TTFT `mean = 142.18 ms`, `P50 = 112.40 ms`, `P95 = 284.10 ms`, `P99 = 492.50 ms`; ITL
     `mean = 16.42 ms`, `P50 = 15.80 ms`, `P95 = 21.10 ms`, `P99 = 28.40 ms`).
   - Models percentile distributions (`P50`, `P90`, `P95`, `P99`) and why `P99` beats average (`DAI` Ch. 10):
     System A (`100.0 ms` mean, bounded `90-110 ms`) vs System B (`80.1 ms` [`~80 ms`] mean, `95%` at `58.0 ms`
     and `5%` at `500.0 ms` -> `P95 = 500.0 ms`, `P99 = 500.0 ms`), plus `P99 / P50 = 500 / 50 = 10.0x` tail ratio.
2. Queueing Theory (Little's Law `L = lambda * W`), Open-Loop Poisson Arrival vs Closed-Loop Concurrency Sweeps:
   - Verifies Little's Law `L = lambda * W` (`L = L_queue + L_service`) and `M/M/1` queueing delay
     `W = 1 / (mu - lambda)` (`W_q = rho / (mu * (1 - rho))`, where `rho = lambda / mu`).
   - Contrasts closed-loop concurrency sweeps (`L = N` fixed, `lambda_eff = N / W` self-throttling when `W` grows,
     and `perf_analyzer` batch synchronization at `C=64` reporting `120.0 tok/s` vs `180.0 tok/s` open-loop at
     `20.0 req/s`, a `+50.0%` throughput gap) against open-loop Poisson arrivals (`Delta_t ~ Exp(lambda)`,
     `--burstiness 1.0`), plus Locust user ramp (`50` users at `1 user/s`, peaking at `34` active users).
   - Models Triton `perf_analyzer` Lab 02 `dense_net` dynamic batching sweep at `C=64` (`V12` Lab 02):
     No-batch (`520.0 RPS`, `121.5 ms` p99, batch `1.0`), Conservative `B=16, delay=5,000 us` (`2,850.0 RPS`,
     `5.48x`, `8.9 ms` p99, realized batch `13.0`; `450.0 RPS` and `3.1 ms` p99 at `C=1`), Aggressive `B=64,
     delay=50,000 us` (`3,400.0 RPS`, `6.54x`, `48.5 ms` p99 at `C=64` but `51.2 ms` p99 at `C=1`, realized
     batch `48.2`), and misconfigured `500,000 us` (`500 ms`) delay at `C=2` (`4.0 RPS`, `> 500 ms` p99).
3. Goodput, the Latency-Throughput Pareto Frontier, and MLPerf Inference (`Server` vs `Offline`):
   - Computes request-level and GPU-normalized Goodput under joint `(SLO_TTFT, SLO_TPOT)` constraints:
     - High-batch throughput trap (`V12` Ch. 10): `B=128` achieves `180.0 tok/s` raw throughput but violates
       SLOs with `p99 TTFT = 1,200.0 ms` (`> 200.0 ms`) and `p99 ITL = 85.0 ms` (`> 25.0 ms`) (`ttft_bucket{le="200"} = 800 / 4,000 = 20.0%`, `itl_bucket{le="25"} = 300 / 3,900 = 7.69%`), yielding `0.0` SLO-compliant cluster goodput.
     - DistServe Pareto frontier (`ASP` Ch. 17): Under `P90 TTFT <= 400.0 ms` (`0.4 s`) and `P90 TPOT <= 40.0 ms`
       (`0.04 s`), colocated (`1` GPU) sustains `3.0 RPS` TTFT-only and `1.6 RPS` TPOT-only -> `min(3.0, 1.6) = 1.6 RPS/GPU` goodput; disaggregated `2P1D` (`3` GPUs) sustains `2 * 5.6 = 11.2 RPS` prefill and `10.0 RPS` decode -> `min(11.2, 10.0) / 3 = 3.33 RPS/GPU` (`~3.3 RPS/GPU`, `2.08x` per-GPU goodput, up to `7.4x` max goodput and `12.6x` tighter SLOs).
     - MLPerf Inference v5.0 (2025) Server vs Offline benchmarks (`ASP` Ch. 1 & 17, `DAI` Ch. 10):
       Llama 2 70B (`450.0 ms` p99 TTFT, `40.0 ms` p99 TPOT), Llama 3.1 405B (`6,000.0 ms` [`6.0 s`] p99 TTFT,
       `175.0 ms` p99 TPOT), and `GB200 NVL72` (`3.4x` inference speedup, `2.6x` training speedup).
4. Practical Optimization Case Studies (`Qwen3-14B` FP16 vs AWQ on `L40S`, `L40S` PCIe vs `A100` NVLink, Cold Starts, Agents & Gateway CPU):
   - Models `Qwen/Qwen3-14B` on `g6e.2xlarge` (`1x L40S`, `46,068 MiB` total, `45,469 MiB` free, compute cap `8.9`,
     `HLS` Ch. 9): ShareGPT dataset stats (`100` samples: prompt `min=5, max=817, mean=232.60, median=141.50,
     std=241.42`; output `min=4, max=771, mean=220.61, median=164.50, std=210.23`), FP16 (`27.5185 GiB` weights
     in `5.265852 s`, `11.00 GiB` KV = `72,064` tokens, `1.76x` concurrency at `40,960` tokens -> `474.38 tok/s`
     ShareGPT [`227.64` output tok/s, `1.10 req/s`, `104.15 ms` TTFT, `43.24 ms` ITL, `72.15 ms` P99 ITL] and
     `1,123.13 tok/s` Prefix Repetition [`2.37x` gain, `97%` GPU util, `104.64 ms` TTFT, `43.95 ms` ITL, `59.22 ms`
     P99 ITL]) vs 4-bit `Qwen3-14B-AWQ` (`9.3619 GiB` weights in `10.652314 s`, `29.15 GiB` KV = `191,056` tokens
     [`2.65x`], `4.66x` concurrency -> `1,280.0 tok/s` ShareGPT [`2.70x` speedup] and `59.29 ms` TTFT [`-42.0%` vs
     `103.61 ms`]).
   - Models `g6e.12xlarge` (`4x L40S` PCIe) vs `p4d.24xlarge` (`8x A100` NVLink: `TP=4` cuts TTFT `66.0 ms -> 33.0 ms`
     [`-50.0%`] at `3,926.0 TPS`, while `4x DP=1` replicas reach `9,816.0 TPS` [`2.50x`]).
   - Models cold-start penalties (`3-5x` small, `16x` mid-size, `50x+` `70B+` [`30.0 s` vs `100.0 ms` = `300.0x`]),
     multi-step reasoning agent latency (`>= 60.0%` external tool/API/DB calls), scaling efficiency (`81.25%` at `8`
     GPUs; `52.0%` at `64` GPUs = `33.28` [`~33`] effective / `30.72` [`~31`] idle GPUs = `$46,502-$51,609` [`~$50,000`]
     wasted over `336` hours; `155.0 ms` `0%` comm on `1` GPU vs `33.0 ms` `55.0%` comm on `16` GPUs; Amdahl's Law
     `10.0%` serial = `10.0x` max speedup), and `V12` Lab 04 CPU tokenization bottleneck (`1,410.20 ms` -> `44.80 ms`
     p99 [`31.48x`], `13.47 -> 104.17 RPS` [`7.73x`]).
5. Production Failure Scenarios (`V12` Ch. 10 Scenarios 1 & 2) and Accuracy Validation (`DAI` Ch. 10):
   - Scenario 1: Fixed `64`-token synthetic test (`45.0 req/s`, `38.0 ms` p95 TTFT, `45.0 ms` p99 TTFT, `16.2 ms` p95
     ITL, `3,400.0 tok/s`, `42.0 GB` VRAM) vs `4,096`-token production RAG (`64.0x` tokens, `4,096.0x` quadratic
     attention ratio -> `6.2 req/s` [`-86.22%` / `-86%`], `4,820.0 ms` p95 TTFT [`+12,584.21%` / `+12,584%`], `6,400.0 ms`
     p99 TTFT, `24.0%` HTTP 504 timeouts, `28.4 ms` p95 ITL [`+75.31%` / `+75%`], `78.4 GB` VRAM [`+86.67%` / `+86%`]);
     remediated by `--enable-chunked-prefill --max-num-batched-tokens 2048 --max-num-seqs 128` (`290.0 ms` p95 TTFT,
     `18.2 ms` p95 ITL).
   - Scenario 2: Open-loop concurrency collapse (`20.0 -> 30.0 req/s` at `--max-num-seqs 512`: `gpu_cache_usage_perc = 0.99`,
     `waiting = 2 -> 340` in `15.0 s`, `p99 TTFT = 180.0 ms -> 18,200.0 ms`); remediated by `--max-num-seqs 64
     --max-num-batched-tokens 2048` + ingress HTTP 429 at queue `> 50` (`340.0 ms` p99 TTFT, `0` preemptions, `8`
     waiting at `35.0 req/s`).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Sequence, Tuple


def evaluate_latency_decomposition_and_percentiles() -> Dict[str, float]:
    """Decomposes TTFT, ITL/TPOT, E2E latency, throughput, and percentile distributions."""
    # 500 generated tokens = 1 prefill pass + 500 decode passes = 501 forward passes (V12 Ch. 10)
    generated_tokens_500 = 500
    total_forward_passes_500 = 1 + generated_tokens_500

    # Two 5.0-second essay generation systems (1,000 words, V12 Ch. 10 Primer)
    essay_e2e_s = 5.0
    bad_system_ttft_s = 4.9
    bad_system_stream_s = 0.1
    good_system_ttft_s = 0.2
    good_system_stream_s = 4.8

    # Exact E2E latency formula: E2E = TTFT + (N_out - 1) * ITL + t_network
    # Example request: TTFT = 142.18 ms, N_out = 189, ITL = 16.42 ms, t_network = 0.0 ms
    sample_ttft_ms = 142.18
    sample_itl_ms = 16.42
    sample_n_out = 189
    sample_decode_ms = round((sample_n_out - 1) * sample_itl_ms, 2)  # 3086.96 ms
    sample_e2e_ms = sample_ttft_ms + sample_decode_ms  # 3229.14 ms (~3.23 seconds)
    sample_e2e_s = round(sample_e2e_ms / 1000.0, 2)    # 3.23 seconds
    sample_tpot_ms = (sample_e2e_ms - sample_ttft_ms) / (sample_n_out - 1)
    bad_system_ttft_ms = 4900.0
    total_tokens_sum = 241042 + 189410  # 430452 tokens
    conservative_p99_reduction_x = round(121.5 / 8.9, 2)  # 13.65x
    w_queue_24_5_ms = 1960.0
    w_queue_24_5_jump_x = 32.67
    cfs_throttled_p99_ms = 3500.0

    # Production SLO targets (V12 Ch. 10, AIE Ch. 9)
    chat_ttft_slo_p95_ms = 200.0
    rag_ttft_slo_p95_ms = 1000.0
    itl_slo_p95_ms = 25.0
    itl_slo_min_tok_per_s = 1000.0 / itl_slo_p95_ms  # 40.0 tok/s
    anyscale_output_vs_input_latency_ratio = 100.0

    # vllm benchmark_serving.py Llama-3-70B ShareGPT run (V12 Ch. 10)
    num_prompts = 1000
    request_rate_configured_rps = 15.0
    duration_s = 71.24
    total_input_tokens = 241042
    total_output_tokens = 189410
    req_throughput_rps = round(num_prompts / duration_s, 2)  # 14.04 req/s
    input_tps = round(total_input_tokens / duration_s, 2)    # 3383.52 tok/s
    output_tps = round(total_output_tokens / duration_s, 2)  # 2658.76 tok/s
    total_tps = round((total_input_tokens + total_output_tokens) / duration_s, 2)  # 6042.28 (~6042.27 reported)
    vllm_ttft_mean_ms = 142.18
    vllm_ttft_p50_ms = 112.40
    vllm_ttft_p95_ms = 284.10
    vllm_ttft_p99_ms = 492.50
    vllm_itl_mean_ms = 16.42
    vllm_itl_p50_ms = 15.80
    vllm_itl_p95_ms = 21.10
    vllm_itl_p99_ms = 28.40

    # Why P99 matters more than average (DAI Ch. 10):
    # System A: 100 requests uniformly distributed in 90..110 ms -> mean = 100.0 ms, P95 = 109.0 ms, P99 = 110.0 ms
    # System B: 95 requests at 57.8947 ms (~58 ms) + 5 requests (5%) at 500.0 ms -> mean = 80.0 ms, P95 = 500.0 ms, P99 = 500.0 ms
    sys_a_latencies = [90.0 + (20.0 * i / 99.0) for i in range(100)]
    sys_b_latencies = [57.89473684210526] * 95 + [500.0] * 5
    sys_a_mean_ms = round(sum(sys_a_latencies) / len(sys_a_latencies), 1)
    sys_b_mean_ms = round(sum(sys_b_latencies) / len(sys_b_latencies), 1)
    sys_a_p99_ms = round( sorted(sys_a_latencies)[98], 1)
    sys_b_p95_ms = round( sorted(sys_b_latencies)[95], 1)
    sys_b_p99_ms = round( sorted(sys_b_latencies)[98], 1)

    # Tail ratio diagnosis (DAI Ch. 10 Short Answer 2): P50 = 50 ms, P99 = 500 ms -> 10.0x ratio
    tail_diag_p50_ms = 50.0
    tail_diag_p99_ms = 500.0
    tail_diag_ratio_x = round(tail_diag_p99_ms / tail_diag_p50_ms, 2)

    return {
        "generated_tokens_500": float(generated_tokens_500),
        "total_forward_passes_500": float(total_forward_passes_500),
        "essay_e2e_s": essay_e2e_s,
        "bad_system_ttft_s": bad_system_ttft_s,
        "bad_system_stream_s": bad_system_stream_s,
        "good_system_ttft_s": good_system_ttft_s,
        "good_system_stream_s": good_system_stream_s,
        "sample_e2e_ms": round(sample_e2e_ms, 2),
        "sample_tpot_ms": round(sample_tpot_ms, 2),
        "chat_ttft_slo_p95_ms": chat_ttft_slo_p95_ms,
        "rag_ttft_slo_p95_ms": rag_ttft_slo_p95_ms,
        "itl_slo_p95_ms": itl_slo_p95_ms,
        "itl_slo_min_tok_per_s": itl_slo_min_tok_per_s,
        "anyscale_output_vs_input_latency_ratio": anyscale_output_vs_input_latency_ratio,
        "num_prompts": float(num_prompts),
        "request_rate_configured_rps": request_rate_configured_rps,
        "duration_s": duration_s,
        "total_input_tokens": float(total_input_tokens),
        "total_output_tokens": float(total_output_tokens),
        "req_throughput_rps": req_throughput_rps,
        "input_tps": input_tps,
        "output_tps": output_tps,
        "total_tps_computed": total_tps,
        "total_tps_reported": 6042.27,
        "vllm_ttft_mean_ms": vllm_ttft_mean_ms,
        "vllm_ttft_p50_ms": vllm_ttft_p50_ms,
        "vllm_ttft_p95_ms": vllm_ttft_p95_ms,
        "vllm_ttft_p99_ms": vllm_ttft_p99_ms,
        "vllm_itl_mean_ms": vllm_itl_mean_ms,
        "vllm_itl_p50_ms": vllm_itl_p50_ms,
        "vllm_itl_p95_ms": vllm_itl_p95_ms,
        "vllm_itl_p99_ms": vllm_itl_p99_ms,
        "sys_a_mean_ms": sys_a_mean_ms,
        "sys_b_mean_ms": sys_b_mean_ms,
        "sys_a_p99_ms": sys_a_p99_ms,
        "sys_b_p95_ms": sys_b_p95_ms,
        "sys_b_p99_ms": sys_b_p99_ms,
        "tail_diag_p50_ms": tail_diag_p50_ms,
        "tail_diag_p99_ms": tail_diag_p99_ms,
        "tail_diag_ratio_x": tail_diag_ratio_x,
    }


def evaluate_littles_law_and_arrival_models() -> Dict[str, float]:
    """Models Little's Law L = lambda * W, open-loop Poisson vs closed-loop concurrency, and perf_analyzer sweeps."""
    # 1. Little's Law verification on the Llama-3-70B vLLM benchmark:
    # At lambda = 14.04 req/s and mean E2E residency W = 0.14218 + (189.41 - 1) * 0.01642 = 3.23589 s:
    lambda_rps = 14.04
    avg_out_tokens = 189410.0 / 1000.0  # 189.41 tokens
    mean_e2e_s = (142.18 + (avg_out_tokens - 1.0) * 16.42) / 1000.0  # 3.2358922 s
    littles_law_concurrency_l = round(lambda_rps * mean_e2e_s, 2)  # 45.43 in-flight requests

    # Clean worked example of Little's Law: lambda = 20.0 RPS, W = 1.6 s -> L = 32.0 concurrent requests
    worked_lambda_rps = 20.0
    worked_w_s = 1.6
    worked_l_requests = round(worked_lambda_rps * worked_w_s, 2)  # 32.0

    # 2. M/M/1 open-loop queue saturation knee (service capacity mu = 25.0 RPS):
    # W_total = 1 / (mu - lambda), W_queue = rho / (mu * (1 - rho))
    mu_capacity_rps = 25.0
    # At lambda = 15.0 RPS (rho = 0.60):
    rho_15 = 15.0 / mu_capacity_rps  # 0.60
    w_total_15_ms = round(1000.0 / (mu_capacity_rps - 15.0), 2)  # 100.0 ms
    w_queue_15_ms = round(1000.0 * rho_15 / (mu_capacity_rps * (1.0 - rho_15)), 2)  # 60.0 ms
    # At lambda = 22.5 RPS (rho = 0.90):
    rho_22_5 = 22.5 / mu_capacity_rps  # 0.90
    w_total_22_5_ms = round(1000.0 / (mu_capacity_rps - 22.5), 2)  # 400.0 ms (4.0x jump)
    w_queue_22_5_ms = round(1000.0 * rho_22_5 / (mu_capacity_rps * (1.0 - rho_22_5)), 2)  # 360.0 ms (6.0x jump)
    # At lambda = 24.5 RPS (rho = 0.98):
    rho_24_5 = 24.5 / mu_capacity_rps  # 0.98
    w_total_24_5_ms = round(1000.0 / (mu_capacity_rps - 24.5), 2)  # 2000.0 ms (20.0x jump)

    # 3. Closed-loop self-throttling vs Open-loop throughput (V12 Ch. 10 Troubleshooting Table):
    # If closed-loop concurrency is fixed at N = 4 and server latency degrades from W = 0.20 s to W = 1.00 s:
    closed_loop_n = 4
    closed_loop_rps_healthy = round(closed_loop_n / 0.20, 2)   # 20.0 RPS
    closed_loop_rps_degraded = round(closed_loop_n / 1.00, 2)  # 4.0 RPS (5.0x self-throttling)
    # perf_analyzer closed-loop vs open-loop on Llama-70B (V12 Ch. 10):
    perf_analyzer_closed_loop_tps = 120.0
    perf_analyzer_open_loop_tps = 180.0
    open_vs_closed_tps_gain_pct = round(
        ((perf_analyzer_open_loop_tps - perf_analyzer_closed_loop_tps) / perf_analyzer_closed_loop_tps) * 100.0, 2
    )  # 50.0%

    # 4. Triton perf_analyzer dynamic batching sweep at C=64 (V12 Lab 02):
    nobatch_rps = 520.0
    nobatch_p99_ms = 121.5
    conservative_rps = 2850.0
    conservative_p99_ms = 8.9
    conservative_realized_batch = 13.0
    conservative_speedup_x = round(conservative_rps / nobatch_rps, 2)  # 5.48x
    aggressive_rps = 3400.0
    aggressive_p99_c64_ms = 48.5
    aggressive_p99_c1_ms = 51.2
    aggressive_realized_batch = 48.2
    aggressive_speedup_x = round(aggressive_rps / nobatch_rps, 2)  # 6.54x
    misconfig_500ms_c2_rps = 4.0

    # 5. Locust ramp test saturation knee (LLP Ch. 6 Figure 6.11):
    locust_max_users = 50
    locust_spawn_rate = 1
    locust_saturation_knee_users = 34

    return {
        "littles_law_concurrency_l": littles_law_concurrency_l,
        "worked_lambda_rps": worked_lambda_rps,
        "worked_w_s": worked_w_s,
        "worked_l_requests": worked_l_requests,
        "mu_capacity_rps": mu_capacity_rps,
        "w_total_15_ms": w_total_15_ms,
        "w_queue_15_ms": w_queue_15_ms,
        "w_total_22_5_ms": w_total_22_5_ms,
        "w_queue_22_5_ms": w_queue_22_5_ms,
        "w_total_24_5_ms": w_total_24_5_ms,
        "closed_loop_rps_healthy": closed_loop_rps_healthy,
        "closed_loop_rps_degraded": closed_loop_rps_degraded,
        "perf_analyzer_closed_loop_tps": perf_analyzer_closed_loop_tps,
        "perf_analyzer_open_loop_tps": perf_analyzer_open_loop_tps,
        "open_vs_closed_tps_gain_pct": open_vs_closed_tps_gain_pct,
        "nobatch_rps": nobatch_rps,
        "nobatch_p99_ms": nobatch_p99_ms,
        "conservative_rps": conservative_rps,
        "conservative_p99_ms": conservative_p99_ms,
        "conservative_realized_batch": conservative_realized_batch,
        "conservative_speedup_x": conservative_speedup_x,
        "aggressive_rps": aggressive_rps,
        "aggressive_p99_c64_ms": aggressive_p99_c64_ms,
        "aggressive_p99_c1_ms": aggressive_p99_c1_ms,
        "aggressive_realized_batch": aggressive_realized_batch,
        "aggressive_speedup_x": aggressive_speedup_x,
        "misconfig_500ms_c2_rps": misconfig_500ms_c2_rps,
        "locust_max_users": float(locust_max_users),
        "locust_spawn_rate": float(locust_spawn_rate),
        "locust_saturation_knee_users": float(locust_saturation_knee_users),
    }


def evaluate_goodput_and_pareto_frontier() -> Dict[str, float]:
    """Quantifies Goodput vs raw throughput, Pareto frontier points, and MLPerf v5.0 Server/Offline targets."""
    # 1. High-throughput / bad-goodput trap at B = 128 (V12 Ch. 10 Troubleshooting Table):
    # Raw throughput = 180 tok/s, but p99 TTFT = 1,200 ms (SLO < 200 ms) and p99 ITL = 85 ms (SLO < 25 ms).
    # Histogram buckets: ttft_bucket{le="200"} = 800, ttft_bucket{le="2000"} = 4000 -> 20.0% meet TTFT <= 200 ms
    # itl_bucket{le="25"} = 300, itl_bucket{le="100"} = 3900 -> 7.69% meet ITL <= 25 ms
    b128_raw_tps = 180.0
    b128_p99_ttft_ms = 1200.0
    b128_p99_itl_ms = 85.0
    ttft_bucket_le_200 = 800
    ttft_bucket_le_2000 = 4000
    itl_bucket_le_25 = 300
    itl_bucket_le_100 = 3900
    ttft_slo_pass_pct = round((ttft_bucket_le_200 / ttft_bucket_le_2000) * 100.0, 2)  # 20.0%
    itl_slo_pass_pct = round((itl_bucket_le_25 / itl_bucket_le_100) * 100.0, 2)       # 7.69%

    # 2. DistServe Colocated vs 2P1D Disaggregated Goodput (ASP Ch. 17 Figure 17-2):
    # SLOs: P90 TTFT <= 400.0 ms (0.4 s) and P90 TPOT <= 40.0 ms (0.04 s)
    slo_p90_ttft_ms = 400.0
    slo_p90_tpot_ms = 40.0
    colocated_ttft_bound_rps = 3.0
    colocated_tpot_bound_rps = 1.6
    colocated_goodput_per_gpu = min(colocated_ttft_bound_rps, colocated_tpot_bound_rps)  # 1.6 RPS/GPU

    prefill_gpus = 2
    decode_gpus = 1
    total_gpus = prefill_gpus + decode_gpus  # 3 GPUs
    prefill_rps_per_gpu = 5.6
    total_prefill_rps = round(prefill_gpus * prefill_rps_per_gpu, 2)  # 11.2 RPS
    total_decode_rps = 10.0
    cluster_goodput_rps = min(total_prefill_rps, total_decode_rps)  # 10.0 RPS
    disagg_goodput_per_gpu_exact = round(cluster_goodput_rps / total_gpus, 2)  # 3.33 RPS/GPU
    disagg_goodput_per_gpu_reported = 3.3
    goodput_gain_x = round(disagg_goodput_per_gpu_exact / colocated_goodput_per_gpu, 2)  # 2.08x

    # 3. Concurrency sweep Pareto frontier (C in {1, 8, 16, 32, 64, 128}) under p95 TTFT <= 300 ms & p95 ITL <= 25 ms:
    # (concurrency, raw_output_tps, p95_ttft_ms, p95_itl_ms)
    sweep_points: List[Tuple[int, float, float, float]] = [
        (1, 58.0, 62.0, 14.5),
        (8, 420.0, 110.0, 16.2),
        (16, 780.0, 165.0, 18.4),
        (32, 1340.0, 245.0, 22.8),   # Pareto-optimal Goodput operating point (meets both <= 300 ms and <= 25 ms)
        (64, 1890.0, 480.0, 29.5),   # Violates both TTFT (480 > 300) and ITL (29.5 > 25)
        (128, 2150.0, 1420.0, 54.0), # Severe queue & ITL degradation
    ]
    valid_points = [pt for pt in sweep_points if pt[2] <= 300.0 and pt[3] <= 25.0]
    best_c, best_goodput_tps, best_ttft_ms, best_itl_ms = max(valid_points, key=lambda x: x[1])
    max_raw_tps = max(pt[1] for pt in sweep_points)
    over_batch_waste_tps = round(max_raw_tps - best_goodput_tps, 2)  # 810.0 tok/s exceeds SLO

    # 4. MLPerf Inference v5.0 (2025) Server SLOs & GB200 NVL72 gains (ASP Ch. 1 & Ch. 17):
    mlperf_70b_ttft_p99_ms = 450.0
    mlperf_70b_tpot_p99_ms = 40.0
    mlperf_405b_ttft_p99_ms = 6000.0
    mlperf_405b_tpot_p99_ms = 175.0
    gb200_nvl72_infer_gain_x = 3.4
    gb200_nvl72_train_gain_x = 2.6

    return {
        "b128_raw_tps": b128_raw_tps,
        "b128_p99_ttft_ms": b128_p99_ttft_ms,
        "b128_p99_itl_ms": b128_p99_itl_ms,
        "ttft_slo_pass_pct": ttft_slo_pass_pct,
        "itl_slo_pass_pct": itl_slo_pass_pct,
        "slo_p90_ttft_ms": slo_p90_ttft_ms,
        "slo_p90_tpot_ms": slo_p90_tpot_ms,
        "colocated_goodput_per_gpu": colocated_goodput_per_gpu,
        "total_prefill_rps": total_prefill_rps,
        "total_decode_rps": total_decode_rps,
        "cluster_goodput_rps": cluster_goodput_rps,
        "disagg_goodput_per_gpu_exact": disagg_goodput_per_gpu_exact,
        "disagg_goodput_per_gpu_reported": disagg_goodput_per_gpu_reported,
        "goodput_gain_x": goodput_gain_x,
        "pareto_optimal_concurrency": float(best_c),
        "pareto_optimal_goodput_tps": best_goodput_tps,
        "pareto_optimal_ttft_ms": best_ttft_ms,
        "pareto_optimal_itl_ms": best_itl_ms,
        "max_raw_tps": max_raw_tps,
        "over_batch_waste_tps": over_batch_waste_tps,
        "mlperf_70b_ttft_p99_ms": mlperf_70b_ttft_p99_ms,
        "mlperf_70b_tpot_p99_ms": mlperf_70b_tpot_p99_ms,
        "mlperf_405b_ttft_p99_ms": mlperf_405b_ttft_p99_ms,
        "mlperf_405b_tpot_p99_ms": mlperf_405b_tpot_p99_ms,
        "gb200_nvl72_infer_gain_x": gb200_nvl72_infer_gain_x,
        "gb200_nvl72_train_gain_x": gb200_nvl72_train_gain_x,
    }


def evaluate_qwen3_14b_and_scaling_benchmarks() -> Dict[str, float]:
    """Models Qwen3-14B FP16 vs AWQ on L40S, L40S PCIe vs A100 NVLink scaling, cold starts, and efficiency."""
    # 1. Hardware & Dataset stats (HLS Ch. 9):
    l40s_total_mib = 46068.0
    l40s_free_mib = 45469.0
    l40s_compute_cap = 8.9
    sharegpt_prompt_min = 5.0
    sharegpt_prompt_max = 817.0
    sharegpt_prompt_mean = 232.60
    sharegpt_prompt_median = 141.50
    sharegpt_prompt_std = 241.42
    sharegpt_output_min = 4.0
    sharegpt_output_max = 771.0
    sharegpt_output_mean = 220.61
    sharegpt_output_median = 164.50
    sharegpt_output_std = 210.23

    # 2. Qwen3-14B FP16 baseline vs Qwen3-14B-AWQ 4-bit on L40S (HLS Ch. 9 Steps 4-6):
    fp16_weights_gib = 27.5185
    fp16_load_s = 5.265852
    fp16_kv_gib = 11.00
    fp16_total_occupied_gib = 38.5
    fp16_kv_tokens = 72064
    fp16_max_concurrency_40k = 1.76

    # ShareGPT 2,000 prompts at 10 RPS (duration 1,810.09 s):
    fp16_sharegpt_duration_s = 1810.09
    fp16_sharegpt_in_tokens = 446619
    fp16_sharegpt_out_tokens = 412052
    fp16_sharegpt_rps = 1.10
    fp16_sharegpt_out_tps = 227.64
    fp16_sharegpt_total_tps = 474.38
    fp16_sharegpt_ttft_ms = 104.15
    fp16_sharegpt_itl_mean_ms = 43.24
    fp16_sharegpt_itl_median_ms = 42.43
    fp16_sharegpt_itl_p99_ms = 72.15

    # Prefix Repetition 1,000 prompts at 5 RPS (duration 569.00 s, 97% GPU util):
    fp16_prefix_duration_s = 569.00
    fp16_prefix_in_tokens = 512000
    fp16_prefix_out_tokens = 127066
    fp16_prefix_rps = 1.76
    fp16_prefix_out_tps = 223.31
    fp16_prefix_total_tps = 1123.13
    fp16_prefix_ttft_ms = 104.64
    fp16_prefix_itl_mean_ms = 43.95
    fp16_prefix_itl_median_ms = 42.82
    fp16_prefix_itl_p99_ms = 59.22
    prefix_cache_tps_gain_x = round(fp16_prefix_total_tps / fp16_sharegpt_total_tps, 2)  # 2.37x

    # AWQ 4-bit quantized Qwen3-14B-AWQ:
    awq_weights_gib = 9.3619
    awq_load_s = 10.652314
    awq_kv_gib = 29.15
    awq_kv_tokens = 191056
    awq_max_concurrency_40k = 4.66
    kv_token_capacity_gain_x = round(awq_kv_tokens / fp16_kv_tokens, 2)  # 2.65x
    awq_sharegpt_total_tps = 1280.0
    awq_tps_gain_x = round(awq_sharegpt_total_tps / 474.0, 2)  # 2.70x (2.7x reported)
    fp16_fig9_2_ttft_ms = 103.61
    awq_fig9_2_ttft_ms = 59.29
    awq_ttft_reduction_pct = round(
        ((fp16_fig9_2_ttft_ms - awq_fig9_2_ttft_ms) / fp16_fig9_2_ttft_ms) * 100.0, 2
    )  # 42.78% (~42% reported)

    # 3. Distributed serving: p4d.24xlarge (A100 NVLink) TP=4 vs 4x DP=1 replicas (HLS Ch. 9 Step 8):
    p4d_tp1_ttft_ms = 66.0
    p4d_tp4_ttft_ms = 33.0
    p4d_tp4_ttft_reduction_pct = round(((p4d_tp1_ttft_ms - p4d_tp4_ttft_ms) / p4d_tp1_ttft_ms) * 100.0, 2)  # 50.0%
    p4d_tp4_total_tps = 3926.0
    p4d_dp4_total_tps = 9816.0
    p4d_dp_vs_tp_gain_x = round(p4d_dp4_total_tps / p4d_tp4_total_tps, 2)  # 2.50x (nearly triple)

    # 4. DAI Ch. 10 benchmarks: SGLang RadixAttention gain, cold starts, reasoning agents, scaling & Amdahl's Law:
    sglang_radix_gain_pct = 40.0
    cold_start_small_min_x = 3.0
    cold_start_small_max_x = 5.0
    cold_start_mid_x = 16.0
    cold_start_70b_min_x = 50.0
    cold_start_30s_vs_100ms_x = round(30.0 / 0.100, 1)  # 300.0x
    agent_external_call_share_pct = 60.0

    # Scaling efficiency (DAI Ch. 10):
    # 8 GPUs delivering 6.5x speedup -> 6.5 / 8 = 81.25%
    eff_8gpu_pct = round((6.5 / 8.0) * 100.0, 2)  # 81.25%
    # 64 GPUs at 52% scaling efficiency -> 33.28 (~33) effective GPUs, 30.72 (~31) idle GPUs over 336 hours (2 weeks)
    eff_64gpu_pct = 52.0
    effective_gpus_64 = round(64.0 * (eff_64gpu_pct / 100.0), 2)  # 33.28 (~33)
    wasted_gpus_64 = round(64.0 - effective_gpus_64, 2)           # 30.72 (~31)
    two_week_hours = 14 * 24  # 336 hours
    wasted_cost_at_4_50_usd = round(31.0 * two_week_hours * 4.80, 2)  # ~$50,000 ($49,996.80)
    # Training iteration time breakdown (DAI Ch. 10 Fig 10.1): 155 ms (0% comm) on 1 GPU -> 33 ms (55% comm) on 16 GPUs
    iter_1gpu_ms = 155.0
    iter_16gpu_ms = 33.0
    comm_share_16gpu_pct = 55.0
    # Amdahl's Law with s = 0.10 (10% serial work): max speedup at N -> inf is 1 / 0.10 = 10.0x
    amdahl_serial_fraction = 0.10
    amdahl_max_speedup_x = round(1.0 / amdahl_serial_fraction, 2)  # 10.0x

    # 5. V12 Lab 04 CPU Tokenization / Preprocessing Bottleneck Remediation:
    lab04_unfixed_rps = 13.47
    lab04_unfixed_total_p99_ms = 1410.20
    lab04_unfixed_cpu_p99_ms = 1395.80
    lab04_unfixed_triton_p99_ms = 18.10
    lab04_fixed_rps = 104.17
    lab04_fixed_total_p99_ms = 44.80
    lab04_fixed_cpu_p99_ms = 31.00
    lab04_fixed_triton_p99_ms = 13.50
    lab04_rps_gain_x = round(lab04_fixed_rps / lab04_unfixed_rps, 2)  # 7.73x
    lab04_p99_reduction_x = round(lab04_unfixed_total_p99_ms / lab04_fixed_total_p99_ms, 2)  # 31.48x

    return {
        "l40s_total_mib": l40s_total_mib,
        "l40s_free_mib": l40s_free_mib,
        "l40s_compute_cap": l40s_compute_cap,
        "sharegpt_prompt_mean": sharegpt_prompt_mean,
        "sharegpt_prompt_median": sharegpt_prompt_median,
        "sharegpt_prompt_std": sharegpt_prompt_std,
        "sharegpt_output_mean": sharegpt_output_mean,
        "sharegpt_output_median": sharegpt_output_median,
        "sharegpt_output_std": sharegpt_output_std,
        "fp16_weights_gib": fp16_weights_gib,
        "fp16_kv_gib": fp16_kv_gib,
        "fp16_kv_tokens": float(fp16_kv_tokens),
        "fp16_max_concurrency_40k": fp16_max_concurrency_40k,
        "fp16_sharegpt_total_tps": fp16_sharegpt_total_tps,
        "fp16_sharegpt_out_tps": fp16_sharegpt_out_tps,
        "fp16_sharegpt_ttft_ms": fp16_sharegpt_ttft_ms,
        "fp16_sharegpt_itl_mean_ms": fp16_sharegpt_itl_mean_ms,
        "fp16_sharegpt_itl_p99_ms": fp16_sharegpt_itl_p99_ms,
        "fp16_prefix_total_tps": fp16_prefix_total_tps,
        "fp16_prefix_ttft_ms": fp16_prefix_ttft_ms,
        "fp16_prefix_itl_p99_ms": fp16_prefix_itl_p99_ms,
        "prefix_cache_tps_gain_x": prefix_cache_tps_gain_x,
        "awq_weights_gib": awq_weights_gib,
        "awq_kv_gib": awq_kv_gib,
        "awq_kv_tokens": float(awq_kv_tokens),
        "awq_max_concurrency_40k": awq_max_concurrency_40k,
        "kv_token_capacity_gain_x": kv_token_capacity_gain_x,
        "awq_sharegpt_total_tps": awq_sharegpt_total_tps,
        "awq_tps_gain_x": awq_tps_gain_x,
        "fp16_fig9_2_ttft_ms": fp16_fig9_2_ttft_ms,
        "awq_fig9_2_ttft_ms": awq_fig9_2_ttft_ms,
        "awq_ttft_reduction_pct": awq_ttft_reduction_pct,
        "p4d_tp1_ttft_ms": p4d_tp1_ttft_ms,
        "p4d_tp4_ttft_ms": p4d_tp4_ttft_ms,
        "p4d_tp4_ttft_reduction_pct": p4d_tp4_ttft_reduction_pct,
        "p4d_tp4_total_tps": p4d_tp4_total_tps,
        "p4d_dp4_total_tps": p4d_dp4_total_tps,
        "p4d_dp_vs_tp_gain_x": p4d_dp_vs_tp_gain_x,
        "sglang_radix_gain_pct": sglang_radix_gain_pct,
        "cold_start_mid_x": cold_start_mid_x,
        "cold_start_70b_min_x": cold_start_70b_min_x,
        "cold_start_30s_vs_100ms_x": cold_start_30s_vs_100ms_x,
        "agent_external_call_share_pct": agent_external_call_share_pct,
        "eff_8gpu_pct": eff_8gpu_pct,
        "eff_64gpu_pct": eff_64gpu_pct,
        "effective_gpus_64": effective_gpus_64,
        "wasted_gpus_64": wasted_gpus_64,
        "two_week_hours": float(two_week_hours),
        "iter_1gpu_ms": iter_1gpu_ms,
        "iter_16gpu_ms": iter_16gpu_ms,
        "comm_share_16gpu_pct": comm_share_16gpu_pct,
        "amdahl_max_speedup_x": amdahl_max_speedup_x,
        "lab04_unfixed_rps": lab04_unfixed_rps,
        "lab04_unfixed_total_p99_ms": lab04_unfixed_total_p99_ms,
        "lab04_fixed_rps": lab04_fixed_rps,
        "lab04_fixed_total_p99_ms": lab04_fixed_total_p99_ms,
        "lab04_rps_gain_x": lab04_rps_gain_x,
        "lab04_p99_reduction_x": lab04_p99_reduction_x,
    }


def evaluate_failure_scenarios_and_accuracy() -> Dict[str, float]:
    """Models V12 Ch. 10 Failure Scenarios 1 & 2, Troubleshooting Table variances, and DAI Ch. 10 accuracy checks."""
    # Scenario 1: Fixed 64-token synthetic test vs 4,096-token production RAG on 4x H100 Llama-3-70B (V12 Ch. 10)
    synth_prompt_tokens = 64
    prod_prompt_tokens = 4096
    prompt_token_ratio_x = prod_prompt_tokens / synth_prompt_tokens  # 64.0x
    quadratic_attn_ratio_x = (prod_prompt_tokens / synth_prompt_tokens) ** 2  # 4096.0x

    synth_rps = 45.0
    prod_rps = 6.2
    rps_drop_pct = round(((prod_rps - synth_rps) / synth_rps) * 100.0, 2)  # -86.22% (-86% reported)

    synth_p95_ttft_ms = 38.0
    prod_p95_ttft_ms = 4820.0
    ttft_spike_pct = round(((prod_p95_ttft_ms - synth_p95_ttft_ms) / synth_p95_ttft_ms) * 100.0, 2)  # +12584.21% (+12,584% reported)
    prod_p99_ttft_ms = 6400.0
    gateway_504_timeout_pct = 24.0

    synth_p95_itl_ms = 16.2
    prod_p95_itl_ms = 28.4
    itl_spike_pct = round(((prod_p95_itl_ms - synth_p95_itl_ms) / synth_p95_itl_ms) * 100.0, 2)  # +75.31% (+75% reported)

    synth_vram_gb = 42.0
    prod_vram_gb = 78.4
    vram_spike_pct = round(((prod_vram_gb - synth_vram_gb) / synth_vram_gb) * 100.0, 2)  # +86.67% (+86% reported)

    # Remediated with --enable-chunked-prefill --max-num-batched-tokens 2048 --max-num-seqs 128:
    remediated_p95_ttft_ms = 290.0
    remediated_p95_itl_ms = 18.2
    ttft_recovery_x = round(prod_p95_ttft_ms / remediated_p95_ttft_ms, 2)  # 16.62x improvement

    # Scenario 2: Open-loop concurrency collapse & KV cache preemption loop (V12 Ch. 10)
    # Jumping 20 -> 30 req/s with --max-num-seqs 512:
    collapse_waiting_before = 2.0
    collapse_waiting_after = 340.0
    collapse_window_s = 15.0
    collapse_kv_usage_ratio = 0.99
    collapse_p99_ttft_before_ms = 180.0
    collapse_p99_ttft_after_ms = 18200.0
    collapse_ttft_spike_x = round(collapse_p99_ttft_after_ms / collapse_p99_ttft_before_ms, 2)  # 101.11x

    # Remediated with --max-num-seqs 64 --max-num-batched-tokens 2048 + ingress HTTP 429 at queue > 50 (tested at 35 req/s):
    remediated_35rps_waiting = 8.0
    remediated_35rps_preemptions = 0.0
    remediated_35rps_p99_ttft_ms = 340.0

    # Production Troubleshooting Table additional real-world gaps (V12 Ch. 10):
    # (a) 10-token / avg 45-token benchmark (200 tok/s) vs avg 3,200-token production (80 tok/s -> 2.5x gap)
    bench_short_tps = 200.0
    prod_long_tps = 80.0
    # (b) Short-prompt benchmark p99 ITL (45 ms) vs 2K median / 16K p99 production p99 ITL (280 ms -> 6.22x / 6.2x worse)
    bench_p99_itl_ms = 45.0
    prod_p99_itl_ms = 280.0
    prod_itl_degradation_x = round(prod_p99_itl_ms / bench_p99_itl_ms, 2)  # 6.22x (6.2x reported)

    # Accuracy validation metrics (DAI Ch. 10):
    int8_throughput_gain_x = 2.0
    int8_math_accuracy_drop_pct = 15.0
    stat_sig_alpha = 0.01
    noise_p_value = 0.30
    regression_p_value = 0.001

    return {
        "synth_prompt_tokens": float(synth_prompt_tokens),
        "prod_prompt_tokens": float(prod_prompt_tokens),
        "prompt_token_ratio_x": prompt_token_ratio_x,
        "quadratic_attn_ratio_x": quadratic_attn_ratio_x,
        "synth_rps": synth_rps,
        "prod_rps": prod_rps,
        "rps_drop_pct_exact": rps_drop_pct,
        "rps_drop_pct_reported": -86.0,
        "synth_p95_ttft_ms": synth_p95_ttft_ms,
        "prod_p95_ttft_ms": prod_p95_ttft_ms,
        "ttft_spike_pct_exact": ttft_spike_pct,
        "ttft_spike_pct_reported": 12584.0,
        "prod_p99_ttft_ms": prod_p99_ttft_ms,
        "gateway_504_timeout_pct": gateway_504_timeout_pct,
        "synth_p95_itl_ms": synth_p95_itl_ms,
        "prod_p95_itl_ms": prod_p95_itl_ms,
        "itl_spike_pct_exact": itl_spike_pct,
        "itl_spike_pct_reported": 75.0,
        "synth_vram_gb": synth_vram_gb,
        "prod_vram_gb": prod_vram_gb,
        "vram_spike_pct_exact": vram_spike_pct,
        "vram_spike_pct_reported": 86.0,
        "remediated_p95_ttft_ms": remediated_p95_ttft_ms,
        "remediated_p95_itl_ms": remediated_p95_itl_ms,
        "ttft_recovery_x": ttft_recovery_x,
        "collapse_waiting_before": collapse_waiting_before,
        "collapse_waiting_after": collapse_waiting_after,
        "collapse_window_s": collapse_window_s,
        "collapse_kv_usage_ratio": collapse_kv_usage_ratio,
        "collapse_p99_ttft_before_ms": collapse_p99_ttft_before_ms,
        "collapse_p99_ttft_after_ms": collapse_p99_ttft_after_ms,
        "collapse_ttft_spike_x": collapse_ttft_spike_x,
        "remediated_35rps_waiting": remediated_35rps_waiting,
        "remediated_35rps_preemptions": remediated_35rps_preemptions,
        "remediated_35rps_p99_ttft_ms": remediated_35rps_p99_ttft_ms,
        "bench_short_tps": bench_short_tps,
        "prod_long_tps": prod_long_tps,
        "bench_p99_itl_ms": bench_p99_itl_ms,
        "prod_p99_itl_ms": prod_p99_itl_ms,
        "prod_itl_degradation_x": prod_itl_degradation_x,
        "int8_throughput_gain_x": int8_throughput_gain_x,
        "int8_math_accuracy_drop_pct": int8_math_accuracy_drop_pct,
        "stat_sig_alpha": stat_sig_alpha,
        "noise_p_value": noise_p_value,
        "regression_p_value": regression_p_value,
    }
