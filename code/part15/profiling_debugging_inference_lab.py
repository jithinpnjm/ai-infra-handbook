#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.13:
Profiling, debugging and tuning inference at scale.

Runs 28 deterministic self-checks across all six chapter domains and prints:
`Summary: 28 passed, 0 failed`
"""

from __future__ import annotations
import sys
from profiling_debugging_inference import (
    evaluate_nvtx_kineto_and_ncu_profile,
    evaluate_dcgm_prometheus_alerts,
    compute_prefill_decode_roofline,
    evaluate_chunked_prefill_and_latency_aware_scheduling,
    evaluate_cpu_gil_and_pipeline_bottlenecks,
    diagnose_kv_cache_preemption_and_allocator,
    diagnose_nccl_cuda_graph_and_xid_faults,
    evaluate_quantization_and_app_optimizations,
)


def run_lab() -> int:
    print("=== Chapter 15.13 Lab: Profiling, Debugging, and Tuning Inference at Scale ===")
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
    # 1. 3-Layer Profiling Funnel: NVTX CUPTI Projection, Kineto, NCU & Linux perf
    # -----------------------------------------------------------------------
    prof = evaluate_nvtx_kineto_and_ncu_profile()
    check(
        "1. PyTorch Kineto Table 13-2 top ops: aten::matmul = 43.00 ms (128 calls), aten::linear = 35.50 ms (64 calls), GEMM total = 78.50 ms",
        prof["kineto_top_ops"][0] == ("aten::matmul", 43.00, 128)
        and prof["kineto_top_ops"][1] == ("aten::linear", 35.50, 64)
        and prof["gemm_total_ms"] == 78.50,
    )
    check(
        "2. PyTorch Kineto Table 13-2 MoE dispatch (18.70 ms, 2 calls) + combine (12.10 ms, 2 calls) = 30.80 ms total",
        prof["kineto_top_ops"][2] == ("dispatch", 18.70, 2)
        and prof["kineto_top_ops"][3] == ("combine", 12.10, 2)
        and prof["moe_comm_total_ms"] == 30.80,
    )
    check(
        "3. Nsight Systems CUPTI GPU projection (Table 13-3): train_step = 138.0 ms (60.5 ms forward + 58.3 ms backward + 19.2 ms optimizer_step)",
        prof["nvtx_projection"]["train_step"]["gpu_ms"] == 138.0
        and prof["nvtx_subrange_sum_ms"] == 138.0
        and prof["nvtx_prefill_color_argb"] == "0xFF4F86F7"
        and prof["nvtx_decode_color_argb"] == "0xFFFF8C00",
    )
    check(
        "4. Nsight Compute Roofline (Table 13-4): baseline 50% FLOPS / 70% BW / 60% occ (memory_bound) -> optimized 85% FLOPS / 40% BW / 80% occ (compute_bound)",
        prof["ncu_roofline"]["baseline"]["pct_peak_flops"] == 50
        and prof["ncu_roofline"]["baseline"]["pct_peak_dram_bw"] == 70
        and prof["ncu_roofline"]["optimized"]["pct_peak_flops"] == 85
        and prof["ncu_roofline"]["optimized"]["pct_peak_dram_bw"] == 40
        and prof["ncu_roofline"]["optimized"]["achieved_occupancy_pct"] == 80,
    )
    check(
        "5. Linux perf on Grace-Blackwell: 1.58 IPC vs 8.0 max IPC; call-graph hotspots 45.0% py::forward, 20.5% aten::matmul, 10.2% dataloader, 8.7% ncclAllReduce, 5.3% read",
        prof["linux_perf"]["measured_ipc"] == 1.58
        and prof["linux_perf"]["grace_neoverse_v2_max_ipc"] == 8.0
        and prof["linux_perf"]["call_graph_hotspots_pct"]["py::forward"] == 45.0
        and prof["linux_perf"]["call_graph_hotspots_pct"]["ncclAllReduce"] == 8.7,
    )

    alerts = evaluate_dcgm_prometheus_alerts()
    check(
        "6. Prometheus Alertmanager Table 16-3: Idle < 10% for > 60 s, Bottleneck > 90%, Memory 80%/95%, Temp 85C/95C, NVLink CRC > 100/s, ECC >= 1",
        alerts["gpu_util_idle"]["threshold_pct"] == 10
        and alerts["gpu_util_idle"]["duration_s"] == 60
        and alerts["memory_warning"]["threshold_pct"] == 80
        and alerts["memory_critical"]["threshold_pct"] == 95
        and alerts["temp_warning_c"]["threshold_c"] == 85
        and alerts["temp_critical_c"]["threshold_c"] == 95
        and alerts["nvlink_crc_errors_per_s"]["threshold_rate"] == 100
        and alerts["uncorrectable_ecc_errors"]["min_count"] == 1,
    )

    # -----------------------------------------------------------------------
    # 2. Diagnosing TTFT Spikes vs ITL/TPOT Stalls & Latency-Aware Scheduling
    # -----------------------------------------------------------------------
    rf64 = compute_prefill_decode_roofline(seq_len=64, hidden_dim=4096)
    rf512 = compute_prefill_decode_roofline(seq_len=512, hidden_dim=4096)
    rf4096 = compute_prefill_decode_roofline(seq_len=4096, hidden_dim=4096)
    check(
        "7. HLS Table 5-10 Roofline on L40S (ridge ~419 FLOPS/B): prefill AI = 62.06 (s=64), 409.60 (s=512), 1365.33 (s=4096) vs decode ~1.0 FLOPS/B",
        rf64["prefill_ai_flops_per_byte"] == 62.06
        and rf512["prefill_ai_flops_per_byte"] == 409.60
        and rf4096["prefill_ai_flops_per_byte"] == 1365.33
        and round(rf4096["decode_ai_flops_per_byte"], 1) == 1.0,
    )

    sched = evaluate_chunked_prefill_and_latency_aware_scheduling()
    check(
        "8. ASP Table 16-5 20K chunked prefill into 4 x 5K chunks: attention ops [12.5M, 37.5M, 62.5M, 87.5M] sum to 200M (exact T(20K) = 200,010,000) and 20K MLP tokens",
        sched["chunk_ops_approx"] == [12_500_000, 37_500_000, 62_500_000, 87_500_000]
        and sched["chunk_ops_sum"] == 200_000_000
        and sched["exact_triangular_total"] == 200_010_000
        and sched["total_mlp_tokens"] == 20_000,
    )
    check(
        "9. ASP Tables 16-6 & 16-7 FIFO [6K, 2K, 6K] (38,007,000 ops, 14K tokens) vs Latency-Aware [2K, 2K, 6K] (22,005,000 ops, 10K tokens) cuts critical path by 42.10%",
        sched["fifo_gpu1_ops"] == 38_007_000
        and sched["fifo_gpu2_ops"] == 6_003_000
        and sched["latency_aware_gpu1_ops"] == 22_005_000
        and sched["critical_path_reduction_pct"] == 42.10,
    )
    check(
        "10. V12 Ch. 7 12,288-token prefill burst: unfixed p99 ITL = 340.0 ms -> chunked (2,048) = 21.4 ms vs over-chunked (512) = 450 switches/s, 45.0 ms ITL, 320.0 ms TTFT",
        sched["v12_unfixed_p99_itl_ms"] == 340.0
        and sched["v12_chunked_2048_p99_itl_ms"] == 21.4
        and sched["v12_overchunked_512_switches_per_s"] == 450
        and sched["v12_overchunked_512_p99_itl_ms"] == 45.0
        and sched["v12_overchunked_512_ttft_ms"] == 320.0,
    )

    # -----------------------------------------------------------------------
    # 3. Host CPU Scheduling Overhead, GIL Bottlenecks & Streaming I/O Stalls
    # -----------------------------------------------------------------------
    cpu = evaluate_cpu_gil_and_pipeline_bottlenecks()
    check(
        "11. V12 Lab 04 unfixed single-threaded CPU pipeline: 14.85 s (13.47 RPS), total p99 = 1,410.20 ms (CPU p99 = 1,395.80 ms vs Triton GPU p99 = 18.10 ms)",
        cpu["lab04_unfixed"]["throughput_rps"] == 13.47
        and cpu["lab04_unfixed"]["total_p99_ms"] == 1410.20
        and cpu["lab04_unfixed"]["cpu_p99_ms"] == 1395.80
        and cpu["lab04_unfixed"]["triton_p99_ms"] == 18.10,
    )
    check(
        "12. V12 Lab 04 ProcessPoolExecutor fix: 1.92 s (104.17 RPS, 7.73x gain), total p99 = 44.80 ms (31.48x reduction); --cpus=0.5 CFS throttle spikes p99 > 3,500 ms",
        cpu["lab04_fixed"]["throughput_rps"] == 104.17
        and cpu["lab04_fixed"]["total_p99_ms"] == 44.80
        and cpu["lab04_rps_gain_x"] == 7.73
        and cpu["lab04_p99_reduction_x"] == 31.48
        and cpu["cfs_throttled_0_5_cpu_p99_ms"] == 3500.0,
    )
    check(
        "13. V12 Ch. 2 Python GIL BPE tokenizer: 320.0 ms (77.1% of 415.0 ms) at 120 RPS -> 16-thread Rust tokenizer 1.4 ms (228.6x faster) and 780 RPS (6.5x gain)",
        cpu["gil_share_pct"] == 77.1
        and cpu["tokenizer_speedup_x"] == 228.6
        and cpu["gil_rps_gain_x"] == 6.50
        and cpu["vllm_v1_image_pad_tokens"] == 644,
    )
    check(
        "14. PCIe Gen5 H2D pinned (58.5 GB/s) vs pageable (12.0 GB/s) = 4.88x speedup; SSE 5-token flush at 20 tok/s delivers first chunk in 0.25 s vs 5.0 s wait",
        cpu["pcie_pinned_speedup_x"] == 4.88
        and cpu["streaming_first_batch_s"] == 0.25
        and cpu["non_streaming_wait_s"] == 5.0
        and cpu["nagle_delayed_ack_worst_ms"] == 200.0
        and cpu["nginx_buffer_stall_ms"] == 600.0,
    )

    # -----------------------------------------------------------------------
    # 4. KV Cache Thrashing, Preemption Debugging & Allocator Fragmentation
    # -----------------------------------------------------------------------
    kv = diagnose_kv_cache_preemption_and_allocator()
    check(
        "15. Llama-3-70B GQA KV cache = 327,680 B/tok (320 KiB) in FP16 and 163,840 B/tok (160 KiB) in FP8",
        kv["llama70b_fp16_bytes_per_tok"] == 327680
        and kv["llama70b_fp8_bytes_per_tok"] == 163840,
    )
    check(
        "16. PCIe Gen4 (64 GB/s) 4 GB KV swap takes 62.5 ms one-way / 125.0 ms round-trip, spiking p99 ITL from 20.0 ms to 850.0 ms (42.5x); recompute wins for S < 8,192",
        kv["one_way_swap_ms"] == 62.5
        and kv["round_trip_swap_ms"] == 125.0
        and kv["swap_itl_inflation_x"] == 42.5
        and kv["recompute_crossover_seq_len"] == 8192,
    )
    check(
        "17. PagedAttention cuts KV fragmentation from 20%-30% (unpaged) to < 4% (32 blocks / 12 wasted slots at S=500, B=16); prefix cache gives 10x speedup on 10 queries",
        kv["unpaged_fragmentation_pct_range"] == (20, 30)
        and kv["paged_max_waste_pct"] == 4.0
        and kv["seq_500_blocks"] == 32
        and kv["seq_500_wasted_slots"] == 12
        and kv["prefix_cache_10q_speedup_x"] == 10.0,
    )
    check(
        "18. PyTorch caching allocator roundup_power2_divisions:[256:1,512:2,1024:4,>:8] with max_split_size_mb:256 rounds a 600 MB request to 768 MB",
        kv["max_split_size_mb"] == 256
        and kv["alloc_request_mb"] == 600
        and kv["rounded_alloc_mb"] == 768,
    )

    # -----------------------------------------------------------------------
    # 5. Multi-GPU NCCL AllReduce Tail Latency, CUDA Graph Bugs & XID/Probe Triage
    # -----------------------------------------------------------------------
    nccl = diagnose_nccl_cuda_graph_and_xid_faults()
    check(
        "19. 80-layer Llama-3-70B TP=8 executes 160 AllReduces/token (8,000/s at 50 tok/s) across 14 ring steps moving 28,672 B per call for B=1, H=8192 FP16",
        nccl["allreduces_per_token"] == 160
        and nccl["allreduces_per_sec_at_50tok_s"] == 8000
        and nccl["ring_steps_per_allreduce"] == 14
        and nccl["per_call_bytes"] == 28672,
    )
    check(
        "20. TensorRT-LLM TP=8 over NVSwitch cuts ITL from 115.0 ms to 18.4 ms (6.25x); degraded RoCEv2 link (TX_DROPPED: 428, RX_ERRORS: 156) stalls AllReduce to 45,000 us",
        nccl["nvswitch_tp8_itl_ms"] == 18.4
        and nccl["naive_tp8_itl_ms"] == 115.0
        and nccl["tp8_speedup_x"] == 6.25
        and nccl["degraded_roce_allreduce_us"] == 45000
        and nccl["degraded_roce_tx_dropped"] == 428
        and nccl["degraded_roce_rx_errors"] == 156,
    )
    check(
        "21. MoE AllToAll > 5.0 ms straggler mitigation: capacity factor CF = 1.2 to 1.5 expands 32-token base cap to 38-48 tokens; SHARP adds 10%-20% throughput",
        nccl["moe_alltoall_outlier_threshold_ms"] == 5.0
        and nccl["cf_1_2_cap"] == 38
        and nccl["cf_1_5_cap"] == 48
        and nccl["sharp_alltoall_gain_pct_range"] == (10, 20),
    )
    check(
        "22. V12 Ch. 11 Zombie Pod XID 62 DB-ECC deadlock blackholes 12.5% (1/8) of requests; startupProbe allows 60 * 10 s = 600 s and readinessProbe uses 5 s timeout",
        nccl["xid_db_ecc_code"] == 62
        and nccl["blackhole_traffic_pct"] == 12.5
        and nccl["max_startup_window_s"] == 600
        and nccl["readiness_timeout_s"] == 5
        and nccl["nfs_stall_latency_s"] == 1.2,
    )

    # -----------------------------------------------------------------------
    # 6. Full-Stack Quantization (`FP8`, `NVFP4`, `GPTQ`, `AWQ`, `W4A8`) & App Tuning
    # -----------------------------------------------------------------------
    quant = evaluate_quantization_and_app_optimizations()
    check(
        "23. Quantization tiers: FP8 (0.50x mem, 1.5x speed), GPTQ/AWQ W4A16 (0.25x mem, ~2.0x speed, 99%+ acc), W4A8 INT4+FP8 (0.25x mem, 1.8x speed), NVFP4 Block-32 (1.8x vs FP8, 3.5x vs FP16)",
        quant["quant_formats"]["FP8"]["memory_ratio"] == 0.50
        and quant["quant_formats"]["GPTQ_AWQ_W4A16"]["speedup_x"] == 2.0
        and quant["quant_formats"]["W4A8_INT4_FP8"]["speedup_x"] == 1.8
        and quant["quant_formats"]["NVFP4_Block32"]["vs_fp8_reduction_x"] == 1.8
        and quant["quant_formats"]["NVFP4_Block32"]["vs_fp16_reduction_x"] == 3.5,
    )
    check(
        "24. PTQ calibration uses 1,000 representative prompts and SmoothQuant W8A8 preserves accuracy within < 1.0% loss",
        quant["ptq_calibration_prompts"] == 1000
        and quant["smoothquant_max_loss_pct"] == 1.0,
    )
    check(
        "25. Prompt compression at 75% context threshold (12,000 / 16,000) summarizes oldest 25% (3,000 -> 300 tokens), cutting active prompt to 9,300 tokens and saving 39.94% triangular attention",
        quant["trigger_tokens"] == 12000
        and quant["compressed_triggered"] is True
        and quant["oldest_25pct_tokens"] == 3000
        and quant["new_prompt_tokens"] == 9300
        and quant["attention_saved_pct"] == 39.94,
    )
    check(
        "26. Config token compression replaces a 200-token system prompt with 10 special tokens (20.0x reduction)",
        quant["config_token_reduction_x"] == 20.0,
    )
    check(
        "27. Model cascade (70B 50 ms / 1x cost + 700B 500 ms / 10x cost at 60% share): expected latency = 230.0 ms (260.0 ms with 10% fallback), cost = 4.6 (5.2 with fallback, up to 5.0x savings)",
        quant["no_fallback_lat_ms"] == 230.0
        and quant["no_fallback_cost"] == 4.6
        and quant["with_fallback_lat_ms"] == 260.0
        and quant["with_fallback_cost"] == 5.2
        and quant["max_cascade_cost_reduction_x"] == 5.0,
    )
    check(
        "28. Production guardrails: 90% peak-throughput headroom buffer (scaling batch 16 -> 8), 10%-15% warm spares (100% critical), 2-5 ms debouncing, 4,096 max tokens, 30 s timeout",
        quant["headroom_target_pct"] == 90
        and quant["batch_scale_back"] == (16, 8)
        and quant["warm_spare_buffer_pct_range"] == (10, 15)
        and quant["critical_spare_buffer_pct"] == 100
        and quant["debounce_interval_ms_range"] == (2, 5)
        and quant["max_output_tokens_limit"] == 4096
        and quant["server_timeout_s"] == 30,
    )

    failed = total - passed
    print(f"Summary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
