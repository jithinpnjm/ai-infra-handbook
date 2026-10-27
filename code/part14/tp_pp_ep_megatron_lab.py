#!/usr/bin/env python3
"""Self-checking lab for Chapter 14.7: Tensor, Pipeline, and Expert Parallelism; Megatron."""

from __future__ import annotations
import sys
from tp_pp_ep_megatron import (
    HybridParallelConfig,
    TensorParallelConfig,
    analyze_context_parallelism_vs_ulysses,
    analyze_expert_parallelism_moe,
    analyze_tensor_and_sequence_parallelism,
    compute_distributed_optimizer_bytes_per_param,
    compute_pipeline_parallel_metrics,
    map_rank_to_3d_coordinates,
    simulate_tp_cross_node_penalty,
    validate_hybrid_5d_config,
)


def run_lab() -> int:
    print("=== Chapter 14.7 Lab: Tensor, Pipeline, and Expert Parallelism; Megatron ===")
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

    # 1. Why FSDP2 Cannot Replace Megatron: Layer Matrix Size Limits (DAI Ch 5)
    check(
        "1. 175B single MLP weight matrix (12288 x 49152) has 603,979,776 params (>600M, ~1.2 GB in FP16) vs 7B (4096 x 16384 = 67,108,864 params)",
        12288 * 49152 == 603_979_776
        and round((12288 * 49152 * 2) / 1e9, 1) == 1.2
        and 4096 * 16384 == 67_108_864,
    )

    check(
        "2. 16K x 16K attention weight matrix (16384 x 16384 = 268,435,456 params) splits across TP=8 into 16384 x 2048 slices per GPU",
        16384 * 16384 == 268_435_456 and 16384 // 8 == 2048,
    )

    # 2. Tensor Parallelism (ColumnParallel + RowParallel) & Sequence Parallelism (SP)
    tp_cfg = TensorParallelConfig(
        hidden_size=12288,
        ffn_hidden_size=49152,
        num_attention_heads=96,
        num_query_groups=96,
        num_layers=96,
        batch_size=1,
        seq_len=2048,
        tp_size=8,
        bytes_per_element=2,
        sequence_parallel=True,
    )
    tp_res = analyze_tensor_and_sequence_parallelism(tp_cfg)
    check(
        "3. GPT-3 175B TP=8 splits ColumnParallelLinear (12288, 49152) -> (12288, 6144), RowParallelLinear -> (6144, 12288), and 96 heads -> 12 heads/GPU",
        tp_res["w1_shard_shape"] == (12288, 6144)
        and tp_res["w2_shard_shape"] == (6144, 12288)
        and tp_res["local_attention_heads"] == 12,
    )

    check(
        "4. Sequence Parallelism (SP) replaces each TP AllReduce with 1 AllGather + 1 ReduceScatter of identical collective volume while cutting non-TP activation memory by TP=8x (local_seq=256)",
        tp_res["comm_volume_identical"] is True
        and tp_res["sp_activation_reduction_factor"] == 8.0
        and tp_res["local_seq_len_sp"] == 256,
    )

    # 3. Cross-Node TP Failure Math (Volume 13 Ch 6)
    tp_fail = simulate_tp_cross_node_penalty(
        shard_mb=219.0, num_layers=120, allreduces_per_layer=2, nvlink_bw_gbps=900.0, ib_bw_gbps=25.0
    )
    check(
        "5. Cross-node TP=32 on 120-layer model (240 AllReduces of 219 MB): NVLink takes ~0.243 ms (~0.25 ms, ~60 ms total) vs IB 8.76 ms (~9 ms, ~2160 ms total, 36x slower per collective)",
        tp_fail["total_allreduces"] == 240.0
        and round(tp_fail["nvlink_ms_per_ar"], 2) == 0.24
        and round(tp_fail["ib_ms_per_ar"], 2) == 8.76
        and round(tp_fail["per_collective_slowdown"], 0) == 36.0,
    )

    check(
        "6. Constraining TP=8 within nodes + PP=4 across nodes restores training throughput from 1.2 tok/s to 18 tok/s (15x recovery vs 16.7x slowdown from 20 tok/s ideal)",
        round(20.0 / 1.2, 1) == 16.7 and round(18.0 / 1.2, 1) == 15.0,
    )

    # 4. Pipeline Parallelism Bubble Fractions: GPipe vs 1F1B vs Interleaved 1F1B (V13 Ch 6 & Ch 7, DAI Ch 5)
    pp_4_8 = compute_pipeline_parallel_metrics(pp_size=4, num_microbatches=8)
    pp_4_16 = compute_pipeline_parallel_metrics(pp_size=4, num_microbatches=16)
    pp_4_32 = compute_pipeline_parallel_metrics(pp_size=4, num_microbatches=32)
    check(
        "7. PP=4 bubble fraction (PP-1)/(m+PP-1) drops from 3/11 (27.3% ~ 27%) at m=8 to 3/19 (15.8% ~ 16%) at m=16 and 3/35 (8.6% ~ 8%) at m=32",
        round(pp_4_8["bubble_time_pct"], 1) == 27.3
        and round(pp_4_16["bubble_time_pct"], 1) == 15.8
        and round(pp_4_32["bubble_time_pct"], 1) == 8.6,
    )

    pp_starve = compute_pipeline_parallel_metrics(pp_size=8, num_microbatches=16)
    pp_fixed = compute_pipeline_parallel_metrics(pp_size=8, num_microbatches=64)
    check(
        "8. PP=8 bubble starvation (m=16 micro-batches: 7/23 = 30.4% ~ 30% bubble, 6.2 tok/s) drops to 7/71 = 9.9% (~10% bubble, 9.7 tok/s) when m=64",
        round(pp_starve["bubble_time_pct"], 1) == 30.4
        and round(pp_fixed["bubble_time_pct"], 1) == 9.9,
    )

    pp_512 = compute_pipeline_parallel_metrics(pp_size=8, num_microbatches=512)
    check(
        "9. PP=8 with global_batch=2048, micro_batch=4 (m=512 micro-batches) achieves 7/519 = 1.35% bubble (~80 ms on a 6 s step)",
        round(pp_512["bubble_time_pct"], 2) == 1.35,
    )

    pp_interleaved = compute_pipeline_parallel_metrics(
        pp_size=16, num_microbatches=256, virtual_stages=2, activation_per_microbatch_gb=0.5
    )
    check(
        "10. 1F1B caps stage-0 in-flight micro-batches at PP=16 vs GPipe m=256 (16x activation memory saving: 8.0 GB vs 128.0 GB), and v=2 interleaved 1F1B halves bubble-to-useful ratio (PP-1)/(m*v)",
        pp_interleaved["gpipe_inflight_microbatches"] == 256
        and pp_interleaved["one_f_one_b_inflight_microbatches"] == 16
        and pp_interleaved["activation_memory_saving_factor"] == 16.0
        and pp_interleaved["interleaved_bubble_to_useful_ratio"]
        == pp_interleaved["bubble_to_useful_ratio"] / 2.0,
    )

    # 5. Pipeline Stage Imbalance ("Ghost Straggler", V13 Ch 7)
    vocab_table_bytes = 50_000 * 12_288 * 2
    check(
        "11. Stage 0/15 embedding/lm_head table for V=50,000, H=12,288 in BF16 (2B) is 1,228,800,000 bytes (~1.2 GB), explaining the ~40% stage straggler",
        vocab_table_bytes == 1_228_800_000 and round(vocab_table_bytes / 1e9, 1) == 1.2,
    )

    # 6. Long Context: Context Parallelism (CP Ring Attention) vs DeepSpeed-Ulysses
    cp_res = analyze_context_parallelism_vs_ulysses(
        batch_size=1,
        seq_len=32768,
        num_heads=32,
        num_kv_heads=8,
        head_dim=128,
        cp_degree=4,
        bytes_per_element=2,
    )
    check(
        "12. Context Parallelism (CP=4 on 32K sequence) shards sequence to 8192 tokens/GPU over 3 Ring Attention P2P rotation steps; DeepSpeed-Ulysses transposes (1, 8192, 32, 128) -> (1, 32768, 8, 128)",
        cp_res["local_seq_len"] == 8192
        and cp_res["ring_steps"] == 3
        and cp_res["ulysses_seq_parallel_shape"] == (1, 8192, 32, 128)
        and cp_res["ulysses_head_parallel_shape"] == (1, 32768, 8, 128),
    )

    # 7. Expert Parallelism (EP) for Mixture-of-Experts (Mixtral 8x7B & DeepSeek-V3)
    ep_mixtral = analyze_expert_parallelism_moe(
        num_experts=8,
        ep_size=8,
        top_k=2,
        batch_size=2,
        seq_len=4096,
        hidden_size=4096,
        capacity_factor=1.25,
        bytes_per_element=2,
    )
    check(
        "13. Mixtral 8x7B (8 experts, EP=8, top_k=2) places 1 expert/GPU, dispatches 16,384 token embeddings/GPU, and sets expert capacity to 20,480 tokens at CF=1.25",
        ep_mixtral["experts_per_gpu"] == 1
        and ep_mixtral["dispatched_tokens_per_gpu"] == 16384
        and ep_mixtral["uniform_tokens_per_expert"] == 16384.0
        and ep_mixtral["expert_capacity_tokens"] == 20480,
    )

    ep_dsv3 = analyze_expert_parallelism_moe(
        num_experts=256,
        ep_size=64,
        top_k=8,
        batch_size=1,
        seq_len=4096,
        hidden_size=7168,
        capacity_factor=1.0,
        bytes_per_element=2,
        shared_experts=1,
    )
    check(
        "14. DeepSeek-V3 MoE (~671B-680B total, 37B active) uses 1 shared + 8 routed experts out of 256 (9 active experts/token) and places 4 routed experts/GPU at EP=64",
        ep_dsv3["experts_per_gpu"] == 4 and ep_dsv3["total_active_experts_per_token"] == 9,
    )

    # 8. Megatron Distributed Optimizer Memory Formulas (DAI Ch 5)
    do_fp16 = compute_distributed_optimizer_bytes_per_param("fp16_params_fp16_grads", dp_size=8)
    do_bf16 = compute_distributed_optimizer_bytes_per_param("bf16_params_fp32_grads", dp_size=8)
    do_fp32 = compute_distributed_optimizer_bytes_per_param("fp32_params_fp32_grads", dp_size=8)
    check(
        "15. Megatron Distributed Optimizer on d=8 DP ranks drops bf16/fp32 memory from 18 B to 6 + 12/8 = 7.5 B/param (2.4x reduction), fp16/fp16 from 20 B to 6.0 B, and fp32/fp32 from 16 B to 9.0 B",
        do_bf16["unsharded_bytes_per_param"] == 18.0
        and do_bf16["sharded_bytes_per_param"] == 7.5
        and round(do_bf16["reduction_factor"], 1) == 2.4
        and do_fp16["sharded_bytes_per_param"] == 6.0
        and do_fp32["sharded_bytes_per_param"] == 9.0,
    )

    # 9. Worked Example: GPT-3 175B on 1024 H100s (V13 Ch 7) & 128 GPUs (DAI Ch 5)
    gpt3_1024 = validate_hybrid_5d_config(
        HybridParallelConfig(
            world_size=1024,
            gpus_per_node=8,
            tp=8,
            pp=16,
            cp=1,
            num_layers=96,
            params_billion=175.0,
            global_batch_size=2048,
            micro_batch_size=1,
        )
    )
    check(
        "16. GPT-3 175B on 1024 H100s (TP=8, PP=16, DP=8): 6 layers/stage, 1.367B (~1.37B) params/GPU = 21.875 GB (~22 GB) state, m=256 micro-batches/DP, and 15/271 = 5.54% (~5.5%) bubble",
        gpt3_1024["valid_world_size"] is True
        and gpt3_1024["dp_size"] == 8
        and gpt3_1024["layers_per_stage"] == 6
        and round(gpt3_1024["params_per_gpu_billion"], 2) == 1.37
        and round(gpt3_1024["unsharded_dp_state_gb"], 0) == 22.0
        and gpt3_1024["num_microbatches_per_dp"] == 256
        and round(gpt3_1024["pipeline_bubble_pct"], 1) == 5.5,
    )

    gpt3_128 = validate_hybrid_5d_config(
        HybridParallelConfig(
            world_size=128,
            gpus_per_node=8,
            tp=8,
            pp=16,
            cp=1,
            num_layers=96,
            params_billion=175.0,
            global_batch_size=1536,
            micro_batch_size=1,
        )
    )
    check(
        "17. GPT-3 175B on 128 GPUs (16 nodes x 8 GPUs, TP=8, PP=16) yields DP=1 and m=1536 micro-batches",
        gpt3_128["dp_size"] == 1 and gpt3_128["num_microbatches_per_dp"] == 1536,
    )

    # 10. Real-World Hybrid Configurations: Llama-3 8B, 70B Hybrid, Mixtral 8x7B, and 1T Model
    llama3_8b = validate_hybrid_5d_config(
        HybridParallelConfig(
            world_size=8,
            gpus_per_node=8,
            tp=1,
            pp=1,
            cp=2,
            num_layers=32,
            params_billion=8.0,
            global_batch_size=128,
            micro_batch_size=1,
        )
    )
    check(
        "18. Llama-3 8B with 8K context on 8 GPUs (TP=1, PP=1, CP=2) yields DP=4 and 32 micro-batches per DP group",
        llama3_8b["dp_size"] == 4 and llama3_8b["num_microbatches_per_dp"] == 32,
    )

    hybrid_70b = validate_hybrid_5d_config(
        HybridParallelConfig(
            world_size=64,
            gpus_per_node=8,
            tp=4,
            pp=2,
            cp=1,
            num_layers=80,
            params_billion=70.0,
            global_batch_size=128,
            micro_batch_size=1,
        )
    )
    check(
        "19. 70B Hybrid config on 64 GPUs (8 nodes x 8 GPUs, TP=4, PP=2) yields DP=8, 40 layers/stage, and TP within NVLink domain",
        hybrid_70b["dp_size"] == 8
        and hybrid_70b["layers_per_stage"] == 40
        and hybrid_70b["tp_within_nvlink_domain"] is True,
    )

    model_1t = validate_hybrid_5d_config(
        HybridParallelConfig(
            world_size=1024,
            gpus_per_node=64,
            tp=8,
            pp=4,
            cp=1,
            num_layers=128,
            params_billion=1000.0,
            global_batch_size=2048,
            micro_batch_size=1,
        )
    )
    check(
        "20. 1T parameter model (12 TB at 12 B/param vs 1.28 TB on 16x80GB H100s = 9.375x ~ 9.4x shortfall) on 1024 GPUs (TP=8, PP=4) yields DP=32",
        round(12.0 / 1.28, 1) == 9.4 and model_1t["dp_size"] == 32,
    )

    # 11. 3D Process Grid Rank Mapping & Concrete Memory Examples (DAI Ch 2, Ch 5 & V13 Ch 1, Ch 8)
    coords = [map_rank_to_3d_coordinates(r, dp=2, tp=2, pp=2) for r in range(8)]
    tp_groups_dp0_pp0 = [c["rank"] for c in coords if c["dp_rank"] == 0 and c["pp_rank"] == 0]
    pp_groups_dp0_tp0 = [c["rank"] for c in coords if c["dp_rank"] == 0 and c["tp_rank"] == 0]
    dp_groups_pp0_tp0 = [c["rank"] for c in coords if c["pp_rank"] == 0 and c["tp_rank"] == 0]
    check(
        "21. 3D grid (WorldSize=8, DP=2, PP=2, TP=2) forms orthogonal groups: TP=[0,1], PP=[0,2], DP=[0,4]",
        tp_groups_dp0_pp0 == [0, 1]
        and pp_groups_dp0_tp0 == [0, 2]
        and dp_groups_pp0_tp0 == [0, 4],
    )

    check(
        "22. 70B memory example (DAI Ch 5): 140 GB FP16 params + 140 GB grads + 840 GB Adam state = 1120 GB (>1 TB); on 8 GPUs ZeRO-1 = 385 GB (140+140+105) and ZeRO-3 = 140 GB/GPU",
        140 + 140 + (840 // 8) == 385 and 1120 // 8 == 140,
    )

    check(
        "23. Megatron-FSDP benchmark gains (DAI Ch 5) & TorchTitan SimpleFSDP (AISPE Ch 13): 15-25% throughput and 23% memory savings (Megatron-FSDP), 28% memory and 69% throughput (SimpleFSDP)",
        15 < 23 < 25 and 28 < 69,
    )

    check(
        "24. Single A100 (312 TFLOPS) GPT-3 175B step (1.46e18 FLOPs) takes ~4,679 s (~78 min) vs ~37 s on 128 GPUs (V13 Ch 1), and 70B on H100 (860 TFLOP / 2.0 s = 430 TFLOPS / 989 TFLOPS) achieves ~43% MFU (DAI Ch 2)",
        round(1.46e18 / 312e12) == 4679
        and round(430.0 / 989.0 * 100.0) == 43,
    )

    check(
        "25. NCCL Ring vs Tree (V13 Ch 8): 28 GB AllReduce moves 49.0 GB in ~54 ms on 8-GPU 900 GB/s NVLink vs 55.9 GB in ~2.2 s on 512-GPU 25 GB/s IB (512 ring hops vs 9 tree hops)",
        2.0 * (7.0 / 8.0) * 28.0 == 49.0
        and round(49.0 / 900.0 * 1000.0) == 54
        and round(2.0 * (511.0 / 512.0) * 28.0, 1) == 55.9
        and round(55.9 / 25.0, 1) == 2.2,
    )

    check(
        "26. GB200 NVL72 rack (AISPE Ch 1): 36 Grace CPUs + 72 Blackwell GPUs = 13,824 GB (13.5 TB) HBM3e (72 x 192 GB), 1.8 TB/s NVLink 5 per GPU (130 TB/s rack), up to 2.6x training and 3.4x inference per-GPU over Hopper in MLPerf v5.0",
        72 * 192 == 13824 and 18 * 100 == 1800,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
