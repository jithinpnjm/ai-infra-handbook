#!/usr/bin/env python3
"""Chapter 10.2 model: The Execution Model — Threads, Warps, Blocks, and SMs.

Encodes the verifiable hardware limits, occupancy formulas, launch sizing,
tile decomposition, and efficiency gate checks from:
- AI Systems Performance Engineering (ASP) Chapter 6 (pp. 179-215):
  Blackwell SM 4-scheduler dual-issue limits (Table 6-1), thread/block/SM/grid
  limits (Tables 6-2, 6-3, 6-4, 6-5), 1D/2D/3D launch configuration and
  bounds-check semantics (`if (idx < N)` vs `cudaErrorIllegalAddress`),
  sequential vs parallel benchmark numbers (Table 6-6), `__launch_bounds__`
  register/residency clamping, and NVIDIA Compute Sanitizer tools.
- Parallel and High Performance Computing (PHPC) Chapter 10 (Sections 10.1-10.2):
  OpenCL/CUDA/HIP/AMD/CPU programming abstraction terminology (Table 10.1),
  NVIDIA Volta/Ampere vs AMD MI50 scheduler limits (Table 10.2), and 1D/2D/3D
  domain tile decomposition (Table 10.3).
- nvidia-devops Volume 02 (Chapters 2, 3, 6, 9; Labs 2, 3) & Volume 04 Ch 1:
  H100 SM anatomy, worked register/shared-memory occupancy calculation,
  5 warp states, and the two Nsight Compute efficiency gates
  (active-lane efficiency & sectors-per-request byte amplification).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Tuple


class ExecutionModelError(ValueError):
    """Raised when invalid kernel launch or SM resource parameters are given."""


# 1. SM Warp Scheduler & Dual-Issue limits per clock cycle (ASP Ch 6 Table 6-1, p. 181)
BLACKWELL_SM_ISSUE_LIMITS: Dict[str, int] = {
    "num_schedulers": 4,
    "max_warps_issued_per_cycle": 4,
    "max_math_ops_issued_per_cycle": 4,
    "max_mem_ops_issued_per_cycle": 4,
    "ld_st_units_per_scheduler": 4,
    "total_ld_st_units_per_sm": 16,
}

# 2. Hardware limits for Hopper H100 and Blackwell B200 (ASP Ch 6 Tables 6-2, 6-3, 6-4, 6-5; V2 Ch 2)
@dataclass(frozen=True)
class GpuExecutionLimits:
    arch: str
    warp_size: int
    max_threads_per_block: int
    max_warps_per_block: int
    max_resident_warps_per_sm: int
    max_resident_threads_per_sm: int
    max_active_blocks_per_sm: int
    registers_per_sm: int
    max_registers_per_thread: int
    l1_smem_total_kb_per_sm: int
    max_shared_mem_kb_per_sm: int
    max_dynamic_shared_mem_kb_per_block: int
    cuda_reserved_shared_mem_kb_per_block: int
    l2_cache_mb: int
    max_grid_dim_x: int
    max_grid_dim_y: int
    max_grid_dim_z: int
    max_concurrent_grids: int


ARCH_LIMITS: Dict[str, GpuExecutionLimits] = {
    "H100": GpuExecutionLimits(
        arch="Hopper H100 SXM5",
        warp_size=32,
        max_threads_per_block=1024,
        max_warps_per_block=32,
        max_resident_warps_per_sm=64,
        max_resident_threads_per_sm=2048,
        max_active_blocks_per_sm=32,
        registers_per_sm=65536,
        max_registers_per_thread=255,
        l1_smem_total_kb_per_sm=256,
        max_shared_mem_kb_per_sm=228,
        max_dynamic_shared_mem_kb_per_block=227,
        cuda_reserved_shared_mem_kb_per_block=1,
        l2_cache_mb=50,
        max_grid_dim_x=2_147_483_647,
        max_grid_dim_y=65_535,
        max_grid_dim_z=65_535,
        max_concurrent_grids=128,
    ),
    "B200": GpuExecutionLimits(
        arch="Blackwell B200",
        warp_size=32,
        max_threads_per_block=1024,
        max_warps_per_block=32,
        max_resident_warps_per_sm=64,
        max_resident_threads_per_sm=2048,
        max_active_blocks_per_sm=32,
        registers_per_sm=65536,
        max_registers_per_thread=255,
        l1_smem_total_kb_per_sm=256,
        max_shared_mem_kb_per_sm=228,
        max_dynamic_shared_mem_kb_per_block=227,
        cuda_reserved_shared_mem_kb_per_block=1,
        l2_cache_mb=126,
        max_grid_dim_x=2_147_483_647,
        max_grid_dim_y=65_535,
        max_grid_dim_z=65_535,
        max_concurrent_grids=128,
    ),
}

# 3. Programming abstraction terminology (PHPC Ch 10 Table 10.1 & Table 10.2)
PROGRAMMING_ABSTRACTIONS: Dict[str, Dict[str, str]] = {
    "domain": {
        "opencl": "NDRange (N-dimensional range)",
        "cuda": "grid",
        "hip": "grid",
        "amd_hc": "extent",
        "cpp_amp": "extent",
        "cpu": "Standard loop bounds / index sets",
    },
    "group": {
        "opencl": "Work Group",
        "cuda": "block or thread block (CTA)",
        "hip": "block",
        "amd_hc": "tile",
        "cpp_amp": "tile",
        "cpu": "loop block",
    },
    "subgroup": {
        "opencl": "Subgroup or Wavefront",
        "cuda": "warp (32)",
        "hip": "warp",
        "amd_hc": "wavefront (64)",
        "cpp_amp": "N/A",
        "cpu": "SIMD length",
    },
    "item": {
        "opencl": "Work Item",
        "cuda": "thread",
        "hip": "thread",
        "amd_hc": "thread",
        "cpp_amp": "thread",
        "cpu": "thread",
    },
}

SCHEDULER_COMPARISON: Dict[str, Dict[str, int]] = {
    "NVIDIA_Volta_Ampere_Hopper_Blackwell": {
        "active_subgroups_per_cu": 64,
        "active_work_groups_per_cu": 32,
        "selected_subgroups_per_cu": 4,
        "subgroup_size": 32,
    },
    "AMD_MI50": {
        "active_subgroups_per_cu": 40,
        "active_work_groups_per_cu": 40,
        "selected_subgroups_per_cu": 4,
        "subgroup_size": 64,
    },
}

# 4. Sequential vs Parallel CUDA add benchmark (ASP Ch 6 Table 6-6, p. 204)
SEQ_VS_PAR_BENCHMARK: Dict[str, Dict[str, float]] = {
    "add_sequential": {
        "exec_time_ms": 48.21,
        "gpu_util_pct": 1.5,
        "achieved_occupancy_pct": 1.3,
        "warp_exec_efficiency_pct": 3.1,
    },
    "add_parallel": {
        "exec_time_ms": 2.17,
        "gpu_util_pct": 95.0,
        "achieved_occupancy_pct": 38.7,
        "warp_exec_efficiency_pct": 100.0,
    },
}

COMPUTE_SANITIZER_TOOLS: Dict[str, str] = {
    "memcheck": "Detects out-of-bounds/misaligned global, local, and shared memory accesses, hardware exceptions, and device heap leaks",
    "racecheck": "Reports shared-memory RAW, WAR, and WAW data hazards across threads",
    "initcheck": "Flags reads from uninitialized device global memory buffers",
    "synccheck": "Detects invalid barrier synchronization (__syncthreads / cooperative groups) and divergent barrier deadlocks",
}


def calc_grid_launch_1d(
    num_elements: int,
    threads_per_block: int = 256,
    min_grid_size: int = 0,
) -> Dict[str, int]:
    """Calculate 1D kernel launch geometry and tail-warp bounds behavior per ASP Ch 6 (pp. 188-191, 207).

    Reproduces:
    - `blocksPerGrid = max(minGridSize, (N + threadsPerBlock - 1) // threadsPerBlock)`
    - For N = 1,000,000 and threadsPerBlock = 256 -> 3,907 blocks (999,936 + 256 = 1,000,192 threads).
    - For N = 63 and threadsPerBlock = 64 (2 warps) -> 1 out-of-bounds lane (`idx == 63`) that must be
      guarded by `if (idx < N)` to avoid `cudaErrorIllegalAddress`.
    """
    if num_elements <= 0 or threads_per_block <= 0 or threads_per_block > 1024:
        raise ExecutionModelError("num_elements must be > 0 and 1 <= threads_per_block <= 1024")
    if min_grid_size < 0:
        raise ExecutionModelError("min_grid_size cannot be negative")

    blocks_for_n = (num_elements + threads_per_block - 1) // threads_per_block
    blocks_per_grid = max(min_grid_size, blocks_for_n)
    total_threads_launched = blocks_per_grid * threads_per_block
    warps_per_block = math.ceil(threads_per_block / 32)
    total_warps_launched = blocks_per_grid * warps_per_block
    out_of_bounds_threads = max(0, total_threads_launched - num_elements)

    return {
        "blocks_for_n": blocks_for_n,
        "blocks_per_grid": blocks_per_grid,
        "threads_per_block": threads_per_block,
        "warps_per_block": warps_per_block,
        "total_threads_launched": total_threads_launched,
        "total_warps_launched": total_warps_launched,
        "out_of_bounds_threads": out_of_bounds_threads,
    }


def calc_domain_tile_decomposition(
    global_dims: Tuple[int, ...],
    tile_dims: Tuple[int, ...],
) -> Dict[str, object]:
    """Calculate 1D/2D/3D domain tile decomposition per PHPC Ch 10 Section 10.1.4 Table 10.3 (p. 320)."""
    if len(global_dims) != len(tile_dims) or not (1 <= len(global_dims) <= 3):
        raise ExecutionModelError("global_dims and tile_dims must have matching 1D, 2D, or 3D length")
    for g, t in zip(global_dims, tile_dims):
        if g <= 0 or t <= 0:
            raise ExecutionModelError("All domain and tile dimensions must be positive")

    tile_size = 1
    num_tiles_per_dim = []
    total_work_groups = 1
    for g, t in zip(global_dims, tile_dims):
        tile_size *= t
        nt = (g + t - 1) // t
        num_tiles_per_dim.append(nt)
        total_work_groups *= nt

    return {
        "dimensions": len(global_dims),
        "tile_size": tile_size,
        "num_tiles_per_dim": tuple(num_tiles_per_dim),
        "total_work_groups": total_work_groups,
    }


def calc_sm_occupancy(
    threads_per_block: int,
    registers_per_thread: int,
    shared_mem_bytes_per_block: int = 0,
    arch: str = "B200",
) -> Dict[str, object]:
    """Calculate theoretical SM block/warp residency and limiting factor.

    Combines the hardware limits from ASP Ch 6 Tables 6-2 & 6-3 with the
    worked register & shared-memory residency method from nvidia-devops V2 Ch 6:
    - Example 1 (V2 Ch 6): 256 threads/block (8 warps), 40 regs/thread, 0 smem
      -> floor(65536 / 40) = 1,638 max threads by registers
      -> floor(1638 / 256) = 6 resident blocks = 48 resident warps = 75.0% occupancy.
    - Example 2 (V2 Ch 6): 256 threads/block (8 warps), 56 regs/thread, 0 smem
      -> floor(65536 / 56) = 1,170 max threads by registers
      -> floor(1170 / 256) = 4 resident blocks = 32 resident warps = 50.0% occupancy.
    Note: Unifying thread/block/warp/register/shared-memory caps into a single
    Python calculator is an authoring synthesis ("my inference").
    """
    if arch not in ARCH_LIMITS:
        raise ExecutionModelError(f"Unsupported architecture: {arch}")
    lim = ARCH_LIMITS[arch]

    if threads_per_block <= 0 or threads_per_block > lim.max_threads_per_block:
        raise ExecutionModelError(
            f"threads_per_block ({threads_per_block}) must be in 1..{lim.max_threads_per_block}"
        )
    if registers_per_thread <= 0:
        raise ExecutionModelError("registers_per_thread must be positive")
    if shared_mem_bytes_per_block < 0:
        raise ExecutionModelError("shared_mem_bytes_per_block cannot be negative")

    max_dyn_smem_bytes = lim.max_dynamic_shared_mem_kb_per_block * 1024
    max_sm_smem_bytes = lim.max_shared_mem_kb_per_sm * 1024

    if registers_per_thread > lim.max_registers_per_thread:
        return {
            "resident_blocks": 0,
            "resident_warps": 0,
            "occupancy_pct": 0.0,
            "limiting_resource": "REGISTER_SPILL_EXCEEDS_255_PER_THREAD",
        }
    if shared_mem_bytes_per_block > max_dyn_smem_bytes:
        return {
            "resident_blocks": 0,
            "resident_warps": 0,
            "occupancy_pct": 0.0,
            "limiting_resource": "SHARED_MEM_EXCEEDS_227KB_BLOCK_LIMIT",
        }

    warps_per_block = math.ceil(threads_per_block / lim.warp_size)

    # 1. Block-slot and thread/warp limits per SM
    blocks_by_slot_limit = lim.max_active_blocks_per_sm
    blocks_by_warp_limit = lim.max_resident_warps_per_sm // warps_per_block
    blocks_by_thread_limit = lim.max_resident_threads_per_sm // threads_per_block

    # 2. Register limit per SM (using the V2 Ch 6 worked calculation: floor(65536 / regs_per_thread) // threads_per_block)
    max_threads_by_regs = lim.registers_per_sm // registers_per_thread
    blocks_by_regs = max_threads_by_regs // threads_per_block

    # 3. Shared memory limit per SM (remembering 1 KB CUDA reserved per block when dynamic shared memory is used)
    if shared_mem_bytes_per_block == 0:
        blocks_by_smem = lim.max_active_blocks_per_sm
    else:
        effective_smem_per_block = shared_mem_bytes_per_block + (
            lim.cuda_reserved_shared_mem_kb_per_block * 1024
        )
        blocks_by_smem = max_sm_smem_bytes // effective_smem_per_block

    caps = {
        "WARP_OR_THREAD_SLOTS": min(blocks_by_slot_limit, blocks_by_warp_limit, blocks_by_thread_limit),
        "REGISTERS": blocks_by_regs,
        "SHARED_MEMORY": blocks_by_smem,
    }
    resident_blocks = min(caps.values())
    resident_warps = resident_blocks * warps_per_block
    occupancy_pct = round((resident_warps / lim.max_resident_warps_per_sm) * 100.0, 2)

    limiting = [name for name, val in caps.items() if val == resident_blocks]
    return {
        "warps_per_block": warps_per_block,
        "resident_blocks": resident_blocks,
        "resident_warps": resident_warps,
        "resident_threads": resident_blocks * threads_per_block,
        "occupancy_pct": occupancy_pct,
        "limiting_resource": limiting[0],
        "caps": caps,
    }


def validate_launch_bounds(
    max_threads_per_block: int,
    min_blocks_per_sm: int,
    arch: str = "B200",
) -> Dict[str, object]:
    """Validate `__launch_bounds__(maxThreadsPerBlock, minBlocksPerMultiprocessor)` per ASP Ch 6 (p. 206).

    Reproduces the ASP Ch 6 p. 206 example:
    `__launch_bounds__(256, 16)` requests 256 * 16 = 4,096 threads/SM, which
    exceeds the 2,048-thread hardware limit on Blackwell, emitting a `ptxas`
    warning (`.minnctapersm will be ignored`) and clamping to 8 blocks (2,048 threads).
    """
    if arch not in ARCH_LIMITS:
        raise ExecutionModelError(f"Unsupported architecture: {arch}")
    lim = ARCH_LIMITS[arch]
    if max_threads_per_block <= 0 or max_threads_per_block > lim.max_threads_per_block:
        raise ExecutionModelError("max_threads_per_block out of hardware range (1..1024)")
    if min_blocks_per_sm <= 0:
        raise ExecutionModelError("min_blocks_per_sm must be positive")

    requested_threads_per_sm = max_threads_per_block * min_blocks_per_sm
    max_feasible_blocks = min(
        lim.max_active_blocks_per_sm,
        lim.max_resident_threads_per_sm // max_threads_per_block,
    )
    exceeds_sm_limit = requested_threads_per_sm > lim.max_resident_threads_per_sm
    effective_blocks = max_feasible_blocks if exceeds_sm_limit else min(min_blocks_per_sm, max_feasible_blocks)
    max_regs_per_thread_without_spill = lim.registers_per_sm // (
        effective_blocks * max_threads_per_block
    )

    return {
        "requested_threads_per_sm": requested_threads_per_sm,
        "exceeds_sm_thread_limit": exceeds_sm_limit,
        "ptxas_warning_emitted": exceeds_sm_limit,
        "effective_blocks_per_sm": effective_blocks,
        "effective_threads_per_sm": effective_blocks * max_threads_per_block,
        "max_regs_per_thread_target": min(lim.max_registers_per_thread, max_regs_per_thread_without_spill),
    }


def diagnose_kernel_efficiency_gates(
    active_threads_per_inst: float,
    sectors_per_global_ld_request: float,
    bytes_per_element: int = 4,
    sector_size_bytes: int = 32,
    warp_size: int = 32,
) -> Dict[str, object]:
    """Evaluate the Control-Flow and Memory-Coalescing efficiency gates per nvidia-devops V2 Ch 9.

    Reproduces the worked examples in V2 Ch 9:
    - `smsp__thread_inst_executed_per_inst_executed.ratio` = 19.4 / 32 = 60.62% active-lane efficiency.
    - For 32 threads reading 4-byte floats (`128` useful bytes) across 32-byte sectors:
      * Ideal coalesced load = `128 / 32 = 4.0` sectors (`128` bytes transferred, `1.0x` amplification).
      * Observed `11.6` sectors/request = `371.2` bytes transferred (`2.9x` amplification).
      * Worst-case scattered load = `32.0` sectors (`1,024` bytes transferred, `8.0x` amplification).
    """
    if not (0.0 < active_threads_per_inst <= warp_size):
        raise ExecutionModelError("active_threads_per_inst must be in (0, warp_size]")
    if sectors_per_global_ld_request <= 0:
        raise ExecutionModelError("sectors_per_global_ld_request must be positive")

    useful_bytes_per_warp = warp_size * bytes_per_element
    ideal_sectors = useful_bytes_per_warp / sector_size_bytes
    transferred_bytes = sectors_per_global_ld_request * sector_size_bytes
    byte_amplification = round(transferred_bytes / useful_bytes_per_warp, 2)
    active_lane_pct = round((active_threads_per_inst / warp_size) * 100.0, 2)

    control_flow_leaking = active_lane_pct < 85.0
    memory_coalescing_leaking = sectors_per_global_ld_request > (ideal_sectors * 1.25)

    return {
        "active_lane_efficiency_pct": active_lane_pct,
        "useful_bytes_per_warp": useful_bytes_per_warp,
        "ideal_sectors_per_request": ideal_sectors,
        "transferred_bytes_per_warp": round(transferred_bytes, 1),
        "byte_amplification_factor": byte_amplification,
        "control_flow_gate_leaking": control_flow_leaking,
        "memory_coalescing_gate_leaking": memory_coalescing_leaking,
    }
