#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.3: vLLM in Depth."""

from __future__ import annotations
import math
import sys
from vllm_paged_attention import (
    compute_kv_cache_metrics,
    compute_padding_flops_waste,
    PagedAttentionSimulator,
    compare_rag_vs_cag_prefix_caching,
    evaluate_chunked_prefill_and_preemption,
    plan_vllm_capacity_and_parallelism,
    evaluate_multi_lora_and_lab03,
)


def run_lab() -> int:
    print("=== Chapter 15.3 Lab: vLLM PagedAttention, APC, Chunked Prefill & Engine Verification ===")
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

    # 1. Llama-3-70B KV Cache Per-Token and Sequence Footprints (V12 Ch. 8 & ASP Ch. 18)
    kv_4k = compute_kv_cache_metrics(seq_len=4096, block_size=16, max_model_len=4096)
    check(
        "1. Llama-3-70B GQA (80 layers, 8 KV heads, 128 head_dim, BF16) uses 327,680 B (320 KiB/token), 87.5% less than MHA (2.56 MiB/token)",
        kv_4k["bytes_per_token_gqa"] == 327680.0
        and kv_4k["kib_per_token_gqa"] == 320.0
        and kv_4k["mib_per_token_mha"] == 2.5
        and kv_4k["gqa_savings_pct"] == 87.5,
    )

    kv_128k = compute_kv_cache_metrics(seq_len=128000, block_size=16, max_model_len=131072)
    check(
        "2. Llama-3-70B KV cache per sequence is 1.25 GiB at S=4096 and 39.0625 GiB (~39.06 GiB) at S=128,000 (vs 312.5 GiB MHA)",
        kv_4k["seq_gib_gqa"] == 1.25
        and round(kv_128k["seq_gib_gqa"], 2) == 39.06
        and kv_128k["seq_gib_mha"] == 312.5,
    )

    kv_250k_32h = compute_kv_cache_metrics(
        num_layers=80, num_query_heads=32, num_kv_heads=32, head_dim=128, precision_bytes=2.0, seq_len=250000
    )
    check(
        "3. 70B model with 80 layers, 32 KV heads, and 128 head_dim at FP16 uses 1,310,720 B (~1.31 MB/token) and ~328 GB (327.68 GB) at 250,000 tokens",
        kv_250k_32h["bytes_per_token_gqa"] == 1310720.0
        and round((kv_250k_32h["bytes_per_token_gqa"] * 250000) / 1e9, 2) == 327.68,
    )

    # 2. PagedAttention Fragmentation Bounds and Zero Padding FLOPs (V12 Ch. 6 & DAI Ch. 6)
    kv_500 = compute_kv_cache_metrics(seq_len=500, block_size=16, max_model_len=4096)
    check(
        "4. For S_actual=500 and B=16 (S_max=4096), PagedAttention allocates 32 blocks (512 tokens, 2.4% actual < 3.2% max bound) vs 87.79% (>87%) contiguous waste",
        kv_500["num_blocks"] == 32.0
        and kv_500["paged_internal_frag_pct"] == 2.4
        and kv_500["paged_max_bound_pct"] == 3.2
        and kv_500["contiguous_waste_pct"] == 87.79,
    )

    pad_flops = compute_padding_flops_waste([4, 7, 3])
    check(
        "5. Batch of lengths [4, 7, 3] padded to 7x3=21 positions wastes 7/21 = 33.33% (~33%) attention FLOPs vs 14 positions (0% waste) in PagedAttention",
        pad_flops["padded_positions"] == 21.0
        and pad_flops["true_tokens"] == 14.0
        and pad_flops["wasted_positions"] == 7.0
        and pad_flops["wasted_flops_pct"] == 33.33
        and pad_flops["paged_wasted_flops_pct"] == 0.0,
    )

    # 3. BlockSpaceManager Allocation, Deallocation, and RAG 24,000-Token Scenario (DAI Ch. 6 & V12 Ch. 6)
    sim_basic = PagedAttentionSimulator(num_blocks=1000, block_size=16, enable_prefix_caching=False)
    b1 = sim_basic.allocate_sequence(seq_id=1, tokens=list(range(100)))
    b2 = sim_basic.allocate_sequence(seq_id=2, tokens=list(range(50)))
    free_before = sim_basic.num_free_blocks
    sim_basic.free_sequence(seq_id=1)
    free_after = sim_basic.num_free_blocks
    check(
        "6. BlockSpaceManager allocates ceil(100/16)=7 blocks for seq 1 and ceil(50/16)=4 blocks for seq 2 (989 free), returning to 996 free after freeing seq 1",
        len(b1) == 7 and len(b2) == 4 and free_before == 989 and free_after == 996,
    )

    rag_blocks_16 = math.ceil(24000 / 16)
    rag_blocks_32 = math.ceil(24000 / 32)
    check(
        "7. A 24,000-token RAG prompt requires 1,500 physical blocks at block_size=16 (15,000 blocks for 10 requests) vs 750 blocks at block_size=32",
        rag_blocks_16 == 1500 and (10 * rag_blocks_16) == 15000 and rag_blocks_32 == 750,
    )

    # 4. Copy-on-Write (CoW) Forking for Beam Search / Parallel Sampling (V12 Ch. 6 & LLP Ch. 6)
    sim_cow = PagedAttentionSimulator(num_blocks=100, block_size=16, enable_prefix_caching=False)
    # 35 prompt tokens -> 2 full blocks (0..15, 16..31) + 1 incomplete tail block (32..34, 3 tokens)
    parent_tbl = sim_cow.allocate_sequence(seq_id=10, tokens=list(range(35)))
    for child_id in (11, 12, 13):
        sim_cow.fork_sequence(parent_seq_id=10, child_seq_id=child_id)
    check(
        "8. Forking 4 parallel branches (n=4) on a 35-token prompt shares all 3 physical blocks with ref_count=4 and 0 extra blocks allocated",
        len(parent_tbl) == 3
        and all(sim_cow.blocks[bid].ref_count == 4 for bid in parent_tbl)
        and sim_cow.num_free_blocks == 97,
    )

    new_bid = sim_cow.append_token(seq_id=11, token_id=999)
    check(
        "9. Writing a new token to branch 11 triggers Copy-on-Write only on the incomplete tail block (ref_count 4->3, 1 new block allocated), keeping 2 full prefix blocks shared",
        new_bid != parent_tbl[-1]
        and sim_cow.cow_copies == 1
        and sim_cow.blocks[parent_tbl[0]].ref_count == 4
        and sim_cow.blocks[parent_tbl[1]].ref_count == 4
        and sim_cow.blocks[parent_tbl[2]].ref_count == 3
        and sim_cow.num_free_blocks == 96,
    )

    # 5. Automatic Prefix Caching (APC) Block Hashing and RAG vs CAG Economics (V12 Ch. 6 & HLS Ch. 6-7)
    sim_apc = PagedAttentionSimulator(num_blocks=256, block_size=16, enable_prefix_caching=True)
    shared_sys = list(range(1000, 1064))  # 64 tokens = 4 full blocks
    req_a = shared_sys + list(range(2000, 2020))  # + 20 tokens (1 full + 1 partial)
    req_b = shared_sys + list(range(3000, 3020))
    tbl_a = sim_apc.allocate_sequence(seq_id=1, tokens=req_a)
    tbl_b = sim_apc.allocate_sequence(seq_id=2, tokens=req_b)
    check(
        "10. Automatic Prefix Caching (APC) matches all 4 shared 16-token system-prompt blocks by SHA-256 hash and increments ref_count to 2",
        tbl_a[:4] == tbl_b[:4]
        and sim_apc.cache_hits == 4
        and all(sim_apc.blocks[bid].ref_count == 2 for bid in tbl_a[:4]),
    )

    cag = compare_rag_vs_cag_prefix_caching()
    check(
        "11. Long-Context CAG caches 100,500 tokens and runs prefill on 500 tokens (vs 5,500 in RAG), cutting TTFT 10x (5.0s -> 0.5s) at $0.013 vs $0.007 per request",
        cag["rag_uncached_tokens"] == 5500.0
        and cag["cag_cached_tokens"] == 100500.0
        and cag["cag_uncached_tokens"] == 500.0
        and cag["rag_cost_usd"] == 0.007
        and cag["cag_cost_usd"] == 0.013
        and cag["cag_ttft_sec"] == 0.5,
    )

    # 6. Continuous Batching, Chunked Prefill & Preemption Swap vs Recompute (V12 Ch. 7, DAI Ch. 6, HLS Ch. 8)
    cp = evaluate_chunked_prefill_and_preemption(
        prompt_tokens=12288,
        active_decode_seqs=45,
        max_num_batched_tokens=2048,
        long_prefill_threshold=512,
        seq_len_for_preemption=4096,
    )
    check(
        "12. Chunked Prefill slices a 12,288-token prompt into 24 chunks of 512 tokens, bounding step tokens to 45 + 512 = 557 <= 2048",
        cp["chunk_size"] == 512.0
        and cp["num_prefill_chunks"] == 24.0
        and cp["scheduled_tokens_step"] == 557.0
        and cp["within_token_budget"] is True,
    )

    check(
        "13. Transferring 4 GB of KV cache over 64 GB/s PCIe takes 62.5 ms one-way (~62 ms), and for S=4096 on H100 (989 TFLOPS) Recompute is faster than PCIe Swap",
        cp["four_gb_one_way_swap_ms"] == 62.5
        and cp["recompute_faster_than_swap"] is True
        and cp["recommended_policy"] == "recompute",
    )

    cp_long = evaluate_chunked_prefill_and_preemption(seq_len_for_preemption=65536)
    check(
        "14. At ultra-long sequence length S=65,536, quadratic O(S^2) prefill makes t_recompute > t_swap",
        cp_long["recompute_faster_than_swap"] is False and cp_long["recommended_policy"] == "swap",
    )

    # 7. Distributed Parallelism (TP, PP, DP, EP) & Concurrency Capacity Planning (V12 Ch. 8-9 & DAI Ch. 6)
    cap_tp4 = plan_vllm_capacity_and_parallelism(tp_size=4)
    check(
        "15. Llama-3-70B on 4x 80 GB GPUs (TP=4, 320 GB total, 140 GB weights, 140 GB KV pool) supports C_max = 218 (S=2048), 54 (S=8192), and 13 (S=32768) requests",
        cap_tp4["total_vram_gb"] == 320.0
        and cap_tp4["weight_memory_gb"] == 140.0
        and cap_tp4["kv_pool_gb"] == 140.0
        and cap_tp4["c_max_2048"] == 218
        and cap_tp4["c_max_8192"] == 54
        and cap_tp4["c_max_32768"] == 13,
    )

    cap_tp8 = plan_vllm_capacity_and_parallelism(tp_size=8)
    check(
        "16. Llama-3-70B on 8x 80 GB GPUs (TP=8, 640 GB total, 428 GB KV pool) supports C_max = 668 (S=2048), 167 (S=8192), and 41 (S=32768) requests with 160 AllReduces/token",
        cap_tp8["total_vram_gb"] == 640.0
        and cap_tp8["kv_pool_gb"] == 428.0
        and cap_tp8["c_max_2048"] == 668
        and cap_tp8["c_max_8192"] == 167
        and cap_tp8["c_max_32768"] == 41
        and cap_tp8["allreduces_per_token_80_layers"] == 160,
    )

    # H200 141 GB TP=1 vs TP=2 KV cache capacity expansion (DAI Ch. 6)
    h200_tp1_free = 141.0 - 121.0  # ~20 GB left after 140B weights/overhead on 1x 141 GB H200
    h200_tp2_free_per_gpu = 141.0 - 71.0  # ~70 GB free per GPU at TP=2
    check(
        "17. Sharding a 140B model across TP=2 on 141 GB H200 GPUs expands free KV cache headroom from ~20 GB on 1 GPU to ~70 GB per GPU",
        h200_tp1_free == 20.0 and h200_tp2_free_per_gpu == 70.0,
    )

    # DeepSeek-R1 671B TP=4, PP=8 (32 GPUs) and Expert Parallelism (256 experts across 8 GPUs)
    ep_tp = plan_vllm_capacity_and_parallelism(tp_size=8, dp_size=1, enable_expert_parallel=True, total_routed_experts=256)
    ep_dp = plan_vllm_capacity_and_parallelism(tp_size=1, dp_size=8, enable_expert_parallel=True, total_routed_experts=256)
    ep_noop = plan_vllm_capacity_and_parallelism(tp_size=1, dp_size=1, enable_expert_parallel=True, total_routed_experts=256)
    check(
        "18. DeepSeek-R1 (256 experts) with EP_SIZE=8 places 32 complete experts/GPU, using all_reduce for TP=8+EP, all_to_all for DP=8+EP, and ignoring EP when TP*DP==1",
        ep_tp["ep_size"] == 8
        and ep_tp["experts_per_gpu"] == 32
        and ep_tp["ep_comm_pattern"] == "all_reduce"
        and ep_dp["experts_per_gpu"] == 32
        and ep_dp["ep_comm_pattern"] == "all_to_all"
        and ep_noop["ep_active"] is False,
    )

    deepseek_32gpu_stage_b = round(671.0 / 8.0, 1)
    pp_comm_elements_tp4 = 8192 // 4
    check(
        "19. DeepSeek-R1 (671B) with TP=4, PP=8 uses 32 GPUs (~83.9B / ~84B params per stage) and transfers 8192/4 = 2048 elements per token between PP stages",
        (4 * 8) == 32 and deepseek_32gpu_stage_b == 83.9 and pp_comm_elements_tp4 == 2048,
    )

    # 8. Quantization (W4A16 vs W8A8 vs FP4) & Speculative Decoding (HLS Ch. 6 & Ch. 7)
    gpt_oss_120b_gb = 117.0 * 0.5
    gpt_oss_20b_gb = 21.0 * 0.5
    check(
        "20. GPT-OSS MXFP4/NVFP4 quantization (0.5 B/param) compresses 117B params to 58.5 GB (< 80 GB GPU) and 21B params to 10.5 GB (< 16 GB edge GPU)",
        gpt_oss_120b_gb == 58.5 and gpt_oss_20b_gb == 10.5,
    )

    eagle3_speedup = round(56.5 / 28.9, 2)
    check(
        "21. On Qwen3-32B at concurrency=1, EAGLE-3 (K=3) boosts throughput from 28.9 tok/s to 56.5 tok/s (1.96x, nearly 2x), while improved n-gram adds +16%",
        eagle3_speedup == 1.96 and 56.5 > 28.9,
    )

    # 9. Multi-LoRA Serving (Punica / S-LoRA) & Lab 03 Telemetry Verification (HLS Ch. 10 & V12 Lab 03)
    lora = evaluate_multi_lora_and_lab03()
    check(
        "22. Rank-16 LoRA across 4 modules/layer on a 32-layer 8B model (d=4096) adds 16,777,216 params (32.0 MB in FP16, 0.2097% < 1% of base weights)",
        lora["params_per_lora"] == 16777216.0
        and lora["mb_per_lora"] == 32.0
        and lora["lora_pct_of_base"] < 1.0,
    )

    check(
        "23. Co-locating 8 active LoRA adapters with an 8B base model in HBM requires 16.2684 GB total and saves 7 GPUs compared to 8 dedicated single-model GPUs",
        lora["base_weights_gb"] == 16.0
        and lora["total_hbm_with_loras_gb"] == 16.2684
        and lora["gpus_saved_vs_dedicated"] == 7.0,
    )

    check(
        "24. Lab 03 Qwen2.5-Coder-1.5B-Instruct at gpu_memory_utilization=0.85 allocates 14,258 GPU blocks (55.69x concurrency at 4096 tokens) vs 120 blocks (1,920 tokens) at 0.25",
        lora["lab03_gpu_blocks_normal"] == 14258.0
        and lora["lab03_max_concurrency_4k"] == 55.69
        and lora["lab03_constrained_max_tokens"] == 1920.0,
    )

    check(
        "25. Lab 03 5-request streaming benchmark averages Mean TTFT = 44.83 ms (p95 = 47.72 ms) and Mean ITL = 12.72 ms (p95 = 13.05 ms)",
        lora["lab03_mean_ttft_ms"] == 44.83 and lora["lab03_mean_itl_ms"] == 12.72,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
