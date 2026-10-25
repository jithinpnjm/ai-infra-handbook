#!/usr/bin/env python3
"""Chapter 10.18 model: Dynamic scheduling, CUDA graphs and device-initiated orchestration.

Models every quantitative benchmark, atomic queue batching formula, CUDA Graph overhead
table, device-initiated graph launch limit, Dynamic Parallelism comparison, NVSHMEM PGAS
pipeline, and Volume 03 production profiling regression from:
  - *AI Systems Performance Engineering* (Chris Fregly), Chapter 12:
    * L2-cache atomic work queues (`atomic_transactions_per_request -> 1.0`, warp-leader
      batching `batchSize = 32, 16, 8`, `uneven_static.cu` `200 ms` vs `uneven_dynamic.cu`
      `100 ms` = `2.0x` speedup on `N = 1 << 20 = 1,048,576`, `work = idx % 256`)
    * DGX GB200 NVL72 domain (`36` Grace CPUs, `72` Blackwell GPUs, `30 TB` unified memory)
    * Table 12-1: CUDA Graphs (`300 -> 100` launches, `300 -> 0` syncs, `~3 us -> 0 us` gaps,
      `1.00 -> 0.75 ms` = `25%` faster)
    * Device-initiated CUDA Graph launch (`cudaGraphInstantiateFlagDeviceLaunch`, `~2x` lower
      launch latency, `120` max fire-and-forget graphs, `255` max pending tail launches,
      `1` max pending self-tail-launch, conditional graph nodes `IF/IF-ELSE/WHILE/SWITCH`
      with `threshold = 123456`)
    * Table 12-2: Dynamic Parallelism (`3 -> 1` host launches, `20 -> 25 us` per-launch cost,
      `40% -> 5%` GPU idle cycles, `1.00 -> 0.75 ms` = `25%` faster, `2,048` default max
      pending child launches `cudaLimitDevRuntimePendingLaunchCount`)
    * NVSHMEM PGAS one-sided puts/signals and Roofline-guided orchestration
  - `nvidia-devops` Volume 03 (Chapters 10, 12, 13 & Lab 04):
    * Decode launch overhead (`15 us` CPU launch for `3 us` GPU kernel = `83.3%` / `~80%` waste;
      Triton `500` words * `80` layers = `40,000` kernel launches)
    * `nsys` API share check (`2.1%` / `4,120,000 ns` `cudaLaunchKernel` vs `97.3%` /
      `189,340,000 ns` `512 MB` `cudaMemcpyAsync`)
    * Lab 04 controlled regressions (`67,108,864` elements: `812.4 ms` baseline vs `1,928.3 ms`
      device sync `2.37x`, `3,140.9 ms` `16 KiB` tiny chunks `3.87x`, `2,214.8 ms` pageable `2.73x`)
    * Fragmentation OOM (`40,960 MiB` total, `1,895 MiB` free vs `1,240 MiB` across `340` blocks
      failing `512 MiB` alloc) and `compute-sanitizer` (`3906 * 256 + 287 = 1,000,223 > 1,000,003`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


GB200_NVL72_GRACE_CPUS: int = 36
GB200_NVL72_BLACKWELL_GPUS: int = 72
GB200_NVL72_UNIFIED_MEMORY_TB: int = 30

MAX_FIRE_AND_FORGET_GRAPHS: int = 120
MAX_PENDING_TAIL_LAUNCHES: int = 255
MAX_PENDING_SELF_TAIL_LAUNCHES: int = 1
DEFAULT_DP_PENDING_LAUNCH_COUNT: int = 2048
CONDITIONAL_NODE_EXAMPLE_THRESHOLD: int = 123_456


@dataclass(frozen=True)
class AtomicWorkQueueAnalysis:
    """L2-cache atomic work queue contention and uneven workload balance model (ASP Ch 12)."""

    num_elements: int
    batch_size: int
    unbatched_atomic_ops: int
    batched_atomic_ops: int
    atomic_reduction_factor: float
    ideal_transactions_per_request: float
    static_runtime_ms: float
    dynamic_runtime_ms: float
    speedup_ratio: float


def evaluate_atomic_work_queue(
    num_elements: int = 1_048_576,  # 1 << 20
    batch_size: int = 32,  # warpSize
    static_runtime_ms: float = 200.0,
    dynamic_runtime_ms: float = 100.0,
) -> AtomicWorkQueueAnalysis:
    """Model warp-batched atomic queue (`computeKernelDynamicBatch`, ASP Ch 12)."""
    if num_elements <= 0 or batch_size <= 0:
        raise ValueError("num_elements and batch_size must be positive")
    if static_runtime_ms <= 0 or dynamic_runtime_ms <= 0:
        raise ValueError("Runtimes must be positive")

    unbatched = num_elements
    batched = (num_elements + batch_size - 1) // batch_size
    return AtomicWorkQueueAnalysis(
        num_elements=num_elements,
        batch_size=batch_size,
        unbatched_atomic_ops=unbatched,
        batched_atomic_ops=batched,
        atomic_reduction_factor=round(unbatched / batched, 2),
        ideal_transactions_per_request=1.0,
        static_runtime_ms=static_runtime_ms,
        dynamic_runtime_ms=dynamic_runtime_ms,
        speedup_ratio=round(static_runtime_ms / dynamic_runtime_ms, 2),
    )


@dataclass(frozen=True)
class CudaGraphComparison:
    """Table 12-1 impact of CUDA Graphs on 100 iterations of a 3-kernel pipeline (ASP Ch 12)."""

    iterations: int
    kernels_per_iteration: int
    launches_before: int
    launches_after: int
    sync_calls_before: int
    sync_calls_after: int
    inter_kernel_gap_before_us: float
    inter_kernel_gap_after_us: float
    latency_before_ms: float
    latency_after_ms: float
    latency_reduction_pct: float


TABLE_12_1_CUDA_GRAPHS = CudaGraphComparison(
    iterations=100,
    kernels_per_iteration=3,
    launches_before=300,
    launches_after=100,
    sync_calls_before=300,
    sync_calls_after=0,
    inter_kernel_gap_before_us=3.0,
    inter_kernel_gap_after_us=0.0,
    latency_before_ms=1.00,
    latency_after_ms=0.75,
    latency_reduction_pct=25.0,
)


@dataclass(frozen=True)
class DynamicParallelismComparison:
    """Table 12-2 host-driven vs GPU-driven nested child-kernel launches (1 parent + 2 children, ASP Ch 12)."""

    host_launches_before: int
    host_launches_after: int
    launch_overhead_before_us: float
    launch_overhead_after_us: float
    gpu_idle_pct_before: float
    gpu_idle_pct_after: float
    idle_reduction_pct_points: float
    execution_time_before_ms: float
    execution_time_after_ms: float
    execution_time_reduction_pct: float
    default_max_pending_launches: int


TABLE_12_2_DYNAMIC_PARALLELISM = DynamicParallelismComparison(
    host_launches_before=3,
    host_launches_after=1,
    launch_overhead_before_us=20.0,
    launch_overhead_after_us=25.0,
    gpu_idle_pct_before=40.0,
    gpu_idle_pct_after=5.0,
    idle_reduction_pct_points=35.0,
    execution_time_before_ms=1.00,
    execution_time_after_ms=0.75,
    execution_time_reduction_pct=25.0,
    default_max_pending_launches=DEFAULT_DP_PENDING_LAUNCH_COUNT,
)


@dataclass(frozen=True)
class DecodeLaunchOverheadModel:
    """LLM autoregressive decode CPU launch overhead model (nvidia-devops V3 Ch 10)."""

    cpu_launch_us: float
    gpu_kernel_us: float
    num_kernels_in_micro_chain: int
    total_cpu_launch_us: float
    total_gpu_exec_us: float
    cpu_overhead_share_pct: float
    output_tokens: int
    model_layers: int
    total_uncaptured_launches: int
    total_graph_replays: int


def analyze_decode_launch_overhead(
    cpu_launch_us: float = 15.0,
    gpu_kernel_us: float = 3.0,
    num_kernels_in_micro_chain: int = 3,
    output_tokens: int = 500,
    model_layers: int = 80,
) -> DecodeLaunchOverheadModel:
    """Model the V3 Ch 10 3-kernel (15 us launch vs 3 us kernel) and 80-layer * 500-token scenarios."""
    if cpu_launch_us <= 0 or gpu_kernel_us <= 0 or num_kernels_in_micro_chain <= 0:
        raise ValueError("Launch durations and kernel count must be positive")
    if output_tokens <= 0 or model_layers <= 0:
        raise ValueError("output_tokens and model_layers must be positive")

    tot_cpu = cpu_launch_us * num_kernels_in_micro_chain
    tot_gpu = gpu_kernel_us * num_kernels_in_micro_chain
    share_pct = round(cpu_launch_us / (cpu_launch_us + gpu_kernel_us) * 100.0, 1)
    return DecodeLaunchOverheadModel(
        cpu_launch_us=cpu_launch_us,
        gpu_kernel_us=gpu_kernel_us,
        num_kernels_in_micro_chain=num_kernels_in_micro_chain,
        total_cpu_launch_us=tot_cpu,
        total_gpu_exec_us=tot_gpu,
        cpu_overhead_share_pct=share_pct,
        output_tokens=output_tokens,
        model_layers=model_layers,
        total_uncaptured_launches=output_tokens * model_layers,
        total_graph_replays=output_tokens,
    )


def recommend_roofline_orchestration(
    regime: str,
    launch_overhead_dominant: bool = False,
) -> Dict[str, str]:
    """Roofline-guided scheduling and orchestration decision helper (ASP Ch 12 Figure 12-17 & V3 Ch 10)."""
    if regime == "memory_bound":
        return {
            "regime": "memory_bound",
            "primary_strategy": "Overlap transfers with CUDA streams, cudaMemcpyAsync, and lower precision (FP16/FP8/FP4)",
            "graph_benefit": "Modest unless kernel durations are microsecond-scale",
        }
    if regime == "compute_bound":
        if launch_overhead_dominant:
            return {
                "regime": "compute_bound_launch_limited",
                "primary_strategy": "Eliminate idle launch gaps with kernel fusion, persistent kernels, CUDA Graphs, or device-initiated launches",
                "graph_benefit": "High (pushes utilization toward flat compute roof)",
            }
        return {
            "regime": "compute_bound_saturated",
            "primary_strategy": "Use Tensor Cores, 2:4 sparsity, and warp-specialized / cluster pipelines",
            "graph_benefit": "Low (long kernels dominate host submission overhead)",
        }
    if regime == "intermediate":
        return {
            "regime": "intermediate",
            "primary_strategy": "Increase concurrency via parallel streams, concurrent CUDA Graphs, or multi-instance persistent kernels",
            "graph_benefit": "Moderate to high when combined with multi-stream concurrency",
        }
    raise ValueError(f"Unknown roofline regime: {regime}")


@dataclass(frozen=True)
class V3Lab04RegressionSummary:
    """nvidia-devops Volume 03 Ch 12 & Lab 04 controlled regressions and diagnostics."""

    total_elements: int
    baseline_chunk_elements: int
    tiny_chunk_elements: int
    chunk_count_multiplier: int
    baseline_ms: float
    sync_regression_ms: float
    sync_slowdown_factor: float
    tiny_chunk_regression_ms: float
    tiny_chunk_slowdown_factor: float
    pageable_regression_ms: float
    pageable_slowdown_factor: float
    sanitizer_fault_block: int
    sanitizer_fault_thread: int
    sanitizer_block_dim: int
    sanitizer_fault_global_idx: int
    sanitizer_array_bound: int
    fb_free_mib: int
    reserved_unallocated_mib: int
    fragmented_blocks: int
    failed_alloc_mib: int


def evaluate_v3_lab04_diagnostics() -> V3Lab04RegressionSummary:
    """Return verified metrics from nvidia-devops Volume 03 Ch 12 & Lab 04."""
    total_elems = 67_108_864
    base_chunk = 4_194_304  # 16 MiB of FP32
    tiny_chunk = 4_096      # 16 KiB of FP32
    base_ms = 812.4
    sync_ms = 1928.3
    tiny_ms = 3140.9
    page_ms = 2214.8
    blk = 3906
    thr = 287
    bdim = 256
    return V3Lab04RegressionSummary(
        total_elements=total_elems,
        baseline_chunk_elements=base_chunk,
        tiny_chunk_elements=tiny_chunk,
        chunk_count_multiplier=base_chunk // tiny_chunk,
        baseline_ms=base_ms,
        sync_regression_ms=sync_ms,
        sync_slowdown_factor=round(sync_ms / base_ms, 2),
        tiny_chunk_regression_ms=tiny_ms,
        tiny_chunk_slowdown_factor=round(tiny_ms / base_ms, 2),
        pageable_regression_ms=page_ms,
        pageable_slowdown_factor=round(page_ms / base_ms, 2),
        sanitizer_fault_block=blk,
        sanitizer_fault_thread=thr,
        sanitizer_block_dim=bdim,
        sanitizer_fault_global_idx=blk * bdim + thr,
        sanitizer_array_bound=1_000_003,
        fb_free_mib=1895,
        reserved_unallocated_mib=1240,
        fragmented_blocks=340,
        failed_alloc_mib=512,
    )
