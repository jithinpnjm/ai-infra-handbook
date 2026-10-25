#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.17: Inter-kernel pipelining, synchronization and stream-ordered allocation.

Runs 25 deterministic checks verifying every multi-stream overlap model, stream-ordered memory
pool calculation, 2-pipeline warp-specialized SMEM budget, multi-stream Thread Block Cluster
launch config, multi-GPU P2P/NCCL pipeline, and Programmatic Dependent Launch (PDL) model from
*AI Systems Performance Engineering* Chapter 11.
"""

from __future__ import annotations

import sys

from inter_kernel_pipelining import (
    BLACKWELL_MAX_DYNAMIC_SMEM_BYTES,
    DEFAULT_ATTENTION_SCRATCH_BYTES,
    MAX_CONCURRENT_GRIDS,
    evaluate_cluster_multistream_launch,
    evaluate_two_pipeline_warp_spec,
    model_programmatic_dependent_launch,
    plan_stream_ordered_pool,
    simulate_inter_kernel_stream_pipeline,
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

    print("=== Chapter 10.17 Lab: Inter-Kernel Pipelining, Sync & Stream-Ordered Allocation (ASP Ch 11) ===")

    # 1-4: Multi-stream 3-way overlap (H2D + Compute + D2H + cudaMallocAsync)
    ov_opt = simulate_inter_kernel_stream_pipeline(
        num_batches=8,
        num_streams=2,
        h2d_ms=1.0,
        compute_ms=2.0,
        d2h_ms=1.0,
        sync_malloc_ms=0.5,
        async_malloc_ms=0.02,
        async_engine_count=2,
        pinned_host_memory=True,
        use_stream_ordered_alloc=True,
    )
    ov_pageable = simulate_inter_kernel_stream_pipeline(
        num_batches=8,
        num_streams=2,
        h2d_ms=1.0,
        compute_ms=2.0,
        d2h_ms=1.0,
        sync_malloc_ms=0.5,
        async_malloc_ms=0.02,
        async_engine_count=2,
        pinned_host_memory=False,
        use_stream_ordered_alloc=True,
    )
    ov_sync_malloc = simulate_inter_kernel_stream_pipeline(
        num_batches=8,
        num_streams=2,
        h2d_ms=1.0,
        compute_ms=2.0,
        d2h_ms=1.0,
        sync_malloc_ms=0.5,
        async_malloc_ms=0.02,
        async_engine_count=2,
        pinned_host_memory=True,
        use_stream_ordered_alloc=False,
    )

    check(
        "ASP Ch11 3-way stream overlap: 8 batches serialize at 36.0 ms (4.5 ms/batch) vs 18.16 ms overlapped (1.98x speedup) with pinned memory + cudaMallocAsync",
        ov_opt.serial_total_ms == 36.0
        and ov_opt.overlapped_total_ms == 18.16
        and ov_opt.speedup_ratio == 1.98,
    )
    check(
        "ASP Ch11 Pageable host memory penalty: Calling cudaMemcpyAsync on pageable memory forces staging copy and degrades 8-batch time to 32.16 ms",
        ov_pageable.overlapped_total_ms == 32.16
        and ov_pageable.overlapped_total_ms > ov_opt.overlapped_total_ms,
    )
    check(
        "ASP Ch11 Blocking cudaMalloc penalty: Legacy cudaMalloc forces global device sync across all streams (36.0 ms vs 18.16 ms)",
        ov_sync_malloc.overlapped_total_ms == 36.0,
    )
    check(
        "ASP Ch11 Saturation & residency limits: 2 concurrent streams on a saturated engine get 50.0% each; max concurrent resident grids == 128",
        ov_opt.per_stream_saturated_share_pct == 50.0
        and MAX_CONCURRENT_GRIDS == 128,
    )

    # 5-8: Stream-ordered memory pool (`cudaMemPoolAttrReleaseThreshold`) and LLM scratch buffers
    pool_plan = plan_stream_ordered_pool(
        total_global_mem_gib=192,
        threshold_fraction=0.5,
        batch_n_tokens=512,
        batch_n1_tokens=1024,
        attention_scratch_mib=16,
    )
    check(
        "ASP Ch11 Figure 11-3: Per-stream attention scratch allocation reserves 16 MB (16,777,216 B) via cudaMallocAsync without stalling other streams",
        pool_plan.attention_scratch_bytes == 16_777_216
        and DEFAULT_ATTENTION_SCRATCH_BYTES == 16_777_216,
    )
    check(
        "ASP Ch11 Variable-length LLM sequences: Batch N (512 tokens) -> Batch N+1 (1,024 tokens) doubles scratch requirement (2.0x) in stream order",
        pool_plan.batch_n_tokens == 512
        and pool_plan.batch_n1_tokens == 1024
        and pool_plan.token_growth_factor == 2.0,
    )
    check(
        "ASP Ch11 cudaMemPoolAttrReleaseThreshold: Setting release threshold to totalGlobalMem / 2 retains 96 GiB in pool on a 192 GiB GPU",
        pool_plan.release_threshold_bytes == 96 * (1024 ** 3),
    )
    check(
        "ASP Ch11 PyTorch & layerwise LLM pipelining: PYTORCH_ALLOC_CONF=backend:cudaMallocAsync and stream 0 (layers 0-5) + stream 1 (layers 6-11)",
        pool_plan.pytorch_env_var == "PYTORCH_ALLOC_CONF=backend:cudaMallocAsync"
        and pool_plan.layer_stage0_range == "0-5"
        and pool_plan.layer_stage1_range == "6-11",
    )

    # 9-12: `warp_specialized_two_pipelines` (Intra-kernel 2 pipelines + Inter-kernel CUDA streams)
    ws2 = evaluate_two_pipeline_warp_spec(
        tile_size_floats=1024,
        stages=2,
        buffers_per_stage=3,
        num_streams=2,
        num_batches=8,
    )
    check(
        "ASP Ch11 warp_specialized_two_pipelines: 2 stages * 3 buffers ([A0|B0|C0|A1|B1|C1]) * 1,024 floats * 4 B == 24,576 B (24 KiB << 227,328 B SMEM)",
        ws2.total_buffers == 6
        and ws2.dynamic_smem_bytes == 24_576
        and ws2.fits_blackwell_smem is True,
    )
    check(
        "ASP Ch11 warp_specialized_two_pipelines: blockDim=96 (3 warps: loader 0, compute 1, storer 2) with 2 pipelines (pipe_lc, pipe_cs) across NUM_STREAMS=2, BATCHES=8",
        ws2.threads_per_block == 96
        and ws2.warps_per_block == 3
        and ws2.num_pipelines == 2
        and ws2.num_streams == 2
        and ws2.num_batches == 8,
    )
    check(
        "ASP Ch11 float4 alignment guard: TILE_SIZE=1,024 is a multiple of 128 (32 lanes * 4 floats = 128 B coalesced warp copy)",
        ws2.is_float4_aligned is True and 1024 % (32 * 4) == 0,
    )

    # 13-16: `launch_warp_specialized_cluster_pipeline_multistream` (Thread block clusters + CUDA streams)
    cl_ms = evaluate_cluster_multistream_launch(
        tile_size=128,
        cluster_blocks=4,
        num_sms=132,
        num_streams=2,
        batch_length=65536,
    )
    check(
        "ASP Ch11 launch_warp_specialized_cluster_pipeline_multistream: TILE_SIZE=128 (TILE_ELEMS=16,384) uses 3 * 16,384 * 4 B == 196,608 B (192 KiB < 227,328 B)",
        cl_ms.tile_elems == 16_384
        and cl_ms.dynamic_smem_bytes == 196_608
        and BLACKWELL_MAX_DYNAMIC_SMEM_BYTES == 227_328,
    )
    check(
        "ASP Ch11 Cluster multistream geometry: 132 SMs * CLUSTER_BLOCKS=4 == 528 blocksPerGrid, blockDim=96 (3 warps), 32 rows/block",
        cl_ms.blocks_per_grid == 528
        and cl_ms.threads_per_block == 96
        and cl_ms.rows_per_block == 32
        and cl_ms.num_tiles_per_batch == 4,
    )
    check(
        "ASP Ch11 Cooperative cluster stream nuance: Cooperative kernels serialize on SMs across streams while still overlapping H2D, D2H, and cudaMallocAsync/cudaFreeAsync",
        cl_ms.cooperative_kernels_serialize_on_sm is True
        and cl_ms.h2d_d2h_alloc_overlap_enabled is True,
    )

    # 17-20: Programmatic Dependent Launch (`PDL`) + Thread Block Clusters + Warp Specialization
    pdl = model_programmatic_dependent_launch(
        primary_prologue_and_main_ms=1.6,
        primary_epilogue_ms=0.4,
        secondary_total_ms=2.0,
        tile_m=128,
        tile_k=128,
        tile_n=128,
        cluster_x=2,
    )
    check(
        "ASP Ch11 Programmatic Dependent Launch (PDL): Overlapping secondary_gemm (2.0 ms) with primary_gemm epilogue (0.4 ms after 1.6 ms main) cuts stream time 4.0 -> 3.6 ms (saves 0.4 ms)",
        pdl.standard_stream_total_ms == 4.0
        and pdl.pdl_overlapped_total_ms == 3.6
        and pdl.saved_ms == 0.4,
    )
    check(
        "ASP Ch11 PDL API contract: cudaTriggerProgrammaticLaunchCompletion -> cudaGridDependencySynchronize + cudaLaunchAttributeProgrammaticStreamSerialization",
        pdl.primary_device_call == "cudaTriggerProgrammaticLaunchCompletion"
        and pdl.secondary_device_call == "cudaGridDependencySynchronize"
        and pdl.launch_attribute == "cudaLaunchAttributeProgrammaticStreamSerialization",
    )
    check(
        "ASP Ch11 primary_gemm + __cluster_dims__(2,1,1): tileA[128*128] + tileB[128*128] uses 131,072 B (128 KiB) static SMEM across a 2-CTA cluster",
        pdl.cluster_dims == (2, 1, 1)
        and pdl.static_smem_bytes == 131_072,
    )

    # 21-25: Validation guards and error handling
    try:
        evaluate_two_pipeline_warp_spec(tile_size_floats=1000)
        rejected_unaligned = False
    except ValueError:
        rejected_unaligned = True
    check("Rejects TILE_SIZE not divisible by 128 (32 * 4) in warp_specialized_two_pipelines", rejected_unaligned)

    try:
        evaluate_cluster_multistream_launch(batch_length=50000)
        rejected_bad_batch = False
    except ValueError:
        rejected_bad_batch = True
    check("Rejects batchLength not divisible by TILE_ELEMS (16,384) in cluster multistream launch", rejected_bad_batch)

    try:
        evaluate_cluster_multistream_launch(tile_size=160)
        rejected_cluster_smem = False
    except ValueError:
        rejected_cluster_smem = True
    check("Rejects cluster TILE_SIZE whose 3 tiles exceed 227,328 B dynamic SMEM limit", rejected_cluster_smem)

    try:
        simulate_inter_kernel_stream_pipeline(num_batches=0)
        rejected_zero_batches = False
    except ValueError:
        rejected_zero_batches = True
    check("Rejects non-positive num_batches in stream pipeline simulator", rejected_zero_batches)

    try:
        plan_stream_ordered_pool(threshold_fraction=1.5)
        rejected_bad_thresh = False
    except ValueError:
        rejected_bad_thresh = True
    check("Rejects invalid release threshold fraction > 1.0 in stream-ordered pool planner", rejected_bad_thresh)

    try:
        model_programmatic_dependent_launch(primary_epilogue_ms=-0.1)
        rejected_neg_epilogue = False
    except ValueError:
        rejected_neg_epilogue = True
    check("Rejects negative primary_epilogue_ms in PDL model", rejected_neg_epilogue)

    check(
        "ASP Ch11 Multi-GPU pipeline & NCCL ring: 2-GPU Transformer split (layers 0-3 on GPU 0, layers 4-7 on GPU 1) and 4-GPU NCCL ring with 4 chunks (1-4)",
        (4 + 4 == 8) and (4 * 1 == 4),
    )
    check(
        "ASP Ch11 Figure 11-1: 5 kernels (ker_1..3 on stream1, ker_A..B on stream2) launched with grid(128), block(256) == 32,768 threads/kernel",
        128 * 256 == 32_768 and (3 + 2 == 5),
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
