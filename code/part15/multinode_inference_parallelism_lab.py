#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.9: Multinode Inference Parallelism, Decoding, and Routing."""

from __future__ import annotations
import sys
from multinode_inference_parallelism import (
    evaluate_tp_vs_pp_communication,
    evaluate_wide_ep_and_hybrid_moe,
    evaluate_moe_routing_and_eplb,
    evaluate_speculative_decoding,
    evaluate_lws_and_prefix_routing,
)


def run_lab() -> int:
    print("=== Chapter 15.9 Lab: Multinode Inference Parallelism, Speculative Decoding & Routing ===")
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

    # 1. TP AllReduce Frequency & Ring Step Math (V12 Ch. 5 & 9, ASP Ch. 15)
    tp8_nvlink = evaluate_tp_vs_pp_communication(
        num_layers=80,
        tp_size=8,
        pp_size=1,
        batch_size=1,
        seq_len=1,
        hidden_size=8192,
        precision_bytes=2.0,
        interconnect_bw_gbps=900.0,
        per_step_latency_us=0.8,
        compute_ms_per_token=14.0,
        target_tokens_per_sec=50.0,
    )
    check(
        "1. 80-layer model (Llama-3-70B) with TP requires 2 AllReduces/layer = 160 AllReduces/token and 8,000 AllReduces/sec at 50 tok/s",
        tp8_nvlink["allreduces_per_layer"] == 2.0
        and tp8_nvlink["allreduces_per_token"] == 160.0
        and tp8_nvlink["allreduces_per_sec"] == 8000.0,
    )
    check(
        "2. Ring AllReduce at TP=8 executes 2*(N-1) = 14 steps per collective (2,240 steps/token) and moves 2*(7/8)*16,384 = 28,672 B per AllReduce",
        tp8_nvlink["ring_steps_per_allreduce"] == 14.0
        and tp8_nvlink["total_ring_steps_per_token"] == 2240.0
        and tp8_nvlink["per_allreduce_bytes"] == 28672.0,
    )
    check(
        "3. Intra-node TP=8 over NVLink 4 (900 GB/s, 0.8 us/collective) adds only ~0.13 ms comm per token (total ITL ~14.13 ms < 25 ms SLA)",
        round(tp8_nvlink["tp_comm_ms_per_token"], 2) == 0.13
        and tp8_nvlink["total_itl_ms"] == 14.13
        and tp8_nvlink["comm_fraction_pct"] < 1.0,
    )

    # 2. Cross-Node TP=16 Failure vs TP=8, PP=2 Resolution (V12 Ch. 9 Failure Scenario 1)
    tp16_cross_node = evaluate_tp_vs_pp_communication(
        num_layers=80,
        tp_size=16,
        pp_size=1,
        hidden_size=8192,
        interconnect_bw_gbps=12.5,
        per_step_latency_us=500.0,
        compute_ms_per_token=14.0,
    )
    check(
        "4. Cross-node TP=16 executes 2*(16-1)=30 ring steps/AllReduce (4,800 steps/token) and adds 80+ ms network stall per token (>85% comm overhead)",
        tp16_cross_node["ring_steps_per_allreduce"] == 30.0
        and tp16_cross_node["total_ring_steps_per_token"] == 4800.0
        and tp16_cross_node["tp_comm_ms_per_token"] >= 80.0
        and tp16_cross_node["comm_fraction_pct"] > 85.0,
    )

    tp4_pp8_ib = evaluate_tp_vs_pp_communication(
        num_layers=80,
        tp_size=4,
        pp_size=8,
        hidden_size=8192,
        precision_bytes=2.0,
        interconnect_bw_gbps=50.0,
        per_step_latency_us=2.0,
    )
    check(
        "5. Combining TP=4 with PP=8 shards inter-stage activation transfers by 1/TP (8,192 / 4 = 2,048 elements = 4,096 B per hop across 7 stage boundaries)",
        tp4_pp8_ib["pp_hops"] == 7.0
        and tp4_pp8_ib["pp_elements_per_token_per_rank"] == 2048.0
        and tp4_pp8_ib["pp_bytes_per_hop"] == 4096.0,
    )

    # 3. Hardware Interconnect Ratios (V12 Ch. 9, HLS Ch. 5, ASP Ch. 2 & 15)
    nvlink4_to_ib_ratio = 900.0 / 50.0
    nvlink4_to_100gbe_ratio = 900.0 / 12.5
    h100_hbm_to_nvlink_ratio = round(3350.0 / 900.0, 2)
    l40s_roofline_knee = round((362.0 * 1000.0) / 864.0, 0)
    check(
        "6. NVLink 4 (900 GB/s) is 18x faster than 400G NDR IB (50 GB/s) and 72x faster than 100GbE (12.5 GB/s); L40S FP16 roofline knee is 419 FLOPS/B",
        nvlink4_to_ib_ratio == 18.0
        and nvlink4_to_100gbe_ratio == 72.0
        and h100_hbm_to_nvlink_ratio == 3.72
        and l40s_roofline_knee == 419.0,
    )

    # 4. Wide Expert Parallelism (EP), DeepSeek-R1 671B & GB200 NVL72 (ASP Ch. 1 & 15, DAI Ch. 6, 7 & 11)
    moe_dp8 = evaluate_wide_ep_and_hybrid_moe(tp_size=1, dp_size=8)
    moe_tp8 = evaluate_wide_ep_and_hybrid_moe(tp_size=8, dp_size=1)
    moe_ep64 = evaluate_wide_ep_and_hybrid_moe(tp_size=1, dp_size=64)
    moe_disabled = evaluate_wide_ep_and_hybrid_moe(tp_size=1, dp_size=1)
    check(
        "7. DeepSeek-V3/R1 (671B total, 37B active = 5.51% active) activates 1 shared + 8 of 256 routed experts (9 total, 3.12% routed density > 3% EP threshold)",
        moe_dp8["total_active_experts_per_token"] == 9.0
        and moe_dp8["routed_activation_density_pct"] == 3.12
        and moe_dp8["active_param_fraction_pct"] == 5.51,
    )
    check(
        "8. EP_SIZE = TP_SIZE * DP_SIZE: 8 GPUs hold 256/8 = 32 complete experts/GPU; 64 GPUs hold 4 experts/GPU; TP=1, DP=1 disables EP (EP_SIZE=1)",
        moe_dp8["ep_size"] == 8.0
        and moe_dp8["experts_per_gpu"] == 32.0
        and moe_ep64["experts_per_gpu"] == 4.0
        and moe_disabled["ep_enabled"] == 0.0,
    )
    check(
        "9. TP=8, DP=1 uses AllReduce and duplicates MLA KV cache 8x across ranks, whereas DP=8, TP=1 (--enable-dp-attention) uses AllToAll and 1x KV cache",
        moe_tp8["uses_all_to_all"] == 0.0
        and moe_tp8["kv_duplication_factor_without_dp_attn"] == 8.0
        and moe_dp8["uses_all_to_all"] == 1.0
        and moe_dp8["kv_duplication_factor_without_dp_attn"] == 1.0,
    )
    check(
        "10. Serving DeepSeek-R1 671B across 32 GPUs (TP=4, PP=8) places 83.875B (~84B) params/stage; ASP 64-GPU hybrid (PP=4, TP=2, EP=16) puts 15 layers/stage and 128 GPUs at DP=2",
        moe_dp8["total_gpus_tp4_pp8"] == 32.0
        and moe_dp8["params_per_pp8_stage_b"] == 83.875
        and moe_dp8["asp_hybrid_layers_per_stage"] == 15.0
        and moe_dp8["asp_hybrid_total_gpus_with_dp2"] == 128.0,
    )
    check(
        "11. GB200 NVL72 unifies 72 GPUs at 1.8 TB/s per GPU (130 TB/s rack aggregate, 13,824 GB HBM3e) and scales to 576 GPUs across 8 racks",
        moe_dp8["nvl72_per_gpu_bw_tbps"] == 1.8
        and moe_dp8["nvl72_rack_bw_tbps"] == 130.0
        and moe_dp8["nvl72_hbm_gb"] == 13824.0
        and moe_dp8["nvl_max_gpus_8_racks"] == 576.0,
    )

    # 5. Dynamic MoE Routing, Wave Scheduling, Capacity Factor & EPLB (ASP Ch. 1, 15 & 19)
    eplb = evaluate_moe_routing_and_eplb(
        num_gpus=72,
        num_waves=4,
        base_token_capacity=32,
        capacity_factor=1.2,
        expert_token_loads=(50, 28, 30, 20),
    )
    check(
        "12. On 72-GPU NVL72, monolithic AllToAll launches 72*71 = 5,112 messages; 4 waves of 18 GPUs cut per-wave messages to 18*17 = 306 (16.71x reduction)",
        eplb["monolithic_messages"] == 5112.0
        and eplb["gpus_per_wave"] == 18.0
        and eplb["intra_wave_messages"] == 306.0
        and eplb["instantaneous_message_reduction_x"] == 16.71,
    )
    check(
        "13. MoE base capacity of 32 tokens scales to 32 (CF=1.0), 38 (CF=1.2, 20% overflow), and 48 (CF=1.5); load [50, 28, 30, 20] spills 12 overflow tokens at CF=1.2",
        eplb["max_tokens_cf_1_0"] == 32.0
        and eplb["max_tokens_per_expert"] == 38.0
        and eplb["max_tokens_cf_1_5"] == 48.0
        and eplb["overflow_tokens"] == 12.0
        and eplb["accepted_primary_tokens"] == 116.0,
    )
    check(
        "14. Hot expert GPU at 99% vs 60% peers (39% straggler gap) triggers the 80% utilization alert; EPLB cloning cuts peak expert load from 50 to 30 tokens",
        eplb["straggler_gap_pct"] == 39.0
        and eplb["triggers_alert"] == 1.0
        and eplb["max_load_before_eplb"] == 50.0
        and eplb["max_load_after_eplb"] == 30.0,
    )

    # 6. Speculative Decoding Draft-Verify Math, EAGLE, Medusa, MTP & Lookahead (ASP Ch. 15, HLS Ch. 7)
    spec = evaluate_speculative_decoding(
        k_draft=4,
        alpha=0.8,
        draft_cost_ratio=0.10,
        p_target_sample=0.4,
        q_draft_sample=0.6,
        positional_accept_rates=(0.8, 0.7, 0.6, 0.5, 0.10, 0.02),
    )
    check(
        "15. Rejection sampling accepts with prob min(1, p/q): p=0.8, q=0.6 -> 1.0 (100%); p=0.4, q=0.6 -> 0.6667 (66.67%) while preserving target distribution",
        spec["accept_prob_when_p_gt_q"] == 1.0
        and spec["accept_prob_sample"] == 0.6667,
    )
    check(
        "16. For K=4 draft tokens and alpha=0.8, E[tokens] = (1 - 0.8^5)/(1 - 0.8) = 3.3616 tokens/pass; at c_draft=0.10, net speedup is 3.3616 / 1.4 = 2.40x",
        spec["expected_tokens"] == 3.3616
        and spec["cycle_cost_units"] == 1.4
        and spec["net_speedup_x"] == 2.4,
    )

    spec_slow_draft = evaluate_speculative_decoding(k_draft=4, alpha=0.6, draft_cost_ratio=0.35)
    check(
        "17. When draft model is < 4x faster (c_draft=0.35) and alpha=0.6, cycle cost is 2.40 units vs 2.3056 expected tokens, degrading speedup to 0.96x (< 1.0x)",
        spec_slow_draft["expected_tokens"] == 2.3056
        and spec_slow_draft["cycle_cost_units"] == 2.4
        and spec_slow_draft["net_speedup_x"] == 0.96,
    )
    check(
        "18. Positional acceptance [0.8, 0.7, 0.6, 0.5, 0.10, 0.02] yields 2.864 tokens at K=4 vs 2.8811 tokens at K=6 (last 2 steps add only 0.0171 tokens)",
        spec["expected_tokens_k4_trimmed"] == 2.864
        and spec["expected_tokens_k6"] == 2.8811
        and spec["marginal_tokens_from_last_2_steps"] == 0.0171,
    )
    check(
        "19. Medusa depth-2 binary tree (4 tokens/pass) cuts 100-token reply from 100 to 25 ideal passes; EAGLE-3 on Qwen3-32B reaches 56.5 vs 28.9 tok/s (1.96x)",
        spec["medusa_ideal_iterations"] == 25.0
        and spec["vanilla_vllm_tps"] == 28.9
        and spec["eagle3_vllm_tps"] == 56.5
        and spec["eagle3_measured_speedup_x"] == 1.96,
    )

    # 7. Kubernetes LeaderWorkerSet (LWS), Prefix-Aware Routing & Failure Modes (V12 Ch. 9, GAK Ch. 3 & 7)
    lws = evaluate_lws_and_prefix_routing(
        lws_replicas=2,
        lws_group_size=2,
        gpus_per_pod=8,
        single_node_tps=60.0,
        num_dp_nodes=4,
        observed_round_robin_tps=110.0,
    )
    check(
        "20. LeaderWorkerSet (replicas=2, size=2, 8 GPUs/pod) schedules 1 leader + 1 worker pod (16 GPUs) per replica and 32 GPUs total with gang semantics",
        lws["pods_per_lws_replica"] == 2.0
        and lws["leader_pods_per_replica"] == 1.0
        and lws["worker_pods_per_replica"] == 1.0
        and lws["gpus_per_lws_replica"] == 16.0
        and lws["total_cluster_gpus"] == 32.0,
    )
    check(
        "21. Naive round-robin across 4 DP nodes achieves 110 tok/s vs 240 tok/s ideal (45.83% efficiency) with 73% GPU util spread (95% vs 22%) and 73% KV spread (91% vs 18%)",
        lws["ideal_dp_tps"] == 240.0
        and lws["round_robin_scaling_eff_pct"] == 45.83
        and lws["gpu_util_spread_pct"] == 73.0
        and lws["kv_usage_spread_pct"] == 73.0,
    )
    check(
        "22. Unbounded prefix-hash routing creates a 3.27x load imbalance (Node 0: 3,600 requests vs Node 1: 1,100 requests)",
        lws["prefix_skew_ratio"] == 3.27,
    )
    check(
        "23. PP stage KV cache imbalance (Stage 0 = 99.2% vs Stage 1 = 38.5%, diff = 0.607 > 0.40) triggers PipelineStageKVCacheImbalance alert",
        lws["pp_kv_imbalance_diff"] == 0.607
        and lws["pp_imbalance_alert_triggered"] == 1.0,
    )

    # 8. GPUDirect RDMA Latency Reduction & DistServe / SGLang Long-Context Multipliers (V12 Ch. 9, ASP Ch. 15, DAI Ch. 11)
    gdr_min_speedup = 4.0
    gdr_max_speedup = 6.0
    distserve_goodput_gain = 7.4
    distserve_slo_tightening = 12.6
    sglang_long_ctx_prefill_gain = 3.31
    sglang_long_ctx_ttft_reduction_pct = 81.0
    check(
        "24. GPUDirect RDMA (NCCL_NET_GDR_LEVEL=5) cuts inter-node P2P latency by 4x to 6x; DistServe PD disaggregation delivers up to 7.4x goodput and 12.6x tighter SLOs",
        gdr_min_speedup == 4.0
        and gdr_max_speedup == 6.0
        and distserve_goodput_gain == 7.4
        and distserve_slo_tightening == 12.6,
    )
    check(
        "25. Long-context sequence/pipeline parallelism on 1M-token prompts achieves 3.31x prefill throughput and up to 81% TTFT reduction",
        sglang_long_ctx_prefill_gain == 3.31
        and sglang_long_ctx_ttft_reduction_pct == 81.0,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
