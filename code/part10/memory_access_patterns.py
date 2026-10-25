#!/usr/bin/env python3
"""Chapter 10.13 model: Memory Access Patterns and Profiling.

Encodes the verifiable global-memory coalescing sector math, vectorized load
(`float4` 16B vs Blackwell `float8` 32B) transaction counts, shared-memory
tiling reuse & register residency limits, 32-bank conflict & `+1` padding math,
warp shuffle butterfly reduction steps, read-only cache (`const __restrict__`),
and TMA (`cuda::memcpy_async`) double-buffering benchmarks from:
- AI Systems Performance Engineering (ASP) Chapter 7 (pp. 215-252):
  - Coalesced vs uncoalesced global loads (128-byte cache line = 4 x 32-byte
    sectors; aligned stride-1 = 4.0 sectors/req; misaligned = 5 or 8 sectors;
    stride-2 = 8.0 sectors/req; worst-case scattered = 32.0 sectors/req;
    Table 7-1: DRAM 25% -> 90%, Load Efficiency 23% -> 99%, Sectors/req 8.0 -> 4.0,
    SM Active 62% -> 99%, Runtime 4.8 ms -> 1.3 ms).
  - Vectorized loads (`float4` 16B/thread = 512B/warp = 4 x 128B lines = 16 sectors;
    Blackwell CUDA 13+ `alignas(32) float8` 32B/thread = 1,024B/warp = 8 x 128B
    lines = 32 sectors; `cudaMalloc` >= 256B alignment; Table 7-2: Load Efficiency
    28% -> 97%, Sectors/req 31.8 -> 4.0, DRAM 25% -> 90%, Runtime 4.2 ms -> 1.2 ms).
  - Shared-memory tiling (`32x32` tile on `N = 1,024`: Table 7-4 DRAM 90% -> 25%,
    Occupancy 42% -> 89%, GFLOPS 15 -> 170, Global load sectors 9,800 -> 1,200,
    Shared memory throughput 52% -> 99%, Intensity 1.5 FLOPs/B @ 10 GB/s ->
    8.0 FLOPs/B @ 21 GB/s; `64x64` tile register math: 12 regs/thread = 12,288
    regs/block -> 5 blocks ~61,440 regs vs 2,048-thread cap = 2 blocks; or
    22 regs/thread = 22,528 regs/block = 2 blocks).
  - Shared-memory bank conflicts (32 banks x 4B = 128B wrap; `[32][32]` vs
    padded `[32][33]` ~3% overhead; Table 7-5: Bank conflicts 4.8M -> 0,
    Shared util 52% -> 100%, Warp stall 38% -> 0.5%, Runtime 4.0 ms -> 1.3 ms).
  - Warp shuffle (`__shfl_down_sync` 5 butterfly steps: offsets 16, 8, 4, 2, 1),
    Read-only cache (`const __restrict__` Table 7-6: Load Efficiency 52% -> 97%,
    DRAM 600 -> 200 GB/s, L2 read 1,500 -> 1,800 GB/s, SM Active 45% -> 93%,
    Runtime 2.5 ms -> 1.0 ms), and TMA async prefetch (`cuda::memcpy_async`
    hiding 800-cycle DRAM latency, Table 7-7: Load Efficiency 23% -> 99%,
    Sectors/req 6.4 -> 4.0, DRAM 25% -> 90%, SM Active 62% -> 100%,
    Runtime 18.0 ms -> 7.0 ms).
"""

from __future__ import annotations

from typing import Dict, List


class MemoryPatternError(ValueError):
    """Raised when invalid memory access pattern or tile parameters are provided."""


ASP_CH7_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "TABLE_7_1_COALESCING": {
        "dram_pct_before": 25.0,
        "dram_pct_after": 90.0,
        "load_eff_pct_before": 23.0,
        "load_eff_pct_after": 99.0,
        "sectors_per_req_before": 8.0,
        "sectors_per_req_after": 4.0,
        "sm_active_pct_before": 62.0,
        "sm_active_pct_after": 99.0,
        "runtime_ms_before": 4.8,
        "runtime_ms_after": 1.3,
    },
    "TABLE_7_2_VECTORIZED": {
        "load_eff_pct_before": 28.0,
        "load_eff_pct_after": 97.0,
        "sectors_per_req_before": 31.8,
        "sectors_per_req_after": 4.0,
        "dram_pct_before": 25.0,
        "dram_pct_after": 90.0,
        "runtime_ms_before": 4.2,
        "runtime_ms_after": 1.2,
    },
    "TABLE_7_4_SHMEM_TILING": {
        "dram_pct_before": 90.0,
        "dram_pct_after": 25.0,
        "occupancy_pct_before": 42.0,
        "occupancy_pct_after": 89.0,
        "gflops_before": 15.0,
        "gflops_after": 170.0,
        "global_sectors_before": 9800.0,
        "global_sectors_after": 1200.0,
        "shmem_pct_before": 52.0,
        "shmem_pct_after": 99.0,
        "ai_flops_per_byte_before": 1.5,
        "ai_flops_per_byte_after": 8.0,
    },
    "TABLE_7_5_BANK_PADDING": {
        "bank_conflicts_millions_before": 4.8,
        "bank_conflicts_millions_after": 0.0,
        "shmem_pct_before": 52.0,
        "shmem_pct_after": 100.0,
        "warp_stall_pct_before": 38.0,
        "warp_stall_pct_after": 0.5,
        "runtime_ms_before": 4.0,
        "runtime_ms_after": 1.3,
    },
    "TABLE_7_6_READONLY_RESTRICT": {
        "load_eff_pct_before": 52.0,
        "load_eff_pct_after": 97.0,
        "dram_gbps_before": 600.0,
        "dram_gbps_after": 200.0,
        "l2_read_gbps_before": 1500.0,
        "l2_read_gbps_after": 1800.0,
        "sm_active_pct_before": 45.0,
        "sm_active_pct_after": 93.0,
        "runtime_ms_before": 2.5,
        "runtime_ms_after": 1.0,
    },
    "TABLE_7_7_TMA_PREFETCH": {
        "load_eff_pct_before": 23.0,
        "load_eff_pct_after": 99.0,
        "sectors_per_req_before": 6.4,
        "sectors_per_req_after": 4.0,
        "dram_pct_before": 25.0,
        "dram_pct_after": 90.0,
        "sm_active_pct_before": 62.0,
        "sm_active_pct_after": 100.0,
        "runtime_ms_before": 18.0,
        "runtime_ms_after": 7.0,
    },
}


def analyze_warp_global_memory_access(
    stride_elements: int = 1,
    bytes_per_element: int = 4,
    start_offset_bytes: int = 0,
    warp_size: int = 32,
) -> Dict[str, object]:
    """Calculate 32-byte sectors and 128-byte cache lines touched by a 32-thread warp load per ASP Ch 7 (pp. 216-226).

    Rules:
    - Each L1/L2 cache line is `128` bytes, divided into `4` sectors of `32` bytes each.
    - Useful bytes requested by the warp = `warp_size * bytes_per_element` (128 bytes for 32 x FP32).
    - When `stride_elements == 1` and `start_offset_bytes % 128 == 0`, all 32 threads fall inside
      1 cache line (`128` bytes = `4` sectors of `32` bytes -> `4.0` sectors/request, `100%` efficiency).
    - When `stride_elements == 1` but misaligned (e.g. `start_offset_bytes = 4`), the 128-byte span
      straddles two 128-byte cache lines and fetches `5` sectors (`160` bytes -> `80.0%` efficiency).
    - When `stride_elements == 2`, 32 threads span `256` bytes across `2` cache lines = `8` sectors
      (`256` bytes fetched for `128` useful bytes -> `50%` theoretical / `23%` measured in Table 7-1).
    - When `stride_elements >= 8` (every thread in a distinct 32B sector), the warp touches `32`
      sectors (`1,024` bytes fetched for `128` useful bytes -> `12.5%` efficiency).
    """
    if stride_elements <= 0 or bytes_per_element <= 0 or start_offset_bytes < 0 or warp_size <= 0:
        raise MemoryPatternError("Stride, element size, and warp size must be positive; offset non-negative")

    sectors_touched = set()
    cache_lines_touched = set()
    for lane in range(warp_size):
        addr = start_offset_bytes + lane * stride_elements * bytes_per_element
        for b in range(bytes_per_element):
            byte_addr = addr + b
            sectors_touched.add(byte_addr // 32)
            cache_lines_touched.add(byte_addr // 128)

    num_sectors = len(sectors_touched)
    num_lines = len(cache_lines_touched)
    useful_bytes = warp_size * bytes_per_element
    fetched_bytes = num_sectors * 32
    load_efficiency_pct = (useful_bytes / fetched_bytes) * 100.0

    return {
        "stride_elements": stride_elements,
        "bytes_per_element": bytes_per_element,
        "start_offset_bytes": start_offset_bytes,
        "useful_bytes": useful_bytes,
        "fetched_bytes": fetched_bytes,
        "sectors_per_request": float(num_sectors),
        "cache_lines_touched": num_lines,
        "theoretical_load_efficiency_pct": round(load_efficiency_pct, 2),
        "is_fully_coalesced": num_sectors == (useful_bytes // 32) and (start_offset_bytes % 128 == 0),
    }


def calc_vectorized_warp_load(
    vector_bytes_per_thread: int = 16,
    pointer_alignment_bytes: int = 256,
    warp_size: int = 32,
) -> Dict[str, object]:
    """Calculate warp-wide vectorized load geometry (`float4` 16B on Hopper vs `float8` 32B on Blackwell) per ASP Ch 7 (pp. 221-226).

    Rules:
    - `vector_bytes_per_thread` must be 4 (scalar `float`), 8 (`float2`), 16 (`float4`, `ld.global.v4.f32`),
      or 32 (`alignas(32) float8`, `ld.global.v8.f32` on Blackwell `sm_100` with CUDA 13+).
    - `cudaMalloc` guarantees at least `256`-byte base alignment.
    - If `pointer_alignment_bytes % vector_bytes_per_thread != 0`, vectorized load is invalid/forfeited.
    - Total bytes per warp instruction = `warp_size * vector_bytes_per_thread` (`512 B` for `float4` =
      `4` x 128B cache lines = `16` sectors; `1,024 B` for `float8` = `8` x 128B cache lines = `32` sectors),
      keeping `sectors_per_128b_transaction == 4.0`.
    """
    if vector_bytes_per_thread not in {4, 8, 16, 32}:
        raise MemoryPatternError(f"Unsupported vector_bytes_per_thread: {vector_bytes_per_thread}")
    if pointer_alignment_bytes <= 0 or warp_size <= 0:
        raise MemoryPatternError("Alignment and warp_size must be positive")

    aligned = (pointer_alignment_bytes % vector_bytes_per_thread) == 0
    floats_per_thread = vector_bytes_per_thread // 4
    warp_bytes = warp_size * vector_bytes_per_thread
    cache_lines_128b = warp_bytes // 128
    sectors_32b = warp_bytes // 32

    ptx_inst = {
        4: "ld.global.f32",
        8: "ld.global.v2.f32",
        16: "ld.global.v4.f32",
        32: "ld.global.v8.f32",
    }[vector_bytes_per_thread]

    return {
        "vector_bytes_per_thread": vector_bytes_per_thread,
        "floats_per_thread": floats_per_thread,
        "aligned": aligned,
        "ptx_instruction": ptx_inst if aligned else "MISALIGNED_FALLBACK_SCALAR",
        "warp_bytes_per_instruction": warp_bytes,
        "cache_lines_128b_per_warp": cache_lines_128b,
        "sectors_32b_per_warp": sectors_32b,
        "sectors_per_128b_transaction": 4.0 if aligned else 8.0,
        "scalar_instruction_reduction_x": float(floats_per_thread) if aligned else 1.0,
    }


def analyze_shared_memory_bank_conflicts(
    tile_cols: int = 32,
    pad_cols: int = 0,
    access_mode: str = "COLUMN_TRANSPOSE_READ",
    warp_size: int = 32,
) -> Dict[str, object]:
    """Calculate shared-memory bank conflicts for a 2D float tile `tile[32][tile_cols + pad_cols]` per ASP Ch 7 (pp. 233-238).

    Rules:
    - Shared memory has `32` banks, each `4` bytes wide (`bank = (float_index) % 32`).
    - Row stride in floats = `tile_cols + pad_cols`.
    - In `ROW_MAJOR_ACCESS` (`tile[constant_row][lane]`), lane `i` accesses `row * stride + i`, hitting
      bank `(row * stride + i) % 32` -> 32 distinct banks (`1`-way, `0` bank conflicts).
    - In `COLUMN_TRANSPOSE_READ` (`tile[lane][constant_col]`), lane `i` accesses `i * stride + col`,
      hitting bank `(i * stride + col) % 32`.
      - When `tile_cols = 32, pad_cols = 0` (`stride = 32` floats = `128` bytes), `(i * 32 + col) % 32 == col % 32`
        for all 32 lanes (all 32 threads hit the SAME bank at 32 DIFFERENT addresses -> **`32`-way bank conflict**).
      - When `tile_cols = 32, pad_cols = 1` (`stride = 33` floats), `(i * 33 + col) % 32 == (i + col) % 32`
        -> all 32 threads hit 32 distinct banks (**`1`-way, `0` bank conflicts**, with `1 / 32 = 3.125%` ~ `3%`
        memory overhead = `128` bytes out of `4,096` bytes).
    - In `UNIFORM_BROADCAST` (`tile[constant_row][constant_col]`), all 32 threads read the exact same address,
      which hardware broadcasts in `1` cycle (`0` bank conflicts).
    """
    if tile_cols <= 0 or pad_cols < 0 or warp_size <= 0:
        raise MemoryPatternError("Invalid tile dimensions")
    row_stride = tile_cols + pad_cols

    if access_mode == "UNIFORM_BROADCAST":
        return {
            "row_stride_floats": row_stride,
            "unique_banks_hit": 1,
            "max_ways_conflict": 1,
            "has_bank_conflict": False,
            "hardware_broadcast": True,
            "padding_overhead_pct": round((pad_cols / tile_cols) * 100.0, 2),
        }

    bank_hits: Dict[int, set[int]] = {}
    for lane in range(warp_size):
        if access_mode == "ROW_MAJOR_ACCESS":
            linear_idx = 0 * row_stride + lane
        elif access_mode == "COLUMN_TRANSPOSE_READ":
            linear_idx = lane * row_stride + 0
        else:
            raise MemoryPatternError(f"Unknown access_mode: {access_mode}")
        bank = linear_idx % 32
        bank_hits.setdefault(bank, set()).add(linear_idx)

    max_ways = max(len(addrs) for addrs in bank_hits.values())
    return {
        "row_stride_floats": row_stride,
        "unique_banks_hit": len(bank_hits),
        "max_ways_conflict": max_ways,
        "has_bank_conflict": max_ways > 1,
        "hardware_broadcast": False,
        "padding_overhead_pct": round((pad_cols / tile_cols) * 100.0, 2),
    }


def calc_tile_residency_and_register_budget(
    tile_dim: int = 64,
    threads_per_block: int = 1024,
    regs_per_thread: int = 12,
    sm_max_regs: int = 65536,
    sm_max_threads: int = 2048,
    sm_max_blocks: int = 32,
    sm_usable_smem_bytes: int = 227 * 1024,
) -> Dict[str, int]:
    """Calculate shared-memory and register residency limits for tiled GEMM per ASP Ch 7 (pp. 231-232).

    Worked example in ASP Ch 7 (pp. 231-232):
    - `tile_dim = 64` (`64 x 64` FP32 tile = `16,384` bytes = `16 KB` per matrix tile, `32 KB` for A+B).
    - `threads_per_block = 1024` (`32 x 32` block, each thread computes a `2 x 2` subtile = 4 outputs).
    - Case 1 (`regs_per_thread = 12`): `12 * 1,024 = 12,288` regs/block. Register file (`65,536` regs) could
      fit `65,536 // 12,288 = 5` blocks (`61,440` regs), but SM thread limit (`2,048` threads) caps residency
      at `2,048 // 1,024 = 2` blocks (`2,048` threads).
    - Case 2 (`regs_per_thread = 22`): `22 * 1,024 = 22,528` regs/block. Register file fits `65,536 // 22,528 = 2`
      blocks (`45,056` regs), matching the `2`-block (`2,048`-thread) SM ceiling.
    """
    if tile_dim <= 0 or threads_per_block <= 0 or regs_per_thread <= 0 or regs_per_thread > 255:
        raise MemoryPatternError("Invalid tile or register parameters")

    bytes_per_matrix_tile = tile_dim * tile_dim * 4
    shmem_per_block_ab = 2 * bytes_per_matrix_tile
    regs_per_block = threads_per_block * regs_per_thread

    blocks_by_regs = sm_max_regs // regs_per_block
    blocks_by_threads = sm_max_threads // threads_per_block
    blocks_by_smem = sm_usable_smem_bytes // shmem_per_block_ab
    active_blocks = min(blocks_by_regs, blocks_by_threads, blocks_by_smem, sm_max_blocks)

    return {
        "tile_dim": tile_dim,
        "bytes_per_matrix_tile": bytes_per_matrix_tile,
        "shmem_per_block_ab_bytes": shmem_per_block_ab,
        "regs_per_block": regs_per_block,
        "blocks_limited_by_regs": blocks_by_regs,
        "blocks_limited_by_threads": blocks_by_threads,
        "blocks_limited_by_smem": blocks_by_smem,
        "resident_blocks_per_sm": active_blocks,
        "resident_threads_per_sm": active_blocks * threads_per_block,
    }


def simulate_warp_shuffle_down_reduction(values: List[float]) -> Dict[str, object]:
    """Simulate a 32-lane `__shfl_down_sync` butterfly reduction per ASP Ch 7 (pp. 239-240)."""
    if len(values) != 32:
        raise MemoryPatternError("Warp shuffle reduction requires exactly 32 lane values")

    lanes = list(values)
    offsets = [16, 8, 4, 2, 1]
    for offset in offsets:
        next_lanes = list(lanes)
        for i in range(32):
            if i + offset < 32:
                next_lanes[i] = lanes[i] + lanes[i + offset]
        lanes = next_lanes

    return {
        "steps": len(offsets),
        "offsets": offsets,
        "lane0_sum": round(lanes[0], 6),
        "expected_sum": round(sum(values), 6),
        "shared_memory_bytes_used": 0,
        "bank_conflicts": 0,
    }
