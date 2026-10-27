#!/usr/bin/env python3
"""Chapter 14.9: PyTorch compilers and kernels: torch.compile.

Pure Python 3 standard-library reference models for:
1. The 4-stage `torch.compile` pipeline (`TorchDynamo -> AOTAutograd -> PrimTorch -> TorchInductor`, ASP Ch 14):
   - `TorchDynamo`: CPython Frame Evaluation API (`PEP 523`), FX Graph capture (`Placeholder`, `aten::sin`,
     `aten::add`, `aten::sum`), shape/dtype/constant guards, and `torch.compiler.set_stance` (`default`,
     `fail_on_recompile`, `eager_on_recompile`, `force_eager`).
   - `AOTAutograd` (`AOT Autograd`): Ahead-of-time joint forward-backward FX graph capture via functional
     autograd, min-cut activation checkpointing partitioner (reusing intermediate buffers across forward/backward
     and reducing HBM traffic), and cross-pass operator fusion.
   - `PrimTorch` (`PrimTorch IR` / `Prims`): Decomposes `> 2,000` (`2,000+`) PyTorch ATen operators down to
     `~250` core primitive ops (`8.0x` / `87.5%` operator surface reduction) and functionalizes in-place
     mutations (`x.add_(y) -> %z = aten::add(x, y); %copy = aten::copy_(x, %z)`).
   - `TorchInductor`: Loop-level Python define-by-run IR (`Pointwise` with `sympy.Expr` index variables
     `i1 + i0*size1` and `2*size1 + i0`), lowering to OpenAI Triton -> LLVM NVPTX -> NVIDIA PTX without
     invoking `nvcc`, routing large GEMMs to `cuBLAS`/`cuBLASLt`/`CUTLASS`, compiling `FlexAttention` to
     `85%–90%` (`85.0%–90.0%`) of FlashAttention performance, and exporting ahead-of-time C++ artifacts via
     `torch.export()` + `AOTInductor`.
2. Compilation modes (`default`, `reduce-overhead`, `max-autotune`, `max-autotune-no-cudagraphs`),
   `AOTAutograd` + `TorchInductor` HBM memory-bandwidth fusion savings, and distributed `DDP` / `FSDP`
   (`use_original_params=True`) intentional communication graph breaks.
3. Dynamic shapes (`SymPy` symbolic expressions `z.size(0) = x.size(0) + y.size(0)`, guard evolution
   `sequence_length <= 256 -> sequence_length <= 1024`, `torch._dynamo.mark_dynamic(tensor, dim)` vs
   `dynamic=True` disabling CUDA Graphs, and the `10%–20%` sequence-length bucket-padding heuristic)
   plus `torch._dynamo.explain()` graph-break analysis (`toy_example`: `Graph Count: 3`,
   `Graph Break Count: 2`, `Op Count: 5` -> `1` graph / `0` breaks via `if not torch._dynamo.is_compiling():`
   + `torch.where` or `torch.cond`), `torch.compiler.allow_in_graph`, and guard-failure recompilation
   budget (`recompile_limit = 8`, `accumulated_recompile_limit = 64`).
4. Table 14-1 (`11` `TORCH_LOGS` flags), `TORCH_COMPILE_DEBUG=1`, `TORCH_TRACE` + `tlparse`, numerical
   accuracy minifier (`TORCHDYNAMO_REPRO_AFTER="aot"`, `TORCHDYNAMO_REPRO_LEVEL=4`), `fallback_random=True`,
   and cuBLAS determinism (`CUBLAS_WORKSPACE_CONFIG=:4096:8` [`32,768` bytes = `32 KB`] or `:16:8` [`128` bytes]).
5. OpenAI Triton `SPMD` programming model (`vector_add_kernel` with `BLOCK_SIZE = 1,024` and `n_elements = 10,000`
   -> `10` programs, `num_warps = 4` [`128` threads] -> `8` [`256` threads] at `BLOCK_SIZE >= 2,048` ->
   `16` [`512` threads] at `BLOCK_SIZE >= 4,096`), `@torch.library.triton_op("my_triton_lib::vector_add", mutates_args=())`
   + `wrap_triton` + `register_autograd(backward, setup_context=setup_context)`, TMA `16-byte` stride alignment
   (`tl.make_tensor_descriptor`), Blackwell `tcgen05` UMMA + `256 KB`/SM `TMEM`, warp specialization
   (`BLOCK_M=128, BLOCK_N=128, BLOCK_K=64, num_warps=8, num_stages=2, num_consumer_groups=2, num_buffers_warp_spec=3`),
   `matmul_kernel_persistent` (`min(65536, MT * NT)`), `Proton` profiler `[M=8192, N=8192, K=512]` benchmark
   (`matmul_kernel_persistent` `159.352 ms` [`4,312.421`, `1.10x`, `15.568 ms` saved, `8.90%` faster] vs
   `matmul_kernel` `165.349 ms` [`4,156.033`, `1.06x`, `9.571 ms` saved, `5.47%` faster] vs
   `torch` `174.671 ms` [`3,934.214`, `1.00x`, `0.249 ms` saved, `0.14%` faster] vs
   `cublas` `174.920 ms` [`3,928.623`, `1.00x`, `0.000 ms` saved, `0.00%`], `ROOT` `168.314 ms` [`16,331.291`]),
   and `AOTAutograd` min-cut fusion (`24` HBM passes = `1,610,612,736` bytes [`1.6106 GB`] -> `6` HBM passes =
   `402,653,184` bytes [`0.4027 GB`], `4.0x` / `75.0%` saved), plus `PyTorch XLA` / `OpenXLA` (`backend="openxla"`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# --- Core Compiler Constants from ASP Chapter 14 ---
PEP_FRAME_EVALUATION_NUMBER: int = 523
PYTORCH_ATEN_OPS_COUNT: int = 2000
PRIMTORCH_PRIMS_OPS_COUNT: int = 250
PRIMTORCH_REDUCTION_RATIO: float = 8.0
PRIMTORCH_REDUCTION_PCT: float = 87.5

DEFAULT_RECOMPILE_LIMIT: int = 8
DEFAULT_ACCUMULATED_RECOMPILE_LIMIT: int = 64

FLEX_ATTENTION_SPEED_PCT_RANGE: Tuple[float, float] = (85.0, 90.0)
DYNAMIC_PADDING_VARIATION_PCT_RANGE: Tuple[float, float] = (10.0, 20.0)
DYNAMIC_GUARD_INITIAL_SEQ_LEN: int = 256
DYNAMIC_GUARD_EXPANDED_SEQ_LEN: int = 1024

TMA_LEADING_STRIDE_ALIGNMENT_BYTES: int = 16
BLACKWELL_TMEM_CAPACITY_KB_PER_SM: int = 256
PERSISTENT_MATMUL_MAX_GRID_SIZE: int = 65536
PERSISTENT_MATMUL_K_THRESHOLD: int = 1024


COMPILE_PIPELINE_STAGES: Tuple[str, str, str, str] = (
    "TorchDynamo",
    "AOTAutograd",
    "PrimTorch",
    "TorchInductor",
)


COMPILER_MODES: Dict[str, Dict[str, object]] = {
    "default": {
        "cudagraphs": False,
        "autotune": False,
        "compile_overhead": "low",
        "description": "Fast compilation startup with TorchInductor fusion; no CUDA Graphs or exhaustive autotuning",
    },
    "reduce-overhead": {
        "cudagraphs": True,
        "autotune": False,
        "compile_overhead": "medium",
        "description": "Wraps compiled regions in CUDA Graphs to minimize Python/CPU launch overhead (requires static shapes)",
    },
    "max-autotune": {
        "cudagraphs": True,
        "autotune": True,
        "compile_overhead": "high",
        "description": "Benchmarks multiple Triton configs + cuBLAS/CUTLASS templates and enables CUDA Graphs for maximum speed",
    },
    "max-autotune-no-cudagraphs": {
        "cudagraphs": False,
        "autotune": True,
        "compile_overhead": "high",
        "description": "Full Triton/GEMM kernel autotuning without CUDA Graph capture (ideal for variable sequence lengths)",
    },
}


COMPILER_STANCES: Dict[str, str] = {
    "default": "Compiles supported regions and silently falls back to eager execution on graph breaks",
    "fail_on_recompile": "Raises a hard error on any graph break, unsupported op, or guard recompile (ideal for CI)",
    "eager_on_recompile": "Uses cached compiled graphs when valid, but falls back to eager mode instead of recompiling",
    "force_eager": "Ignores all torch.compile directives and runs entirely in eager mode",
}


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


@dataclass(frozen=True)
class AOTAutogradFusionReport:
    """Memory-bandwidth and kernel-launch savings from AOTAutograd + TorchInductor fusion."""

    num_tokens: int
    hidden_dim: int
    bytes_per_elem: int
    eager_forward_kernels: int
    eager_backward_kernels: int
    eager_total_kernels: int
    compiled_forward_kernels: int
    compiled_backward_kernels: int
    compiled_total_kernels: int
    eager_hbm_bytes: int
    compiled_hbm_bytes: int
    eager_hbm_gb: float
    compiled_hbm_gb: float
    hbm_traffic_reduction_ratio: float
    hbm_bandwidth_saved_pct: float


def evaluate_aot_autograd_fusion_savings(
    batch_size: int = 4,
    seq_len: int = 2048,
    hidden_dim: int = 4096,
    bytes_per_elem: int = 2,
    num_elementwise_ops_fwd: int = 5,
    num_elementwise_ops_bwd: int = 5,
    saved_tensors_eager: int = 4,
    saved_tensors_min_cut: int = 1,
) -> AOTAutogradFusionReport:
    """Quantify kernel launches and HBM memory traffic before and after AOTAutograd joint fusion.

    In eager mode, each elementwise op reads at least one tensor and writes one tensor (`2` HBM passes
    per op), plus `saved_tensors_eager` intermediate tensors are materialized for backward.
    With `AOTAutograd` + `TorchInductor`, the forward elementwise chain fuses into `1` kernel (`1` read +
    `1` write + `saved_tensors_min_cut` saved tensor via the min-cut partitioner) and the backward chain
    fuses into `1` kernel (`1` grad read + `saved_tensors_min_cut` read + `1` grad write).
    """
    if batch_size <= 0 or seq_len <= 0 or hidden_dim <= 0 or bytes_per_elem <= 0:
        raise ValueError("batch_size, seq_len, hidden_dim, and bytes_per_elem must be positive")
    if num_elementwise_ops_fwd <= 0 or num_elementwise_ops_bwd <= 0:
        raise ValueError("num_elementwise_ops_fwd and num_elementwise_ops_bwd must be positive")

    num_tokens = batch_size * seq_len
    tensor_bytes = num_tokens * hidden_dim * bytes_per_elem

    # Eager: each op reads 1 input and writes 1 output (2 tensor passes/op), plus backward reads saved tensors
    eager_fwd_passes = 2 * num_elementwise_ops_fwd
    eager_bwd_passes = 2 * num_elementwise_ops_bwd + saved_tensors_eager
    eager_total_passes = eager_fwd_passes + eager_bwd_passes

    # Compiled (AOTAutograd min-cut + Inductor fusion):
    # Forward fused kernel: 1 input read + 1 output write + saved_tensors_min_cut write
    # Backward fused kernel: 1 grad_out read + saved_tensors_min_cut read + 1 grad_in write
    compiled_fwd_passes = 2 + saved_tensors_min_cut
    compiled_bwd_passes = 2 + saved_tensors_min_cut
    compiled_total_passes = compiled_fwd_passes + compiled_bwd_passes

    eager_bytes = eager_total_passes * tensor_bytes
    compiled_bytes = compiled_total_passes * tensor_bytes

    eager_gb = round(eager_bytes / 1e9, 4)
    compiled_gb = round(compiled_bytes / 1e9, 4)
    ratio = round(eager_bytes / compiled_bytes, 2)
    saved_pct = round((1.0 - compiled_bytes / eager_bytes) * 100.0, 2)

    return AOTAutogradFusionReport(
        num_tokens=num_tokens,
        hidden_dim=hidden_dim,
        bytes_per_elem=bytes_per_elem,
        eager_forward_kernels=num_elementwise_ops_fwd,
        eager_backward_kernels=num_elementwise_ops_bwd,
        eager_total_kernels=num_elementwise_ops_fwd + num_elementwise_ops_bwd,
        compiled_forward_kernels=1,
        compiled_backward_kernels=1,
        compiled_total_kernels=2,
        eager_hbm_bytes=eager_bytes,
        compiled_hbm_bytes=compiled_bytes,
        eager_hbm_gb=eager_gb,
        compiled_hbm_gb=compiled_gb,
        hbm_traffic_reduction_ratio=ratio,
        hbm_bandwidth_saved_pct=saved_pct,
    )


@dataclass(frozen=True)
class DynamoExplainResult:
    """Model of `torch._dynamo.explain()` output for `toy_example` and FSDP/DDP subgraphs (ASP Ch 14)."""

    variant: str
    graph_count: int
    graph_break_count: int
    op_count: int
    break_reasons: Tuple[str, ...]
    cuda_graphs_compatible: bool


def analyze_dynamo_explain(
    has_print_side_effect: bool = True,
    has_data_dependent_if: bool = True,
    num_fsdp_comm_boundaries: int = 0,
    dynamic_shapes: bool = False,
) -> DynamoExplainResult:
    """Compute `Graph Count`, `Graph Break Count`, `Op Count`, and break reasons (ASP Ch 14).

    For `toy_example(a, b)`:
      - `x = a / (torch.abs(a) + 1)` (3 ops: `abs`, `add`, `div`)
      - `print("woo")` -> Break Reason 1: `builtin: print [...ConstantVariable] False`
      - `if b.sum() < 0:` (`sum`, `lt`) -> Break Reason 2: `generic_jump TensorVariable()`
      - `b = -b; return x * b` -> total `Graph Count: 3`, `Graph Break Count: 2`, `Op Count: 5`.
    When refactored with `if not torch._dynamo.is_compiling():` and `torch.where(b.sum() < 0, -b, b)`
    (or `torch.cond`), `Graph Count` drops to `1` and `Graph Break Count` drops to `0`.
    """
    if num_fsdp_comm_boundaries < 0:
        raise ValueError("num_fsdp_comm_boundaries must be non-negative")

    reasons: List[str] = []
    if has_print_side_effect:
        reasons.append("builtin: print [...ConstantVariable] False")
    if has_data_dependent_if:
        reasons.append("generic_jump TensorVariable()")
    for idx in range(num_fsdp_comm_boundaries):
        reasons.append(f"fsdp_all_gather_reduce_scatter_boundary_{idx + 1}")

    breaks = len(reasons)
    graphs = breaks + 1
    variant = "toy_example_broken" if (has_print_side_effect or has_data_dependent_if) else "refactored_single_graph"
    if num_fsdp_comm_boundaries > 0:
        variant = f"fsdp_sharded_{num_fsdp_comm_boundaries}_boundaries"

    return DynamoExplainResult(
        variant=variant,
        graph_count=graphs,
        graph_break_count=breaks,
        op_count=5,
        break_reasons=tuple(reasons),
        cuda_graphs_compatible=(breaks == 0 and not dynamic_shapes),
    )


@dataclass(frozen=True)
class RecompileBudgetReport:
    """Guard-failure recompilation budget and `mark_dynamic` symbolic shape analysis."""

    observed_seq_lengths: Tuple[int, ...]
    mark_dynamic_used: bool
    dynamic_flag: bool
    stance: str
    recompile_limit: int
    compilations_triggered: int
    guard_failures: int
    hit_recompile_limit: bool
    fell_back_to_eager: bool
    raised_fail_on_recompile: bool
    active_guard_expression: str
    cudagraphs_enabled: bool


def simulate_guard_recompilations(
    observed_seq_lengths: Tuple[int, ...] = (128, 256, 384, 512, 640, 768, 896, 1024, 1536, 2048),
    mark_dynamic_used: bool = False,
    dynamic_flag: bool = False,
    Constant_python_arg_changing: bool = False,
    stance: str = "default",
    recompile_limit: int = DEFAULT_RECOMPILE_LIMIT,
    mode: str = "reduce-overhead",
) -> RecompileBudgetReport:
    """Simulate TorchDynamo guard evaluations, symbolic shape specialization, and `recompile_limit = 8`.

    - If `Constant_python_arg_changing=True` (e.g., passing a changing Python float/int step counter or
      random seed per step without wrapping in a `torch.Tensor`), every step after step 1 triggers a
      guard failure until `recompile_limit` (`8`) is reached, forcing an eager fallback (or raising an
      exception under `stance="fail_on_recompile"`).
    - If `mark_dynamic_used=True` or `dynamic_flag=True`, the sequence dimension `s0` is symbolic from
      step 1 (`1` compilation, `0` guard failures), except when `seq_len` exceeds a range guard
      (`sequence_length <= 256 -> sequence_length <= 1024`).
    - Under `dynamic=None` (default) without `Constant_python_arg_changing`, step 1 compiles statically
      (`s0 == L0`), step 2 with a new shape triggers `1` extra recompile that generalizes `s0` symbolically
      (`2` total compilations, `1` guard failure).
    """
    if not observed_seq_lengths:
        raise ValueError("observed_seq_lengths must be non-empty")
    if recompile_limit <= 0:
        raise ValueError("recompile_limit must be positive")
    if stance not in COMPILER_STANCES:
        raise ValueError(f"Unsupported compiler stance: {stance}")
    if mode not in COMPILER_MODES:
        raise ValueError(f"Unsupported compiler mode: {mode}")

    if stance == "force_eager":
        return RecompileBudgetReport(
            observed_seq_lengths=observed_seq_lengths,
            mark_dynamic_used=mark_dynamic_used,
            dynamic_flag=dynamic_flag,
            stance=stance,
            recompile_limit=recompile_limit,
            compilations_triggered=0,
            guard_failures=0,
            hit_recompile_limit=False,
            fell_back_to_eager=True,
            raised_fail_on_recompile=False,
            active_guard_expression="eager_mode_forced",
            cudagraphs_enabled=False,
        )

    compilations = 1
    guard_failures = 0
    hit_limit = False
    eager_fallback = False
    raised_error = False

    if Constant_python_arg_changing:
        for _ in observed_seq_lengths[1:]:
            guard_failures += 1
            if stance == "fail_on_recompile":
                raised_error = True
                break
            if stance == "eager_on_recompile":
                eager_fallback = True
                break
            if guard_failures >= recompile_limit:
                hit_limit = True
                eager_fallback = True
                break
            compilations += 1
        guard_expr = f"python_constant_step == {observed_seq_lengths[min(compilations - 1, len(observed_seq_lengths) - 1)]}"
    elif mark_dynamic_used or dynamic_flag:
        max_len = max(observed_seq_lengths)
        bound = DYNAMIC_GUARD_INITIAL_SEQ_LEN if max_len <= DYNAMIC_GUARD_INITIAL_SEQ_LEN else max(DYNAMIC_GUARD_EXPANDED_SEQ_LEN, max_len)
        guard_expr = f"2 <= s0 <= {bound} (SymPy symbolic)"
    else:
        unique_lengths = []
        for length in observed_seq_lengths:
            if length not in unique_lengths:
                unique_lengths.append(length)
        if len(unique_lengths) > 1:
            guard_failures = 1
            if stance == "fail_on_recompile":
                raised_error = True
            elif stance == "eager_on_recompile":
                eager_fallback = True
            else:
                compilations = 2
        max_len = max(observed_seq_lengths)
        bound = DYNAMIC_GUARD_INITIAL_SEQ_LEN if max_len <= DYNAMIC_GUARD_INITIAL_SEQ_LEN else max(DYNAMIC_GUARD_EXPANDED_SEQ_LEN, max_len)
        guard_expr = f"s0 == {observed_seq_lengths[0]}" if len(unique_lengths) == 1 else f"s0 <= {bound} (auto-dynamic after 1 recompile)"

    mode_wants_cudagraphs = bool(COMPILER_MODES[mode]["cudagraphs"])
    has_dynamic_shapes = dynamic_flag or mark_dynamic_used or (len(set(observed_seq_lengths)) > 1)
    cudagraphs_active = mode_wants_cudagraphs and (not has_dynamic_shapes) and (not eager_fallback) and (not raised_error)

    return RecompileBudgetReport(
        observed_seq_lengths=observed_seq_lengths,
        mark_dynamic_used=mark_dynamic_used,
        dynamic_flag=dynamic_flag,
        stance=stance,
        recompile_limit=recompile_limit,
        compilations_triggered=compilations,
        guard_failures=guard_failures,
        hit_recompile_limit=hit_limit,
        fell_back_to_eager=eager_fallback,
        raised_fail_on_recompile=raised_error,
        active_guard_expression=guard_expr,
        cudagraphs_enabled=cudagraphs_active,
    )


def select_torch_logs_flag(symptom: str) -> str:
    """Map an engineering diagnostic symptom to the exact Table 14-1 `TORCH_LOGS` flag (ASP Ch 14)."""
    mapping = {
        "graph_break": "graph_breaks",
        "dynamo_trace": "dynamo",
        "joint_fwd_bwd_graph": "aot_graphs",
        "inductor_lowering": "inductor",
        "compiled_fx_graph": "graph_outputs",
        "fx_python_code": "graph_code",
        "symbolic_shapes": "dynamic",
        "missed_cudagraph_or_fusion": "perf_hints",
        "generated_triton_or_cpp": "output_code",
        "guard_recompile_reason": "recompiles",
        "guard_expressions": "guards",
    }
    if symptom not in mapping:
        raise ValueError(f"Unknown diagnostic symptom: {symptom}")
    return mapping[symptom]


@dataclass(frozen=True)
class TritonCustomOpSpec:
    """Specification and launch geometry for a `@torch.library.triton_op` kernel with autograd."""

    qualname: str
    mutates_args: Tuple[str, ...]
    has_wrap_triton: bool
    has_register_autograd: bool
    has_setup_context: bool
    n_elements: int
    block_size: int
    grid_programs: int
    num_warps: int
    threads_per_block: int
    elements_per_thread: float
    num_stages: int
    num_consumer_groups: int
    num_buffers_warp_spec: int
    tma_descriptor_valid: bool
    causes_dynamo_graph_break: bool


def build_triton_custom_op_spec(
    qualname: str = "my_triton_lib::vector_add",
    mutates_args: Tuple[str, ...] = (),
    has_wrap_triton: bool = True,
    has_register_autograd: bool = True,
    has_setup_context: bool = True,
    n_elements: int = 10_000,
    block_size: int = 1024,
    num_stages: int = 2,
    leading_stride_bytes: int = 16,
    inner_dim_contiguous: bool = True,
    warp_specialize: bool = False,
) -> TritonCustomOpSpec:
    """Validate a `@triton_op` custom Triton operator for `torch.compile` training/autograd (ASP Ch 14)."""
    if "::" not in qualname:
        raise ValueError("qualname must be namespaced as 'namespace::op_name'")
    if n_elements <= 0 or block_size <= 0 or num_stages <= 0 or leading_stride_bytes <= 0:
        raise ValueError("n_elements, block_size, num_stages, and leading_stride_bytes must be positive")
    if block_size % 32 != 0:
        raise ValueError("block_size must be a multiple of 32")

    grid_programs = (n_elements + block_size - 1) // block_size
    if block_size >= 4096:
        num_warps = 16
    elif block_size >= 2048:
        num_warps = 8
    else:
        num_warps = 4

    threads_per_block = num_warps * 32
    elems_per_thread = round(block_size / threads_per_block, 2)
    tma_ok = (leading_stride_bytes % TMA_LEADING_STRIDE_ALIGNMENT_BYTES == 0) and inner_dim_contiguous
    causes_break = not (has_wrap_triton and has_register_autograd and has_setup_context)

    return TritonCustomOpSpec(
        qualname=qualname,
        mutates_args=mutates_args,
        has_wrap_triton=has_wrap_triton,
        has_register_autograd=has_register_autograd,
        has_setup_context=has_setup_context,
        n_elements=n_elements,
        block_size=block_size,
        grid_programs=grid_programs,
        num_warps=num_warps,
        threads_per_block=threads_per_block,
        elements_per_thread=elems_per_thread,
        num_stages=num_stages,
        num_consumer_groups=2 if warp_specialize else 0,
        num_buffers_warp_spec=3 if warp_specialize else 0,
        tma_descriptor_valid=tma_ok,
        causes_dynamo_graph_break=causes_break,
    )


@dataclass(frozen=True)
class PersistentMatmulPlan:
    """1D persistent grid and tile-stepping schedule for `matmul_kernel_persistent` (ASP Ch 14)."""

    m: int
    n: int
    k: int
    block_m: int
    block_n: int
    block_k: int
    mt_tiles: int
    nt_tiles: int
    tile_count: int
    k_tiles: int
    grid_programs: int
    max_tiles_per_program: int


def plan_persistent_matmul_grid(
    m: int = 8192,
    n: int = 8192,
    k: int = 512,
    block_m: int = 128,
    block_n: int = 128,
    block_k: int = 64,
    max_grid_programs: int = PERSISTENT_MATMUL_MAX_GRID_SIZE,
) -> PersistentMatmulPlan:
    """Compute `MT`, `NT`, `TILE_COUNT`, `K_tiles`, and `min(65536, MT * NT)` for `matmul_kernel_persistent`."""
    if m <= 0 or n <= 0 or k < 0 or block_m <= 0 or block_n <= 0 or block_k <= 0:
        raise ValueError("Matrix and block dimensions must be positive (k >= 0)")

    mt = (m + block_m - 1) // block_m
    nt = (n + block_n - 1) // block_n
    tile_count = mt * nt
    k_tiles = (k + block_k - 1) // block_k if k > 0 else 0
    grid_progs = min(max_grid_programs, tile_count)
    max_tiles_per_prog = (tile_count + grid_progs - 1) // grid_progs

    return PersistentMatmulPlan(
        m=m,
        n=n,
        k=k,
        block_m=block_m,
        block_n=block_n,
        block_k=block_k,
        mt_tiles=mt,
        nt_tiles=nt,
        tile_count=tile_count,
        k_tiles=k_tiles,
        grid_programs=grid_progs,
        max_tiles_per_program=max_tiles_per_prog,
    )


@dataclass(frozen=True)
class ProtonBenchmarkComparison:
    """Triton `Proton` profiler comparison for `[M=8192, N=8192, K=512]` (ASP Ch 14)."""

    root_ms: float
    root_score: float
    cublas_ms: float
    cublas_score: float
    torch_ms: float
    torch_score: float
    tiled_triton_ms: float
    tiled_triton_score: float
    persistent_triton_ms: float
    persistent_triton_score: float
    single_gemm_gflops: float
    persistent_vs_cublas_saved_ms: float
    persistent_vs_cublas_speedup_x: float
    persistent_vs_cublas_reduction_pct: float
    tiled_vs_cublas_reduction_pct: float


def evaluate_proton_matmul_benchmark() -> ProtonBenchmarkComparison:
    """Return the exact ASP Ch 14 Triton Proton profiler benchmark for `[M=8192, N=8192, K=512]`."""
    root_ms, root_score = 168.314, 16331.291
    cublas_ms, cublas_score = 174.920, 3928.623
    torch_ms, torch_score = 174.671, 3934.214
    tiled_ms, tiled_score = 165.349, 4156.033
    pers_ms, pers_score = 159.352, 4312.421

    # Single GEMM 2*M*N*K FLOPs: 2 * 8192 * 8192 * 512 = 68,719,476,736 FLOPs (~68.72 GFLOPs)
    single_gflops = round((2 * 8192 * 8192 * 512) / 1e9, 2)
    saved_ms = round(cublas_ms - pers_ms, 3)
    speedup_x = round(cublas_ms / pers_ms, 2)
    pers_red_pct = round((cublas_ms - pers_ms) / cublas_ms * 100.0, 2)
    tiled_red_pct = round((cublas_ms - tiled_ms) / cublas_ms * 100.0, 2)

    return ProtonBenchmarkComparison(
        root_ms=root_ms,
        root_score=root_score,
        cublas_ms=cublas_ms,
        cublas_score=cublas_score,
        torch_ms=torch_ms,
        torch_score=torch_score,
        tiled_triton_ms=tiled_ms,
        tiled_triton_score=tiled_score,
        persistent_triton_ms=pers_ms,
        persistent_triton_score=pers_score,
        single_gemm_gflops=single_gflops,
        persistent_vs_cublas_saved_ms=saved_ms,
        persistent_vs_cublas_speedup_x=speedup_x,
        persistent_vs_cublas_reduction_pct=pers_red_pct,
        tiled_vs_cublas_reduction_pct=tiled_red_pct,
    )
