#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.10: Prefill and decode disaggregation."""

from __future__ import annotations
import sys
from prefill_decode_disaggregation import (
    evaluate_colocated_interference_and_goodput,
    evaluate_worker_ratio_sizing,
    compute_kv_cache_transfer_footprints,
    evaluate_nixl_rdma_transfer_vs_ttft,
    evaluate_routing_and_qos_policies,
    evaluate_heterogeneous_gpu_pairings,
)


def run_lab() -> int:
    print("=== Chapter 15.10 Lab: Prefill and Decode Disaggregation Verification ===")
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

    # 1. Opposite hardware profiles & co-located prefill-decode interference
    ig = evaluate_colocated_interference_and_goodput()
    check(
        "1. Prefill utilizes 85% compute / 40% memory bandwidth whereas Decode utilizes 25% compute / 90% memory bandwidth",
        ig["prefill_compute_util_pct"] == 85.0
        and ig["prefill_mem_bw_util_pct"] == 40.0
        and ig["decode_compute_util_pct"] == 25.0
        and ig["decode_mem_bw_util_pct"] == 90.0,
    )

    check(
        "2. An unchunked 12,288-token prefill on 4x H100 (TP=4) stalls 45 decode streams for 320.0 ms, spiking p99 ITL from 18.0 ms to 340.0 ms (18.89x spike, violating < 30.0 ms SLA) before chunked prefill (2,048 tokens) restores p99 ITL to 21.4 ms",
        ig["long_prompt_tokens"] == 12288.0
        and ig["active_decode_streams"] == 45.0
        and ig["unchunked_prefill_stall_ms"] == 320.0
        and ig["spiked_p99_itl_ms"] == 340.0
        and ig["itl_spike_ratio_12k_x"] == 18.89
        and ig["chunked_2048_p99_itl_ms"] == 21.4,
    )

    check(
        "3. An 8,192-token prefill bubble spikes a 15.0 ms decode step to 380.0 ms (25.33x), whereas 512-token chunked prefill bounds the hybrid step to 28.0 ms",
        ig["bubble_prompt_tokens"] == 8192.0
        and ig["normal_decode_step_ms"] == 15.0
        and ig["bubble_prefill_step_ms"] == 380.0
        and ig["itl_spike_ratio_8k_x"] == 25.33
        and ig["chunked_512_step_ms"] == 28.0,
    )

    check(
        "4. Request-level dynamic batching (B=32, tau=50 ms) suffers 420.0 ms p99 ITL, 14.2 s p99 TTFT, and 18.0% SM occupancy vs 19.1 ms p99 ITL and 3.8x throughput with continuous batching",
        ig["req_batch_p99_itl_ms"] == 420.0
        and ig["req_batch_p99_ttft_s"] == 14.2
        and ig["req_batch_sm_occupancy_pct"] == 18.0
        and ig["cont_batch_p99_itl_ms"] == 19.1
        and ig["cont_batch_throughput_gain_x"] == 3.8,
    )

    # 2. DistServe 2P1D Goodput math & MLPerf v5.0 SLOs
    check(
        "5. Under P90 TTFT <= 400 ms and P90 TPOT <= 40 ms SLOs, colocated serving achieves min(3.0, 1.6) = 1.6 RPS/GPU goodput whereas disaggregated 2P1D (2 * 5.6 = 11.2 RPS prefill, 10.0 RPS decode across 3 GPUs) achieves 10.0 / 3 = 3.33 RPS/GPU (~3.3 RPS/GPU, 2.08x gain)",
        ig["colocated_goodput_per_gpu"] == 1.6
        and ig["total_prefill_rps"] == 11.2
        and ig["total_decode_rps"] == 10.0
        and ig["total_cluster_goodput_rps"] == 10.0
        and ig["disagg_goodput_per_gpu_exact"] == 3.33
        and ig["disagg_goodput_per_gpu_reported"] == 3.3
        and ig["goodput_per_gpu_gain_x"] == 2.08,
    )

    check(
        "6. DistServe achieves up to 7.4x higher goodput and 12.6x tighter SLOs, and MLPerf v5.0 p99 SLOs target 450 ms TTFT / 40 ms TPOT for Llama-2-70B and 6,000 ms (6 s) TTFT / 175 ms TPOT for Llama-3.1-405B",
        ig["distserve_max_goodput_gain_x"] == 7.4
        and ig["distserve_tighter_slo_x"] == 12.6
        and ig["mlperf_v5_70b_ttft_slo_ms"] == 450.0
        and ig["mlperf_v5_70b_tpot_slo_ms"] == 40.0
        and ig["mlperf_v5_405b_ttft_slo_ms"] == 6000.0
        and ig["mlperf_v5_405b_tpot_slo_ms"] == 175.0,
    )

    # 3. Prefill-to-Decode worker ratio sizing (N_P : N_D) across 3 workload regimes
    # Regime A: Prefill-heavy RAG (lambda = 10 RPS, L_in = 8192, L_out = 128, cache_hit = 0.0, T_P = 27306.67 tok/s, T_D = 1280 tok/s -> 3:1)
    rag_sizing = evaluate_worker_ratio_sizing(
        arrival_rate_rps=10.0,
        prompt_tokens=8192,
        output_tokens=128,
        prefix_cache_hit_ratio=0.0,
        prefill_tok_per_s_per_worker=27306.67,
        decode_tok_per_s_per_worker=1280.0,
    )
    check(
        "7. Prefill-heavy RAG workload (10 RPS, 8,192 prompt tokens, 128 output tokens) requires 81,920 prefill tok/s and 1,280 decode tok/s, yielding N_P = 3, N_D = 1 (3:1 prefill-to-decode ratio)",
        rag_sizing["total_prefill_tok_per_s"] == 81920.0
        and rag_sizing["total_decode_tok_per_s"] == 1280.0
        and rag_sizing["np_workers"] == 3
        and rag_sizing["nd_workers"] == 1
        and rag_sizing["provisioned_ratio"] == "3:1",
    )

    # Regime B: Balanced enterprise chat matching Dynamo 4P8D (lambda = 16 RPS, L_in = 2048, cache_hit = 0.0, L_out = 512, T_P = 8192 tok/s, T_D = 1024 tok/s -> N_P = 4, N_D = 8 -> 4:8 = 1:2)
    chat_sizing = evaluate_worker_ratio_sizing(
        arrival_rate_rps=16.0,
        prompt_tokens=2048,
        output_tokens=512,
        prefix_cache_hit_ratio=0.0,
        prefill_tok_per_s_per_worker=8192.0,
        decode_tok_per_s_per_worker=1024.0,
    )
    check(
        "8. Enterprise chat workload (16 RPS, 2,048 prompt tokens, 512 output tokens) requires 32,768 prefill tok/s and 8,192 decode tok/s, yielding N_P = 4 prefill workers and N_D = 8 decode workers (4:8 = 1:2 ratio)",
        chat_sizing["total_prefill_tok_per_s"] == 32768.0
        and chat_sizing["total_decode_tok_per_s"] == 8192.0
        and chat_sizing["np_workers"] == 4
        and chat_sizing["nd_workers"] == 8
        and chat_sizing["exact_np_to_nd_ratio"] == 0.5,
    )

    # Regime C: Decode-heavy Chain-of-Thought reasoning (lambda = 8 RPS, L_in = 1024, cache_hit = 0.5 -> eff_len = 512, L_out = 4096, T_P = 4096 tok/s, T_D = 8192 tok/s -> N_P = 1, N_D = 4 -> 1:4)
    cot_sizing = evaluate_worker_ratio_sizing(
        arrival_rate_rps=8.0,
        prompt_tokens=1024,
        output_tokens=4096,
        prefix_cache_hit_ratio=0.50,
        prefill_tok_per_s_per_worker=4096.0,
        decode_tok_per_s_per_worker=8192.0,
    )
    check(
        "9. Chain-of-Thought reasoning workload (8 RPS, 1,024 prompt tokens with 50% prefix cache hit -> 512 effective tokens, 4,096 output tokens) yields N_P = 1 and N_D = 4 (1:4 prefill-to-decode ratio)",
        cot_sizing["effective_prompt_tokens"] == 512.0
        and cot_sizing["total_prefill_tok_per_s"] == 4096.0
        and cot_sizing["total_decode_tok_per_s"] == 32768.0
        and cot_sizing["np_workers"] == 1
        and cot_sizing["nd_workers"] == 4
        and cot_sizing["provisioned_ratio"] == "1:4",
    )

    # 4. KV Cache transfer bandwidth math across MHA, GQA, MQA, and MLA
    kv = compute_kv_cache_transfer_footprints(seq_len=4096)
    check(
        "10. Llama-13B (L=40, d=128) 4,096-token KV cache is 819,200 B/tok (0.819 MB/tok, 3.36 GB FP16 / 1.68 GB FP8) for MHA (H_kv=40), 0.671 GB FP16 / 0.336 GB FP8 for GQA-8 (5.0x reduction), and 0.084 GB FP16 for MQA-1 (40.0x reduction)",
        kv["llama_13b_mha"]["bytes_per_token_fp16"] == 819200.0
        and kv["llama_13b_mha"]["mb_per_token_fp16_decimal"] == 0.819
        and kv["llama_13b_mha"]["seq_gb_fp16_decimal"] == 3.36
        and kv["llama_13b_mha"]["seq_gb_fp8_decimal"] == 1.68
        and kv["llama_13b_gqa8"]["seq_gb_fp16_decimal"] == 0.671
        and kv["llama_13b_gqa8"]["seq_gb_fp8_decimal"] == 0.336
        and kv["llama_13b_gqa8"]["mha_to_gqa_reduction_x"] == 5.0
        and kv["llama_13b_mqa1"]["seq_gb_fp16_decimal"] == 0.084
        and kv["llama_13b_mqa1"]["mha_to_mqa_reduction_x"] == 40.0,
    )

    check(
        "11. Llama-3-8B (L=32, H_kv=8, d=128) FP16 KV cache is 131,072 B/tok (128.0 KiB/tok), totaling 0.134 GB at 1,024 tokens and 1.342 GB at 10,240 tokens (~21.47 GB/s exact or 24.0-25.0 GB/s at 16 RPS)",
        kv["llama_3_8b_gqa8"]["bytes_per_token_fp16"] == 131072.0
        and kv["llama_3_8b_gqa8"]["kib_per_token_fp16"] == 128.0
        and kv["llama_3_8b_gqa8"]["seq_1024_gb_decimal"] == 0.134
        and kv["llama_3_8b_gqa8"]["seq_10240_gb_decimal"] == 1.342
        and kv["llama_3_8b_gqa8"]["bw_at_16rps_10k_gb_s"] == 21.47
        and kv["llama_3_8b_gqa8"]["bw_at_16rps_1_5gb_s"] == 24.0,
    )

    check(
        "12. Llama-3-70B (L=80, H_kv=8, d=128) GQA-8 KV cache is 327,680 B/tok (320.0 KiB/tok FP16, 160.0 KiB/tok FP8), requiring 1.342 GB (1.25 GiB) at 4,096 tokens in FP16 and 0.671 GB (0.625 GiB) in FP8",
        kv["llama_3_70b"]["gqa8_bytes_per_token_fp16"] == 327680.0
        and kv["llama_3_70b"]["gqa8_kib_per_token_fp16"] == 320.0
        and kv["llama_3_70b"]["gqa8_bytes_per_token_fp8"] == 163840.0
        and kv["llama_3_70b"]["gqa8_kib_per_token_fp8"] == 160.0
        and kv["llama_3_70b"]["gqa8_4k_gb_fp16_decimal"] == 1.342
        and kv["llama_3_70b"]["gqa8_4k_gib_fp16_binary"] == 1.25
        and kv["llama_3_70b"]["gqa8_4k_gb_fp8_decimal"] == 0.671
        and kv["llama_3_70b"]["gqa8_4k_gib_fp8_binary"] == 0.625,
    )

    check(
        "13. At 128,000 tokens, Llama-3-70B GQA-8 reduces KV cache from 312.5 GiB (64-head MHA) to 39.06 GiB (8.0x / 87.5% reduction), and a 250,000-token 32-head 70B MHA context consumes 327.7 GB (~328 GB) in FP16",
        kv["llama_3_70b"]["mha64_128k_gib_fp16"] == 312.5
        and kv["llama_3_70b"]["gqa8_128k_gib_fp16"] == 39.06
        and kv["llama_3_70b"]["mha64_to_gqa8_reduction_x"] == 8.0
        and kv["llama_3_70b"]["mha64_to_gqa8_savings_pct"] == 87.5
        and kv["llama_3_70b"]["mha32_250k_gb_fp16"] == 327.7,
    )

    check(
        "14. DeepSeek-V3/R1 (L=61, d_c=512, d_r=64) MLA caches 70,272 B/tok (68.625 KiB/tok FP16) or 35,136 B/tok (FP8), requiring 0.288 GB at 4,096 tokens in FP16 and 0.144 GB in FP8 (4.66x smaller than 70B GQA-8 and 37.3x smaller than 70B MHA)",
        kv["deepseek_v3_mla"]["bytes_per_token_fp16"] == 70272.0
        and kv["deepseek_v3_mla"]["kib_per_token_fp16"] == 68.625
        and kv["deepseek_v3_mla"]["bytes_per_token_fp8"] == 35136.0
        and kv["deepseek_v3_mla"]["seq_4k_gb_fp16_decimal"] == 0.288
        and kv["deepseek_v3_mla"]["seq_4k_gb_fp8_decimal"] == 0.144
        and kv["deepseek_v3_mla"]["vs_70b_gqa8_reduction_x"] == 4.66
        and kv["deepseek_v3_mla"]["vs_70b_mha64_reduction_x"] == 37.3,
    )

    # 5. RDMA / NVLink NIXL transfer latency vs TTFT budget & PagedAttention collation
    nx = evaluate_nixl_rdma_transfer_vs_ttft()
    check(
        "15. Transferring a 4,096-token Llama-3-70B FP16 KV cache (1.342 GB) takes 134.22 ms on non-RDMA PCIe/TCP (10 GB/s, violating 250 ms TTFT SLO at 180 ms compute) vs 26.84 ms on single 400G NDR IB (50 GB/s), 13.42 ms on 800G ConnectX-8 (100 GB/s), 3.36 ms on 8x NDR rails (400 GB/s), 1.49 ms on NVLink 4 (900 GB/s), and 0.75 ms on NVLink 5 (1,800 GB/s)",
        nx["transfer_ms_by_fabric"]["pcie_non_rdma_tcp_10gbs"] == 134.22
        and nx["meets_unpipelined_ttft_slo"]["pcie_non_rdma_tcp_10gbs"] is False
        and nx["transfer_ms_by_fabric"]["ib_ndr_400g_single_nic_50gbs"] == 26.84
        and nx["meets_unpipelined_ttft_slo"]["ib_ndr_400g_single_nic_50gbs"] is True
        and nx["transfer_ms_by_fabric"]["ib_xdr_cx8_800g_single_nic_100gbs"] == 13.42
        and nx["transfer_ms_by_fabric"]["ib_ndr_8x_rail_400gbs"] == 3.36
        and nx["transfer_ms_by_fabric"]["nvlink4_h100_900gbs"] == 1.49
        and nx["transfer_ms_by_fabric"]["nvlink5_blackwell_1800gbs"] == 0.75,
    )

    check(
        "16. Layer-by-layer pipelined NIXL transfer across 80 layers overlaps layers 1..79 with compute, exposing only 0.34 ms (0.19% < 1% of 180 ms prefill) and yielding 180.34 ms total TTFT",
        nx["exposed_final_layer_ms"] == 0.34
        and nx["pipelined_ttft_ms"] == 180.34
        and nx["exposed_overhead_pct"] == 0.19
        and nx["overhead_under_1_percent"] is True,
    )

    check(
        "17. Collating a 7,500-token KV cache from 16-token pages (469 WQEs, ~470) into 128-token slabs (59 WQEs) cuts RDMA transfer time from 20.0 ms to 8.0 ms (2.5x speedup)",
        nx["uncollated_16tok_wqes"] == 469
        and nx["collated_128tok_wqes"] == 59
        and nx["uncollated_7500_ms"] == 20.0
        and nx["collated_7500_ms"] == 8.0
        and nx["collation_speedup_x"] == 2.5,
    )

    check(
        "18. NIXL / LMCache uses 1 MiB (1,048,576 B) C++ test buffers, 1 GiB (1,073,741,824 B) pd_buffer_size, UCX_RNDV_THRESH=16384, and achieves 14.0x TTFT speedup on x86+H100 KV offload and 2.0x additional (28.0x total) on GH200 NVLink-C2C",
        nx["nixl_1mib_buffer_bytes"] == 1048576
        and nx["lmcache_1gib_buffer_bytes"] == 1073741824
        and nx["ucx_rndv_thresh_bytes"] == 16384
        and nx["x86_h100_offload_speedup_x"] == 14.0
        and nx["gh200_vs_x86_offload_speedup_x"] == 2.0
        and nx["gh200_total_offload_speedup_x"] == 28.0,
    )

    # 6. Disaggregated routing, latency_cost scoring, and QoS early rejection
    rt_offload = evaluate_routing_and_qos_policies(
        prompt_length=1024,
        prefix_cached_length=256,
        prefill_queue_size=4,
        decode_active_reqs=6,
        priority="low",
        decode_queue_size=6,
    )
    check(
        "19. For a 1,024-token prompt with 256 cached tokens (eff_len = 768 >= 256) and prefill_queue_size = 4 (< 10), should_offload_prefill() returns True and YAML remote score is 0.7 + 0.3 = 1.0 (> 0.5)",
        rt_offload["effective_prompt_length"] == 768
        and rt_offload["should_offload"] is True
        and rt_offload["yaml_score"] == 1.0
        and rt_offload["yaml_offload"] is True,
    )

    rt_local_cache = evaluate_routing_and_qos_policies(
        prompt_length=1024,
        prefix_cached_length=980,
        prefill_queue_size=3,
        decode_active_reqs=4,
    )
    check(
        "20. When prefix caching matches 980 of 1,024 tokens (eff_len = 44 < 64) and decode load is 4 (< 8), should_offload_prefill() keeps prefill local on the decode worker (yaml_score = 0.3 <= 0.5)",
        rt_local_cache["effective_prompt_length"] == 44
        and rt_local_cache["should_offload"] is False
        and rt_local_cache["yaml_score"] == 0.3
        and rt_local_cache["yaml_offload"] is False,
    )

    rt_reject = evaluate_routing_and_qos_policies(
        prompt_length=512,
        prefix_cached_length=0,
        prefill_queue_size=12,
        decode_active_reqs=10,
        priority="low",
        avg_prefill_ms_per_req=35.0,
        avg_decode_ms_per_req=20.0,
        decode_queue_size=12,
        ttft_slo_ms=500,
    )
    check(
        "21. Composite latency_cost prefers prefix-cached Worker A (-2.95) over uncached Worker B (+2.70), and QoSController rejects low-priority traffic when est_ttft = 12*35 + 12*20 = 660.0 ms exceeds the 500 ms SLO",
        rt_reject["cost_worker_cached"] == -2.95
        and rt_reject["cost_worker_uncached"] == 2.70
        and rt_reject["selected_worker"] == "worker_cached"
        and rt_reject["est_ttft_ms"] == 660.0
        and rt_reject["admitted"] is False
        and rt_reject["qos_tiers"] == {"premium": 0.10, "standard": 0.30, "free": 0.60},
    )

    # 7. Heterogeneous GPU pairing (H100+H200, B200+B300, GB200 NVL72, Splitwise, HexGen-2, Arrow)
    het = evaluate_heterogeneous_gpu_pairings()
    check(
        "22. Pairing H100 (80 GB, 3.35 TB/s) for prefill with H200 (141 GB, 4.8 TB/s) for decode provides 1.76x HBM capacity and 1.43x HBM bandwidth on decode while matching prefill BF16/FP8 TFLOPS",
        het["h100_vram_gb"] == 80.0
        and het["h200_vram_gb"] == 141.0
        and het["h200_vs_h100_vram_x"] == 1.76
        and het["h200_vs_h100_bw_x"] == 1.43,
    )

    check(
        "23. Pairing B200 (180 GB HBM3e, 10 PFLOPS FP4) for prefill with B300 (288 GB HBM3e, 15 PFLOPS FP4) for decode provides 1.60x total HBM and expands post-70B-weight arithmetic KV capacity from 110.0 GB (122.0 GB ASP reported) to 218.0 GB (1.98x)",
        het["b200_vram_gb"] == 180.0
        and het["b300_vram_gb"] == 288.0
        and het["b300_vs_b200_vram_x"] == 1.60
        and het["asp_b200_reported_kv_gb"] == 122.0
        and het["b200_arith_kv_gb"] == 110.0
        and het["b300_arith_kv_gb"] == 218.0
        and het["b300_vs_b200_kv_pool_x"] == 1.98,
    )

    check(
        "24. Splitwise (4x H100 prefill + 4x A100 decode) achieves 2.35x RPS at iso-cost/power, 1.4x RPS at 20% lower cost, or 25.0% GPU savings (6 vs 8 GPUs), while HexGen-2 achieves up to 2.0x (1.3x avg) throughput or 30.0% lower cost",
        het["splitwise_iso_cost_rps_gain_x"] == 2.35
        and het["splitwise_lower_cost_rps_gain_x"] == 1.4
        and het["splitwise_cost_reduction_pct"] == 20.0
        and het["splitwise_gpu_saving_pct"] == 25.0
        and het["hexgen2_peak_rps_gain_x"] == 2.0
        and het["hexgen2_avg_rps_gain_x"] == 1.3
        and het["hexgen2_cost_reduction_pct"] == 30.0,
    )

    check(
        "25. GB200 NVL72 (72 GPUs + 36 Grace CPUs, 30 TB unified memory, 130 TB/s NVSwitch) delivers 30.0x throughput on 680B LLMs with Dynamo + NIXL, Arrow adaptive scaling delivers up to 5.6x request rate, and SGLang DP Attention delivers 1.9x decode throughput",
        het["nvl72_gpus"] == 72
        and het["nvl72_grace_cpus"] == 36
        and het["nvl72_unified_mem_tb"] == 30.0
        and het["nvl72_nvswitch_bw_tbs"] == 130.0
        and het["nvl72_dynamo_680b_speedup_x"] == 30.0
        and het["arrow_adaptive_rps_gain_x"] == 5.6
        and het["sglang_dp_attention_speedup_x"] == 1.9,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
