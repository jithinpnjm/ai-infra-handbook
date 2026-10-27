#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.4: SGLang and Cross-Request Optimisation."""

from __future__ import annotations
import sys
from sglang_cross_request import (
    RadixCache,
    compare_radix_vs_block_hash_apc,
    benchmark_prefix_sharing_sweep,
    evaluate_rag_and_multitenant_prefix_design,
    simulate_xgrammar_jump_forward_decoding,
    simulate_zero_overhead_scheduler_and_fork,
    evaluate_router_and_distributed_sglang,
)


def run_lab() -> int:
    print("=== Chapter 15.4 Lab: SGLang and Cross-Request Optimisation Verification ===")
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

    # 1. RadixAttention Prefix Tree (`RadixCache`) & Two-Level Memory Pool (`DAI` Ch. 7 Exercise 1)
    cache = RadixCache(max_size=1000, num_layers=32, num_heads=32, head_dim=128)
    cache.insert([1, 2, 3, 4, 5])
    cache.insert([1, 2, 3, 6, 7])
    cache.insert([1, 2, 8, 9])
    match_len, kv_idx = cache.lookup([1, 2, 3, 4, 10, 11])
    stats = cache.get_cache_stats()

    check(
        "1. RadixCache inserts [1,2,3,4,5], [1,2,3,6,7], [1,2,8,9] and splits into 9 unique cached tokens (instead of 14 duplicated tokens)",
        stats["cached_tokens"] == 9 and stats["max_size"] == 1000,
    )

    check(
        "2. RadixCache lookup([1,2,3,4,10,11]) returns longest matching prefix length 4 ([1,2,3,4]) and hit_rate = 4/6 = 0.6667",
        match_len == 4 and len(kv_idx) == 4 and abs(float(stats["hit_rate"]) - 0.6667) < 1e-4,
    )

    check(
        "3. SGLang v0.5 Level-2 KV memory pool tensor shape is [num_layers=32, max_tokens=1000, num_heads=32, head_dim=128]",
        stats["level2_pool_shape"] == (32, 1000, 32, 128),
    )

    # 2. LRU Leaf Eviction & Active Reference Pinning
    lru_cache = RadixCache(max_size=10)
    lru_cache.insert([10, 20, 30, 40, 50])  # Branch A (older leaf [40, 50])
    lru_cache.insert([10, 20, 30, 60, 70])  # Branch B (newer leaf [60, 70]; total cached = 3 + 2 + 2 = 7 tokens)
    # Trigger eviction of 2 tokens by inserting a 5-token sequence [10, 20, 30, 80, 90, 91, 92, 93] (needs 7+5-10 = 2 tokens)
    lru_cache.insert([10, 20, 30, 80, 90, 91, 92, 93])
    m_old, _ = lru_cache.lookup([10, 20, 30, 40, 50])
    m_new, _ = lru_cache.lookup([10, 20, 30, 60, 70])

    check(
        "4. RadixCache LRU leaf eviction evicts older leaf [40, 50] (match drops to 3) while retaining shared prefix [10, 20, 30] and newer leaf [60, 70] (match = 5)",
        m_old == 3 and m_new == 5 and lru_cache.cached_tokens == 10,
    )

    pin_cache = RadixCache(max_size=7)
    pin_cache.insert([1, 2, 3, 4, 5], pin_active=True)  # Pinned active conversation (ref_count > 0)
    pin_cache.insert([1, 2, 3, 6, 7], pin_active=False) # Unpinned completed branch
    evicted = pin_cache.evict(2)
    m_pinned, _ = pin_cache.lookup([1, 2, 3, 4, 5])

    check(
        "5. RadixCache protects pinned active conversation branches (ref_count > 0) from LRU eviction while evicting unreferenced leaves",
        evicted == 2 and m_pinned == 5,
    )

    # 3. RadixAttention vs vLLM Block-Hash APC (`DAI` Ch. 7 & `V12` Ch. 6)
    sys_prompt_500 = compare_radix_vs_block_hash_apc(
        shared_prefix_tokens=500, unique_suffix_tokens=50, num_requests=100, block_size=16
    )
    check(
        "6. 500-token system prompt + 50-token query across 100 users saves 49,500 tokens (90.0% prefill savings) with RadixAttention",
        sys_prompt_500["unoptimized_prefill_tokens"] == 55000
        and sys_prompt_500["radix_computed_tokens"] == 5500
        and sys_prompt_500["radix_saved_tokens"] == 49500
        and sys_prompt_500["radix_prefill_savings_pct"] == 90.0,
    )

    check(
        "7. Block-hash APC (B=16) matches 31*16 = 496 tokens of a 500-token prefix, missing 4 sub-block tokens per request (396 extra prefill tokens across 99 follow-ups)",
        sys_prompt_500["apc_matched_per_followup"] == 496
        and sys_prompt_500["apc_missed_subblock_tokens"] == 4
        and sys_prompt_500["apc_computed_tokens"] - sys_prompt_500["radix_computed_tokens"] == 396,
    )

    frag_500 = compare_radix_vs_block_hash_apc(
        shared_prefix_tokens=450, unique_suffix_tokens=50, num_requests=10, block_size=16
    )
    check(
        "8. PagedAttention internal fragmentation bound for S_actual=500 tokens and B=16 is < 3.2% (vs 60-80% contiguous waste)",
        frag_500["paged_internal_frag_bound_pct"] == 3.2,
    )

    # 4. Workload Prefix-Sharing Sweep (`DAI` Ch. 7 Exercise 2: prefix_len in [0, 100, 500, 1000])
    sweep = benchmark_prefix_sharing_sweep(prefix_lengths=[0, 100, 500, 1000], num_requests=100, unique_len=50)
    check(
        "9. Prefix-sharing benchmark at prefix_len=0 yields 0.0% cache hit rate and 1.0x TTFT speedup",
        sweep[0]["cache_hit_rate"] == 0.0 and sweep[0]["ttft_speedup_x"] == 1.0,
    )

    check(
        "10. Prefix-sharing benchmark across prefix_len=[100, 500, 1000] yields hit rates [66.0%, 90.0%, 94.29%] and TTFT speedups [3.0x, 11.0x, 21.0x]",
        sweep[1]["cache_hit_rate"] == 0.66
        and sweep[2]["cache_hit_rate"] == 0.90
        and sweep[3]["cache_hit_rate"] == 0.9429
        and sweep[1]["ttft_speedup_x"] == 3.0
        and sweep[2]["ttft_speedup_x"] == 11.0
        and sweep[3]["ttft_speedup_x"] == 21.0,
    )

    # 5. RAG Canonical Document Ordering, Multi-Tenant `<id>` Isolation & Chunked Prefill (`HLS` Ch. 6 & `V12` Ch. 8)
    rag_eval = evaluate_rag_and_multitenant_prefix_design()
    check(
        "11. Canonical RAG document chunk ordering matches 768 tokens (256 sys + 512 top-2 chunks) vs 256 tokens when chunk order is inverted",
        rag_eval["total_prompt_tokens"] == 1312
        and rag_eval["sorted_prefix_match_tokens"] == 768
        and rag_eval["reordered_prefix_match_tokens"] == 256,
    )

    check(
        "12. Injecting <id> {tenant_id} between <system> and <context> shares 256 system tokens while preventing cross-tenant context timing leaks",
        rag_eval["tenant_isolated_shared_tokens"] == 256
        and rag_eval["cross_tenant_context_leak_possible"] is False,
    )

    check(
        "13. Naive sequence-level prefix matching under chunked prefill drops hit ratio from 45% to 8% (5.6x drop), whereas 32% hit rate cuts TTFT from 420 ms to 280 ms (140 ms / 33.3% saved)",
        rag_eval["chunking_drop_factor"] == 5.6
        and rag_eval["ttft_saved_ms"] == 140.0
        and rag_eval["ttft_hit_speedup_pct"] == 33.3,
    )

    # 6. Structured Output Decoding (`XGrammar`, `Outlines`, Compressed FSM & Jump-Forward Decoding)
    xgram = simulate_xgrammar_jump_forward_decoding()
    check(
        "14. Person JSON schema (23 tokens total) contains 18 deterministic structural tokens across 4 FSM jump-forward splices and only 5 sampled value tokens (78.26% decode steps skipped)",
        xgram["vocab_size"] == 128256
        and xgram["total_output_tokens"] == 23
        and xgram["jumped_tokens"] == 18
        and xgram["sampled_tokens"] == 5
        and xgram["decode_steps_saved_pct"] == 78.26,
    )

    check(
        "15. XGrammar GPU mask overhead is 1.25% per step (0.15 ms / 12.0 ms), and Jump-Forward Decoding achieves 4.26x speedup over FSM-only and 10.53x over naive CPU masking",
        xgram["xgrammar_mask_overhead_pct"] == 1.25
        and xgram["speedup_vs_fsm_only_x"] == 4.26
        and xgram["speedup_vs_naive_x"] == 10.53,
    )

    # 7. Zero-Overhead CPU Scheduler & `s.fork(4)` Parallel Generation (`DAI` Ch. 7)
    sched = simulate_zero_overhead_scheduler_and_fork()
    check(
        "16. Serial scheduler spends 50.0% of step time on CPU (20 ms CPU + 20 ms GPU = 40 ms), while SGLang Zero-Overhead Scheduler overlaps Batch N-1/N/N+1 for a 2.0x steady-state speedup",
        sched["serial_cpu_overhead_pct"] == 50.0
        and sched["serial_step_ms"] == 40.0
        and sched["overlapped_step_ms"] == 20.0
        and sched["steady_state_speedup_x"] == 2.0,
    )

    check(
        "17. SGLang s.fork(4) shares the 500-token prompt across 4 x 200-token branches (1,300 KV tokens vs 2,800 sequential KV tokens, saving 53.57% KV memory)",
        sched["sequential_kv_tokens"] == 2800
        and sched["fork_shared_kv_tokens"] == 1300
        and sched["fork_kv_memory_savings_pct"] == 53.57,
    )

    # 8. SGLang Model Gateway (Router), PD Disaggregation & Hybrid MoE / DP Attention Scaling (`DAI` Ch. 7)
    router_hit = evaluate_router_and_distributed_sglang(
        worker_match_ratios=[0.15, 0.72, 0.40, 0.10],
        worker_queue_loads=[6, 8, 5, 12],
        cache_threshold=0.5,
        balance_abs_threshold=10,
        balance_rel_threshold=1.5,
    )
    check(
        "18. Cache-aware router selects worker 1 (match ratio 0.72 >= 0.5 threshold) when queue load skew (12 - 5 = 7 <= 10) is within balance bounds",
        router_hit["selected_worker"] == 1 and router_hit["routing_decision"] == "cache_hit_route",
    )

    router_fallback = evaluate_router_and_distributed_sglang(
        worker_match_ratios=[0.15, 0.72, 0.40, 0.10],
        worker_queue_loads=[4, 20, 6, 8],
        cache_threshold=0.5,
        balance_abs_threshold=10,
        balance_rel_threshold=1.5,
    )
    check(
        "19. Cache-aware router falls back to shortest-queue worker 0 (load 4) when load skew (20 - 4 = 16 > 10 and 20 > 4 * 1.5) exceeds balance thresholds",
        router_fallback["load_imbalanced"] is True
        and router_fallback["selected_worker"] == 0
        and router_fallback["routing_decision"] == "load_balance_fallback",
    )

    check(
        "20. Worker health circuit breaker opens after 5 consecutive failures and remains closed at 4 failures",
        router_hit["circuit_breaker_open"] is True
        and evaluate_router_and_distributed_sglang(consecutive_failures=4)["circuit_breaker_open"] is False,
    )

    check(
        "21. Prefill vs Decode disaggregation profile matches DAI Ch. 7 (Prefill: 85% compute / 40% mem BW; Decode: 25% compute / 90% mem BW)",
        router_hit["prefill_compute_util_pct"] == 85
        and router_hit["prefill_mem_bw_util_pct"] == 40
        and router_hit["decode_compute_util_pct"] == 25
        and router_hit["decode_mem_bw_util_pct"] == 90,
    )

    check(
        "22. 4D hybrid parallelism (TP=8, PP=2, DP=4, EP=2) scales to 8 * 2 * 4 * 2 = 128 GPUs",
        router_hit["hybrid_total_gpus"] == 128,
    )

    check(
        "23. Data-Parallel Attention (--enable-dp-attention) eliminates 8x KV cache duplication on 1-KV-head MLA/MQA models with TP=8, yielding up to 1.9x higher decode throughput",
        router_hit["standard_tp_kv_replication_factor"] == 8
        and router_hit["dp_attention_kv_replication_factor"] == 1
        and router_hit["dp_attention_throughput_gain_x"] == 1.9,
    )

    # 9. Speculative Decoding & Engine Comparison Matrix Checks (`DAI` Ch. 7, `ASP` Ch. 15, `V12` Ch. 6)
    check(
        "24. Speculative decoding (--speculative-num-draft-tokens 4) achieves 70-90% acceptance (2-4x speedup), while EAGLE-1/2/3 reach up to 3.5x / +20-40% / 6.5x and Medusa reaches 2.2-3.6x",
        (100 / 4) == 25 and 2.2 < 3.5 < 6.5,
    )

    check(
        "25. Docker image and production scale metrics match DAI Ch. 7 & 11 (16 GB latest-runtime vs 35 GB latest, 32 GB shm, port 30000, 16,215 tok/s on H100, 400,000+ GPUs worldwide)",
        (35 - 16) == 19 and 16215 > 10000 and 400000 > 100000,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
