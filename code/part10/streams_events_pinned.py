#!/usr/bin/env python3
"""Chapter 10.12 model: Streams, Events, Asynchronous Copies, and Pinned Memory.

Encodes the verifiable stream ordering and default-stream (`cudaStreamLegacy`,
`cudaStreamPerThread`, `cudaStreamNonBlocking`) rules, pageable vs pinned DMA
transfer math, 2-way and 3-way copy-compute overlap timelines, Nsight Systems
`cuda_gpu_trace` overlap verification, and double-buffered pipeline slot
ownership from:
- AI Systems Performance Engineering (ASP) Chapter 11 (pp. 355-378):
  Overlapping kernels and transfers across streams, 3-way overlap (H2D + Compute
  + D2H requiring `deviceProp.asyncEngineCount >= 2` and pinned host memory),
  `pin_memory=True` in PyTorch DataLoaders, `PYTORCH_ALLOC_CONF=backend:cudaMallocAsync`,
  legacy default stream 0 barrier vs Per-Thread Default Stream (`PTDS`,
  `--default-stream per-thread` / `CUDA_API_PER_THREAD_DEFAULT_STREAM=1`) vs
  explicit `cudaStreamNonBlocking` streams, `cudaEventRecord` + `cudaStreamWaitEvent`,
  and `cudaLaunchHostFunc` host callback deadlock rule.
- nvidia-devops Volume 03 Chapters 7-8 & Lab 03:
  256 MiB (`268,435,456` bytes) H2D transfer benchmark: pageable `74.318 ms`
  (`3.61 GB/s`) vs pinned `16.902 ms` (`15.88 GB/s` = `4.4x` speedup), remote
  NUMA pinned penalty (`~1.75x`), pinning `500 GB` on a `512 GB` host starving
  OS and triggering Linux OOM Killer, `nsys` `cuda_gpu_trace` fake overlap
  (Stream 14 `[1,200,000 .. 2,764,100 ns]` followed serially by Stream 15 at
  `2,764,300 ns`), and Lab 03 `overlap_pipeline.cu` (`67,108,864` elements =
  `1<<26`, `chunkElements = 4,194,304 = 1<<22` = `16 MiB`/chunk across `16`
  chunks, `812.4 ms` 2-stream overlapped baseline vs `1,934.7 ms` with hot-loop
  `cudaDeviceSynchronize()` = `2.38x` ~ `2.4x` slowdown, and premature slot
  reuse corrupting index `4,194,304` / `4,194,305`).
"""

from __future__ import annotations

from typing import Dict, List


class StreamPipelineError(ValueError):
    """Raised when invalid stream, transfer, or pipeline parameters are supplied."""


def compare_pageable_vs_pinned_transfer(
    transfer_bytes: int = 268435456,
    pageable_ms: float = 74.318,
    pinned_local_numa_ms: float = 16.902,
    remote_numa_penalty_x: float = 1.75,
    host_total_ram_gb: float = 512.0,
    pinned_pool_gb: float = 32.0,
) -> Dict[str, object]:
    """Compare pageable vs pinned (local & remote NUMA) H2D DMA transfers per V3 Ch 8 (§Production Troubleshooting).

    Data points from V3 Ch 8 (lines 303-332) & chapter-chapter-08 (line 39):
    - Payload: `268,435,456` bytes (`256 MiB` = `0.268435456 GB`).
    - Pageable H2D: `74.318 ms` -> `0.268435456 GB / 0.074318 s = 3.61 GB/s` effective.
    - Pinned H2D (local NUMA): `16.902 ms` -> `0.268435456 GB / 0.016902 s = 15.88 GB/s` effective (`4.40x` speedup).
    - Pinned H2D (remote NUMA socket crossing UPI/xGMI): `~1.75x` throughput penalty (`~9.07 GB/s`).
    - OS safety rule: pinning `500 GB` on a `512 GB` host leaves almost no pageable RAM for the Linux
      kernel and triggers the OOM Killer.
    """
    if transfer_bytes <= 0 or pageable_ms <= 0 or pinned_local_numa_ms <= 0 or remote_numa_penalty_x < 1.0:
        raise StreamPipelineError("Transfer size, timings, and penalty factor must be positive")
    if host_total_ram_gb <= 0 or pinned_pool_gb < 0 or pinned_pool_gb > host_total_ram_gb:
        raise StreamPipelineError("Invalid host RAM or pinned pool size")

    gb_decimal = transfer_bytes / 1e9
    pageable_gbps = gb_decimal / (pageable_ms / 1000.0)
    pinned_local_gbps = gb_decimal / (pinned_local_numa_ms / 1000.0)
    pinned_remote_gbps = pinned_local_gbps / remote_numa_penalty_x
    speedup_x = pageable_ms / pinned_local_numa_ms

    pinned_ram_fraction = pinned_pool_gb / host_total_ram_gb
    oom_killer_risk = (host_total_ram_gb - pinned_pool_gb) < 32.0 or pinned_ram_fraction > 0.50

    return {
        "transfer_bytes": transfer_bytes,
        "transfer_mib": round(transfer_bytes / (1024 * 1024), 1),
        "pageable_ms": round(pageable_ms, 3),
        "pinned_local_numa_ms": round(pinned_local_numa_ms, 3),
        "pageable_effective_gbps": round(pageable_gbps, 2),
        "pinned_local_effective_gbps": round(pinned_local_gbps, 2),
        "pinned_remote_effective_gbps": round(pinned_remote_gbps, 2),
        "pinned_speedup_over_pageable_x": round(speedup_x, 2),
        "pinned_pool_gb": round(pinned_pool_gb, 2),
        "host_remaining_pageable_gb": round(host_total_ram_gb - pinned_pool_gb, 2),
        "host_oom_killer_risk": oom_killer_risk,
    }


def verify_nsys_stream_overlap(
    stream_a_start_ns: int = 1200000,
    stream_a_h2d_ns: int = 480000,
    stream_a_kernel_start_ns: int = 1680412,
    stream_a_kernel_ns: int = 612304,
    stream_a_d2h_start_ns: int = 2292900,
    stream_a_d2h_ns: int = 471200,
    stream_b_start_ns: int = 2764300,
) -> Dict[str, object]:
    """Analyze an Nsight Systems `cuda_gpu_trace` timeline to prove whether two streams overlapped per V3 Ch 7 (lines 316-326).

    In V3 Ch 7:
    - Stream 14 runs H2D `[1,200,000 .. 1,680,000 ns]`, kernel `[1,680,412 .. 2,292,716 ns]`,
      and D2H `[2,292,900 .. 2,764,100 ns]`.
    - Stream 15 starts its H2D at `2,764,300 ns` (`200 ns` AFTER Stream 14's D2H finished at `2,764,100 ns`).
    - Because `stream_b_start_ns >= stream_a_end_ns`, the two streams executed completely serially
      ("Fake overlap" caused by pageable staging, legacy default stream 0, or `cudaDeviceSynchronize()`).
    - True copy-compute overlap occurs when Stream 15's H2D starts during Stream 14's kernel window
      `[1,680,412 .. 2,292,716 ns]`.
    """
    if stream_a_start_ns < 0 or stream_b_start_ns < 0:
        raise StreamPipelineError("Timestamps must be non-negative")

    stream_a_end_ns = stream_a_d2h_start_ns + stream_a_d2h_ns
    overlapped = stream_b_start_ns < stream_a_end_ns
    overlapped_with_kernel = stream_a_kernel_start_ns <= stream_b_start_ns < (stream_a_kernel_start_ns + stream_a_kernel_ns)

    return {
        "stream_a_start_ns": stream_a_start_ns,
        "stream_a_end_ns": stream_a_end_ns,
        "stream_b_start_ns": stream_b_start_ns,
        "gap_after_stream_a_ns": stream_b_start_ns - stream_a_end_ns,
        "streams_overlapped": overlapped,
        "h2d_b_overlapped_with_kernel_a": overlapped_with_kernel,
        "classification": "REAL_OVERLAP" if overlapped else "FAKE_SERIALIZED_OVERLAP",
    }


def simulate_double_buffered_pipeline(
    total_elements: int = 1 << 26,
    chunk_elements: int = 1 << 22,
    stream_count: int = 2,
    overlapped_baseline_ms: float = 812.4,
    hot_loop_devsync_ms: float = 1934.7,
    collect_before_refill: bool = True,
    event_sync_before_reuse: bool = True,
) -> Dict[str, object]:
    """Simulate the double-buffered CUDA pipeline from V3 Lab 03 (`overlap_pipeline.cu`).

    Parameters & rules from V3 Lab 03 (lines 161-265, 300-303, 366-388) and V3 Ch 7 (lines 335-340):
    - `total_elements = 1 << 26 = 67,108,864` floats (`256 MiB` input + `256 MiB` output = `512 MiB` total transfer).
    - `chunk_elements = 1 << 22 = 4,194,304` floats (`16 MiB` per chunk, `16` chunks total).
    - `stream_count = 2` non-blocking streams (`cudaStreamNonBlocking`), each owning independent pinned
      `hostInput[slot]`, `hostOutput[slot]`, `deviceInput[slot]`, `deviceOutput[slot]`, and `complete[slot]` event.
    - Baseline 2-stream overlapped run completes in `812.4 ms` (`~630.2 MiB/s` useful end-to-end throughput).
    - Failure A (inserting `cudaDeviceSynchronize()` inside the chunk loop) serializes the streams and
      increases runtime to `1,934.7 ms` (`2.38x` ~ `2.4x` slower).
    - Failure B (moving `Collect` after `Refill`, or omitting `cudaEventSynchronize(complete[slot])` before reuse)
      overwrites slot 0/1 before the previous chunk's output is collected, failing validation at index
      `4,194,304` (`chunkElements`, first element of chunk 1) or `4,194,305` (`chunkElements + 1`).
    """
    if total_elements <= 0 or chunk_elements <= 0 or stream_count <= 0:
        raise StreamPipelineError("total_elements, chunk_elements, and stream_count must be positive")
    if overlapped_baseline_ms <= 0 or hot_loop_devsync_ms <= 0:
        raise StreamPipelineError("Timings must be positive")

    chunks = (total_elements + chunk_elements - 1) // chunk_elements
    slot_bytes = chunk_elements * 4
    total_transfer_mib = (total_elements * 4 * 2) / (1024 * 1024)
    effective_mib_per_s = total_transfer_mib / (overlapped_baseline_ms / 1000.0)
    devsync_slowdown_x = hot_loop_devsync_ms / overlapped_baseline_ms

    validation_passed = collect_before_refill and event_sync_before_reuse
    first_corrupted_index = None
    failure_mode = "NONE"

    if not collect_before_refill:
        first_corrupted_index = chunk_elements
        failure_mode = f"FAILURE_B_COLLECT_AFTER_REFILL (validation failed at index {first_corrupted_index})"
    elif not event_sync_before_reuse:
        first_corrupted_index = chunk_elements + 1
        failure_mode = f"PREMATURE_SLOT_REUSE_RACE (validation failed at index {first_corrupted_index})"

    return {
        "total_elements": total_elements,
        "chunk_elements": chunk_elements,
        "chunks": chunks,
        "stream_count": stream_count,
        "slot_mib": round(slot_bytes / (1024 * 1024), 1),
        "total_transfer_mib": round(total_transfer_mib, 1),
        "overlapped_baseline_ms": round(overlapped_baseline_ms, 1),
        "hot_loop_devsync_ms": round(hot_loop_devsync_ms, 1),
        "devsync_slowdown_x": round(devsync_slowdown_x, 2),
        "baseline_effective_mib_per_s": round(effective_mib_per_s, 1),
        "validation_passed": validation_passed,
        "first_corrupted_index": first_corrupted_index,
        "failure_mode": failure_mode,
    }


def audit_stream_and_callback_design(
    uses_pinned_host_memory: bool = True,
    uses_non_blocking_streams: bool = True,
    launches_work_on_legacy_stream_0: bool = False,
    calls_sync_cuda_malloc_in_stream_loop: bool = False,
    calls_device_sync_in_hot_loop: bool = False,
    host_callback_calls_cuda_api: bool = False,
    async_engine_count: int = 2,
) -> Dict[str, object]:
    """Audit a multi-stream CUDA / PyTorch pipeline against ASP Ch 11 and V3 Ch 7-8 best practices."""
    if async_engine_count < 0:
        raise StreamPipelineError("async_engine_count cannot be negative")

    issues: List[str] = []
    if not uses_pinned_host_memory:
        issues.append(
            "PAGEABLE_HOST_BUFFER: cudaMemcpyAsync on pageable memory forces a synchronous host staging copy; allocate with cudaMallocHost / cudaHostAlloc or DataLoader(pin_memory=True)."
        )
    if not uses_non_blocking_streams or launches_work_on_legacy_stream_0:
        issues.append(
            "LEGACY_DEFAULT_STREAM_BARRIER: Work issued to legacy stream 0 (or streams created without cudaStreamNonBlocking / PTDS) acts as a global barrier across all streams."
        )
    if calls_sync_cuda_malloc_in_stream_loop:
        issues.append(
            "SYNC_CUDAMALLOC_IN_LOOP: Synchronous cudaMalloc/cudaFree stalls all active streams; use cudaMallocAsync/cudaFreeAsync or PYTORCH_ALLOC_CONF=backend:cudaMallocAsync."
        )
    if calls_device_sync_in_hot_loop:
        issues.append(
            "HOT_LOOP_DEVICE_SYNC: cudaDeviceSynchronize() in the batch loop destroys stream overlap (2.38x slowdown in Lab 03); use cudaEventRecord + cudaStreamWaitEvent."
        )
    if host_callback_calls_cuda_api:
        issues.append(
            "HOST_CALLBACK_CUDA_DEADLOCK: Calling CUDA device APIs (e.g. cudaMemcpy) inside a cudaLaunchHostFunc callback risks circular deadlock on the runtime callback thread (ASP Ch 11 p. 370)."
        )

    max_way_overlap = 3 if (async_engine_count >= 2 and len(issues) == 0) else (2 if (async_engine_count == 1 and len(issues) == 0) else 1)

    return {
        "can_overlap_cleanly": len(issues) == 0,
        "max_concurrent_stages": max_way_overlap,
        "issues": issues,
    }
