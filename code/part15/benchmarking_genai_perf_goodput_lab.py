#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.14: Benchmarking: genai-perf, latency percentiles and goodput."""

from __future__ import annotations
import sys
from benchmarking_genai_perf_goodput import (
    evaluate_latency_decomposition_and_percentiles,
    evaluate_littles_law_and_arrival_models,
    evaluate_goodput_and_pareto_frontier,
    evaluate_qwen3_14b_and_scaling_benchmarks,
    evaluate_failure_scenarios_and_accuracy,
)


def run_lab() -> int:
    print("=== Chapter 15.14 Lab: Benchmarking, Latency Percentiles, and Goodput Verification ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Latency decomposition, throughput metrics, and percentile distributions
    ld = evaluate_latency_decomposition_and_percentiles()
    check(
        "1. Generating 500 output tokens requires 501 forward passes (1 prefill + 500 decode), and two 5.0 s E2E systems differ between 4.9 s TTFT + 0.1 s dump vs 0.2 s TTFT + 4.8 s stream",
        ld["generated_tokens_500"] == 500.0
        and ld["total_forward_passes_500"] == 501.0
        and ld["essay_e2e_s"] == 5.0
        and ld["bad_system_ttft_s"] == 4.9
        and ld["good_system_ttft_s"] == 0.2,
    )

    check(
        "2. Exact E2E latency E2E = TTFT + (N_out - 1) * ITL yields 3,229.14 ms for TTFT = 142.18 ms, N_out = 189, ITL = 16.42 ms, and TPOT = (E2E - TTFT) / (N_out - 1) = 16.42 ms",
        ld["sample_e2e_ms"] == 3229.14
        and ld["sample_tpot_ms"] == 16.42,
    )

    check(
        "3. Production p95 SLOs target < 200 ms TTFT for chat, < 1,000 ms TTFT for RAG, and < 25 ms ITL (> 40.0 tok/s), with 1 output token having the latency impact of ~100 input tokens",
        ld["chat_ttft_slo_p95_ms"] == 200.0
        and ld["rag_ttft_slo_p95_ms"] == 1000.0
        and ld["itl_slo_p95_ms"] == 25.0
        and ld["itl_slo_min_tok_per_s"] == 40.0
        and ld["anyscale_output_vs_input_latency_ratio"] == 100.0,
    )

    check(
        "4. vLLM benchmark_serving.py on Llama-3-70B (1,000 ShareGPT prompts at 15.0 RPS in 71.24 s; 241,042 in + 189,410 out tokens) achieves 14.04 RPS, 3,383.52 input tok/s, 2,658.76 output tok/s, and 6,042.27 total tok/s",
        ld["num_prompts"] == 1000.0
        and ld["duration_s"] == 71.24
        and ld["req_throughput_rps"] == 14.04
        and ld["input_tps"] == 3383.52
        and ld["output_tps"] == 2658.76
        and ld["total_tps_reported"] == 6042.27,
    )

    check(
        "5. Llama-3-70B ShareGPT percentiles report TTFT (mean 142.18 ms, P50 112.40 ms, P95 284.10 ms, P99 492.50 ms) and ITL (mean 16.42 ms, P50 15.80 ms, P95 21.10 ms, P99 28.40 ms)",
        ld["vllm_ttft_mean_ms"] == 142.18
        and ld["vllm_ttft_p50_ms"] == 112.40
        and ld["vllm_ttft_p95_ms"] == 284.10
        and ld["vllm_ttft_p99_ms"] == 492.50
        and ld["vllm_itl_mean_ms"] == 16.42
        and ld["vllm_itl_p50_ms"] == 15.80
        and ld["vllm_itl_p95_ms"] == 21.10
        and ld["vllm_itl_p99_ms"] == 28.40,
    )

    check(
        "6. System B (80.0 ms mean, 5% at 500.0 ms -> P95/P99 = 500.0 ms) has lower average latency than System A (100.0 ms mean, P99 = 110.0 ms) but 4.55x worse tail latency, and P50 = 50 ms vs P99 = 500 ms yields a 10.0x tail ratio",
        ld["sys_a_mean_ms"] == 100.0
        and ld["sys_b_mean_ms"] == 80.0
        and ld["sys_b_p95_ms"] == 500.0
        and ld["sys_b_p99_ms"] == 500.0
        and ld["tail_diag_ratio_x"] == 10.0,
    )

    # 2. Queueing theory (Little's Law), Open-Loop Poisson vs Closed-Loop Concurrency
    ll = evaluate_littles_law_and_arrival_models()
    check(
        "7. Little's Law L = lambda * W yields L = 32.0 in-flight requests at lambda = 20.0 RPS and W = 1.6 s, and L = 45.43 requests for the 70B ShareGPT run (14.04 RPS * 3.2359 s)",
        ll["worked_l_requests"] == 32.0
        and ll["littles_law_concurrency_l"] == 45.43,
    )

    check(
        "8. In an M/M/1 queue with capacity mu = 25.0 RPS, increasing arrival rate lambda from 15.0 RPS (rho=0.60) to 22.5 RPS (rho=0.90) and 24.5 RPS (rho=0.98) spikes total residency W from 100.0 ms to 400.0 ms (4.0x) and 2,000.0 ms (20.0x)",
        ll["w_total_15_ms"] == 100.0
        and ll["w_queue_15_ms"] == 60.0
        and ll["w_total_22_5_ms"] == 400.0
        and ll["w_queue_22_5_ms"] == 360.0
        and ll["w_total_24_5_ms"] == 2000.0,
    )

    check(
        "9. Closed-loop concurrency N = 4 self-throttles effective arrival rate from 20.0 RPS (at W = 0.20 s) to 4.0 RPS (at W = 1.00 s), and perf_analyzer closed-loop (120.0 tok/s) under-reports open-loop throughput (180.0 tok/s at 20 RPS) by 50.0%",
        ll["closed_loop_rps_healthy"] == 20.0
        and ll["closed_loop_rps_degraded"] == 4.0
        and ll["perf_analyzer_closed_loop_tps"] == 120.0
        and ll["perf_analyzer_open_loop_tps"] == 180.0
        and ll["open_vs_closed_tps_gain_pct"] == 50.0,
    )

    check(
        "10. Triton perf_analyzer at C=64 shows No-Batch (520.0 RPS, 121.5 ms p99) vs Conservative B=16/5ms (2,850.0 RPS, 5.48x, 8.9 ms p99, batch 13.0) vs Aggressive B=64/50ms (3,400.0 RPS, 6.54x, 48.5 ms p99 at C=64, 51.2 ms at C=1, batch 48.2) vs 500ms delay at C=2 (4.0 RPS)",
        ll["nobatch_rps"] == 520.0
        and ll["conservative_rps"] == 2850.0
        and ll["conservative_speedup_x"] == 5.48
        and ll["conservative_p99_ms"] == 8.9
        and ll["aggressive_rps"] == 3400.0
        and ll["aggressive_speedup_x"] == 6.54
        and ll["aggressive_p99_c1_ms"] == 51.2
        and ll["misconfig_500ms_c2_rps"] == 4.0,
    )

    check(
        "11. Locust load test ramping to 50 users at 1 user/s exposes a service saturation knee at 34 active users",
        ll["locust_max_users"] == 50.0
        and ll["locust_spawn_rate"] == 1.0
        and ll["locust_saturation_knee_users"] == 34.0,
    )

    # 3. Goodput, Pareto frontier, and MLPerf Inference
    gp = evaluate_goodput_and_pareto_frontier()
    check(
        "12. At B = 128, raw throughput reaches 180.0 tok/s but p99 TTFT = 1,200.0 ms (> 200 ms SLO, only 20.0% pass) and p99 ITL = 85.0 ms (> 25 ms SLO, only 7.69% pass)",
        gp["b128_raw_tps"] == 180.0
        and gp["b128_p99_ttft_ms"] == 1200.0
        and gp["b128_p99_itl_ms"] == 85.0
        and gp["ttft_slo_pass_pct"] == 20.0
        and gp["itl_slo_pass_pct"] == 7.69,
    )

    check(
        "13. Under P90 TTFT <= 400 ms and P90 TPOT <= 40 ms, DistServe colocated Goodput is min(3.0, 1.6) = 1.6 RPS/GPU whereas 2P1D disaggregated Goodput is min(11.2, 10.0) / 3 = 3.33 RPS/GPU (~3.3 RPS/GPU, 2.08x gain)",
        gp["colocated_goodput_per_gpu"] == 1.6
        and gp["total_prefill_rps"] == 11.2
        and gp["total_decode_rps"] == 10.0
        and gp["disagg_goodput_per_gpu_exact"] == 3.33
        and gp["disagg_goodput_per_gpu_reported"] == 3.3
        and gp["goodput_gain_x"] == 2.08,
    )

    check(
        "14. Across concurrency sweep C in {1, 8, 16, 32, 64, 128}, Pareto-optimal Goodput under p95 TTFT <= 300 ms and p95 ITL <= 25 ms occurs at C = 32 (1,340.0 tok/s, 245.0 ms TTFT, 22.8 ms ITL), whereas C = 64 (1,890 tok/s) and C = 128 (2,150 tok/s) breach SLOs",
        gp["pareto_optimal_concurrency"] == 32.0
        and gp["pareto_optimal_goodput_tps"] == 1340.0
        and gp["pareto_optimal_ttft_ms"] == 245.0
        and gp["pareto_optimal_itl_ms"] == 22.8
        and gp["max_raw_tps"] == 2150.0
        and gp["over_batch_waste_tps"] == 810.0,
    )

    check(
        "15. MLPerf Inference v5.0 (2025) Server p99 SLOs target 450.0 ms TTFT / 40.0 ms TPOT for Llama-2-70B and 6,000.0 ms (6.0 s) TTFT / 175.0 ms TPOT for Llama-3.1-405B, with GB200 NVL72 delivering 3.4x inference and 2.6x training speedups",
        gp["mlperf_70b_ttft_p99_ms"] == 450.0
        and gp["mlperf_70b_tpot_p99_ms"] == 40.0
        and gp["mlperf_405b_ttft_p99_ms"] == 6000.0
        and gp["mlperf_405b_tpot_p99_ms"] == 175.0
        and gp["gb200_nvl72_infer_gain_x"] == 3.4
        and gp["gb200_nvl72_train_gain_x"] == 2.6,
    )

    # 4. Qwen3-14B optimization, distributed scaling, cold starts, agents, and Lab 04 CPU remediation
    qw = evaluate_qwen3_14b_and_scaling_benchmarks()
    check(
        "16. On L40S (46,068 MiB total, 45,469 MiB free, compute cap 8.9), ShareGPT 100-sample inspection shows prompt mean 232.60 (median 141.50, std 241.42) and output mean 220.61 (median 164.50, std 210.23)",
        qw["l40s_total_mib"] == 46068.0
        and qw["l40s_free_mib"] == 45469.0
        and qw["l40s_compute_cap"] == 8.9
        and qw["sharegpt_prompt_mean"] == 232.60
        and qw["sharegpt_prompt_median"] == 141.50
        and qw["sharegpt_output_mean"] == 220.61
        and qw["sharegpt_output_median"] == 164.50,
    )

    check(
        "17. Qwen3-14B FP16 on L40S uses 27.5185 GiB weights and 11.00 GiB KV cache (72,064 tokens, 1.76x concurrency at 40,960 tokens), achieving 474.38 tok/s on ShareGPT (104.15 ms TTFT, 43.24 ms ITL, 72.15 ms P99 ITL) and 1,123.13 tok/s (2.37x) on Prefix Repetition",
        qw["fp16_weights_gib"] == 27.5185
        and qw["fp16_kv_gib"] == 11.00
        and qw["fp16_kv_tokens"] == 72064.0
        and qw["fp16_max_concurrency_40k"] == 1.76
        and qw["fp16_sharegpt_total_tps"] == 474.38
        and qw["fp16_sharegpt_ttft_ms"] == 104.15
        and qw["fp16_prefix_total_tps"] == 1123.13
        and qw["prefix_cache_tps_gain_x"] == 2.37,
    )

    check(
        "18. Quantizing to 4-bit Qwen3-14B-AWQ shrinks weights to 9.3619 GiB and expands KV cache to 29.15 GiB (191,056 tokens, 2.65x larger, 4.66x concurrency), boosting ShareGPT throughput 2.70x (to 1,280 tok/s) and cutting mean TTFT by 42.78% (~42%, from 103.61 ms to 59.29 ms)",
        qw["awq_weights_gib"] == 9.3619
        and qw["awq_kv_gib"] == 29.15
        and qw["awq_kv_tokens"] == 191056.0
        and qw["awq_max_concurrency_40k"] == 4.66
        and qw["kv_token_capacity_gain_x"] == 2.65
        and qw["awq_sharegpt_total_tps"] == 1280.0
        and qw["awq_tps_gain_x"] == 2.70
        and qw["awq_fig9_2_ttft_ms"] == 59.29
        and qw["awq_ttft_reduction_pct"] == 42.78,
    )

    check(
        "19. On p4d.24xlarge (A100 NVLink), TP=4 cuts TTFT by 50.0% (from 66.0 ms to 33.0 ms) at 3,926.0 TPS, whereas 4 independent DP=1 replicas achieve 9,816.0 TPS (2.50x higher throughput); SGLang RadixAttention gives +40.0% throughput on variable 50-5,000 token prompts",
        qw["p4d_tp1_ttft_ms"] == 66.0
        and qw["p4d_tp4_ttft_ms"] == 33.0
        and qw["p4d_tp4_ttft_reduction_pct"] == 50.0
        and qw["p4d_tp4_total_tps"] == 3926.0
        and qw["p4d_dp4_total_tps"] == 9816.0
        and qw["p4d_dp_vs_tp_gain_x"] == 2.50
        and qw["sglang_radix_gain_pct"] == 40.0,
    )

    check(
        "20. Cold-start latency is 3-5x (1-3B), 16.0x (mid-size), and 50.0x+ (70B+, 30.0 s vs 100.0 ms = 300.0x); in multi-step reasoning agents >= 60.0% of E2E latency comes from external tool/API calls",
        qw["cold_start_mid_x"] == 16.0
        and qw["cold_start_70b_min_x"] == 50.0
        and qw["cold_start_30s_vs_100ms_x"] == 300.0
        and qw["agent_external_call_share_pct"] == 60.0,
    )

    check(
        "21. Scaling efficiency is 81.25% at 6.5x on 8 GPUs and 52.0% on 64 GPUs (33.28 effective GPUs, 30.72 idle GPUs over 336 hours), comm share grows 0% -> 55.0% (155 ms -> 33 ms on 1..16 GPUs), and Amdahl's Law with 10% serial work bounds max speedup to 10.0x",
        qw["eff_8gpu_pct"] == 81.25
        and qw["eff_64gpu_pct"] == 52.0
        and qw["effective_gpus_64"] == 33.28
        and qw["wasted_gpus_64"] == 30.72
        and qw["two_week_hours"] == 336.0
        and qw["iter_1gpu_ms"] == 155.0
        and qw["iter_16gpu_ms"] == 33.0
        and qw["comm_share_16gpu_pct"] == 55.0
        and qw["amdahl_max_speedup_x"] == 10.0,
    )

    check(
        "22. In V12 Lab 04, replacing single-threaded Python preprocessing (13.47 RPS, 1,410.20 ms p99 total, 18.10 ms p99 Triton) with ProcessPoolExecutor raises throughput 7.73x to 104.17 RPS and cuts p99 latency 31.48x to 44.80 ms",
        qw["lab04_unfixed_rps"] == 13.47
        and qw["lab04_unfixed_total_p99_ms"] == 1410.20
        and qw["lab04_fixed_rps"] == 104.17
        and qw["lab04_fixed_total_p99_ms"] == 44.80
        and qw["lab04_rps_gain_x"] == 7.73
        and qw["lab04_p99_reduction_x"] == 31.48,
    )

    # 5. Production failure scenarios & accuracy validation
    fs = evaluate_failure_scenarios_and_accuracy()
    check(
        "23. Failure Scenario 1: Moving from 64-token synthetic prompts (45.0 RPS, 38.0 ms p95 TTFT, 16.2 ms p95 ITL, 42.0 GB VRAM) to 4,096-token RAG prompts (64.0x tokens) drops RPS -86% to 6.2 RPS, spikes p95 TTFT +12,584% to 4,820.0 ms (6,400 ms p99, 24% HTTP 504), and raises VRAM +86% to 78.4 GB; chunked prefill (2,048 tokens) restores 290.0 ms p95 TTFT and 18.2 ms p95 ITL",
        fs["prompt_token_ratio_x"] == 64.0
        and fs["synth_rps"] == 45.0
        and fs["prod_rps"] == 6.2
        and fs["rps_drop_pct_reported"] == -86.0
        and fs["synth_p95_ttft_ms"] == 38.0
        and fs["prod_p95_ttft_ms"] == 4820.0
        and fs["ttft_spike_pct_reported"] == 12584.0
        and fs["gateway_504_timeout_pct"] == 24.0
        and fs["remediated_p95_ttft_ms"] == 290.0
        and fs["remediated_p95_itl_ms"] == 18.2,
    )

    check(
        "24. Failure Scenario 2: Open-loop spike (20 -> 30 RPS at max_num_seqs=512) drives KV cache to 0.99, waiting queue 2 -> 340 in 15.0 s, and p99 TTFT 180.0 ms -> 18,200.0 ms (101.11x); capping max_num_seqs=64 + HTTP 429 at queue > 50 holds 35 RPS at 340.0 ms p99 TTFT with 0 preemptions and 8 waiting",
        fs["collapse_waiting_before"] == 2.0
        and fs["collapse_waiting_after"] == 340.0
        and fs["collapse_kv_usage_ratio"] == 0.99
        and fs["collapse_p99_ttft_before_ms"] == 180.0
        and fs["collapse_p99_ttft_after_ms"] == 18200.0
        and fs["remediated_35rps_waiting"] == 8.0
        and fs["remediated_35rps_preemptions"] == 0.0
        and fs["remediated_35rps_p99_ttft_ms"] == 340.0,
    )

    check(
        "25. Troubleshooting & Accuracy Validation: Short-prompt benchmarks over-report throughput (200.0 vs 80.0 tok/s) and p99 ITL (45.0 ms vs 280.0 ms, 6.22x worse at 16K p99 context), while INT8 2.0x speedup with 15.0% math drop or 0.5% drop at p = 0.001 (< 0.01) vs p = 0.30 is caught by statistical accuracy gates",
        fs["bench_short_tps"] == 200.0
        and fs["prod_long_tps"] == 80.0
        and fs["bench_p99_itl_ms"] == 45.0
        and fs["prod_p99_itl_ms"] == 280.0
        and fs["int8_throughput_gain_x"] == 2.0
        and fs["int8_math_accuracy_drop_pct"] == 15.0
        and fs["regression_p_value"] == 0.001
        and fs["noise_p_value"] == 0.30,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
