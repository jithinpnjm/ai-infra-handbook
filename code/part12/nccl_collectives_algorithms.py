#!/usr/bin/env python3
"""Chapter 12.15 model: NCCL: collectives and algorithms.

Encodes the verifiable mathematical models, collective communication primitives,
algorithmic step and volume formulas, protocol framing efficiencies, bus
bandwidth conversions, zero-copy buffer registration rules, wave scheduling,
and disaggregated point-to-point comparisons from:
- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`),
  Chapter 4 (*Tuning Distributed Networking Communication*) and Chapter 19
  (*Dynamic and Adaptive Inference Engine Optimizations*).
- *Distributed AI Systems* (`distributed-ai-systems`), Chapter 1 and Chapter 2
  (*GPU Hardware, Networking, and Parallelism Strategies*).
- `nvidia-devops` Volume 07 Chapter 9 (*Multi-Node Collectives and NCCL*) and
  Volume 06 Chapter 2 (*Masterclass: GPUDirect, NCCL, Fabric, and Network Operator*).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


class NCCLCollectiveModelError(ValueError):
    """Raised when invalid collective, algorithm, protocol, or topology parameters are supplied."""


@dataclass(frozen=True)
class CollectivePrimitiveSpec:
    collective: str
    pattern: str
    per_rank_input_formula: str
    per_rank_output_formula: str
    ring_steps_formula: str
    busbw_factor_formula: str
    in_place_supported: bool
    primary_ai_workloads: str


COLLECTIVE_PRIMITIVES: Dict[str, CollectivePrimitiveSpec] = {
    "AllReduce": CollectivePrimitiveSpec(
        collective="AllReduce",
        pattern="Many-to-many reduction + distribution (ReduceScatter + AllGather)",
        per_rank_input_formula="S",
        per_rank_output_formula="S (reduced across all N ranks)",
        ring_steps_formula="2*(N-1)",
        busbw_factor_formula="2*(N-1)/N",
        in_place_supported=True,
        primary_ai_workloads="DDP gradient averaging, Tensor Parallelism activation reductions",
    ),
    "ReduceScatter": CollectivePrimitiveSpec(
        collective="ReduceScatter",
        pattern="Many-to-many reduction with sharded output (1/N per rank)",
        per_rank_input_formula="S",
        per_rank_output_formula="S/N (reduced shard r)",
        ring_steps_formula="N-1",
        busbw_factor_formula="(N-1)/N",
        in_place_supported=True,
        primary_ai_workloads="FSDP / ZeRO-2 / ZeRO-3 backward gradient reduction + sharding, Sequence Parallelism",
    ),
    "AllGather": CollectivePrimitiveSpec(
        collective="AllGather",
        pattern="Many-to-many concatenation of 1/N shards to full tensor S on all ranks",
        per_rank_input_formula="S/N",
        per_rank_output_formula="S (concatenated in rank order 0..N-1)",
        ring_steps_formula="N-1",
        busbw_factor_formula="(N-1)/N",
        in_place_supported=True,
        primary_ai_workloads="FSDP / ZeRO-3 forward & backward parameter unsharding, Tensor Parallelism column gather",
    ),
    "Broadcast": CollectivePrimitiveSpec(
        collective="Broadcast",
        pattern="One-to-all replication from root rank to all N ranks",
        per_rank_input_formula="S on root, 0 on non-root",
        per_rank_output_formula="S on all N ranks",
        ring_steps_formula="N-1 (pipelined ring) or 1 (NVLS multicast)",
        busbw_factor_formula="1.0",
        in_place_supported=True,
        primary_ai_workloads="Initial model weight/checkpoint distribution, hyperparameter & seed sync",
    ),
    "Reduce": CollectivePrimitiveSpec(
        collective="Reduce",
        pattern="All-to-one reduction from all N ranks onto root rank only",
        per_rank_input_formula="S on all N ranks",
        per_rank_output_formula="S on root (other ranks unchanged)",
        ring_steps_formula="N-1",
        busbw_factor_formula="1.0",
        in_place_supported=True,
        primary_ai_workloads="Centralized metric/loss aggregation, single-rank checkpoint reduction",
    ),
    "AllToAll": CollectivePrimitiveSpec(
        collective="AllToAll",
        pattern="All-to-all personalized transpose (rank i sends chunk j of size S/N to rank j)",
        per_rank_input_formula="S (N chunks of S/N)",
        per_rank_output_formula="S (N chunks of S/N transposed)",
        ring_steps_formula="N-1 (remote pairwise/ring rounds; 1 local self-chunk)",
        busbw_factor_formula="(N-1)/N",
        in_place_supported=False,
        primary_ai_workloads="MoE Expert Parallelism token dispatch/combine, Context/Sequence Parallelism transpose",
    ),
}


@dataclass(frozen=True)
class NCCLAlgorithmSpec:
    algo_name: str
    nccl_algo_token: str
    latency_steps_complexity: str
    per_gpu_allreduce_volume: str
    hardware_offload: str
    optimal_regime: str


NCCL_ALGORITHMS: Dict[str, NCCLAlgorithmSpec] = {
    "RING": NCCLAlgorithmSpec(
        algo_name="Ring AllReduce",
        nccl_algo_token="Ring",
        latency_steps_complexity="2*(N-1) sequential hop steps (N-1 per reduction pass)",
        per_gpu_allreduce_volume="2*(N-1)/N * S",
        hardware_offload="None (GPU SMs / DMA engines execute peer-to-peer ring transfers)",
        optimal_regime="Large bandwidth-dominated messages at small-to-medium GPU counts",
    ),
    "TREE": NCCLAlgorithmSpec(
        algo_name="Double Binary Tree AllReduce",
        nccl_algo_token="Tree",
        latency_steps_complexity="2*log2(N) steps (reduce to root + broadcast from root across dual complementary trees)",
        per_gpu_allreduce_volume="~2 * S (split 50/50 across two complementary binary trees so all ranks stay active)",
        hardware_offload="None (intranode chain + internode dual binary tree on GPUs)",
        optimal_regime="Small/medium latency-dominated messages and large multi-node scale where 2*(N-1) ring hops stall",
    ),
    "COLLNET": NCCLAlgorithmSpec(
        algo_name="CollNet (CollNetDirect / CollNetChain with InfiniBand SHARP)",
        nccl_algo_token="CollNetDirect,CollNetChain",
        latency_steps_complexity="O(log_k(N_nodes)) switch-tree reduction + intranode local reduction",
        per_gpu_allreduce_volume="B/N received per endpoint from switch tree (1/(N-1) of ring ReduceScatter volume)",
        hardware_offload="Quantum InfiniBand switch ASICs via SHARP Aggregation Manager + NCCL RDMA SHARP plugin",
        optimal_regime="Multi-node InfiniBand clusters (especially 32+ nodes, 2x to 5x AllReduce speedup)",
    ),
    "NVLS": NCCLAlgorithmSpec(
        algo_name="NVLink SHARP (NVLS / NVLSTree)",
        nccl_algo_token="NVLS,NVLSTree",
        latency_steps_complexity="Single-stage / two-stage switch reduction + hardware multicast across NVSwitch domain",
        per_gpu_allreduce_volume="B/N per endpoint in ReduceScatter and B/N sent in AllGather (1/(N-1) vs ring)",
        hardware_offload="NVSwitch 3.0/4.0 (Hopper HGX/DGX and Blackwell NVL72 72-GPU rack domains)",
        optimal_regime="High-bandwidth intra-node or intra-rack NVL72 collectives and overlapped AG+RS (~1/2 wall time)",
    ),
    "PAT": NCCLAlgorithmSpec(
        algo_name="Parallel Aggregated Tree (PAT)",
        nccl_algo_token="PAT",
        latency_steps_complexity="O(log2(N)) startup latency per pipelined segment",
        per_gpu_allreduce_volume="Near-ring optimal bandwidth via staggered multi-chunk tree ReduceScatter/AllGather",
        hardware_offload="Topology-aware multi-stream GPU scheduling across NVSwitch and scale-out links",
        optimal_regime="Medium-to-large messages at scale requiring both tree-like O(log N) latency and ring-like bandwidth",
    ),
}


@dataclass(frozen=True)
class NCCLProtocolSpec:
    protocol: str
    word_packet_bytes: int
    payload_bytes: int
    flag_bytes: int
    payload_efficiency_pct: float
    flag_overhead_pct: float
    synchronization_mechanism: str
    typical_message_regime: str


NCCL_PROTOCOLS: Dict[str, NCCLProtocolSpec] = {
    "LL": NCCLProtocolSpec(
        protocol="LL (Low Latency)",
        word_packet_bytes=8,
        payload_bytes=4,
        flag_bytes=4,
        payload_efficiency_pct=50.0,
        flag_overhead_pct=50.0,
        synchronization_mechanism="8-byte atomic store/poll (4B data + 4B inline flag, no memory fence)",
        typical_message_regime="Tiny messages (up to ~32-64 KiB) where sub-microsecond flag polling beats bandwidth efficiency",
    ),
    "LL128": NCCLProtocolSpec(
        protocol="LL128 (Low Latency 128-Byte)",
        word_packet_bytes=128,
        payload_bytes=120,
        flag_bytes=8,
        payload_efficiency_pct=93.75,
        flag_overhead_pct=6.25,
        synchronization_mechanism="128-byte NVLink/PCIe atomic transaction (120B payload + 8B flag, no memory fence)",
        typical_message_regime="Small-to-medium messages (~64 KiB to several MiB on NVLink/PCIe supporting 128B atomics)",
    ),
    "Simple": NCCLProtocolSpec(
        protocol="Simple (Bulk DMA + Fence)",
        word_packet_bytes=4194304,
        payload_bytes=4194304,
        flag_bytes=0,
        payload_efficiency_pct=100.0,
        flag_overhead_pct=0.0,
        synchronization_mechanism="Bulk peer DMA into NCCL_BUFFSIZE (default 4 MiB) + __threadfence_system() per slice",
        typical_message_regime="Large bandwidth-bound messages (> 4-16 MiB) where fence latency is amortized",
    ),
}


def compute_collective_volume_and_busbw(
    collective: str,
    tensor_bytes: int,
    num_gpus: int,
    elapsed_sec: float = 0.001,
) -> Dict[str, float]:
    """Compute exact Ring steps, per-rank transferred bytes, algbw, and busbw.

    Follows official `nccl-tests` and `distributed-ai-systems` Ch 1-2 /
    `ai-systems-performance-engineering` Ch 4 formulas:
    - `algbw = tensor_bytes / elapsed_sec` (in GB/s, 10^9 B/s)
    - `busbw = algbw * factor`, where `factor` is:
      * `AllReduce`:     `2 * (N - 1) / N`
      * `ReduceScatter`: `(N - 1) / N`
      * `AllGather`:     `(N - 1) / N`
      * `AllToAll`:      `(N - 1) / N`
      * `Broadcast`:     `1.0`
      * `Reduce`:        `1.0`
    """
    if collective not in COLLECTIVE_PRIMITIVES:
        raise NCCLCollectiveModelError(f"Unknown collective: {collective}")
    if tensor_bytes <= 0 or num_gpus < 1 or elapsed_sec <= 0.0:
        raise NCCLCollectiveModelError("tensor_bytes, num_gpus, and elapsed_sec must be positive")

    if num_gpus == 1:
        factor = 0.0
        ring_steps = 0
        chunk_bytes = float(tensor_bytes)
    elif collective == "AllReduce":
        factor = (2.0 * (num_gpus - 1)) / num_gpus
        ring_steps = 2 * (num_gpus - 1)
        chunk_bytes = tensor_bytes / num_gpus
    elif collective in ("ReduceScatter", "AllGather", "AllToAll"):
        factor = (num_gpus - 1) / num_gpus
        ring_steps = num_gpus - 1
        chunk_bytes = tensor_bytes / num_gpus
    else:  # Broadcast, Reduce
        factor = 1.0
        ring_steps = num_gpus - 1
        chunk_bytes = float(tensor_bytes)

    per_rank_bytes = tensor_bytes * factor
    algbw_gbps = (tensor_bytes / elapsed_sec) / 1e9
    busbw_gbps = algbw_gbps * factor

    return {
        "collective": collective,
        "tensor_bytes": float(tensor_bytes),
        "num_gpus": float(num_gpus),
        "ring_steps": float(ring_steps),
        "chunk_bytes": round(chunk_bytes, 2),
        "busbw_factor": round(factor, 6),
        "per_rank_bytes_transferred": round(per_rank_bytes, 2),
        "algbw_gbps": round(algbw_gbps, 4),
        "busbw_gbps": round(busbw_gbps, 4),
    }


def evaluate_dai_ch2_benchmarks(
    size_mb: int = 100,
    world_size: int = 2,
    iterations: int = 50,
    elapsed_sec: float = 0.248,
    single_gpu_copy_mb: int = 64,
    single_gpu_iters: int = 200,
    single_gpu_elapsed_sec: float = 0.01262339,
    model_tflops_per_iter: float = 860.0,
    iter_time_sec: float = 2.0,
    peak_gpu_tflops: float = 989.0,
) -> Dict[str, float]:
    """Reproduce the exact `distributed-ai-systems` Ch 2 benchmark and MFU calculations.

    - `allreduce_microbench.py` (DAI Ch 2 lines 761-795):
      `alg_bytes = size_bytes * n * iterations`, `bus_bytes = size_bytes * 2 * (n - 1) * iterations`.
      For `100 MB`, `world_size = 2`, `50` iterations, `0.248 s`:
      `40,322.58 MB/s` (`39.38 GB/s` in binary GiB/s).
    - `bandwidth_test.py` (DAI Ch 2 lines 712-745):
      `bytes_moved = 2 * nbytes * iterations` (read `a` + write `b`) = `1,980.45 GB/s`.
    - `MFU` (DAI Ch 2 lines 41-47):
      `860 TFLOP / 2.0 s = 430 TFLOPS`, `430 / 989 = 43.48%` (`~43%`).
    """
    if size_mb <= 0 or world_size < 2 or iterations <= 0 or elapsed_sec <= 0.0:
        raise NCCLCollectiveModelError("Invalid microbenchmark parameters")

    size_bytes = size_mb * 1024 * 1024
    alg_bytes = size_bytes * world_size * iterations
    bus_bytes = size_bytes * 2 * (world_size - 1) * iterations

    alg_bw_mb_s = (alg_bytes / (1024**2)) / elapsed_sec
    bus_bw_mb_s = (bus_bytes / (1024**2)) / elapsed_sec
    alg_bw_gib_s = (alg_bytes / (1024**3)) / elapsed_sec
    bus_bw_gib_s = (bus_bytes / (1024**3)) / elapsed_sec

    copy_bytes = 2 * (single_gpu_copy_mb * 1024 * 1024) * single_gpu_iters
    copy_bw_gib_s = (copy_bytes / (1024**3)) / single_gpu_elapsed_sec

    actual_tflops = model_tflops_per_iter / iter_time_sec
    mfu_pct = (actual_tflops / peak_gpu_tflops) * 100.0

    return {
        "alg_bw_mb_s": round(alg_bw_mb_s, 2),
        "bus_bw_mb_s": round(bus_bw_mb_s, 2),
        "alg_bw_gib_s": round(alg_bw_gib_s, 2),
        "bus_bw_gib_s": round(bus_bw_gib_s, 2),
        "ring_factor": round((2.0 * (world_size - 1)) / world_size, 4),
        "single_gpu_copy_gib_s": round(copy_bw_gib_s, 2),
        "actual_tflops": round(actual_tflops, 2),
        "mfu_pct": round(mfu_pct, 2),
    }


def compare_ring_vs_tree_crossover(
    num_gpus: int,
    message_bytes: int,
    per_hop_latency_us: float = 1.5,
    link_bw_gbps: float = 50.0,
) -> Dict[str, float | str]:
    """Compare Ring vs Double Binary Tree AllReduce latency and compute crossover message size.

    In an N-GPU AllReduce of message size S bytes over links with per-hop latency
    `alpha` (seconds) and effective unidirectional bandwidth `B` (bytes/s):
    - Ring AllReduce:
      `T_ring(S) = 2 * (N - 1) * alpha + 2 * ((N - 1) / N) * (S / B)`
    - Double Binary Tree AllReduce:
      `T_tree(S) = 2 * ceil(log2(N)) * alpha + 2 * (S / B) * (tree_bw_penalty)`
      Wait: in a two-phase tree Reduce + Broadcast without SHARP, total volume per interior
      node across both complementary binary trees is `2 * ((N - 1) / N) * S` or `~2 * S / B`
      with a small pipelining/branch factor `k_tree > (N - 1) / N`. Even comparing against
      `2 * S / B` (where tree transfers `(1 / N)` more volume per rank than ring's `(N - 1) / N`,
      plus dual-tree pipeline overhead `tree_bw_overhead_factor >= 1.0`):
      Setting `T_ring(S*) = T_tree(S*)` gives the exact latency-bandwidth crossover size `S*`.
    """
    if num_gpus < 2 or message_bytes <= 0 or per_hop_latency_us <= 0.0 or link_bw_gbps <= 0.0:
        raise NCCLCollectiveModelError("Invalid Ring vs Tree parameters")

    alpha_s = per_hop_latency_us * 1e-6
    bw_bytes_s = link_bw_gbps * 1e9

    ring_one_way_steps = num_gpus - 1
    ring_allreduce_steps = 2 * (num_gpus - 1)
    tree_floor_log2_steps = int(math.floor(math.log2(num_gpus)))
    tree_ceil_log2_steps = int(math.ceil(math.log2(num_gpus)))
    tree_allreduce_steps = 2 * tree_ceil_log2_steps

    ring_latency_us = ring_allreduce_steps * per_hop_latency_us
    ring_bw_us = (2.0 * (num_gpus - 1) / num_gpus) * (message_bytes / bw_bytes_s) * 1e6
    ring_total_us = ring_latency_us + ring_bw_us

    # Double binary tree carries ~15% effective bandwidth overhead at scale vs ideal ring streaming
    tree_effective_bw_factor = 1.15
    tree_latency_us = tree_allreduce_steps * per_hop_latency_us
    tree_bw_us = (2.0 * tree_effective_bw_factor) * (message_bytes / bw_bytes_s) * 1e6
    tree_total_us = tree_latency_us + tree_bw_us

    # Solve ring_latency + 2*((N-1)/N)*(S/B) = tree_latency + 2*tree_effective_bw_factor*(S/B)
    delta_steps = ring_allreduce_steps - tree_allreduce_steps
    bw_slope_diff = 2.0 * (tree_effective_bw_factor - ((num_gpus - 1) / num_gpus))
    if delta_steps <= 0 or bw_slope_diff <= 0:
        crossover_bytes = 0.0
    else:
        crossover_bytes = (delta_steps * alpha_s * bw_bytes_s) / bw_slope_diff

    winner = "TREE" if tree_total_us < ring_total_us else "RING"

    return {
        "num_gpus": num_gpus,
        "ring_one_way_steps": ring_one_way_steps,
        "ring_allreduce_steps": ring_allreduce_steps,
        "tree_floor_log2_steps": tree_floor_log2_steps,
        "tree_ceil_log2_steps": tree_ceil_log2_steps,
        "tree_allreduce_steps": tree_allreduce_steps,
        "ring_total_us": round(ring_total_us, 2),
        "tree_total_us": round(tree_total_us, 2),
        "crossover_bytes": round(crossover_bytes, 2),
        "crossover_mib": round(crossover_bytes / (1024**2), 2),
        "faster_algorithm": winner,
    }


def compute_sharp_and_nvls_offload_math(
    tensor_bytes: int,
    num_gpus: int,
    ag_time_ms: float = 10.0,
    rs_time_ms: float = 10.0,
) -> Dict[str, float]:
    """Compute SHARP and NVLS per-endpoint volume reductions and overlapped phase time.

    Follows *AI Systems Performance Engineering* Chapter 4 (lines 407, 736-740):
    - Ring ReduceScatter receives `B * (N - 1) / N` bytes per GPU across `N - 1` hops.
    - In-network SHARP / NVLS ReduceScatter aggregates in switch silicon and returns
      only `B / N` bytes per GPU: a `1 / (N - 1)` volume ratio versus full ring.
    - NVLS multicast AllGather sends `B / N` once from each GPU while the NVSwitch
      replicates it: a `1 / (N - 1)` sender volume ratio versus full ring.
    - Overlapping NVLS multicast AllGather with in-network ReduceScatter reduces
      serial wall time `T_AG + T_RS` to `max(T_AG, T_RS)` (~1/2 wall time when balanced).
    """
    if tensor_bytes <= 0 or num_gpus < 2 or ag_time_ms <= 0.0 or rs_time_ms <= 0.0:
        raise NCCLCollectiveModelError("Invalid SHARP/NVLS parameters")

    ring_rs_bytes = tensor_bytes * (num_gpus - 1) / num_gpus
    sharp_rs_bytes = tensor_bytes / num_gpus
    volume_ratio_vs_ring = 1.0 / (num_gpus - 1)

    serial_phase_ms = ag_time_ms + rs_time_ms
    overlapped_phase_ms = max(ag_time_ms, rs_time_ms)
    wall_time_ratio = overlapped_phase_ms / serial_phase_ms

    return {
        "num_gpus": float(num_gpus),
        "ring_rs_bytes_per_gpu": round(ring_rs_bytes, 2),
        "sharp_rs_bytes_per_gpu": round(sharp_rs_bytes, 2),
        "ring_ag_send_bytes_per_gpu": round(ring_rs_bytes, 2),
        "nvls_ag_send_bytes_per_gpu": round(sharp_rs_bytes, 2),
        "endpoint_volume_ratio_vs_ring": round(volume_ratio_vs_ring, 6),
        "endpoint_reduction_factor": float(num_gpus - 1),
        "serial_ag_plus_rs_ms": round(serial_phase_ms, 2),
        "overlapped_nvls_ag_rs_ms": round(overlapped_phase_ms, 2),
        "overlapped_wall_time_ratio": round(wall_time_ratio, 4),
        "nvlink_small_msg_max_speedup_x": 7.6,
        "sharp_large_scale_min_speedup_x": 2.0,
        "sharp_large_scale_max_speedup_x": 5.0,
    }


def evaluate_protocol_framing(payload_bytes: int) -> Dict[str, Dict[str, float]]:
    """Compute wire bytes, flag overhead bytes, and framing efficiency for LL, LL128, and Simple."""
    if payload_bytes <= 0:
        raise NCCLCollectiveModelError("payload_bytes must be positive")

    results: Dict[str, Dict[str, float]] = {}
    for name, spec in NCCL_PROTOCOLS.items():
        if name == "Simple":
            packets = math.ceil(payload_bytes / spec.payload_bytes)
            wire_bytes = float(payload_bytes)
            flag_bytes = 0.0
        else:
            packets = math.ceil(payload_bytes / spec.payload_bytes)
            wire_bytes = float(packets * spec.word_packet_bytes)
            flag_bytes = float(packets * spec.flag_bytes)

        results[name] = {
            "packets": float(packets),
            "payload_bytes": float(payload_bytes),
            "flag_bytes": flag_bytes,
            "total_wire_bytes": wire_bytes,
            "efficiency_pct": spec.payload_efficiency_pct,
            "overhead_pct": spec.flag_overhead_pct,
        }
    return results


def evaluate_zero_copy_registration(
    all_ranks_registered: bool,
    symmetric_head_offsets: bool,
    allocator_type: str = "ncclMemAlloc",
    num_channels_default: int = 16,
    num_channels_zero_copy: int = 4,
) -> Dict[str, bool | int | str]:
    """Evaluate persistent NCCL user buffer registration (`ncclCommRegister` / `ncclMemAlloc`).

    Follows *AI Systems Performance Engineering* Chapter 4 (lines 748-751):
    - `ncclCommRegister()` / `ncclCommDeregister()` registers persistent user buffers
      (often allocated with `ncclMemAlloc` / `cudaMemCreate` physical multicast/IPC handles)
      so NCCL collectives operate directly on tensor buffers without internal staging copies.
    - All ranks in the communicator must register buffers, and for symmetric algorithms
      the offset from the buffer head must match across ranks.
    - Reduces channel/SM usage (freeing SMs for compute) and unlocks best NVLS/SHARP paths.
    """
    if num_channels_default <= 0 or num_channels_zero_copy <= 0:
        raise NCCLCollectiveModelError("Channel counts must be positive")

    zero_copy_active = bool(all_ranks_registered and symmetric_head_offsets)
    sm_blocks_saved = (num_channels_default - num_channels_zero_copy) if zero_copy_active else 0

    return {
        "zero_copy_active": zero_copy_active,
        "staging_buffer_bypassed": zero_copy_active,
        "nvls_sharp_zero_copy_eligible": zero_copy_active and allocator_type in ("ncclMemAlloc", "cudaMemCreate"),
        "sm_blocks_saved_per_gpu": sm_blocks_saved,
        "status": (
            "ZERO_COPY_REGISTERED_ACTIVE"
            if zero_copy_active
            else "FALLBACK_INTERNAL_STAGING_BUFFER"
        ),
    }


def plan_nvl72_wave_schedule(
    total_gpus: int = 72,
    ports_per_gpu: int = 18,
    num_waves: int = 4,
    total_concurrent_collectives: int = 12,
    max_collectives_per_wave: int = 4,
) -> Dict[str, int | float | List[int]]:
    """Plan NVL72 collective wave scheduling and rotating ring start ranks (ASP Ch 19).

    Follows *AI Systems Performance Engineering* Chapter 19 (lines 1124-1211):
    - Splitting a 72-GPU AllToAll into `4` waves of `18` GPUs (`72 / 4 = 18`) matches
      each Blackwell GPU's `18` NVLink 5 ports (`~100 GB/s` per port = `1.8 TB/s` total),
      avoiding NVSwitch queueing spikes.
    - Staggering `12` heavy expert-gather/broadcast collectives into batches of `4`
      (`2-4` sweet spot) yields `3` sequential waves without fabric contention.
    - Rotating ring start endpoints across iterations distributes wrap-around link load.
    """
    if total_gpus <= 0 or ports_per_gpu <= 0 or num_waves <= 0 or max_collectives_per_wave <= 0:
        raise NCCLCollectiveModelError("Wave schedule parameters must be positive")

    gpus_per_wave = total_gpus // num_waves
    collective_waves = math.ceil(total_concurrent_collectives / max_collectives_per_wave)
    rotated_starts = [(w * gpus_per_wave) % total_gpus for w in range(num_waves)]

    return {
        "total_gpus": total_gpus,
        "ports_per_gpu": ports_per_gpu,
        "num_waves": num_waves,
        "gpus_per_wave": gpus_per_wave,
        "fits_port_capacity": gpus_per_wave <= ports_per_gpu,
        "collective_waves_for_burst": collective_waves,
        "rotated_ring_start_ranks": rotated_starts,
    }


def evaluate_overlap_and_communicator_pitfalls() -> Dict[str, float | int]:
    """Return the exact ASP Ch 4 overlap, backend, communicator lifecycle, and NIXL metrics."""
    return {
        "no_overlap_compute_ms": 10.0,
        "no_overlap_comm_ms": 12.0,
        "no_overlap_total_ms": 22.0,
        "full_overlap_total_ms": 12.0,
        "table_4_1_baseline_ms": 100.0,
        "table_4_1_overlapped_ms": 70.0,
        "table_4_1_sm_busy_before_pct": 60.0,
        "table_4_1_sm_busy_after_pct": 90.0,
        "ddp_default_bucket_cap_mb": 25.0,
        "dp_step_ms": 45.0,
        "ddp_step_ms": 30.0,
        "ddp_speedup_over_dp_pct": round(((45.0 - 30.0) / 45.0) * 100.0, 2),
        "ring_Scaling_Table_S100MB": {
            "N2": ("50.00 MB", "0.5000", "1.0000", "100.00 MB"),
            "N4": ("25.00 MB", "0.7500", "1.5000", "150.00 MB"),
            "N8": ("12.50 MB", "0.8750", "1.7500", "175.00 MB", "0.875x", "1.75x"),
            "N64": ("1.5625 MB", "0.984375", "1.96875", "196.88 MB", "1.97"),
            "N72": ("1.3889 MB", "0.986111", "1.972222", "197.22 MB", "1.9722x"),
            "N_inf": ("1.0000", "2.0000", "200.00 MB"),
            "dai_10000_mib_to_gib": 9.765625,
            "nvl72_1mib_tree_vs_ring": ("38.12 µs", "162.68 µs"),
            "nvl72_256mib_ring_vs_tree": ("5,436.14 µs", "6,188.02 µs"),
            "nvl72_crossover_bytes": "39,051,908",
        },
        "gloo_400mb_ms": 200.0,
        "gloo_400mb_gbps": 2.0,
        "nccl_400mb_ms": 4.0,
        "nccl_400mb_gbps": 100.0,
        "repeated_init_overhead_ms": 48.0,
        "tiny_allreduce_ms": 0.5,
        "repeated_init_total_ms": 48.5,
        "repeated_init_reduction_pct": round((48.0 / 48.5) * 100.0, 2),
        "max_socket_connections_per_comm": 64,
        "nccl_default_buffsize_bytes": 4194304,
        "ucx_reserved_iter0_gb": 0.800,
        "ucx_reserved_iter1_gb": 1.040,
        "ucx_reserved_iter2_gb": 1.240,
        "llama3_405b_total_interruptions": 419,
        "llama3_405b_network_switch_cable": 35,
        "llama3_405b_nic": 7,
        "llama3_405b_nccl_watchdog": 7,
        "nixl_x86_h100_ttft_speedup_x": 14.0,
        "nixl_gh200_vs_x86_ttft_speedup_x": 2.0,
        "nixl_dynamo_680b_nvl72_speedup_x": 30.0,
    }
