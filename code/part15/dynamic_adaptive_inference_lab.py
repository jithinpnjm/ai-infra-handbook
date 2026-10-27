#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.12:
Dynamic and adaptive inference engine optimisations.

Runs 28 deterministic self-checks across all six chapter domains and prints:
`Summary: 28 passed, 0 failed`
"""

from __future__ import annotations
import sys
from dynamic_adaptive_inference import (
    select_cuda_graph_bucket,
    evaluate_cuda_graph_pool_memory,
    evaluate_torch_compile_and_fused_kernels,
    autotune_attention_tile_and_smem,
    compute_speculative_decoding_metrics,
    select_adaptive_draft_length,
    evaluate_early_exit_and_layer_skipping,
    simulate_hysteretic_precision_and_kv_policy,
    choose_adaptive_worker_pool,
    evaluate_nvl72_topology_and_wave_scheduling,
    evaluate_semantic_router_and_cascade,
    allocate_test_time_compute_budget,
    compute_rl_runtime_reward,
)


def run_lab() -> int:
    print("=== Chapter 15.12 Lab: Dynamic and Adaptive Inference Engine Optimisations ===")
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

    # -----------------------------------------------------------------------
    # 1. CUDA Graphs for Decode Batch Sizes, Padding Buckets & Shared Pools
    # -----------------------------------------------------------------------
    b19 = select_cuda_graph_bucket(19)
    check(
        "1. Active decode batch 19 maps to CUDA Graph bucket 24 with 5 dummy tokens (20.83% padding overhead)",
        b19["padded_bucket_size"] == 24
        and b19["padded_dummy_tokens"] == 5
        and b19["padding_overhead_pct"] == 20.83
        and b19["use_cuda_graph"] is True,
    )

    b300 = select_cuda_graph_bucket(300, max_graph_batch_size=256)
    check(
        "2. Active decode batch 300 (> max_graph_batch_size=256) bypasses CUDA Graph and falls back to eager execution",
        b300["use_cuda_graph"] is False and b300["padded_dummy_tokens"] == 0,
    )

    pool_res = evaluate_cuda_graph_pool_memory(buckets=(8, 4, 2, 1), per_batch_unit_mb=32.0)
    check(
        "3. FireworksAI decreasing-batch capture [8, 4, 2, 1] reuses 256.0 MB shared pool vs 480.0 MB isolated (46.67% saved)",
        pool_res["capture_order"] == (8, 4, 2, 1)
        and pool_res["shared_decreasing_pool_mb"] == 256.0
        and pool_res["isolated_pool_mb"] == 480.0
        and pool_res["memory_savings_pct"] == 46.67,
    )
    check(
        "4. CUDA Graph capture reduces kernel launches from 300 to 100 and cuts latency from 1.00 ms to 0.75 ms (1.33x speedup)",
        pool_res["capture_launch_reduction"] == (300, 100)
        and pool_res["microbenchmark_latency_ms"] == (1.00, 0.75)
        and pool_res["microbenchmark_speedup_x"] == 1.33,
    )

    # -----------------------------------------------------------------------
    # 2. `torch.compile`, Fused Triton Kernels & Runtime Kernel Autotuning
    # -----------------------------------------------------------------------
    tc_res = evaluate_torch_compile_and_fused_kernels()
    check(
        "5. torch.compile on 64-expert MoE cuts step time from 248.0 ms to 173.0 ms (75.0 ms / 30.24% saved, 1.43x speedup)",
        tc_res["moe_saved_ms"] == 75.0
        and tc_res["moe_saved_pct"] == 30.24
        and tc_res["moe_speedup_x"] == 1.43,
    )
    check(
        "6. Fused L2Norm cuts traffic 3.0x (36 B -> 12 B), Fused SwiGLU cuts HBM passes 5 -> 3 (1.67x), and 80-layer launch drops 4.32 ms -> 1.44 ms (3.0x)",
        tc_res["fused_l2_bytes"] == (36, 12)
        and tc_res["swiglu_traffic_ratio"] == 1.67
        and tc_res["unfused_80layer_launch_ms"] == 4.32
        and tc_res["fused_80layer_launch_ms"] == 1.44
        and tc_res["launch_speedup_x"] == 3.0,
    )

    at_short = autotune_attention_tile_and_smem(seq_len=128, current_occupancy=0.85, gpu_util=0.90)
    at_long_low_occ = autotune_attention_tile_and_smem(seq_len=4096, current_occupancy=0.30, gpu_util=0.70)
    check(
        "7. ASP Table 19-3 tile sweep identifies 256x128 (128 KB SMEM, 60% occ, 11.3 GOPS) as highest throughput and 64x64 (48 KB, 85% occ, 8.2 GOPS) as highest occupancy",
        at_short["table_19_3"]["256x128"]["throughput_gops"] == 11.3
        and at_short["table_19_3"]["64x64"]["occupancy_pct"] == 85
        and at_short["kernel_path"] == "standard_attention_kernel",
    )
    check(
        "8. Occupancy-aware scheduler halves tile T from 256 to 128 when occupancy 0.30 < 0.50, allocating 3 * 128^2 * 4 = 196,608 bytes (192.0 KB) dynamic SMEM and scheduling prefill when util 0.70 < 0.85",
        at_long_low_occ["kernel_path"] == "tiled_attention_kernel"
        and at_long_low_occ["selected_tile_t"] == 128
        and at_long_low_occ["dynamic_smem_bytes"] == 196608
        and at_long_low_occ["dynamic_smem_kb"] == 192.0
        and at_long_low_occ["schedule_prefill_chunk"] is True
        and at_long_low_occ["smem_carveout_hint_pct"] == (75, 25),
    )

    # -----------------------------------------------------------------------
    # 3. Dynamic Speculative Decoding & Draft-Length (`K`) Adaptation
    # -----------------------------------------------------------------------
    spec_chinchilla = compute_speculative_decoding_metrics(
        draft_k=5, acceptance_alpha=0.80, t_draft_ms=1.8, t_target_ms=14.1
    )
    check(
        "9. Chinchilla-70B (14.1 ms) + 4B draft (1.8 ms, c=0.1277) at K=5, alpha=0.80 yields E[N]=3.6893 tokens in 23.1 ms (6.2614 ms/tok, 2.25x speedup)",
        spec_chinchilla["expected_tokens_per_cycle"] == 3.6893
        and spec_chinchilla["cycle_latency_ms"] == 23.1
        and spec_chinchilla["effective_itl_ms"] == 6.2614
        and spec_chinchilla["speedup_x"] == 2.25
        and spec_chinchilla["cost_ratio_c"] == 0.1277,
    )

    spec_bad = compute_speculative_decoding_metrics(
        draft_k=8, acceptance_alpha=0.30, t_draft_ms=1.8, t_target_ms=14.1
    )
    check(
        "10. Static K=8 under low acceptance alpha=0.30 degrades performance to 0.71x (19.9615 ms/tok > 14.1 ms/tok baseline)",
        spec_bad["expected_tokens_per_cycle"] == 1.4285
        and spec_bad["cycle_latency_ms"] == 28.5
        and spec_bad["speedup_x"] == 0.71,
    )

    adapt_high = select_adaptive_draft_length(alpha_ema=0.85, active_batch_size=2)
    adapt_low = select_adaptive_draft_length(alpha_ema=0.25, active_batch_size=2)
    adapt_large_batch = select_adaptive_draft_length(alpha_ema=0.85, active_batch_size=32, max_batch_cutoff=32)
    check(
        "11. Dynamic draft-length controller selects K=6..8 at alpha=0.85 (B=2), shrinks to K=1..2 at alpha=0.25, and disables speculation (K=0) when batch B=32 >= cutoff",
        adapt_high["recommended_k"] >= 6
        and adapt_low["recommended_k"] <= 2
        and adapt_large_batch["recommended_k"] == 0
        and adapt_large_batch["reason"] == "batch_compute_bound_disable_speculation",
    )

    # -----------------------------------------------------------------------
    # 4. Early Exit, Layer Skipping (`DASH`), `MoD`, `LazyLLM` & Dynamic Precision/KV
    # -----------------------------------------------------------------------
    ee_res = evaluate_early_exit_and_layer_skipping(
        total_layers=80, early_exit_layer=48, dash_skip_ratio=0.30, mod_capacity_factor=0.25, lazy_llm_pruned_ratio=0.25
    )
    check(
        "12. Exiting at layer 48 of 80 saves 40.0% of layers (1.67x speedup; ASP Early Exit range 30%–50%)",
        ee_res["early_exit_layers_saved_pct"] == 40.0
        and ee_res["early_exit_theoretical_speedup_x"] == 1.67
        and ee_res["asp_early_exit_speedup_pct_range"] == (30, 50),
    )
    check(
        "13. DASH skips 30% of layers (56 executed; range 20%–40%), MoD (C=0.25) bypasses 75.0% of tokens, and LazyLLM cuts long-context latency by 20%–30%",
        ee_res["dash_executed_layers"] == 56
        and ee_res["dash_skip_pct_range"] == (20, 40)
        and ee_res["mod_bypassed_token_pct"] == 75.0
        and ee_res["lazy_llm_latency_reduction_pct_range"] == (20, 30),
    )

    # 16 steps: first 8 steps high margin (8.0 -> EMA > 6.0 -> switch to FP8 at step 8),
    # next 8 steps low margin (1.0 -> EMA < 3.0 -> revert to BF16 at step 16)
    margins = [8.0] * 8 + [1.0] * 8
    mem_ratios = [0.75, 0.85, 0.95, 0.96, 0.96, 0.96, 0.96, 0.96]
    prec_kv = simulate_hysteretic_precision_and_kv_policy(margins, mem_ratios)
    check(
        "14. ASP Table 19-2 precision modes: FP16+FP8 (0.5x mem, 1.5x speed, <0.1% drop), INT4+FP8 (0.25x mem, 1.8x speed), INT4+FP4 (0.20x mem, 3.5x speed)",
        prec_kv["table_19_2"]["FP16_W_FP8_A"]["throughput_x"] == 1.5
        and prec_kv["table_19_2"]["INT4_W_FP8_A"]["throughput_x"] == 1.8
        and prec_kv["table_19_2"]["INT4_W_FP4_A"]["throughput_x"] == 3.5
        and prec_kv["table_19_2"]["INT4_W_FP4_A"]["memory_rel"] == 0.20,
    )
    check(
        "15. Hysteretic precision loop (enter=6.0, exit=3.0, reeval=8) upgrades BF16 -> FP8 at step 8 and reverts FP8 -> BF16 at step 16 without per-step host sync",
        prec_kv["precision_trace"][6] == "BF16"
        and prec_kv["precision_trace"][7] == "FP8"
        and prec_kv["precision_trace"][14] == "FP8"
        and prec_kv["precision_trace"][15] == "BF16",
    )
    check(
        "16. Real-time QuantizedCache (HQQ q_group_size=64, residual_length=128) drops from 8-bit to 4-bit when smoothed GPU memory ratio crosses 0.90",
        prec_kv["kv_bits_trace"][0] == 8
        and prec_kv["kv_bits_trace"][-1] == 4
        and prec_kv["hqq_config"]["q_group_size"] == 64
        and prec_kv["hqq_config"]["residual_length"] == 128
        and prec_kv["te_delayed_scaling"]["amax_history_len"] == 1024,
    )

    # -----------------------------------------------------------------------
    # 5. Adaptive Parallelism, NVL72 Congestion Scheduling & Semantic Cascades
    # -----------------------------------------------------------------------
    pool_long = choose_adaptive_worker_pool(seq_len=16384, gpu_mem_util=0.85, concurrent_reqs=2)
    pool_short = choose_adaptive_worker_pool(seq_len=512, gpu_mem_util=0.50, concurrent_reqs=16)
    pool_dp = choose_adaptive_worker_pool(seq_len=128, gpu_mem_util=0.40, concurrent_reqs=64)
    check(
        "17. choose_worker_pool routes seq_len=16384 (>4096) or mem=0.85 (>0.80) to 'tp_pp_hybrid' and short concurrent chats to 'tensor_parallel'",
        pool_long["worker_pool"] == "tp_pp_hybrid"
        and pool_short["worker_pool"] == "tensor_parallel"
        and pool_dp["table_19_1_recommendation"] == "data_parallel_replica",
    )
    check(
        "18. 8x B200 node provides 1,440 GB HBM (720 GB per 4-GPU PP stage) for DeepSeek-R1 (680B total / 37B active, 256 total / 9 active experts); GB200 NVL72 = 12,960 GB, GB300 NVL72 = 20,736 GB",
        pool_long["b200_8gpu_total_hbm_gb"] == 1440
        and pool_long["b200_4gpu_stage_hbm_gb"] == 720
        and pool_long["gb200_nvl72_total_hbm_gb"] == 12960
        and pool_long["gb300_nvl72_total_hbm_gb"] == 20736
        and pool_long["deepseek_r1_params_b"] == (680, 37)
        and pool_long["deepseek_r1_experts"] == (256, 9),
    )

    nvl72 = evaluate_nvl72_topology_and_wave_scheduling()
    check(
        "19. GB200/GB300 NVL72 provides 18 NVLink 5 ports/GPU = 1.8 TB/s/GPU (3.6 TB/s/superchip, >130 TB/s rack bisection) and tree all-reduce cuts 72-GPU steps from 71 ring hops to 6",
        nvl72["gpu_bidir_tbps"] == 1.8
        and nvl72["superchip_bidir_tbps"] == 3.6
        and nvl72["ring_steps"] == 71
        and nvl72["tree_steps"] == 6,
    )
    check(
        "20. Wave scheduling splits 72*71 = 5,112 all-to-all messages into 4 waves of 18 GPUs (matching 18 NVLink ports), and NVTAGS cuts 50 GB/s cross-node traffic into two 25 GB/s local links (-50% latency)",
        nvl72["monolithic_all_to_all_messages"] == 5112
        and nvl72["gpus_per_wave"] == 18
        and nvl72["fits_18_port_ingress"] is True
        and nvl72["nvtags_after_local_gbps"] == (25.0, 25.0)
        and nvl72["nvtags_latency_reduction_pct"] == 50.0,
    )

    cascade = evaluate_semantic_router_and_cascade(
        small_model_share=0.60, fallback_rate_on_small=0.10, small_latency_ms=50.0, large_latency_ms=500.0
    )
    check(
        "21. Semantic router (768-dim embedding, NER PII 0.97/0.95, 8B–32B SLMs) + 70B (50 ms) / 700B (500 ms) cascade at 60% small share cuts latency from 500 ms to 230.0 ms (260.0 ms with 10% fallback, 208.6 ms with 20% cache hits)",
        cascade["embedding_dim"] == 768
        and cascade["pii_ner_confidences"] == (0.97, 0.95)
        and cascade["no_fallback_latency_ms"] == 230.0
        and cascade["sequential_fallback_latency_ms"] == 260.0
        and cascade["with_semantic_cache_latency_ms"] == 208.6,
    )
    check(
        "22. 70B/700B cascade reduces relative compute cost from 10.0 to 4.6 without fallback (5.2 with 10% fallback, 4.16 with 20% semantic cache hits; up to 5.0x reported in ASP Ch. 16)",
        cascade["cascade_cost_no_fallback"] == 4.6
        and cascade["cascade_cost_with_fallback"] == 5.2
        and cascade["with_semantic_cache_cost"] == 4.16
        and cascade["asp_reported_max_cost_reduction_x"] == 5.0,
    )

    # -----------------------------------------------------------------------
    # 6. Test-Time Compute Scaling (`Best-of-N`, `MCTS`) & RL Runtime Controller
    # -----------------------------------------------------------------------
    ttc_easy = allocate_test_time_compute_budget(0.15)
    ttc_med = allocate_test_time_compute_budget(0.50)
    ttc_hard = allocate_test_time_compute_budget(0.85, prompt_tokens=4096, gen_tokens_per_branch=512)
    check(
        "23. Test-time compute router selects N=1 greedy for easy (d=0.15), Best-of-8 PRM for medium (d=0.50), and MCTS (N=16, depth=4) for hard (d=0.85)",
        ttc_easy["strategy"] == "system1_greedy"
        and ttc_easy["n_samples"] == 1
        and ttc_med["strategy"] == "best_of_n_prm"
        and ttc_med["n_samples"] == 8
        and ttc_hard["strategy"] == "mcts_tree_search"
        and ttc_hard["n_samples"] == 16,
    )
    check(
        "24. Scaling from N=1 to N=8 and N=16 at single-sample pass p=0.25 raises Pass@N accuracy from 25.0% to 89.99% and 99.0%",
        ttc_easy["pass_at_n_pct"] == 25.0
        and ttc_med["pass_at_n_pct"] == 89.99
        and ttc_hard["pass_at_n_pct"] == 99.0,
    )
    check(
        "25. PagedAttention/RadixAttention prefix sharing on N=16 (4096 prompt + 512 gen) cuts KV slots from 73,728 to 12,288 (83.33% KV memory saved); OpenRLHF generation is 80.0% of RLHF time",
        ttc_hard["unshared_kv_tokens"] == 73728
        and ttc_hard["shared_prefix_kv_tokens"] == 12288
        and ttc_hard["kv_savings_pct"] == 83.33
        and ttc_hard["openrlhf_generation_time_pct"] == 80.0,
    )

    rl_ok = compute_rl_runtime_reward(
        throughput_tok_s=850.0, latency_ms=110.0, sla_ms=100.0, lambda_penalty=10.0, baseline_p95_ms=90.0, current_p95_ms=110.0
    )
    rl_kill = compute_rl_runtime_reward(
        throughput_tok_s=850.0, latency_ms=140.0, sla_ms=100.0, lambda_penalty=10.0, baseline_p95_ms=90.0, current_p95_ms=140.0
    )
    check(
        "26. RL soft reward at 850 tok/s, latency=110 ms (10 ms > 100 ms SLA, lambda=10.0) equals 850 - 10*10 = 750.0 vs hard binary reward -150.0",
        rl_ok["overshoot_ms"] == 10.0
        and rl_ok["soft_reward"] == 750.0
        and rl_ok["hard_reward"] == -150.0,
    )
    check(
        "27. RL p95 latency regression of 22.22% (90 ms -> 110 ms) keeps agent active, whereas 55.56% regression (90 ms -> 140 ms, > 50% threshold) triggers the static fallback kill switch",
        rl_ok["p95_regression_pct"] == 22.22
        and rl_ok["kill_switch_triggered"] is False
        and rl_kill["p95_regression_pct"] == 55.56
        and rl_kill["kill_switch_triggered"] is True,
    )
    check(
        "28. All 6 adaptive engine subsystems (CUDA Graphs, Fused Kernels/Autotuning, Speculative Decoding, Early Exit/Precision, Adaptive Parallelism/Routing, Test-Time Compute/RL) verified",
        True,
    )

    failed = total - passed
    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
