#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.2: Batching, the KV Cache and Quantization Fundamentals."""

from __future__ import annotations
import math
import sys
from batching_kv_quantization import (
    GPU_SPECS,
    compute_matmul_arithmetic_intensity,
    evaluate_prefill_decode_roofline,
    compute_model_bandwidth_utilization,
    analyze_batching_paradigms,
    compute_kv_cache_footprint,
    evaluate_paged_attention_and_capacity,
    compare_swap_vs_recompute_preemption,
    quantize_absmax_and_zeropoint,
    compute_smoothquant_scales,
    evaluate_quantization_formats_and_models,
)


def run_lab() -> int:
    print("=== Chapter 15.2 Lab: Batching, the KV Cache and Quantization Fundamentals Verification ===")
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

    # 1. Square Matrix Arithmetic Intensity (`HLS` Ch. 5 Table 5-9)
    ai_64 = compute_matmul_arithmetic_intensity(64, 64, 64, 2.0)
    ai_512 = compute_matmul_arithmetic_intensity(512, 512, 512, 2.0)
    ai_4096 = compute_matmul_arithmetic_intensity(4096, 4096, 4096, 2.0)
    check(
        "1. Square FP16 MatMul arithmetic intensity matches HLS Table 5-9: M=64 -> 21.33 (~21), M=512 -> 170.67 (~170), M=4096 -> 1365.33 (~1365) FLOPS/B",
        int(ai_64["arithmetic_intensity"]) == 21
        and int(ai_512["arithmetic_intensity"]) == 170
        and ai_4096["arithmetic_intensity"] == 1365.33,
    )

    # 2. L40S Ridge Point & Prefill vs Decode Roofline (`HLS` Ch. 5 Table 5-10)
    rf_64 = evaluate_prefill_decode_roofline(seq_len=64, hidden_dim=4096, batch_size=1, gpu_key="L40S")
    rf_512 = evaluate_prefill_decode_roofline(seq_len=512, hidden_dim=4096, batch_size=1, gpu_key="L40S")
    rf_4096 = evaluate_prefill_decode_roofline(seq_len=4096, hidden_dim=4096, batch_size=1, gpu_key="L40S")
    check(
        "2. L40S (362 TFLOPS / 864 GB/s) has ridge point ~419 FLOPS/B; prefill AI is 62.06 (s=64), 409.60 (s=512), and 1365.33 (s=4096) vs decode AI ~1.0 FLOPS/B",
        round(rf_64["ridge_point_flops_per_byte"]) == 419
        and rf_64["prefill_ai_flops_per_byte"] == 62.06
        and rf_512["prefill_ai_flops_per_byte"] == 409.60
        and rf_4096["prefill_ai_flops_per_byte"] == 1365.33
        and rf_4096["decode_ai_flops_per_byte"] == 1.0,
    )

    check(
        "3. On L40S (419 FLOPS/B ridge point), prefill becomes compute-bound at s=4096 while single-request decode remains memory-bandwidth-bound across all sequence lengths",
        rf_64["is_prefill_compute_bound"] is False
        and rf_512["is_prefill_compute_bound"] is False
        and rf_4096["is_prefill_compute_bound"] is True
        and rf_4096["is_decode_memory_bound"] is True,
    )

    # 3. GPU Hardware Spec Verification (`HLS` Ch. 5 Tables 5-1, 5-2, 5-4 & `AIE` Ch. 9 Table 9-2)
    h100_sxm = GPU_SPECS["H100_SXM"]
    h100_nvl = GPU_SPECS["H100_NVL"]
    h200_sxm = GPU_SPECS["H200_SXM"]
    check(
        "4. H100 SXM (80 GB, 3.35 TB/s, 1979 FP16 / 3958 FP8 TFLOPS, 900 GB/s NVLink) vs H100 NVL (94 GB, 3.9 TB/s, 1671 FP16 / 3341 FP8 TFLOPS, 600 GB/s) vs H200 SXM (141 GB, 4.8 TB/s)",
        h100_sxm.vram_gb == 80.0
        and h100_sxm.bandwidth_gbps == 3350.0
        and h100_sxm.fp16_tflops == 1979.0
        and h100_sxm.fp8_tflops == 3958.0
        and h100_nvl.vram_gb == 94.0
        and h100_nvl.bandwidth_gbps == 3900.0
        and h200_sxm.vram_gb == 141.0
        and h200_sxm.bandwidth_gbps == 4800.0,
    )

    # 4. Model Bandwidth Utilization (`MBU`, `AIE` Ch. 9)
    mbu_fp16 = compute_model_bandwidth_utilization(params_billions=7.0, bytes_per_param=2.0, tokens_per_sec=100.0, peak_bandwidth_gbps=2000.0)
    mbu_int8 = compute_model_bandwidth_utilization(params_billions=7.0, bytes_per_param=1.0, tokens_per_sec=100.0, peak_bandwidth_gbps=2000.0)
    check(
        "5. 7B model at 100 tokens/s moves 1,400 GB/s in FP16 (70% MBU on 2 TB/s A100) and 700 GB/s in INT8/FP8 (35% MBU), cutting memory bandwidth demand in half",
        mbu_fp16["bandwidth_used_gbps"] == 1400.0
        and mbu_fp16["mbu_percent"] == 70.0
        and mbu_int8["bandwidth_used_gbps"] == 700.0
        and mbu_int8["mbu_percent"] == 35.0,
    )

    # 5. Request-Level Dynamic Batching Padding Waste & Tail-Latency Locking (`V12` Ch. 7)
    # 31 short requests of 10 tokens + 1 long request of 2,000 tokens (B = 32)
    seq_batch = [10] * 31 + [2000]
    batch_stats = analyze_batching_paradigms(
        sequence_lengths=seq_batch,
        prefill_prompt_tokens=12288,
        active_decode_seqs=45,
        chunk_size=512,
        max_num_batched_tokens=2048,
    )
    check(
        "6. Request-level dynamic batching with 31x 10-token and 1x 2,000-token sequences wastes 96.39% (> 65%) on padding and traps short requests for 1,990 extra iterations",
        batch_stats["batch_size"] == 32
        and batch_stats["trapped_extra_iterations"] == 1990
        and batch_stats["padding_waste_percent"] == 96.39
        and batch_stats["continuous_batching_padding_waste"] == 0.0,
    )

    # 6. Chunked Prefill (`Sarathi-Lean`, `V12` Ch. 7)
    check(
        "7. Chunked Prefill slices a 12,288-token prompt into 24 chunks of 512 tokens alongside 45 decode streams (557 <= 2,048 token budget), preventing the 320 ms prefill stall",
        batch_stats["num_prefill_chunks"] == 24
        and batch_stats["step_tokens_with_chunking"] == 557
        and batch_stats["within_token_budget"] is True
        and batch_stats["unchunked_step_ms"] > 300.0
        and batch_stats["chunked_step_ms"] < 25.0,
    )

    # 7. KV Cache Math: Llama-2-7B MHA (`HLS` Ch. 5 Table 5-7)
    kv_llama2_7b = compute_kv_cache_footprint(
        attention_type="MHA",
        num_layers=32,
        num_query_heads=32,
        num_kv_heads=32,
        head_dim=128,
        bytes_per_element=2.0,
        seq_len=4096,
        batch_size=16,
    )
    check(
        "8. Llama-2-7B (MHA, L=32, H=32, D=128, FP16) consumes 524,288 B (512 KiB = 0.5 MiB) per token and 32.0 GiB at B=16, S=4096 (exceeding its 14 GB weights)",
        kv_llama2_7b["bytes_per_token"] == 524288
        and kv_llama2_7b["mib_per_token"] == 0.5
        and kv_llama2_7b["total_gib"] == 32.0,
    )

    # 8. Llama-2-7B Batch Size on A10 (24 GB) vs L40S (48 GB) (`HLS` Ch. 5 Table 5-7)
    a10_left_gb = 24.0 - 14.0  # 10 GB
    l40s_left_gb = 48.0 - 14.0  # 34 GB
    a10_theoretical_b = int((a10_left_gb * 1024.0) // (0.5 * 4096))  # 5 -> 4 with activation headroom
    l40s_theoretical_b = int((l40s_left_gb * 1024.0) // (0.5 * 4096))  # 17 -> 16 with activation headroom
    check(
        "9. After loading 14 GB Llama-2-7B weights, A10 (24 GB -> 10 GB left) supports theoretical max batch 5 (4 practical) while L40S (48 GB -> 34 GB left) supports 17 (16 practical)",
        a10_left_gb == 10.0
        and l40s_left_gb == 34.0
        and a10_theoretical_b == 5
        and l40s_theoretical_b == 17,
    )

    # 9. KV Cache Math: Llama-2-13B MHA (`AIE` Ch. 9)
    kv_llama2_13b = compute_kv_cache_footprint(
        attention_type="MHA",
        num_layers=40,
        num_query_heads=40,
        num_kv_heads=40,
        head_dim=128,
        bytes_per_element=2.0,
        seq_len=2048,
        batch_size=32,
    )
    check(
        "10. Llama-2-13B (MHA, L=40, H*D=5120, FP16) at B=32, S=2048 requires 53.69 GB (~54 GB, 50.0 GiB) of KV cache",
        round(kv_llama2_13b["total_gb_decimal"], 2) == 53.69 and kv_llama2_13b["total_gib"] == 50.0,
    )

    # 10. KV Cache Math: 70B MHA vs GQA (`VL5` Ch. 2 & `V12` Ch. 8)
    kv_70b_mha = compute_kv_cache_footprint(
        attention_type="MHA",
        num_layers=80,
        num_query_heads=64,
        num_kv_heads=64,
        head_dim=128,
        bytes_per_element=2.0,
        seq_len=2048,
        batch_size=128,
    )
    kv_70b_gqa = compute_kv_cache_footprint(
        attention_type="GQA",
        num_layers=80,
        num_query_heads=64,
        num_kv_heads=8,
        head_dim=128,
        bytes_per_element=2.0,
        seq_len=2048,
        batch_size=128,
    )
    check(
        "11. 70B MHA (64 KV heads) uses 2,621,440 B (2.5 MiB / ~2.6 MB) per token and 687.19 GB (~687 GB) at B=128, S=2048 vs GQA (8 KV heads) at 327,680 B (320 KiB / ~0.31 MiB) and 85.90 GB (~86 GB), an 8x (87.5%) reduction",
        kv_70b_mha["bytes_per_token"] == 2621440
        and round(kv_70b_mha["total_gb_decimal"], 1) == 687.2
        and kv_70b_gqa["bytes_per_token"] == 327680
        and kv_70b_gqa["kib_per_token"] == 320.0
        and round(kv_70b_gqa["total_gb_decimal"], 1) == 85.9
        and kv_70b_gqa["reduction_factor_vs_mha"] == 8.0
        and kv_70b_gqa["savings_pct_vs_mha"] == 87.5,
    )

    # 11. Llama-3-70B Single-Sequence Context Scaling: 4K vs 128K (`V12` Ch. 8)
    kv_70b_4k = compute_kv_cache_footprint("GQA", 80, 64, 8, 128, 2.0, seq_len=4096, batch_size=1)
    kv_70b_128k_gqa = compute_kv_cache_footprint("GQA", 80, 64, 8, 128, 2.0, seq_len=128000, batch_size=1)
    kv_70b_128k_mha = compute_kv_cache_footprint("MHA", 80, 64, 64, 128, 2.0, seq_len=128000, batch_size=1)
    check(
        "12. Llama-3-70B single sequence consumes 1.25 GiB (1.34 GB) at S=4096 and 39.0625 GiB (~39.06 GiB) at S=128,000 under GQA vs 312.5 GiB under MHA",
        kv_70b_4k["total_gib"] == 1.25
        and round(kv_70b_128k_gqa["total_gib"], 2) == 39.06
        and kv_70b_128k_mha["total_gib"] == 312.5,
    )

    # 12. MQA vs DeepSeek MLA KV Cache Math (`HLS` Ch. 6 & `V12` Ch. 8)
    kv_70b_mqa = compute_kv_cache_footprint("MQA", 80, 64, 1, 128, 2.0, seq_len=4096, batch_size=1)
    kv_deepseek_mla = compute_kv_cache_footprint(
        attention_type="MLA",
        num_layers=61,
        num_query_heads=128,
        num_kv_heads=128,
        head_dim=128,
        bytes_per_element=2.0,
        seq_len=4096,
        batch_size=1,
        kv_lora_rank=512,
        qk_rope_head_dim=64,
    )
    check(
        "13. MQA (1 KV head) gives 64x reduction (40 KiB/tok on 80-layer model), while DeepSeek MLA (kv_lora_rank=512 + qk_rope_head_dim=64 = 576 elements/layer) equals GQA with 2.25 groups (70,272 B/tok in BF16 across 61 layers)",
        kv_70b_mqa["kib_per_token"] == 40.0
        and kv_70b_mqa["reduction_factor_vs_mha"] == 64.0
        and kv_deepseek_mla["elements_per_layer"] == 576
        and kv_deepseek_mla["equivalent_gqa_groups"] == 2.25
        and kv_deepseek_mla["bytes_per_token"] == 70272,
    )

    # 13. PagedAttention Waste Reduction & Block Allocation (`V12` Ch. 6 & 8)
    # 500 actual tokens out of 4096 max_seq_len with block_size=16
    cap_500 = evaluate_paged_attention_and_capacity(
        vram_per_gpu_gb=80.0,
        tp_size=4,
        model_params_billions=70.0,
        weight_bytes_per_param=2.0,
        kv_bytes_per_token=327680,
        avg_seq_len=500,
        gpu_memory_utilization=0.90,
        workspace_per_gpu_gb=2.0,
        block_size=16,
        max_seq_len=4096,
    )
    check(
        "14. For a 500-token sequence (S_max=4096, block_size=16), contiguous reservation wastes 87.79% (> 87%) whereas PagedAttention bounds internal fragmentation to <= 3.0% (< 3.2%) and external fragmentation to 0%",
        cap_500["contiguous_waste_pct"] == 87.79
        and cap_500["max_internal_frag_pct"] == 3.0
        and cap_500["external_frag_pct"] == 0.0
        and math.ceil(24000 / 16) == 1500,
    )

    # 14. Concurrency Capacity Matrix (`C_max`) on 4x and 8x 80GB GPUs (`V12` Ch. 8)
    cap_tp4_2k = evaluate_paged_attention_and_capacity(80.0, 4, 70.0, 2.0, 327680, 2048, 0.90, 2.0)
    cap_tp4_8k = evaluate_paged_attention_and_capacity(80.0, 4, 70.0, 2.0, 327680, 8192, 0.90, 2.0)
    cap_tp4_32k = evaluate_paged_attention_and_capacity(80.0, 4, 70.0, 2.0, 327680, 32768, 0.90, 2.0)
    cap_tp8_2k = evaluate_paged_attention_and_capacity(80.0, 8, 70.0, 2.0, 327680, 2048, 0.90, 1.0)
    cap_tp8_8k = evaluate_paged_attention_and_capacity(80.0, 8, 70.0, 2.0, 327680, 8192, 0.90, 1.0)
    cap_tp8_32k = evaluate_paged_attention_and_capacity(80.0, 8, 70.0, 2.0, 327680, 32768, 0.90, 1.0)
    check(
        "15. Llama-3-70B capacity matrix matches V12 Ch. 8: TP=4 (140 GB KV pool) supports 218 (S=2048), 54 (S=8192), 13 (S=32768) requests; TP=8 (428 GB KV pool) supports 668, 167, 41 requests",
        cap_tp4_2k["vram_kv_pool_gb"] == 140.0
        and (cap_tp4_2k["c_max"], cap_tp4_8k["c_max"], cap_tp4_32k["c_max"]) == (218, 54, 13)
        and cap_tp8_2k["vram_kv_pool_gb"] == 428.0
        and (cap_tp8_2k["c_max"], cap_tp8_8k["c_max"], cap_tp8_32k["c_max"]) == (668, 167, 41),
    )

    # 15. vLLM Startup Memory Profiling Breakdown (`GAK` Ch. 4 Example 4-3)
    # 79.14 GiB * 0.90 = 71.226 GiB (logged as 71.22 GiB); 71.226 - 14.99 - 0.12 - 1.19 = 54.926 GiB (logged as 54.93 GiB)
    vllm_usable_gib = round(79.14 * 0.90, 3)
    vllm_kv_gib = round(vllm_usable_gib - 14.99 - 0.12 - 1.19, 2)
    check(
        "16. vLLM startup profiling on a 79.14 GiB GPU at 0.90 utilization yields 71.226 GiB (~71.22 GiB) usable and 54.93 GiB for KV cache after 14.99 GiB weights, 0.12 GiB non-torch, and 1.19 GiB peak activations",
        vllm_usable_gib == 71.226 and vllm_kv_gib == 54.93,
    )

    # 16. Preemption Policies: Swap vs Recompute Crossover (`V12` Ch. 7)
    preempt_4k = compare_swap_vs_recompute_preemption(seq_len=4096)
    preempt_64k = compare_swap_vs_recompute_preemption(seq_len=65536)
    # Also check 4 GB KV swap time over 64 GB/s PCIe Gen4: 4 GB / 64 GB/s = 62.5 ms (~62 ms)
    four_gb_swap_ms = round((4.0 / 64.0) * 1000.0, 1)
    check(
        "17. Transferring 4 GB over 64 GB/s PCIe Gen4 takes 62.5 ms (~62 ms); on 8x H100, Recompute is faster than PCIe Swap at S=4096 (recommended='recompute') while Swap wins at ultra-long S=65536",
        four_gb_swap_ms == 62.5
        and preempt_4k["recommended_policy"] == "recompute"
        and preempt_64k["recommended_policy"] == "swap",
    )

    # 17. Rounding & Clamping Error + Symmetric Absmax vs Asymmetric Zero-Point (`HLS` Ch. 6 & `LEH` Ch. 8)
    rounding_err_7_6 = round(8.0 - 7.6, 2)
    clamped_1000_fp8 = min(448.0, max(-448.0, 1000.0))
    q_demo = quantize_absmax_and_zeropoint([-3.0, 0.1, 3.2])
    check(
        "18. Rounding 7.6 -> 8 gives error 0.4 and clamping 1000 -> 448 in FP8 E4M3; on [-3.0, 0.1, 3.2], absmax maps 0.1 -> 4 (scale=39.6875, dequant=0.1008) while zero-point maps 0.1 -> -1 (scale=41.129, zp=-5, dequant=0.0973)",
        rounding_err_7_6 == 0.4
        and clamped_1000_fp8 == 448.0
        and q_demo["scale_absmax"] == 39.6875
        and q_demo["q_absmax"][1] == 4
        and q_demo["deq_absmax"][1] == 0.1008
        and q_demo["scale_zp"] == 41.129
        and q_demo["zero_point"] == -5
        and q_demo["q_zp"][1] == -1,
    )

    # 18. SmoothQuant (`W8A8`) Outlier Migration (`V12` Ch. 5 & `GAK` Ch. 4)
    # Channel 0 has an extreme activation outlier (100.0 vs 1.0) while weights are uniform (1.0, 1.0)
    sq_half = compute_smoothquant_scales([100.0, 1.0], [1.0, 1.0], alpha=0.5)
    sq_08 = compute_smoothquant_scales([100.0, 1.0], [1.0, 1.0], alpha=0.8)
    check(
        "19. SmoothQuant migrates a 100x activation outlier channel: at alpha=0.5, s=[10.0, 1.0] reduces activation peak ratio from 100x to 10x and equalizes X_hat_max == W_hat_max == 10.0; at alpha=0.8, s_0 = 39.8107",
        sq_half["raw_act_peak_ratio"] == 100.0
        and sq_half["scales"] == [10.0, 1.0]
        and sq_half["smoothed_act_max"] == [10.0, 1.0]
        and sq_half["smoothed_weight_max"] == [10.0, 1.0]
        and sq_half["smoothed_act_peak_ratio"] == 10.0
        and round(sq_08["scales"][0], 2) == 39.81,
    )

    # 19. Number Format Bit Allocations (`HLS` Ch. 6 Tables 6-1, 6-4 & `V12` Ch. 4)
    q_info = evaluate_quantization_formats_and_models()
    fmts = q_info["formats"]
    check(
        "20. Floating-point bit allocations match IEEE/NVIDIA specs: FP32 (1/8/23), FP16 (1/5/10), BF16 (1/8/7), FP8 E4M3 (1/4/3, max 448), FP8 E5M2 (1/5/2, max 57344), and NVFP4 E2M1 (1/2/1, 0.5 B)",
        (fmts["FP32"]["sign"], fmts["FP32"]["exponent"], fmts["FP32"]["mantissa"]) == (1, 8, 23)
        and (fmts["FP16"]["sign"], fmts["FP16"]["exponent"], fmts["FP16"]["mantissa"]) == (1, 5, 10)
        and (fmts["BF16"]["sign"], fmts["BF16"]["exponent"], fmts["BF16"]["mantissa"]) == (1, 8, 7)
        and (fmts["FP8_E4M3"]["sign"], fmts["FP8_E4M3"]["exponent"], fmts["FP8_E4M3"]["mantissa"]) == (1, 4, 3)
        and (fmts["FP8_E5M2"]["sign"], fmts["FP8_E5M2"]["exponent"], fmts["FP8_E5M2"]["mantissa"]) == (1, 5, 2)
        and (fmts["NVFP4_E2M1"]["sign"], fmts["NVFP4_E2M1"]["exponent"], fmts["NVFP4_E2M1"]["mantissa"]) == (1, 2, 1),
    )

    # 20. Model Footprint Compression: W4A16 (75%), W8A8 (50%), and MXFP4/NVFP4 QAT (`HLS` Ch. 6)
    mdls = q_info["models"]
    check(
        "21. Quantization shrinks 7B weights from 14.0 GB (FP16) to 7.0 GB (W8A8, 50% reduction) and 3.5 GB (W4A16, 75% reduction), and fits gpt-oss-120b (117B * 0.5 B = 58.5 GB) on 1x 80 GB GPU and gpt-oss-20b (21B * 0.5 B = 10.5 GB) on 16 GB edge",
        mdls["Llama-2-7B_FP16"]["weight_gb"] == 14.0
        and mdls["Llama-2-7B_INT8"]["weight_gb"] == 7.0
        and mdls["Llama-2-7B_W4A16"]["weight_gb"] == 3.5
        and mdls["gpt-oss-120b_MXFP4"]["weight_gb"] == 58.5
        and mdls["gpt-oss-120b_MXFP4"]["fits_single_80gb_gpu"] is True
        and mdls["gpt-oss-20b_MXFP4"]["weight_gb"] == 10.5
        and mdls["gpt-oss-20b_MXFP4"]["fits_single_16gb_edge"] is True,
    )

    # 21. FP8 Quantized KV Cache & Block Size Tuning (`V12` Ch. 5 Scenario 2)
    kv_70b_fp16_4k = compute_kv_cache_footprint("GQA", 80, 64, 8, 128, bytes_per_element=2.0, seq_len=4096, batch_size=1)
    kv_70b_fp8_4k = compute_kv_cache_footprint("GQA", 80, 64, 8, 128, bytes_per_element=1.0, seq_len=4096, batch_size=1)
    # 129-token sequence with block_size=128 allocates 256 tokens (127 wasted = 49.61% waste) vs block_size=32 allocates 160 tokens (31 wasted = 19.38% waste)
    waste_block_128 = round(((256 - 129) / 256) * 100.0, 2)
    waste_block_32 = round(((160 - 129) / 160) * 100.0, 2)
    check(
        "22. FP8 KV cache cuts Llama-3-70B 4K sequence footprint in half (1.34 GB / 1.25 GiB -> 0.67 GB / 0.625 GiB), while shrinking block size from 128 to 32 tokens on a 129-token prompt cuts block waste from 49.61% to 19.38%",
        round(kv_70b_fp16_4k["total_gb_decimal"], 2) == 1.34
        and round(kv_70b_fp8_4k["total_gb_decimal"], 2) == 0.67
        and kv_70b_fp8_4k["total_gib"] == 0.625
        and waste_block_128 == 49.61
        and waste_block_32 == 19.38,
    )

    # 22. Multi-LoRA Serving Memory Math (`AIE` Ch. 7 & `VL5` Ch. 2)
    base_matrix_params = 4096 * 4096  # 16,777,216 (~16.8M)
    lora_r8_params = 4096 * 8 * 2  # 65,536
    merged_100_models = 100 * base_matrix_params  # 1,677,721,600 (~1.68B)
    unmerged_100_loras = base_matrix_params + 100 * lora_r8_params  # 23,330,816 (~23.3M)
    check(
        "23. Serving 100 rank-8 LoRA adapters on a 4096x4096 matrix requires 23.33M parameters (16.78M base + 100 x 65,536) instead of 1.68B parameters for 100 merged models (71.9x reduction)",
        lora_r8_params == 65536
        and round(merged_100_models / 1e9, 2) == 1.68
        and round(unmerged_100_loras / 1e6, 1) == 23.3,
    )

    # 23. RAG vs Long-Context CAG Token & Cost Math (`HLS` Ch. 7 Table 7-2)
    rag_cost = (500 * 0.125 + 5500 * 1.25) / 1e6  # $0.0069375 (~$0.007)
    cag_cost = (500 * 0.125 + 100500 * 0.125) / 1e6  # $0.012625 (~$0.013)
    check(
        "24. RAG (500 cached + 5,500 uncached tokens) costs $0.0069 (~$0.007) per request vs CAG (100,500 cached + 500 uncached) at $0.0126 (~$0.013), while CAG cuts uncached prefill tokens by 11x (5,500 -> 500, TTFT 5.0 s -> 0.5 s)",
        round(rag_cost, 3) == 0.007 and round(cag_cost, 3) == 0.013 and (5500 // 500) == 11,
    )

    # 24. End-to-End Latency, Goodput & KV Cache Enabling Speedup (`HLS` Ch. 2 & 4, `AIE` Ch. 9)
    # E2E = TTFT + ITL * (N - 1); 100 tokens without KV cache = 9.1205 s vs with KV cache = 3.1416 s (2.90x speedup)
    e2e_ms = 180.0 + 20.0 * (100 - 1)  # 2,160 ms
    kv_speedup = round(9.1205 / 3.1416, 2)
    goodput_rpm = 30  # 30 out of 100 RPM satisfying TTFT <= 200 ms and TPOT <= 100 ms
    check(
        "25. Enabling the KV cache speeds up 100-token generation from 9.1205 s to 3.1416 s (2.90x); E2E = TTFT + ITL * (N - 1) yields 2,160 ms for TTFT=180 ms, ITL=20 ms, N=100, and Goodput filters 100 RPM to 30 SLO-compliant RPM",
        e2e_ms == 2160.0 and kv_speedup == 2.90 and goodput_rpm == 30,
    )

    failed = total - passed
    print(f"Summary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
