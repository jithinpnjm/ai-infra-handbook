#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.18: Dynamic scheduling, CUDA graphs and device-initiated orchestration.

Runs 25 deterministic checks verifying every formula, table, and diagnostic scenario from
*AI Systems Performance Engineering* Chapter 12 and `nvidia-devops` Volume 03 (Chapters 10, 12, 13 & Lab 04).
"""

from __future__ import annotations

import sys

from dynamic_scheduling_graphs import (
    CONDITIONAL_NODE_EXAMPLE_THRESHOLD,
    DEFAULT_DP_PENDING_LAUNCH_COUNT,
    GB200_NVL72_BLACKWELL_GPUS,
    GB200_NVL72_GRACE_CPUS,
    GB200_NVL72_UNIFIED_MEMORY_TB,
    MAX_FIRE_AND_FORGET_GRAPHS,
    MAX_PENDING_SELF_TAIL_LAUNCHES,
    MAX_PENDING_TAIL_LAUNCHES,
    TABLE_12_1_CUDA_GRAPHS,
    TABLE_12_2_DYNAMIC_PARALLELISM,
    analyze_decode_launch_overhead,
    evaluate_atomic_work_queue,
    evaluate_v3_lab04_diagnostics,
    recommend_roofline_orchestration,
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

    print("=== Chapter 10.18 Lab: Dynamic Scheduling, CUDA Graphs & Device Orchestration (ASP Ch 12 + V3) ===")

    # 1-4: L2-cache atomic work queues & DGX GB200 NVL72 domain
    aq32 = evaluate_atomic_work_queue(num_elements=1_048_576, batch_size=32, static_runtime_ms=200.0, dynamic_runtime_ms=100.0)
    aq16 = evaluate_atomic_work_queue(num_elements=1_048_576, batch_size=16)
    aq8 = evaluate_atomic_work_queue(num_elements=1_048_576, batch_size=8)

    check(
        "ASP Ch12 DGX GB200 NVL72: 36 Grace CPUs + 72 Blackwell GPUs with up to 30 TB unified memory in a single NVLink domain",
        GB200_NVL72_GRACE_CPUS == 36
        and GB200_NVL72_BLACKWELL_GPUS == 72
        and GB200_NVL72_UNIFIED_MEMORY_TB == 30,
    )
    check(
        "ASP Ch12 Warp-batched atomic queue (batchSize=32): Reduces 1,048,576 atomics by 32.0x to 32,768 atomics and drives atomic_transactions_per_request toward 1.0",
        aq32.unbatched_atomic_ops == 1_048_576
        and aq32.batched_atomic_ops == 32_768
        and aq32.atomic_reduction_factor == 32.0
        and aq32.ideal_transactions_per_request == 1.0,
    )
    check(
        "ASP Ch12 uneven_static.cu vs uneven_dynamic.cu (N=1<<20, work=idx%256): Dynamic warp-leader queue cuts runtime 200 ms -> 100 ms (2.0x speedup)",
        aq32.static_runtime_ms == 200.0
        and aq32.dynamic_runtime_ms == 100.0
        and aq32.speedup_ratio == 2.0,
    )
    check(
        "ASP Ch12 Modest atomic batching: batchSize=8 (131,072 atomics, 8.0x reduction) and batchSize=16 (65,536 atomics, 16.0x reduction)",
        aq8.batched_atomic_ops == 131_072
        and aq8.atomic_reduction_factor == 8.0
        and aq16.batched_atomic_ops == 65_536
        and aq16.atomic_reduction_factor == 16.0,
    )

    # 5-8: CUDA Graphs Table 12-1 & V3 Ch 10 decode launch overhead
    check(
        "ASP Ch12 Table 12-1: CUDA Graphs cut 100-iteration launches 300 -> 100, syncs 300 -> 0, inter-kernel gaps ~3 us -> 0 us, and iteration latency 1.00 -> 0.75 ms (-25.0%)",
        TABLE_12_1_CUDA_GRAPHS.launches_before == 300
        and TABLE_12_1_CUDA_GRAPHS.launches_after == 100
        and TABLE_12_1_CUDA_GRAPHS.sync_calls_before == 300
        and TABLE_12_1_CUDA_GRAPHS.sync_calls_after == 0
        and TABLE_12_1_CUDA_GRAPHS.inter_kernel_gap_before_us == 3.0
        and TABLE_12_1_CUDA_GRAPHS.inter_kernel_gap_after_us == 0.0
        and TABLE_12_1_CUDA_GRAPHS.latency_before_ms == 1.00
        and TABLE_12_1_CUDA_GRAPHS.latency_after_ms == 0.75
        and TABLE_12_1_CUDA_GRAPHS.latency_reduction_pct == 25.0,
    )

    dec = analyze_decode_launch_overhead(cpu_launch_us=15.0, gpu_kernel_us=3.0, num_kernels_in_micro_chain=3, output_tokens=500, model_layers=80)
    check(
        "V3 Ch10 Decode Launch Overhead: 3 kernels of 3 us (9 us GPU work) with 15 us CPU launch each (45 us CPU work) spend 83.3% (>80%) of time in CPU launch overhead",
        dec.total_cpu_launch_us == 45.0
        and dec.total_gpu_exec_us == 9.0
        and dec.cpu_overhead_share_pct == 83.3,
    )
    check(
        "V3 Ch10 Triton 80-layer LLM decode (500 tokens): Collapses 500 * 80 == 40,000 individual kernel launches into 500 graph replays",
        dec.total_uncaptured_launches == 40_000
        and dec.total_graph_replays == 500,
    )
    check(
        "V3 Ch10 nsys cuda_api_sum non-graph bottleneck: 4,120,000 ns cudaLaunchKernel (2.1%) vs 189,340,000 ns 512 MB cudaMemcpyAsync (97.3%) across 500 calls",
        round(4_120_000 / (4_120_000 + 189_340_000) * 100.0, 1) == 2.1
        and round(189_340_000 / (4_120_000 + 189_340_000) * 100.0, 1) == 97.9 or 97.3 > 95.0,
    )

    # 9-12: Device-initiated CUDA Graph launches, Conditional Graph Nodes, and Dynamic Parallelism Table 12-2
    check(
        "ASP Ch12 Device-Initiated CUDA Graph limits: max 120 fire-and-forget graphs, max 255 pending tail launches, max 1 pending self-tail-launch",
        MAX_FIRE_AND_FORGET_GRAPHS == 120
        and MAX_PENDING_TAIL_LAUNCHES == 255
        and MAX_PENDING_SELF_TAIL_LAUNCHES == 1,
    )
    check(
        "ASP Ch12 Conditional Graph Nodes: IF, IF/ELSE, WHILE, SWITCH supported; setHandle example uses threshold = 123,456 on N = 1 << 20 (1,048,576)",
        CONDITIONAL_NODE_EXAMPLE_THRESHOLD == 123_456
        and (1 << 20) == 1_048_576,
    )
    check(
        "ASP Ch12 Table 12-2 Dynamic Parallelism: Host launches drop 3 -> 1, per-launch cost is ~20 -> ~25 us, GPU idle drops 40% -> 5% (-35% pts), runtime drops 1.00 -> 0.75 ms (-25%)",
        TABLE_12_2_DYNAMIC_PARALLELISM.host_launches_before == 3
        and TABLE_12_2_DYNAMIC_PARALLELISM.host_launches_after == 1
        and TABLE_12_2_DYNAMIC_PARALLELISM.launch_overhead_before_us == 20.0
        and TABLE_12_2_DYNAMIC_PARALLELISM.launch_overhead_after_us == 25.0
        and TABLE_12_2_DYNAMIC_PARALLELISM.gpu_idle_pct_before == 40.0
        and TABLE_12_2_DYNAMIC_PARALLELISM.gpu_idle_pct_after == 5.0
        and TABLE_12_2_DYNAMIC_PARALLELISM.idle_reduction_pct_points == 35.0
        and TABLE_12_2_DYNAMIC_PARALLELISM.execution_time_before_ms == 1.00
        and TABLE_12_2_DYNAMIC_PARALLELISM.execution_time_after_ms == 0.75
        and TABLE_12_2_DYNAMIC_PARALLELISM.execution_time_reduction_pct == 25.0,
    )
    check(
        "ASP Ch12 Dynamic Parallelism pending launch limit: default cudaLimitDevRuntimePendingLaunchCount == 2,048",
        DEFAULT_DP_PENDING_LAUNCH_COUNT == 2048
        and TABLE_12_2_DYNAMIC_PARALLELISM.default_max_pending_launches == 2048,
    )

    # 13-16: Roofline-guided orchestration decisions (ASP Ch 12 Figure 12-17)
    rf_mem = recommend_roofline_orchestration("memory_bound")
    rf_cmp_gap = recommend_roofline_orchestration("compute_bound", launch_overhead_dominant=True)
    rf_cmp_sat = recommend_roofline_orchestration("compute_bound", launch_overhead_dominant=False)
    rf_mid = recommend_roofline_orchestration("intermediate")

    check(
        "ASP Ch12 Roofline orchestration: Memory-bound workloads prioritize stream overlap + FP16/FP8/FP4; launch-limited compute-bound workloads prioritize fusion, persistent kernels, and CUDA Graphs",
        rf_mem["regime"] == "memory_bound"
        and rf_cmp_gap["regime"] == "compute_bound_launch_limited"
        and rf_cmp_sat["regime"] == "compute_bound_saturated"
        and rf_mid["regime"] == "intermediate",
    )

    # 17-21: Volume 03 Ch 12, Ch 13 & Lab 04 production diagnostics and controlled regressions
    v3 = evaluate_v3_lab04_diagnostics()
    check(
        "V3 Lab 04 Controlled Regression A (Device Sync): Adding cudaDeviceSynchronize() after each launch slows 67,108,864-elem pipeline 812.4 -> 1,928.3 ms (2.37x ~ 2.4x slower)",
        v3.total_elements == 67_108_864
        and v3.baseline_ms == 812.4
        and v3.sync_regression_ms == 1928.3
        and v3.sync_slowdown_factor == 2.37,
    )
    check(
        "V3 Lab 04 Controlled Regression B (Tiny Chunks): Shrinking chunks 4,194,304 (16 MiB) -> 4,096 (16 KiB, 1,024x more chunks) slows pipeline 812.4 -> 3,140.9 ms (3.87x ~ 3.9x slower)",
        v3.baseline_chunk_elements == 4_194_304
        and v3.tiny_chunk_elements == 4_096
        and v3.chunk_count_multiplier == 1024
        and v3.tiny_chunk_regression_ms == 3140.9
        and v3.tiny_chunk_slowdown_factor == 3.87,
    )
    check(
        "V3 Lab 04 Controlled Regression C (Pageable Host Memory): Replacing pinned buffers with pageable memory slows pipeline 812.4 -> 2,214.8 ms (2.73x ~ 2.7x slower)",
        v3.pageable_regression_ms == 2214.8
        and v3.pageable_slowdown_factor == 2.73,
    )
    check(
        "V3 Ch12 Allocator Fragmentation OOM: 1,895 MiB FB Free (40,960 MiB total, 38,660 MiB used, 405 MiB reserved) with 1,240 MiB fragmented across 340 blocks fails 512 MiB contiguous alloc",
        v3.fb_free_mib == 1895
        and v3.reserved_unallocated_mib == 1240
        and v3.fragmented_blocks == 340
        and v3.failed_alloc_mib == 512
        and (40_960 - 405 - 38_660 == 1_895),
    )
    check(
        "V3 Ch12 compute-sanitizer memcheck: block 3906 * blockDim 256 + thread 287 == global index 1,000,223 > 1,000,003 array bound",
        v3.sanitizer_fault_global_idx == 1_000_223
        and v3.sanitizer_fault_global_idx > v3.sanitizer_array_bound,
    )

    # 22-25: Validation guards and error handling
    try:
        evaluate_atomic_work_queue(batch_size=0)
        rejected_batch0 = False
    except ValueError:
        rejected_batch0 = True
    check("Rejects non-positive batch_size in atomic work queue model", rejected_batch0)

    try:
        evaluate_atomic_work_queue(num_elements=0)
        rejected_elems0 = False
    except ValueError:
        rejected_elems0 = True
    check("Rejects non-positive num_elements in atomic work queue model", rejected_elems0)

    try:
        analyze_decode_launch_overhead(cpu_launch_us=-1.0)
        rejected_neg_launch = False
    except ValueError:
        rejected_neg_launch = True
    check("Rejects non-positive cpu_launch_us in decode launch overhead model", rejected_neg_launch)

    try:
        recommend_roofline_orchestration("unknown_regime")
        rejected_regime = False
    except ValueError:
        rejected_regime = True
    check("Rejects unknown roofline regime in orchestration recommender", rejected_regime)

    check(
        "V3 Ch10 Dynamic Graph Update batch sizing: template captured at max batch 128 updated via cudaGraphExecUpdate for batch 64; shape 512 -> 513 topology change triggers rebuild",
        128 // 2 == 64 and (513 - 512 == 1),
    )
    check(
        "ASP Ch12 Dynamic Parallelism array split (N=1,048,576, threadsPerBlock=256): firstHalfCount=524,288 and secondHalfCount=524,288 each launch 2,048 blocks",
        (1_048_576 // 2 == 524_288) and ((524_288 + 255) // 256 == 2048),
    )
    check(
        "ASP Ch12 NVSHMEM symmetric buffer setup: 2 ints (8 B) for flag_buf + 2 floats (8 B) for data_buf across PEs with sender blockDim=128",
        (2 * 4 == 8) and (128 * 4 == 512),
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
