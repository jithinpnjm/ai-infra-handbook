#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.5: TensorRT and TensorRT-LLM."""

from __future__ import annotations
import math
import sys
from tensorrt_llm_engine import (
    OptimizationProfileSpec,
    EngineArtifactMetadata,
    fold_batchnorm_into_weights,
    fuse_qkv_projections_horizontal,
    evaluate_optimization_profile,
    verify_engine_portability_and_context_pool,
    compute_kl_entropy_calibration_scale,
    compute_smoothquant_scales,
    evaluate_modelopt_quantization_formats,
    evaluate_tp_layer_communication,
    model_flash_decoding_xqa_occupancy,
    evaluate_paged_kv_cache_and_batching,
)


def run_lab() -> int:
    print("=== Chapter 15.5 Lab: TensorRT and TensorRT-LLM Engine Verification ===")
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

    # 1. Vertical Fusion: Conv + BatchNorm + Activation weight folding
    w_folded, b_folded = fold_batchnorm_into_weights(
        weights=[[2.0, -4.0], [1.5, 3.0]],
        bias=[1.0, 2.0],
        mu=[0.5, 1.0],
        sigma_sq=[0.25, 1.0],
        gamma=[1.0, 2.0],
        beta=[0.1, -0.5],
        epsilon=0.0,
    )
    # Channel 0: scale = 1.0 / sqrt(0.25) = 2.0 -> W_hat[0] = [4.0, -8.0], b_hat[0] = (1.0 - 0.5)*2.0 + 0.1 = 1.1
    # Channel 1: scale = 2.0 / sqrt(1.0)  = 2.0 -> W_hat[1] = [3.0,  6.0], b_hat[1] = (2.0 - 1.0)*2.0 - 0.5 = 1.5
    check(
        "1. Vertical fusion folds BatchNorm (mu, sigma^2, gamma, beta) into Conv weights W_hat=[[4.0, -8.0], [3.0, 6.0]] and bias b_hat=[1.1, 1.5]",
        w_folded == [[4.0, -8.0], [3.0, 6.0]] and b_folded == [1.1, 1.5],
    )

    # 2. Horizontal Fusion: QKV projection concatenation W_QKV = [W_Q | W_K | W_V]
    qkv_res = fuse_qkv_projections_horizontal(
        hidden_state=[1.0, 2.0, -1.0, 0.5],
        w_q=[[1.0, 0.0], [0.5, 1.0], [-1.0, 2.0], [2.0, -1.0]],
        w_k=[[0.5, -0.5], [1.0, 0.0], [0.0, 1.0], [-1.0, 2.0]],
        w_v=[[-1.0, 1.0], [0.0, 0.5], [2.0, -1.0], [1.0, 1.0]],
    )
    check(
        "2. Horizontal QKV fusion concatenates W_Q, W_K, W_V into W_QKV (4x6), cutting kernel launches from 3 to 1 (3.0x) with bit-exact output",
        qkv_res["unfused_kernel_launches"] == 3
        and qkv_res["fused_kernel_launches"] == 1
        and qkv_res["w_qkv_shape"] == (4, 6)
        and qkv_res["outputs_match"] is True,
    )

    # 3. Dynamic Shapes & IOptimizationProfile: Unbounded MAX OOM vs Bounded Profile
    prof_oom = evaluate_optimization_profile(
        OptimizationProfileSpec(
            input_name="input_image",
            min_shape=(1, 3, 256, 256),
            opt_shape=(128, 3, 4096, 4096),
            max_shape=(128, 3, 4096, 4096),
            bytes_per_element=4,
            workspace_limit_gb=4.0,
        ),
        runtime_shape=(8, 3, 512, 512),
        production_median_shape=(8, 3, 1024, 1024),
        num_Intermediate_layers=4,
        gpu_vram_gb=80.0,
    )
    check(
        "3. Unbounded IOptimizationProfile MAX=(128, 3, 4096, 4096) in FP32 allocates 25,769,803,776 bytes (~25.77 GB decimal / 24.0 GiB) per layer and triggers builder OOM on 80 GB A100",
        prof_oom["single_layer_max_bytes"] == 25769803776
        and prof_oom["single_layer_max_gb_decimal"] == 25.77
        and prof_oom["opt_equals_max_antipattern"] is True
        and prof_oom["builder_oom"] is True,
    )

    prof_seq_oom = evaluate_optimization_profile(
        OptimizationProfileSpec(
            input_name="attn_matrix",
            min_shape=(1, 512, 512),
            opt_shape=(16, 2048, 2048),
            max_shape=(128, 8192, 8192),
            bytes_per_element=4,
            workspace_limit_gb=4.0,
        ),
        runtime_shape=(16, 2048, 2048),
        production_median_shape=(16, 2048, 2048),
        num_Intermediate_layers=3,
        gpu_vram_gb=80.0,
    )
    check(
        "4. Sequence profile MAX=(128, 8192, 8192) in FP32 requires 34,359,738,368 bytes (~34.36 GB / 34 GB) per activation layer, causing tactic profiler std::bad_alloc",
        prof_seq_oom["single_layer_max_bytes"] == 34359738368
        and prof_seq_oom["single_layer_max_gb_decimal"] == 34.36
        and prof_seq_oom["builder_oom"] is True,
    )

    prof_fixed = evaluate_optimization_profile(
        OptimizationProfileSpec(
            input_name="input_image",
            min_shape=(1, 3, 256, 256),
            opt_shape=(8, 3, 1024, 1024),
            max_shape=(32, 3, 2048, 2048),
            bytes_per_element=2,  # FP16 enabled
            workspace_limit_gb=4.0,
        ),
        runtime_shape=(8, 3, 1024, 1024),
        production_median_shape=(8, 3, 1024, 1024),
        num_Intermediate_layers=2,
        gpu_vram_gb=80.0,
    )
    check(
        "5. Bounded FP16 profile min=(1,3,256,256), opt=(8,3,1024,1024), max=(32,3,2048,2048) with 4 GB workspace fits in 5.61 GB (< 6.1 GB peak VRAM) and aligns kOPT with P50 median",
        prof_fixed["bounds_valid"] is True
        and prof_fixed["opt_matches_median"] is True
        and prof_fixed["builder_oom"] is False
        and prof_fixed["total_builder_activation_gb"] <= 6.1,
    )

    # 4. Hardware/Driver Portability & Multi-Threaded IExecutionContext Pool
    eng_a100 = EngineArtifactMetadata(
        model_name="llama-3-8b",
        sm_arch="sm_80",
        trt_version="10.8.0",
        tp_size=2,
        pp_size=1,
        max_batch_size=128,
        max_input_len=4096,
        max_seq_len=8192,
    )
    port_fail_sm = verify_engine_portability_and_context_pool(
        eng_a100,
        target_sm_arch="sm_90a",  # H100
        target_trt_version="10.8.1",
        target_tp_size=2,
        target_pp_size=1,
        worker_threads=8,
        execution_contexts_allocated=8,
    )
    check(
        "6. Engine compiled on A100 (sm_80) is rejected on H100 (sm_90a) due to SM binary incompatibility",
        port_fail_sm["sm_match"] is False and port_fail_sm["can_deserialize"] is False,
    )

    port_fail_ctx = verify_engine_portability_and_context_pool(
        eng_a100,
        target_sm_arch="sm_80",
        target_trt_version="10.8.0",
        target_tp_size=2,
        target_pp_size=1,
        worker_threads=16,
        execution_contexts_allocated=1,  # Shared single IExecutionContext across 16 threads
    )
    check(
        "7. Sharing 1 mutable IExecutionContext across 16 concurrent worker threads is flagged unsafe (setTensorAddress race)",
        port_fail_ctx["can_deserialize"] is True
        and port_fail_ctx["context_thread_safe"] is False
        and port_fail_ctx["deployment_safe"] is False,
    )

    port_ok = verify_engine_portability_and_context_pool(
        eng_a100,
        target_sm_arch="sm_80",
        target_trt_version="10.8.2",
        target_tp_size=2,
        target_pp_size=1,
        worker_threads=16,
        execution_contexts_allocated=16,
    )
    check(
        "8. Matching sm_80, TensorRT 10.8, TP=2, PP=1, and 16 pooled IExecutionContexts for 16 streams is deployment_safe=True with 1 shared ICudaEngine per GPU",
        port_ok["deployment_safe"] is True and port_ok["cuda_engines_per_gpu"] == 1,
    )

    # 5. INT8 KL-Divergence Entropy Calibration (2048 bins, S = T* / 127)
    num_bins = 2048
    bin_width = 0.05  # Max range = 102.4
    edges = [i * bin_width for i in range(num_bins + 1)]
    # Dense core distribution in bins 0..511 (values 0..25.6), negligible outlier spike in bin 2047
    counts = [1000.0 * math.exp(-i / 120.0) if i < 512 else (0.001 if i == 2047 else 0.0) for i in range(num_bins)]
    kl_res = compute_kl_entropy_calibration_scale(counts, edges, candidate_clip_bins=[256, 512, 1024, 1536, 2048])
    check(
        "9. INT8 KL-divergence calibrator over 2048 bins selects clip threshold T*=25.6 (bin 512, S=25.6/127=0.201575) instead of outlier max T=102.4 (S=0.806299)",
        kl_res["num_bins"] == 2048.0
        and kl_res["optimal_clip_bin"] == 512.0
        and abs(kl_res["optimal_threshold_T"] - 25.6) < 1e-5
        and abs(kl_res["optimal_scale_S"] - round(25.6 / 127.0, 6)) < 1e-5
        and kl_res["optimal_scale_S"] < kl_res["abs_max_scale"],
    )

    # 6. SmoothQuant Per-Channel Migration (W8A8 INT8)
    sq_res = compute_smoothquant_scales(
        activation_channel_max=[64.0, 100.0, 16.0],
        weight_channel_max=[1.0, 4.0, 1.0],
        alpha=0.5,
    )
    # Channel 0: s = 64^0.5 / 1^0.5 = 8.0 -> X_hat=8.0, W_hat=8.0
    # Channel 1: s = 100^0.5 / 4^0.5 = 10 / 2 = 5.0 -> X_hat=20.0, W_hat=20.0
    # Channel 2: s = 16^0.5 / 1^0.5 = 4.0 -> X_hat=4.0, W_hat=4.0
    check(
        "10. SmoothQuant (alpha=0.5) computes s=[8.0, 5.0, 4.0], equalizing activation and weight maxima to [8.0, 20.0, 4.0]",
        sq_res["scales"] == [8.0, 5.0, 4.0]
        and sq_res["smoothed_activation_max"] == [8.0, 20.0, 4.0]
        and sq_res["smoothed_weight_max"] == [8.0, 20.0, 4.0],
    )

    # 7. ModelOpt Quantization Formats (70B & 117B/21B GPT-OSS FP4)
    q_70b = evaluate_modelopt_quantization_formats(params_billions=70.0)
    check(
        "11. Llama-3-70B raw weight footprint scales from 280.0 GB (FP32) -> 140.0 GB (FP16/BF16) -> 70.0 GB (FP8/INT8) -> 35.0 GB (INT4 AWQ / NVFP4)",
        q_70b["FP32"]["raw_weight_gb"] == 280.0
        and q_70b["FP16_BF16"]["raw_weight_gb"] == 140.0
        and q_70b["FP8_E4M3_E5M2"]["raw_weight_gb"] == 70.0
        and q_70b["INT4_AWQ_W4A16"]["raw_weight_gb"] == 35.0
        and q_70b["NVFP4_W4A4"]["raw_weight_gb"] == 35.0,
    )

    check(
        "12. Effective 70B weight size including group/microblock scales is 36.09 GB for INT4 AWQ (group=128) and 39.38 GB for NVFP4 (block=16)",
        q_70b["INT4_AWQ_W4A16"]["effective_weight_gb"] == 36.09
        and q_70b["NVFP4_W4A4"]["effective_weight_gb"] == 39.38,
    )

    q_117b = evaluate_modelopt_quantization_formats(params_billions=117.0)
    q_21b = evaluate_modelopt_quantization_formats(params_billions=21.0)
    check(
        "13. 4-bit FP4 (0.5 B/param) shrinks 117B gpt-oss-120b to 58.5 GB (< 80 GB GPU) and 21B gpt-oss-20b to 10.5 GB (< 16 GB edge GPU)",
        q_117b["NVFP4_W4A4"]["raw_weight_gb"] == 58.5 and q_21b["NVFP4_W4A4"]["raw_weight_gb"] == 10.5,
    )

    # 8. TensorRT-LLM Megatron-Style TP Communication Math
    tp8_decode = evaluate_tp_layer_communication(
        tp_size=8,
        batch_size=64,
        seq_len=1,
        hidden_size=8192,
        num_layers=80,
        bytes_per_element=2,
        nvlink_bw_gbps=900.0,
        ib_bw_gbps=50.0,
    )
    # Per AllReduce: 2 * (7/8) * 64 * 1 * 8192 * 2 = 1,835,008 bytes (1.75 MiB)
    # Per layer (2 AllReduces): 3,670,016 bytes (3.5 MiB); Total 80 layers: 280.0 MiB
    check(
        "14. TP=8 executes 2 AllReduces/layer (160 total across 80 layers), moving 1,835,008 B per AllReduce and 280.0 MiB per decode step at B=64",
        tp8_decode["allreduces_per_layer"] == 2
        and tp8_decode["total_allreduces"] == 160
        and tp8_decode["bytes_per_allreduce"] == 1835008.0
        and tp8_decode["total_comm_mb"] == 280.0,
    )

    check(
        "15. Running TP=8 across 50 GB/s InfiniBand instead of 900 GB/s NVLink slows AllReduce communication by 18.0x",
        tp8_decode["ib_vs_nvlink_slowdown_x"] == 18.0,
    )

    # 9. FlashDecoding & XQA Decode SM Occupancy on 132-SM H100
    occ_b4 = model_flash_decoding_xqa_occupancy(
        batch_size=4,
        kv_seq_len=8192,
        num_q_heads=64,
        num_kv_heads=8,
        tp_size=8,
        kv_chunk_size=256,
        gpu_sms=132,
    )
    # At TP=8, local_kv_heads = 1, local_q_heads = 8 (GQA group = 8).
    # Standard FA2 GQA without KV split launches 4 * 1 = 4 thread blocks on 132 SMs (3.03% SM coverage).
    # FlashDecoding/XQA splits 8192 / 256 = 32 chunks -> 4 * 1 * 32 = 128 blocks (96.97% SM coverage, capped at 8.0x speedup).
    check(
        "16. At B=4, S_kv=8192, TP=8 on H100 (132 SMs), unsplit GQA launches 4 blocks (3.03% SMs) while FlashDecoding/XQA (256-tok chunks) launches 128 blocks (96.97% SMs, 8.0x speedup)",
        occ_b4["local_kv_heads"] == 1
        and occ_b4["gqa_group_size"] == 8
        and occ_b4["fa2_thread_blocks"] == 4
        and occ_b4["fa2_sm_utilization_pct"] == 3.03
        and occ_b4["flash_decoding_thread_blocks"] == 128
        and occ_b4["flash_decoding_sm_utilization_pct"] == 96.97
        and occ_b4["estimated_decode_speedup_x"] == 8.0,
    )

    # 10. Paged KV Cache Sizing, Block Fragmentation, and Concurrency Scaling
    kv_fp16_b128 = evaluate_paged_kv_cache_and_batching(
        num_layers=80,
        num_kv_heads=8,
        head_dim=128,
        seq_len=4096,
        sample_unaligned_seq_len=129,
        tokens_per_block=128,
        kv_bytes_per_element=2,
        tp_size=4,
        gpu_vram_gb=80.0,
        model_weights_total_gb=140.0,
        free_gpu_mem_fraction=0.95,
    )
    check(
        "17. Llama-3-70B FP16 KV cache consumes 327,680 bytes/token (320.0 KB/token) and 1.31 GB per 4,096-token sequence",
        kv_fp16_b128["kv_bytes_per_token"] == 327680
        and kv_fp16_b128["kv_kb_per_token"] == 320.0
        and kv_fp16_b128["seq_kv_gb"] == 1.31,
    )

    check(
        "18. Setting tokens_per_block=128 allocates 2 blocks (256 slots) for a 129-token sequence, wasting 127 slots (49.61% internal fragmentation)",
        kv_fp16_b128["blocks_for_unaligned_seq"] == 2
        and kv_fp16_b128["allocated_slots_unaligned"] == 256
        and kv_fp16_b128["wasted_slots_unaligned"] == 127
        and kv_fp16_b128["internal_fragmentation_pct"] == 49.61,
    )

    kv_fp8_b32 = evaluate_paged_kv_cache_and_batching(
        num_layers=80,
        num_kv_heads=8,
        head_dim=128,
        seq_len=4096,
        sample_unaligned_seq_len=129,
        tokens_per_block=32,
        kv_bytes_per_element=1,
        tp_size=4,
        gpu_vram_gb=80.0,
        model_weights_total_gb=140.0,
        free_gpu_mem_fraction=0.85,
    )
    check(
        "19. Enabling FP8 KV cache cuts Llama-3-70B KV footprint by 50% to 163,840 bytes/token (160.0 KB/token) and 0.65 GB per 4,096-token sequence",
        kv_fp8_b32["kv_bytes_per_token"] == 163840
        and kv_fp8_b32["kv_kb_per_token"] == 160.0
        and kv_fp8_b32["seq_kv_gb"] == 0.65,
    )

    check(
        "20. Reducing tokens_per_block from 128 to 32 cuts internal fragmentation on a 129-token sequence from 49.61% (127 wasted) to 19.38% (5 blocks = 160 slots, 31 wasted)",
        kv_fp8_b32["blocks_for_unaligned_seq"] == 5
        and kv_fp8_b32["allocated_slots_unaligned"] == 160
        and kv_fp8_b32["wasted_slots_unaligned"] == 31
        and kv_fp8_b32["internal_fragmentation_pct"] == 19.38,
    )

    check(
        "21. Lowering free_gpu_mem_fraction from 0.95 to 0.85 on 4x 80 GB GPUs (180 GB post-weight VRAM) increases activation workspace headroom from 9.0 GB to 27.0 GB while expanding full 4K-sequence capacity from 136 to 244",
        kv_fp16_b128["activation_headroom_gb"] == 9.0
        and kv_fp8_b32["activation_headroom_gb"] == 27.0
        and kv_fp16_b128["max_concurrent_full_seqs"] == 136
        and kv_fp8_b32["max_concurrent_full_seqs"] == 244,
    )

    # 11. Production Benchmark & Troubleshooting Ratios from Volume 12 Ch. 4 & Ch. 5 and ASP Ch. 8 & Ch. 9
    itl_speedup = round(115.0 / 18.4, 2)
    check(
        "22. TensorRT-LLM reduces 70B Inter-Token Latency (ITL) at 150 concurrent sessions from 115.0 ms/tok to 18.4 ms/tok (6.25x speedup, meeting < 25 ms/tok SLA)",
        itl_speedup == 6.25 and 18.4 < 25.0,
    )

    seg_speedup = round(48.0 / 11.3, 2)
    check(
        "23. Bounded TensorRT segmentation engine reduces median B=8 (1024x1024) latency from 48.0 ms to 11.3 ms (4.25x speedup)",
        seg_speedup == 4.25,
    )

    wer_delta = round(3.35 - 3.20, 2)
    check(
        "24. Representative 1,000-sample production audio INT8 calibration restores WER from 24.8% to 3.35% (within 0.15% of 3.2% FP16 baseline at 3.1x speedup)",
        wer_delta == 0.15,
    )

    tp4_comm_efficiency = round(8.0 / (8.0 + 11.0) * 100.0, 2)
    b200_fp4_vs_fp32 = round(10000.0 / 80.0, 1)  # 10 PFLOPS (10,000 TFLOPS) vs 80 TFLOPS FP32 = 125.0x
    b300_vs_b200_fp4 = round(15.0 / 10.0, 2)     # 15 PFLOPS vs 10 PFLOPS = 1.5x (+50%)
    check(
        "25. Small-model TP=4 compute/comm efficiency (8 ms compute vs 11 ms comm) is 42.11% (~42%), and Blackwell NVFP4 delivers 10 PFLOPS on B200 (125.0x over 80 TFLOPS FP32) and 15 PFLOPS on B300 (1.5x)",
        tp4_comm_efficiency == 42.11 and b200_fp4_vs_fp32 == 125.0 and b300_vs_b200_fp4 == 1.5,
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
