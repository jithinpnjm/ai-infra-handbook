#!/usr/bin/env python3
"""Chapter 12.1 model: AI traffic: collectives, incast and elephant flows.

Encodes the verifiable AI workload traffic rules, Job Completion Time (JCT) and
tail-latency math (serial vs parallel tasks), collective communication algorithms
(Ring vs Tree vs CollNet vs PAT vs SHARP/NVLS), compute-communication overlap
(`DistributedDataParallel` bucketing vs `DataParallel` and manual sync, `Gloo` vs
`NCCL`, repeated communicator init overhead), elephant flows, low-entropy RoCEv2
(`UDP 4791`) flowlets, the four-tier load-balancing pyramid (`SLB`, `DLB`, `GLB`,
`sDLB`), reactive congestion control (`DCQCN`: `ECN = 11` + `CNP` + `PFC`), and
`NIXL` disaggregated inference KV cache transfers from:
- *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`),
  Chapter 1 (*Wonders in the Workload*) and Chapter 2 (*"The Common-Man View" of AI Data Center Fabrics*).
- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`),
  Chapter 4 (*Tuning Distributed Networking Communication*).
- `nvidia-devops` Volume 07 (*GPU Networking and Data Paths*, Chapters 1-12 and Labs 01-04).
- *NVIDIA Base Command Manager 11 Administrator Manual* (`bcm11-admin`, §3.6, §3.12, §5.3.3).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List


class AITrafficModelError(ValueError):
    """Raised when invalid AI traffic, JCT, collective, or fabric parameters are supplied."""


@dataclass(frozen=True)
class ParallelismTrafficProfile:
    parallelism_type: str
    what_is_split: str
    primary_collectives: str
    typical_interconnect_domain: str
    traffic_pattern_notes: str


PARALLELISM_TRAFFIC_PROFILES: Dict[str, ParallelismTrafficProfile] = {
    "DATA_PARALLELISM": ParallelismTrafficProfile(
        parallelism_type="Data Parallelism (DP / DDP / FSDP)",
        what_is_split="Training dataset split into batches across GPUs running replicas (or shards) of the model",
        primary_collectives="AllReduce (DDP), AllGather + ReduceScatter (FSDP), or AllToAll",
        typical_interconnect_domain="Scale-out fabric (InfiniBand / RoCEv2 Ethernet) and intra-node NVLink",
        traffic_pattern_notes="Synchronizes gradients at the end of backward propagation (or overlapped per bucket); generates synchronous east-west elephant flows.",
    ),
    "PIPELINE_PARALLELISM": ParallelismTrafficProfile(
        parallelism_type="Pipeline Parallelism (PP)",
        what_is_split="Model layers sliced horizontally across sequential GPUs or subsets of GPUs",
        primary_collectives="Point-to-point Send / Recv (or NIXL / UCX transfers between stages)",
        typical_interconnect_domain="Scale-out fabric across nodes or intra-rack NVLink",
        traffic_pattern_notes="Output activations of GPU k become input to GPU k+1 in forward pass; gradients flow in reverse.",
    ),
    "TENSOR_PARALLELISM": ParallelismTrafficProfile(
        parallelism_type="Tensor Parallelism (TP)",
        what_is_split="Individual layer weight matrices sliced vertically across GPUs within a server or NVLink domain",
        primary_collectives="AllReduce / AllGather / ReduceScatter on every transformer layer",
        typical_interconnect_domain="Scale-up NVLink / NVSwitch fabric (900 GB/s H100, 1,800 GB/s B200 / NVL72)",
        traffic_pattern_notes="Extremely latency-sensitive; stalls on PCIe (32-64 GB/s) when NVLink is absent (such as on L40S PCIe cards).",
    ),
}


@dataclass(frozen=True)
class LoadBalancingTierSpec:
    tier_code: str
    name: str
    pyramid_level: int
    decision_inputs: str
    reordering_risk: str
    ai_fabric_suitability: str


LOAD_BALANCING_PYRAMID: Dict[str, LoadBalancingTierSpec] = {
    "SLB": LoadBalancingTierSpec(
        tier_code="SLB",
        name="Static Load Balancing (5-Tuple ECMP)",
        pyramid_level=1,
        decision_inputs="Outer packet 5-tuple hash only (Source IP, Dest IP, Protocol, Source Port, Dest Port 4791)",
        reordering_risk="None (all packets of a 5-tuple pinned to one path)",
        ai_fabric_suitability="Poor for AI east-west elephant flows due to low IP/UDP entropy and hash collisions",
    ),
    "DLB": LoadBalancingTierSpec(
        tier_code="DLB",
        name="Dynamic Load Balancing",
        pyramid_level=2,
        decision_inputs="Local switch member-link bandwidth utilization and egress queue buffer utilization",
        reordering_risk="Low (assigns new flows and reassigns flowlets on local link quality changes)",
        ai_fabric_suitability="Good local congestion avoidance, but blind to downstream spine-to-leaf congestion",
    ),
    "GLB": LoadBalancingTierSpec(
        tier_code="GLB",
        name="Global Load Balancing",
        pyramid_level=3,
        decision_inputs="Local link/queue state plus Next-to-Next-Hop (NNH) downstream path quality from spine switches",
        reordering_risk="Low (steers flows/flowlets around downstream spine-to-leaf hotspots)",
        ai_fabric_suitability="High end-to-end congestion avoidance across multi-tier leaf-spine Clos fabrics",
    ),
    "SDLB": LoadBalancingTierSpec(
        tier_code="sDLB",
        name="Selective Dynamic Load Balancing",
        pyramid_level=4,
        decision_inputs="RoCEv2 Base Transport Header (BTH) Read/Write opcodes to detect elephant flows and spray packets",
        reordering_risk="Requires destination NIC out-of-order Packet Sequence Number (PSN) handling",
        ai_fabric_suitability="Highest bandwidth utilization for massive RDMA Read/Write elephant flows",
    ),
}


def compute_tail_latency_jct(
    num_tasks: int,
    normal_task_ms: float,
    straggler_task_ms: float,
    num_stragglers: int = 1,
) -> Dict[str, float]:
    """Compute serial vs parallel Job Completion Time (JCT) under tail latency.

    Follows *AI Data Center Network Design and Technologies* Chapter 1 (Figures 1-4, 1-5, 1-6):
    - In ADC Ch 1's serial example (Figure 1-5): n tasks run serially where tasks take `normal_task_ms`
      (1 ms) and one task `taskX` takes `straggler_task_ms` (1,000 ms = 1 s). The book writes the formula
      `1 second + (n x 1 ms)` = `1.010 seconds` (`1010 ms`) for `n = 10` (and strictly `(n - 1)*normal + straggler`
      = `1009 ms` if `taskX` is one of the `n` tasks; we return both so the exact book figure `1.010 s` and
      exact sum `1.009 s` are both verified).
    - In ADC Ch 1's parallel example (Figure 1-6): n tasks run in parallel across GPUs. 99% (or n-1) finish
      in `normal_task_ms` (1 ms), while `taskX` takes `straggler_task_ms` (1,000 ms = 1 s).
      The fast tasks wait `straggler_task_ms - normal_task_ms` (`999 ms`) for the straggler thread, and
      overall parallel JCT equals `max(task_times) = 1,000 ms` (`1.0 s`), a `1000x` slowdown vs an ideal
      `1 ms` parallel step.
    """
    if num_tasks < 2:
        raise AITrafficModelError("num_tasks must be >= 2")
    if normal_task_ms <= 0 or straggler_task_ms < normal_task_ms:
        raise AITrafficModelError("normal_task_ms must be > 0 and straggler_task_ms >= normal_task_ms")
    if num_stragglers < 1 or num_stragglers >= num_tasks:
        raise AITrafficModelError("num_stragglers must be between 1 and num_tasks - 1")

    normal_count = num_tasks - num_stragglers
    serial_strict_ms = normal_count * normal_task_ms + num_stragglers * straggler_task_ms
    serial_book_formula_ms = num_tasks * normal_task_ms + num_stragglers * straggler_task_ms
    parallel_ideal_ms = normal_task_ms
    parallel_actual_ms = straggler_task_ms
    parallel_wait_ms = straggler_task_ms - normal_task_ms
    parallel_inflation_factor = parallel_actual_ms / parallel_ideal_ms

    return {
        "num_tasks": float(num_tasks),
        "serial_strict_ms": round(serial_strict_ms, 3),
        "serial_book_formula_ms": round(serial_book_formula_ms, 3),
        "serial_book_formula_s": round(serial_book_formula_ms / 1000.0, 3),
        "parallel_ideal_ms": round(parallel_ideal_ms, 3),
        "parallel_actual_ms": round(parallel_actual_ms, 3),
        "parallel_wait_ms": round(parallel_wait_ms, 3),
        "parallel_inflation_factor": round(parallel_inflation_factor, 2),
    }


def compute_synchronous_efficiency(
    compute_ms: float,
    comm_sync_ms: float,
    overlapped_comm_fraction: float = 0.0,
) -> Dict[str, float]:
    """Compute cluster compute efficiency and iteration time with and without overlap.

    Follows:
    - `nvidia-devops` Volume 07 Chapter 1 (§1, line 37): 10,000 GPUs finish calculation in `2 ms`,
      but gradient synchronization takes `50 ms` across the network -> total step time is `52 ms`
      (or `2 / 50 = 4.0%` compute-to-sync ratio quoted in the note, `2 / 52 = 3.85%` of total step time).
    - *AI Systems Performance Engineering* Chapter 4 (§"Achieving Maximal Overlap in Practice", p. 86 & Table 4-1):
      Non-overlapped manual sync takes `compute_ms + comm_sync_ms` (`10 ms + 12 ms = 22 ms`).
      Fully overlapped execution achieves `max(compute_ms, comm_sync_ms)` (`max(10, 12) = 12 ms`),
      saving `10 ms` (`45.45%` reduction vs `22 ms`). In Table 4-1 & Table 4-2, DDP overlap reduces
      total iteration time from `100 ms` to `70 ms` (`30%` faster), raising SM busy from `60%` to `90%`.
    """
    if compute_ms <= 0 or comm_sync_ms < 0:
        raise AITrafficModelError("compute_ms must be > 0 and comm_sync_ms >= 0")
    if not (0.0 <= overlapped_comm_fraction <= 1.0):
        raise AITrafficModelError("overlapped_comm_fraction must be in [0.0, 1.0]")

    serial_step_ms = compute_ms + comm_sync_ms
    exposed_comm_ms = comm_sync_ms * (1.0 - overlapped_comm_fraction)
    overlapped_step_ms = compute_ms + exposed_comm_ms
    ideal_full_overlap_ms = max(compute_ms, comm_sync_ms)

    ratio_compute_to_comm_pct = (compute_ms / comm_sync_ms * 100.0) if comm_sync_ms > 0 else 100.0
    serial_compute_share_pct = (compute_ms / serial_step_ms) * 100.0
    overlapped_compute_share_pct = (compute_ms / overlapped_step_ms) * 100.0
    step_time_reduction_pct = ((serial_step_ms - overlapped_step_ms) / serial_step_ms) * 100.0
    ideal_overlap_reduction_pct = ((serial_step_ms - ideal_full_overlap_ms) / serial_step_ms) * 100.0

    return {
        "serial_step_ms": round(serial_step_ms, 3),
        "overlapped_step_ms": round(overlapped_step_ms, 3),
        "ideal_full_overlap_ms": round(ideal_full_overlap_ms, 3),
        "ratio_compute_to_comm_pct": round(ratio_compute_to_comm_pct, 2),
        "serial_compute_share_pct": round(serial_compute_share_pct, 2),
        "overlapped_compute_share_pct": round(overlapped_compute_share_pct, 2),
        "step_time_reduction_pct": round(step_time_reduction_pct, 2),
        "ideal_overlap_reduction_pct": round(ideal_overlap_reduction_pct, 2),
    }


def compute_collective_bytes_and_steps(
    data_size_bytes: int,
    num_gpus: int,
) -> Dict[str, float]:
    """Compute per-rank byte volumes and step counts for Ring, Tree, and SHARP/NVLS collectives.

    Follows *AI Systems Performance Engineering* Chapter 4 (§"NCCL Communication Algorithms" &
    §"In-Network SHARP Aggregation", lines 394-402, 736-740):
    - Ring Reduce-Scatter or Ring All-Gather: `(num_gpus - 1)` steps; each GPU sends and receives
      `data_size_bytes * (num_gpus - 1) / num_gpus` bytes.
    - Ring All-Reduce (= Reduce-Scatter + All-Gather): `2 * (num_gpus - 1)` steps; each GPU transfers
      `2 * data_size_bytes * (num_gpus - 1) / num_gpus` bytes (`data_size_bytes / num_gpus` per step).
    - Tree All-Reduce: `2 * ceil(log2(num_gpus))` steps (`O(log N)` latency scaling vs `O(N)` for Ring).
    - SHARP / NVLS In-Network Reduce-Scatter (or NVLS multicast All-Gather): switch performs the reduction
      or replication in hardware so each endpoint receives (or sends) only `data_size_bytes / num_gpus` bytes,
      which is `1 / (num_gpus - 1)` of the full-ring per-endpoint volume (`data_size_bytes * (n - 1) / n`).
      When an NVLS multicast All-Gather is overlapped with an in-network Reduce-Scatter, end-to-end phase
      wall time drops by ~`1/2` (`max(t_rs, t_ag)` instead of `t_rs + t_ag`).
    """
    if data_size_bytes <= 0 or num_gpus < 2:
        raise AITrafficModelError("data_size_bytes must be > 0 and num_gpus >= 2")

    chunk_bytes = data_size_bytes / num_gpus
    ring_rs_or_ag_bytes = data_size_bytes * (num_gpus - 1) / num_gpus
    ring_allreduce_bytes = 2.0 * ring_rs_or_ag_bytes
    ring_allreduce_steps = 2 * (num_gpus - 1)
    tree_one_way_steps = math.ceil(math.log2(num_gpus))
    tree_allreduce_steps = 2 * tree_one_way_steps

    sharp_endpoint_rs_bytes = data_size_bytes / num_gpus
    sharp_vs_ring_volume_ratio = sharp_endpoint_rs_bytes / ring_rs_or_ag_bytes  # 1 / (num_gpus - 1)
    sharp_volume_reduction_factor = float(num_gpus - 1)

    return {
        "chunk_bytes": round(chunk_bytes, 2),
        "ring_rs_or_ag_bytes": round(ring_rs_or_ag_bytes, 2),
        "ring_allreduce_bytes": round(ring_allreduce_bytes, 2),
        "ring_allreduce_steps": float(ring_allreduce_steps),
        "tree_allreduce_steps": float(tree_allreduce_steps),
        "sharp_endpoint_rs_bytes": round(sharp_endpoint_rs_bytes, 2),
        "sharp_vs_ring_volume_ratio": round(sharp_vs_ring_volume_ratio, 6),
        "sharp_volume_reduction_factor": round(sharp_volume_reduction_factor, 2),
    }


def evaluate_multinode_pitfalls(
    tensor_mb: float = 400.0,
    gloo_time_ms: float = 200.0,
    nccl_time_ms: float = 4.0,
    dp_step_ms: float = 45.0,
    ddp_step_ms: float = 30.0,
    comm_init_destroy_ms: float = 48.0,
    tiny_allreduce_ms: float = 0.5,
    socket_nthreads: int = 2,
    nsocks_per_thread: int = 2,
) -> Dict[str, object]:
    """Reproduce the multi-node communication pitfall benchmarks from ASP Chapter 4.

    Follows *AI Systems Performance Engineering* Chapter 4:
    1. Gloo (CPU/TCP) vs NCCL (GPUDirect RDMA on 800 Gb/s = 100 GB/s IB) for a `400.0 MB` (`100M` float32)
       All-Reduce (pp. 234-281): Gloo takes `200.00 ms` (`2.0 GB/s`), whereas NCCL takes `4.00 ms` (`100.0 GB/s`),
       a `50x` speedup.
    2. `nn.DataParallel` (`DP`) vs `DistributedDataParallel` (`DDP`) on batch size `512` (`2 x 256`, pp. 429-525):
       `DP` takes `45.00 ms` vs `DDP` `30.00 ms` (`33.33%` faster / `1.5x` speedup).
    3. Repeated `init_process_group` + `destroy_process_group` inside the training loop (Table 4-3, p. 585):
       `48.0 ms` init/destroy + `0.5 ms` all-reduce = `48.5 ms` per iteration vs `0.5 ms` when initialized
       once outside the loop (`98.97%` reduction, i.e. over `98%`).
    4. Socket transport thread-socket product rule (p. 299 & p. 617):
       `NCCL_SOCKET_NTHREADS * NCCL_NSOCKS_PERTHREAD` must not exceed `64`.
    """
    if tensor_mb <= 0 or gloo_time_ms <= 0 or nccl_time_ms <= 0:
        raise AITrafficModelError("tensor_mb and times must be > 0")
    if socket_nthreads <= 0 or nsocks_per_thread <= 0:
        raise AITrafficModelError("socket_nthreads and nsocks_per_thread must be > 0")

    gloo_gbps = (tensor_mb / 1000.0) / (gloo_time_ms / 1000.0)
    nccl_gbps = (tensor_mb / 1000.0) / (nccl_time_ms / 1000.0)
    nccl_vs_gloo_speedup = gloo_time_ms / nccl_time_ms

    ddp_time_saving_pct = ((dp_step_ms - ddp_step_ms) / dp_step_ms) * 100.0

    bad_iter_ms = comm_init_destroy_ms + tiny_allreduce_ms
    good_iter_ms = tiny_allreduce_ms
    init_saving_pct = ((bad_iter_ms - good_iter_ms) / bad_iter_ms) * 100.0

    total_socket_connections = socket_nthreads * nsocks_per_thread
    socket_limit_ok = total_socket_connections <= 64

    return {
        "gloo_gbps": round(gloo_gbps, 2),
        "nccl_gbps": round(nccl_gbps, 2),
        "nccl_vs_gloo_speedup": round(nccl_vs_gloo_speedup, 2),
        "ddp_time_saving_pct": round(ddp_time_saving_pct, 2),
        "bad_iter_ms": round(bad_iter_ms, 2),
        "good_iter_ms": round(good_iter_ms, 2),
        "init_saving_pct": round(init_saving_pct, 2),
        "total_socket_connections": total_socket_connections,
        "socket_limit_ok": socket_limit_ok,
    }


def summarize_llama3_405b_interruptions() -> Dict[str, object]:
    """Summarize Meta's 54-day Llama 3 405B pretraining interruption table (ASP Ch 4, Table 4-4).

    Verifies the exact counts and percentages reported in Table 4-4 (lines 640-716).
    """
    rows = [
        ("Faulty GPU", "GPU", 148, 35.3),
        ("GPU HBM3 memory", "GPU", 72, 17.2),
        ("Software bug", "Dependency", 54, 12.9),
        ("Network switch/cable", "Network", 35, 8.4),
        ("Host maintenance", "Unplanned Maintenance", 32, 7.6),
        ("GPU SRAM memory", "GPU", 19, 4.5),
        ("GPU system processor", "GPU", 17, 4.1),
        ("NIC", "Host", 7, 1.7),
        ("NCCL watchdog timeouts", "Unknown", 7, 1.7),
        ("Silent data corruption", "GPU", 6, 1.4),
        ("GPU thermal interface and sensor", "GPU", 6, 1.4),
        ("SSD", "Host", 3, 0.7),
        ("Power supply", "Host", 3, 0.7),
        ("Server chassis", "Host", 2, 0.5),
        ("IO expansion board", "Host", 2, 0.5),
        ("Dependency", "Dependency", 2, 0.5),
        ("CPU", "Host", 2, 0.5),
        ("System memory", "Host", 2, 0.5),
    ]
    total_interruptions = sum(r[2] for r in rows)
    network_nic_watchdog_count = 35 + 7 + 7  # Network switch/cable (35) + NIC (7) + NCCL watchdog (7) = 49
    gpu_category_count = sum(r[2] for r in rows if r[1] == "GPU")
    return {
        "duration_days": 54,
        "num_categories": len(rows),
        "total_interruptions": total_interruptions,
        "faulty_gpu_count": 148,
        "faulty_gpu_pct": 35.3,
        "network_switch_cable_count": 35,
        "network_switch_cable_pct": 8.4,
        "nic_count": 7,
        "nccl_watchdog_count": 7,
        "network_nic_watchdog_total": network_nic_watchdog_count,
        "gpu_category_count": gpu_category_count,
    }


def audit_rocev2_and_fabric_design(
    udp_dest_port: int,
    load_balancing_mode: str,
    ecn_enabled: bool,
    pfc_enabled: bool,
    spine_oversubscription_ratio: float,
    compute_and_storage_share_switch: bool,
) -> Dict[str, object]:
    """Audit an AI training fabric against ADC Ch 1 & 2 and Volume 07 Ch 1, 11, 12 rules.

    Rules:
    1. RoCEv2 uses UDP destination port `4791` before the InfiniBand Base Transport Header (`BTH`).
    2. Static 5-tuple ECMP (`SLB`) suffers from low entropy on 1:1 / small-group GPU flows where all
       packets share UDP port `4791`; AI fabrics require `DLB`, `GLB`, or `sDLB`.
    3. Lossless RoCEv2 requires `DCQCN`, combining end-to-end `ECN` (`11` marking + `CNP` return packet
       with IP ECN `01`) and link-level `PFC` pause frames.
    4. Dedicated AI training fabrics require `1:1` non-blocking leaf-to-spine bandwidth (`oversubscription <= 1.0`);
       a `2:1` oversubscription saturates during synchronous `AllReduce` bursts (V7 Ch 11 Scenario 2).
    5. Storage traffic (such as `100 GB` checkpoint bursts) must not share compute switches (V7 Ch 11 Scenario 3).
    """
    if udp_dest_port <= 0 or spine_oversubscription_ratio <= 0:
        raise AITrafficModelError("udp_dest_port and spine_oversubscription_ratio must be > 0")
    lb_key = load_balancing_mode.strip().upper()
    if lb_key not in LOAD_BALANCING_PYRAMID:
        raise AITrafficModelError(f"Unknown load_balancing_mode '{load_balancing_mode}'")

    findings: List[str] = []
    if udp_dest_port != 4791:
        findings.append(f"RoCEv2 UDP destination port is {udp_dest_port}; standard IANA/IBTA RoCEv2 port is 4791.")
    if lb_key == "SLB":
        findings.append(
            "Static Load Balancing (SLB 5-tuple ECMP) selected: low entropy on RoCEv2 UDP port 4791 causes "
            "elephant-flow collisions and flowlet pinning; upgrade to DLB, GLB, or sDLB."
        )
    if not (ecn_enabled and pfc_enabled):
        findings.append(
            "Lossless RoCEv2 requires DCQCN with both ECN (end-to-end rate control via CNP) and PFC (link-level pause)."
        )
    if spine_oversubscription_ratio > 1.0:
        findings.append(
            f"Leaf-to-spine oversubscription is {spine_oversubscription_ratio:.1f}:1 (> 1.0:1 non-blocking): "
            "synchronous AllReduce bursts at 400 Gbps/GPU will saturate spine uplinks."
        )
    if compute_and_storage_share_switch:
        findings.append(
            "Storage and GPU compute share the same switch plane: 100 GB checkpoint writes will fill switch "
            "buffers and inject queueing jitter into synchronous collectives."
        )

    return {
        "healthy": len(findings) == 0,
        "load_balancing_tier": LOAD_BALANCING_PYRAMID[lb_key].name,
        "findings": findings,
    }


def size_two_tier_nonblocking_fattree(
    num_servers: int,
    nics_per_server: int,
    switch_radix_ports: int,
) -> Dict[str, int]:
    """Calculate leaf groups, leaf switches, and spine switches for a 2-tier 1:1 non-blocking rail-optimized fat-tree.

    Follows `nvidia-devops` Volume 07 Chapter 11 (Scenario 1, lines 29-45):
    - For `128` DGX H100 servers (`8` compute NICs per server = `1,024` GPUs) and `64`-port Quantum-2 NDR switches:
      - Each Leaf switch uses half its ports (`32`) down to servers and half (`32`) up to Spine switches (`1:1` non-blocking).
      - One Leaf Group of `8` rail-aligned Leaf switches serves `32` servers (`256` GPUs).
      - `128` servers require `128 / 32 = 4` Leaf Groups = `4 * 8 = 32` Leaf switches (`1,024` downlinks, `1,024` uplinks).
      - `1,024` uplinks divided by `64` ports per Spine switch = `16` Spine switches.
    """
    if num_servers <= 0 or nics_per_server <= 0 or switch_radix_ports <= 0 or switch_radix_ports % 2 != 0:
        raise AITrafficModelError("Inputs must be positive and switch_radix_ports must be even")

    downlinks_per_leaf = switch_radix_ports // 2
    uplinks_per_leaf = switch_radix_ports // 2
    if num_servers % downlinks_per_leaf != 0:
        raise AITrafficModelError("num_servers must be a multiple of switch_radix_ports // 2 for symmetric leaf groups")

    num_leaf_groups = num_servers // downlinks_per_leaf
    leaves_per_group = nics_per_server
    total_leaf_switches = num_leaf_groups * leaves_per_group
    total_gpus = num_servers * nics_per_server
    total_uplinks = total_leaf_switches * uplinks_per_leaf
    if total_uplinks % switch_radix_ports != 0:
        raise AITrafficModelError("total_uplinks must be divisible by switch_radix_ports")
    total_spine_switches = total_uplinks // switch_radix_ports

    return {
        "total_gpus": total_gpus,
        "downlinks_per_leaf": downlinks_per_leaf,
        "uplinks_per_leaf": uplinks_per_leaf,
        "num_leaf_groups": num_leaf_groups,
        "leaves_per_group": leaves_per_group,
        "total_leaf_switches": total_leaf_switches,
        "total_uplinks": total_uplinks,
        "total_spine_switches": total_spine_switches,
    }
