#!/usr/bin/env python3
"""Chapter 14.12 model: Training Performance Engineering and Troubleshooting.

Models:
1. Model FLOPs Utilization (MFU), Hardware FLOPs Utilization (HFU), and Goodput (`V13` Ch. 11, `ASP` Ch. 1, `DAI` Ch. 10):
   - Dense Transformer training step compute: `C_step = 6 * N_params * tokens_per_step` (`2N` forward + `4N` backward).
   - Achieved compute rate: `Achieved_FLOPs_per_sec = 6 * N_params * tokens_per_sec`.
   - `MFU = Achieved_FLOPs_per_sec / (num_gpus * Peak_GPU_FLOPs_per_sec)`.
   - Worked 70B model on 8x H100 SXM (`989 TFLOPS/GPU` dense BF16 -> `7,912 TFLOPS` node peak):
     * Before DataLoader fix (`30%` GPU util, `3,200 tok/s`): `1,344 TFLOPS` -> `16.99%` (`~17%`) MFU.
     * After DataLoader fix (`9,000 tok/s`): `3,780 TFLOPS` -> `47.78%` (`~48%`) MFU (`2.8125x` speedup).
   - `HFU` with full activation recomputation (`8 * N_params * tokens_per_sec`): `HFU = (8 / 6) * MFU` (`63.70%` at `9,000 tok/s`).
   - Goodput & Wasted GPU Cost (`ASP` Ch. 1 & `DAI` Ch. 10):
     * `100,000` tokens in `10 s` = `10,000 tok/s` vs `8 * 1,500 = 12,000 tok/s` peak -> `83.33%` (`83.3%`) efficiency.
     * `300 / 1,000 samples/s = 30.0%` goodput (`70.0%` wasted capacity, matching Meta's `70%–75%` lost compute).
     * `64` GPUs at `45%` GPU util and `52%` scaling efficiency -> `33.28` effective GPUs, `30.72` wasted GPUs;
       over a `2`-week (`336`-hour) run = `10,321.92` wasted GPU-hours = `$41,287.68` at `$4/hr` or `$51,609.60` at `$5/hr`.

2. Step-Time Phase Decomposition, Scaling Efficiency, and Amdahl's Law (`DAI` Ch. 10, `ASP` Ch. 13):
   - Iteration scaling from `1` GPU (`155.0 ms`, `0%` comm) to `16` GPUs (`33.0 ms`, `55.0%` comm = `18.15 ms` comm + `14.85 ms` compute;
     speedup = `4.697x`, scaling efficiency = `29.36%`).
   - MLPerf Logging `24.0 ms` step breakdown (`ASP` Ch. 13 Table 13-6): `forward = 10.5 ms` (`43.75%`), `backward = 9.0 ms` (`37.50%`),
     total compute = `19.5 ms` (`81.25%`), `allreduce = 4.0 ms` (`16.67%` = `1/6`), `other = 0.5 ms` (`2.08%`).
   - 64-Expert MoE `138.0 ms` step (`ASP` Ch. 13 Tables 13-2 & 13-3): `forward = 60.5 ms` (`43.84%`), `backward = 58.3 ms` (`42.25%`),
     `optimizer_step = 19.2 ms` (`13.91%`, `64` `aten::add_` kernels); GEMM (`matmul` `43.00 ms` + `linear` `35.50 ms` = `78.50 ms`, `56.88%`),
     routing (`dispatch` `18.70 ms` + `combine` `12.10 ms` = `30.80 ms`, `22.32%`), other 6 ops = `28.70 ms` (`20.80%`).
   - Amdahl's Law: `Speedup(N) = 1 / (s + (1 - s) / N)` (`s = 0.10` -> `10.0x` asymptotic cap; `8.77x` at `N = 64`).

3. Top-Down Bottleneck Classifier, Kernel Roofline, and Memory Allocator / Compiler Tuning (`V13` Ch. 11, `ASP` Ch. 13):
   - Classifies DataLoader CPU starvation (`30%` GPU util, `10%–17%` MFU), Unfused Memory-Bound Kernels (`98%–100%` GPU util, `22%` MFU),
     Network/Straggler Stall (`200 ms` NCCL `Wait` on `63/64` nodes), and Thermal Throttling (`45% -> 28%` MFU decay over 24 hours).
   - Nsight Compute (`ncu`) Roofline (`ASP` Ch. 13 Table 13-4): Baseline (`50%` FLOPS, `70%` HBM BW, `60%` occ -> `Memory bound`) vs
     Optimized (`85%` FLOPS, `40%` HBM BW, `80%` occ -> `Compute bound`).
   - `torch.compile` (`248.0 ms -> 173.0 ms`, `75.0 ms` / `30.24%` saved, `1.43x` speedup), `SimpleFSDP` (`64.0 -> 46.08 GB` `-28%`,
     `10,000 -> 16,900 tok/s` `+69%`), `AsyncTP` (`12.0 + 4.0 = 16.0 ms` -> `12.6 ms` at `85%` overlap, `21.25%` saved),
     and `PYTORCH_ALLOC_CONF` (`600 MB` rounded to `768 MB` under `512:2` vs `600 MB` with `expandable_segments:True`, saving `168 MB` / `21.88%`).

4. NCCL Collective Profiling, Straggler Detection, and Production Failure Triage (`V13` Ch. 1, 8, 11, 12, Labs 01–04; `ASP` Ch. 4 & 13):
   - Communicator lifecycle (`ASP` Ch. 4 Table 4-3): `48.0 ms` init + `0.5 ms` AllReduce = `48.5 ms` vs `0.5 ms` reuse (`98.97%` reduction, `97.0x`).
   - Ring vs Tree & SHARP (`V13` Ch. 8, `ASP` Ch. 4): `28 GB` FP32 gradients -> `8` GPUs (`49.0 GB` in `54.4 ms` on `900 GB/s` NVLink, `8` hops) vs
     `512` GPUs (`55.89 GB` in `2.24 s` on `25 GB/s` IB, `512` ring hops vs `9` tree hops); SHARP reduces per-GPU receive volume by `1/(N-1)`.
   - Multi-rank straggler detection (`V13` Ch. 11 64-node `200 ms` NCCL wait on 63 fast nodes vs `0 ms` wait on `node-14-straggler`;
     `ASP` Ch. 13 8-rank HTA trace pinpointing Rank `7` at `21.0 ms` compute and Rank `0` at `2.0 ms` idle).
   - Llama 3 405B 54-day interruption ledger (`ASP` Ch. 4 Table 4-4: `419` total interruptions across 17 root-cause categories),
     thermal clock throttling (`45% -> 28%` MFU), `nvidia-fabricmanager` PCIe fallback (`950 -> 310 tok/s`, `800 -> 90 GB/s` or `400 -> 20 GB/s`),
     MoE `AllToAll` collapse (`25%` throughput at `40%–50%` uniform GPU util), and PyTorch HUD CI regression gate (`>= 5.0%` drop over `3` consecutive runs).
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List, Tuple


def compute_mfu_hfu_and_goodput(
    params_b: float = 70.0,
    tokens_per_sec: float = 3200.0,
    num_gpus: int = 8,
    peak_tflops_per_gpu: float = 989.0,
    activation_recompute: bool = True,
    goodput_tokens: int = 100000,
    goodput_window_sec: float = 10.0,
    peak_tokens_per_sec_per_gpu: float = 1500.0,
) -> Dict[str, float]:
    """Computes MFU, HFU (with 8N recomputation vs 6N forward+backward), and cluster goodput."""
    n_params = params_b * 1e9
    achieved_flops_per_sec = 6.0 * n_params * tokens_per_sec
    achieved_tflops = achieved_flops_per_sec / 1e12
    cluster_peak_tflops = num_gpus * peak_tflops_per_gpu
    mfu_pct = 100.0 * achieved_tflops / cluster_peak_tflops

    hfu_multiplier = (8.0 / 6.0) if activation_recompute else 1.0
    hfu_tflops = achieved_tflops * hfu_multiplier
    hfu_pct = mfu_pct * hfu_multiplier

    realized_goodput_tok_s = goodput_tokens / goodput_window_sec
    peak_cluster_tok_s = num_gpus * peak_tokens_per_sec_per_gpu
    goodput_efficiency_pct = 100.0 * realized_goodput_tok_s / peak_cluster_tok_s

    return {
        "params_b": params_b,
        "tokens_per_sec": tokens_per_sec,
        "num_gpus": float(num_gpus),
        "peak_tflops_per_gpu": peak_tflops_per_gpu,
        "cluster_peak_tflops": round(cluster_peak_tflops, 2),
        "achieved_tflops": round(achieved_tflops, 2),
        "mfu_pct": round(mfu_pct, 2),
        "hfu_tflops": round(hfu_tflops, 2),
        "hfu_pct": round(hfu_pct, 2),
        "realized_goodput_tok_s": round(realized_goodput_tok_s, 2),
        "peak_cluster_tok_s": round(peak_cluster_tok_s, 2),
        "goodput_efficiency_pct": round(goodput_efficiency_pct, 2),
    }


def evaluate_wasted_cluster_cost(
    num_gpus: int = 64,
    gpu_util_pct: float = 45.0,
    scaling_efficiency_pct: float = 52.0,
    run_hours: float = 336.0,
    cost_per_gpu_hour_low: float = 4.0,
    cost_per_gpu_hour_high: float = 5.0,
) -> Dict[str, float]:
    """Quantifies effective GPUs, wasted GPUs, and wasted cloud cost (`DAI` Ch. 10 64-GPU case study)."""
    effective_gpus = num_gpus * (scaling_efficiency_pct / 100.0)
    wasted_gpus = num_gpus - effective_gpus
    total_gpu_hours = num_gpus * run_hours
    wasted_gpu_hours = wasted_gpus * run_hours
    wasted_cost_low_usd = wasted_gpu_hours * cost_per_gpu_hour_low
    wasted_cost_high_usd = wasted_gpu_hours * cost_per_gpu_hour_high

    return {
        "num_gpus": float(num_gpus),
        "gpu_util_pct": gpu_util_pct,
        "scaling_efficiency_pct": scaling_efficiency_pct,
        "effective_gpus": round(effective_gpus, 2),
        "wasted_gpus": round(wasted_gpus, 2),
        "run_hours": run_hours,
        "total_gpu_hours": round(total_gpu_hours, 2),
        "wasted_gpu_hours": round(wasted_gpu_hours, 2),
        "wasted_cost_low_usd": round(wasted_cost_low_usd, 2),
        "wasted_cost_high_usd": round(wasted_cost_high_usd, 2),
    }


def analyze_step_scaling_and_amdahl(
    single_gpu_step_ms: float = 155.0,
    scaled_gpu_step_ms: float = 33.0,
    num_gpus: int = 16,
    scaled_comm_share_pct: float = 55.0,
    serial_fraction: float = 0.10,
) -> Dict[str, float]:
    """Analyzes step-time scaling, exposed communication overhead, and Amdahl's Law ceiling (`DAI` Ch. 10)."""
    speedup = single_gpu_step_ms / scaled_gpu_step_ms
    scaling_efficiency_pct = 100.0 * speedup / num_gpus
    comm_ms = scaled_gpu_step_ms * (scaled_comm_share_pct / 100.0)
    compute_ms = scaled_gpu_step_ms - comm_ms

    amdahl_max_speedup = 1.0 / serial_fraction
    amdahl_speedup_n = 1.0 / (serial_fraction + (1.0 - serial_fraction) / num_gpus)
    amdahl_speedup_64 = 1.0 / (serial_fraction + (1.0 - serial_fraction) / 64.0)

    return {
        "single_gpu_step_ms": single_gpu_step_ms,
        "scaled_gpu_step_ms": scaled_gpu_step_ms,
        "num_gpus": float(num_gpus),
        "speedup": round(speedup, 4),
        "scaling_efficiency_pct": round(scaling_efficiency_pct, 2),
        "comm_ms": round(comm_ms, 2),
        "compute_ms": round(compute_ms, 2),
        "serial_fraction": serial_fraction,
        "amdahl_max_speedup": round(amdahl_max_speedup, 2),
        "amdahl_speedup_n": round(amdahl_speedup_n, 2),
        "amdahl_speedup_64": round(amdahl_speedup_64, 2),
    }


def reconcile_moe_and_mlperf_profiles() -> Dict[str, object]:
    """Reconciles `torch.profiler` Table 13-2, `nsys` Table 13-3, and MLPerf Table 13-6 (`ASP` Ch. 13)."""
    ops = [
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
    total_cuda_ms = sum(t for _, t, _ in ops)
    total_calls = sum(c for _, _, c in ops)
    gemm_ms = 43.00 + 35.50
    routing_ms = 18.70 + 12.10
    other_ops_ms = total_cuda_ms - gemm_ms - routing_ms

    nvtx_forward_ms = 60.5
    nvtx_backward_ms = 58.3
    nvtx_optimizer_ms = 19.2
    nvtx_total_ms = nvtx_forward_ms + nvtx_backward_ms + nvtx_optimizer_ms

    mlperf_step_ms = 24.0
    mlperf_fwd_ms = 10.5
    mlperf_bwd_ms = 9.0
    mlperf_allreduce_ms = 4.0
    mlperf_other_ms = 0.5
    mlperf_compute_ms = mlperf_fwd_ms + mlperf_bwd_ms

    return {
        "moe_total_cuda_ms": round(total_cuda_ms, 2),
        "moe_total_calls": total_calls,
        "moe_gemm_ms": round(gemm_ms, 2),
        "moe_gemm_pct": round(100.0 * gemm_ms / total_cuda_ms, 2),
        "moe_routing_ms": round(routing_ms, 2),
        "moe_routing_pct": round(100.0 * routing_ms / total_cuda_ms, 2),
        "moe_other_ops_ms": round(other_ops_ms, 2),
        "moe_other_ops_pct": round(100.0 * other_ops_ms / total_cuda_ms, 2),
        "nvtx_total_ms": round(nvtx_total_ms, 2),
        "nvtx_forward_pct": round(100.0 * nvtx_forward_ms / nvtx_total_ms, 2),
        "nvtx_backward_pct": round(100.0 * nvtx_backward_ms / nvtx_total_ms, 2),
        "nvtx_optimizer_pct": round(100.0 * nvtx_optimizer_ms / nvtx_total_ms, 2),
        "mlperf_step_ms": mlperf_step_ms,
        "mlperf_compute_ms": mlperf_compute_ms,
        "mlperf_compute_pct": round(100.0 * mlperf_compute_ms / mlperf_step_ms, 1),
        "mlperf_allreduce_ms": mlperf_allreduce_ms,
        "mlperf_allreduce_pct": round(100.0 * mlperf_allreduce_ms / mlperf_step_ms, 1),
        "mlperf_other_pct": round(100.0 * mlperf_other_ms / mlperf_step_ms, 1),
    }


def classify_training_bottleneck(
    gpu_util_pct: float,
    mfu_pct: float,
    cpu_util_or_iowait_pct: float,
    tensor_core_active_pct: float,
    nccl_wait_ms: float = 0.0,
    sm_clock_drop_pct: float = 0.0,
) -> Dict[str, str]:
    """Implements the Top-Down Bottleneck Decision Tree (`V13` Ch. 11 & Ch. 12)."""
    if sm_clock_drop_pct >= 15.0:
        return {
            "category": "THERMAL_THROTTLING",
            "diagnosis": "GPU SM clocks throttled due to elevated temperature (>83-85C) or cooling degradation",
            "first_command": "nvidia-smi -q -d TEMPERATURE,CLOCK",
            "remediation": "Inspect rack cooling/airflow, clean fans/CDU filters, or drain thermally degraded node",
        }
    if gpu_util_pct < 60.0:
        if cpu_util_or_iowait_pct >= 80.0:
            return {
                "category": "DATALOADER_CPU_IO_BOTTLENECK",
                "diagnosis": "GPUs are starved waiting for host CPU preprocessing or storage I/O",
                "first_command": "iostat -x 1 && nsys profile -t cuda,osrt,nvtx -o dataloader_trace python train.py",
                "remediation": "Increase DataLoader num_workers (2-4x per GPU), enable pin_memory=True, persistent_workers=True, prefetch_factor=4, or offload augmentations to DALI/GPU",
            }
        return {
            "category": "NETWORK_OR_STRAGGLER_BOTTLENECK",
            "diagnosis": "GPUs sit idle blocked on NCCL collectives or a slow straggler rank/link",
            "first_command": "NCCL_DEBUG=INFO ./build/all_reduce_perf -b 8 -e 128M -f 2 -g 8",
            "remediation": "Identify rank with 0 ms NCCL wait in nsys/HTA, inspect dmesg for PCIe AER or IB symbol errors, and cordon straggler node",
        }
    if mfu_pct < 30.0 or tensor_core_active_pct < 30.0:
        if nccl_wait_ms >= 50.0:
            return {
                "category": "STRAGGLER_NCCL_SPIN_WAIT",
                "diagnosis": "High nvidia-smi utilization is masked by NCCL kernel spin-waiting on a straggler node",
                "first_command": "dmesg | grep -i 'AER' && kubectl cordon node-14-straggler",
                "remediation": "Isolate the rank without NCCL Wait states, run pairwise nccl-tests, and drain/cordon the degraded node",
            }
        return {
            "category": "MEMORY_BANDWIDTH_BOUND_UNFUSED_KERNELS",
            "diagnosis": "100% nvidia-smi utilization Lie: GPU is busy running small, unfused memory-bound kernels that starve Tensor Cores",
            "first_command": "ncu --metrics sm__throughput.avg.pct_of_peak_sustained_elapsed python train.py",
            "remediation": "Enable torch.compile(mode='max-autotune'), FlashAttention/SDPA, BF16/FP8 autocast, and larger micro-batches",
        }
    return {
        "category": "COMPUTE_BOUND_HEALTHY",
        "diagnosis": "Tensor Cores are well-utilized and MFU is in the healthy 40-50%+ target band",
        "first_command": "nvidia-smi dmon -s pucvmet -d 1",
        "remediation": "Scale out batch size or apply AsyncTP / SimpleFSDP for additional overlap",
    }


def evaluate_compiler_allocator_and_overlap() -> Dict[str, float | List[int] | str]:
    """Models `torch.compile`, `PYTORCH_ALLOC_CONF`, CUDA Graph pools, `SimpleFSDP`, and `AsyncTP` (`ASP` Ch. 13)."""
    eager_ms = 248.0
    compiled_ms = 173.0
    compile_saved_ms = eager_ms - compiled_ms
    compile_reduction_pct = 100.0 * compile_saved_ms / eager_ms
    compile_speedup = eager_ms / compiled_ms

    # PYTORCH_ALLOC_CONF roundup_power2_divisions:[256:1,512:2,1024:4,>:8]
    # In [512, 1024], division=2 -> step size = (1024 - 512) / 2 = 256 MB -> buckets [512, 768, 1024]
    requested_mb = 600.0
    step_mb = (1024.0 - 512.0) / 2.0
    rounded_vram_mb = 512.0 + math.ceil((requested_mb - 512.0) / step_mb) * step_mb
    expandable_vram_mb = requested_mb
    vram_saved_mb = rounded_vram_mb - expandable_vram_mb
    vram_saved_pct = 100.0 * vram_saved_mb / rounded_vram_mb

    # SimpleFSDP vs eager FSDP2
    fsdp2_mem_gb = 64.0
    simplefsdp_mem_gb = fsdp2_mem_gb * (1.0 - 0.28)
    fsdp2_tok_s = 10000.0
    simplefsdp_tok_s = fsdp2_tok_s * 1.69

    # AsyncTP overlap
    tp_compute_ms = 12.0
    tp_allgather_ms = 4.0
    tp_seq_ms = tp_compute_ms + tp_allgather_ms
    overlap_efficiency = 0.85
    hidden_comm_ms = tp_allgather_ms * overlap_efficiency
    asynctp_ms = tp_seq_ms - hidden_comm_ms
    asynctp_reduction_pct = 100.0 * hidden_comm_ms / tp_seq_ms

    return {
        "eager_ms": eager_ms,
        "compiled_ms": compiled_ms,
        "compile_saved_ms": round(compile_saved_ms, 2),
        "compile_reduction_pct": round(compile_reduction_pct, 2),
        "compile_speedup": round(compile_speedup, 2),
        "cudagraph_capture_order": [8, 4, 2, 1],
        "requested_mb": requested_mb,
        "rounded_vram_mb": rounded_vram_mb,
        "expandable_vram_mb": expandable_vram_mb,
        "vram_saved_mb": vram_saved_mb,
        "vram_saved_pct": round(vram_saved_pct, 2),
        "simplefsdp_mem_gb": round(simplefsdp_mem_gb, 2),
        "simplefsdp_tok_s": round(simplefsdp_tok_s, 1),
        "tp_seq_ms": tp_seq_ms,
        "asynctp_ms": round(asynctp_ms, 2),
        "asynctp_reduction_pct": round(asynctp_reduction_pct, 2),
    }


def analyze_nccl_collectives_and_stragglers() -> Dict[str, object]:
    """Models NCCL init overhead, Ring vs Tree vs SHARP cost, and HTA / 64-node straggler detection."""
    # Table 4-3: repeated communicator init/destroy vs reuse
    init_destroy_ms = 48.0
    allreduce_1elem_ms = 0.5
    iter_bad_ms = init_destroy_ms + allreduce_1elem_ms
    iter_good_ms = allreduce_1elem_ms
    init_overhead_reduction_pct = 100.0 * (iter_bad_ms - iter_good_ms) / iter_bad_ms

    # Ring vs Tree on 28 GB FP32 gradients (V13 Ch. 8)
    grad_gb = 28.0
    ring_8_data_gb = 2.0 * (7.0 / 8.0) * grad_gb
    ring_8_time_ms = 1000.0 * (ring_8_data_gb / 900.0)
    ring_512_data_gb = 2.0 * (511.0 / 512.0) * grad_gb
    ring_512_time_s = ring_512_data_gb / 25.0
    ring_512_hops = 512
    tree_512_hops = int(math.log2(512))

    # SHARP in-network reduction factor: (B / N) / (B * (N - 1) / N) = 1 / (N - 1)
    sharp_rx_ratio_8 = 1.0 / (8 - 1)

    # 8-rank HTA straggler trace (24.0 ms total step time)
    hta_ranks = [
        {"rank": 0, "compute_ms": 18.0, "comm_ms": 4.0, "idle_ms": 2.0},
        {"rank": 1, "compute_ms": 19.0, "comm_ms": 4.0, "idle_ms": 1.0},
        {"rank": 2, "compute_ms": 19.0, "comm_ms": 4.0, "idle_ms": 1.0},
        {"rank": 3, "compute_ms": 19.5, "comm_ms": 3.5, "idle_ms": 1.0},
        {"rank": 4, "compute_ms": 19.5, "comm_ms": 3.5, "idle_ms": 1.0},
        {"rank": 5, "compute_ms": 19.0, "comm_ms": 4.0, "idle_ms": 1.0},
        {"rank": 6, "compute_ms": 19.0, "comm_ms": 4.0, "idle_ms": 1.0},
        {"rank": 7, "compute_ms": 21.0, "comm_ms": 3.0, "idle_ms": 0.0},
    ]
    compute_straggler_rank = max(hta_ranks, key=lambda r: r["compute_ms"])["rank"]
    most_idle_rank = max(hta_ranks, key=lambda r: r["idle_ms"])["rank"]

    return {
        "iter_bad_ms": iter_bad_ms,
        "iter_good_ms": iter_good_ms,
        "init_overhead_reduction_pct": round(init_overhead_reduction_pct, 2),
        "ring_8_data_gb": round(ring_8_data_gb, 2),
        "ring_8_time_ms": round(ring_8_time_ms, 1),
        "ring_512_data_gb": round(ring_512_data_gb, 2),
        "ring_512_time_s": round(ring_512_time_s, 2),
        "ring_512_hops": ring_512_hops,
        "tree_512_hops": tree_512_hops,
        "sharp_rx_ratio_8": round(sharp_rx_ratio_8, 4),
        "compute_straggler_rank": compute_straggler_rank,
        "most_idle_rank": most_idle_rank,
        "max_socket_connections": 64,
    }


def summarize_llama3_405b_interruptions() -> Dict[str, object]:
    """Summarizes Meta's 54-day Llama 3 405B unexpected interruption root causes (`ASP` Ch. 4 Table 4-4)."""
    rows: List[Tuple[str, str, int, float]] = [
        ("Faulty GPU", "GPU", 148, 35.3),
        ("GPU HBM3 memory", "GPU", 72, 17.2),
        ("Software bug", "Dependency", 54, 12.9),
        ("Network switch/cable", "Network", 35, 8.4),
        ("Host maintenance", "Unplanned Maintenance", 32, 7.6),
        ("GPU SRAM memory", "GPU", 19, 4.5),
        ("GPU system processor", "GPU", 17, 4.1),
        ("NIC", "Host", 7, 1.7),
        ("NCCL watchdog timeouts", "Unknown", 7, 1.7),
        ("Silent data corruption", "GPU", 6, 1.4),
        ("GPU thermal interface and sensor", "GPU", 6, 1.4),
        ("SSD", "Host", 3, 0.7),
        ("Power supply", "Host", 3, 0.7),
        ("Server chassis", "Host", 2, 0.5),
        ("IO expansion board", "Host", 2, 0.5),
        ("Dependency", "Dependency", 2, 0.5),
        ("CPU", "Host", 2, 0.5),
        ("System memory", "Host", 2, 0.5),
    ]
    total_count = sum(c for _, _, c, _ in rows)
    gpu_category_count = sum(c for _, cat, c, _ in rows if cat == "GPU")
    gpu_category_pct = 100.0 * gpu_category_count / total_count
    top_two_gpu_count = 148 + 72
    top_two_gpu_pct = 35.3 + 17.2

    return {
        "duration_days": 54,
        "total_interruptions": total_count,
        "gpu_category_count": gpu_category_count,
        "gpu_category_pct": round(gpu_category_pct, 1),
        "top_two_gpu_count": top_two_gpu_count,
        "top_two_gpu_pct": round(top_two_gpu_pct, 1),
        "network_switch_cable_count": 35,
        "nccl_watchdog_count": 7,
        "sdc_count": 6,
    }


def evaluate_ci_regression_and_hardware_degradation(
    baseline_tok_s: float = 10000.0,
    run_series_tok_s: List[float] | None = None,
    regression_threshold_pct: float = 5.0,
    consecutive_runs_required: int = 3,
) -> Dict[str, object]:
    """Evaluates PyTorch HUD CI regression gate (`>= 5%` over 3 runs) and hardware degradation signatures."""
    if run_series_tok_s is None:
        run_series_tok_s = [9400.0, 9450.0, 9480.0]

    consecutive_regressions = 0
    max_consecutive = 0
    for val in run_series_tok_s:
        drop_pct = 100.0 * (baseline_tok_s - val) / baseline_tok_s
        if drop_pct >= regression_threshold_pct:
            consecutive_regressions += 1
            max_consecutive = max(max_consecutive, consecutive_regressions)
        else:
            consecutive_regressions = 0

    ci_build_failed = max_consecutive >= consecutive_runs_required

    # Thermal throttling MFU drift: 45% -> 28% (V13 Ch. 11)
    mfu_initial_pct = 45.0
    mfu_throttled_pct = 28.0
    mfu_relative_drop_pct = 100.0 * (mfu_initial_pct - mfu_throttled_pct) / mfu_initial_pct

    # Reboot fabricmanager / PCIe fallback: 950 -> 310 tok/s, 800 -> 90 GB/s, 400 -> 20 GB/s (V13 Ch. 8 & 12)
    reboot_tok_s_drop_pct = 100.0 * (950.0 - 310.0) / 950.0
    nvlink_bridge_bw_drop_factor = 400.0 / 20.0

    return {
        "baseline_tok_s": baseline_tok_s,
        "max_consecutive_regressions": max_consecutive,
        "ci_build_failed": ci_build_failed,
        "mfu_initial_pct": mfu_initial_pct,
        "mfu_throttled_pct": mfu_throttled_pct,
        "mfu_relative_drop_pct": round(mfu_relative_drop_pct, 2),
        "reboot_tok_s_drop_pct": round(reboot_tok_s_drop_pct, 2),
        "nvlink_bridge_bw_drop_factor": round(nvlink_bridge_bw_drop_factor, 1),
    }


if __name__ == "__main__":
    mfu_before = compute_mfu_hfu_and_goodput(params_b=70.0, tokens_per_sec=3200.0)
    mfu_after = compute_mfu_hfu_and_goodput(params_b=70.0, tokens_per_sec=9000.0)
    print("70B on 8x H100 (Before DataLoader Fix):", mfu_before)
    print("70B on 8x H100 (After DataLoader Fix): ", mfu_after)
    print("64-GPU Wasted Cost:", evaluate_wasted_cluster_cost())
    print("MoE & MLPerf Reconciliation:", reconcile_moe_and_mlperf_profiles())
    print("Llama 3 405B Interruptions:", summarize_llama3_405b_interruptions())
