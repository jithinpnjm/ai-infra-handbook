#!/usr/bin/env python3
"""Chapter 10.14 model: Occupancy, Warp Efficiency, and Instruction-Level Parallelism (ILP).

Encodes the verifiable occupancy calculation formulas, __launch_bounds__
register ceiling math, Nsight Compute warp stall & regime classifiers,
warp-divergence vs predication metrics, and ILP-vs-occupancy trade-off tables
from:
- AI Systems Performance Engineering (ASP) Chapter 8 (pp. 253-294):
  - Nsight Compute warp stall reasons (`Long Scoreboard`, `Short Scoreboard`,
    `Memory Throttle`, `Not Selected`, `Exec Dependency`, `Compute Unit Busy` /
    `Math Pipe Throttle`, `Synchronization`, `Instruction Fetch/Issue`, Table 8-1)
    and the 4 execution regimes (`UNDERUTILIZED`, `LATENCY_BOUND`, `MEMORY_BOUND`,
    `COMPUTE_BOUND`, Table 8-2).
  - SM occupancy limits: 64 warps (2,048 threads) per SM on Ampere/Hopper/Blackwell
    (`sm_80`/`sm_90`/`sm_100`) vs 48 warps (1,536 threads) per SM on RTX PRO 6000
    and Spark DGX GB10 (`sm_120`, CC 12.x); 30% occupancy on a 64-warp SM = 19.2
    (~19) active warps; `__launch_bounds__(256, 8)` = 2,048 threads (64 warps,
    100% occupancy) with max 32 registers/thread (`65,536 // 2,048 = 32`).
  - Predication vs branch divergence (`threshold_naive` vs `threshold_predicated`,
    Table 8-3: runtime 30 ms -> 15 ms (-50%), dynamic instructions 600M -> 300M
    (-50%), branch-resolving stall latency 200 -> 100 cycles (-50%), warp
    execution efficiency 50% -> 99%, predicated-off threads 50% -> 0%).
  - Instruction-Level Parallelism (ILP) vs required occupancy to saturate a
    Blackwell SM (Table 8-4: ILP 1 -> 1,536 threads / 48 warps / 75% occ;
    ILP 2 -> 1,024 threads / 32 warps / 50% occ; ILP 3 -> 768 threads / 24 warps
    / 37.5% occ; ILP 4 -> 512 threads / 16 warps / 25% occ), IPC rising from
    1.0 to 1.8 per scheduler, and Blackwell unified INT32/FP32 core dual-issue rule.
"""

from __future__ import annotations

from typing import Dict, List


class OccupancyILPError(ValueError):
    """Raised when invalid occupancy, warp divergence, or ILP parameters are provided."""


# Table 8-4: How ILP reduces threads/warps/occupancy needed to saturate a Blackwell SM (ASP Ch 8 p. 286)
ILP_SATURATION_TABLE: Dict[int, Dict[str, float]] = {
    1: {"threads_per_sm": 1536.0, "warps_per_sm": 48.0, "occupancy_pct": 75.0},
    2: {"threads_per_sm": 1024.0, "warps_per_sm": 32.0, "occupancy_pct": 50.0},
    3: {"threads_per_sm": 768.0, "warps_per_sm": 24.0, "occupancy_pct": 37.5},
    4: {"threads_per_sm": 512.0, "warps_per_sm": 16.0, "occupancy_pct": 25.0},
}

# Table 8-3: Profiling results of removing warp divergence via predication (ASP Ch 8 p. 280)
TABLE_8_3_PREDICATION: Dict[str, float] = {
    "runtime_ms_before": 30.0,
    "runtime_ms_after": 15.0,
    "dynamic_instructions_millions_before": 600.0,
    "dynamic_instructions_millions_after": 300.0,
    "branch_stall_cycles_before": 200.0,
    "branch_stall_cycles_after": 100.0,
    "warp_exec_efficiency_pct_before": 50.0,
    "warp_exec_efficiency_pct_after": 99.0,
    "predicated_off_threads_pct_before": 50.0,
    "predicated_off_threads_pct_after": 0.0,
}


def calc_sm_occupancy_and_limiters(
    threads_per_block: int = 256,
    regs_per_thread: int = 32,
    shmem_per_block_bytes: int = 8192,
    gpu_profile: str = "BLACKWELL_B200",
    achieved_occupancy_pct: float = 30.0,
) -> Dict[str, object]:
    """Calculate theoretical SM occupancy, active warps, and primary occupancy limiter per ASP Ch 8 (pp. 262-274).

    Hardware profiles (ASP Ch 8 p. 269):
    - `BLACKWELL_B200` (and `A100` / `H100`): max 64 warps (2,048 threads) per SM, max 32 blocks/SM,
      65,536 (64K) 32-bit registers/SM, max 255 regs/thread, 227 KB (232,448 B) usable SMEM/SM.
    - `RTX_PRO_6000_GB10` (CC 12.x): max 48 warps (1,536 threads) per SM, max 32 blocks/SM,
      65,536 registers/SM.
    """
    profiles = {
        "BLACKWELL_B200": {"max_warps": 64, "max_threads": 2048, "max_blocks": 32, "max_regs": 65536, "max_smem": 227 * 1024},
        "RTX_PRO_6000_GB10": {"max_warps": 48, "max_threads": 1536, "max_blocks": 32, "max_regs": 65536, "max_smem": 227 * 1024},
    }
    if gpu_profile not in profiles:
        raise OccupancyILPError(f"Unsupported gpu_profile: {gpu_profile}")
    if threads_per_block <= 0 or threads_per_block > 1024:
        raise OccupancyILPError("threads_per_block must be in 1..1024")
    if regs_per_thread <= 0 or regs_per_thread > 255:
        raise OccupancyILPError("regs_per_thread must be in 1..255")
    if shmem_per_block_bytes < 0 or not (0.0 <= achieved_occupancy_pct <= 100.0):
        raise OccupancyILPError("Invalid shared memory or achieved occupancy percentage")

    hw = profiles[gpu_profile]
    warps_per_block = (threads_per_block + 31) // 32
    regs_per_block = threads_per_block * regs_per_thread

    blocks_by_threads = hw["max_threads"] // threads_per_block
    blocks_by_warps = hw["max_warps"] // warps_per_block
    blocks_by_regs = hw["max_regs"] // regs_per_block
    blocks_by_smem = (hw["max_smem"] // shmem_per_block_bytes) if shmem_per_block_bytes > 0 else hw["max_blocks"]

    active_blocks = min(blocks_by_threads, blocks_by_warps, blocks_by_regs, blocks_by_smem, hw["max_blocks"])
    theoretical_warps = active_blocks * warps_per_block
    theoretical_occ_pct = (theoretical_warps / hw["max_warps"]) * 100.0
    achieved_active_warps = round((achieved_occupancy_pct / 100.0) * hw["max_warps"])

    limiters: List[str] = []
    if blocks_by_regs == active_blocks and blocks_by_regs < blocks_by_threads:
        limiters.append("LIMITED_BY_REGISTERS_PER_THREAD")
    if blocks_by_smem == active_blocks and blocks_by_smem < blocks_by_threads:
        limiters.append("LIMITED_BY_SHARED_MEMORY_PER_BLOCK")
    if not limiters:
        limiters.append("LIMITED_BY_THREAD_OR_WARP_SLOTS")

    return {
        "gpu_profile": gpu_profile,
        "max_warps_per_sm": hw["max_warps"],
        "max_threads_per_sm": hw["max_threads"],
        "warps_per_block": warps_per_block,
        "active_blocks_per_sm": active_blocks,
        "theoretical_active_warps": theoretical_warps,
        "theoretical_occupancy_pct": round(theoretical_occ_pct, 1),
        "achieved_occupancy_pct": achieved_occupancy_pct,
        "achieved_active_warps": achieved_active_warps,
        "primary_limiters": limiters,
    }


def evaluate_launch_bounds(
    max_threads_per_block: int = 256,
    min_blocks_per_sm: int = 8,
    sm_register_file_size: int = 65536,
    sm_max_threads: int = 2048,
) -> Dict[str, object]:
    """Evaluate `__launch_bounds__(maxThreadsPerBlock, minBlocksPerSM)` per ASP Ch 8 (p. 272).

    Worked example in ASP Ch 8 (p. 272):
    - `__launch_bounds__(256, 8)` requests `8 * 256 = 2,048` resident threads per SM
      (`64` warps = `100.0%` theoretical occupancy on Blackwell B200).
    - To fit `2,048` threads inside the `65,536`-register file without spilling, the compiler
      caps register allocation at `65,536 // 2,048 = 32` registers per thread.
    """
    if max_threads_per_block <= 0 or max_threads_per_block > 1024 or min_blocks_per_sm <= 0:
        raise OccupancyILPError("Invalid __launch_bounds__ parameters")
    target_threads_per_sm = max_threads_per_block * min_blocks_per_sm
    if target_threads_per_sm > sm_max_threads:
        raise OccupancyILPError(
            f"__launch_bounds__({max_threads_per_block}, {min_blocks_per_sm}) requests {target_threads_per_sm} "
            f"threads/SM, exceeding hardware limit of {sm_max_threads}"
        )

    max_regs_per_thread_without_spill = min(255, sm_register_file_size // target_threads_per_sm)
    target_warps_per_sm = target_threads_per_sm // 32
    target_occupancy_pct = (target_threads_per_sm / sm_max_threads) * 100.0

    return {
        "max_threads_per_block": max_threads_per_block,
        "min_blocks_per_sm": min_blocks_per_sm,
        "target_threads_per_sm": target_threads_per_sm,
        "target_warps_per_sm": target_warps_per_sm,
        "target_occupancy_pct": round(target_occupancy_pct, 1),
        "compiler_max_regs_per_thread": max_regs_per_thread_without_spill,
    }


def classify_ncu_stall_and_regime(
    dram_bw_pct_of_peak: float,
    compute_pipe_pct_of_peak: float,
    sm_active_pct: float,
    dominant_stall_reason: str,
    eligible_warps_per_cycle: float = 2.0,
    schedulers_per_sm: int = 4,
) -> Dict[str, object]:
    """Classify a kernel into the 4 performance regimes & map Nsight Compute warp stall reasons per ASP Ch 8 (Tables 8-1 & 8-2, pp. 258-268).

    Four regimes (ASP Ch 8 Table 8-2, p. 266):
    1. `UNDERUTILIZED`: Both DRAM bandwidth (< 30%) and compute (< 30%) are low, with low `sm_active_pct` (< 50%)
       or `No Eligible` / `Idle` stalls -> grid/batch too small to fill all SMs.
    2. `MEMORY_BOUND`: DRAM bandwidth is near peak (>= 75%, e.g. 80%-95%) while compute is low ->
       dominated by `Long Scoreboard` or `Memory Throttle` stalls; fix with tiling, kernel fusion,
       coalescing, caching, or lower precision.
    3. `COMPUTE_BOUND`: Compute / Tensor Core pipeline utilization is near peak (>= 75%) ->
       dominated by `Compute Unit Busy` / `Math Pipe Throttle` or `Not Selected`; fix with lower
       precision (FP16/FP8/FP4), Tensor Cores, or 2:4 sparsity.
    4. `LATENCY_BOUND`: Neither DRAM bandwidth (< 75%) nor compute (< 75%) is saturated, yet warps
       stall on `Long Scoreboard`, `Short Scoreboard`, `Exec Dependency`, or `Synchronization`
       (with `eligible_warps_per_cycle < schedulers_per_sm`) -> fix by raising occupancy, exposing
       2-to-4-way ILP (`#pragma unroll`), or TMA asynchronous prefetching.
    """
    valid_stalls = {
        "LONG_SCOREBOARD",
        "SHORT_SCOREBOARD",
        "MEMORY_THROTTLE",
        "EXEC_DEPENDENCY",
        "COMPUTE_UNIT_BUSY",
        "MATH_PIPE_THROTTLE",
        "SYNCHRONIZATION_BARRIER",
        "INSTRUCTION_FETCH",
        "NOT_SELECTED",
        "NO_ELIGIBLE_IDLE",
    }
    stall = dominant_stall_reason.strip().upper()
    if stall not in valid_stalls:
        raise OccupancyILPError(f"Unknown Nsight Compute stall reason: {dominant_stall_reason}")
    if not (0.0 <= dram_bw_pct_of_peak <= 100.0) or not (0.0 <= compute_pipe_pct_of_peak <= 100.0):
        raise OccupancyILPError("Throughput percentages must be in 0..100")

    starved_schedulers = eligible_warps_per_cycle < float(schedulers_per_sm)

    if sm_active_pct < 50.0 or stall == "NO_ELIGIBLE_IDLE":
        regime = "UNDERUTILIZED"
        remedy = "Increase grid size, batch size, or use CUDA streams / CUDA Graphs (`torch.compile`) to fill all SMs."
    elif dram_bw_pct_of_peak >= 75.0:
        regime = "MEMORY_BOUND"
        remedy = "Raise arithmetic intensity via shared-memory tiling, kernel fusion, coalescing/vectorizing, or FP8/FP4 quantization."
    elif compute_pipe_pct_of_peak >= 75.0 or stall in {"COMPUTE_UNIT_BUSY", "MATH_PIPE_THROTTLE"}:
        regime = "COMPUTE_BOUND"
        remedy = "Shift math to lower-precision Tensor Cores (`tcgen05.mma` FP16/FP8/NVFP4/MXFP4), 2:4 sparsity, or dual-issue math+memory ILP."
    else:
        regime = "LATENCY_BOUND"
        if stall == "EXEC_DEPENDENCY":
            remedy = "Break sequential ALU dependency chains and expose 2-to-4-way ILP via loop unrolling (`#pragma unroll`) and multiple accumulators."
        elif stall in {"LONG_SCOREBOARD", "SHORT_SCOREBOARD"}:
            remedy = "Hide memory latency by raising occupancy (50%-75%), exposing independent loads per thread (ILP), or TMA `cuda::memcpy_async` double-buffering."
        elif stall == "SYNCHRONIZATION_BARRIER":
            remedy = "Reduce `__syncthreads()` frequency, balance per-warp work, or replace shared-memory reductions with `__shfl_down_sync`."
        else:
            remedy = "Increase occupancy or per-thread ILP so eligible warps/cycle >= 4 warp schedulers."

    return {
        "regime": regime,
        "dominant_stall_reason": stall,
        "dram_bw_pct_of_peak": dram_bw_pct_of_peak,
        "compute_pipe_pct_of_peak": compute_pipe_pct_of_peak,
        "eligible_warps_per_cycle": eligible_warps_per_cycle,
        "schedulers_starved_for_eligible_warps": starved_schedulers,
        "recommended_remedy": remedy,
    }


def evaluate_warp_divergence_and_ilp(
    active_lanes_in_branch_a: int = 16,
    warp_size: int = 32,
    ilp_independent_ops_per_thread: int = 2,
    dual_issue_pair: tuple[str, str] = ("FP32_MATH", "LD_ST_MEMORY"),
) -> Dict[str, object]:
    """Evaluate SIMT branch divergence efficiency, predication speedup, and Blackwell ILP / dual-issue rules per ASP Ch 8 (pp. 274-290).

    Rules:
    1. In a two-way divergent `if/else` branch where `k` of 32 lanes take branch A and `32 - k` take
       branch B (`0 < k < 32`), the warp executes both paths serially (`2` passes):
       - For a 50/50 split (`k = 16`), warp execution efficiency is `50.0%`, and predication (`?:` or
         `torch.maximum`) cuts runtime `30 ms -> 15 ms` (`2.0x`), dynamic instructions `600M -> 300M`,
         and branch stall latency `200 -> 100` cycles (Table 8-3).
       - For a `1 vs 31` split (`k = 1`), `31/32` lanes (`96.88%`) sit idle during the 1-lane pass.
    2. Table 8-4 (ILP vs Occupancy on Blackwell):
       - `ILP = 1` requires `~1,536` threads (`48` warps = `75.0%` occupancy).
       - `ILP = 2` requires `~1,024` threads (`32` warps = `50.0%` occupancy).
       - `ILP = 3` requires `~768` threads (`24` warps = `37.5%` occupancy).
       - `ILP = 4` requires `~512` threads (`16` warps = `25.0%` occupancy).
    3. Blackwell unified INT32/FP32 core rule (ASP Ch 8 pp. 266, 283):
       On Blackwell, INT32 and FP32 cores are unified and execute *either* FP32 *or* INT32 in a cycle,
       so (`INT32_MATH`, `FP32_MATH`) **cannot** dual-issue on the same unified core in the same cycle,
       whereas (`FP32_MATH`, `LD_ST_MEMORY`) can dual-issue within a warp scheduler partition.
    """
    if not (0 <= active_lanes_in_branch_a <= warp_size) or warp_size <= 0:
        raise OccupancyILPError("active_lanes_in_branch_a must be in 0..warp_size")
    if ilp_independent_ops_per_thread not in ILP_SATURATION_TABLE:
        raise OccupancyILPError("ilp_independent_ops_per_thread must be in {1, 2, 3, 4}")

    divergent = 0 < active_lanes_in_branch_a < warp_size
    passes = 2 if divergent else 1
    warp_exec_eff_pct = 50.0 if divergent else 100.0
    max_idle_lanes_in_single_pass = max(active_lanes_in_branch_a, warp_size - active_lanes_in_branch_a) if divergent else 0

    pair_set = {dual_issue_pair[0].upper(), dual_issue_pair[1].upper()}
    can_dual_issue_on_blackwell = pair_set != {"INT32_MATH", "FP32_MATH"}

    ilp_spec = ILP_SATURATION_TABLE[ilp_independent_ops_per_thread]

    return {
        "divergent": divergent,
        "serial_passes": passes,
        "warp_execution_efficiency_pct": warp_exec_eff_pct,
        "max_idle_lanes_in_single_pass": max_idle_lanes_in_single_pass,
        "ilp_level": ilp_independent_ops_per_thread,
        "threads_per_sm_for_saturation": int(ilp_spec["threads_per_sm"]),
        "warps_per_sm_for_saturation": int(ilp_spec["warps_per_sm"]),
        "occupancy_pct_for_saturation": ilp_spec["occupancy_pct"],
        "blackwell_can_dual_issue_pair": can_dual_issue_on_blackwell,
    }
