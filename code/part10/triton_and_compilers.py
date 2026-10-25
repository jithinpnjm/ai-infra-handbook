#!/usr/bin/env python3
"""Chapter 10.19 model: Triton language and compilers: OpenAI Triton, torch.compile, XLA.

Models every compiler pipeline invariant, PrimTorch IR decomposition count, dynamic shape
guard, `torch._dynamo.explain` graph-break analysis, Triton SPMD launch geometry, TMA
tensor descriptor rule, persistent GEMM grid bound, Proton profiler benchmark, and OpenXLA
comparison from *AI Systems Performance Engineering* (Chris Fregly), Chapter 14:
  - PyTorch 2.x compiler stack: TorchDynamo (PEP 523 bytecode capture) -> AOT Autograd
    (joint forward + backward graph) -> PrimTorch IR (`> 2,000` ATen ops reduced to `~250`
    core primitives, functionalization `x.add_(y) -> aten::add + aten::copy_`) ->
    TorchInductor (Python loop IR -> OpenAI Triton -> LLVM NVPTX -> PTX)
  - `FlexAttention` (`85%-90%` of modern FlashAttention performance in forward & backward)
  - `toy_example` graph break diagnosis (`Graph Count: 3, Graph Break Count: 2, Op Count: 5`
    from `print` and `if b.sum() < 0:` -> fixed to `1` graph via `if not is_compiling()` +
    `torch.where` or `torch.cond`)
  - Table 14-1: 11 `TORCH_LOGS` flags, `TORCHDYNAMO_REPRO_AFTER="aot"`, `TORCHDYNAMO_REPRO_LEVEL=4`,
    and cuBLAS determinism (`CUBLAS_WORKSPACE_CONFIG=:4096:8` or `:16:8`)
  - Triton SPMD programming model: `BLOCK_SIZE = 1,024` elements per program vs `num_warps * 32`
    CUDA threads per block (`default 4 warps = 128 threads`, `8 warps = 256 threads` for
    `BLOCK_SIZE >= 2,048`, `16 warps = 512 threads` for `BLOCK_SIZE >= 4,096`)
  - Triton TMA tensor descriptors (`tl.make_tensor_descriptor`: 16-byte leading stride rule,
    contiguous inner dimension, `tl.dot -> tcgen05` UMMA accumulating in `256 KB` per-SM `TMEM`),
    warp specialization (`num_consumer_groups = 2`, `num_buffers_warp_spec = 3`), and
    `matmul_kernel_persistent` (`min(65536, MT * NT)`)
  - Triton Proton profiler `[M=8192, N=8192, K=512]` benchmark:
    * `cublas`: `174.920 ms` (`3928.623`)
    * `torch`: `174.671 ms` (`3934.214`)
    * `matmul_kernel`: `165.349 ms` (`4156.033`)
    * `matmul_kernel_persistent`: `159.352 ms` (`4312.421`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


PYTORCH_TOTAL_ATEN_OPS_APPROX: int = 2000
PRIMTORCH_CORE_PRIMITIVES_APPROX: int = 250
PEP_FRAME_EVALUATION_NUMBER: int = 523
FLEX_ATTENTION_EFFICIENCY_RANGE_PCT: Tuple[float, float] = (85.0, 90.0)
DYNAMIC_SHAPE_PADDING_THRESHOLD_PCT: Tuple[float, float] = (10.0, 20.0)
PERSISTENT_MATMUL_MAX_GRID_PROGRAMS: int = 65536
TMA_STRIDE_ALIGNMENT_BYTES: int = 16
BLACKWELL_TMEM_PER_SM_KB: int = 256


TABLE_14_1_TORCH_LOGS: Dict[str, str] = {
    "graph_breaks": "Logs graph break events",
    "dynamo": "Verbose logging from TorchDynamo",
    "aot_graphs": "Verbose logging from AOT Autograd",
    "inductor": "Verbose logging from TorchInductor",
    "graph_outputs": "Shows the compiled FX graphs",
    "graph_code": "Dumps the Python code for each FX graph that TorchDynamo produces",
    "dynamic": "Traces decisions around dynamic shapes and when dimensions are marked as dynamic",
    "perf_hints": "Shows you the missed performance-optimization opportunities",
    "output_code": "Prints the generated code for each compiled graph",
    "recompiles": "Logs recompilation triggers",
    "guards": "Logs guards and guard evaluations",
}


COMPILER_STANCES: Dict[str, str] = {
    "default": "Compiles what it can, silently falling back to eager execution on unsupported code",
    "fail_on_recompile": "Raises an error if a graph break, unsupported op, or recompile occurs",
    "eager_on_recompile": "Runs in eager mode when a recompile would occur while reusing cached compiled graphs",
    "force_eager": "Uses eager mode and ignores all torch.compile directives",
}


@dataclass(frozen=True)
class DynamoExplainSummary:
    """`torch._dynamo.explain()` output model for `toy_example` before and after refactoring (ASP Ch 14)."""

    variant: str
    graph_count: int
    graph_break_count: int
    op_count: int
    break_reasons: Tuple[str, ...]
    cuda_graphs_eligible: bool


def analyze_dynamo_graph_breaks(
    has_unguarded_print: bool = True,
    has_python_tensor_branch: bool = True,
    dynamic_shapes_enabled: bool = False,
) -> DynamoExplainSummary:
    """Model `torch._dynamo.explain(toy_example)` before and after fixing `print()` and `if b.sum() < 0:`."""
    reasons: List[str] = []
    if has_unguarded_print:
        reasons.append("builtin: print [...ConstantVariable] False")
    if has_python_tensor_branch:
        reasons.append("generic_jump TensorVariable()")

    breaks = len(reasons)
    graphs = breaks + 1
    variant = "toy_example_unoptimized" if breaks > 0 else "model_where_or_cond_optimized"
    return DynamoExplainSummary(
        variant=variant,
        graph_count=graphs,
        graph_break_count=breaks,
        op_count=5,
        break_reasons=tuple(reasons),
        cuda_graphs_eligible=(breaks == 0 and not dynamic_shapes_enabled),
    )


@dataclass(frozen=True)
class TritonLaunchConfigPlan:
    """Triton SPMD program grid, warp count, thread count, and TMA descriptor validation (ASP Ch 14)."""

    n_elements: int
    block_size: int
    grid_programs: int
    num_warps: int
    threads_per_cuda_block: int
    elements_per_thread: float
    num_stages: int
    num_consumer_groups: int
    num_buffers_warp_spec: int
    tma_descriptor_valid: bool


def plan_triton_kernel_launch(
    n_elements: int = 10_000,
    block_size: int = 1024,
    num_stages: int = 2,
    leading_stride_bytes: int = 16,
    inner_dim_contiguous: bool = True,
    warp_specialize: bool = False,
) -> TritonLaunchConfigPlan:
    """Compute Triton `cdiv(n_elements, BLOCK_SIZE)` grid, recommended `num_warps` (`4, 8, 16`),
    and TMA descriptor validity (ASP Ch 14).
    """
    if n_elements <= 0 or block_size <= 0 or num_stages <= 0 or leading_stride_bytes <= 0:
        raise ValueError("n_elements, block_size, num_stages, and leading_stride_bytes must be positive")
    if block_size % 32 != 0:
        raise ValueError("block_size must be a multiple of 32 (warpSize)")

    grid_progs = (n_elements + block_size - 1) // block_size
    # ASP Ch 14 rule: default 4 warps (128 threads); push to 8 warps when BLOCK_SIZE >= 2048
    # and 16 warps when BLOCK_SIZE >= 4096
    if block_size >= 4096:
        num_warps = 16
    elif block_size >= 2048:
        num_warps = 8
    else:
        num_warps = 4

    threads_per_block = num_warps * 32
    elems_per_thread = round(block_size / threads_per_block, 2)
    tma_ok = (leading_stride_bytes % TMA_STRIDE_ALIGNMENT_BYTES == 0) and inner_dim_contiguous

    return TritonLaunchConfigPlan(
        n_elements=n_elements,
        block_size=block_size,
        grid_programs=grid_progs,
        num_warps=num_warps,
        threads_per_cuda_block=threads_per_block,
        elements_per_thread=elems_per_thread,
        num_stages=num_stages,
        num_consumer_groups=2 if warp_specialize else 0,
        num_buffers_warp_spec=3 if warp_specialize else 0,
        tma_descriptor_valid=tma_ok,
    )


@dataclass(frozen=True)
class PersistentMatmulGridPlan:
    """Grid and tile stepping plan for `matmul_kernel_persistent` (ASP Ch 14)."""

    m: int
    n: int
    k: int
    block_m: int
    block_n: int
    block_k: int
    mt_tiles: int
    nt_tiles: int
    total_output_tiles: int
    k_tiles_per_output: int
    persistent_grid_programs: int
    max_tiles_per_program: int


def plan_persistent_triton_matmul(
    m: int = 8192,
    n: int = 8192,
    k: int = 512,
    block_m: int = 128,
    block_n: int = 128,
    block_k: int = 64,
    max_grid_programs: int = PERSISTENT_MATMUL_MAX_GRID_PROGRAMS,
) -> PersistentMatmulGridPlan:
    """Model `matmul_kernel_persistent` (`grid = min(65536, MT * NT)`, `K_tiles = cdiv(K, BLOCK_K)`)."""
    if m <= 0 or n <= 0 or k < 0 or block_m <= 0 or block_n <= 0 or block_k <= 0:
        raise ValueError("Matrix and block dimensions must be positive (k >= 0)")

    mt = (m + block_m - 1) // block_m
    nt = (n + block_n - 1) // block_n
    total_tiles = mt * nt
    k_tiles = (k + block_k - 1) // block_k if k > 0 else 0
    grid_progs = min(max_grid_programs, total_tiles)
    max_tiles_per_prog = (total_tiles + grid_progs - 1) // grid_progs
    return PersistentMatmulGridPlan(
        m=m,
        n=n,
        k=k,
        block_m=block_m,
        block_n=block_n,
        block_k=block_k,
        mt_tiles=mt,
        nt_tiles=nt,
        total_output_tiles=total_tiles,
        k_tiles_per_output=k_tiles,
        persistent_grid_programs=grid_progs,
        max_tiles_per_program=max_tiles_per_prog,
    )


@dataclass(frozen=True)
class ProtonMatmulEntry:
    """Triton Proton profiler `[M=8192, N=8192, K=512]` benchmark entry (ASP Ch 14)."""

    name: str
    time_ms: float
    metric_score: float


PROTON_8192_MATMUL_BENCHMARK: Dict[str, ProtonMatmulEntry] = {
    "ROOT": ProtonMatmulEntry("ROOT", 168.314, 16331.291),
    "cublas": ProtonMatmulEntry("cublas [M=8192,N=8192,K=512]", 174.920, 3928.623),
    "matmul_kernel": ProtonMatmulEntry("matmul_kernel [M=8192,N=8192,K=512]", 165.349, 4156.033),
    "matmul_kernel_persistent": ProtonMatmulEntry("matmul_kernel_persistent [M=8192,N=8192,K=512]", 159.352, 4312.421),
    "torch": ProtonMatmulEntry("torch [M=8192,N=8192,K=512]", 174.671, 3934.214),
}
