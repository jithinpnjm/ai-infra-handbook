#!/usr/bin/env python3
"""Chapter 10.16 model: Intra-kernel pipelining, warp specialization and thread block clusters.

Models every quantitative benchmark, SMEM budget, persistent-kernel launch calculation,
cooperative grid residency limit, and DSMEM / Thread Block Cluster pipeline table from
*AI Systems Performance Engineering* (Chris Fregly), Chapter 10:
  - Table 10-1: Double-buffered vs Warp-specialized `<cuda/pipeline>` variants
  - `gemm_tiled_pipeline`: multi-stage ring buffer (`TILE_SIZE = 32`, `STAGES = 2` or `3`)
  - `warp_specialized_pipeline_kernel`: 3-role SMEM budget (`3 * 112 * 112 * 4 = 150,528 B < 227,328 B`)
  - Tables 10-2, 10-3, and 10-5: 4-stage progression (`41.3 ms -> 20.5 ms -> 18.4 ms -> 17.2 ms`,
    `68% -> 92% -> 96% -> 97%` warp efficiency, `80 -> 155 -> 165 -> 170 GB/s` L2 throughput,
    `1.7B -> 1.05B -> 1.00B -> 0.98B` instructions)
  - Persistent kernel launch overhead & SM utilization (`1,000` tasks * `0.1 ms` = `100 ms` work +
    `1,000 * 0.02 ms = 20 ms` launch overhead vs `132` blocks * `256` threads = `33,792` threads at
    `12.5%` thread occupancy and `100%` active SMs; megakernels `1.2x-6.7x` decode speedup)
  - Cooperative grid sizing (`cudaOccupancyMaxActiveBlocksPerMultiprocessor`, `132 * 4 = 528` blocks,
    `combinedKernel` replacing `2,000` launches over `1,000` iterations with `1` launch)
  - Table 10-4: DSMEM CTA pair (`2x -> 1x` global loads, `50% -> 85%` L2 hit rate,
    `300 -> 150 GB/s` DRAM BW/CTA, `1.0x -> 0.6x` kernel time = `40%` speedup)
  - `warp_specialized_cluster_pipeline`: `TILE_SIZE = 128`, `3 * 16,384 * 4 = 196,608 B` (`192 KiB`)
    and TMA multicast vs DSMEM `map_shared_rank` selection rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


BLACKWELL_MAX_DYNAMIC_SMEM_BYTES: int = 227_328  # ~227 KB per block on Blackwell (ASP Ch 10)
BLACKWELL_MAX_WARPS_PER_SM: int = 64
BLACKWELL_MAX_THREADS_PER_SM: int = 2048
PORTABLE_MAX_CLUSTER_CTAS: int = 8
NONPORTABLE_MAX_CLUSTER_CTAS: int = 16


@dataclass(frozen=True)
class PipelineVariantProfile:
    """Table 10-2, Table 10-3, and Table 10-5 kernel progression metrics (ASP Ch 10)."""

    name: str
    kernel_time_ms: float
    warp_execution_efficiency_pct: float
    shared_mem_barrier_stall_level: str
    l2_throughput_gbps: float
    max_scalable_warps_per_sm: int
    instructions_billions: float
    speedup_vs_naive: float
    speedup_vs_prior_pct: float


TABLE_10_5_PIPELINE_PROGRESSION: Dict[str, PipelineVariantProfile] = {
    "naive_tiling": PipelineVariantProfile(
        name="Naive tiling",
        kernel_time_ms=41.3,
        warp_execution_efficiency_pct=68.0,
        shared_mem_barrier_stall_level="High",
        l2_throughput_gbps=80.0,
        max_scalable_warps_per_sm=3,
        instructions_billions=1.70,
        speedup_vs_naive=1.00,
        speedup_vs_prior_pct=0.0,
    ),
    "double_buffered_pipeline": PipelineVariantProfile(
        name="Two-stage, double-buffered (double_buffer_pipeline)",
        kernel_time_ms=20.5,
        warp_execution_efficiency_pct=92.0,
        shared_mem_barrier_stall_level="Low",
        l2_throughput_gbps=155.0,
        max_scalable_warps_per_sm=6,
        instructions_billions=1.05,
        speedup_vs_naive=round(41.3 / 20.5, 2),  # 2.01x
        speedup_vs_prior_pct=round((41.3 - 20.5) / 41.3 * 100.0, 1),
    ),
    "warp_specialized_pipeline": PipelineVariantProfile(
        name="Warp-specialized (warp_specialized_pipeline)",
        kernel_time_ms=18.4,
        warp_execution_efficiency_pct=96.0,
        shared_mem_barrier_stall_level="Minimal",
        l2_throughput_gbps=165.0,
        max_scalable_warps_per_sm=64,
        instructions_billions=1.00,
        speedup_vs_naive=round(41.3 / 18.4, 2),  # 2.24x
        speedup_vs_prior_pct=round((20.5 - 18.4) / 20.5 * 100.0, 1),  # 10.2%
    ),
    "warp_specialized_cluster_pipeline": PipelineVariantProfile(
        name="Thread block cluster pipeline (warp_specialized_cluster_pipeline)",
        kernel_time_ms=17.2,
        warp_execution_efficiency_pct=97.0,
        shared_mem_barrier_stall_level="Minimal (further reduced)",
        l2_throughput_gbps=170.0,
        max_scalable_warps_per_sm=64,
        instructions_billions=0.98,
        speedup_vs_naive=round(41.3 / 17.2, 2),  # 2.40x
        speedup_vs_prior_pct=round((18.4 - 17.2) / 18.4 * 100.0, 1),  # 6.5%
    ),
}


@dataclass(frozen=True)
class DsmemPairComparison:
    """Table 10-4 performance impact of DSMEM on a two-block workload (ASP Ch 10)."""

    independent_global_loads_factor: float
    dsmem_pair_global_loads_factor: float
    independent_l2_hit_rate_pct: float
    dsmem_pair_l2_hit_rate_pct: float
    independent_dram_bw_per_cta_gbps: float
    dsmem_pair_dram_bw_per_cta_gbps: float
    dram_bw_reduction_pct: float
    independent_rel_time: float
    dsmem_pair_rel_time: float
    kernel_time_reduction_pct: float


TABLE_10_4_DSMEM_CTA_PAIR = DsmemPairComparison(
    independent_global_loads_factor=2.0,
    dsmem_pair_global_loads_factor=1.0,
    independent_l2_hit_rate_pct=50.0,
    dsmem_pair_l2_hit_rate_pct=85.0,
    independent_dram_bw_per_cta_gbps=300.0,
    dsmem_pair_dram_bw_per_cta_gbps=150.0,
    dram_bw_reduction_pct=50.0,
    independent_rel_time=1.0,
    dsmem_pair_rel_time=0.6,
    kernel_time_reduction_pct=40.0,
)


@dataclass(frozen=True)
class PipelineSmemBudget:
    """Dynamic shared memory footprint for multi-stage or warp-specialized tiled kernels."""

    kernel_variant: str
    tile_size: int
    num_buffers: int
    elem_bytes: int
    total_smem_bytes: int
    fits_blackwell_block_smem: bool
    smem_utilization_pct: float
    row_band_per_cta: int


def evaluate_pipeline_smem_budget(
    kernel_variant: str,
    tile_size: int,
    stages: int = 2,
    cluster_ctas: int = 1,
    elem_bytes: int = 4,
    max_block_smem_bytes: int = BLACKWELL_MAX_DYNAMIC_SMEM_BYTES,
) -> PipelineSmemBudget:
    """Compute dynamic shared memory bytes for `gemm_tiled_pipeline`, `warp_specialized_pipeline_kernel`,
    or `warp_specialized_cluster_pipeline` (ASP Ch 10).
    """
    if tile_size <= 0 or stages <= 0 or cluster_ctas <= 0 or elem_bytes <= 0:
        raise ValueError("tile_size, stages, cluster_ctas, and elem_bytes must be positive")
    tile_elems = tile_size * tile_size
    if kernel_variant == "gemm_tiled_pipeline":
        # A_buf[STAGES] + B_buf[STAGES]
        num_buffers = 2 * stages
    elif kernel_variant in ("warp_specialized_pipeline", "warp_specialized_cluster_pipeline"):
        # A_tile + B_tile + C_tile (3 square tiles in dynamic shared memory)
        num_buffers = 3
    else:
        raise ValueError(f"Unknown kernel_variant: {kernel_variant}")

    total_bytes = num_buffers * tile_elems * elem_bytes
    fits = total_bytes <= max_block_smem_bytes
    util_pct = round(total_bytes / max_block_smem_bytes * 100.0, 2)
    rows_per_cta = (tile_size + cluster_ctas - 1) // cluster_ctas
    return PipelineSmemBudget(
        kernel_variant=kernel_variant,
        tile_size=tile_size,
        num_buffers=num_buffers,
        elem_bytes=elem_bytes,
        total_smem_bytes=total_bytes,
        fits_blackwell_block_smem=fits,
        smem_utilization_pct=util_pct,
        row_band_per_cta=rows_per_cta,
    )


@dataclass(frozen=True)
class PersistentKernelModel:
    """Persistent kernel launch overhead and SM occupancy analysis (ASP Ch 10)."""

    total_tasks: int
    task_time_ms: float
    launch_overhead_ms: float
    separate_launches_overhead_ms: float
    separate_launches_total_ms: float
    persistent_total_ms: float
    overhead_saved_ms: float
    num_sms: int
    blocks_launched: int
    threads_per_block: int
    total_persistent_threads: int
    per_sm_thread_occupancy_pct: float
    active_sm_pct: float


def model_persistent_kernel(
    total_tasks: int = 1000,
    task_time_ms: float = 0.1,
    launch_overhead_ms: float = 0.02,
    num_sms: int = 132,
    blocks_per_sm: int = 1,
    threads_per_block: int = 256,
    max_threads_per_sm: int = BLACKWELL_MAX_THREADS_PER_SM,
) -> PersistentKernelModel:
    """Compare launching `total_tasks` separate tiny kernels vs 1 persistent kernel (ASP Ch 10)."""
    if total_tasks <= 0 or task_time_ms <= 0 or launch_overhead_ms < 0:
        raise ValueError("total_tasks and task_time_ms must be positive; launch_overhead_ms >= 0")
    if num_sms <= 0 or blocks_per_sm <= 0 or threads_per_block <= 0:
        raise ValueError("num_sms, blocks_per_sm, and threads_per_block must be positive")

    work_ms = total_tasks * task_time_ms
    sep_overhead_ms = total_tasks * launch_overhead_ms
    sep_total_ms = work_ms + sep_overhead_ms
    pers_total_ms = work_ms + launch_overhead_ms
    saved_ms = sep_overhead_ms - launch_overhead_ms

    blocks = num_sms * blocks_per_sm
    total_threads = blocks * threads_per_block
    threads_per_sm = blocks_per_sm * threads_per_block
    occ_pct = round(threads_per_sm / max_threads_per_sm * 100.0, 2)
    active_sm_pct = round(min(blocks, num_sms) / num_sms * 100.0, 1)

    return PersistentKernelModel(
        total_tasks=total_tasks,
        task_time_ms=task_time_ms,
        launch_overhead_ms=launch_overhead_ms,
        separate_launches_overhead_ms=round(sep_overhead_ms, 3),
        separate_launches_total_ms=round(sep_total_ms, 3),
        persistent_total_ms=round(pers_total_ms, 3),
        overhead_saved_ms=round(saved_ms, 3),
        num_sms=num_sms,
        blocks_launched=blocks,
        threads_per_block=threads_per_block,
        total_persistent_threads=total_threads,
        per_sm_thread_occupancy_pct=occ_pct,
        active_sm_pct=active_sm_pct,
    )


@dataclass(frozen=True)
class CooperativeGridPlan:
    """Cooperative launch (`cudaLaunchCooperativeKernel`) grid sizing plan (ASP Ch 10)."""

    num_sms: int
    max_active_blocks_per_sm: int
    max_cooperative_blocks: int
    requested_elements: int
    block_size: int
    unclamped_blocks: int
    clamped_cooperative_blocks: int
    would_fail_if_unclamped: bool
    iterations: int
    stages_per_iteration: int
    naive_kernel_launches: int
    cooperative_persistent_launches: int


def plan_cooperative_grid(
    requested_elements: int,
    block_size: int = 256,
    num_sms: int = 132,
    max_active_blocks_per_sm: int = 4,
    iterations: int = 1000,
    stages_per_iteration: int = 2,
) -> CooperativeGridPlan:
    """Size and clamp a cooperative grid so all blocks co-reside for `grid.sync()` (ASP Ch 10)."""
    if requested_elements <= 0 or block_size <= 0 or num_sms <= 0 or max_active_blocks_per_sm <= 0:
        raise ValueError("Grid sizing inputs must be positive")
    if iterations <= 0 or stages_per_iteration <= 0:
        raise ValueError("iterations and stages_per_iteration must be positive")

    max_coop_grid = num_sms * max_active_blocks_per_sm
    unclamped = (requested_elements + block_size - 1) // block_size
    clamped = min(unclamped, max_coop_grid)
    return CooperativeGridPlan(
        num_sms=num_sms,
        max_active_blocks_per_sm=max_active_blocks_per_sm,
        max_cooperative_blocks=max_coop_grid,
        requested_elements=requested_elements,
        block_size=block_size,
        unclamped_blocks=unclamped,
        clamped_cooperative_blocks=clamped,
        would_fail_if_unclamped=unclamped > max_coop_grid,
        iterations=iterations,
        stages_per_iteration=stages_per_iteration,
        naive_kernel_launches=iterations * stages_per_iteration,
        cooperative_persistent_launches=1,
    )


@dataclass(frozen=True)
class ClusterLaunchPlan:
    """Thread Block Cluster (`cudaLaunchKernelEx`) configuration and sharing policy (ASP Ch 10)."""

    grid_blocks: int
    cluster_dim_x: int
    num_clusters: int
    non_portable_allowed: bool
    sharing_mechanism: str
    global_loads_per_cluster: int
    redundant_loads_eliminated_factor: float


def plan_thread_block_cluster(
    grid_blocks: int = 128,
    cluster_dim_x: int = 2,
    non_portable_allowed: bool = False,
    tile_reuse_per_block: str = "high",
    smem_pressure: str = "moderate",
) -> ClusterLaunchPlan:
    """Validate a `cudaLaunchKernelEx` cluster launch and choose TMA multicast vs DSMEM sharing (ASP Ch 10)."""
    if grid_blocks <= 0 or cluster_dim_x <= 0:
        raise ValueError("grid_blocks and cluster_dim_x must be positive")
    if grid_blocks % cluster_dim_x != 0:
        raise ValueError("grid_blocks must be evenly divisible by cluster_dim_x")
    if cluster_dim_x > NONPORTABLE_MAX_CLUSTER_CTAS:
        raise ValueError(f"cluster_dim_x={cluster_dim_x} exceeds max hardware limit {NONPORTABLE_MAX_CLUSTER_CTAS}")
    if cluster_dim_x > PORTABLE_MAX_CLUSTER_CTAS and not non_portable_allowed:
        raise ValueError(
            f"cluster_dim_x={cluster_dim_x} exceeds portable limit {PORTABLE_MAX_CLUSTER_CTAS}; "
            "enable cudaFuncAttributeNonPortableClusterSizeAllowed"
        )

    # ASP Ch 10 decision rule:
    # - High tile reuse per block or large cluster (8-16 CTAs) -> TMA multicast (`cp.async.bulk.tensor` to `shared::cluster`)
    # - Tight SMEM (large tiles) or small cluster (2-4 CTAs) with single-touch follower reads -> DSMEM `map_shared_rank` + `cluster.sync()`
    if smem_pressure == "tight" or (cluster_dim_x <= 4 and tile_reuse_per_block == "low"):
        mechanism = "DSMEM_MAP_SHARED_RANK"
    else:
        mechanism = "TMA_MULTICAST_SHARED_CLUSTER"

    return ClusterLaunchPlan(
        grid_blocks=grid_blocks,
        cluster_dim_x=cluster_dim_x,
        num_clusters=grid_blocks // cluster_dim_x,
        non_portable_allowed=non_portable_allowed,
        sharing_mechanism=mechanism,
        global_loads_per_cluster=1,
        redundant_loads_eliminated_factor=float(cluster_dim_x),
    )


def verify_cluster_dsmem_reduction(cluster_size: int = 2, block_dim: int = 256) -> Dict[str, int]:
    """Simulate `MyClusterKernel` (`cg::this_cluster()`, `map_shared_rank(shared_buffer, 0)`,
    on-chip DSMEM `atomicAdd` of `shared_buffer[0]` across blocks in the cluster; ASP Ch 10).
    """
    if cluster_size <= 0 or block_dim <= 0:
        raise ValueError("cluster_size and block_dim must be positive")
    # In MyClusterKernel: shared_buffer[threadIdx.x] = threadIdx.x;
    # Nonzero blocks atomically add shared_buffer[0] (or their block's local sum) into rank 0's shared_buffer[0].
    # Let's track both shared_buffer[0] literal from the snippet and a full thread sum across the cluster:
    per_block_thread_sum = block_dim * (block_dim - 1) // 2
    combined_cluster_thread_sum = cluster_size * per_block_thread_sum
    remote_atomic_adds_per_cluster = cluster_size - 1
    return {
        "cluster_size": cluster_size,
        "block_dim": block_dim,
        "per_block_thread_sum": per_block_thread_sum,
        "combined_cluster_thread_sum": combined_cluster_thread_sum,
        "remote_atomic_adds_per_cluster": remote_atomic_adds_per_cluster,
        "cluster_sync_barriers": 2,
    }
