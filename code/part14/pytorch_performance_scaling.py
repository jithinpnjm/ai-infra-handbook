#!/usr/bin/env python3
"""Chapter 14.8 model: PyTorch performance: profiling, tuning and scaling.

Models every profiling table, compiler speedup, CUDA Graph Tree & FireworksAI shared-pool
batch order, CUDA caching allocator `roundup_power2_divisions` & fragmentation savings,
`SuperOffload` / `GraceAdam` superchip offload, `DDP`/`FSDP`/`SimpleFSDP`/`TorchTitan`/
`AsyncTP`/`AutoParallel` distributed scaling metrics, `HTA` multi-GPU trace analysis,
`PyTorch HUD` CI regression gate, and `MLPerf Logging` (`:::MLL`) step breakdown from:
  - *AI Systems Performance Engineering* (Chris Fregly), Chapter 13:
    * Table 13-1: 9 profiling & visualization tools (`PyTorch profiler (Kineto)`, `nsys`,
      `ncu`, `PyTorch memory profiler`, `Linux perf`, `HTA`, `Perfetto`, `TorchEval`, `ExecuTorch`)
    * Table 13-2: Top 10 MoE operations by `self_cuda_time_total` (`138.00 ms` total across
      `64` experts: `aten::matmul` `43.00 ms`/`128` calls, `aten::linear` `35.50 ms`/`64` calls,
      `dispatch` `18.70 ms` + `combine` `12.10 ms` = `30.80 ms`, `aten::layer_norm` `10.20 ms`/
      `16` calls, `aten::softmax` `5.70 ms`/`4` calls, `aten::scatter` `4.10 ms`/`16` calls,
      `aten::gather` `3.60 ms`/`16` calls, `aten::to` `2.90 ms`/`8` calls, `aten::add_`
      `2.20 ms`/`64` calls)
    * Table 13-3: Nsight Systems `nvtx_gpu_proj_sum` (`train_step` `138.0 ms` child = `forward`
      `60.5 ms` [`130` instances] + `backward` `58.3 ms` [`130` instances] + `optimizer_step`
      `19.2 ms` [`1` instance bracketing `64` `aten::add_` kernels])
    * Table 13-4: Nsight Compute `matmul` Roofline shift (`Baseline`: `50%` FLOPS, `70%` mem BW,
      `60%` occ [memory-bound] -> `Optimized`: `85%` FLOPS, `40%` mem BW, `80%` occ [compute-bound];
      `25%–50%` latency-hiding occupancy note)
    * Linux `perf stat` (`0.600` CPUs, `1,200.345 msec`, `2,400,567,890` cycles at `~2.0 GHz`,
      `3,800,123,456` instructions = `1.58` IPC vs `8` max IPC on ARM Neoverse V2 Grace core,
      `12,345,678` cache-misses [`0.32%`], `4,567,890` branch-misses [`0.12%`], `1.234567890 s`) &
      `perf record -F 2000 -g --call-graph dwarf` / `perf report` (`45.0%` `py::forward`, `20.5%`
      `aten::matmul`, `10.2%` `dataloader_iter_next`, `8.7%` `ncclAllReduce`, `5.3%` `read`) +
      Grace-Blackwell `nvidia_nvlink_c2c0_pmu_0/cycles` (`3,567,890,123` cycles, `45,678,901` CPU
      cycles, `7,890,123` cache-misses, `2.345678901 s`)
    * MoE `torch.compile` step time (`248 ms` eager -> `173 ms` compiled = `30.24%` / `~30%` faster,
      `1.43x` speedup vs `< 10%` on single-GEMM dense models), Table 13-5 compilation modes
      (`default`, `reduce-overhead`, `max-autotune`, `max-autotune-no-cudagraphs`), Regional
      Compilation (`nested_compile_region`), `SDPA` / `FlexAttention` / `FlexDecoding` /
      `context_parallel`, `torchao` (`INT8`/`FP8` + `2:4` sparsity)
    * CUDA Graph Trees & FireworksAI decreasing-batch (`[8, 4, 2, 1]`) shared graph pool (`96`
      worst-case batch vs `64` normal max), `PYTORCH_ALLOC_CONF` (`max_split_size_mb:256`,
      `roundup_power2_divisions:[256:1,512:2,1024:4,>:8]` rounding `600 MB` -> `768 MB`, and
      `expandable_segments:True,max_split_size_mb:128,garbage_collection_threshold:0.8` reducing
      reserved VRAM from `768 MB` down to `600 MB`), `SuperOffload` (`STV` + `GraceAdam` on ARM SVE
      `32` vector / `16` predicate registers), `CUDAPluggableAllocator` + `MemPool` (`ncclMemAlloc`
      on `1.8 TB/s` bidir / `900 GB/s` unidir Blackwell NVLink 5, `max_entries=100000`), `UCX`
      (`NCCL_NET=UCX`, `NCCL_PLUGIN_P2P=ucx`, `UCX_TLS=rc,self,gdr_copy,cuda_copy`), `PyTorch
      Symmetric Memory` (`all_to_all_v`, `one_shot_all_reduce`, `triton.nvshmem.put()/get()`)
    * Distributed scaling (`DDP` `25 MB` default bucket, `FSDP` `transformer_auto_wrap_policy`
      `min_num_params=int(1e8)` = `100,000,000`, `FULL_SHARD` vs `HYBRID_SHARD` vs `SHARD_GRAD_OP`,
      `SimpleFSDP` `-28%` memory & `+69%` throughput vs eager `FSDP2`, `TorchTitan`, `AsyncTP`,
      `AutoParallel`), Multi-GPU profiling with `HTA` (`8` ranks) & `Perfetto`, CI (`TorchBench`
      `--iters 10 --batch-size 4` & `PyTorch HUD` `>= 5%` regression over `3` runs), and Table 13-6
      (`MLPerf Logging` `:::MLL` `24.0 ms` step = `10.5 ms` [`43.8%`] forward + `9.0 ms` [`37.5%`]
      backward + `4.0 ms` [`16.7%`] all-reduce + `0.5 ms` [`2.1%`] other).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


GRACE_NEOVERSE_V2_MAX_IPC: int = 8
GRACE_MEASURED_IPC: float = 1.58
GRACE_TASK_CLOCK_MSEC: float = 1200.345
GRACE_CPUS_UTILIZED: float = 0.600
GRACE_CYCLES: int = 2_400_567_890
GRACE_INSTRUCTIONS: int = 3_800_123_456
GRACE_CACHE_MISSES: int = 12_345_678
GRACE_CACHE_MISS_PCT: float = 0.32
GRACE_BRANCH_MISSES: int = 4_567_890
GRACE_BRANCH_MISS_PCT: float = 0.12
GRACE_ELAPSED_SEC: float = 1.234567890
NVLINK_C2C_PMU_CYCLES: int = 3_567_890_123
NVLINK_C2C_HOST_CYCLES: int = 45_678_901
NVLINK_C2C_CACHE_MISSES: int = 7_890_123
NVLINK_C2C_ELAPSED_SEC: float = 2.345678901

GRACE_SVE_VECTOR_REGISTERS: int = 32
GRACE_SVE_PREDICATE_REGISTERS: int = 16
DDP_DEFAULT_BUCKET_CAP_MB: int = 25
FSDP_AUTOWRAP_MIN_PARAMS: int = 100_000_000
HUD_REGRESSION_THRESHOLD_PCT: float = 5.0
HUD_SUSTAINED_RUNS_REQUIRED: int = 3
TORCHBENCH_CI_ITERS: int = 10
TORCHBENCH_CI_BATCH_SIZE: int = 4
SIMPLE_FSDP_MEM_REDUCTION_PCT: float = 28.0
SIMPLE_FSDP_THROUGHPUT_GAIN_PCT: float = 69.0
BLACKWELL_NVLINK5_BIDIR_BW_TBPS: float = 1.8
BLACKWELL_NVLINK5_UNIDIR_BW_GBPS: float = 900.0
MEMORY_HISTORY_MAX_ENTRIES: int = 100_000
FIREWORKS_DECREASING_BATCH_BUCKETS: Tuple[int, ...] = (8, 4, 2, 1)
CUDAGRAPH_NORMAL_MAX_BATCH: int = 64
CUDAGRAPH_WORST_CASE_BATCH: int = 96


@dataclass(frozen=True)
class ProfilingToolSpec:
    """Table 13-1 profiling and visualization tool entry (ASP Ch 13)."""

    tool: str
    scope: str
    typical_use_case: str


TABLE_13_1_PROFILING_TOOLS: Tuple[ProfilingToolSpec, ...] = (
    ProfilingToolSpec(
        "PyTorch profiler (Kineto)",
        "In-PyTorch op-level profiling (CPU/GPU)",
        "Fine-grained breakdown of model code, shape/memory stats, compile graph breaks",
    ),
    ProfilingToolSpec(
        "Nsight Systems (nsys)",
        "System-wide timeline (CPU, GPU, OS, I/O)",
        "End-to-end view of training/inference pipeline, data loader stalls, CPU-GPU overlap",
    ),
    ProfilingToolSpec(
        "Nsight Compute (ncu)",
        "GPU kernel analysis (per kernel)",
        "Deep dive into kernel efficiency, Roofline analysis, occupancy, memory vs compute bound",
    ),
    ProfilingToolSpec(
        "PyTorch memory profiler",
        "GPU memory usage by operation",
        "Diagnose fragmentation or high peak memory usage per operation over time",
    ),
    ProfilingToolSpec(
        "Linux perf",
        "CPU profiling and system events",
        "Identify Python interpreter/GIL overhead, CPU data loading stalls, NVLink-C2C PMUs",
    ),
    ProfilingToolSpec(
        "Holistic Trace Analysis (HTA)",
        "Distributed training trace visualization",
        "Multi-GPU/multinode trace aggregation, rank stragglers, compute-communication overlap",
    ),
    ProfilingToolSpec(
        "Chrome trace / Perfetto",
        "Offline trace viewing (web-based)",
        "Interactive web timeline viewing and Perfetto SQL queries across shared JSON traces",
    ),
    ProfilingToolSpec(
        "TorchEval (metrics)",
        "Model metrics and performance logging",
        "Correlate model throughput/latency alongside validation accuracy during scaling",
    ),
    ProfilingToolSpec(
        "ExecuTorch",
        "Deployment runtime for mobile, embedded, and edge devices",
        "Profile, export, and debug lightweight PyTorch models on edge/wearable runtimes",
    ),
)


@dataclass(frozen=True)
class OperatorProfileRow:
    """Table 13-2 PyTorch Profiler top-10 operation entry (ASP Ch 13)."""

    operation: str
    self_cuda_ms: float
    calls: int
    share_pct: float


TABLE_13_2_MOE_TOP10_OPS: Tuple[OperatorProfileRow, ...] = (
    OperatorProfileRow("aten::matmul", 43.00, 128, 31.16),
    OperatorProfileRow("aten::linear", 35.50, 64, 25.72),
    OperatorProfileRow("dispatch", 18.70, 2, 13.55),
    OperatorProfileRow("combine", 12.10, 2, 8.77),
    OperatorProfileRow("aten::layer_norm", 10.20, 16, 7.39),
    OperatorProfileRow("aten::softmax", 5.70, 4, 4.13),
    OperatorProfileRow("aten::scatter", 4.10, 16, 2.97),
    OperatorProfileRow("aten::gather", 3.60, 16, 2.61),
    OperatorProfileRow("aten::to", 2.90, 8, 2.10),
    OperatorProfileRow("aten::add_", 2.20, 64, 1.59),
)
TABLE_13_2_GEMM_COMBINED_MS: float = 78.50
TABLE_13_2_GEMM_COMBINED_PCT: float = 56.88
TABLE_13_2_ROUTING_COMBINED_MS: float = 30.80
TABLE_13_2_ROUTING_COMBINED_PCT: float = 22.32
TABLE_13_2_TOP4_COMBINED_MS: float = 109.30
TABLE_13_2_TOP4_COMBINED_PCT: float = 79.2


@dataclass(frozen=True)
class NvtxProjectionRow:
    """Table 13-3 Nsight Systems `nvtx_gpu_proj_sum` entry (ASP Ch 13)."""

    nvtx_range: str
    gpu_time_ms: float
    self_gpu_time_ms: float
    child_gpu_time_ms: float
    instances: int
    share_pct: float


TABLE_13_3_NVTX_PROJECTION: Dict[str, NvtxProjectionRow] = {
    "train_step": NvtxProjectionRow("train_step", 138.0, 0.0, 138.0, 1, 100.00),
    "forward": NvtxProjectionRow("forward", 60.5, 60.5, 0.0, 130, 43.84),
    "backward": NvtxProjectionRow("backward", 58.3, 58.3, 0.0, 130, 42.25),
    "optimizer_step": NvtxProjectionRow("optimizer_step", 19.2, 19.2, 0.0, 1, 13.91),
}


@dataclass(frozen=True)
class NcuRooflineShift:
    """Table 13-4 Nsight Compute Roofline metrics for expert `matmul` before and after tuning."""

    config: str
    peak_flops_pct: float
    peak_mem_bw_pct: float
    achieved_occupancy_pct: float
    regime: str


TABLE_13_4_NCU_ROOFLINE: Dict[str, NcuRooflineShift] = {
    "baseline": NcuRooflineShift("Baseline", 50.0, 70.0, 60.0, "Memory bound"),
    "optimized": NcuRooflineShift("Optimized", 85.0, 40.0, 80.0, "Compute bound"),
}


PERF_REPORT_HOTSPOTS_PCT: Dict[str, float] = {
    "py::forward": 45.0,
    "aten::matmul": 20.5,
    "dataloader_iter_next": 10.2,
    "ncclAllReduce": 8.7,
    "read": 5.3,
}


@dataclass(frozen=True)
class TorchCompileModeSpec:
    """Table 13-5 `torch.compile` mode characteristics (ASP Ch 13)."""

    mode: str
    compile_time: str
    extra_memory: str
    uses_cudagraphs: bool
    notable_features: str


TABLE_13_5_COMPILE_MODES: Dict[str, TorchCompileModeSpec] = {
    "default": TorchCompileModeSpec(
        "default",
        "Low-Medium",
        "No",
        False,
        "Balanced general fusion and basic autotuning",
    ),
    "reduce-overhead": TorchCompileModeSpec(
        "reduce-overhead",
        "Medium",
        "Yes (workspace caching)",
        True,
        "CUDA Graph Trees to eliminate per-iteration Python/launch overhead",
    ),
    "max-autotune": TorchCompileModeSpec(
        "max-autotune",
        "High (slow compile)",
        "Maybe (if graphs are used)",
        True,
        "Aggressive Triton/cuBLAS autotuning plus CUDA Graphs on GPU",
    ),
    "max-autotune-no-cudagraphs": TorchCompileModeSpec(
        "max-autotune-no-cudagraphs",
        "High",
        "No",
        False,
        "Aggressive kernel autotuning without CUDA Graph capture for dynamic shapes",
    ),
}


@dataclass(frozen=True)
class TorchCompileComparison:
    """MoE eager vs `torch.compile` step-time evaluation (ASP Ch 13)."""

    eager_ms: float
    compiled_ms: float
    time_saved_ms: float
    reduction_pct: float
    speedup_ratio: float


def evaluate_torch_compile_speedup(
    eager_ms: float = 248.0,
    compiled_ms: float = 173.0,
) -> TorchCompileComparison:
    """Compute step-time reduction and speedup ratio for `torch.compile` (ASP Ch 13)."""
    if eager_ms <= 0 or compiled_ms <= 0:
        raise ValueError("eager_ms and compiled_ms must be positive")
    saved = round(eager_ms - compiled_ms, 3)
    red_pct = round(saved / eager_ms * 100.0, 2)
    speedup = round(eager_ms / compiled_ms, 2)
    return TorchCompileComparison(
        eager_ms=eager_ms,
        compiled_ms=compiled_ms,
        time_saved_ms=saved,
        reduction_pct=red_pct,
        speedup_ratio=speedup,
    )


def round_up_caching_allocator_request(
    requested_mb: int,
    divisions_spec: Dict[int, int] | None = None,
) -> int:
    """Model `roundup_power2_divisions:[256:1,512:2,1024:4,>:8]` (ASP Ch 13).

    For a request in `(low_pow2, high_pow2]`, the range of width `low_pow2` is split
    into `divs` equal sub-buckets of step `low_pow2 // divs`.
    Example: for `600 MB` in `[512, 1024]` with `512:2`, step is `512 // 2 = 256 MB`,
    so buckets are `[512, 768, 1024]` and `600 MB` rounds up to `768 MB`.
    """
    if requested_mb <= 0:
        raise ValueError("requested_mb must be positive")
    spec = divisions_spec or {256: 1, 512: 2, 1024: 4}

    low = 256
    while low * 2 < requested_mb:
        low *= 2
    if requested_mb <= 256:
        return 256
    divs = spec.get(low, 8)
    step = low // divs
    offset = requested_mb - low
    steps_needed = (offset + step - 1) // step
    return low + steps_needed * step


def evaluate_alloc_conf_vram_savings(
    requested_mb: int = 600,
    unoptimized_reserved_mb: int = 768,
    expandable_segments: bool = True,
    max_split_size_mb: int = 128,
    gc_threshold: float = 0.8,
) -> Dict[str, float]:
    """Evaluate reserved VRAM reduction from `PYTORCH_ALLOC_CONF` tuning (`768 MB -> 600 MB`)."""
    if requested_mb <= 0 or unoptimized_reserved_mb < requested_mb:
        raise ValueError("requested_mb must be > 0 and <= unoptimized_reserved_mb")
    if not (0.0 < gc_threshold <= 1.0) or max_split_size_mb <= 0:
        raise ValueError("gc_threshold must be in (0, 1] and max_split_size_mb > 0")

    optimized_reserved_mb = requested_mb if expandable_segments else unoptimized_reserved_mb
    saved_mb = unoptimized_reserved_mb - optimized_reserved_mb
    saved_pct = round(saved_mb / unoptimized_reserved_mb * 100.0, 2)
    return {
        "requested_mb": float(requested_mb),
        "unoptimized_reserved_mb": float(unoptimized_reserved_mb),
        "optimized_reserved_mb": float(optimized_reserved_mb),
        "saved_mb": float(saved_mb),
        "saved_pct": saved_pct,
        "max_split_size_mb": float(max_split_size_mb),
        "gc_threshold": gc_threshold,
    }


def evaluate_simple_fsdp_scaling(
    baseline_memory_gb: float = 64.0,
    baseline_tps: float = 10_000.0,
) -> Dict[str, float]:
    """Compute `SimpleFSDP` memory (`-28%`) and throughput (`+69%`) gains vs eager `FSDP2`."""
    if baseline_memory_gb <= 0 or baseline_tps <= 0:
        raise ValueError("baseline_memory_gb and baseline_tps must be positive")
    opt_mem = round(baseline_memory_gb * (1.0 - SIMPLE_FSDP_MEM_REDUCTION_PCT / 100.0), 3)
    opt_tps = round(baseline_tps * (1.0 + SIMPLE_FSDP_THROUGHPUT_GAIN_PCT / 100.0), 2)
    return {
        "baseline_memory_gb": baseline_memory_gb,
        "simple_fsdp_memory_gb": opt_mem,
        "memory_reduction_pct": SIMPLE_FSDP_MEM_REDUCTION_PCT,
        "baseline_tps": baseline_tps,
        "simple_fsdp_tps": opt_tps,
        "throughput_gain_pct": SIMPLE_FSDP_THROUGHPUT_GAIN_PCT,
    }


def evaluate_async_tp_overlap(
    compute_wave_ms: float,
    tp_allgather_ms: float,
    overlap_efficiency: float = 0.85,
) -> Dict[str, float]:
    """Compare sequential TP vs TorchTitan `AsyncTP` dual-stream SM-wave overlap (ASP Ch 13)."""
    if compute_wave_ms <= 0 or tp_allgather_ms < 0 or not (0.0 <= overlap_efficiency <= 1.0):
        raise ValueError("compute_wave_ms > 0, tp_allgather_ms >= 0, overlap_efficiency in [0, 1]")
    sequential_ms = round(compute_wave_ms + tp_allgather_ms, 3)
    hidden_ms = min(compute_wave_ms, tp_allgather_ms * overlap_efficiency)
    async_tp_ms = round(sequential_ms - hidden_ms, 3)
    speedup_pct = round((sequential_ms - async_tp_ms) / sequential_ms * 100.0, 2)
    return {
        "sequential_ms": sequential_ms,
        "async_tp_ms": async_tp_ms,
        "hidden_comm_ms": round(hidden_ms, 3),
        "step_time_reduction_pct": speedup_pct,
    }


def analyze_hta_multi_gpu_traces(
    rank_compute_ms: Sequence[float],
    rank_comm_ms: Sequence[float],
    step_wall_ms: float,
) -> Dict[str, float | int]:
    """Compute HTA multi-GPU compute/communication/idle breakdown and pinpoint straggler rank."""
    if not rank_compute_ms or len(rank_compute_ms) != len(rank_comm_ms) or step_wall_ms <= 0:
        raise ValueError("rank_compute_ms and rank_comm_ms must be equal-length non-empty sequences")
    n_ranks = len(rank_compute_ms)
    idle_ms_per_rank: List[float] = []
    for c_ms, m_ms in zip(rank_compute_ms, rank_comm_ms):
        if c_ms < 0 or m_ms < 0 or (c_ms + m_ms) > step_wall_ms:
            raise ValueError("invalid per-rank compute/comm time vs step_wall_ms")
        idle_ms_per_rank.append(round(step_wall_ms - (c_ms + m_ms), 3))

    straggler_rank = max(range(n_ranks), key=lambda r: rank_compute_ms[r])
    most_idle_rank = max(range(n_ranks), key=lambda r: idle_ms_per_rank[r])
    avg_compute_pct = round(sum(rank_compute_ms) / (n_ranks * step_wall_ms) * 100.0, 2)
    avg_comm_pct = round(sum(rank_comm_ms) / (n_ranks * step_wall_ms) * 100.0, 2)
    avg_idle_pct = round(sum(idle_ms_per_rank) / (n_ranks * step_wall_ms) * 100.0, 2)
    return {
        "num_ranks": n_ranks,
        "straggler_rank": straggler_rank,
        "most_idle_rank": most_idle_rank,
        "max_idle_ms": max(idle_ms_per_rank),
        "avg_compute_pct": avg_compute_pct,
        "avg_comm_pct": avg_comm_pct,
        "avg_idle_pct": avg_idle_pct,
    }


def evaluate_hud_ci_regression_gate(
    baseline_tps: float,
    recent_runs_tps: Sequence[float],
    threshold_pct: float = HUD_REGRESSION_THRESHOLD_PCT,
    sustained_runs: int = HUD_SUSTAINED_RUNS_REQUIRED,
) -> Dict[str, bool | float | int]:
    """Evaluate PyTorch HUD / TorchBench CI regression gate (`>= 5%` drop over `3` consecutive runs)."""
    if baseline_tps <= 0 or not recent_runs_tps or threshold_pct <= 0 or sustained_runs <= 0:
        raise ValueError("baseline_tps, threshold_pct, sustained_runs must be > 0 and recent_runs_tps non-empty")

    consecutive_regressions = 0
    max_consecutive = 0
    latest_drop_pct = round((baseline_tps - recent_runs_tps[-1]) / baseline_tps * 100.0, 2)

    for tps in recent_runs_tps:
        drop_pct = (baseline_tps - tps) / baseline_tps * 100.0
        if drop_pct >= threshold_pct - 1e-9:
            consecutive_regressions += 1
            max_consecutive = max(max_consecutive, consecutive_regressions)
        else:
            consecutive_regressions = 0

    return {
        "baseline_tps": baseline_tps,
        "latest_drop_pct": latest_drop_pct,
        "max_consecutive_regressions": max_consecutive,
        "sustained_runs_required": sustained_runs,
        "threshold_pct": threshold_pct,
        "fail_ci_build": max_consecutive >= sustained_runs,
    }


@dataclass(frozen=True)
class MlperfStepBreakdown:
    """Table 13-6 MLPerf Logging (`:::MLL`) training step breakdown (ASP Ch 13)."""

    step_time_ms: float
    forward_ms: float
    forward_pct: float
    backward_ms: float
    backward_pct: float
    compute_total_ms: float
    compute_total_pct: float
    allreduce_ms: float
    allreduce_pct: float
    other_ms: float
    other_pct: float


def evaluate_mlperf_step_breakdown(
    forward_ms: float = 10.5,
    backward_ms: float = 9.0,
    allreduce_ms: float = 4.0,
    other_ms: float = 0.5,
) -> MlperfStepBreakdown:
    """Compute Table 13-6 MLPerf step time and component shares (ASP Ch 13)."""
    if forward_ms <= 0 or backward_ms <= 0 or allreduce_ms < 0 or other_ms < 0:
        raise ValueError("forward_ms and backward_ms must be > 0; allreduce_ms and other_ms >= 0")

    total = round(forward_ms + backward_ms + allreduce_ms + other_ms, 3)
    comp = round(forward_ms + backward_ms, 3)
    return MlperfStepBreakdown(
        step_time_ms=total,
        forward_ms=forward_ms,
        forward_pct=round(forward_ms / total * 100.0, 1),
        backward_ms=backward_ms,
        backward_pct=round(backward_ms / total * 100.0, 1),
        compute_total_ms=comp,
        compute_total_pct=round(comp / total * 100.0, 1),
        allreduce_ms=allreduce_ms,
        allreduce_pct=round(allreduce_ms / total * 100.0, 1),
        other_ms=other_ms,
        other_pct=round(other_ms / total * 100.0, 1),
    )
