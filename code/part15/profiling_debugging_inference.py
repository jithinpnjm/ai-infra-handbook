#!/usr/bin/env python3
"""Deterministic models and diagnostic calculators for Chapter 15.13:
Profiling, debugging and tuning inference at scale.

Covers:
1. 3-Layer Inference Profiling Funnel (`Serving -> Framework -> Runtime`),
   Nsight Systems (`nsys`) NVTX CUPTI GPU projection (`Table 13-3`),
   PyTorch Profiler (`Kineto` `Table 13-2`), Nsight Compute (`ncu` Roofline
   `Table 13-4` & CUDA PC Sampling), Linux `perf` on Grace-Blackwell (`1.58` IPC
   vs `8.0` max), and DCGM / Prometheus Alertmanager rules (`Table 16-3`).
2. Diagnosing TTFT spikes vs ITL/TPOT stalls: Prefill vs Decode Roofline
   arithmetic intensity (`HLS` `Tables 5-8..5-10`), colocated prefill blocking
   (`12,288` tokens spiking `p99 ITL` `18.0 ms -> 340.0 ms`, fixed to `21.4 ms`
   at chunk size `2,048` vs `512` over-chunking `450` switches/s), `20K` chunked
   prefill triangular attention math (`ASP` `Table 16-5`: `T(N) = N(N+1)/2`),
   and FIFO vs Latency-Aware scheduling (`ASP` `Tables 16-6 & 16-7`: `38,007,000`
   vs `22,005,000` QK ops, `42.10%` critical-path reduction).
3. Host CPU scheduling overhead, Python GIL bottlenecks, and streaming I/O stalls:
   Volume 12 `Lab 04` single-threaded preprocessing (`13.47 RPS`, `1,410.20 ms`
   `p99` -> `ProcessPoolExecutor` `104.17 RPS`, `44.80 ms` `p99`, and `--cpus=0.5`
   CFS throttling `> 3,500 ms`), Python GIL (`320.0 ms` / `77.1%` -> 16-thread
   Rust tokenizer `1.4 ms`, `120 -> 780 RPS`), `vLLM` V1 Process 0 / Process 1
   decoupling (`644` `<|image_pad|>` tokens), pageable (`12.0 GB/s`) vs pinned
   (`58.5 GB/s`) PCIe Gen5 H2D, and SSE `TCP_NODELAY` streaming (`4-7` tok/s
   human reading, `5 tok / 20 tok/s = 0.25 s` first chunk vs `5.0 s`).
4. KV cache thrashing, preemption debugging (`PreemptionMode.RECOMPUTE` vs PCIe
   `Swap` `125.0 ms` round-trip / `850.0 ms` ITL), prefix cache hit rate
   (`10x` shared document speedup, `< 60%` alert, SGLang RadixAttention LRU
   eviction), unpaged (`20%-30%`) vs PagedAttention (`< 4%`, `3.2%` at `500`
   tokens) fragmentation, and PyTorch caching allocator (`PYTORCH_CUDA_ALLOC_CONF`
   rounding `600 MB -> 768 MB` and `expandable_segments:True`).
5. Multi-GPU / Multi-node NCCL AllReduce tail latency (`160` AllReduces/token
   on `80`-layer `Llama-3-70B`, `18.4 ms` NVSwitch vs `115.0 ms` naive, `45.0 ms`
   degraded RoCEv2 link with `TX_DROPPED: 428, RX_ERRORS: 156`, MoE `CF = 1.2-1.5`
   and SHARP `10%-20%` gain), CUDA Graph capture/replay bugs, and Zombie Pod
   `XID 62` (`12.5%` traffic blackhole) + Kubernetes probe separation (`600 s`
   startup, `5 s` `/health` readiness vs `1 s` NFS storm, `/ping` liveness).
6. Full-stack quantization (`FP8`, `NVFP4` `32`-element block microscaling `1.8x`
   vs FP8 / `3.5x` vs FP16, `GPTQ` `99%+` / `2x` speed / `4x` size, `AWQ`,
   `SmoothQuant` `< 1%` loss, `W4A8` fused quant-dequant) and application-level
   tuning (prompt compression `75%` -> summarize `25%`, `200 -> 10` config tokens,
   `70B/700B` cascade `230.0 ms` / `5.0x` cost savings, `90%` headroom buffer,
   `10%-15%` warm spares, `2-5 ms` debouncing, `4,096`-token / `30 s` timeout).
"""

from __future__ import annotations
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. 3-Layer Profiling Funnel: NVTX CUPTI Projection, Kineto, NCU & Linux perf
# ---------------------------------------------------------------------------

def evaluate_nvtx_kineto_and_ncu_profile() -> Dict[str, object]:
    """Return exact profiling breakdowns from `ASP` Ch. 13 & Ch. 16.

    - Table 13-2 (`torch.profiler` Kineto top 10 CUDA ops on 64-expert MoE).
    - Table 13-3 (`nsys stats --report=nvtx_gpu_proj_sum` CUPTI projection).
    - Table 13-4 (`ncu` GEMM Roofline before and after optimization).
    - Linux `perf stat` and `perf record -F 2000 -g --call-graph dwarf` on Grace-Blackwell.
    """
    kineto_top_ops: List[Tuple[str, float, int]] = [
        ("aten::matmul", 43.00, 128),
        ("aten::linear", 35.50, 64),
        ("dispatch", 18.70, 2),
        ("combine", 12.10, 2),
        ("aten::layer_norm", 10.20, 16),
        ("aten::softmax", 5.70, 4),
        ("aten::scatter", 4.10, 16),
        ("aten::gather", 3.60, 16),
        ("aten::to", 2.90, 8),
        ("aten::add_", 2.20, 64),
    ]
    gemm_total_ms = round(43.00 + 35.50, 2)
    moe_comm_total_ms = round(18.70 + 12.10, 2)

    nvtx_projection = {
        "train_step": {"gpu_ms": 138.0, "self_ms": 0.0, "child_ms": 138.0, "instances": 1},
        "forward": {"gpu_ms": 60.5, "self_ms": 60.5, "child_ms": 0.0, "instances": 130},
        "backward": {"gpu_ms": 58.3, "self_ms": 58.3, "child_ms": 0.0, "instances": 130},
        "optimizer_step": {"gpu_ms": 19.2, "self_ms": 19.2, "child_ms": 0.0, "instances": 1},
    }
    subrange_sum_ms = round(
        nvtx_projection["forward"]["gpu_ms"]
        + nvtx_projection["backward"]["gpu_ms"]
        + nvtx_projection["optimizer_step"]["gpu_ms"],
        1,
    )

    ncu_roofline = {
        "baseline": {
            "pct_peak_flops": 50,
            "pct_peak_dram_bw": 70,
            "achieved_occupancy_pct": 60,
            "bound": "memory_bound",
        },
        "optimized": {
            "pct_peak_flops": 85,
            "pct_peak_dram_bw": 40,
            "achieved_occupancy_pct": 80,
            "bound": "compute_bound",
        },
    }

    linux_perf = {
        "cpus_utilized": 0.600,
        "task_clock_ms": 1200.345,
        "cycles": 2_400_567_890,
        "instructions": 3_800_123_456,
        "measured_ipc": 1.58,
        "grace_neoverse_v2_max_ipc": 8.0,
        "cache_miss_pct": 0.32,
        "branch_miss_pct": 0.12,
        "call_graph_hotspots_pct": {
            "py::forward": 45.0,
            "aten::matmul": 20.5,
            "dataloader_iter_next": 10.2,
            "ncclAllReduce": 8.7,
            "read": 5.3,
        },
    }

    return {
        "kineto_top_ops": kineto_top_ops,
        "gemm_total_ms": gemm_total_ms,
        "moe_comm_total_ms": moe_comm_total_ms,
        "nvtx_projection": nvtx_projection,
        "nvtx_subrange_sum_ms": subrange_sum_ms,
        "nvtx_prefill_color_argb": "0xFF4F86F7",
        "nvtx_decode_color_argb": "0xFFFF8C00",
        "ncu_roofline": ncu_roofline,
        "linux_perf": linux_perf,
    }


def evaluate_dcgm_prometheus_alerts() -> Dict[str, Dict[str, object]]:
    """Return the production Prometheus Alertmanager thresholds from `ASP` Table 16-3 & `V12`."""
    return {
        "gpu_util_idle": {"threshold_pct": 10, "duration_s": 60, "severity": "Idle"},
        "gpu_util_bottleneck": {"threshold_pct": 90, "severity": "Bottleneck"},
        "memory_warning": {"threshold_pct": 80, "severity": "Warning"},
        "memory_critical": {"threshold_pct": 95, "severity": "Critical"},
        "temp_warning_c": {"threshold_c": 85, "severity": "Warning"},
        "temp_critical_c": {"threshold_c": 95, "severity": "Critical"},
        "nvlink_replay_errors": {"min_count": 1, "severity": "Critical"},
        "nvlink_crc_errors_per_s": {"threshold_rate": 100, "severity": "Critical"},
        "pcie_replay_errors": {"min_count": 1, "severity": "Critical"},
        "uncorrectable_ecc_errors": {"min_count": 1, "severity": "Critical"},
    }


# ---------------------------------------------------------------------------
# 2. Diagnosing TTFT Spikes vs ITL/TPOT Stalls & Latency-Aware Scheduling
# ---------------------------------------------------------------------------

def compute_prefill_decode_roofline(
    seq_len: int,
    hidden_dim: int = 4096,
    gpu_tflops: float = 362.0,
    gpu_bw_gbs: float = 864.0,
) -> Dict[str, float | str]:
    """Compute prefill vs decode arithmetic intensity (`HLS` Ch. 5 Tables 5-8..5-10).

    Formula in `HLS` Ch. 5:
      AI = (s * h * h) / (s * h + s * h + h * h) = (s * h^2) / (2 * s * h + h^2)
    Ridge point on L40S: 362,000 / 864 = 418.98 (~419) FLOPS/Byte (H100 SXM: 989,500 / 3,350 = 295.4 FLOPS/Byte).
    """
    ridge_flops_per_byte = round((gpu_tflops * 1000.0) / gpu_bw_gbs, 2)
    h100_ridge_flops_per_byte = 295.4
    prefill_ai = round((seq_len * hidden_dim * hidden_dim) / (2.0 * seq_len * hidden_dim + hidden_dim * hidden_dim), 2)
    s_decode = 1
    decode_ai = round((s_decode * hidden_dim * hidden_dim) / (2.0 * s_decode * hidden_dim + hidden_dim * hidden_dim), 4)
    verdict = (
        "Compute-bound on prefill, Memory-bound on decode"
        if prefill_ai >= ridge_flops_per_byte
        else "Memory-bound for both prefill and decode"
    )
    return {
        "seq_len": seq_len,
        "hidden_dim": hidden_dim,
        "ridge_flops_per_byte": ridge_flops_per_byte,
        "prefill_ai_flops_per_byte": prefill_ai,
        "decode_ai_flops_per_byte": decode_ai,
        "verdict": verdict,
    }


def evaluate_chunked_prefill_and_latency_aware_scheduling(
    prompt_tokens: int = 20000,
    chunk_size: int = 5000,
    incoming_prompts_k: Sequence[int] = (6, 2, 6, 2, 2, 2),
) -> Dict[str, object]:
    """Model chunked prefill triangular attention (`ASP` Table 16-5) and FIFO vs
    Latency-Aware scheduling (`ASP` Tables 16-6 & 16-7), plus `V12` Ch. 7 stalls.
    """
    num_chunks = prompt_tokens // chunk_size
    exact_triangular_total = prompt_tokens * (prompt_tokens + 1) // 2
    approx_quadratic_total = (prompt_tokens * prompt_tokens) // 2

    # Per-chunk quadratic approximation from ASP Table 16-5:
    # Chunk k (1-indexed) attends over (k-1)*C prior tokens + C current tokens:
    # C*(k-1)*C + C^2/2 = (k - 0.5) * C^2
    chunk_ops_approx = [int((k - 0.5) * (chunk_size ** 2)) for k in range(1, num_chunks + 1)]
    total_mlp_tokens = num_chunks * chunk_size

    # FIFO vs Latency-Aware scheduling on 2 GPUs for [6K, 2K, 6K, 2K, 2K, 2K]
    def tri(n_tokens: int) -> int:
        return n_tokens * (n_tokens + 1) // 2

    prompts = [p * 1000 for p in incoming_prompts_k]
    fifo_gpu1 = prompts[:3]  # [6000, 2000, 6000]
    fifo_gpu2 = prompts[3:]  # [2000, 2000, 2000]
    fifo_gpu1_ops = sum(tri(n) for n in fifo_gpu1)  # 38,007,000
    fifo_gpu2_ops = sum(tri(n) for n in fifo_gpu2)  # 6,003,000
    fifo_critical_ops = max(fifo_gpu1_ops, fifo_gpu2_ops)

    # Latency-aware balanced batches: [2000, 2000, 6000] on each GPU
    la_gpu1 = [2000, 2000, 6000]
    la_gpu2 = [2000, 2000, 6000]
    la_gpu1_ops = sum(tri(n) for n in la_gpu1)  # 22,005,000
    la_gpu2_ops = sum(tri(n) for n in la_gpu2)  # 22,005,000
    la_critical_ops = max(la_gpu1_ops, la_gpu2_ops)
    critical_path_reduction_pct = round(
        ((fifo_critical_ops - la_critical_ops) / fifo_critical_ops) * 100.0, 2
    )

    return {
        "prompt_tokens": prompt_tokens,
        "chunk_size": chunk_size,
        "num_chunks": num_chunks,
        "exact_triangular_total": exact_triangular_total,
        "approx_quadratic_total": approx_quadratic_total,
        "chunk_ops_approx": chunk_ops_approx,
        "chunk_ops_sum": sum(chunk_ops_approx),
        "total_mlp_tokens": total_mlp_tokens,
        "fifo_gpu1_ops": fifo_gpu1_ops,
        "fifo_gpu2_ops": fifo_gpu2_ops,
        "fifo_gpu1_tokens": sum(fifo_gpu1),
        "fifo_gpu2_tokens": sum(fifo_gpu2),
        "latency_aware_gpu1_ops": la_gpu1_ops,
        "latency_aware_gpu2_ops": la_gpu2_ops,
        "latency_aware_tokens_per_gpu": sum(la_gpu1),
        "critical_path_reduction_pct": critical_path_reduction_pct,
        "v12_prefill_burst_tokens": 12288,
        "v12_unfixed_p99_itl_ms": 340.0,
        "v12_chunked_2048_p99_itl_ms": 21.4,
        "v12_overchunked_512_switches_per_s": 450,
        "v12_overchunked_512_p99_itl_ms": 45.0,
        "v12_overchunked_512_ttft_ms": 320.0,
    }


# ---------------------------------------------------------------------------
# 3. Host CPU Scheduling Overhead, GIL Bottlenecks & Streaming I/O Stalls
# ---------------------------------------------------------------------------

def evaluate_cpu_gil_and_pipeline_bottlenecks() -> Dict[str, object]:
    """Model Volume 12 Lab 04 CPU preprocessing incident, Ch. 2 Python GIL
    tokenization bottleneck, PCIe H2D staging, and SSE streaming flush math.
    """
    # Volume 12 Lab 04 (200 requests, concurrency = 8)
    lab04_unfixed = {
        "duration_s": 14.85,
        "throughput_rps": 13.47,
        "total_mean_ms": 585.40,
        "total_p95_ms": 1120.50,
        "total_p99_ms": 1410.20,
        "cpu_mean_ms": 572.10,
        "cpu_p95_ms": 1105.10,
        "cpu_p99_ms": 1395.80,
        "triton_mean_ms": 11.80,
        "triton_p95_ms": 14.20,
        "triton_p99_ms": 18.10,
    }
    lab04_fixed = {
        "duration_s": 1.92,
        "throughput_rps": 104.17,
        "total_mean_ms": 38.15,
        "total_p95_ms": 41.20,
        "total_p99_ms": 44.80,
        "cpu_mean_ms": 25.40,
        "cpu_p95_ms": 28.10,
        "cpu_p99_ms": 31.00,
        "triton_mean_ms": 11.20,
        "triton_p95_ms": 12.80,
        "triton_p99_ms": 13.50,
    }
    lab04_rps_gain_x = round(lab04_fixed["throughput_rps"] / lab04_unfixed["throughput_rps"], 2)
    lab04_p99_reduction_x = round(lab04_unfixed["total_p99_ms"] / lab04_fixed["total_p99_ms"], 2)

    # Volume 12 Ch. 2 Python GIL BPE tokenizer vs 16-thread Rust tokenizer
    gil_tokenization_ms = 320.0
    total_unfixed_req_ms = 415.0
    gil_share_pct = round((gil_tokenization_ms / total_unfixed_req_ms) * 100.0, 1)
    rust_tokenization_ms = 1.4
    tokenizer_speedup_x = round(gil_tokenization_ms / rust_tokenization_ms, 1)
    gil_rps_before = 120
    gil_rps_after = 780
    gil_rps_gain_x = round(gil_rps_after / gil_rps_before, 2)

    # PCIe Gen5 x16 (64 GB/s): Pageable (12.0 GB/s nominal) vs Pinned (58.5 GB/s nominal)
    pageable_bw_gbs = 12.0
    pinned_bw_gbs = 58.5
    pcie_pinned_speedup_x = round(pinned_bw_gbs / pageable_bw_gbs, 2)

    # Streaming response math (`ASP` Ch. 16): 100 tokens at 20 tok/s = 5.0 s total;
    # flushing every 5 tokens delivers first batch in 5 / 20 = 0.25 s.
    total_tokens = 100
    gen_rate_tok_s = 20.0
    flush_batch_tokens = 5
    non_streaming_wait_s = round(total_tokens / gen_rate_tok_s, 2)
    streaming_first_batch_s = round(flush_batch_tokens / gen_rate_tok_s, 2)

    return {
        "lab04_unfixed": lab04_unfixed,
        "lab04_fixed": lab04_fixed,
        "lab04_rps_gain_x": lab04_rps_gain_x,
        "lab04_p99_reduction_x": lab04_p99_reduction_x,
        "cfs_throttled_0_5_cpu_rps": 3.00,
        "cfs_throttled_0_5_cpu_p99_ms": 3500.00,
        "cfs_throttled_0_5_cpu_prep_ms": 3480.00,
        "gil_tokenization_ms": gil_tokenization_ms,
        "gil_share_pct": gil_share_pct,
        "rust_tokenization_ms": rust_tokenization_ms,
        "tokenizer_speedup_x": tokenizer_speedup_x,
        "gil_rps_before": gil_rps_before,
        "gil_rps_after": gil_rps_after,
        "gil_rps_gain_x": gil_rps_gain_x,
        "vllm_v1_image_pad_tokens": 644,
        "pageable_bw_gbs": pageable_bw_gbs,
        "pinned_bw_gbs": pinned_bw_gbs,
        "pcie_pinned_speedup_x": pcie_pinned_speedup_x,
        "human_reading_tok_s_range": (4, 13),
        "non_streaming_wait_s": non_streaming_wait_s,
        "streaming_first_batch_s": streaming_first_batch_s,
        "nagle_delayed_ack_worst_ms": 200.0,
        "nginx_buffer_stall_ms": 600.0,
        "backpressure_token_buffer_range": (50, 100),
    }


# ---------------------------------------------------------------------------
# 4. KV Cache Thrashing, Preemption Debugging & Allocator Fragmentation
# ---------------------------------------------------------------------------

def diagnose_kv_cache_preemption_and_allocator(
    kv_swap_gb: float = 4.0,
    pcie_bw_gbs: float = 64.0,
    alloc_request_mb: int = 600,
) -> Dict[str, object]:
    """Model KV cache sizing (`Llama-3-70B`), PCIe swap vs recompute preemption,
    prefix cache hit rate, PagedAttention waste, and PyTorch allocator rounding.
    """
    # Llama-3-70B GQA: 2 * 80 * 8 * 128 * 2 = 327,680 B (320 KiB/tok)
    llama70b_fp16_bytes_per_tok = 2 * 80 * 8 * 128 * 2
    llama70b_fp8_bytes_per_tok = llama70b_fp16_bytes_per_tok // 2

    # PCIe Swap round-trip time: t_swap = 2 * KV_bytes / B_PCIe
    one_way_swap_ms = round((kv_swap_gb / pcie_bw_gbs) * 1000.0, 1)
    round_trip_swap_ms = round(2.0 * one_way_swap_ms, 1)
    healthy_itl_ms = 20.0
    swap_thrashing_itl_ms = 850.0
    swap_itl_inflation_x = round(swap_thrashing_itl_ms / healthy_itl_ms, 1)

    # PagedAttention fragmentation at 500 tokens, block_size = 16:
    # ceil(500 / 16) = 32 blocks = 512 capacity -> 12 unused slots = 2.34% internal waste
    seq_tokens = 500
    block_size = 16
    blocks_allocated = (seq_tokens + block_size - 1) // block_size
    allocated_slots = blocks_allocated * block_size
    wasted_slots = allocated_slots - seq_tokens

    # PyTorch caching allocator roundup_power2_divisions:[256:1,512:2,1024:4,>:8]
    # In range [512, 1024] with 2 divisions, step = (1024 - 512) / 2 = 256 MB -> buckets [512, 768, 1024]
    step_mb = (1024 - 512) // 2
    rounded_alloc_mb = 512 + ((alloc_request_mb - 512 + step_mb - 1) // step_mb) * step_mb

    return {
        "llama70b_fp16_bytes_per_tok": llama70b_fp16_bytes_per_tok,
        "llama70b_fp8_bytes_per_tok": llama70b_fp8_bytes_per_tok,
        "one_way_swap_ms": one_way_swap_ms,
        "round_trip_swap_ms": round_trip_swap_ms,
        "healthy_itl_ms": healthy_itl_ms,
        "swap_thrashing_itl_ms": swap_thrashing_itl_ms,
        "swap_itl_inflation_x": swap_itl_inflation_x,
        "recompute_crossover_seq_len": 8192,
        "unpaged_fragmentation_pct_range": (20, 30),
        "paged_max_waste_pct": 4.0,
        "seq_500_blocks": blocks_allocated,
        "seq_500_wasted_slots": wasted_slots,
        "prefix_cache_10q_speedup_x": 10.0,
        "prefix_hit_rate_alert_pct": 60.0,
        "sglang_radix_thrash_ttft_spike_pct": 400.0,
        "sglang_fixed_ttft_ms": 22.0,
        "max_split_size_mb": 256,
        "alloc_request_mb": alloc_request_mb,
        "rounded_alloc_mb": rounded_alloc_mb,
    }


# ---------------------------------------------------------------------------
# 5. Multi-GPU NCCL AllReduce Tail Latency, CUDA Graph Bugs & XID/Probe Triage
# ---------------------------------------------------------------------------

def diagnose_nccl_cuda_graph_and_xid_faults(
    num_layers: int = 80,
    tp_size: int = 8,
    batch_tokens: int = 1,
    hidden_dim: int = 8192,
    bytes_per_elem: int = 2,
) -> Dict[str, object]:
    """Model TP AllReduce count/volume, degraded RoCEv2 tail latency, MoE capacity
    factor spillover, CUDA Graph capture rules, and XID 62 / Kubernetes probe math.
    """
    allreduces_per_layer = 2
    allreduces_per_token = num_layers * allreduces_per_layer  # 160
    ring_steps_per_allreduce = 2 * (tp_size - 1)  # 14
    per_call_bytes = int(
        2 * ((tp_size - 1) / tp_size) * batch_tokens * hidden_dim * bytes_per_elem
    )

    # MoE Capacity Factor (ASP Ch. 16: CF = 1.2 to 1.5 -> 20% to 50% extra tokens)
    base_expert_tokens = 32
    cf_1_2_cap = int(base_expert_tokens * 1.2)  # 38
    cf_1_5_cap = int(base_expert_tokens * 1.5)  # 48

    # Kubernetes probes & XID 62 blackhole (V12 Ch. 11)
    startup_failure_threshold = 60
    startup_period_s = 10
    max_startup_window_s = startup_failure_threshold * startup_period_s  # 600 s
    total_pods = 8
    deadlocked_pods = 1
    blackhole_traffic_pct = round((deadlocked_pods / total_pods) * 100.0, 2)  # 12.5%

    return {
        "allreduces_per_token": allreduces_per_token,
        "allreduces_per_sec_at_50tok_s": allreduces_per_token * 50,
        "ring_steps_per_allreduce": ring_steps_per_allreduce,
        "per_call_bytes": per_call_bytes,
        "nvswitch_tp8_itl_ms": 18.4,
        "naive_tp8_itl_ms": 115.0,
        "tp8_speedup_x": round(115.0 / 18.4, 2),
        "degraded_roce_allreduce_us": 45000,
        "degraded_roce_tx_dropped": 428,
        "degraded_roce_rx_errors": 156,
        "moe_alltoall_outlier_threshold_ms": 5.0,
        "moe_cf_range": (1.2, 1.5),
        "cf_1_2_cap": cf_1_2_cap,
        "cf_1_5_cap": cf_1_5_cap,
        "sharp_alltoall_gain_pct_range": (10, 20),
        "max_startup_window_s": max_startup_window_s,
        "readiness_timeout_s": 5,
        "broken_readiness_timeout_s": 1,
        "nfs_stall_latency_s": 1.2,
        "xid_db_ecc_code": 62,
        "blackhole_traffic_pct": blackhole_traffic_pct,
    }


# ---------------------------------------------------------------------------
# 6. Full-Stack Quantization (`FP8`, `NVFP4`, `GPTQ`, `AWQ`, `W4A8`) & App Tuning
# ---------------------------------------------------------------------------

def evaluate_quantization_and_app_optimizations(
    max_context_tokens: int = 16000,
    current_chat_tokens: int = 12000,
    small_model_share: float = 0.60,
    fallback_rate_of_small: float = 0.10,
) -> Dict[str, object]:
    """Model `ASP` Ch. 16 quantization tiers, prompt compression (`75%` trigger ->
    summarize oldest `25%`), config tokens (`200 -> 10`), `70B/700B` cascade, and
    `90%` headroom / `10%-15%` warm spare rules.
    """
    quant_formats = {
        "FP16": {"memory_ratio": 1.00, "speedup_x": 1.0, "accuracy_drop_pct": 0.0},
        "FP8": {"memory_ratio": 0.50, "speedup_x": 1.5, "accuracy_drop_pct": 0.1},
        "GPTQ_AWQ_W4A16": {"memory_ratio": 0.25, "speedup_x": 2.0, "accuracy_retained_pct": 99.0},
        "W4A8_INT4_FP8": {"memory_ratio": 0.25, "speedup_x": 1.8, "accuracy_drop_pct": 0.5},
        "NVFP4_Block32": {"memory_ratio": 0.20, "speedup_x": 3.5, "vs_fp8_reduction_x": 1.8, "vs_fp16_reduction_x": 3.5},
    }

    # Prompt compression rule (ASP Ch. 16): when chat reaches >= 75% of max context,
    # summarize oldest 25% of messages (e.g., 3,000 tokens -> 300-token summary,
    # cutting active prompt from 12,000 to 9,300 tokens; exact T(N) drops from 72,006,000 to 43,249,650).
    trigger_tokens = int(max_context_tokens * 0.75)  # 12,000
    compressed_triggered = current_chat_tokens >= trigger_tokens
    oldest_25pct_tokens = int(current_chat_tokens * 0.25)  # 3,000
    summary_tokens = oldest_25pct_tokens // 10  # 300
    new_prompt_tokens = current_chat_tokens - oldest_25pct_tokens + summary_tokens  # 9,300
    tri_before = current_chat_tokens * (current_chat_tokens + 1) // 2
    tri_after = new_prompt_tokens * (new_prompt_tokens + 1) // 2
    attention_saved_pct = round(((tri_before - tri_after) / tri_before) * 100.0, 2)

    # Config tokens (ASP Ch. 16): 200-token system prompt -> 10 config tokens (20.0x reduction)
    sys_prompt_tokens = 200
    config_tokens = 10
    config_token_reduction_x = round(sys_prompt_tokens / config_tokens, 1)

    # Model cascading (70B: 50 ms, 1.0 cost vs 700B: 500 ms, 10.0 cost)
    small_lat_ms, large_lat_ms = 50.0, 500.0
    small_cost, large_cost = 1.0, 10.0
    no_fallback_lat_ms = round(
        small_model_share * small_lat_ms + (1.0 - small_model_share) * large_lat_ms, 1
    )  # 230.0 ms
    no_fallback_cost = round(
        small_model_share * small_cost + (1.0 - small_model_share) * large_cost, 2
    )  # 4.6
    fallback_total_share = small_model_share * fallback_rate_of_small  # 0.06
    with_fallback_lat_ms = round(no_fallback_lat_ms + fallback_total_share * large_lat_ms, 1)  # 260.0 ms
    with_fallback_cost = round(no_fallback_cost + fallback_total_share * large_cost, 2)  # 5.2

    return {
        "quant_formats": quant_formats,
        "ptq_calibration_prompts": 1000,
        "smoothquant_max_loss_pct": 1.0,
        "trigger_tokens": trigger_tokens,
        "compressed_triggered": compressed_triggered,
        "oldest_25pct_tokens": oldest_25pct_tokens,
        "new_prompt_tokens": new_prompt_tokens,
        "tri_before": tri_before,
        "tri_after": tri_after,
        "attention_saved_pct": attention_saved_pct,
        "config_token_reduction_x": config_token_reduction_x,
        "no_fallback_lat_ms": no_fallback_lat_ms,
        "no_fallback_cost": no_fallback_cost,
        "with_fallback_lat_ms": with_fallback_lat_ms,
        "with_fallback_cost": with_fallback_cost,
        "max_cascade_cost_reduction_x": 5.0,
        "headroom_target_pct": 90,
        "batch_scale_back": (16, 8),
        "warm_spare_buffer_pct_range": (10, 15),
        "critical_spare_buffer_pct": 100,
        "debounce_interval_ms_range": (2, 5),
        "max_output_tokens_limit": 4096,
        "server_timeout_s": 30,
    }


if __name__ == "__main__":
    p = evaluate_nvtx_kineto_and_ncu_profile()
    c = evaluate_chunked_prefill_and_latency_aware_scheduling()
    g = evaluate_cpu_gil_and_pipeline_bottlenecks()
    k = diagnose_kv_cache_preemption_and_allocator()
    n = diagnose_nccl_cuda_graph_and_xid_faults()
    q = evaluate_quantization_and_app_optimizations()
    print(f"NVTX train_step projected GPU time: {p['nvtx_subrange_sum_ms']} ms")
    print(f"Latency-aware critical-path QK reduction: {c['critical_path_reduction_pct']}%")
    print(f"Lab 04 p99 latency reduction: {g['lab04_unfixed']['total_p99_ms']} ms -> {g['lab04_fixed']['total_p99_ms']} ms")
    print(f"PyTorch allocator 600 MB rounded to: {k['rounded_alloc_mb']} MB")
    print(f"Llama-3-70B TP=8 AllReduces/token: {n['allreduces_per_token']}")
    print(f"Cascade expected latency (60% 70B share): {q['no_fallback_lat_ms']} ms")
