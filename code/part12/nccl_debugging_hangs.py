#!/usr/bin/env python3
"""Chapter 12.18 model: NCCL debugging: hangs, timeouts and errors.

Encodes the verifiable mathematical models, log parsers, root-cause classifiers,
PyTorch Flight Recorder ring buffer analyzers, ncclResult_t error code taxonomies,
container /dev/shm exhaustion calculators, and AI Systems Performance Engineering
Chapter 4 reliability and communicator lifecycle calculations from:
- *AI Systems Performance Engineering* (`ai-systems-performance-engineering`),
  Chapter 4 (*Tuning Distributed Networking Communication*):
  - All 6 multinode pitfalls (`Gloo` `200.0 ms` / `2.0 GB/s` vs `NCCL` `4.0 ms` /
    `100.0 GB/s` on `400 MB` `800G` IB; mismatched `NCCL` versions;
    `/proc/sys/net/ipv4/ip_local_port_range` `50000 51000`; insufficient bandwidth
    and `NCCL_SOCKET_NTHREADS * NCCL_NSOCKS_PERTHREAD <= 64`; stragglers; `UCX`
    caching allocator fragmentation `0.800 GB -> 1.040 GB -> 1.240 GB` reserved
    vs `0.000 GB` allocated).
  - All 6 communicator lifecycle & environment gotchas (Table 4-3 `48.0 ms`
    repeated `init_process_group` + `0.5 ms` `AllReduce` = `48.5 ms -> 0.5 ms`
    `98.97%` reduction; `ncclGroupStart`/`ncclGroupEnd`; `NCCL_BUFFSIZE=4194304`
    (`4 MB`), `NCCL_P2P_DISABLE=1`, `NCCL_SHM_DISABLE=1`; `NCCL_IGNORE_CPU_AFFINITY=1`;
    ignoring `NCCL WARN` logs; Table 4-4 Meta `Llama 3 405B` `54`-day `419`
    interruption breakdown across `16,384` `H100` GPUs).
  - `NCCL_PROFILER_PLUGIN` `5` callbacks (`init`, `startEvent`, `stopEvent`,
    `recordEventState`, `finalize`) and `32`-bit event activation mask.
- `nvidia-devops` Volume 20 (`chapter-01` through `chapter-12`, `index.md`, and
  `labs/lab-01` through `lab-04`) and Volume 10 Chapter 15
  (`15-senior-deep-dive-3-mpi-and-nccl-joint-debugging.md` /
  `15-nccl-and-distributed-training-failures.md`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence


class NCCLDebugModelError(ValueError):
    """Raised when invalid parameters or trace entries are supplied."""


@dataclass(frozen=True)
class NcclResultSpec:
    code: int
    enum_name: str
    log_string: str
    primary_layer: str
    typical_triggers: str
    first_diagnostic_command: str


NCCL_RESULT_CODES: Dict[int, NcclResultSpec] = {
    0: NcclResultSpec(
        code=0,
        enum_name="ncclSuccess",
        log_string="no error",
        primary_layer="None",
        typical_triggers="Collective or communicator call succeeded without error",
        first_diagnostic_command="None",
    ),
    1: NcclResultSpec(
        code=1,
        enum_name="ncclUnhandledCudaError",
        log_string="unhandled cuda error",
        primary_layer="CUDA runtime / GPU silicon (Xid)",
        typical_triggers=(
            "Prior asynchronous CUDA kernel fault (Xid 13, 31, 43, 48, 74, 79, 94, 95), "
            "OOM, or invalid device context before/during NCCL launch"
        ),
        first_diagnostic_command="dmesg -T | grep -i xid; CUDA_LAUNCH_BLOCKING=1",
    ),
    2: NcclResultSpec(
        code=2,
        enum_name="ncclSystemError",
        log_string="unhandled system error",
        primary_layer="OS / Container / Verbs / NVML / Shared Memory",
        typical_triggers=(
            "/dev/shm exhaustion (Docker/K8s 64 MiB default -> Error 28 No space left on device), "
            "memlock limit (ibv_reg_mr / ibv_create_qp failed), TCP bootstrap port exhaustion, "
            "or NVLink/PCIe hardware link failure"
        ),
        first_diagnostic_command="df -h /dev/shm; ulimit -l; NCCL_DEBUG=INFO",
    ),
    3: NcclResultSpec(
        code=3,
        enum_name="ncclInternalError",
        log_string="internal error",
        primary_layer="NCCL internal state machine / P2P / NVSwitch / Version mismatch",
        typical_triggers=(
            "Mismatched bundled vs system libnccl versions, corrupted proxy ring buffer, "
            "broken P2P BAR1 mapping, or unexpected token in NCCL_ALGO (NCCL 2.24+)"
        ),
        first_diagnostic_command="python3 -c 'import torch; print(torch.cuda.nccl.version())'; nvidia-smi topo -m",
    ),
    4: NcclResultSpec(
        code=4,
        enum_name="ncclInvalidArgument",
        log_string="invalid argument",
        primary_layer="Application / Framework API call",
        typical_triggers=(
            "Null sendbuff/recvbuff pointer, invalid rank (< 0 or >= nranks), "
            "unsupported ncclDataType_t or ncclRedOp_t, or negative count"
        ),
        first_diagnostic_command="TORCH_DISTRIBUTED_DEBUG=DETAIL",
    ),
    5: NcclResultSpec(
        code=5,
        enum_name="ncclInvalidUsage",
        log_string="invalid usage",
        primary_layer="Application collective ordering / CUDA stream / Buffer registration",
        typical_triggers=(
            "Mismatched collective sequence across ranks, duplicate GPU device per communicator, "
            "asymmetric ncclCommRegister usage, or invalid ncclGroupStart/ncclGroupEnd nesting"
        ),
        first_diagnostic_command="NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=COLL,INIT",
    ),
    6: NcclResultSpec(
        code=6,
        enum_name="ncclRemoteError",
        log_string="remote process exited or there was a network error",
        primary_layer="Peer Rank Process / RDMA Fabric Transport",
        typical_triggers=(
            "Peer rank crashed (OOM, SIGKILL, Xid 79/48/95), remote QP retry/RNR timeout exceeded "
            "(local_ack_timeout_err, rnr_nak_retry_err), or link flap on remote HCA/RoCE switch"
        ),
        first_diagnostic_command="ncclras -v; rdma statistic; dmesg -T | grep -i xid",
    ),
}


@dataclass(frozen=True)
class WatchdogLogReport:
    reporting_rank: int
    world_size: int
    op_type: str
    seq_num: int
    timeout_ms: int
    work_ran_sec: float
    classification: str
    lagging_ranks: List[int]
    dead_ranks: List[int]
    recommended_action: str


WATCHDOG_REGEX = re.compile(
    r"\[Rank (?P<rank>\d+)\]\s*Watchdog caught collective operation timeout:\s*"
    r"WorkNCCL\((?:SeqNum=(?P<seq>\d+),\s*)?OpType=(?P<op>[A-Za-z0-9_]+)"
    r"(?:,\s*NumelIn=\d+,\s*NumelOut=\d+)?,\s*Timeout\(ms\)=(?P<timeout>\d+)\)\s*"
    r"ran for (?P<ran>[0-9.]+)\s*milliseconds"
)


def parse_watchdog_and_classify_hang(
    watchdog_log_line: str,
    world_size: int,
    rank_op_counts: Dict[int, int],
    rank_op_types: Optional[Dict[int, str]] = None,
    dead_or_xid_ranks: Optional[Sequence[int]] = None,
    fabric_retry_errors: int = 0,
    rank_sm_util_pct: Optional[Dict[int, float]] = None,
) -> WatchdogLogReport:
    """Parse a PyTorch ProcessGroupNCCL watchdog timeout line and classify root cause.

    Distinguishes four canonical failure classes:
    1. 'dead_rank_or_gpu_xid': One or more ranks exited or hit a fatal GPU Xid (e.g. Xid 79/48/95).
    2. 'rank_desync_divergent_collective': Ranks reached the same sequence window with
       mismatched OpTypes or permanently divergent non-converging opCounts (if/else bug).
    3. 'upstream_straggler_starvation': One or a few alive ranks lag behind at a lower
       opCount with low SM utilization (e.g. 2% SM util, 47.31s dataloader stall on a
       96% full storage volume or 187G vs 41G uneven shard) or thermal throttle.
    4. 'fabric_transport_drop': All ranks entered the exact same collective SeqNum and
       OpType, processes and GPUs are alive, and RDMA retry/timeout counters are rising.
    """
    if world_size <= 0:
        raise NCCLDebugModelError("world_size must be positive")
    match = WATCHDOG_REGEX.search(watchdog_log_line)
    if not match:
        raise NCCLDebugModelError(f"Unrecognized watchdog log format: {watchdog_log_line!r}")

    reporting_rank = int(match.group("rank"))
    seq_num = int(match.group("seq") or 0)
    op_type = match.group("op")
    timeout_ms = int(match.group("timeout"))
    work_ran_sec = round(float(match.group("ran")) / 1000.0, 3)

    if len(rank_op_counts) != world_size:
        raise NCCLDebugModelError("rank_op_counts must contain an entry for every rank in world_size")

    dead_list = sorted(set(dead_or_xid_ranks or []))
    max_seq = max(rank_op_counts.values())
    min_seq = min(rank_op_counts.values())
    lagging = sorted(r for r, c in rank_op_counts.items() if c < max_seq)

    op_types = rank_op_types or {}
    distinct_ops_at_front = len(set(op_types.values())) > 1 if op_types else False

    if dead_list:
        classification = "dead_rank_or_gpu_xid"
        action = (
            f"Inspect dmesg/Xid and container exit status on dead rank(s) {dead_list}; "
            "cordon/reset if Tier 3 Xid (48, 61, 62, 64, 79, 95) and resume from checkpoint."
        )
    elif distinct_ops_at_front:
        classification = "rank_desync_divergent_collective"
        action = (
            "Fix divergent conditional collective path in application code (e.g. rank-gated "
            "all_reduce or missing find_unused_parameters); raising timeout will never resolve this."
        )
    elif lagging:
        sm_map = rank_sm_util_pct or {}
        low_sm_laggards = [r for r in lagging if sm_map.get(r, 0.0) < 15.0]
        if len(set(rank_op_counts.values())) >= 3 and not low_sm_laggards:
            classification = "rank_desync_divergent_collective"
            action = (
                f"Multiple non-converging opCounts ({min_seq}..{max_seq}) indicate rank desynchronization; "
                "inspect Flight Recorder trace buffer for divergent collective call sites."
            )
        else:
            classification = "upstream_straggler_starvation"
            action = (
                f"Investigate lagging rank(s) {lagging} stuck at opCount {min_seq} (vs {max_seq}): "
                "check CPU dataloader stall (e.g. uneven shard or full disk), NUMA binding, or GPU thermal/power throttle."
            )
    elif fabric_retry_errors > 0 or min_seq == max_seq:
        classification = "fabric_transport_drop"
        action = (
            f"All {world_size} ranks entered SeqNum {max_seq} ({op_type}); check RDMA fabric "
            "(ibstat, perfquery, rdma statistic, ethtool -S PFC/pause/CNP, and per-rail ib_write_bw)."
        )
    else:
        classification = "unknown"
        action = "Collect ncclras -v and Flight Recorder dump across all ranks."

    return WatchdogLogReport(
        reporting_rank=reporting_rank,
        world_size=world_size,
        op_type=op_type,
        seq_num=seq_num,
        timeout_ms=timeout_ms,
        work_ran_sec=work_ran_sec,
        classification=classification,
        lagging_ranks=lagging,
        dead_ranks=dead_list,
        recommended_action=action,
    )


@dataclass(frozen=True)
class FlightRecorderEntry:
    rank: int
    pg_name: str
    seq_id: int
    op_type: str
    tensor_bytes: int
    state: str  # "scheduled", "started", "completed"
    duration_ms: float


def analyze_flight_recorder_buffer(
    entries: Sequence[FlightRecorderEntry],
    world_size: int,
    buffer_capacity: int = 2000,
) -> Dict[str, object]:
    """Analyze PyTorch Flight Recorder (`TORCH_FR_BUFFER_SIZE`) ring buffer entries.

    Identifies the target `seq_id` where the collective stalled, which ranks entered
    that `seq_id`, which rank(s) never entered `AllReduce` `seq_id` k (the root-cause
    missing rank(s)), whether any rank entered with a mismatched `op_type` or
    `tensor_bytes`, and the ring-buffer memory footprint.
    """
    if world_size <= 1:
        raise NCCLDebugModelError("world_size must be >= 2")
    if buffer_capacity <= 0:
        raise NCCLDebugModelError("buffer_capacity must be positive")
    if not entries:
        raise NCCLDebugModelError("Flight Recorder entries cannot be empty")

    by_seq: Dict[int, Dict[int, FlightRecorderEntry]] = {}
    highest_completed_per_rank: Dict[int, int] = {r: -1 for r in range(world_size)}
    highest_seen_per_rank: Dict[int, int] = {r: -1 for r in range(world_size)}

    for e in entries:
        if e.rank < 0 or e.rank >= world_size:
            raise NCCLDebugModelError(f"Invalid rank {e.rank} for world_size {world_size}")
        by_seq.setdefault(e.seq_id, {})[e.rank] = e
        if e.seq_id > highest_seen_per_rank[e.rank]:
            highest_seen_per_rank[e.rank] = e.seq_id
        if e.state == "completed" and e.seq_id > highest_completed_per_rank[e.rank]:
            highest_completed_per_rank[e.rank] = e.seq_id

    target_seq_id = max(by_seq.keys())
    seq_map = by_seq[target_seq_id]
    present_ranks = sorted(seq_map.keys())
    missing_ranks = sorted(set(range(world_size)) - set(present_ranks))

    ops_at_target = sorted({e.op_type for e in seq_map.values()})
    sizes_at_target = sorted({e.tensor_bytes for e in seq_map.values()})
    op_mismatch = len(ops_at_target) > 1
    size_mismatch = len(sizes_at_target) > 1

    if op_mismatch or size_mismatch:
        diagnosis = "collective_desync_mismatch"
    elif missing_ranks:
        diagnosis = "missing_rank_never_entered"
    else:
        incomplete = sorted(r for r, e in seq_map.items() if e.state != "completed")
        diagnosis = "in_flight_fabric_or_kernel_stall" if incomplete else "all_completed"

    return {
        "world_size": world_size,
        "buffer_capacity": buffer_capacity,
        "target_seq_id": target_seq_id,
        "present_ranks": present_ranks,
        "missing_ranks": missing_ranks,
        "ops_at_target": ops_at_target,
        "sizes_at_target": sizes_at_target,
        "op_mismatch": op_mismatch,
        "size_mismatch": size_mismatch,
        "highest_seen_per_rank": highest_seen_per_rank,
        "highest_completed_per_rank": highest_completed_per_rank,
        "diagnosis": diagnosis,
    }


def evaluate_shm_Requirement(
    local_ranks: int = 8,
    num_channels: int = 16,
    buffsize_bytes: int = 4_194_304,
    num_communicators: int = 2,
    container_shm_mib: float = 64.0,
    control_overhead_mib_per_rank: float = 2.0,
) -> Dict[str, object]:
    """Calculate NCCL /dev/shm allocation vs Docker/Kubernetes default 64 MiB limit.

    When intra-node shared-memory transport or host staging allocates channel buffers
    across `local_ranks` and `num_communicators` inside a container with the default
    64 MiB `/dev/shm`, `ncclSystemError` (code 2, `Error 28: No space left on device`
    while creating `/dev/shm/nccl-*`) is raised during communicator initialization or
    when falling back to SHM.
    """
    if local_ranks <= 0 or num_channels <= 0 or buffsize_bytes <= 0 or num_communicators <= 0:
        raise NCCLDebugModelError("All rank, channel, buffer, and communicator counts must be positive")
    if container_shm_mib <= 0:
        raise NCCLDebugModelError("container_shm_mib must be positive")

    channel_bytes_per_comm = local_ranks * num_channels * buffsize_bytes
    total_channel_mib = (channel_bytes_per_comm * num_communicators) / (1024.0 * 1024.0)
    control_mib = local_ranks * control_overhead_mib_per_rank * num_communicators
    required_shm_mib = round(total_channel_mib + control_mib, 2)
    exhausted = required_shm_mib > container_shm_mib

    return {
        "local_ranks": local_ranks,
        "num_channels": num_channels,
        "buffsize_mib": round(buffsize_bytes / (1024.0 * 1024.0), 2),
        "num_communicators": num_communicators,
        "container_shm_mib": container_shm_mib,
        "required_shm_mib": required_shm_mib,
        "shm_exhausted": exhausted,
        "nccl_result_code": 2 if exhausted else 0,
        "nccl_result_enum": "ncclSystemError" if exhausted else "ncclSuccess",
        "errno_code": 28 if exhausted else 0,
        "recommended_shm_gib": 16 if local_ranks >= 8 else 8,
    }


def evaluate_asp_ch4_tables_and_pitfalls() -> Dict[str, object]:
    """Verify exact calculations from ASP Chapter 4 Tables 4-1, 4-2, 4-3, 4-4 and 6+6 pitfalls.

    Covers:
    - Table 4-1 & 4-2: 100 ms (60% SM busy) -> 70 ms (90% SM busy) = 30.0% faster with ~50% overlap;
      10.0 ms compute + 12.0 ms AllReduce = 22.0 ms serial vs 12.0 ms overlapped (45.45% savings);
      DP 45.0 ms vs DDP 30.0 ms (33.33% faster, 25 MiB default bucket_cap_mb).
    - Multinode Pitfall #1: Gloo 400 MB AllReduce in 200.00 ms (2.0 GB/s) vs NCCL 4.00 ms (100.0 GB/s, 50x).
    - Multinode Pitfall #3 & #4: ephemeral port range 50000..51000 (1,001 ports);
      socket limit NCCL_SOCKET_NTHREADS * NCCL_NSOCKS_PERTHREAD <= 64 (e.g. 2 * 2 = 4);
      multi-rail 2 x 800 Gbps = 1.6 Tbps, 4 x 800 Gbps = 3.2 Tbps.
    - Multinode Pitfall #6: UCX/RDMA caching allocator memory_reserved growth
      0.800 GB (Iter 00) -> 1.040 GB (Iter 01, +40 MB +200 MB) -> 1.240 GB (Iter 02..10)
      while memory_allocated drops to 0.000 GB.
    - Table 4-3 (Communicator Pitfall #1 & #2): repeated init_process_group + destroy = 48.0 ms
      per iter + 0.5 ms AllReduce = 48.5 ms -> 0.5 ms when initialized once (98.97% reduction).
    - Table 4-4 (Communicator Pitfall #6): Meta Llama 3 405B 54-day pretraining on 16,384 H100 GPUs,
      419 total unexpected interruptions across 18 categories.
    - NCCL Profiler Plugin API: 5 callbacks and 32-bit event activation mask.
    """
    # Table 4-3 repeated init_process_group calculation
    init_destroy_ms = 48.0
    allreduce_1elem_ms = 0.5
    before_iter_ms = init_destroy_ms + allreduce_1elem_ms
    after_iter_ms = allreduce_1elem_ms
    init_reduction_pct = round(100.0 * (before_iter_ms - after_iter_ms) / before_iter_ms, 2)

    # Gloo vs NCCL 400 MB on 800 Gbps (100 GB/s) IB
    data_mb = 400.0
    gloo_ms = 200.0
    nccl_ms = 4.0
    gloo_gbps = round((data_mb / 1000.0) / (gloo_ms / 1000.0), 2)
    nccl_gbps = round((data_mb / 1000.0) / (nccl_ms / 1000.0), 2)
    nccl_speedup_x = round(gloo_ms / nccl_ms, 1)

    # Overlap & DP vs DDP
    serial_ms = 10.0 + 12.0
    overlapped_ms = 12.0
    overlap_reduction_pct = round(100.0 * (serial_ms - overlapped_ms) / serial_ms, 2)
    topo_before_ms = 100.0
    topo_after_ms = 70.0
    topo_reduction_pct = round(100.0 * (topo_before_ms - topo_after_ms) / topo_before_ms, 1)
    dp_ms = 45.0
    ddp_ms = 30.0
    ddp_speedup_pct = round(100.0 * (dp_ms - ddp_ms) / dp_ms, 2)

    # Table 4-4 Meta Llama 3 405B 54-day interruption breakdown on 16,384 H100 GPUs
    llama3_table_4_4 = [
        ("Faulty GPU", "GPU", 148, 30.1),
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
    total_interruptions = sum(row[2] for row in llama3_table_4_4)
    gpu_category_count = sum(row[2] for row in llama3_table_4_4 if row[1] == "GPU")
    gpu_category_pct = round(100.0 * gpu_category_count / total_interruptions, 1)
    network_nic_watchdog_count = 35 + 7 + 7
    network_nic_watchdog_pct = round(100.0 * network_nic_watchdog_count / total_interruptions, 1)
    mtbi_hours = round((54.0 * 24.0) / total_interruptions, 2)
    single_gpu_fleet_share_pct = round(100.0 / 16384.0, 4)

    return {
        "table_4_3_before_ms": before_iter_ms,
        "table_4_3_after_ms": after_iter_ms,
        "table_4_3_init_destroy_ms": init_destroy_ms,
        "table_4_3_allreduce_ms": allreduce_1elem_ms,
        "table_4_3_reduction_pct": init_reduction_pct,
        "gloo_400mb_ms": gloo_ms,
        "gloo_400mb_gbps": gloo_gbps,
        "nccl_400mb_ms": nccl_ms,
        "nccl_400mb_gbps": nccl_gbps,
        "nccl_over_gloo_speedup_x": nccl_speedup_x,
        "serial_step_ms": serial_ms,
        "overlapped_step_ms": overlapped_ms,
        "overlap_reduction_pct": overlap_reduction_pct,
        "table_4_2_before_ms": topo_before_ms,
        "table_4_2_after_ms": topo_after_ms,
        "table_4_2_reduction_pct": topo_reduction_pct,
        "table_4_2_sm_busy_before_pct": 60,
        "table_4_2_sm_busy_after_pct": 90,
        "dp_step_ms": dp_ms,
        "ddp_step_ms": ddp_ms,
        "ddp_speedup_pct": ddp_speedup_pct,
        "ddp_default_bucket_cap_mib": 25,
        "socket_max_connections": 64,
        "two_nic_socket_connections": 2 * 2,
        "ephemeral_port_range": (50000, 51000),
        "ucx_reserved_gb_progression": [0.800, 1.040, 1.240],
        "ucx_allocated_after_free_gb": 0.000,
        "table_4_4_days": 54,
        "table_4_4_gpus": 16384,
        "table_4_4_single_gpu_fleet_share_pct": single_gpu_fleet_share_pct,
        "table_4_4_total_interruptions": total_interruptions,
        "table_4_4_gpu_category_count": gpu_category_count,
        "table_4_4_gpu_category_pct": gpu_category_pct,
        "table_4_4_faulty_gpu_count": 148,
        "table_4_4_faulty_gpu_pct": 30.1,
        "table_4_4_hbm3_count": 72,
        "table_4_4_hbm3_pct": 17.2,
        "table_4_4_sw_bug_count": 54,
        "table_4_4_sw_bug_pct": 12.9,
        "table_4_4_switch_cable_count": 35,
        "table_4_4_switch_cable_pct": 8.4,
        "table_4_4_host_maint_count": 32,
        "table_4_4_host_maint_pct": 7.6,
        "table_4_4_sram_count": 19,
        "table_4_4_sram_pct": 4.5,
        "table_4_4_gsp_count": 17,
        "table_4_4_gsp_pct": 4.1,
        "table_4_4_nic_count": 7,
        "table_4_4_nic_pct": 1.7,
        "table_4_4_nccl_watchdog_count": 7,
        "table_4_4_nccl_watchdog_pct": 1.7,
        "table_4_4_sdc_count": 6,
        "table_4_4_sdc_pct": 1.4,
        "table_4_4_thermal_count": 6,
        "table_4_4_thermal_pct": 1.4,
        "table_4_4_network_nic_watchdog_count": network_nic_watchdog_count,
        "table_4_4_network_nic_watchdog_pct": network_nic_watchdog_pct,
        "table_4_4_mtbi_hours": mtbi_hours,
        "profiler_plugin_callbacks": [
            "init",
            "startEvent",
            "stopEvent",
            "recordEventState",
            "finalize",
        ],
        "profiler_plugin_event_mask_bits": 32,
    }


def evaluate_cross_layer_and_xid_triage() -> Dict[str, object]:
    """Encode Volume 20 & Volume 10 Ch 15 cross-layer triage metrics and Xid classifications.

    Covers:
    - Volume 20 Ch 2 & Ch 5 & Ch 7 Xid 3-tier classification:
      - Tier 1 (informational / self-healing): 45, 63, 92
      - Tier 2 (process / app recoverable unless recurring): 13, 31, 32, 43, 94
      - Tier 3 (GPU-level drain immediately): 48, 61, 62, 64, 79, 95
      - Link-specific NVLink error: 74 (paired with dcgmi nvlink -e CRC 184213, replay 92104, recovery 12)
    - Volume 20 Ch 3: rank 3 stuck at opCount 4820 while ranks 0..2 at 4821;
      SM util 2%, temp 61C, power 78.3W; batch fetch 47.31s; storage 480G/500G (96%),
      shard-3 187G vs shard-0 41G (4.56x imbalance).
    - Volume 20 Ch 6, 8, 9, 10: H100 boost 1980 MHz -> 1833 MHz (~7.4% drop) at 85C;
      DVFS oscillation 1980 -> 1200 -> 800 MHz (P0 vs P2/P8); PSU cap 300W -> 200W (198W draw).
    - Volume 20 Ch 11: straggler iteration times [125.3, 126.1, 1250.5, 124.8] ms
      (min 124.8 ms, max 1250.5 ms, ratio 10.02x; alert threshold > 1.2x).
    - Volume 20 Ch 12: layer-by-layer breakdown totaling 750.00 ms
      (data_load_cpu 450.00 ms = 60.0%, allreduce_network 150.00 ms = 20.0%,
      backward_gpu 60.00 ms = 8.0%, forward_gpu 30.00 ms = 4.0%,
      data_transfer_pcie 10.00 ms = 1.3%, optimizer_gpu 10.00 ms = 1.3%,
      loss_gpu 8.00 ms = 1.1%); profiler Heisenbug 500 -> 450 (10%) -> 250 (50%) samples/sec.
    - Volume 10 Ch 15: NCCL 2.24+ RAS port 28028 (`ncclras -v`), NCCL 2.31+ `NCCL_RUN_DIAGNOSTICS=1`
      (`52/56` P2P checks), Cumulus Linux 5.12 RoCE defaults (PFC priority 3, RoCE DSCP 26 -> TC 3,
      CNP DSCP 48 -> TC 6, UDP 4791).
    """
    iter_times_ms = [125.3, 126.1, 1250.5, 124.8]
    min_iter = min(iter_times_ms)
    max_iter = max(iter_times_ms)
    imbalance_ratio = round(max_iter / min_iter, 2)

    shard3_gb = 187.0
    shard0_gb = 41.0
    shard_ratio = round(shard3_gb / shard0_gb, 2)

    return {
        "xid_tier_1": [45, 63, 92],
        "xid_tier_2": [13, 31, 32, 43, 94],
        "xid_tier_3": [48, 61, 62, 64, 79, 95],
        "xid_nvlink": 74,
        "nvlink_gpu2_link2_crc_errors": 184213,
        "nvlink_gpu2_link2_replay_errors": 92104,
        "nvlink_gpu2_link2_recovery_errors": 12,
        "ch03_fast_op_count": 4821,
        "ch03_stalled_op_count": 4820,
        "ch03_rank3_sm_util_pct": 2,
        "ch03_rank3_temp_c": 61,
        "ch03_rank3_power_w": 78.3,
        "ch03_batch_fetch_sec": 47.31,
        "ch03_pv_used_pct": 96,
        "ch03_shard3_to_shard0_ratio": shard_ratio,
        "ch11_iter_times_ms": iter_times_ms,
        "ch11_min_ms": min_iter,
        "ch11_max_ms": max_iter,
        "ch11_imbalance_ratio": imbalance_ratio,
        "ch12_data_load_pct": round(100.0 * 450.0 / 750.0, 1),
        "ch12_allreduce_pct": round(100.0 * 150.0 / 750.0, 1),
        "ch12_backward_pct": round(100.0 * 60.0 / 750.0, 1),
        "ch12_heisenbug_smi_overhead_pct": round(100.0 * (500.0 - 450.0) / 500.0, 1),
        "ch12_heisenbug_nsys_overhead_pct": round(100.0 * (500.0 - 250.0) / 500.0, 1),
        "ras_default_port": 28028,
        "roce_data_dscp": 26,
        "roce_pfc_priority": 3,
        "roce_cnp_dscp": 48,
        "roce_cnp_priority": 6,
        "roce_udp_port": 4791,
    }


if __name__ == "__main__":
    asp = evaluate_asp_ch4_tables_and_pitfalls()
    shm = evaluate_shm_Requirement()
    triage = evaluate_cross_layer_and_xid_triage()
    print(
        f"ASP Ch4 Table 4-3 reduction: {asp['table_4_3_reduction_pct']}%, "
        f"Table 4-4 Llama 3 405B interruptions: {asp['table_4_4_total_interruptions']} "
        f"(MTBI={asp['table_4_4_mtbi_hours']}h)"
    )
    print(
        f"Container /dev/shm check: required={shm['required_shm_mib']} MiB vs "
        f"limit={shm['container_shm_mib']} MiB -> {shm['nccl_result_enum']}"
    )
    print(
        f"Cross-layer straggler ratio: {triage['ch11_imbalance_ratio']}x, "
        f"RAS port: {triage['ras_default_port']}"
    )
