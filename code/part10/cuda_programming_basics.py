#!/usr/bin/env python3
"""Chapter 10.11 model: CUDA Programming Basics: Kernels, Indexing, and Memory.

Encodes the verifiable CUDA launch-configuration and indexing formulas, warp
lane waste calculations, hardware thread/block/SM/grid limits, memory-API
lifecycle timings, Unified Memory demand-paging and oversubscription cliffs,
and synchronization/correctness diagnostics from:
- AI Systems Performance Engineering (ASP) Chapter 6 (pp. 177-198):
  Blackwell B200 thread/block/SM/grid limits (32 threads/warp, 1,024 threads/block,
  32 warps/block, 64 warps/SM = 2,048 threads/SM, 32 blocks/SM, grid X=2,147,483,647,
  Y=65,535, Z=65,535, 128 concurrent grids), 1D/2D kernel indexing (`N = 1,000,000`
  with 256 threads = 3,907 blocks; `N = 63` across 2 warps = 64 threads with 1 guarded),
  and stream-ordered memory pools (`cudaMallocAsync`/`cudaFreeAsync`).
- nvidia-devops Volume 03 Chapters 1, 3, 4, 5, 6, 9 & Lab 02:
  1D global index (`blockIdx.x * blockDim.x + threadIdx.x`, e.g. Block 3, Thread 5
  with blockDim 256 = 773), ceiling vs truncated block count (`N = 1,000,003`,
  threads = 256 -> ceiling 3,907 blocks = 1,000,192 threads with 189 guarded vs
  truncated 3,906 blocks = 999,936 threads leaving 67 elements untouched),
  4K image (`3840 x 2160`) launched with `dim3(1,1)` wasting 31/32 = 96.88% (~97%)
  of warp lanes vs `dim3(16,16)` (256 threads = 100% warp fill), `<<<1, 50>>>`
  spawning 2 warps (64 threads) with 14 idle lanes, `<<<64, 256>>>` leaving 68 of
  132 H100 SMs idle, async host timer trap (`0.014 ms` submission vs `4.812 ms`
  CUDA event time = 343.71x ~ 340x gap), Lab 02 `vector_add.cu` (`0.847 ms` copy in
  + `0.412 ms` copy out = `1.259 ms` vs `0.096 ms` kernel = `13.11x` ~ `13x` transfer
  ratio), `nsys` `cuda_api_sum` (`cudaMalloc` 71.2% + `cudaFree` 6.4% = 77.6% of API
  time across 4,000 calls), Unified Memory cold first-touch (`812.4 ms` vs `41.2 ms`
  warm = `19.72x` ~ `20x`, reduced to `38.9 ms` via `cudaMemPrefetchAsync`), CPU debug
  print (`96.7 ms` vs `4.1 ms` kernel = `23.59x`), and 40 GB oversubscription cliff
  (`24 GB` @ 118 GB/s -> `36 GB` @ 104 GB/s -> `44 GB` @ 9 GB/s).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


class CUDABasicsError(ValueError):
    """Raised when invalid CUDA launch, indexing, or memory parameters are provided."""


@dataclass(frozen=True)
class CUDAHardwareLimits:
    warp_size: int = 32
    max_threads_per_block: int = 1024
    max_warps_per_block: int = 32
    max_resident_warps_per_sm: int = 64
    max_resident_threads_per_sm: int = 2048
    max_active_blocks_per_sm: int = 32
    max_grid_dim_x: int = 2147483647
    max_grid_dim_y: int = 65535
    max_grid_dim_z: int = 65535
    max_concurrent_grids: int = 128


BLACKWELL_CUDA_LIMITS = CUDAHardwareLimits()


def calc_1d_launch_and_indexing(
    element_count: int,
    threads_per_block: int = 256,
    sample_block_idx: int = 3,
    sample_thread_idx: int = 5,
    gpu_sm_count: int = 132,
) -> Dict[str, object]:
    """Calculate 1D CUDA grid geometry, warp lane efficiency, and truncation vs ceiling coverage.

    Sources:
    - V3 Ch 3, Ch 4 & Lab 02; ASP Ch 6 (pp. 181-190).
    """
    if element_count <= 0:
        raise CUDABasicsError("element_count must be positive")
    if threads_per_block <= 0 or threads_per_block > BLACKWELL_CUDA_LIMITS.max_threads_per_block:
        raise CUDABasicsError(
            f"invalid configuration argument: threads_per_block ({threads_per_block}) "
            f"must be in 1..{BLACKWELL_CUDA_LIMITS.max_threads_per_block}"
        )
    if sample_block_idx < 0 or sample_thread_idx < 0 or sample_thread_idx >= threads_per_block:
        raise CUDABasicsError("sample_block_idx and sample_thread_idx must be within valid bounds")
    if gpu_sm_count <= 0:
        raise CUDABasicsError("gpu_sm_count must be positive")

    warp_size = BLACKWELL_CUDA_LIMITS.warp_size
    blocks_ceiling = (element_count + threads_per_block - 1) // threads_per_block
    blocks_truncated = element_count // threads_per_block

    launched_threads_ceiling = blocks_ceiling * threads_per_block
    guarded_extra_threads = launched_threads_ceiling - element_count
    unprocessed_if_truncated = element_count - (blocks_truncated * threads_per_block)

    warps_per_block = (threads_per_block + warp_size - 1) // warp_size
    allocated_warp_lanes_per_block = warps_per_block * warp_size
    idle_warp_lanes_per_block = allocated_warp_lanes_per_block - threads_per_block
    warp_lane_efficiency_pct = (threads_per_block / allocated_warp_lanes_per_block) * 100.0

    sample_global_index = sample_block_idx * threads_per_block + sample_thread_idx
    idle_sms = max(0, gpu_sm_count - blocks_ceiling)

    return {
        "element_count": element_count,
        "threads_per_block": threads_per_block,
        "blocks_ceiling": blocks_ceiling,
        "blocks_truncated": blocks_truncated,
        "launched_threads_ceiling": launched_threads_ceiling,
        "guarded_extra_threads": guarded_extra_threads,
        "unprocessed_if_truncated": unprocessed_if_truncated,
        "warps_per_block": warps_per_block,
        "allocated_warp_lanes_per_block": allocated_warp_lanes_per_block,
        "idle_warp_lanes_per_block": idle_warp_lanes_per_block,
        "warp_lane_efficiency_pct": round(warp_lane_efficiency_pct, 2),
        "sample_global_index": sample_global_index,
        "gpu_sm_count": gpu_sm_count,
        "idle_sms": idle_sms,
        "grid_underfills_gpu": idle_sms > 0,
    }


def evaluate_2d_image_launch(
    width: int = 3840,
    height: int = 2160,
    block_x: int = 16,
    block_y: int = 16,
) -> Dict[str, object]:
    """Evaluate a 2D image launch configuration per V3 Ch 4 Customer Scenario & ASP Ch 6 (p. 191).

    In V3 Ch 4 Customer Scenario (lines 78-90):
    - Launching a 4K image (`3840 x 2160`) with `dim3(1, 1)` (1 thread per block) spawns
      `8,294,400` blocks of 1 thread, wasting `31 of 32` warp lanes (`96.88%` ~ `97%` waste).
    - Reconfiguring to `dim3(16, 16)` (`256` threads = `8` full warps) achieves `100.0%` warp
      lane utilization across `240 x 135 = 32,400` blocks.
    """
    if width <= 0 or height <= 0 or block_x <= 0 or block_y <= 0:
        raise CUDABasicsError("Image and block dimensions must be positive")
    threads_per_block = block_x * block_y
    if threads_per_block > BLACKWELL_CUDA_LIMITS.max_threads_per_block:
        raise CUDABasicsError("block_x * block_y exceeds 1024 threads per block")

    grid_x = (width + block_x - 1) // block_x
    grid_y = (height + block_y - 1) // block_y
    total_blocks = grid_x * grid_y

    warp_size = BLACKWELL_CUDA_LIMITS.warp_size
    warps_per_block = (threads_per_block + warp_size - 1) // warp_size
    allocated_lanes = warps_per_block * warp_size
    wasted_lanes_per_block = allocated_lanes - threads_per_block
    wasted_lane_pct = (wasted_lanes_per_block / allocated_lanes) * 100.0

    return {
        "width": width,
        "height": height,
        "block_dim": (block_x, block_y),
        "threads_per_block": threads_per_block,
        "grid_dim": (grid_x, grid_y),
        "total_blocks": total_blocks,
        "warps_per_block": warps_per_block,
        "wasted_lanes_per_block": wasted_lanes_per_block,
        "wasted_lane_pct": round(wasted_lane_pct, 2),
        "active_lane_pct": round(100.0 - wasted_lane_pct, 2),
    }


def analyze_memory_and_timing_Lifecycle(
    copy_in_ms: float = 0.847,
    kernel_ms: float = 0.096,
    copy_out_ms: float = 0.412,
    async_host_timer_ms: float = 0.014,
    true_event_kernel_ms: float = 4.812,
    malloc_ns_pct: float = 71.2,
    memcpy_ns_pct: float = 18.6,
    free_ns_pct: float = 6.4,
    launch_ns_pct: float = 3.8,
) -> Dict[str, float]:
    """Quantify the timing and memory-lifecycle metrics from V3 Ch 3, Ch 5 & Lab 02.

    1. V3 Lab 02 Step 4: `copy_in` (0.847 ms) + `copy_out` (0.412 ms) = 1.259 ms vs `kernel` (0.096 ms)
       -> transfer time is `13.11x` (~13x) larger than kernel compute time.
    2. V3 Ch 3 §Production Troubleshooting: host `steady_clock` around async launch (`0.014 ms`) vs
       `cudaEventElapsedTime` (`4.812 ms`) = `343.71x` (~340x) gap.
    3. V3 Ch 5 §Production Troubleshooting: `cudaMalloc` (71.2%) + `cudaFree` (6.4%) = `77.6%` of
       total CUDA API time across 4,000 unpooled requests (`20.42x` >8x the 3.8% kernel launch time).
    """
    if copy_in_ms < 0 or kernel_ms <= 0 or copy_out_ms < 0 or async_host_timer_ms <= 0 or true_event_kernel_ms <= 0:
        raise CUDABasicsError("Timing values must be positive")

    total_transfer_ms = copy_in_ms + copy_out_ms
    transfer_to_kernel_ratio = total_transfer_ms / kernel_ms
    async_timer_error_ratio = true_event_kernel_ms / async_host_timer_ms
    alloc_free_api_pct = malloc_ns_pct + free_ns_pct
    alloc_to_launch_ratio = alloc_free_api_pct / launch_ns_pct

    return {
        "total_transfer_ms": round(total_transfer_ms, 3),
        "kernel_ms": round(kernel_ms, 3),
        "transfer_to_kernel_ratio_x": round(transfer_to_kernel_ratio, 2),
        "async_timer_error_ratio_x": round(async_timer_error_ratio, 2),
        "alloc_free_api_pct": round(alloc_free_api_pct, 1),
        "alloc_to_launch_ratio_x": round(alloc_to_launch_ratio, 2),
    }


def evaluate_unified_memory_behavior(
    working_set_gb: float,
    device_capacity_gb: float = 40.0,
    cold_first_touch_ms: float = 812.4,
    warm_iter_ms: float = 41.2,
    prefetch_ms: float = 38.9,
    kernel_only_ms: float = 4.1,
    cpu_debug_print_ms: float = 96.7,
) -> Dict[str, object]:
    """Evaluate Unified Memory (`cudaMallocManaged`) first-touch, prefetch, CPU read stall, and oversubscription per V3 Ch 9.

    Data points from V3 Ch 9 (§Production Troubleshooting):
    - Cold iteration 1 (`812.4 ms`) vs warm iteration 2 (`41.2 ms`) = `19.72x` (~20x) slower due to page faults;
      `cudaMemPrefetchAsync` moves migration into a `38.9 ms` schedulable operation so iteration 1 runs in `41.6 ms`.
    - Working set vs 40 GB GPU capacity:
      24 GB (60%) -> 118 GB/s; 36 GB (90%) -> 104 GB/s; 44 GB (110%, oversubscribed) -> 9 GB/s (page thrashing).
    - Single CPU debug read (`std::cout << data[0]`) costs `96.7 ms` vs `4.1 ms` kernel (`23.59x` >23x the kernel).
    """
    if working_set_gb <= 0 or device_capacity_gb <= 0:
        raise CUDABasicsError("working_set_gb and device_capacity_gb must be positive")

    utilization_pct = (working_set_gb / device_capacity_gb) * 100.0
    oversubscribed = working_set_gb > device_capacity_gb

    if working_set_gb <= 24.0:
        effective_bw_gbps = 118.0
        state = "RESIDENT_HIGH_LOCALITY"
    elif not oversubscribed:
        effective_bw_gbps = 104.0
        state = "RESIDENT_NEAR_CAPACITY"
    else:
        effective_bw_gbps = 9.0
        state = "OVERSUBSCRIBED_PAGE_THRASHING"

    return {
        "working_set_gb": round(working_set_gb, 1),
        "device_capacity_gb": round(device_capacity_gb, 1),
        "capacity_utilization_pct": round(utilization_pct, 1),
        "oversubscribed": oversubscribed,
        "state": state,
        "effective_bw_gbps": effective_bw_gbps,
        "cold_vs_warm_ratio_x": round(cold_first_touch_ms / warm_iter_ms, 2),
        "prefetch_ms": prefetch_ms,
        "cpu_debug_stall_ratio_x": round(cpu_debug_print_ms / kernel_only_ms, 2),
    }


def diagnose_cuda_correctness_and_sync(
    passed_host_pointer_to_kernel: bool = False,
    missing_bounds_check: bool = False,
    used_truncated_block_division: bool = False,
    cross_block_spin_wait: bool = False,
    unprotected_concurrent_reduction: bool = False,
) -> Dict[str, object]:
    """Diagnose the 5 classic CUDA correctness/synchronization bugs from V3 Ch 3, Ch 4, Ch 6 & Lab 02."""
    defects: List[str] = []
    if passed_host_pointer_to_kernel:
        defects.append(
            "HOST_POINTER_IN_KERNEL: Passed CPU malloc() pointer directly to __global__ kernel instead of cudaMalloc() device pointer (V3 Ch 3 Customer Scenario)."
        )
    if missing_bounds_check:
        defects.append(
            "MISSING_BOUNDS_CHECK: Missing 'if (idx < N)' guard allows extra threads in final partial block to write out of bounds (cudaErrorIllegalAddress or silent heap corruption, V3 Ch 4 & Lab 02 Failure A)."
        )
    if used_truncated_block_division:
        defects.append(
            "TRUNCATED_GRID_UNDERLAUNCH: Used integer truncation 'N / threadsPerBlock' instead of ceiling division '(N + threadsPerBlock - 1) / threadsPerBlock', leaving tail elements untouched at 0.0 (V3 Ch 4 & Lab 02 Failure D)."
        )
    if cross_block_spin_wait:
        defects.append(
            "INTER_BLOCK_SPIN_DEADLOCK: Kernel uses 'while(true)' spin-loop waiting for another thread block; blocks have no guaranteed scheduling order and deadlock SMs (split into two sequential kernels instead, V3 Ch 6 Customer Scenario)."
        )
    if unprotected_concurrent_reduction:
        defects.append(
            "DATA_RACE_NON_DETERMINISTIC: Concurrent threads update shared/global sum without __syncthreads() or atomicAdd(), producing different wrong sums across runs (e.g. 483920.125 vs 501234.875 vs 512000.0, V3 Ch 6)."
        )

    return {
        "correct": len(defects) == 0,
        "defect_count": len(defects),
        "defects": defects,
    }
