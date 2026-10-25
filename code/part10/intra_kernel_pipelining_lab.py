#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.16: Intra-kernel pipelining, warp specialization and thread block clusters.

Runs 25 deterministic checks verifying every table, formula, SMEM budget, persistent-kernel model,
cooperative grid calculation, and DSMEM / Thread Block Cluster pipeline metric from
*AI Systems Performance Engineering* Chapter 10.
"""

from __future__ import annotations

import sys

from intra_kernel_pipelining import (
    BLACKWELL_MAX_DYNAMIC_SMEM_BYTES,
    BLACKWELL_MAX_THREADS_PER_SM,
    BLACKWELL_MAX_WARPS_PER_SM,
    NONPORTABLE_MAX_CLUSTER_CTAS,
    PORTABLE_MAX_CLUSTER_CTAS,
    TABLE_10_4_DSMEM_CTA_PAIR,
    TABLE_10_5_PIPELINE_PROGRESSION,
    evaluate_pipeline_smem_budget,
    model_persistent_kernel,
    plan_cooperative_grid,
    plan_thread_block_cluster,
    verify_cluster_dsmem_reduction,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    print("=== Chapter 10.16 Lab: Intra-Kernel Pipelining, Warp Specialization & Thread Block Clusters (ASP Ch 10) ===")

    # 1-4: Tables 10-2, 10-3, and 10-5 progression
    naive = TABLE_10_5_PIPELINE_PROGRESSION["naive_tiling"]
    dbl = TABLE_10_5_PIPELINE_PROGRESSION["double_buffered_pipeline"]
    ws = TABLE_10_5_PIPELINE_PROGRESSION["warp_specialized_pipeline"]
    wsc = TABLE_10_5_PIPELINE_PROGRESSION["warp_specialized_cluster_pipeline"]

    check(
        "ASP Ch10 Table 10-2: Double-buffered pipeline cuts time 41.3 -> 20.5 ms (2.01x faster) and raises SM Active / warp eff 68% -> 92% (+24%)",
        naive.kernel_time_ms == 41.3
        and dbl.kernel_time_ms == 20.5
        and dbl.speedup_vs_naive == 2.01
        and naive.warp_execution_efficiency_pct == 68.0
        and dbl.warp_execution_efficiency_pct == 92.0,
    )
    check(
        "ASP Ch10 Table 10-3: Single-block warp specialization cuts time 20.5 -> 18.4 ms (+10.2% speedup vs 2-stage), raises efficiency to 96%, L2 to 165 GB/s (+6.45%), and scales to 64 warps/SM",
        ws.kernel_time_ms == 18.4
        and ws.speedup_vs_prior_pct == 10.2
        and ws.warp_execution_efficiency_pct == 96.0
        and ws.l2_throughput_gbps == 165.0
        and ws.max_scalable_warps_per_sm == 64,
    )
    check(
        "ASP Ch10 Table 10-5: Thread block cluster warp specialization cuts time 18.4 -> 17.2 ms (+6.5% vs single-block, 2.40x vs naive), reaches 97% efficiency and 170 GB/s L2",
        wsc.kernel_time_ms == 17.2
        and wsc.speedup_vs_prior_pct == 6.5
        and wsc.speedup_vs_naive == 2.40
        and wsc.warp_execution_efficiency_pct == 97.0
        and wsc.l2_throughput_gbps == 170.0,
    )
    check(
        "ASP Ch10 Tables 10-3 & 10-5: Dynamic instruction count drops 1.7B -> 1.05B (-38%) -> 1.00B (-4.76%) -> 0.98B (-2%)",
        naive.instructions_billions == 1.70
        and dbl.instructions_billions == 1.05
        and ws.instructions_billions == 1.00
        and wsc.instructions_billions == 0.98,
    )

    # 5-8: Dynamic shared memory budgets (`gemm_tiled_pipeline`, `warp_specialized_pipeline_kernel`, `warp_specialized_cluster_pipeline`)
    smem_dbl = evaluate_pipeline_smem_budget("gemm_tiled_pipeline", tile_size=32, stages=2)
    smem_tri = evaluate_pipeline_smem_budget("gemm_tiled_pipeline", tile_size=32, stages=3)
    smem_ws112 = evaluate_pipeline_smem_budget("warp_specialized_pipeline", tile_size=112)
    smem_wsc128 = evaluate_pipeline_smem_budget("warp_specialized_cluster_pipeline", tile_size=128, cluster_ctas=2)
    smem_oversize = evaluate_pipeline_smem_budget("warp_specialized_pipeline", tile_size=160)

    check(
        "ASP Ch10 gemm_tiled_pipeline: TILE_SIZE=32 uses 16,384 B (4 buffers, STAGES=2) and 24,576 B (6 buffers, STAGES=3)",
        smem_dbl.num_buffers == 4
        and smem_dbl.total_smem_bytes == 16_384
        and smem_tri.num_buffers == 6
        and smem_tri.total_smem_bytes == 24_576,
    )
    check(
        "ASP Ch10 warp_specialized_pipeline_kernel: 3 tiles * 112 * 112 * 4 B == 150,528 B (147.0 KiB, 66.22% of 227,328 B ~227 KB Blackwell per-block dynamic SMEM limit)",
        smem_ws112.total_smem_bytes == 150_528
        and round(smem_ws112.total_smem_bytes / 1024.0, 1) == 147.0
        and smem_ws112.smem_utilization_pct == 66.22
        and BLACKWELL_MAX_DYNAMIC_SMEM_BYTES == 227_328
        and smem_ws112.fits_blackwell_block_smem is True,
    )
    check(
        "ASP Ch10 warp_specialized_cluster_pipeline: TILE_SIZE=128 (TILE_ELEMS=16,384) uses 3 * 16,384 * 4 B == 196,608 B (192.0 KiB, 86.49% of 227,328 B) and splits 64 rows/CTA across a 2-CTA cluster",
        smem_wsc128.total_smem_bytes == 196_608
        and round(smem_wsc128.total_smem_bytes / 1024.0, 1) == 192.0
        and smem_wsc128.smem_utilization_pct == 86.49
        and smem_wsc128.fits_blackwell_block_smem is True
        and smem_wsc128.row_band_per_cta == 64,
    )
    check(
        "ASP Ch10 SMEM guard: 3 tiles * 160 * 160 * 4 B (307,200 B) exceeds 227,328 B per-block dynamic SMEM limit",
        smem_oversize.total_smem_bytes == 307_200
        and smem_oversize.fits_blackwell_block_smem is False,
    )

    # 9-11: Persistent kernel launch overhead & SM utilization
    pers = model_persistent_kernel(
        total_tasks=1000,
        task_time_ms=0.1,
        launch_overhead_ms=0.02,
        num_sms=132,
        blocks_per_sm=1,
        threads_per_block=256,
    )
    check(
        "ASP Ch10 Persistent Kernel: 1,000 tasks * 0.1 ms = 100 ms work + 1,000 * 0.02 ms = 20.0 ms launch overhead (120.0 ms) vs 100.02 ms persistent (saves 19.98 ms ~ 20 ms)",
        pers.separate_launches_overhead_ms == 20.0
        and pers.separate_launches_total_ms == 120.0
        and pers.persistent_total_ms == 100.02
        and pers.overhead_saved_ms == 19.98,
    )
    check(
        "ASP Ch10 Persistent Kernel grid: 132 SMs * 256 threads/block == 33,792 total persistent threads",
        pers.blocks_launched == 132
        and pers.total_persistent_threads == 33_792,
    )
    check(
        "ASP Ch10 Persistent Kernel residency: 256 / 2,048 threads == 12.5% (~12%) per-SM thread occupancy while keeping 100.0% of 132 SMs active",
        pers.per_sm_thread_occupancy_pct == 12.5
        and pers.active_sm_pct == 100.0
        and BLACKWELL_MAX_THREADS_PER_SM == 2048,
    )

    # 12-14: Cooperative groups (`cudaLaunchCooperativeKernel` & `combinedKernel`)
    coop_clamped = plan_cooperative_grid(
        requested_elements=1_000_000,
        block_size=256,
        num_sms=132,
        max_active_blocks_per_sm=4,
        iterations=1000,
        stages_per_iteration=2,
    )
    coop_small = plan_cooperative_grid(
        requested_elements=65_536,
        block_size=256,
        num_sms=132,
        max_active_blocks_per_sm=4,
        iterations=1000,
        stages_per_iteration=2,
    )
    check(
        "ASP Ch10 Cooperative Launch: 132 SMs * 4 active blocks/SM == 528 max concurrent cooperative blocks; N=1,000,000 (3,907 blocks) must be clamped to 528",
        coop_clamped.max_cooperative_blocks == 528
        and coop_clamped.unclamped_blocks == 3907
        and coop_clamped.clamped_cooperative_blocks == 528
        and coop_clamped.would_fail_if_unclamped is True,
    )
    check(
        "ASP Ch10 combinedKernel: Fuses 2 stages * 1,000 iterations == 2,000 separate kernel launches into 1 cooperative persistent launch with grid.sync()",
        coop_clamped.naive_kernel_launches == 2000
        and coop_clamped.cooperative_persistent_launches == 1,
    )
    check(
        "ASP Ch10 Cooperative Launch: N=65,536 at blockSize=256 requires 256 blocks <= 528 max cooperative blocks (launches without clamping)",
        coop_small.unclamped_blocks == 256
        and coop_small.clamped_cooperative_blocks == 256
        and coop_small.would_fail_if_unclamped is False,
    )

    # 15-19: Thread Block Clusters, DSMEM Table 10-4, and TMA multicast vs DSMEM selection
    check(
        "ASP Ch10 Table 10-4: CTA pair with DSMEM cuts global loads 2x -> 1x, lifts L2 hit rate 50% -> 85%, cuts DRAM BW/CTA 300 -> 150 GB/s (-50%), and cuts kernel time 1.0x -> 0.6x (40% speedup)",
        TABLE_10_4_DSMEM_CTA_PAIR.independent_global_loads_factor == 2.0
        and TABLE_10_4_DSMEM_CTA_PAIR.dsmem_pair_global_loads_factor == 1.0
        and TABLE_10_4_DSMEM_CTA_PAIR.independent_l2_hit_rate_pct == 50.0
        and TABLE_10_4_DSMEM_CTA_PAIR.dsmem_pair_l2_hit_rate_pct == 85.0
        and TABLE_10_4_DSMEM_CTA_PAIR.independent_dram_bw_per_cta_gbps == 300.0
        and TABLE_10_4_DSMEM_CTA_PAIR.dsmem_pair_dram_bw_per_cta_gbps == 150.0
        and TABLE_10_4_DSMEM_CTA_PAIR.dsmem_pair_rel_time == 0.6
        and TABLE_10_4_DSMEM_CTA_PAIR.kernel_time_reduction_pct == 40.0,
    )

    cluster_pair = plan_thread_block_cluster(
        grid_blocks=128,
        cluster_dim_x=2,
        non_portable_allowed=False,
        tile_reuse_per_block="low",
        smem_pressure="tight",
    )
    cluster_tma8 = plan_thread_block_cluster(
        grid_blocks=128,
        cluster_dim_x=8,
        non_portable_allowed=False,
        tile_reuse_per_block="high",
        smem_pressure="moderate",
    )
    cluster_tma16 = plan_thread_block_cluster(
        grid_blocks=128,
        cluster_dim_x=16,
        non_portable_allowed=True,
        tile_reuse_per_block="high",
        smem_pressure="moderate",
    )

    check(
        "ASP Ch10 cudaLaunchKernelEx: gridDim=128 with clusterDim.x=2 launches 64 CTA-pair clusters and selects DSMEM_MAP_SHARED_RANK when SMEM is tight",
        cluster_pair.num_clusters == 64
        and cluster_pair.sharing_mechanism == "DSMEM_MAP_SHARED_RANK"
        and cluster_pair.redundant_loads_eliminated_factor == 2.0,
    )
    check(
        "ASP Ch10 Cluster sharing rule: 8-CTA portable cluster with high tile reuse selects TMA_MULTICAST_SHARED_CLUSTER (16 clusters, 8x load reduction)",
        cluster_tma8.num_clusters == 16
        and cluster_tma8.sharing_mechanism == "TMA_MULTICAST_SHARED_CLUSTER"
        and cluster_tma8.redundant_loads_eliminated_factor == 8.0
        and PORTABLE_MAX_CLUSTER_CTAS == 8,
    )
    check(
        "ASP Ch10 Non-portable 16-CTA cluster on Blackwell: 128 / 16 == 8 clusters with 16x load reduction when cudaFuncAttributeNonPortableClusterSizeAllowed is True",
        cluster_tma16.num_clusters == 8
        and cluster_tma16.redundant_loads_eliminated_factor == 16.0
        and NONPORTABLE_MAX_CLUSTER_CTAS == 16,
    )

    dsmem_red = verify_cluster_dsmem_reduction(cluster_size=4, block_dim=256)
    check(
        "ASP Ch10 MyClusterKernel: 4-CTA cluster executes 3 remote on-chip DSMEM atomicAdd operations into rank 0 bounded by 2 cluster.sync() barriers",
        dsmem_red["remote_atomic_adds_per_cluster"] == 3
        and dsmem_red["cluster_sync_barriers"] == 2
        and dsmem_red["per_block_thread_sum"] == 32_640
        and dsmem_red["combined_cluster_thread_sum"] == 130_560,
    )

    # 20-25: Error handling and input validation guards
    try:
        plan_thread_block_cluster(grid_blocks=128, cluster_dim_x=16, non_portable_allowed=False)
        rejected_np16 = False
    except ValueError:
        rejected_np16 = True
    check("Rejects 16-CTA cluster when non_portable_allowed is False", rejected_np16)

    try:
        plan_thread_block_cluster(grid_blocks=128, cluster_dim_x=32, non_portable_allowed=True)
        rejected_gt16 = False
    except ValueError:
        rejected_gt16 = True
    check("Rejects cluster_dim_x > 16 hardware limit", rejected_gt16)

    try:
        plan_thread_block_cluster(grid_blocks=130, cluster_dim_x=4)
        rejected_nondiv = False
    except ValueError:
        rejected_nondiv = True
    check("Rejects grid_blocks not divisible by cluster_dim_x", rejected_nondiv)

    try:
        evaluate_pipeline_smem_budget("unknown_kernel", tile_size=32)
        rejected_variant = False
    except ValueError:
        rejected_variant = True
    check("Rejects unknown pipeline kernel variant", rejected_variant)

    try:
        model_persistent_kernel(total_tasks=0)
        rejected_zero_tasks = False
    except ValueError:
        rejected_zero_tasks = True
    check("Rejects non-positive total_tasks in persistent kernel model", rejected_zero_tasks)

    check(
        "ASP Ch10 Table 10-3 & 10-5: L2 throughput progresses 80 -> 155 (+93.75% ~ +94%) -> 165 (+6.45%) -> 170 GB/s (+3.03% ~ +3%) up to 64 warps/SM",
        round((155.0 - 80.0) / 80.0 * 100.0, 2) == 93.75
        and round((165.0 - 155.0) / 155.0 * 100.0, 2) == 6.45
        and round((170.0 - 165.0) / 165.0 * 100.0, 2) == 3.03
        and BLACKWELL_MAX_WARPS_PER_SM == 64,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
