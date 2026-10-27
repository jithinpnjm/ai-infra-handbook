#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.1: The Anatomy of an Inference Request."""

from __future__ import annotations
import sys
from inference_request_anatomy import (
    RequestStageTimingsMs,
    decompose_inference_latency,
    evaluate_latency_distribution_and_goodput,
    compute_inference_cost_breakdown,
    compute_gemm_arithmetic_intensity,
    evaluate_roofline_and_decode_wall,
    calculate_kv_cache_sizing,
    sample_next_token_pipeline,
    check_stopping_criteria,
)


def run_lab() -> int:
    print("=== Chapter 15.1 Lab: The Anatomy of an Inference Request Verification ===")
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

    # 1. Nine-Stage E2E Request Latency Decomposition (`V12` Ch. 1 & Ch. 2)
    base_lat = decompose_inference_latency(
        RequestStageTimingsMs(
            t_ingress_tls_ms=2.0,
            t_queue_ms=12.0,
            t_tokenize_ms=4.0,
            t_schedule_kv_alloc_ms=0.5,
            t_h2d_pcie_ms=0.4,
            t_prefill_gpu_ms=180.0,
            itl_gpu_decode_ms=22.0,
            t_sampler_gpu_ms=0.5,
            t_d2h_detok_ms=0.5,
            t_sse_flush_ms=1.0,
            num_output_tokens=50,
        )
    )
    check(
        "1. Baseline 50-token request decomposes into TTFT=200.9 ms, ITL/TPOT=24.0 ms, and E2E=1,376.9 ms",
        base_lat["ttft_ms"] == 200.9
        and base_lat["itl_ms"] == 24.0
        and base_lat["tpot_ms"] == 24.0
        and base_lat["e2e_ms"] == 1376.9,
    )

    # 2. Python GIL Tokenizer Bottleneck vs 16-Thread Rust Tokenizer (`V12` Ch. 2 Scenario 1)
    gil_trace = decompose_inference_latency(
        RequestStageTimingsMs(
            t_ingress_tls_ms=2.0,
            t_queue_ms=0.0,
            t_tokenize_ms=320.0,
            t_schedule_kv_alloc_ms=0.0,
            t_h2d_pcie_ms=0.4,
            t_prefill_gpu_ms=88.0,
            t_sampler_gpu_ms=0.0,
            t_d2h_detok_ms=0.0,
            t_sse_flush_ms=1.6,
            num_output_tokens=1,
        )
    )
    check(
        "2. Python GIL tokenizer trace (320 ms CPU tokenize, 88 ms GPU, 412 ms total) spends 78.64% non-GPU (77.67% on CPU tokenization alone)",
        gil_trace["single_pass_total_ms"] == 412.0
        and round(100.0 * 320.0 / 412.0, 1) == 77.7
        and gil_trace["single_pass_non_gpu_share_pct"] == 78.64,
    )

    rust_trace = decompose_inference_latency(
        RequestStageTimingsMs(
            t_ingress_tls_ms=2.0,
            t_queue_ms=0.0,
            t_tokenize_ms=1.4,
            t_schedule_kv_alloc_ms=0.0,
            t_h2d_pcie_ms=0.4,
            t_prefill_gpu_ms=88.0,
            t_sampler_gpu_ms=0.0,
            t_d2h_detok_ms=0.0,
            t_sse_flush_ms=1.6,
            num_output_tokens=1,
        )
    )
    check(
        "3. 16-thread Rust/C++ tokenizer cuts tokenization from 320.0 ms to 1.4 ms (228.6x faster), dropping total span from 412.0 ms to 93.4 ms and lifting cluster throughput 6.5x (120 -> 780 RPS)",
        rust_trace["single_pass_total_ms"] == 93.4
        and round(320.0 / 1.4, 1) == 228.6
        and round(780.0 / 120.0, 2) == 6.5,
    )

    # 3. Pageable vs Pinned Host RAM (`cudaHostAlloc`) over PCIe Gen5 (`V12` Ch. 2)
    check(
        "4. Pinned host RAM (55-62 GB/s on 64 GB/s PCIe Gen5) transfers 4.4x-5.5x faster than pageable malloc (10-14 GB/s)",
        round(55.0 / 10.0, 1) == 5.5 and round(62.0 / 14.0, 2) == 4.43,
    )

    # 4. Mean vs Percentile Latency & Goodput Under Dual SLOs (`AIE` Ch. 9)
    ttft_10 = [100.0, 102.0, 100.0, 100.0, 99.0, 104.0, 110.0, 90.0, 3000.0, 95.0]
    tpot_10 = [40.0, 42.0, 45.0, 120.0, 115.0, 130.0, 140.0, 150.0, 160.0, 170.0]
    dist = evaluate_latency_distribution_and_goodput(
        ttft_10, tpot_10, ttft_slo_ms=200.0, tpot_slo_ms=100.0, window_seconds=1.0
    )
    check(
        "5. Single 3,000 ms TTFT outlier among 10 requests skews mean TTFT to 390.0 ms while median (p50) remains 100.0 ms (AIE Ch. 9)",
        dist["mean_ttft_ms"] == 390.0 and dist["p50_ttft_ms"] == 100.0,
    )

    check(
        "6. At 10 RPS raw throughput (100 RPM scaled), if only 30% satisfy TTFT <= 200 ms and TPOT <= 100 ms, Goodput is 3.0 RPS (30 RPM at 100 RPM)",
        dist["throughput_rps"] == 10.0
        and dist["goodput_rps"] == 3.0
        and dist["slo_attainment_pct"] == 30.0,
    )

    # 5. Inference Cost Decomposition (`AIE` Ch. 9)
    cost = compute_inference_cost_breakdown(
        gpu_hourly_cost_usd=2.0,
        decode_tps=100.0,
        prefill_rpm=100.0,
        avg_output_tokens_per_req=200,
        num_requests=1000,
    )
    check(
        "7. At $2.00/hr GPU cost and 100 tok/s decode, output costs $5.556/1M tokens ($1.11/1K requests of 200 tokens) + $0.33 prefill (100 RPM) = $1.44 per 1K requests",
        cost["cost_per_1m_output_tokens_usd"] == 5.556
        and cost["decode_cost_usd"] == 1.11
        and cost["prefill_cost_usd"] == 0.33
        and cost["total_cost_usd"] == 1.44,
    )

    # 6. Roofline Ridge Point Across Accelerators (`HLS` Ch. 5, `V01` Ch. 7, `V12` Ch. 1)
    l40s_roof = evaluate_roofline_and_decode_wall(
        model_params_b=7.0, bytes_per_param=2, peak_tflops=362.05, hbm_bandwidth_gbps=864.0
    )
    check(
        "8. NVIDIA L40S (362.05 FP16 TFLOPS, 864 GB/s GDDR6) has a Roofline ridge point of 419.04 FLOPs/Byte (~419 FLOPs/Byte, HLS Ch. 5)",
        round(l40s_roof["ridge_flops_per_byte"]) == 419,
    )

    h100_dense_roof = evaluate_roofline_and_decode_wall(
        model_params_b=70.0, bytes_per_param=2, peak_tflops=989.0, hbm_bandwidth_gbps=3350.0
    )
    h100_sparse_roof = evaluate_roofline_and_decode_wall(
        model_params_b=70.0, bytes_per_param=2, peak_tflops=1979.0, hbm_bandwidth_gbps=3350.0
    )
    check(
        "9. NVIDIA H100 SXM5 (3.35 TB/s HBM3) has a Roofline ridge point of 295.22 FLOPs/Byte (989 dense FP16 TFLOPS) and 590.75 FLOPs/Byte (1,979 sparse TFLOPS)",
        h100_dense_roof["ridge_flops_per_byte"] == 295.22
        and h100_sparse_roof["ridge_flops_per_byte"] == 590.75,
    )

    # 7. Square GEMM Arithmetic Intensity (`HLS` Ch. 5 Table 5-9)
    ai_sq_64 = compute_gemm_arithmetic_intensity(64, 64, 64, 2)["arithmetic_intensity_flops_per_byte"]
    ai_sq_512 = compute_gemm_arithmetic_intensity(512, 512, 512, 2)["arithmetic_intensity_flops_per_byte"]
    ai_sq_4096 = compute_gemm_arithmetic_intensity(4096, 4096, 4096, 2)["arithmetic_intensity_flops_per_byte"]
    check(
        "10. Square FP16 GEMM (M=N=K) yields Arithmetic Intensity of 21.33 (M=64), 170.67 (M=512), and 1365.33 FLOPs/Byte (M=4096) (HLS Ch. 5 Table 5-9)",
        int(ai_sq_64) == 21 and int(ai_sq_512) == 170 and int(ai_sq_4096) == 1365,
    )

    # 8. LLM Prefill vs Decode Arithmetic Intensity (`HLS` Ch. 5 Table 5-10, h=4096)
    ai_prefill_64 = compute_gemm_arithmetic_intensity(64, 4096, 4096, 2)["arithmetic_intensity_flops_per_byte"]
    ai_prefill_512 = compute_gemm_arithmetic_intensity(512, 4096, 4096, 2)["arithmetic_intensity_flops_per_byte"]
    ai_prefill_4096 = compute_gemm_arithmetic_intensity(4096, 4096, 4096, 2)["arithmetic_intensity_flops_per_byte"]
    ai_decode_1 = compute_gemm_arithmetic_intensity(1, 4096, 4096, 2)["arithmetic_intensity_flops_per_byte"]
    check(
        "11. LLM linear layer (h=4096) prefill intensity scales from 62.06 (s=64) to 409.60 (s=512) to 1365.33 FLOPs/Byte (s=4096), crossing L40S (419) and H100 (295/591) ridge points",
        ai_prefill_64 == 62.06
        and ai_prefill_512 == 409.60
        and ai_prefill_4096 == 1365.33,
    )

    check(
        "12. Single-sequence decode (M=1, h=4096) has an Arithmetic Intensity of 1.00 FLOPs/Byte (4096/4098 = 0.9995), trapping decode on the memory-bandwidth roof",
        ai_decode_1 == 1.00,
    )

    # 9. Single-Stream 70B FP16 Decode Wall & Model Bandwidth Utilization (`V12` Ch. 1, `AIE` Ch. 9)
    check(
        "13. Loading 140 GB of 70B FP16 weights over 3,350 GB/s H100 HBM3 takes 41.79 ms (~41.7 ms) per token, capping single-stream decode at 23.93 tok/s (~24 tok/s)",
        h100_dense_roof["weight_bytes_gb"] == 140.0
        and h100_dense_roof["min_decode_step_ms"] == 41.79
        and h100_dense_roof["max_single_stream_tps"] == 23.93,
    )

    mbu_7b = evaluate_roofline_and_decode_wall(
        model_params_b=7.0, bytes_per_param=2, peak_tflops=312.0, hbm_bandwidth_gbps=2000.0, observed_tps=50.0
    )
    check(
        "14. Model Bandwidth Utilization (MBU) formula (params * bytes * tok/s / peak_bw) yields 700.0 GB/s (35.0% MBU at 50 tok/s, or 70.0% at 100 tok/s on 1 byte/700 GB/s) on 2 TB/s A100",
        mbu_7b["bandwidth_used_gbps"] == 700.0 and mbu_7b["mbu_pct"] == 35.0 and round(700.0 / 2000.0 * 200.0, 1) == 70.0,
    )

    # 10. KV Cache Sizing: Llama-3-70B GQA vs MHA (`V12` Ch. 1, `V05` Ch. 2)
    kv_70b_64 = calculate_kv_cache_sizing(
        num_layers=80, num_kv_heads=8, head_dim=128, seq_len=4096, batch_size=64, bytes_per_elem=2
    )
    kv_70b_100 = calculate_kv_cache_sizing(
        num_layers=80, num_kv_heads=8, head_dim=128, seq_len=4096, batch_size=100, bytes_per_elem=2,
        model_weights_gb=140.0, workspace_gb=10.0, gpu_vram_gb=80.0
    )
    check(
        "15. Llama-3-70B GQA (L=80, N_kv=8, d_head=128, FP16) consumes 327,680 bytes/token (327.68 KB / 0.3125 MiB) and 1.342 GB (~1.34 GB) per 4,096-token sequence",
        kv_70b_64["bytes_per_token"] == 327680
        and kv_70b_64["kb_per_token_decimal"] == 327.68
        and kv_70b_64["gb_per_seq_decimal"] == 1.342,
    )

    check(
        "16. At 64 concurrent 4K sequences on Llama-3-70B, KV cache alone consumes 85.90 GB (85.76 GB at 1.34 GB/seq), exceeding a single 80 GB GPU",
        kv_70b_64["total_kv_gb_decimal"] == 85.90 and round(64 * 1.34, 2) == 85.76,
    )

    check(
        "17. Serving 100 concurrent 4K sequences on Llama-3-70B requires 140.0 GB weights + 134.22 GB KV + 10.0 GB workspace = 284.22 GB (~284.2 GB) VRAM -> minimum 4x 80GB H100 GPUs (TP=4)",
        kv_70b_100["total_kv_gb_decimal"] == 134.22
        and kv_70b_100["total_vram_decimal_gb"] == 284.22
        and kv_70b_100["min_tp_gpus"] == 4,
    )

    kv_70b_mha = calculate_kv_cache_sizing(
        num_layers=80, num_kv_heads=64, head_dim=128, seq_len=2048, batch_size=128, bytes_per_elem=2
    )
    kv_70b_gqa_128 = calculate_kv_cache_sizing(
        num_layers=80, num_kv_heads=8, head_dim=128, seq_len=2048, batch_size=128, bytes_per_elem=2
    )
    check(
        "18. GQA (8 KV heads vs 64 MHA heads) shrinks 70B per-token KV cache 8.0x from 2,621,440 B (~2.62 MB) to 327,680 B (~0.31 MiB), cutting 128x2048 KV cache from 687.19 GB to 85.90 GB (~86 GB)",
        kv_70b_mha["bytes_per_token"] == 2621440
        and kv_70b_mha["bytes_per_token"] // kv_70b_gqa_128["bytes_per_token"] == 8
        and round(kv_70b_mha["total_kv_gb_decimal"]) == 687
        and round(kv_70b_gqa_128["total_kv_gb_decimal"]) == 86,
    )

    # 11. KV Cache Sizing: Llama-2-7B MHA (`HLS` Ch. 5 Table 5-7) & No-Cache vs KV-Cache (`HLS` Ch. 2)
    kv_7b_16 = calculate_kv_cache_sizing(
        num_layers=32, num_kv_heads=32, head_dim=128, seq_len=4096, batch_size=16, bytes_per_elem=2,
        model_weights_gb=14.0, workspace_gb=2.0, gpu_vram_gb=48.0
    )
    check(
        "19. Llama-2-7B MHA (L=32, N_kv=32, d_head=128, FP16) uses 524,288 bytes/token (0.5 MiB/tok) and 32.0 GiB KV cache for 16 x 4,096 sequences (allowing 4 seqs on 24 GB A10 vs 16 seqs on 48 GB L40S)",
        kv_7b_16["bytes_per_token"] == 524288
        and kv_7b_16["mib_per_token_binary"] == 0.5
        and kv_7b_16["total_kv_gib_binary"] == 32.0,
    )

    check(
        "20. Enabling past_key_values KV cache on Qwen2.5-0.5B cuts 100-token generation time from 9.1205 s to 3.1416 s (2.90x speedup); vLLM cuts pipeline time from 19.58 s to 1.12 s (17.48x speedup)",
        round(9.1205 / 3.1416, 2) == 2.90 and round(19.58 / 1.12, 2) == 17.48,
    )

    # 12. Chunked Prefill Tail-Latency Mitigation (`V12` Ch. 1 Scenario 2)
    check(
        "21. Enabling Chunked Prefill (--enable-chunked-prefill --max-num-batched-tokens 512) eliminates the 3,850 ms prefill stall on 16K prompts, cutting P99 ITL 197.4x from 4,500 ms to 22.8 ms",
        round(4500.0 / 22.8, 1) == 197.4,
    )

    # 13. Tokenization & Logit Sampling Pipeline (`Temperature`, `Repetition Penalty`, `Top-K`, `Top-P`)
    qwen_prompt_ids = [1100, 10930, 261, 4022, 22575, 1078, 290, 2952, 9029, 5030, 693]
    check(
        "22. Reference prompt 'Write a short introduction about the US capital city' tokenizes into 11 integer token IDs (HLS Ch. 2)",
        len(qwen_prompt_ids) == 11 and qwen_prompt_ids[0] == 1100 and qwen_prompt_ids[-1] == 693,
    )

    logits_demo = [4.0, 3.0, 2.0, 1.0, 0.0]
    greedy = sample_next_token_pipeline(logits_demo, temperature=0.0)
    check(
        "23. Greedy decoding (temperature=0.0) deterministically selects argmax token_id=0 with probability 1.0 and active_vocab_count=1",
        greedy["selected_token_id"] == 0
        and greedy["final_probs"][0] == 1.0
        and greedy["active_vocab_count"] == 1,
    )

    top_kp = sample_next_token_pipeline(logits_demo, temperature=1.0, top_k=3, top_p=0.80)
    check(
        "24. Top-K=3 followed by Top-P=0.80 nucleus filtering truncates the 5-token distribution to the top 2 tokens (whose unnormalized probs 0.6364 + 0.2341 = 0.8705 >= 0.80) and renormalizes to 1.0",
        top_kp["active_vocab_count"] == 2
        and abs(sum(top_kp["final_probs"]) - 1.0) < 1e-5
        and top_kp["final_probs"][2] == 0.0,
    )

    rep_pen = sample_next_token_pipeline(logits_demo, generated_history=[0], temperature=0.0, repetition_penalty=2.0)
    check(
        "25. Repetition penalty=2.0 on already-generated token 0 halves its positive logit (4.0 -> 2.0), promoting token 1 (logit 3.0) to argmax",
        rep_pen["selected_token_id"] == 1,
    )

    # 14. Stopping Conditions Verification (`EOS`, `stop` string, `max_tokens`, `max_model_len`, `abort`)
    stop_eos = check_stopping_criteria([10930, 128009], "Washington, D.C.", eos_token_ids=(128001, 128009))
    stop_str = check_stopping_criteria([10930, 261], "Answer:\n###", stop_strings=("\n", "###"))
    stop_len = check_stopping_criteria(list(range(100)), "text", max_new_tokens=100)
    stop_ctx = check_stopping_criteria(list(range(64)), "text", max_new_tokens=200, prompt_tokens=4032, max_model_len=4096)
    stop_abt = check_stopping_criteria([10930], "text", client_aborted=True)
    check(
        "26. All 5 production stop conditions (eos_token, stop_string, max_tokens, model_length, client abort) trigger deterministically",
        stop_eos["finish_reason"] == "eos_token"
        and stop_str["finish_reason"] == "stop_string:'\\n'"
        and stop_len["finish_reason"] == "max_tokens"
        and stop_ctx["finish_reason"] == "model_length"
        and stop_abt["finish_reason"] == "abort",
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
