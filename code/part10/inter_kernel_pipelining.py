#!/usr/bin/env python3
"""Chapter 10.17 model: Inter-kernel pipelining, synchronization and stream-ordered allocation.

Models every quantitative formula, shared-memory footprint, multi-stream timeline,
stream-ordered memory pool calculation, multi-GPU P2P/NCCL pipeline, and Programmatic
Dependent Launch (PDL) overlap model from *AI Systems Performance Engineering*
(Chris Fregly), Chapter 11:
  - 3-way H2D / Compute / D2H overlap across `asyncEngineCount >= 2` DMA copy engines
    (`MAX_CONCURRENT_GRIDS = 128`, `50%` throughput split when 2 streams contend on a saturated engine)
  - Stream-ordered memory allocator (`cudaMallocAsync` / `cudaFreeAsync`, `cudaMemPoolAttrReleaseThreshold`,
    `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync`, `16 MB` attention scratch buffers, `512 -> 1,024`
    variable-length sequence growth, layerwise pipelining `layers 0-5` on `stream 0` & `6-11` on `stream 1`)
  - Legacy default stream (`stream 0` global barrier) vs Per-Thread Default Stream (`PTDS`) vs
    explicit `cudaStreamNonBlocking` streams, plus `cudaEventRecord` / `cudaStreamWaitEvent` and
    `cudaLaunchHostFunc` deadlock rules
  - `warp_specialized_two_pipelines`: `blockDim = 96` (`3` warps), `2` pipelines (`pipe_lc`, `pipe_cs`)
    each of depth `2`, `TILE_SIZE = 1,024` (divisible by `128 = 32 * 4` for `float4`),
    `6 * 1,024 * 4 = 24,576 B` (`24 KiB`) dynamic SMEM across `NUM_STREAMS = 2` and `BATCHES = 8`
  - `launch_warp_specialized_cluster_pipeline_multistream`: `TILE_SIZE = 128` (`TILE_ELEMS = 16,384`),
    `3 * 16,384 * 4 = 196,608 B` (`192 KiB`) dynamic SMEM, `CLUSTER_BLOCKS = 4`, `blocksPerGrid = 132 * 4 = 528`,
    cooperative kernel SM serialization vs overlapped `cudaMallocAsync` + `cudaMemcpyAsync` H2D/D2H
  - Multi-GPU overlap (`layers 0-3` on GPU 0 + `cudaMemcpyPeerAsync` on DMA engine + `layers 4-7` on GPU 1,
    4-GPU `NCCL` ring all-reduce with 4 chunks `1-4`, `NIXL`, and `cudaStreamBeginCapture` with
    `cudaStreamCaptureModeGlobal`)
  - Programmatic Dependent Launch (`PDL`): `cudaTriggerProgrammaticLaunchCompletion()`,
    `cudaGridDependencySynchronize()`, `cudaLaunchAttributeProgrammaticStreamSerialization`, and
    `primary_gemm` / `secondary_gemm` with `__cluster_dims__(2,1,1)` (`TILE_M=128, TILE_K=128, TILE_N=128`,
    `131,072 B` = `128 KiB` static SMEM).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


MAX_CONCURRENT_GRIDS: int = 128  # Hard hardware limit on concurrent resident grids per GPU (ASP Ch 11)
BLACKWELL_MAX_DYNAMIC_SMEM_BYTES: int = 227_328  # ~227 KB per block on Blackwell
DEFAULT_ATTENTION_SCRATCH_BYTES: int = 16 * 1024 * 1024  # 16 MB (16,777,216 B) scratch buffer example (ASP Ch 11)


@dataclass(frozen=True)
class MultiStreamOverlapSummary:
    """Timeline comparison of serialized vs 3-way overlapped H2D + Compute + D2H across batches."""

    num_batches: int
    num_streams: int
    async_engine_count: int
    pinned_host_memory: bool
    use_stream_ordered_alloc: bool
    serial_total_ms: float
    overlapped_total_ms: float
    speedup_ratio: float
    per_stream_saturated_share_pct: float


def simulate_inter_kernel_stream_pipeline(
    num_batches: int = 8,
    num_streams: int = 2,
    h2d_ms: float = 1.0,
    compute_ms: float = 2.0,
    d2h_ms: float = 1.0,
    sync_malloc_ms: float = 0.5,
    async_malloc_ms: float = 0.02,
    async_engine_count: int = 2,
    pinned_host_memory: bool = True,
    use_stream_ordered_alloc: bool = True,
) -> MultiStreamOverlapSummary:
    """Compare a blocking `cudaMalloc` + default-stream pipeline against a non-blocking multi-stream
    pipeline with pinned host memory (`cudaMallocHost`) and `cudaMallocAsync` (ASP Ch 11).
    """
    if num_batches <= 0 or num_streams <= 0 or async_engine_count <= 0:
        raise ValueError("num_batches, num_streams, and async_engine_count must be positive")
    if h2d_ms < 0 or compute_ms <= 0 or d2h_ms < 0:
        raise ValueError("Stage durations must be non-negative and compute_ms > 0")

    serial_per_batch = sync_malloc_ms + h2d_ms + compute_ms + d2h_ms
    serial_total = num_batches * serial_per_batch

    if not pinned_host_memory or not use_stream_ordered_alloc or num_streams == 1:
        # Pageable memory or blocking cudaMalloc serializes across streams
        alloc_cost = async_malloc_ms if use_stream_ordered_alloc else sync_malloc_ms
        overlapped_total = num_batches * (alloc_cost + h2d_ms + compute_ms + d2h_ms)
    else:
        # Steady-state bottleneck per batch is max(h2d_ms, compute_ms, d2h_ms) + async_malloc_ms
        # plus prologue (h2d_ms) and epilogue (d2h_ms) of the pipeline
        stage_bottleneck = max(h2d_ms, compute_ms, d2h_ms) + async_malloc_ms
        overlapped_total = h2d_ms + num_batches * stage_bottleneck + d2h_ms

    # ASP Ch 11 p. 117: when 2 concurrent operations contend on a 100%-saturated resource, each gets 50%
    saturated_share_pct = round(100.0 / 2.0, 1)

    return MultiStreamOverlapSummary(
        num_batches=num_batches,
        num_streams=num_streams,
        async_engine_count=async_engine_count,
        pinned_host_memory=pinned_host_memory,
        use_stream_ordered_alloc=use_stream_ordered_alloc,
        serial_total_ms=round(serial_total, 3),
        overlapped_total_ms=round(overlapped_total, 3),
        speedup_ratio=round(serial_total / overlapped_total, 2),
        per_stream_saturated_share_pct=saturated_share_pct,
    )


@dataclass(frozen=True)
class TwoPipelineWarpSpecConfig:
    """Configuration for `warp_specialized_two_pipelines` (ASP Ch 11)."""

    tile_size_floats: int
    stages: int
    buffers_per_stage: int
    total_buffers: int
    dynamic_smem_bytes: int
    fits_blackwell_smem: bool
    is_float4_aligned: bool
    threads_per_block: int
    warps_per_block: int
    num_pipelines: int
    num_streams: int
    num_batches: int


def evaluate_two_pipeline_warp_spec(
    tile_size_floats: int = 1024,
    stages: int = 2,
    buffers_per_stage: int = 3,
    num_streams: int = 2,
    num_batches: int = 8,
) -> TwoPipelineWarpSpecConfig:
    """Validate `warp_specialized_two_pipelines` (`[A0|B0|C0|A1|B1|C1]`, `pipe_lc` + `pipe_cs`, ASP Ch 11)."""
    if tile_size_floats <= 0 or stages <= 0 or buffers_per_stage <= 0:
        raise ValueError("tile_size_floats, stages, and buffers_per_stage must be positive")
    if num_streams <= 0 or num_batches <= 0:
        raise ValueError("num_streams and num_batches must be positive")
    # static_assert((TILE_SIZE % (32 * 4)) == 0, "TILE_SIZE must be multiple of 128 for float4 vectorization")
    if tile_size_floats % 128 != 0:
        raise ValueError("tile_size_floats must be a multiple of 128 (32 lanes * 4 floats) for float4 vectorization")

    total_buffers = stages * buffers_per_stage
    smem_bytes = total_buffers * tile_size_floats * 4
    return TwoPipelineWarpSpecConfig(
        tile_size_floats=tile_size_floats,
        stages=stages,
        buffers_per_stage=buffers_per_stage,
        total_buffers=total_buffers,
        dynamic_smem_bytes=smem_bytes,
        fits_blackwell_smem=smem_bytes <= BLACKWELL_MAX_DYNAMIC_SMEM_BYTES,
        is_float4_aligned=(tile_size_floats % 128 == 0),
        threads_per_block=96,
        warps_per_block=3,
        num_pipelines=2,
        num_streams=num_streams,
        num_batches=num_batches,
    )


@dataclass(frozen=True)
class ClusterMultistreamConfig:
    """Configuration for `launch_warp_specialized_cluster_pipeline_multistream` (ASP Ch 11)."""

    tile_size: int
    tile_elems: int
    dynamic_smem_bytes: int
    cluster_blocks: int
    num_sms: int
    blocks_per_grid: int
    threads_per_block: int
    num_streams: int
    batch_length: int
    num_tiles_per_batch: int
    rows_per_block: int
    cooperative_kernels_serialize_on_sm: bool
    h2d_d2h_alloc_overlap_enabled: bool


def evaluate_cluster_multistream_launch(
    tile_size: int = 128,
    cluster_blocks: int = 4,
    num_sms: int = 132,
    num_streams: int = 2,
    batch_length: int = 65536,
) -> ClusterMultistreamConfig:
    """Validate `launch_warp_specialized_cluster_pipeline_multistream` (ASP Ch 11)."""
    if tile_size <= 0 or cluster_blocks <= 0 or num_sms <= 0 or num_streams <= 0 or batch_length <= 0:
        raise ValueError("All cluster multistream parameters must be positive")
    tile_elems = tile_size * tile_size
    if batch_length % tile_elems != 0:
        raise ValueError(f"batch_length ({batch_length}) must be a multiple of TILE_ELEMS ({tile_elems})")

    smem_bytes = 3 * tile_elems * 4
    if smem_bytes > BLACKWELL_MAX_DYNAMIC_SMEM_BYTES:
        raise ValueError(f"smem_bytes ({smem_bytes}) exceeds Blackwell dynamic SMEM limit ({BLACKWELL_MAX_DYNAMIC_SMEM_BYTES})")

    blocks_per_grid = num_sms * cluster_blocks
    rows_per_block = (tile_size + cluster_blocks - 1) // cluster_blocks
    return ClusterMultistreamConfig(
        tile_size=tile_size,
        tile_elems=tile_elems,
        dynamic_smem_bytes=smem_bytes,
        cluster_blocks=cluster_blocks,
        num_sms=num_sms,
        blocks_per_grid=blocks_per_grid,
        threads_per_block=96,
        num_streams=num_streams,
        batch_length=batch_length,
        num_tiles_per_batch=batch_length // tile_elems,
        rows_per_block=rows_per_block,
        cooperative_kernels_serialize_on_sm=True,
        h2d_d2h_alloc_overlap_enabled=(num_streams >= 2),
    )


@dataclass(frozen=True)
class StreamOrderedPoolPlan:
    """Stream-ordered memory pool (`cudaMemPool_t`) and LLM scratch allocation plan (ASP Ch 11)."""

    total_global_mem_bytes: int
    release_threshold_bytes: int
    batch_n_tokens: int
    batch_n1_tokens: int
    token_growth_factor: float
    attention_scratch_bytes: int
    layer_stage0_range: str
    layer_stage1_range: str
    pytorch_env_var: str


def plan_stream_ordered_pool(
    total_global_mem_gib: int = 192,
    threshold_fraction: float = 0.5,
    batch_n_tokens: int = 512,
    batch_n1_tokens: int = 1024,
    attention_scratch_mib: int = 16,
) -> StreamOrderedPoolPlan:
    """Model `cudaMemPoolAttrReleaseThreshold` (`prop.totalGlobalMem / 2`) and LLM variable-length
    scratch allocations (`16 MB`, `512 -> 1,024` tokens, layers `0-5` & `6-11`, ASP Ch 11).
    """
    if total_global_mem_gib <= 0 or not (0.0 < threshold_fraction <= 1.0):
        raise ValueError("total_global_mem_gib must be > 0 and threshold_fraction in (0, 1]")
    if batch_n_tokens <= 0 or batch_n1_tokens <= 0 or attention_scratch_mib <= 0:
        raise ValueError("Token counts and scratch MiB must be positive")

    total_bytes = total_global_mem_gib * (1024 ** 3)
    threshold_bytes = int(total_bytes * threshold_fraction)
    scratch_bytes = attention_scratch_mib * (1024 ** 2)
    return StreamOrderedPoolPlan(
        total_global_mem_bytes=total_bytes,
        release_threshold_bytes=threshold_bytes,
        batch_n_tokens=batch_n_tokens,
        batch_n1_tokens=batch_n1_tokens,
        token_growth_factor=round(batch_n1_tokens / batch_n_tokens, 2),
        attention_scratch_bytes=scratch_bytes,
        layer_stage0_range="0-5",
        layer_stage1_range="6-11",
        pytorch_env_var="PYTORCH_ALLOC_CONF=backend:cudaMallocAsync",
    )


@dataclass(frozen=True)
class ProgrammaticDependentLaunchModel:
    """Programmatic Dependent Launch (PDL) overlap model (`kernel_A` -> `kernel_B` and
    `primary_gemm` -> `secondary_gemm` with `__cluster_dims__(2,1,1)`, ASP Ch 11).
    """

    primary_prologue_and_main_ms: float
    primary_epilogue_ms: float
    secondary_total_ms: float
    standard_stream_total_ms: float
    pdl_overlapped_total_ms: float
    saved_ms: float
    cluster_dims: tuple[int, int, int]
    tile_m: int
    tile_k: int
    tile_n: int
    static_smem_bytes: int
    launch_attribute: str
    primary_device_call: str
    secondary_device_call: str


def model_programmatic_dependent_launch(
    primary_prologue_and_main_ms: float = 1.6,
    primary_epilogue_ms: float = 0.4,
    secondary_total_ms: float = 2.0,
    tile_m: int = 128,
    tile_k: int = 128,
    tile_n: int = 128,
    cluster_x: int = 2,
) -> ProgrammaticDependentLaunchModel:
    """Calculate execution time savings when `primary_gemm` triggers `secondary_gemm` via PDL
    (`cudaTriggerProgrammaticLaunchCompletion` -> `cudaGridDependencySynchronize`, ASP Ch 11).
    """
    if primary_prologue_and_main_ms <= 0 or primary_epilogue_ms < 0 or secondary_total_ms <= 0:
        raise ValueError("Kernel phase durations must be positive (epilogue >= 0)")
    if tile_m <= 0 or tile_k <= 0 or tile_n <= 0 or cluster_x <= 0:
        raise ValueError("Tile and cluster dimensions must be positive")

    primary_total = primary_prologue_and_main_ms + primary_epilogue_ms
    standard_total = primary_total + secondary_total_ms
    # With PDL, secondary_gemm starts as soon as primary_gemm finishes main work + flush
    # and overlaps with primary_epilogue_ms
    pdl_total = primary_prologue_and_main_ms + max(primary_epilogue_ms, secondary_total_ms)
    saved = standard_total - pdl_total

    # __shared__ float tileA[TILE_M * TILE_K]; __shared__ float tileB[TILE_K * TILE_N];
    static_smem = (tile_m * tile_k + tile_k * tile_n) * 4

    return ProgrammaticDependentLaunchModel(
        primary_prologue_and_main_ms=round(primary_prologue_and_main_ms, 3),
        primary_epilogue_ms=round(primary_epilogue_ms, 3),
        secondary_total_ms=round(secondary_total_ms, 3),
        standard_stream_total_ms=round(standard_total, 3),
        pdl_overlapped_total_ms=round(pdl_total, 3),
        saved_ms=round(saved, 3),
        cluster_dims=(cluster_x, 1, 1),
        tile_m=tile_m,
        tile_k=tile_k,
        tile_n=tile_n,
        static_smem_bytes=static_smem,
        launch_attribute="cudaLaunchAttributeProgrammaticStreamSerialization",
        primary_device_call="cudaTriggerProgrammaticLaunchCompletion",
        secondary_device_call="cudaGridDependencySynchronize",
    )
