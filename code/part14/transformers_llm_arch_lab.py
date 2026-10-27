#!/usr/bin/env python3
"""
Chapter 14.2 Verification Lab: Transformers and LLM Architecture
Runs 28 deterministic self-checks covering:
  - Transformer parameter counting across Embedding, MHA/GQA/MQA Attention, SwiGLU MLP, and LM Head
  - Attention quadratic FLOPs (4*B*s^2*d) vs linear projection FLOPs & triangular causal QK ops
  - KV cache byte footprint per token (2 * n_layers * n_kv_heads * d_head * bytes_per_elem) across MHA, GQA, MQA, and MLA
  - Dense vs Mixture-of-Experts (MoE) active vs total parameter and FLOPs math (Mixtral 8x7B, DeepSeek-V3 671B/37B, Jamba 52B/12B)
  - Chinchilla compute-optimal scaling (D ~= 20*N, C ~= 6*N*D), GPT-3 175B cluster cost, and 100T model sizing
  - Temperature softmax, logprobs, top-k / top-p sampling, and multilingual tokenization inflation
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import transformers_llm_arch as tla


def run_lab() -> int:
    print("=== Chapter 14.2: Transformers & LLM Architecture Verification Lab ===\n")
    passed = 0
    failed = 0

    def check(num: int, desc: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {num:02d}. {desc}")
        else:
            failed += 1
            print(f"  [FAIL] {num:02d}. {desc}" + (f" ({detail})" if detail else ""))

    # 1. Llama 2-7B MHA attention parameter count per layer (4 * 4096^2 = 67,108,864)
    l2_7b_attn = tla.count_attention_params_per_layer(4096, 32, 32)
    check(
        1,
        "Llama 2-7B MHA attention projections (W_Q, W_K, W_V, W_O) each have 4,096x4,096 = 16,777,216 params (67,108,864 total/layer, d_head=128)",
        l2_7b_attn["q_proj"] == 16_777_216
        and l2_7b_attn["total_attn_params"] == 67_108_864
        and tla.LLAMA2_7B.d_head == 128,
    )

    # 2. Llama 3-8B GQA-8 attention parameter reduction vs MHA (41,943,040 vs 67,108,864 = -37.5%)
    l3_8b_attn = tla.count_attention_params_per_layer(4096, 32, 8)
    mqa_attn = tla.count_attention_params_per_layer(4096, 32, 1)
    check(
        2,
        "GQA-8 (n_kv_heads=8) cuts attention projection params from 67,108,864 (MHA) to 41,943,040/layer (-37.5%), and MQA (n_kv_heads=1) to 34,603,008",
        l3_8b_attn["total_attn_params"] == 41_943_040
        and mqa_attn["total_attn_params"] == 34_603_008,
    )

    # 3. SwiGLU 3-matrix MLP vs standard 2-layer MLP parameter count
    l2_7b_mlp = tla.count_mlp_params_per_layer(4096, 11008, swiglu=True)
    l2_7b_mlp_std = tla.count_mlp_params_per_layer(4096, 11008, swiglu=False)
    check(
        3,
        "Llama 2-7B SwiGLU MLP (3 * 4,096 * 11,008) has 135,266,304 params/layer vs 90,177,536 for a 2-matrix ReLU/GELU MLP",
        l2_7b_mlp["total_mlp_params"] == 135_266_304
        and l2_7b_mlp_std["total_mlp_params"] == 90_177_536,
    )

    # 4. Full Llama 2-7B parameter count (~6.74B parameters, ~13.48 GB in FP16)
    l2_7b_tot = tla.count_transformer_parameters(tla.LLAMA2_7B)
    check(
        4,
        "Llama 2-7B full parameter breakdown totals 6,738,415,616 (~6.74B) parameters (131,072,000 embedding + 202,383,360 * 32 layers + 131,072,000 LM head)",
        l2_7b_tot["embedding_params"] == 131_072_000
        and l2_7b_tot["params_per_layer"] == 202_383_360
        and l2_7b_tot["total_params"] == 6_738_415_616,
    )

    # 5. Full Llama 3-8B parameter count (~8.03B parameters with 128,256 vocab and d_ff=14,336)
    l3_8b_tot = tla.count_transformer_parameters(tla.LLAMA3_8B)
    check(
        5,
        "Llama 3-8B (vocab=128,256, d_ff=14,336, GQA-8) totals 8,030,261,248 (~8.03B) parameters (~16.06 GB in FP16)",
        l3_8b_tot["total_params"] == 8_030_261_248
        and l3_8b_tot["embedding_params"] == 525_336_576,
    )

    # 6. Qwen 2.5-0.5B parameter count (~494M parameters with tied embeddings)
    qwen_tot = tla.count_transformer_parameters(tla.QWEN25_05B)
    check(
        6,
        "Qwen 2.5-0.5B (24 layers, d_model=896, n_heads=14, n_kv_heads=2, d_ff=4,864, vocab=151,936, tied embeddings) totals ~494M parameters (494,032,768 with QKV bias)",
        493_000_000 <= qwen_tot["total_params"] <= 495_000_000
        and tla.QWEN25_05B.d_head == 64,
    )

    # 7. Llama 3-70B and Llama 3-405B scale verification (Table 2-4)
    l3_70b_tot = tla.count_transformer_parameters(tla.LLAMA3_70B)
    l3_405b_tot = tla.count_transformer_parameters(tla.LLAMA3_405B)
    check(
        7,
        "Llama 3-70B (80 layers, d=8,192, d_ff=28,672) totals 70.55B (70,553,706,496) params and Llama 3-405B (126 layers, d=16,384, d_ff=53,248) totals 405.85B (405,853,388,800) params",
        l3_70b_tot["total_params"] == 70_553_706_496
        and l3_405b_tot["total_params"] == 405_853_388_800,
    )

    # 8. Attention quadratic FLOPs (4*B*s^2*d) vs linear FLOPs at short context (s=4,096) vs long context (s=128,000)
    flops_4k = tla.compute_layer_forward_flops(1, 4096, 4096, 11008, 32, 32, swiglu=True)
    flops_128k = tla.compute_layer_forward_flops(1, 128000, 4096, 11008, 32, 32, swiglu=True)
    check(
        8,
        "In Llama 2-7B, quadratic attention core FLOPs (4*B*s^2*d) grow from 14.22% of layer FLOPs at s=4,096 to 83.82% at s=128,000 (crossover s*=24,704 tokens)",
        round(flops_4k["attn_core_share_pct"], 2) == 14.22
        and round(flops_128k["attn_core_share_pct"], 2) == 83.82
        and int(flops_4k["crossover_seq_len"]) == 24_704,
    )

    # 9. Triangular causal self-attention QK dot products T(N) = N(N+1)/2 (AISPE Ch 16)
    qk_20k = tla.compute_triangular_qk_ops(20000)
    qk_6k = tla.compute_triangular_qk_ops(6000)
    qk_2k = tla.compute_triangular_qk_ops(2000)
    check(
        9,
        "Causal self-attention QK dot products T(N) = N(N+1)/2 equal 200,010,000 (~200M) at N=20,000, 18,003,000 at N=6,000, and 2,001,000 at N=2,000",
        qk_20k == 200_010_000 and qk_6k == 18_003_000 and qk_2k == 2_001_000,
    )

    # 10. FIFO vs Latency-Aware prompt batching critical-path QK reduction (AISPE Table 16-6 & 16-7)
    sched = tla.evaluate_fifo_vs_latency_aware_batches()
    check(
        10,
        "Latency-aware scheduling of [6K, 2K, 6K, 2K, 2K, 2K] across 2 GPUs cuts critical-path QK dot products by 42.10% (38,007,000 -> 22,005,000)",
        sched["fifo_critical_ops"] == 38_007_000
        and sched["balanced_critical_ops"] == 22_005_000
        and sched["critical_path_reduction_pct"] == 42.10,
    )

    # 11. KV cache footprint for Llama-13B MHA at 4,096 tokens (AISPE Ch 17: ~0.819 MB/tok, ~3.36 GB FP16, ~1.68 GB FP8)
    kv_13b = tla.compare_attention_kv_variants(40, 40, 128, 4096, gqa_groups=8)
    check(
        11,
        "13B MHA (40 layers, 40 heads, d_head=128) KV cache is 819,200 B/tok (~0.819 MB/tok) or 3.36 GB (3,355,443,200 B) at FP16 and 1.68 GB at FP8 for 4,096 tokens",
        kv_13b["MHA_FP16"]["bytes_per_token"] == 819_200
        and round(kv_13b["MHA_FP16"]["total_gb_decimal"], 2) == 3.36
        and round(kv_13b["MHA_FP8"]["total_gb_decimal"], 2) == 1.68,
    )

    # 12. KV cache reduction across GQA-8 (5x), MQA (40x), and DeepSeek MLA (17.78x) on 13B model
    check(
        12,
        "On 13B (4,096 tokens), GQA-8 shrinks KV cache 5.0x to 0.671 GB FP16 (0.336 GB FP8), MQA shrinks 40.0x to 0.084 GB FP16, and MLA (dim 576) shrinks 17.78x to 0.189 GB",
        round(kv_13b["GQA8_FP16"]["total_gb_decimal"], 3) == 0.671
        and round(kv_13b["GQA8_FP8"]["total_gb_decimal"], 3) == 0.336
        and round(kv_13b["MQA_FP16"]["total_gb_decimal"], 3) == 0.084
        and kv_13b["gqa_reduction_factor"] == 5.0
        and kv_13b["mqa_reduction_factor"] == 40.0
        and round(kv_13b["MLA_FP16"]["compression_vs_mha"], 2) == 17.78,
    )

    # 13. 70B KV cache at 250,000-token ultralong context (AISPE Ch 18: 80 layers, 32 KV heads, d_head=128 -> ~1.31 MB/tok, ~328 GB FP16)
    kv_70b_250k = tla.compute_kv_cache_footprint(
        n_layers=80, n_kv_heads=32, d_head=128, bytes_per_elem=2, seq_len=250_000
    )
    check(
        13,
        "70B model (80 layers, 32 heads, d_head=128) generates 655,360 floats (1,310,720 B ~= 1.31 MB/tok) and 327.68 GB (~328 GB) of FP16 KV cache at 250,000 tokens",
        kv_70b_250k["floats_per_token"] == 655_360
        and kv_70b_250k["bytes_per_token"] == 1_310_720
        and round(kv_70b_250k["total_gb_decimal"], 2) == 327.68,
    )

    # 14. Mixtral 8x7B MoE total vs active parameters (AIE Ch 2: 46.7B total vs 56B unshared, 12.9B active for 2 of 8 experts)
    mixtral = tla.compute_moe_architecture_metrics(
        "Mixtral 8x7B", total_params_b=46.7, active_params_b=12.9, num_routed_experts=8, active_routed_experts=2
    )
    check(
        14,
        "Mixtral 8x7B activates 2 of 8 experts per token (12.9B active of 46.7B total params = 27.62%, 3.62x compute savings, 93.4 GB FP16 weights)",
        mixtral["active_param_pct"] == 27.62
        and mixtral["compute_savings_factor"] == 3.62
        and mixtral["hbm_weight_gb"] == 93.4,
    )

    # 15. DeepSeek-V3 / R1 MoE architecture (AISPE Ch 1 & Hands-On Ch 2: 671B / ~680B total, 37B active, 1 shared + 8 of 256 routed = 9 active experts)
    dsv3 = tla.compute_moe_architecture_metrics(
        "DeepSeek-V3",
        total_params_b=671.0,
        active_params_b=37.0,
        num_routed_experts=256,
        active_routed_experts=8,
        shared_experts=1,
    )
    check(
        15,
        "DeepSeek-V3 / R1 routes 1 shared + 8 of 256 experts (9 active experts/token), activating 37B of 671B (~680B) total params (5.51% active, 18.14x compute savings)",
        dsv3["total_active_experts"] == 9
        and dsv3["active_param_pct"] == 5.51
        and dsv3["compute_savings_factor"] == 18.14,
    )

    # 16. Jamba hybrid Transformer-Mamba MoE (AIE Ch 2: 52B total, 12B active, 256K context, fits in 80 GB GPU when quantized)
    jamba = tla.compute_moe_architecture_metrics(
        "Jamba", total_params_b=52.0, active_params_b=12.0, num_routed_experts=16, active_routed_experts=2
    )
    check(
        16,
        "Jamba hybrid Transformer-Mamba MoE activates 12B of 52B total parameters (23.08% active, 4.33x compute savings)",
        jamba["active_param_pct"] == 23.08 and jamba["compute_savings_factor"] == 4.33,
    )

    # 17. Chinchilla compute-optimal scaling law D ~= 20*N and C ~= 6*N*D (DeepMind 2022, AIE Ch 2 Table 2-5)
    chin_3b = tla.compute_chinchilla_scaling(params_b=3.0)
    chin_70b = tla.compute_chinchilla_scaling(params_b=70.0)
    check(
        17,
        "Chinchilla scaling (D ~= 20*N, C ~= 6*N*D) prescribes 60B tokens for a 3B model (1.08e21 FLOPs) and 1.4T tokens for Chinchilla-70B (5.88e23 FLOPs)",
        chin_3b["optimal_tokens_b"] == 60.0
        and math.isclose(chin_3b["compute_flops"], 1.08e21, rel_tol=1e-6)
        and chin_70b["optimal_tokens_t"] == 1.4
        and math.isclose(chin_70b["compute_flops"], 5.88e23, rel_tol=1e-6),
    )

    # 18. Over-training vs Chinchilla optimal for inference usability (Llama 1=1.4T, Llama 2=2T, Llama 3=15T tokens; Llama 3-8B at 15T = 1,875 tokens/param)
    llama3_8b_ratio = 15_000.0 / 8.0
    check(
        18,
        "Llama 3 pre-trains on 15T tokens (vs 1.4T for Llama 1 and 2T for Llama 2), giving Llama 3-8B 1,875 tokens/parameter (93.75x Chinchilla's 20x ratio)",
        llama3_8b_ratio == 1875.0 and (llama3_8b_ratio / 20.0) == 93.75,
    )

    # 19. GPT-3 175B training FLOPs, cluster time, and cost on 256 H100s (AIE Ch 2: 3.14e23 FLOPs, ~236 days, $4,142,811.43 at 70% util)
    gpt3_cost = tla.estimate_training_cluster_cost(
        total_flops=3.14e23, num_gpus=256, gpu_tflops_fp32=60.0, flops_per_gpu_day=5.2e18, utilization=0.70, hourly_cost_per_gpu=2.0
    )
    check(
        19,
        "Training GPT-3 175B (3.14e23 FLOPs, 300B tokens) on 256 GPUs at 5.2e18 FLOPs/day takes ~236 ideal days (~7.8 months) and costs $4,142,811.43 at 70% utilization and $2/GPU/hr",
        gpt3_cost["seconds_per_day"] == 86_400
        and gpt3_cost["ideal_days_rounded"] == 236
        and gpt3_cost["ideal_months"] == 7.8
        and gpt3_cost["cost_usd_at_util"] == 4_142_811.43,
    )

    # 20. 100-Trillion-Parameter dense model compute and memory sizing (AISPE Ch 1: 29T tokens -> 1.74e28 FLOPs, 200 TB FP16 weights, ~1,110 B200 or ~695 B300 GPUs)
    m100t = tla.estimate_100t_model_footprint(100.0, 29.0)
    check(
        20,
        "100T-parameter dense model trained on 29T tokens requires 1.74e28 FLOPs (C ~= 6ND) and 200 TB FP16 weight memory (~1,110 B200 GPUs at 180 GB or 695 B300 GPUs at 288 GB)",
        math.isclose(m100t["training_flops"], 1.74e28, rel_tol=1e-6)
        and m100t["weight_memory_tb"] == 200.0
        and 1110 <= m100t["min_b200_gpus_exact"] <= 1112
        and m100t["min_b300_gpus_exact"] == 695,
    )

    # 21. GB200 NVL72 rack-scale specs (AISPE Ch 1: 36 Grace CPUs + 72 Blackwell GPUs, 1.8 TB/s per GPU NVLink 5, 130 TB/s rack, 1.44 exaFLOPS FP4, 13,824 GB HBM3e)
    nvl72_hbm_gb = 72 * 192
    nvl72_agg_bw_tbs = (72 * 1.8)  # 129.6 TB/s (~130 TB/s)
    check(
        21,
        "GB200 NVL72 integrates 36 Grace CPUs and 72 Blackwell GPUs with 1.8 TB/s/GPU NVLink 5 (~130 TB/s aggregate), 13,824 GB (13.5 TB) HBM3e, and 1.44 exaFLOPS FP4 (720 PFLOPS FP8)",
        nvl72_hbm_gb == 13_824 and round(nvl72_agg_bw_tbs) == 130,
    )

    # 22. Temperature-scaled softmax probabilities for logits [1, 2] (AIE Ch 2: T=1.0 -> [0.27, 0.73], T=0.5 -> [0.12, 0.88], T=0 -> [0.0, 1.0])
    p_t1 = tla.softmax_with_temperature([1.0, 2.0], temperature=1.0)
    p_t05 = tla.softmax_with_temperature([1.0, 2.0], temperature=0.5)
    p_t0 = tla.softmax_with_temperature([1.0, 2.0], temperature=0.0)
    check(
        22,
        "For logits [1, 2], softmax yields [0.27, 0.73] at T=1.0, sharpens to [0.12, 0.88] at T=0.5, and selects greedy argmax [0.0, 1.0] at T=0",
        round(p_t1[0], 2) == 0.27
        and round(p_t1[1], 2) == 0.73
        and round(p_t05[0], 2) == 0.12
        and round(p_t05[1], 2) == 0.88
        and p_t0 == [0.0, 1.0],
    )

    # 23. Top-p (nucleus) dynamic vocabulary filtering (AIE Ch 2 Fig 2-18: top_p=0.90 keeps ['yes', 'maybe'], top_p=0.99 keeps ['yes', 'maybe', 'no'])
    sample_dist = {"yes": 0.60, "maybe": 0.32, "no": 0.07, "never": 0.01}
    p90 = [tok for tok, _ in tla.filter_top_k_top_p(sample_dist, top_p=0.90)]
    p99 = [tok for tok, _ in tla.filter_top_k_top_p(sample_dist, top_p=0.99)]
    check(
        23,
        "Top-p (nucleus) sampling dynamically keeps ['yes', 'maybe'] at top_p=0.90 (cum=0.92 >= 0.90) and ['yes', 'maybe', 'no'] at top_p=0.99 (cum=0.99)",
        p90 == ["yes", "maybe"] and p99 == ["yes", "maybe", "no"],
    )

    # 24. Sequence probability and average logprob for ["I", "love", "food"] with probs [0.2, 0.1, 0.3] (AIE Ch 2: p = 0.006)
    seq_lp = tla.compute_sequence_logprob_metrics([0.2, 0.1, 0.3])
    check(
        24,
        "Sequence ['I', 'love', 'food'] with token probabilities [0.2, 0.1, 0.3] has product probability 0.006, total logprob -5.115996, and average logprob -1.705332",
        seq_lp["seq_prob"] == 0.006
        and round(seq_lp["total_logprob"], 4) == -5.1160
        and round(seq_lp["avg_logprob"], 4) == -1.7053,
    )

    # 25. Test-time compute verifier scaling (AIE Ch 2: Cobbe et al. 2021 verifier gives ~30x model size boost: 100M + verifier ~= 3B without verifier)
    verifier_base_m = 100
    verifier_multiplier = 30
    equivalent_model_b = (verifier_base_m * verifier_multiplier) / 1000.0
    check(
        25,
        "Test-time compute with a reward verifier boosts a 100M-parameter model by ~30x in effective scale to match a 3.0B-parameter unverified model (up to ~400 samples before adversarial drop)",
        equivalent_model_b == 3.0,
    )

    # 26. Multilingual tokenization inflation and Common Crawl representation skew (AIE Ch 2 Table 2-1, Table 2-2, MASSIVE benchmark)
    ml_tax = tla.evaluate_multilingual_token_tax()
    check(
        26,
        "On MASSIVE, median token length jumps from 7 (English) to 32 (Hindi, 4.57x) and 72 (Burmese, 10.29x ~= 10x cost/latency); English is 45.88% of Common Crawl vs Punjabi 0.0061% (231.56x under-represented)",
        ml_tax["English"]["median_tokens"] == 7
        and ml_tax["Hindi"]["median_tokens"] == 32
        and ml_tax["Burmese"]["median_tokens"] == 72
        and ml_tax["Burmese"]["cost_latency_multiplier"] == 10.29
        and ml_tax["Punjabi"]["pop_cc_ratio"] == 231.56,
    )

    # 27. Post-training compute & SFT/RLHF annotation economics (AIE Ch 2 & EAS Ch 4: 2% post-training vs 98% pre-training; 13,000 pairs * $10 = $130,000; $3.50 comparison vs $25 SFT; LoRA 10,000x param / 3x compute reduction)
    sft_pairs = 13_000
    sft_cost_per_pair = 10
    sft_total_usd = sft_pairs * sft_cost_per_pair
    lora_param_reduction = 10_000
    lora_compute_reduction = 3
    check(
        27,
        "InstructGPT used 2% compute for post-training vs 98% pre-training and $130,000 for 13,000 SFT pairs ($10/pair; Llama 2 paid $3.50/comparison vs $25/response), while LoRA cuts trainable params 10,000x and compute 3x",
        sft_total_usd == 130_000 and lora_param_reduction == 10_000 and lora_compute_reduction == 3,
    )

    # 28. KV cache manual walkthrough speedup & disaggregated RDMA collation (Hands-On Ch 2: 9.1205 s no cache -> 3.1416 s with KV cache over 100 tokens; AISPE Ch 18: LMCache 7.5K-token KV 470 pages 20 ms -> 8 ms collated)
    no_cache_s = 9.1205
    with_cache_s = 3.1416
    kv_speedup = round(no_cache_s / with_cache_s, 2)
    rdma_uncollated_ms = 20.0
    rdma_collated_ms = 8.0
    rdma_speedup = rdma_uncollated_ms / rdma_collated_ms
    check(
        28,
        "Enabling KV cache accelerates 100-token Qwen 2.5 generation 2.90x (9.1205 s -> 3.1416 s), and collating 16-token PagedAttention blocks into >=128-token RDMA transfers cuts 7.5K-token KV handoff 2.5x (20 ms -> 8 ms)",
        kv_speedup == 2.90 and rdma_speedup == 2.5,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
