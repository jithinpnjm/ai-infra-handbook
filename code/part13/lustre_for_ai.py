#!/usr/bin/env python3
"""Deterministic modeling and diagnostics for Chapter 13.4: Lustre for AI.

Covers:
1. Progressive File Layout (PFL) + Data-on-MDT (DoM) component selection and
   round-robin RAID0 OST chunk distribution (`(offset // stripe_size) % stripe_count`).
2. Distributed Namespace (DNE Phase 1 & Phase 2) multi-MDT metadata IOPS scaling,
   epoch-start latency estimation, and dataset shard repackaging (10M files -> 100 shards).
3. Client RPC bandwidth-delay-product (BDP) calculator:
   `B_max = (max_rpcs_in_flight * max_pages_per_rpc * page_size_bytes) / rtt_sec`
   across single and multiple OSTs, plus GPUDirect Storage (`gdsio` `-x 2` vs `-x 0`).
4. Distributed AI checkpoint write modeling: N-to-1 shared file LDLM lock contention
   and unaligned stripe splitting vs aligned N-to-1 (`stripe_count = -1`) and N-to-N
   per-rank sharded checkpoints (`stripe_count = 1..4`).
5. LNet multi-rail (`o2ib` / `RoCEv2` / `tcp` port 988) NID health, NUMA/PCIe locality,
   OST capacity balance (`lfs df -h`), and OSS RAM sizing (`400 MB + 600 MB + 1.5 MB * N_threads`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

KiB = 1024
MiB = 1024 * 1024
GiB = 1024 * 1024 * 1024


@dataclass(frozen=True)
class PFLComponent:
    """One component in a Lustre Progressive File Layout (PFL)."""

    end_bytes: Optional[int]  # None represents -E -1 (eof)
    layout_type: str  # "mdt" (DoM) or "raid0"
    stripe_count: int  # -1 means all available OSTs
    stripe_size_bytes: int


@dataclass(frozen=True)
class LNetRailNID:
    """One LNet Network Identifier (NID) rail on a GPU compute node or OSS."""

    nid: str
    protocol: str  # "o2ib" or "tcp"
    net_index: int
    interface: str
    numa_node: int
    gpu_numa_node: int
    link_up: bool
    rate_gbps: float
    peer_credits: int
    tx_Queued_errors: int = 0
    rx_drop_errors: int = 0


def default_ai_pfl_layout() -> List[PFLComponent]:
    """Return the standard 4-tier AI PFL + DoM composite layout:
    - [0, 1 MiB): DoM on MDT (-E 1M -L mdt)
    - [1 MiB, 64 MiB): 1 OST, 1 MiB stripe (-E 64M -c 1 -S 1M)
    - [64 MiB, 4 GiB): 4 OSTs, 4 MiB stripe (-E 4G -c 4 -S 4M)
    - [4 GiB, EOF): all OSTs (-1), 4 MiB stripe (-E -1 -c -1 -S 4M)
    """
    return [
        PFLComponent(end_bytes=1 * MiB, layout_type="mdt", stripe_count=1, stripe_size_bytes=1 * MiB),
        PFLComponent(end_bytes=64 * MiB, layout_type="raid0", stripe_count=1, stripe_size_bytes=1 * MiB),
        PFLComponent(end_bytes=4 * GiB, layout_type="raid0", stripe_count=4, stripe_size_bytes=4 * MiB),
        PFLComponent(end_bytes=None, layout_type="raid0", stripe_count=-1, stripe_size_bytes=4 * MiB),
    ]


def evaluate_pfl_dom_file(
    file_size_bytes: int,
    components: Sequence[PFLComponent],
    total_osts: int = 24,
    start_ost_index: int = 0,
) -> Dict[str, object]:
    """Instantiate PFL/DoM components for a file of `file_size_bytes` and compute
    MDT (DoM) bytes, per-OST bytes, active components, and RPC object fans.
    """
    if file_size_bytes < 0 or total_osts <= 0:
        raise ValueError("file_size_bytes must be >= 0 and total_osts > 0")

    mdt_dom_bytes = 0
    ost_bytes = [0] * total_osts
    instantiated: List[Dict[str, object]] = []
    comp_start = 0

    for idx, comp in enumerate(components):
        if comp_start >= file_size_bytes and file_size_bytes > 0:
            break
        comp_end = file_size_bytes if comp.end_bytes is None else min(comp.end_bytes, file_size_bytes)
        if file_size_bytes == 0 and idx == 0:
            comp_end = 0
        if comp_end < comp_start:
            continue

        span_bytes = comp_end - comp_start
        eff_count = total_osts if comp.stripe_count == -1 else min(comp.stripe_count, total_osts)

        if comp.layout_type == "mdt":
            mdt_dom_bytes += span_bytes
            touched_osts: List[int] = []
        else:
            touched_set = set()
            rel_off = 0
            while rel_off < span_bytes:
                chunk_len = min(comp.stripe_size_bytes, span_bytes - rel_off)
                chunk_idx = rel_off // comp.stripe_size_bytes
                ost_slot = (start_ost_index + (chunk_idx % eff_count)) % total_osts
                ost_bytes[ost_slot] += chunk_len
                touched_set.add(ost_slot)
                rel_off += chunk_len
            touched_osts = sorted(touched_set)

        instantiated.append(
            {
                "component_index": idx,
                "start_bytes": comp_start,
                "end_bytes": comp_end,
                "span_bytes": span_bytes,
                "layout_type": comp.layout_type,
                "effective_stripe_count": eff_count,
                "stripe_size_bytes": comp.stripe_size_bytes,
                "touched_osts": touched_osts,
            }
        )
        comp_start = comp_end
        if comp_start >= file_size_bytes:
            break

    active_osts = [i for i, b in enumerate(ost_bytes) if b > 0]
    return {
        "file_size_bytes": file_size_bytes,
        "mdt_dom_bytes": mdt_dom_bytes,
        "ost_bytes": ost_bytes,
        "active_ost_count": len(active_osts),
        "active_osts": active_osts,
        "uses_dom_only": mdt_dom_bytes == file_size_bytes and file_size_bytes > 0,
        "instantiated_components": instantiated,
    }


def map_raid0_read_window(
    offset_bytes: int,
    length_bytes: int,
    stripe_size_bytes: int,
    stripe_count: int,
) -> Dict[str, object]:
    """Model round-robin RAID0 chunk placement for a read/write window `[offset, offset+length)`."""
    if stripe_size_bytes <= 0 or stripe_count <= 0 or length_bytes <= 0:
        raise ValueError("stripe_size_bytes, stripe_count, and length_bytes must be > 0")

    per_slot = [0] * stripe_count
    chunk_sequence: List[Tuple[int, int, int]] = []
    cur = offset_bytes
    end = offset_bytes + length_bytes
    while cur < end:
        chunk_idx = cur // stripe_size_bytes
        next_boundary = (chunk_idx + 1) * stripe_size_bytes
        nbytes = min(end, next_boundary) - cur
        slot = chunk_idx % stripe_count
        per_slot[slot] += nbytes
        chunk_sequence.append((chunk_idx, slot, nbytes))
        cur += nbytes

    touched_slots = [idx for idx, b in enumerate(per_slot) if b > 0]
    return {
        "offset_bytes": offset_bytes,
        "length_bytes": length_bytes,
        "stripe_size_bytes": stripe_size_bytes,
        "stripe_count": stripe_count,
        "per_slot_bytes": per_slot,
        "touched_slots": touched_slots,
        "parallel_ost_fanout": len(touched_slots),
        "chunk_sequence": chunk_sequence,
    }


def model_dne_metadata_scaling(
    file_count: int,
    mdt_count: int,
    ops_per_mdt_sec: float = 50000.0,
    dne_phase: int = 2,
    directory_count: int = 1,
    files_per_shard: int = 1,
) -> Dict[str, object]:
    """Compare single-MDT vs DNE Phase 1 / Phase 2 metadata scaling and dataset sharding.

    - DNE Phase 1 (`lfs mkdir -i N`): pins whole subdirectories to specific MDTs. If all files sit
      in 1 directory (`directory_count == 1`), Phase 1 still bottlenecks on 1 MDT.
    - DNE Phase 2 (`lfs setdirstripe -c M`): hashes filenames inside a single directory across M MDTs.
    - Sharding (`files_per_shard > 1`, e.g., WebDataset `.tar` or TFRecord/Parquet shards): reduces
      open() count from `file_count` to `ceil(file_count / files_per_shard)`.
    """
    if file_count <= 0 or mdt_count <= 0 or ops_per_mdt_sec <= 0 or files_per_shard <= 0:
        raise ValueError("All counts and rates must be > 0")

    effective_opens = (file_count + files_per_shard - 1) // files_per_shard
    if dne_phase == 1:
        active_mdts = min(mdt_count, max(1, directory_count))
    else:
        active_mdts = mdt_count

    aggregate_iops_capacity = active_mdts * ops_per_mdt_sec
    single_mdt_time_sec = file_count / ops_per_mdt_sec
    epoch_open_time_sec = effective_opens / aggregate_iops_capacity
    metadata_reduction_factor = file_count / effective_opens
    total_speedup_vs_unsharded_single_mdt = single_mdt_time_sec / epoch_open_time_sec

    return {
        "raw_file_count": file_count,
        "effective_opens": effective_opens,
        "mdt_count": mdt_count,
        "active_mdts": active_mdts,
        "dne_phase": dne_phase,
        "ops_per_mdt_sec": ops_per_mdt_sec,
        "aggregate_iops_capacity": aggregate_iops_capacity,
        "single_mdt_unsharded_sec": round(single_mdt_time_sec, 4),
        "epoch_open_time_sec": round(epoch_open_time_sec, 4),
        "metadata_reduction_factor": round(metadata_reduction_factor, 2),
        "total_speedup": round(total_speedup_vs_unsharded_single_mdt, 2),
    }


def evaluate_lctl_metadata_stats(
    open_samples: int,
    window_sec: float,
    avg_open_us: float,
    max_open_us: float,
    getattr_samples: int = 0,
    healthy_ops_sec_limit: float = 50000.0,
    healthy_avg_ms_limit: float = 5.0,
) -> Dict[str, object]:
    """Classify `lctl get_param llite.*.stats` open/getattr pressure (from V15 Ch 5)."""
    open_rate_sec = open_samples / window_sec
    getattr_rate_sec = getattr_samples / window_sec
    # Also track total sample count including close_samples = open_samples (e.g., 950000 + 950000 + 1900000 = 3800000 -> 63333.33 ops/sec)
    total_samples_with_close = open_samples * 2 + getattr_samples
    total_rate_with_close_sec = total_samples_with_close / window_sec
    avg_open_ms = avg_open_us / 1000.0
    max_open_ms = max_open_us / 1000.0
    saturated = avg_open_ms > healthy_avg_ms_limit or (open_rate_sec + getattr_rate_sec) > healthy_ops_sec_limit
    return {
        "open_rate_per_sec": round(open_rate_sec, 2),
        "getattr_rate_per_sec": round(getattr_rate_sec, 2),
        "total_meta_ops_per_sec": round(open_rate_sec + getattr_rate_sec, 2),
        "total_samples_with_close": total_samples_with_close,
        "total_rate_with_close_per_sec": round(total_rate_with_close_sec, 2),
        "avg_open_ms": round(avg_open_ms, 2),
        "max_open_ms": round(max_open_ms, 2),
        "status": "METADATA_SATURATED" if saturated else "HEALTHY_HEADROOM",
        "remediation": (
            "Repackage millions of small files into WebDataset/TFRecord shards, enable DNE across multiple MDTs, or enable DoM"
            if saturated
            else "Metadata server has headroom"
        ),
    }


def calculate_client_rpc_bdp(
    max_rpcs_in_flight: int = 8,
    max_pages_per_rpc: int = 256,
    page_size_bytes: int = 4096,
    rtt_us: float = 500.0,
    active_osts: int = 1,
    per_ost_cap_mbps: float = 800.0,
    client_nic_gbps: float = 400.0,
) -> Dict[str, float]:
    """Compute Lustre OSC client RPC Bandwidth-Delay Product (BDP):
    - `rpc_size_bytes = max_pages_per_rpc * page_size_bytes` (e.g., 256 * 4 KiB = 1 MiB, or 4096 * 4 KiB = 16 MiB)
    - `in_flight_bytes_per_ost = max_rpcs_in_flight * rpc_size_bytes`
    - `bdp_mbps_per_ost = in_flight_bytes_per_ost / rtt_sec / 1e6`
    - Effective per-OST bandwidth is `min(bdp_mbps_per_ost, per_ost_cap_mbps)`.
    - Aggregate client bandwidth across `active_osts` is capped by `client_nic_gbps * 125` MB/s.
    """
    if max_rpcs_in_flight <= 0 or max_pages_per_rpc <= 0 or page_size_bytes <= 0 or rtt_us <= 0 or active_osts <= 0:
        raise ValueError("All RPC and network parameters must be > 0")

    rpc_size_bytes = max_pages_per_rpc * page_size_bytes
    rpc_size_mib = rpc_size_bytes / MiB
    in_flight_mib_per_ost = (max_rpcs_in_flight * rpc_size_bytes) / MiB
    rtt_sec = rtt_us / 1_000_000.0
    bdp_mbps_per_ost = (max_rpcs_in_flight * rpc_size_bytes) / rtt_sec / 1_000_000.0
    effective_per_ost_mbps = min(bdp_mbps_per_ost, per_ost_cap_mbps)
    nic_cap_mbps = client_nic_gbps * 125.0
    aggregate_mbps = min(active_osts * effective_per_ost_mbps, nic_cap_mbps)

    return {
        "rpc_size_mib": round(rpc_size_mib, 4),
        "in_flight_mib_per_ost": round(in_flight_mib_per_ost, 4),
        "bdp_mbps_per_ost": round(bdp_mbps_per_ost, 2),
        "effective_per_ost_mbps": round(effective_per_ost_mbps, 2),
        "aggregate_client_mbps": round(aggregate_mbps, 2),
        "aggregate_client_gbps_ decimal": round(aggregate_mbps / 1000.0, 3),
    }


def compare_gdsio_paths(
    cpu_path_gbps: float = 8.0,
    cpu_path_lat_ms: float = 1.25,
    gds_path_gbps: float = 9.6,
    gds_path_lat_ms: float = 1.00,
) -> Dict[str, float]:
    """Compare `gdsio` CPU bounce-buffer path (`-x 2`) vs GPUDirect Storage direct path (`-x 0`)
    from *AI Systems Performance Engineering* Ch. 5 Table 5-1.
    """
    tp_gain_pct = ((gds_path_gbps - cpu_path_gbps) / cpu_path_gbps) * 100.0
    lat_reduction_pct = ((cpu_path_lat_ms - gds_path_lat_ms) / cpu_path_lat_ms) * 100.0
    return {
        "cpu_path_gbps": cpu_path_gbps,
        "cpu_path_lat_ms": cpu_path_lat_ms,
        "gds_path_gbps": gds_path_gbps,
        "gds_path_lat_ms": gds_path_lat_ms,
        "throughput_gain_pct": round(tp_gain_pct, 2),
        "latency_reduction_pct": round(lat_reduction_pct, 2),
    }


def model_checkpoint_write_strategy(
    checkpoint_gb: float,
    num_ranks: int,
    total_osts: int,
    per_ost_write_mbps: float,
    strategy: str,
    stripe_count: int = 1,
    stripe_aligned: bool = True,
) -> Dict[str, object]:
    """Compare 4 distributed checkpoint write patterns on Lustre:
    1. `n_to_1_single_ost`: all ranks or rank-0 write to 1 shared file with `stripe_count=1`.
    2. `n_to_1_unaligned_ldlm`: all `num_ranks` write concurrently to 1 shared file across `stripe_count`
       OSTs without stripe-boundary alignment -> LDLM extent lock ping-pong degrades effective OST rate.
    3. `n_to_1_aligned_all_osts`: stripe-aligned collective write with `stripe_count = total_osts` (`-c -1`).
    4. `n_to_n_sharded`: `num_ranks` independent shard files (e.g., PyTorch Distributed Checkpointing / DCP),
       each with `stripe_count` (`1..4`) balanced across all `total_osts` with zero cross-rank LDLM contention.
    """
    total_mb = checkpoint_gb * 1000.0
    if strategy == "n_to_1_single_ost":
        used_osts = 1
        lock_efficiency = 1.0
    elif strategy == "n_to_1_unaligned_ldlm":
        used_osts = total_osts if stripe_count == -1 else min(stripe_count, total_osts)
        # Unaligned concurrent writes to shared stripe extents cause severe LDLM lock ping-pong
        lock_efficiency = 0.25 if not stripe_aligned else 0.85
    elif strategy == "n_to_1_aligned_all_osts":
        used_osts = total_osts if stripe_count == -1 else min(stripe_count, total_osts)
        lock_efficiency = 0.90 if stripe_aligned else 0.25
    elif strategy == "n_to_n_sharded":
        used_osts = min(total_osts, num_ranks * max(1, stripe_count))
        lock_efficiency = 1.0
    else:
        raise ValueError(f"Unknown checkpoint strategy: {strategy}")

    effective_bw_mbps = used_osts * per_ost_write_mbps * lock_efficiency
    write_time_sec = total_mb / effective_bw_mbps
    per_ost_gb = round(checkpoint_gb / used_osts, 2)
    per_rank_gb = round(checkpoint_gb / max(1, num_ranks), 2)
    return {
        "strategy": strategy,
        "checkpoint_gb": checkpoint_gb,
        "num_ranks": num_ranks,
        "total_osts": total_osts,
        "used_osts": used_osts,
        "per_ost_gb": per_ost_gb,
        "per_rank_gb": per_rank_gb,
        "lock_efficiency": round(lock_efficiency, 2),
        "effective_bw_gbps": round(effective_bw_mbps / 1000.0, 2),
        "write_time_sec": round(write_time_sec, 2),
        "write_time_sec_1dp": round(write_time_sec, 1),
    }


def audit_lnet_multirail_and_osts(
    rails: Sequence[LNetRailNID],
    ost_used_pct: Sequence[float],
    num_clients: int = 128,
    osts_per_oss: int = 6,
) -> Dict[str, object]:
    """Validate LNet multi-rail NID health, NUMA affinity, OST fill skew (`lfs df`), and OSS RAM sizing."""
    healthy_rails = [r for r in rails if r.link_up and r.tx_Queued_errors == 0 and r.rx_drop_errors == 0]
    numa_aligned_rails = [r for r in healthy_rails if r.numa_node == r.gpu_numa_node]
    aggregate_gbps = sum(r.rate_gbps for r in healthy_rails)

    min_fill = min(ost_used_pct) if ost_used_pct else 0.0
    max_fill = max(ost_used_pct) if ost_used_pct else 0.0
    fill_skew_pct = max_fill - min_fill
    imbalanced_osts = [idx for idx, pct in enumerate(ost_used_pct) if pct >= 90.0 or (pct - min_fill) > 10.0]

    total_osts = len(ost_used_pct)
    threads_per_ost = max(1.0, num_clients / max(1, total_osts))
    per_ost_ram_mb = 400.0 + 600.0 + 1.5 * threads_per_ost
    recommended_oss_ram_gb = 2.0 + 1.0 * osts_per_oss

    return {
        "total_rails": len(rails),
        "healthy_rail_count": len(healthy_rails),
        "numa_aligned_rail_count": len(numa_aligned_rails),
        "aggregate_healthy_gbps": round(aggregate_gbps, 1),
        "ost_fill_skew_pct": round(fill_skew_pct, 2),
        "imbalanced_osts": imbalanced_osts,
        "ost_balance_status": "IMBALANCED_MIGRATE_REQUIRED" if imbalanced_osts else "BALANCED",
        "threads_per_ost_est": round(threads_per_ost, 2),
        "per_ost_ram_mb": round(per_ost_ram_mb, 2),
        "recommended_oss_ram_gb": round(recommended_oss_ram_gb, 2),
    }


if __name__ == "__main__":
    layout = default_ai_pfl_layout()
    tiny = evaluate_pfl_dom_file(256 * KiB, layout, total_osts=24)
    ckpt = evaluate_pfl_dom_file(10 * GiB, layout, total_osts=24)
    print(f"256 KiB file -> DoM bytes: {tiny['mdt_dom_bytes']}, active OSTs: {tiny['active_ost_count']}")
    print(f"10 GiB file  -> DoM bytes: {ckpt['mdt_dom_bytes']}, active OSTs: {ckpt['active_ost_count']}")
    dne = model_dne_metadata_scaling(file_count=10_000_000, mdt_count=4, ops_per_mdt_sec=50_000, files_per_shard=100_000)
    print(f"10M files sharded to 100 shards across 4 MDTs -> open time: {dne['epoch_open_time_sec']} s")
