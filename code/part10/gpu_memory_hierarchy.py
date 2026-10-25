#!/usr/bin/env python3
"""Chapter 10.3 model: The GPU Memory Hierarchy.

Encodes the verifiable specs, latency/bandwidth formulas, shared-memory bank
mapping, coalescing/vectorization sector rules, and host-device memory checks from:
- AI Systems Performance Engineering (ASP) Chapter 6 (pp. 193-201, Table 6-5)
  and Chapter 7 (pp. 216-253, Tables 7-1, 7-4, 7-5, 7-6, 7-7):
  Blackwell 7-tier memory hierarchy (Registers, Shared/L1, TMEM, Constant Cache,
  L2 126 MB, Local Memory, Global HBM3e), Points of Coherency, `cudaMallocAsync`
  pools, Unified Memory (`cudaMallocManaged`, `cudaMemPrefetchAsync`,
  `cudaMemAdvise`), 128-byte cache lines / four 32-byte sectors, `float4` (16B)
  vs Blackwell 32B vector loads, Shared Memory 32-bank conflict math and `[32][33]`
  padding, `__shfl_down_sync` butterfly reduction, `const __restrict__` read-only
  cache, and `TMA` (`cuda::memcpy_async`) double-buffering.
- nvidia-devops Volume 02 (Chapters 5, 7, 8, 9; Lab 3) & Volume 04 Chapter 1:
  13B FP16 capacity vs decode weight-read latency floor (`26 GB / 3,350 GB/s`),
  worked register spill traffic calculation (`65,536 threads * 8B * 2`),
  worked bandwidth utilization check (`16 GB / 6 ms`), and PCIe `BAR1` /
  Resizable BAR (`ReBAR`) validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


class MemoryHierarchyError(ValueError):
    """Raised when invalid memory hierarchy or access parameters are given."""


# 1. Blackwell B200 7-tier memory hierarchy specifications (ASP Ch 6 Table 6-5, p. 195)
@dataclass(frozen=True)
class MemoryTierSpec:
    name: str
    scope: str
    capacity_desc: str
    latency_cycles_approx: str
    backed_by: str
    directly_pointer_addressable: bool


BLACKWELL_MEMORY_TIERS: Dict[str, MemoryTierSpec] = {
    "registers": MemoryTierSpec(
        name="Registers",
        scope="thread",
        capacity_desc="64K 32-bit registers per SM (256 KB total; max 255 per thread)",
        latency_cycles_approx="~1 cycle",
        backed_by="On-SM SRAM register file",
        directly_pointer_addressable=False,
    ),
    "shared_l1": MemoryTierSpec(
        name="Shared Memory & L1 Data Cache",
        scope="thread_block / sm",
        capacity_desc="256 KB combined SRAM per SM (up to 228 KB shared/SM; 227 KB dynamic/block + 1 KB CUDA reserved)",
        latency_cycles_approx="~20-30 cycles",
        backed_by="On-SM 32-bank SRAM",
        directly_pointer_addressable=True,
    ),
    "tmem": MemoryTierSpec(
        name="Tensor Memory (TMEM)",
        scope="sm_tensor_cores",
        capacity_desc="256 KB dedicated SRAM per SM for 5th-gen Tensor Cores (tcgen05 / UMMA)",
        latency_cycles_approx="~10 cycles",
        backed_by="Dedicated on-SM Tensor Core SRAM (managed via TMA & tcgen05 descriptors)",
        directly_pointer_addressable=False,
    ),
    "constant_cache": MemoryTierSpec(
        name="Constant Memory Cache",
        scope="sm_read_only_broadcast",
        capacity_desc="~8 KB cache per SM fronting 64 KB __constant__ space",
        latency_cycles_approx="~1 cycle (warp-uniform broadcast)",
        backed_by="On-SM constant cache fronting device memory",
        directly_pointer_addressable=True,
    ),
    "l2_cache": MemoryTierSpec(
        name="L2 Cache",
        scope="device",
        capacity_desc="126 MB GPU-wide on Blackwell B200 (50 MB on Hopper H100)",
        latency_cycles_approx="~200 cycles",
        backed_by="On-die shared SRAM hub across all SMs and HBM controllers",
        directly_pointer_addressable=False,
    ),
    "local_memory": MemoryTierSpec(
        name="Local Memory (Spill Space)",
        scope="thread",
        capacity_desc="Per-thread logical space for register spills and dynamic per-thread arrays",
        latency_cycles_approx="100s to 1,000+ cycles (when missing L1/L2)",
        backed_by="Off-chip HBM DRAM (cached via L1/L2)",
        directly_pointer_addressable=True,
    ),
    "global_hbm": MemoryTierSpec(
        name="Global Memory (HBM3 / HBM3e)",
        scope="device / system",
        capacity_desc="Up to 180-192 GB HBM3e on B200 (~288 GB on B300) at ~8 TB/s across 8 stacks (2 dies @ 10 TB/s link)",
        latency_cycles_approx="100s to 1,000+ cycles (~800 cycles typical round trip)",
        backed_by="Off-chip 3D-stacked HBM on silicon interposer",
        directly_pointer_addressable=True,
    ),
}

POINTS_OF_COHERENCY: List[str] = [
    "thread",
    "thread_block_cta",
    "thread_block_cluster",
    "device",
    "system",
]

# 2. Before/After Optimization Benchmark Tables (ASP Ch 7 Tables 7-1, 7-4, 7-5, 7-6, 7-7)
ASP_CH7_BENCHMARKS: Dict[str, Dict[str, float]] = {
    "table_7_1_coalescing": {
        "uncoalesced_dram_pct": 25.0,
        "coalesced_dram_pct": 90.0,
        "uncoalesced_load_eff_pct": 23.0,
        "coalesced_load_eff_pct": 99.0,
        "uncoalesced_sectors_per_req": 8.0,
        "coalesced_sectors_per_req": 4.0,
        "uncoalesced_time_ms": 4.8,
        "coalesced_time_ms": 1.3,
    },
    "table_7_4_shared_mem_tiling": {
        "naive_dram_pct": 90.0,
        "tiled_dram_pct": 25.0,
        "naive_occupancy_pct": 42.0,
        "tiled_occupancy_pct": 89.0,
        "naive_gflops": 15.0,
        "tiled_gflops": 170.0,
        "naive_global_sectors": 9800.0,
        "tiled_global_sectors": 1200.0,
        "naive_arith_intensity": 1.5,
        "tiled_arith_intensity": 8.0,
    },
    "table_7_5_bank_conflict_padding": {
        "unpadded_bank_conflicts": 4_800_000.0,
        "padded_bank_conflicts": 0.0,
        "unpadded_smem_util_pct": 52.0,
        "padded_smem_util_pct": 100.0,
        "unpadded_stall_pct": 38.0,
        "padded_stall_pct": 0.5,
        "unpadded_time_ms": 4.0,
        "padded_time_ms": 1.3,
    },
    "table_7_6_readonly_restrict": {
        "before_load_eff_pct": 52.0,
        "after_load_eff_pct": 97.0,
        "before_dram_gbps": 600.0,
        "after_dram_gbps": 200.0,
        "before_l2_read_gbps": 1500.0,
        "after_l2_read_gbps": 1800.0,
        "before_sm_active_pct": 45.0,
        "after_sm_active_pct": 93.0,
        "before_time_ms": 2.5,
        "after_time_ms": 1.0,
    },
    "table_7_7_tma_async_prefetch": {
        "before_load_eff_pct": 23.0,
        "after_load_eff_pct": 99.0,
        "before_sectors_per_req": 6.4,
        "after_sectors_per_req": 4.0,
        "before_dram_pct": 25.0,
        "after_dram_pct": 90.0,
        "before_sm_active_pct": 62.0,
        "after_sm_active_pct": 100.0,
        "before_time_ms": 18.0,
        "after_time_ms": 7.0,
    },
}


def evaluate_capacity_vs_decode_floor(
    num_params_billions: float,
    bytes_per_param: float,
    gpu_hbm_capacity_gb: float,
    gpu_peak_bw_gbps: float,
) -> Dict[str, object]:
    """Evaluate weight capacity fit vs unbatched decode weight-read latency floor (V2 Ch 5).

    Worked example in V2 Ch 5:
    - 13B model in FP16 (2 bytes) = 26.0 GB of weights (fits inside 80 GB H100 with 54 GB spare).
    - At 3,350 GB/s (3.35 TB/s) peak HBM bandwidth, reading 26 GB per token sets a
      theoretical minimum latency floor of 26 / 3,350 = 0.007761 s ≈ 7.76 ms/token (~7.8 ms).
    """
    if (
        num_params_billions <= 0
        or bytes_per_param <= 0
        or gpu_hbm_capacity_gb <= 0
        or gpu_peak_bw_gbps <= 0
    ):
        raise MemoryHierarchyError("All capacity and bandwidth inputs must be positive")

    weight_gb = round(num_params_billions * bytes_per_param, 2)
    fits_in_vram = weight_gb <= gpu_hbm_capacity_gb
    free_vram_gb = round(gpu_hbm_capacity_gb - weight_gb, 2)
    min_token_latency_ms = round((weight_gb / gpu_peak_bw_gbps) * 1000.0, 2)

    return {
        "weight_gb": weight_gb,
        "fits_in_vram": fits_in_vram,
        "free_vram_gb": free_vram_gb,
        "min_token_latency_ms": min_token_latency_ms,
    }


def calc_register_spill_traffic(
    spilled_bytes_per_thread: int,
    threads_per_block: int,
    num_blocks: int,
) -> Dict[str, float]:
    """Calculate uncached register spill traffic per launch per nvidia-devops V2 Ch 7.

    Worked example in V2 Ch 7:
    - 2 float values (8 bytes) spilled per thread across 65,536 threads (256 * 256).
    - Each spilled value incurs 1 store + 1 load = 2 transactions:
      65,536 * 8 * 2 = 1,048,576 bytes (1.0 MiB, or ~1.05 MB decimal) of extra traffic.
    """
    if spilled_bytes_per_thread < 0 or threads_per_block <= 0 or num_blocks <= 0:
        raise MemoryHierarchyError("Invalid spill calculation parameters")
    total_threads = threads_per_block * num_blocks
    total_bytes = total_threads * spilled_bytes_per_thread * 2
    return {
        "total_threads": total_threads,
        "total_spill_bytes": total_bytes,
        "total_spill_mb_decimal": round(total_bytes / 1_000_000.0, 2),
        "total_spill_mib": round(total_bytes / (1024.0 * 1024.0), 2),
    }


def calc_effective_bandwidth_utilization(
    bytes_read_gb: float,
    bytes_written_gb: float,
    elapsed_ms: float,
    peak_bw_gbps: float = 3350.0,
) -> Dict[str, float]:
    """Calculate effective memory bandwidth and % of peak per nvidia-devops V2 Ch 8.

    Worked example in V2 Ch 8:
    - 8 GB read + 8 GB written = 16 GB in 6 ms (0.006 s) on H100 (3,350 GB/s peak)
    - Achieved = 16 / 0.006 = 2,666.67 GB/s -> 79.6% (~80%) of peak.
    """
    if bytes_read_gb < 0 or bytes_written_gb < 0 or elapsed_ms <= 0 or peak_bw_gbps <= 0:
        raise MemoryHierarchyError("Invalid bandwidth utilization parameters")
    total_gb = bytes_read_gb + bytes_written_gb
    achieved_gbps = total_gb / (elapsed_ms / 1000.0)
    pct_of_peak = (achieved_gbps / peak_bw_gbps) * 100.0
    return {
        "total_gb": round(total_gb, 2),
        "achieved_gbps": round(achieved_gbps, 1),
        "pct_of_peak": round(pct_of_peak, 1),
    }


def calc_warp_coalescing_and_vector_loads(
    bytes_per_thread: int = 4,
    stride_elements: int = 1,
    base_offset_bytes: int = 0,
    all_threads_same_address: bool = False,
) -> Dict[str, object]:
    """Model 128-byte cache-line & 32-byte sector transactions for a 32-thread warp (ASP Ch 7 pp. 217-226).

    Rules from ASP Ch 7:
    - Cache line = 128 bytes = 4 sectors of 32 bytes.
    - Aligned contiguous 4B scalar load (`bytes_per_thread=4, stride=1, offset=0`):
      128 B total -> 1 cache line, 4 sectors, 100% load efficiency.
    - Misaligned contiguous 4B load (`offset=4`, i.e., shifted by 1 float / non-32B-aligned):
      128 B (`bytes 4..131`) spans 2 cache lines and touches 5 sectors (`sectors 0..4` = 160 B fetched for 128 B used = 80% efficiency).
    - Strided 4B load (`stride=2`, `offset=0`):
      32 threads span 256 B taking every even 4B word -> touches all 8 sectors across 2 lines (50% efficiency).
    - Vectorized `float4` (`bytes_per_thread=16, stride=1, offset=0`):
      512 B per warp -> 4 cache lines (16 sectors), 4.0 sectors per 128B transaction, 4x fewer instructions.
    - Vectorized Blackwell 256-bit (`bytes_per_thread=32, stride=1, offset=0`):
      1,024 B per warp -> 8 cache lines (32 sectors), 4.0 sectors per 128B transaction, 8x fewer instructions.
    """
    if bytes_per_thread not in (4, 8, 16, 32):
        raise MemoryHierarchyError("bytes_per_thread must be 4, 8, 16, or 32")
    if stride_elements <= 0 or base_offset_bytes < 0:
        raise MemoryHierarchyError("stride_elements must be > 0 and base_offset_bytes >= 0")

    warp_size = 32
    if all_threads_same_address:
        return {
            "useful_bytes": bytes_per_thread,
            "unique_32b_sectors": 1,
            "unique_128b_lines": 1,
            "load_efficiency_pct": round((bytes_per_thread / 32.0) * 100.0, 1),
            "broadcast": True,
        }

    sectors_touched = set()
    lines_touched = set()
    for lane in range(warp_size):
        start_byte = base_offset_bytes + (lane * stride_elements * bytes_per_thread)
        for b in range(start_byte, start_byte + bytes_per_thread):
            sectors_touched.add(b // 32)
            lines_touched.add(b // 128)

    useful_bytes = warp_size * bytes_per_thread
    fetched_bytes = len(sectors_touched) * 32
    efficiency_pct = round((useful_bytes / fetched_bytes) * 100.0, 1)

    return {
        "useful_bytes": useful_bytes,
        "fetched_bytes": fetched_bytes,
        "unique_32b_sectors": len(sectors_touched),
        "unique_128b_lines": len(lines_touched),
        "load_efficiency_pct": efficiency_pct,
        "broadcast": False,
    }


def calc_shared_mem_bank_conflict(
    stride_words_4b: int,
    all_threads_same_word: bool = False,
) -> Dict[str, object]:
    """Calculate shared-memory 32-bank conflict degree for a 32-thread warp (ASP Ch 7 pp. 235-241).

    Rules from ASP Ch 7:
    - Shared memory has 32 banks of 4-byte width (`bank = word_index % 32`).
    - If all 32 threads access the exact same 4-byte word (`all_threads_same_word=True` or `stride == 0`),
      hardware broadcasts/multicasts the word in 1 cycle (`conflict_way = 1`, `broadcast = True`).
    - Otherwise, thread `t` (for `t in 0..31`) accesses word `t * stride_words_4b` in bank
      `(t * stride_words_4b) % 32`.
    - For `stride = 1` (row-major) or `stride = 33` (padded `tile[32][33]` column access):
      all 32 threads hit 32 distinct banks (`conflict_way = 1`, conflict-free!).
    - For `stride = 32` (unpadded `tile[32][32]` column access):
      all 32 threads hit bank 0 (`conflict_way = 32`, 32-way bank conflict!).
    """
    if stride_words_4b < 0:
        raise MemoryHierarchyError("stride_words_4b cannot be negative")
    if all_threads_same_word or stride_words_4b == 0:
        return {
            "unique_banks_touched": 1,
            "conflict_way": 1,
            "is_conflict_free": True,
            "broadcast": True,
        }

    bank_counts: Dict[int, int] = {}
    for lane in range(32):
        word_idx = lane * stride_words_4b
        bank = word_idx % 32
        bank_counts[bank] = bank_counts.get(bank, 0) + 1

    max_way = max(bank_counts.values())
    return {
        "unique_banks_touched": len(bank_counts),
        "conflict_way": max_way,
        "is_conflict_free": max_way == 1,
        "broadcast": False,
    }


def audit_host_device_memory_config(
    vram_total_mib: int,
    bar1_total_mib: int,
    uses_pinned_host_memory: bool,
    uses_stream_ordered_async_alloc: bool,
    uses_unified_memory: bool = False,
    unified_memory_prefetched: bool = False,
) -> Dict[str, object]:
    """Audit host-device memory configuration per VL4 Ch 1 (§3.3-3.4) and ASP Ch 6 (pp. 193-201).

    Note: Combining the BAR1 Resizable BAR check (`bar1_total_mib == 256` vs full VRAM),
    pinned DMA memory check, `cudaMallocAsync` pool check, and `cudaMemPrefetchAsync`
    Unified Memory check into one readiness validator is an authoring synthesis ("my inference").
    """
    if vram_total_mib <= 0 or bar1_total_mib <= 0:
        raise MemoryHierarchyError("vram_total_mib and bar1_total_mib must be positive")

    issues: List[str] = []
    rebar_enabled = bar1_total_mib >= vram_total_mib
    if not rebar_enabled:
        issues.append(
            f"Resizable BAR (Large BAR1) disabled: BAR1 is {bar1_total_mib} MiB for {vram_total_mib} MiB VRAM"
        )
    if not uses_pinned_host_memory:
        issues.append(
            "Pageable host memory in use: DMA transfers will bounce through temporary CPU staging buffers and cannot overlap with compute"
        )
    if not uses_stream_ordered_async_alloc:
        issues.append(
            "Synchronous cudaMalloc/cudaFree in loop: use cudaMallocAsync/cudaFreeAsync or PyTorch caching allocator pool"
        )
    if uses_unified_memory and not unified_memory_prefetched:
        issues.append(
            "Unprefetched Unified Memory (cudaMallocManaged): demand page-fault stalls will occur without cudaMemPrefetchAsync / cudaMemAdvise"
        )

    return {
        "rebar_enabled": rebar_enabled,
        "healthy": len(issues) == 0,
        "issues": issues,
    }
