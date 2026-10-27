#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.11: Advanced prefill-decode and KV cache tuning."""

from __future__ import annotations
import sys
from advanced_kv_cache_tuning import (
    evaluate_decode_attention_kernels,
    evaluate_chunked_prefill_tuning,
    evaluate_kv_quantization_and_eviction,
    evaluate_pd_kv_transfer_and_transpose,
    evaluate_hierarchical_kv_offload,
    should_offload_prefill,
    compute_worker_latency_cost,
    evaluate_heterogeneous_and_slo_schedulers,
)


def run_lab() -> int:
    print("=== Chapter 15.11 Lab: Advanced Prefill-Decode & KV Cache Tuning Verification ===")
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

    # 1. Split-KV Parallel Decode Attention, XQA, FlashMLA, ThunderMLA & POD-Attention (ASP Ch. 18, V12 Ch. 5)
    dk = evaluate_decode_attention_kernels(
        batch_size=1, num_query_heads=64, num_kv_heads=8, seq_len=4096, split_chunk_tokens=256, num_sms=132
    )
    check(
        "1. Standard FlashAttention-2 decode at B=1, H_kv=8 launches only 8 CTAs (6.06% of 132 H100 SMs), whereas FlashDecoding split-KV (C_split=256, S=4096) launches 128 CTAs across 16 splits (96.97% SM occupancy, up to 8.0x speedup)",
        dk["standard_fa2_ctas"] == 8.0
        and dk["standard_sm_occupancy_pct"] == 6.06
        and dk["num_kv_splits"] == 16.0
        and dk["flash_decoding_ctas"] == 128.0
        and dk["split_kv_sm_occupancy_pct"] == 96.97
        and dk["flash_decoding_max_speedup_x"] == 8.0,
    )
    check(
        "2. Two-stage split-KV online log-sum-exp reduction matches exact global softmax LSE within 1e-12 numerical precision",
        dk["lse_max_abs_err"] < 1e-12,
    )
    check(
        "3. XQA packs G=8 query heads per KV head on Llama-3-70B (64/8), and DeepSeek MLA caches 576 elements/layer (512 latent + 64 RoPE = 2.25 GQA groups equivalent)",
        dk["gqa_group_size"] == 8.0
        and dk["mla_elements_per_layer"] == 576.0
        and dk["mla_equivalent_gqa_groups"] == 2.25,
    )
    check(
        "4. ThunderMLA delivers 20%-35% faster decode throughput over FlashMLA (120-135 tok/s vs 100 tok/s) and POD-Attention SM-aware CTA scheduling gains up to 29%",
        dk["thunder_mla_min_tok_s"] == 120.0
        and dk["thunder_mla_max_tok_s"] == 135.0
        and dk["pod_attention_max_gain_pct"] == 29.0,
    )

    # 2. Chunked Prefill Token-Budget Tuning, Over-Chunking & Prefix-Cache Alignment (V12 Ch. 7 & 8, ASP Ch. 19)
    cp = evaluate_chunked_prefill_tuning()
    check(
        "5. Sarathi-Lean token budget (MaxTokensPerIter=2048) pairs 512 decode requests with a 1,536-token prefill chunk (or 45 decodes + 2,003 prefill tokens across 7 chunks for a 12,288-token prompt)",
        cp["v12_ch8_total_tokens"] == 2048.0
        and cp["available_prefill_budget"] == 2003.0
        and cp["num_chunks_2048"] == 6.0
        and cp["num_chunks_with_decode"] == 7.0,
    )
    check(
        "6. Enabling Chunked Prefill (max_num_batched_tokens=2048) eliminates the 320 ms prefill stall on 12,288-token bursts and cuts p99 ITL from 340.0 ms to 21.4 ms (15.89x reduction)",
        cp["unchunked_prefill_stall_ms"] == 320.0
        and cp["unchunked_p99_itl_ms"] == 340.0
        and cp["chunked_p99_itl_ms"] == 21.4
        and cp["itl_reduction_x"] == 15.89,
    )
    check(
        "7. SARATHI slices a 10,000-token prompt into 5 chunks of 2,000 tokens (~50-100 ms/chunk), improving throughput by 1.3x to 1.9x",
        cp["sarathi_num_chunks"] == 5.0
        and cp["sarathi_min_speedup_x"] == 1.3
        and cp["sarathi_max_speedup_x"] == 1.9,
    )
    check(
        "8. Over-chunking with max_num_batched_tokens=512 (8 ms chunk + 2 ms decode) triggers 450 context switches/sec, degrading p99 ITL from 28 ms to 45 ms and TTFT from 180 ms to 320 ms",
        cp["overchunk_switches_per_sec"] == 450.0
        and cp["overchunk_p99_itl_before_ms"] == 28.0
        and cp["overchunk_p99_itl_after_ms"] == 45.0
        and cp["overchunk_ttft_before_ms"] == 180.0
        and cp["overchunk_ttft_after_ms"] == 320.0,
    )
    check(
        "9. Naive whole-sequence prefix matching drops prefix-cache hit ratio from 45% to 8% (5.625x drop) under chunked prefill unless chunk-boundary hashing or RadixAttention is used",
        cp["prefix_hit_before_chunking"] == 0.45
        and cp["prefix_hit_after_naive_chunking"] == 0.08
        and cp["prefix_hit_drop_x"] == 5.625,
    )

    # 3. KV Cache Quantization, Block Sizing, HQQ Policy Switching & Eviction (ASP Ch. 17-19, V12 Ch. 5 & 8)
    kv = evaluate_kv_quantization_and_eviction()
    check(
        "10. A 70B MHA model (80 layers, 32 heads, 128 dim) generates 8,192 floats/layer and 655,360 floats/token (1.31 MB/token in FP16), requiring 327.68 GB (~328 GB) at 250,000 tokens vs 163.84 GB in FP8",
        kv["mha70b_floats_per_layer"] == 8192.0
        and kv["mha70b_floats_per_tok"] == 655360.0
        and kv["mha70b_fp16_bytes_per_tok"] == 1310720.0
        and kv["mha70b_250k_fp16_gb"] == 327.68
        and kv["mha70b_250k_fp8_gb"] == 163.84,
    )
    check(
        "11. Llama-3-70B GQA uses 327,680 B/token in FP16 (1.25 GiB at 4K, 39.06 GiB at 128K vs 312.5 GiB MHA), 163,840 B/token in FP8 (0.625 GiB at 4K), and 81,920 B/token in INT4",
        kv["l3_70b_fp16_bytes_per_tok"] == 327680.0
        and kv["l3_70b_fp8_bytes_per_tok"] == 163840.0
        and kv["l3_70b_int4_bytes_per_tok"] == 81920.0
        and kv["l3_70b_4k_fp16_gib"] == 1.25
        and kv["l3_70b_4k_fp8_gib"] == 0.625
        and kv["l3_70b_128k_gqa_gib"] == 39.06
        and kv["l3_70b_128k_mha_gib"] == 312.5,
    )
    check(
        "12. Reducing PagedAttention block size from 128 to 32 tokens cuts internal fragmentation at S=129 from 49.61% (127/256) to 19.38% (31/160), and with FP8 KV + 0.85 memory fraction scales sessions from 64 (52% util) to 210 (91% util)",
        kv["waste_128_pct"] == 49.61
        and kv["waste_32_pct"] == 19.38
        and kv["sessions_before_tuning"] == 64.0
        and kv["sessions_after_tuning"] == 210.0
        and kv["util_before_pct"] == 52.0
        and kv["util_after_pct"] == 91.0,
    )
    check(
        "13. Llama-13B (40 layers, 40 heads, 128 dim) at 4,096 tokens uses 3.36 GB in MHA FP16 (0.8192 MB/tok), 1.68 GB in MHA FP8, 0.671 GB in GQA-8 FP16, 0.336 GB in GQA-8 FP8, and 0.084 GB in MQA FP16",
        kv["l13b_mha_fp16_mb_per_tok"] == 0.8192
        and kv["l13b_4k_mha_fp16_gb"] == 3.36
        and kv["l13b_4k_mha_fp8_gb"] == 1.68
        and kv["l13b_4k_gqa8_fp16_gb"] == 0.671
        and kv["l13b_4k_gqa8_fp8_gb"] == 0.336
        and kv["l13b_4k_mqa_fp16_gb"] == 0.084,
    )
    check(
        "14. Real-time HQQ QuantizedCache policy switches from 8-bit to 4-bit when EMA memory utilization crosses 0.90, achieving 3.66x KV compression at S=4096 with residual_length=128 in BF16",
        kv["hqq_final_bits"] == 4.0 and kv["hqq_int4_compression_x"] == 3.66,
    )
    check(
        "15. StreamingLLM retains 4 sink tokens + 4,092 sliding-window tokens (4,096 total, 31.25x reduction at 128K), while H2O/SnapKV retains 2,052 tokens (4 sinks + 1,024 heavy hitters + 1,024 local window)",
        kv["streaming_llm_active_tokens"] == 4096.0
        and kv["swa_kv_reduction_x"] == 31.25
        and kv["h2o_retained_tokens"] == 2052.0,
    )

    # 4. Fast PD KV Handoff, LMCache RDMA Collation, NIXL Buffer & [TP_p]->[TP_d] Transpose (ASP Ch. 18, HLS Ch. 7)
    pd = evaluate_pd_kv_transfer_and_transpose()
    check(
        "16. An 8B model with 10,240-token prompts (1.5 GB KV cache/request) at 16 RPS requires 24.0 GB/s (~25 GB/s) KV transfer bandwidth, fitting inside 900 GB/s NVLink and 50-100 GB/s IB RDMA",
        pd["kv_8b_10k_max_gb"] == 1.5 and pd["required_bw_gb_s"] == 24.0,
    )
    check(
        "17. LMCache RDMA page collation from 16-token blocks (469 transfers, 20.0 ms) to 128-token slabs (59 transfers) cuts 7,500-token KV handoff latency to 8.0 ms (2.5x speedup, 60.0% reduction)",
        pd["small_transfers"] == 469.0
        and pd["collated_transfers"] == 59.0
        and pd["uncollated_rdma_ms"] == 20.0
        and pd["collated_rdma_ms"] == 8.0
        and pd["collation_speedup_x"] == 2.5
        and pd["collation_latency_reduction_pct"] == 60.0,
    )
    check(
        "18. NIXL allocates a 1 GiB (1,073,741,824 B) GPU transfer buffer (1,280 MiB when 256 MB-aligned for 7.5K FP8 tokens) with UCX_RNDV_THRESH=16384",
        pd["pd_buffer_1gib_bytes"] == 1073741824.0
        and pd["aligned_fp8_buffer_mib"] == 1280.0
        and pd["ucx_rndv_thresh"] == 16384.0,
    )
    check(
        "19. Phase-specific parallelism transpose converts [TP_p=1, PP_p=4] (8 KV heads/GPU) into [TP_d=4, PP_d=1] (2 KV heads/GPU, 0.25 shard fraction per decode rank)",
        pd["kv_heads_per_prefill_gpu"] == 8.0
        and pd["kv_heads_per_decode_gpu"] == 2.0
        and pd["decode_shard_fraction"] == 0.25,
    )

    # 5. Hierarchical KV Offloading: NVLink-C2C, LMCache, CAG vs RAG, CacheBlend & GDS/3FS (ASP Ch. 2, 4, 5; HLS Ch. 7)
    off = evaluate_hierarchical_kv_offload()
    check(
        "20. NIXL KV offload achieves 14.0x TTFT speedup on x86+H100 (PCIe Gen5 64 GB/s) and 2.0x additional (28.0x total) TTFT speedup on GH200 NVLink-C2C (900 GB/s bidirectional, 450 GB/s per direction, 7.03x PCIe Gen5), while GB200 provides 864 GB/superchip and GB300 NVL72 provides 38.7 TB (~38 TB) total memory",
        off["nvlink_c2c_bidirectional_gb_s"] == 900.0
        and off["nvlink_c2c_unidirectional_gb_s"] == 450.0
        and off["c2c_vs_pcie_bw_ratio"] == 7.03
        and off["gb200_superchip_total_gb"] == 864.0
        and off["gb300_nvl72_total_tb"] == 38.7
        and off["nixl_x86_h100_ttft_speedup_x"] == 14.0
        and off["nixl_gh200_vs_x86_ttft_speedup_x"] == 2.0
        and off["nixl_gh200_total_ttft_speedup_x"] == 28.0
        and off["dynamo_nvl72_680b_speedup_x"] == 30.0,
    )
    check(
        "21. LMCache expands KV capacity 3x in CPU RAM and 50x on NVMe SSD (4x replica cost savings), cuts warm retrieval latency to 1.0 s (vs 6-7 s cold prefill), and achieves 16.0x throughput (75,200 vs 4,700 tok/s) under 5-way concurrency",
        off["lmcache_cpu_capacity_mult"] == 3.0
        and off["lmcache_ssd_capacity_mult"] == 50.0
        and off["lmcache_replica_cost_savings_x"] == 4.0
        and off["lmcache_cpu_warm_latency_s"] == 1.0
        and off["vanilla_vllm_concurrent_tps"] == 4700.0
        and off["lmcache_throughput_mult"] == 16.0
        and off["lmcache_concurrent_tps"] == 75200.0,
    )
    check(
        "22. Long-context CAG (100,500 cached + 500 uncached tokens) cuts TTFT 10.0x (5.0 s -> 0.5 s) at $0.013/req vs $0.007/req for RAG, while CacheBlend 15% selective recomputation saves 85.0% of prefill compute (6.67x reduction)",
        off["rag_uncached_tokens"] == 5500.0
        and off["cag_uncached_tokens"] == 500.0
        and off["rag_cost_usd"] == 0.007
        and off["cag_cost_usd"] == 0.013
        and off["cag_ttft_speedup_x"] == 10.0
        and off["cacheblend_recompute_ratio"] == 0.15
        and off["cacheblend_saved_pct"] == 85.0
        and off["cacheblend_compute_reduction_x"] == 6.67,
    )
    check(
        "23. GPUDirect Storage (gdsio -x 0 vs -x 2) boosts NVMe->GPU read bandwidth by 20.0% (8.0 -> 9.6 GB/s) and cuts latency by 20.0% (1.25 -> 1.00 ms), while DeepSeek 3FS reaches 6.6 TB/s (6.0x Ceph's 1.1 TB/s)",
        off["gds_bw_gain_pct"] == 20.0
        and off["gds_lat_reduction_pct"] == 20.0
        and off["deepseek_3fs_vs_ceph_x"] == 6.0,
    )

    # 6. Conditional Prefill Offload Routing, Multifactor Latency Cost, Heterogeneous PD & SLO Schedulers (ASP Ch. 17 & 18)
    offload_long = should_offload_prefill(
        prompt_length=1024, prefix_cached_length=512, prefill_queue_size=4, decode_active_reqs=3
    )  # eff_len = 512 >= 256 and queue 4 < 10 -> True
    keep_local_cached = should_offload_prefill(
        prompt_length=1024, prefix_cached_length=900, prefill_queue_size=4, decode_active_reqs=3
    )  # eff_len = 124 < 256 and decode 3 < 8 -> False
    keep_local_queue_full = should_offload_prefill(
        prompt_length=1024, prefix_cached_length=0, prefill_queue_size=12, decode_active_reqs=3
    )  # queue 12 >= 10 and decode 3 < 8 -> False
    offload_busy_decode = should_offload_prefill(
        prompt_length=200, prefix_cached_length=100, prefill_queue_size=12, decode_active_reqs=9
    )  # decode 9 >= 8 and eff_len = 100 >= 64 -> True

    cost_cached_worker = compute_worker_latency_cost(
        occupancy_percent=0.60, active_reqs=5, cache_match_flag=True, mem_bw_percent=0.50, recent_prefix_flag=True
    )  # 1.8 + 5.0 - 10.0 + 0.25 - 1.0 = -3.95
    cost_cold_worker = compute_worker_latency_cost(
        occupancy_percent=0.30, active_reqs=2, cache_match_flag=False, mem_bw_percent=0.20, recent_prefix_flag=False
    )  # 0.9 + 2.0 + 0.1 = 3.00

    check(
        "24. Conditional prefill offload router and KV-aware latency cost function (-3.95 cached warm worker vs +3.00 idle cold worker) route requests to prefix-matching workers while shedding overloaded prefill queues",
        offload_long is True
        and keep_local_cached is False
        and keep_local_queue_full is False
        and offload_busy_decode is True
        and round(cost_cached_worker, 2) == -3.95
        and round(cost_cold_worker, 2) == 3.00,
    )

    het = evaluate_heterogeneous_and_slo_schedulers()
    check(
        "25. Splitwise achieves 1.4x throughput at 20% lower cost and 2.35x RPS at iso-cost/power (4x H100 + 4x A100, or 25% fewer GPUs), HexGen-2 achieves up to 2.0x throughput or 30% lower cost, Mooncake rejects low-priority requests when est_ttft (550 ms) > 500 ms SLO, and Arrow reaches up to 5.6x request serving rate",
        het["splitwise_throughput_gain_x"] == 1.4
        and het["splitwise_cost_reduction_pct"] == 20.0
        and het["splitwise_iso_budget_rps_x"] == 2.35
        and het["splitwise_gpu_count_reduction_pct"] == 25.0
        and het["hexgen2_max_throughput_x"] == 2.0
        and het["hexgen2_cost_reduction_pct"] == 30.0
        and het["qos_total_frac"] == 1.0
        and het["est_ttft_ms"] == 550.0
        and het["low_priority_admitted"] == 0.0
        and het["high_priority_admitted"] == 1.0
        and het["arrow_max_serving_rate_x"] == 5.6,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
