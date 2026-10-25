#!/usr/bin/env python3
"""Chapter 10.20 model: Profiling tools: Nsight Systems, Nsight Compute, PyTorch profiler.

Models every profiling table, NVTX projection summary, Nsight Compute Roofline shift,
Linux `perf` Grace-Blackwell counter report, CUDA caching allocator power-of-two sub-bucket
rounding rule, `SimpleFSDP` gain, CI regression gate, and MLPerf step-time breakdown from:
  - *AI Systems Performance Engineering* (Chris Fregly), Chapter 13:
    * Table 13-1: 9 profiling & visualization tools (`PyTorch profiler (Kineto)`, `nsys`,
      `ncu`, `PyTorch memory profiler`, `Linux perf`, `HTA`, `Perfetto`, `TorchEval`, `ExecuTorch`)
    * Table 13-2: Top 10 MoE operations by `self_cuda_time_total` (`138.00 ms` total across
      `64` experts: `aten::matmul` `43.00 ms`/`128` calls, `aten::linear` `35.50 ms`/`64` calls,
      `dispatch` `18.70 ms` + `combine` `12.10 ms` = `30.80 ms`, ..., `aten::add_` `2.20 ms`/`64` calls)
    * Table 13-3: Nsight Systems `nvtx_gpu_proj_sum` (`train_step` `138.0 ms` child = `forward`
      `60.5 ms` [`130` instances] + `backward` `58.3 ms` [`130` instances] + `optimizer_step`
      `19.2 ms` [`1` instance bracketing `64` `aten::add_` kernels])
    * Table 13-4: Nsight Compute `matmul` Roofline shift (`Baseline`: `50%` FLOPS, `70%` mem BW,
      `60%` occ [memory-bound] -> `Optimized`: `85%` FLOPS, `40%` mem BW, `80%` occ [compute-bound])
    * Linux `perf stat` (`1.58` IPC vs `8` max IPC on ARM Neoverse V2 Grace core) & `perf report`
      (`45.0%` `py::forward`, `20.5%` `aten::matmul`, `10.2%` `dataloader_iter_next`,
      `8.7%` `ncclAllReduce`, `5.3%` `read`) + `nvidia_nvlink_c2c0_pmu_0/cycles/`
    * MoE `torch.compile` step time (`248 ms` eager -> `173 ms` compiled = `30.24%` / `~30%` faster),
      Table 13-5 compilation modes, `roundup_power2_divisions:[256:1,512:2,1024:4,>:8]`
      (`600 MB -> 768 MB`), `SuperOffload` (`GraceAdam` on ARM SVE `32` vector / `16` predicate regs),
      `SimpleFSDP` (`-28%` memory, `+69%` throughput), `DDP` `25 MB` default bucket,
      `PyTorch HUD` (`>= 5%` threshold over `3` runs), and Table 13-6 (`MLPerf` `24.0 ms` step)
  - `nvidia-devops` Volume 17 Chapter 2 (`chapter-02-profiling-tools-landscape.md`):
    * 4-layer Evidence Ladder (`DCGM` Thermometer -> `nsys` Traffic Camera -> `ncu` Microscope ->
      `PyTorch Profiler` Translator; H100 `4x` slower custom sparse Triton kernel case study).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


GRACE_NEOVERSE_V2_MAX_IPC: int = 8
GRACE_MEASURED_IPC: float = 1.58
GRACE_SVE_VECTOR_REGISTERS: int = 32
GRACE_SVE_PREDICATE_REGISTERS: int = 16
DDP_DEFAULT_BUCKET_CAP_MB: int = 25
HUD_REGRESSION_THRESHOLD_PCT: float = 5.0
HUD_SUSTAINED_RUNS_REQUIRED: int = 3
SIMPLE_FSDP_MEM_REDUCTION_PCT: float = 28.0
SIMPLE_FSDP_THROUGHPUT_GAIN_PCT: float = 69.0
BLACKWELL_NVLINK5_BIDIR_BW_TBPS: float = 1.8
BLACKWELL_NVLINK5_UNIDIR_BW_GBPS: float = 900.0


@dataclass(frozen=True)
class OperatorProfileRow:
    """Table 13-2 PyTorch Profiler top-10 operation entry (ASP Ch 13)."""

    operation: str
    self_cuda_ms: float
    calls: int


TABLE_13_2_MOE_TOP10_OPS: Tuple[OperatorProfileRow, ...] = (
    OperatorProfileRow("aten::matmul", 43.00, 128),
    OperatorProfileRow("aten::linear", 35.50, 64),
    OperatorProfileRow("dispatch", 18.70, 2),
    OperatorProfileRow("combine", 12.10, 2),
    OperatorProfileRow("aten::layer_norm", 10.20, 16),
    OperatorProfileRow("aten::softmax", 5.70, 4),
    OperatorProfileRow("aten::scatter", 4.10, 16),
    OperatorProfileRow("aten::gather", 3.60, 16),
    OperatorProfileRow("aten::to", 2.90, 8),
    OperatorProfileRow("aten::add_", 2.20, 64),
)


@dataclass(frozen=True)
class NvtxProjectionRow:
    """Table 13-3 Nsight Systems `nvtx_gpu_proj_sum` entry (ASP Ch 13)."""

    nvtx_range: str
    gpu_time_ms: float
    self_gpu_time_ms: float
    child_gpu_time_ms: float
    instances: int


TABLE_13_3_NVTX_PROJECTION: Dict[str, NvtxProjectionRow] = {
    "train_step": NvtxProjectionRow("train_step", 138.0, 0.0, 138.0, 1),
    "forward": NvtxProjectionRow("forward", 60.5, 60.5, 0.0, 130),
    "backward": NvtxProjectionRow("backward", 58.3, 58.3, 0.0, 130),
    "optimizer_step": NvtxProjectionRow("optimizer_step", 19.2, 19.2, 0.0, 1),
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


def round_up_caching_allocator_request(
    requested_mb: int,
    divisions_spec: Dict[int, int] | None = None,
) -> int:
    """Model `roundup_power2_divisions:[256:1,512:2,1024:4,>:8]` (ASP Ch 13 p. 818).

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


def select_profiling_tool_from_ladder(symptom: str) -> Dict[str, str]:
    """Map an operational symptom to the right tool on the V17 Ch 2 & ASP Ch 13 Evidence Ladder."""
    mapping = {
        "cluster_trend_drop": {
            "layer": "Layer 1: Macro Telemetry (The Thermometer)",
            "tool": "DCGM / Prometheus + nvidia-smi",
            "reason": "Continuous near-zero-overhead cluster telemetry over hours/days/weeks",
        },
        "dataloader_or_pcie_gap": {
            "layer": "Layer 2: System Timeline (The Traffic Camera / X-Ray)",
            "tool": "Nsight Systems (nsys)",
            "reason": "Correlates CPU threads, OS file I/O, PCIe/NVLink DMA, and GPU streams on one timeline",
        },
        "slow_custom_cuda_or_triton_kernel": {
            "layer": "Layer 3: Kernel Micro-Architecture (The Microscope)",
            "tool": "Nsight Compute (ncu)",
            "reason": "Inspects SM Roofline, register spills, L1/L2 hit rates, and warp stalls inside one kernel",
        },
        "pytorch_operator_attribution": {
            "layer": "Layer 4: Framework Operator Attribution (The Translator)",
            "tool": "PyTorch Profiler (Kineto) + HTA / Perfetto",
            "reason": "Maps Python/ATen ops (aten::matmul, dispatch) and per-op memory to GPU kernels",
        },
    }
    if symptom not in mapping:
        raise ValueError(f"Unknown symptom: {symptom}")
    return mapping[symptom]
