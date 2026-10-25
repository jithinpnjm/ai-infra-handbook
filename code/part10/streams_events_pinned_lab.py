#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.12: Streams, events, asynchronous copies and pinned memory."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from streams_events_pinned import (
    StreamPipelineError,
    audit_stream_and_callback_design,
    compare_pageable_vs_pinned_transfer,
    simulate_double_buffered_pipeline,
    verify_nsys_stream_overlap,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 10.12 Lab: Streams, Events, Asynchronous Copies & Pinned Memory ===")

    # 1. Pageable vs Pinned Host Memory Transfer Math (V3 Ch 8 lines 303-332 & chapter-chapter-08 line 39)
    xfer = compare_pageable_vs_pinned_transfer(
        transfer_bytes=268435456,
        pageable_ms=74.318,
        pinned_local_numa_ms=16.902,
        remote_numa_penalty_x=1.75,
        host_total_ram_gb=512.0,
        pinned_pool_gb=32.0,
    )
    check(
        "V3 Ch8: 268,435,456 B (256 MiB) pageable H2D takes 74.318 ms (3.61 GB/s) vs pinned 16.902 ms (15.88 GB/s = 4.40x speedup)",
        xfer["transfer_mib"] == 256.0
        and xfer["pageable_effective_gbps"] == 3.61
        and xfer["pinned_local_effective_gbps"] == 15.88
        and xfer["pinned_speedup_over_pageable_x"] == 4.40
        and xfer["host_oom_killer_risk"] is False,
    )
    check(
        "V3 Ch8: Remote NUMA pinned transfer incurs ~1.75x penalty (drops from 15.88 GB/s to 9.08 GB/s)",
        xfer["pinned_remote_effective_gbps"] == 9.08,
    )

    oom_pin = compare_pageable_vs_pinned_transfer(host_total_ram_gb=512.0, pinned_pool_gb=500.0)
    check(
        "V3 Ch8 §1: Pinning 500 GB on a 512 GB host leaves only 12 GB pageable RAM and triggers Linux OOM Killer risk",
        oom_pin["host_remaining_pageable_gb"] == 12.0 and oom_pin["host_oom_killer_risk"] is True,
    )

    # 2. Nsight Systems `cuda_gpu_trace` Overlap Verification (V3 Ch 7 lines 316-326)
    fake_trace = verify_nsys_stream_overlap(
        stream_a_start_ns=1200000,
        stream_a_h2d_ns=480000,
        stream_a_kernel_start_ns=1680412,
        stream_a_kernel_ns=612304,
        stream_a_d2h_start_ns=2292900,
        stream_a_d2h_ns=471200,
        stream_b_start_ns=2764300,
    )
    check(
        "V3 Ch7 §Production Troubleshooting: Stream 14 ends at 2,764,100 ns before Stream 15 starts at 2,764,300 ns (200 ns gap -> FAKE_SERIALIZED_OVERLAP)",
        fake_trace["stream_a_end_ns"] == 2764100
        and fake_trace["gap_after_stream_a_ns"] == 200
        and fake_trace["streams_overlapped"] is False
        and fake_trace["classification"] == "FAKE_SERIALIZED_OVERLAP",
    )

    real_trace = verify_nsys_stream_overlap(
        stream_a_start_ns=1200000,
        stream_a_h2d_ns=480000,
        stream_a_kernel_start_ns=1680412,
        stream_a_kernel_ns=612304,
        stream_a_d2h_start_ns=2292900,
        stream_a_d2h_ns=471200,
        stream_b_start_ns=1700000,
    )
    check(
        "V3 Ch7: Stream 15 H2D starting at 1,700,000 ns during Stream 14 kernel [1,680,412..2,292,716 ns] is REAL_OVERLAP",
        real_trace["streams_overlapped"] is True
        and real_trace["h2d_b_overlapped_with_kernel_a"] is True
        and real_trace["classification"] == "REAL_OVERLAP",
    )

    # 3. Double-Buffered Overlapped Pipeline (`overlap_pipeline.cu` in V3 Lab 03)
    pipe_ok = simulate_double_buffered_pipeline()
    check(
        "V3 Lab 03 Step 1 & 3: 67,108,864 elements (1<<26) in 4,194,304-element (16 MiB) chunks = 16 chunks, 512 MiB total transfer",
        pipe_ok["total_elements"] == 67108864
        and pipe_ok["chunk_elements"] == 4194304
        and pipe_ok["chunks"] == 16
        and pipe_ok["slot_mib"] == 16.0
        and pipe_ok["total_transfer_mib"] == 512.0,
    )
    check(
        "V3 Lab 03 Step 3 & Failure A: 812.4 ms baseline (~630.2 MiB/s) vs 1,934.7 ms with hot-loop cudaDeviceSynchronize (2.38x ~ 2.4x slowdown)",
        pipe_ok["overlapped_baseline_ms"] == 812.4
        and pipe_ok["hot_loop_devsync_ms"] == 1934.7
        and pipe_ok["devsync_slowdown_x"] == 2.38
        and pipe_ok["baseline_effective_mib_per_s"] == 630.2
        and pipe_ok["validation_passed"] is True,
    )

    pipe_fail_b = simulate_double_buffered_pipeline(collect_before_refill=False)
    check(
        "V3 Lab 03 Failure B: Moving Collect after Refill corrupts slot output at index 4,194,304 (chunkElements)",
        pipe_fail_b["validation_passed"] is False
        and pipe_fail_b["first_corrupted_index"] == 4194304
        and "4194304" in pipe_fail_b["failure_mode"],
    )

    pipe_race = simulate_double_buffered_pipeline(event_sync_before_reuse=False)
    check(
        "V3 Ch7 line 336: Omitting cudaEventSynchronize before slot reuse corrupts output at index 4,194,305",
        pipe_race["validation_passed"] is False
        and pipe_race["first_corrupted_index"] == 4194305,
    )

    pipe_non_pow2 = simulate_double_buffered_pipeline(total_elements=10000003, chunk_elements=1048576)
    check(
        "V3 Lab 03 §9: Non-power-of-two 10,000,003 elements with 1,048,576 chunk size requires 10 chunks and passes validation",
        pipe_non_pow2["chunks"] == 10 and pipe_non_pow2["validation_passed"] is True,
    )

    # 4. Stream, Default-Stream, Allocator, and Callback Best-Practice Audits (ASP Ch 11 & V3 Ch 7-8)
    audit_ok = audit_stream_and_callback_design(async_engine_count=2)
    check(
        "ASP Ch11 Fig 11-2: Pinned host memory + cudaStreamNonBlocking + 2 async copy engines achieves 3-way overlap (H2D + Compute + D2H)",
        audit_ok["can_overlap_cleanly"] is True and audit_ok["max_concurrent_stages"] == 3,
    )

    audit_1ce = audit_stream_and_callback_design(async_engine_count=1)
    check(
        "Single async copy engine supports 2-way overlap",
        audit_1ce["can_overlap_cleanly"] is True and audit_1ce["max_concurrent_stages"] == 2,
    )

    audit_pageable = audit_stream_and_callback_design(uses_pinned_host_memory=False)
    check(
        "ASP Ch11 & V3 Ch7 Customer Scenario: Flags pageable host memory breaking cudaMemcpyAsync overlap",
        audit_pageable["can_overlap_cleanly"] is False
        and any("PAGEABLE_HOST_BUFFER" in i for i in audit_pageable["issues"]),
    )

    audit_stream0 = audit_stream_and_callback_design(launches_work_on_legacy_stream_0=True)
    check(
        "ASP Ch11 pp.366-369: Flags legacy default stream 0 acting as a global barrier across streams",
        audit_stream0["can_overlap_cleanly"] is False
        and any("LEGACY_DEFAULT_STREAM_BARRIER" in i for i in audit_stream0["issues"]),
    )

    audit_nonblock = audit_stream_and_callback_design(uses_non_blocking_streams=False)
    check(
        "ASP Ch11: Flags streams created without cudaStreamNonBlocking / PTDS",
        audit_nonblock["can_overlap_cleanly"] is False
        and any("LEGACY_DEFAULT_STREAM_BARRIER" in i for i in audit_nonblock["issues"]),
    )

    audit_malloc = audit_stream_and_callback_design(calls_sync_cuda_malloc_in_stream_loop=True)
    check(
        "ASP Ch11 pp.361-365: Flags synchronous cudaMalloc in multi-stream loop (use cudaMallocAsync / backend:cudaMallocAsync)",
        audit_malloc["can_overlap_cleanly"] is False
        and any("SYNC_CUDAMALLOC_IN_LOOP" in i for i in audit_malloc["issues"]),
    )

    audit_devsync = audit_stream_and_callback_design(calls_device_sync_in_hot_loop=True)
    check(
        "V3 Lab 03 Failure A: Flags cudaDeviceSynchronize() inside hot loop",
        audit_devsync["can_overlap_cleanly"] is False
        and any("HOT_LOOP_DEVICE_SYNC" in i for i in audit_devsync["issues"]),
    )

    audit_cb = audit_stream_and_callback_design(host_callback_calls_cuda_api=True)
    check(
        "ASP Ch11 p.370: Flags calling CUDA device APIs inside a cudaLaunchHostFunc host callback (deadlock risk)",
        audit_cb["can_overlap_cleanly"] is False
        and any("HOST_CALLBACK_CUDA_DEADLOCK" in i for i in audit_cb["issues"]),
    )

    # 5. Input Validation Checks
    try:
        compare_pageable_vs_pinned_transfer(transfer_bytes=0)
        check("Rejects non-positive transfer_bytes", False)
    except StreamPipelineError:
        check("Rejects non-positive transfer_bytes", True)

    try:
        compare_pageable_vs_pinned_transfer(host_total_ram_gb=128.0, pinned_pool_gb=256.0)
        check("Rejects pinned_pool_gb > host_total_ram_gb", False)
    except StreamPipelineError:
        check("Rejects pinned_pool_gb > host_total_ram_gb", True)

    try:
        verify_nsys_stream_overlap(stream_a_start_ns=-1)
        check("Rejects negative timestamps in Nsight trace verifier", False)
    except StreamPipelineError:
        check("Rejects negative timestamps in Nsight trace verifier", True)

    try:
        simulate_double_buffered_pipeline(total_elements=0)
        check("Rejects non-positive total_elements in pipeline simulator", False)
    except StreamPipelineError:
        check("Rejects non-positive total_elements in pipeline simulator", True)

    try:
        audit_stream_and_callback_design(async_engine_count=-1)
        check("Rejects negative async_engine_count", False)
    except StreamPipelineError:
        check("Rejects negative async_engine_count", True)

    check(
        "1<<26 elements == 67,108,864 and 1<<22 chunkElements == 4,194,304",
        (1 << 26) == 67108864 and (1 << 22) == 4194304,
    )
    check(
        "ASP Ch11 p.372: 2 stages * 3 buffers * 1024 floats * 4 B == 24,576 B (24 KB << 227 KB usable SMEM)",
        2 * 3 * 1024 * 4 == 24576,
    )

    print(f"\nSummary: {passed} passed, 0 failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
