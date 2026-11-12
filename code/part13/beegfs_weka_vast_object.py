"""Chapter 13.5: BeeGFS, Weka, VAST and object storage.

Pure Python 3 standard-library reference models for:
1. BeeGFS Parallel Filesystem Architecture & Stripe Chunking (V15 Ch. 06):
   - Four core services: Management Service (`beegfs-mgmtd`), Metadata Service (`beegfs-meta`,
     50,000-100,000 ops/sec per MDS, < 5 ms healthy latency), Storage Service (`beegfs-storage`,
     500 MB/s-2 GB/s per storage node, targets within +/-5% fill balance), and Client Service
     (`beegfs-client`, kernel module with `connUseRDMA=true`, `tuneUseGDTLSConnPool=true`,
     `tunePrefetchType=buffered`, `connMaxInactiveTime=900000`).
   - Round-robin file stripe layout (`beegfs-ctl --setpattern --chunksize=1M --numtargets=8`):
     maps byte offsets (e.g. `10,486,272` = `10 MiB + 512 B`) to `(chunk_index, target_slot, target_id, intra_chunk_offset)` and models
     aggregate single-client and multi-client throughput and checkpoint stall time (e.g., 500 GB
     checkpoint across 2 targets at 800 MB/s = 1.6 GB/s = 312.5 s vs 8 targets = 6.4 GB/s = 78.125 s
     or 5.0 GB/s sustained at 78.125% efficiency = 100.0 s, and 12 targets = 9.6 GB/s = 52.08 s;
     storage1 44-45% vs storage2 71-72% has 58.0% mean and 28.0% spread).
   - Metadata saturation vs dataset repackaging (256 GPUs generating 200,000+ ops/sec on millions
     of small JPEGs vs WebDataset / TFRecord sharding reducing metadata rate by 100x to < 5,000 ops/sec).
2. WekaFS Distributed Virtual Metadata & POSIX Client Core Pinning (ADC Ch. 9, AISPE Ch. 5):
   - Fully distributed data and metadata chunks across all NVMe nodes (no single MDS bottleneck),
     4 KB metadata/small-file efficiency, POSIX client over RDMA (`RoCEv2` UDP 4791 / InfiniBand)
     with dedicated pinned polling CPU cores (`ll_core`) vs kernel NFSv3/v4.1 fallback.
   - Unified Tier 1 hot NVMe-o-PCIe / RDMA pool + transparent Tier 2 S3 object storage tiering
     preserving a single POSIX namespace for PyTorch (`.pt`, `.ckpt`, `.safetensors`, `.bin`).
   - Erasure coding `N + K` (e.g., `6 + 2` = `75.0%` or `16 + 2` = `88.89%` distributed stripe protection;
     `737.28 TB` usable of `983.04 TB` raw vs `327.68 TB` / `33.33%` usable and `66.67%` overhead under `3x` replication).
3. VAST Data Disaggregated Shared-Everything (`DASE`) & GPUDirect Storage (`GDS`) (ADC Ch. 9, AISPE Ch. 5):
   - Stateless CNodes (protocol/compute containers serving NFS-over-RDMA, SMB, and S3) decoupled over
     an NVMe-oF fabric (`RoCEv2` / InfiniBand) from HA DNodes (enclosures holding Storage Class Memory /
     Optane / 3D XPoint low-latency write buffers + global metadata and high-density QLC NAND flash).
   - Shared-everything global namespace without east-west CNode coordination locks, wide erasure stripes
     (e.g., `146 + 4` = 97.33% efficiency), similarity-based data reduction, and write-buffer coalescing
     that turns small random writes into large sequential QLC erase-block stripes.
   - GPUDirect Storage (`GDS` / `cuFile` / `gdsio`): CPU bounce-buffer path (`-x 2`, `8.0 GB/s`,
     `1.25 ms`) vs direct `GDS` DMA path (`-x 0`, `9.6 GB/s`, `1.00 ms`, `+20%` throughput and `-20%`
     latency on A100, and `+30%+` on H100).
4. DeepSeek Fire-Flyer File System (`3FS`) peak read benchmark:
   - Four RDMA-connected components: Cluster Manager, Metadata Service (sharded/replicated), Storage
     Service, and Client using Linux `O_DIRECT` + `io_uring` + RDMA (avoiding kernel page-cache
     thrashing on random LLM training/KVCache reads).
   - Why user-space FUSE filesystems cannot support true `GDS` zero-copy DMA (unless paired with
     explicit RDMA/USRBIOS or kernel `nvidia-fs` `O_DIRECT` integration).
   - Benchmark math on the published 180-node cluster (`16 x 14 TiB` NVMe SSDs and dual `200 Gb/s` NICs per
     node): about `6.6 TiB/s` aggregate read throughput with training background traffic.
5. Object Storage (`S3` / `GCS` / MinIO) Prefix Sharding, Multipart Transfers & Staging Pipelines (V15 Ch. 07, AISPE Ch. 5):
   - Per-request HTTP/TLS latency trap (`50 ms` TLS + `100 ms` API = `150 ms` = `0.150 s` per small object ->
     `2,000,000` objects x `0.150 s` = `300,000 s` = `83.33 hours` serial overhead vs sharded manifests).
   - S3 partition prefix sharding (`3,500` PUT/COPY/POST/DELETE and `5,500` GET/HEAD requests/sec per
     prefix) and how `P` hash/hex prefixes scale aggregate request rate to `P x 5,500` GET ops/sec.
   - Parallel multipart / shard download throughput math (`1 GB` single-stream in `6.2 s` = `161.29 MB/s`
     vs `8 x 1 GB` parallel streams in `7.5 s` = `1066.67 MB/s` aggregate, `133.33 MB/s` per worker;
     `20 GB` initial `2`-shard prefetch at `8 x 150 MB/s = 1.2 GB/s` in `16.67 s` + `10.2 s` API/TLS =
     `~26.87 s` / `27 s` time-to-first-batch).
   - Local NVMe staging cache hit-rate and eviction model across epochs (`Epoch 1` cold `0.1%` hit rate,
     `45.3 min` wait -> `Epoch 2` warm `98.2%` hit rate, `2.1 min` wait -> `Epoch 3` eviction onset at
     `> 85%` fill, `97.5%` hit rate, `3.5 min` wait).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. BeeGFS Architecture, Striping, Metadata & Target Balance (V15 Ch. 06)
# ---------------------------------------------------------------------------

BEEGFS_SERVICES: Dict[str, Dict[str, str | int]] = {
    "beegfs-mgmtd": {
        "role": "Management Service",
        "responsibility": "Cluster node/target registry and topology map",
        "critical_path": "Control plane only (lookup on mount/membership change)",
    },
    "beegfs-meta": {
        "role": "Metadata Service (MDS)",
        "responsibility": "Directory tree, POSIX permissions, file-to-stripe layout mapping",
        "ops_per_sec_min": 50000,
        "ops_per_sec_max": 100000,
        "healthy_latency_ms_max": 5,
    },
    "beegfs-storage": {
        "role": "Storage Service (OSS)",
        "responsibility": "Manages underlying XFS/EXT4 NVMe storage targets and serves striped chunks",
        "mb_per_sec_min": 500,
        "mb_per_sec_max": 2000,
        "healthy_fill_skew_pct_max": 5,
    },
    "beegfs-client": {
        "role": "Client Kernel Module",
        "responsibility": "Mounts /beegfs, queries MDS for layout, executes parallel RDMA reads/writes to targets",
        "transport": "RDMA (InfiniBand / RoCEv2) or TCP",
    },
}


@dataclass(frozen=True)
class BeeGFSStripeMapping:
    file_offset_bytes: int
    chunk_size_bytes: int
    num_targets: int
    chunk_index: int
    stripe_row: int
    target_slot: int
    target_id: int
    intra_chunk_offset_bytes: int


def map_beegfs_file_offset(
    file_offset_bytes: int,
    chunk_size_bytes: int = 1048576,
    target_ids: Tuple[int, ...] = (1001, 1002, 2001, 2002, 3001, 3002, 4001, 4002),
) -> BeeGFSStripeMapping:
    """Map a logical file byte offset to its BeeGFS round-robin chunk and storage target."""
    if file_offset_bytes < 0:
        raise ValueError("file_offset_bytes must be non-negative")
    if chunk_size_bytes <= 0 or not target_ids:
        raise ValueError("chunk_size_bytes and target_ids must be positive")
    num_targets = len(target_ids)
    chunk_index = file_offset_bytes // chunk_size_bytes
    stripe_row = chunk_index // num_targets
    target_slot = chunk_index % num_targets
    intra_chunk_offset = file_offset_bytes % chunk_size_bytes
    return BeeGFSStripeMapping(
        file_offset_bytes=file_offset_bytes,
        chunk_size_bytes=chunk_size_bytes,
        num_targets=num_targets,
        chunk_index=chunk_index,
        stripe_row=stripe_row,
        target_slot=target_slot,
        target_id=target_ids[target_slot],
        intra_chunk_offset_bytes=intra_chunk_offset,
    )


def evaluate_beegfs_stripe_throughput(
    file_size_gb: float = 500.0,
    num_targets: int = 8,
    per_target_mb_s: float = 800.0,
    efficiency_factor: float = 0.78125,
) -> Dict[str, float]:
    """Calculate BeeGFS theoretical and sustained throughput and checkpoint write duration."""
    if num_targets <= 0 or per_target_mb_s <= 0:
        raise ValueError("num_targets and per_target_mb_s must be positive")
    theoretical_gb_s = (num_targets * per_target_mb_s) / 1000.0
    sustained_gb_s = theoretical_gb_s * efficiency_factor
    theoretical_write_sec = file_size_gb / theoretical_gb_s
    sustained_write_sec = file_size_gb / sustained_gb_s
    return {
        "file_size_gb": file_size_gb,
        "num_targets": float(num_targets),
        "per_target_mb_s": per_target_mb_s,
        "theoretical_gb_s": round(theoretical_gb_s, 4),
        "sustained_gb_s": round(sustained_gb_s, 4),
        "theoretical_write_sec": round(theoretical_write_sec, 4),
        "sustained_write_sec": round(sustained_write_sec, 4),
    }


def analyze_beegfs_mds_scaling_and_sharding(
    num_gpus: int = 256,
    raw_ops_per_gpu_epoch_start: int = 800,
    mds_capacity_ops_sec: int = 50000,
    mds_count: int = 1,
    repackage_reduction_factor: int = 100,
    healthy_latency_ms_threshold: float = 5.0,
) -> Dict[str, float | int | bool | str]:
    """Evaluate BeeGFS metadata saturation at epoch start and the impact of WebDataset sharding."""
    raw_peak_ops_sec = num_gpus * raw_ops_per_gpu_epoch_start
    cluster_mds_capacity = mds_count * mds_capacity_ops_sec
    mds_needed_for_raw = (raw_peak_ops_sec + mds_capacity_ops_sec - 1) // mds_capacity_ops_sec
    sharded_ops_sec = raw_peak_ops_sec // repackage_reduction_factor
    raw_saturated = raw_peak_ops_sec > cluster_mds_capacity
    sharded_saturated = sharded_ops_sec > cluster_mds_capacity
    return {
        "num_gpus": num_gpus,
        "raw_peak_ops_sec": raw_peak_ops_sec,
        "mds_count": mds_count,
        "mds_capacity_ops_sec": mds_capacity_ops_sec,
        "cluster_mds_capacity_ops_sec": cluster_mds_capacity,
        "mds_needed_for_raw": mds_needed_for_raw,
        "raw_saturated": raw_saturated,
        "repackage_reduction_factor": repackage_reduction_factor,
        "sharded_ops_sec": sharded_ops_sec,
        "sharded_saturated": sharded_saturated,
        "healthy_latency_ms_threshold": healthy_latency_ms_threshold,
        "remediation": "Scale MDS nodes AND repackage small files into WebDataset/TFRecord shards",
    }


def evaluate_beegfs_target_fill_balance(
    targets: List[Tuple[int, str, float, float]],
    healthy_band_pct: float = 5.0,
    investigate_skew_pct: float = 10.0,
) -> Dict[str, float | bool | List[int]]:
    """Inspect BeeGFS storage target fill levels (`beegfs-ctl --listtargets --spaceinfo`).

    Each tuple is `(target_id, node_name, used_tb, capacity_tb)`.
    """
    pcts = [(tid, (used / cap) * 100.0) for tid, _node, used, cap in targets]
    values = [p for _tid, p in pcts]
    mean_pct = sum(values) / len(values)
    min_pct = min(values)
    max_pct = max(values)
    max_spread_pct = max_pct - min_pct
    max_deviation_from_mean = max(abs(p - mean_pct) for p in values)
    overloaded_targets = [tid for tid, p in pcts if p - mean_pct > healthy_band_pct]
    return {
        "mean_fill_pct": round(mean_pct, 2),
        "min_fill_pct": round(min_pct, 2),
        "max_fill_pct": round(max_pct, 2),
        "max_spread_pct": round(max_spread_pct, 2),
        "within_healthy_plus_minus_5pct": max_deviation_from_mean <= healthy_band_pct,
        "requires_rebalance_investigation": max_spread_pct > investigate_skew_pct,
        "overloaded_target_ids": overloaded_targets,
    }


# ---------------------------------------------------------------------------
# 2. WekaFS Distributed Virtual Metadata & Tiering (ADC Ch. 9, AISPE Ch. 5)
# ---------------------------------------------------------------------------

def evaluate_wekafs_cluster_architecture(
    num_storage_nodes: int = 8,
    nvme_drives_per_node: int = 8,
    data_chunks_n: int = 6,
    parity_chunks_k: int = 2,
    raw_tb_per_drive: float = 15.36,
    client_pinned_cores_per_gpu_node: int = 4,
    total_cores_per_gpu_node: int = 128,
    tier2_s3_capacity_tb: float = 2000.0,
) -> Dict[str, float | int | bool | str]:
    """Model WekaFS distributed metadata/data chunking, N+K erasure coding, and POSIX client core pinning."""
    stripe_width = data_chunks_n + parity_chunks_k
    if stripe_width > num_storage_nodes:
        raise ValueError("N + K stripe width cannot exceed failure-domain storage nodes")
    raw_nvme_tb = num_storage_nodes * nvme_drives_per_node * raw_tb_per_drive
    ec_efficiency = data_chunks_n / stripe_width
    usable_tier1_nvme_tb = raw_nvme_tb * ec_efficiency
    three_way_rep_usable_tb = raw_nvme_tb / 3.0
    total_namespace_tb = usable_tier1_nvme_tb + tier2_s3_capacity_tb
    cpu_core_tax_pct = (client_pinned_cores_per_gpu_node / total_cores_per_gpu_node) * 100.0
    return {
        "num_storage_nodes": num_storage_nodes,
        "metadata_architecture": "Fully distributed virtual metadata across all NVMe nodes (no single MDS bottleneck)",
        "stripe_protection": f"{data_chunks_n}+{parity_chunks_k}",
        "ec_efficiency_pct": round(ec_efficiency * 100.0, 2),
        "raw_nvme_tb": round(raw_nvme_tb, 2),
        "usable_tier1_nvme_tb": round(usable_tier1_nvme_tb, 2),
        "three_way_replication_usable_tb": round(three_way_rep_usable_tb, 2),
        "capacity_gain_vs_3x_rep": round(usable_tier1_nvme_tb / three_way_rep_usable_tb, 4),
        "tier2_s3_capacity_tb": round(tier2_s3_capacity_tb, 2),
        "unified_posix_namespace_tb": round(total_namespace_tb, 2),
        "client_pinned_cores": client_pinned_cores_per_gpu_node,
        "client_core_tax_pct": round(cpu_core_tax_pct, 4),
        "supports_gds_rdma": True,
    }


# ---------------------------------------------------------------------------
# 3. VAST Data DASE Architecture & GPUDirect Storage (ADC Ch. 9, AISPE Ch. 5)
# ---------------------------------------------------------------------------

def evaluate_vast_dase_and_gds(
    cnode_count: int = 16,
    dnode_enclosures: int = 8,
    ec_data_strips: int = 146,
    ec_parity_strips: int = 4,
    scm_write_buffer_tb: float = 24.0,
    qlc_raw_capacity_tb: float = 1500.0,
    similarity_reduction_ratio: float = 2.0,
    gds_baseline_cpu_gb_s: float = 8.0,
    gds_baseline_cpu_latency_ms: float = 1.25,
    gds_direct_gpu_gb_s: float = 9.6,
    gds_direct_gpu_latency_ms: float = 1.00,
    h100_gds_uplift_pct: float = 30.0,
) -> Dict[str, float | int | bool | str]:
    """Model VAST Data Disaggregated Shared-Everything (DASE) and GPUDirect Storage (`gdsio`) uplifts."""
    wide_stripe_total = ec_data_strips + ec_parity_strips
    ec_efficiency_pct = (ec_data_strips / wide_stripe_total) * 100.0
    ec_overhead_pct = (ec_parity_strips / wide_stripe_total) * 100.0
    usable_qlc_tb = qlc_raw_capacity_tb * (ec_data_strips / wide_stripe_total)
    effective_logical_tb = usable_qlc_tb * similarity_reduction_ratio
    gds_throughput_uplift_pct = ((gds_direct_gpu_gb_s - gds_baseline_cpu_gb_s) / gds_baseline_cpu_gb_s) * 100.0
    gds_latency_reduction_pct = (
        (gds_baseline_cpu_latency_ms - gds_direct_gpu_latency_ms) / gds_baseline_cpu_latency_ms
    ) * 100.0
    return {
        "architecture": "Disaggregated Shared-Everything (DASE)",
        "cnode_count": cnode_count,
        "cnode_stateful": False,
        "cnode_east_west_lock_traffic": False,
        "dnode_enclosures": dnode_enclosures,
        "fabric_transport": "NVMe-oF (RoCEv2 / InfiniBand)",
        "write_buffer_media": "SCM / Optane / 3D XPoint (absorbs random writes & holds global metadata)",
        "capacity_media": "QLC NAND Flash (written sequentially after SCM coalescing)",
        "scm_write_buffer_tb": scm_write_buffer_tb,
        "wide_erasure_code": f"{ec_data_strips}+{ec_parity_strips}",
        "ec_efficiency_pct": round(ec_efficiency_pct, 2),
        "ec_overhead_pct": round(ec_overhead_pct, 2),
        "usable_qlc_tb": round(usable_qlc_tb, 2),
        "effective_logical_tb": round(effective_logical_tb, 2),
        "gds_cpu_path_flag": "-x 2",
        "gds_direct_path_flag": "-x 0",
        "gds_cpu_gb_s": gds_baseline_cpu_gb_s,
        "gds_direct_gb_s": gds_direct_gpu_gb_s,
        "gds_a100_throughput_uplift_pct": round(gds_throughput_uplift_pct, 2),
        "gds_latency_reduction_pct": round(gds_latency_reduction_pct, 2),
        "gds_h100_throughput_uplift_pct": h100_gds_uplift_pct,
    }


# ---------------------------------------------------------------------------
# 4. DeepSeek Fire-Flyer File System (3FS) peak read benchmark
# ---------------------------------------------------------------------------

def evaluate_deepseek_3fs_benchmark(
    num_storage_nodes: int = 180,
    nvme_drives_per_node: int = 16,
    nvme_drive_capacity_tib: int = 14,
    nics_per_node: int = 2,
    nic_speed_gbps: int = 200,
    achieved_read_tib_s: float = 6.6,
) -> Dict[str, float | int | bool | Tuple[str, ...]]:
    """Model the peak read benchmark published in the 3FS README: 180 storage nodes, each with two 200 Gbps
    InfiniBand NICs and sixteen 14 TiB NVMe SSDs, about 6.6 TiB/s aggregate read with training background traffic."""
    total_nvme_drives = num_storage_nodes * nvme_drives_per_node
    total_raw_capacity_tib = total_nvme_drives * nvme_drive_capacity_tib
    per_node_network_gbps = nics_per_node * nic_speed_gbps
    per_node_network_gb_s = per_node_network_gbps / 8.0
    cluster_line_rate_tb_s = (num_storage_nodes * per_node_network_gb_s) / 1000.0
    achieved_read_tb_s = achieved_read_tib_s * (2 ** 40) / 1e12
    per_node_achieved_gib_s = achieved_read_tib_s * 1024.0 / num_storage_nodes
    per_node_achieved_gb_s = achieved_read_tb_s * 1000.0 / num_storage_nodes
    return {
        "components": ("Cluster Manager", "Metadata Service", "Storage Service", "Client"),
        "num_storage_nodes": num_storage_nodes,
        "total_nvme_drives": total_nvme_drives,
        "total_raw_capacity_tib": total_raw_capacity_tib,
        "per_node_network_gbps": per_node_network_gbps,
        "per_node_network_gb_s": per_node_network_gb_s,
        "cluster_line_rate_tb_s": round(cluster_line_rate_tb_s, 2),
        "achieved_read_tib_s": achieved_read_tib_s,
        "achieved_read_tb_s": round(achieved_read_tb_s, 2),
        "per_node_achieved_gib_s": round(per_node_achieved_gib_s, 2),
        "per_node_achieved_gb_s": round(per_node_achieved_gb_s, 2),
        "share_of_line_rate_pct": round(100.0 * achieved_read_tb_s / cluster_line_rate_tb_s, 1),
        "bypasses_os_page_cache": True,
        "uses_o_direct_and_io_uring_and_rdma": True,
        "standard_fuse_supports_kernel_gds": False,
    }


# ---------------------------------------------------------------------------
# 5. Object Storage Prefix Sharding, Multipart Math & Cache Staging (V15 Ch. 07)
# ---------------------------------------------------------------------------

def evaluate_s3_small_object_trap_vs_sharded_pipeline(
    num_small_objects: int = 2_000_000,
    small_object_kb: float = 260.0,
    per_request_overhead_ms: float = 150.0,
    num_shards: int = 50,
    shard_size_gb: float = 10.0,
    num_download_workers: int = 8,
    per_worker_mb_s: float = 150.0,
    initial_prefetch_shards: int = 2,
    s3_api_overhead_per_shard_s: float = 5.0,
    tls_handshake_per_shard_s: float = 0.1,
) -> Dict[str, float | int]:
    """Compare serial small-object S3 fetches against an 8-worker sharded prefetch pipeline (V15 Ch. 07)."""
    serial_api_wait_sec = num_small_objects * (per_request_overhead_ms / 1000.0)
    serial_api_wait_hours = serial_api_wait_sec / 3600.0
    aggregate_worker_mb_s = num_download_workers * per_worker_mb_s
    aggregate_worker_gb_s = aggregate_worker_mb_s / 1000.0
    prefetch_gb = initial_prefetch_shards * shard_size_gb
    transfer_sec = prefetch_gb / aggregate_worker_gb_s
    api_and_tls_sec = initial_prefetch_shards * (s3_api_overhead_per_shard_s + tls_handshake_per_shard_s)
    startup_time_to_first_batch_sec = transfer_sec + api_and_tls_sec
    return {
        "num_small_objects": num_small_objects,
        "small_object_kb": small_object_kb,
        "serial_api_wait_sec": round(serial_api_wait_sec, 2),
        "serial_api_wait_hours": round(serial_api_wait_hours, 2),
        "num_shards": num_shards,
        "shard_size_gb": shard_size_gb,
        "num_download_workers": num_download_workers,
        "aggregate_worker_mb_s": round(aggregate_worker_mb_s, 2),
        "aggregate_worker_gb_s": round(aggregate_worker_gb_s, 3),
        "prefetch_gb": round(prefetch_gb, 2),
        "prefetch_transfer_sec": round(transfer_sec, 2),
        "api_and_tls_overhead_sec": round(api_and_tls_sec, 2),
        "startup_time_to_first_batch_sec": round(startup_time_to_first_batch_sec, 2),
    }


def evaluate_s3_prefix_sharding_and_multipart(
    num_prefixes: int = 16,
    get_limit_per_prefix_ops_s: int = 5500,
    put_limit_per_prefix_ops_s: int = 3500,
    single_object_gb: float = 1.0,
    single_object_elapsed_s: float = 6.2,
    parallel_objects_count: int = 8,
    parallel_elapsed_s: float = 7.5,
) -> Dict[str, float | int]:
    """Calculate S3 prefix-sharded IOPS limits and parallel multipart/multi-object throughput (V15 Ch. 07)."""
    if num_prefixes <= 0:
        raise ValueError("num_prefixes must be positive")
    total_get_ops_s = num_prefixes * get_limit_per_prefix_ops_s
    total_put_ops_s = num_prefixes * put_limit_per_prefix_ops_s
    single_mb_s = (single_object_gb * 1000.0) / single_object_elapsed_s
    parallel_total_mb = parallel_objects_count * single_object_gb * 1000.0
    parallel_aggregate_mb_s = parallel_total_mb / parallel_elapsed_s
    parallel_per_worker_mb_s = parallel_aggregate_mb_s / parallel_objects_count
    serial_eight_elapsed_s = parallel_objects_count * single_object_elapsed_s
    return {
        "num_prefixes": num_prefixes,
        "get_limit_per_prefix_ops_s": get_limit_per_prefix_ops_s,
        "put_limit_per_prefix_ops_s": put_limit_per_prefix_ops_s,
        "aggregate_get_ops_s": total_get_ops_s,
        "aggregate_put_ops_s": total_put_ops_s,
        "single_object_mb_s": round(single_mb_s, 2),
        "serial_eight_elapsed_s": round(serial_eight_elapsed_s, 2),
        "parallel_eight_elapsed_s": parallel_elapsed_s,
        "parallel_aggregate_mb_s": round(parallel_aggregate_mb_s, 2),
        "parallel_per_worker_mb_s": round(parallel_per_worker_mb_s, 2),
        "speedup_factor": round(serial_eight_elapsed_s / parallel_elapsed_s, 2),
    }


def evaluate_nvme_staging_cache_epochs(
    epoch_metrics: Tuple[Tuple[int, float, float, float], ...] = (
        (1, 0.1, 45.3, 40.0),
        (2, 98.2, 2.1, 78.0),
        (3, 97.5, 3.5, 88.0),
    ),
    eviction_fill_threshold_pct: float = 85.0,
) -> Dict[str, object]:
    """Analyze local NVMe staging cache hit rates, wait times, and LRU eviction onset across epochs (V15 Ch. 07).

    Each tuple is `(epoch, hit_rate_pct, download_wait_min, cache_fill_pct)`.
    """
    eviction_epochs = [ep for ep, _hr, _wait, fill in epoch_metrics if fill > eviction_fill_threshold_pct]
    ep1_wait = epoch_metrics[0][2]
    ep2_wait = epoch_metrics[1][2]
    wait_reduction_factor = ep1_wait / ep2_wait if ep2_wait > 0 else 0.0
    return {
        "epochs_analyzed": len(epoch_metrics),
        "epoch_1_cold_hit_rate_pct": epoch_metrics[0][1],
        "epoch_1_download_wait_min": ep1_wait,
        "epoch_2_warm_hit_rate_pct": epoch_metrics[1][1],
        "epoch_2_download_wait_min": ep2_wait,
        "epoch_3_eviction_hit_rate_pct": epoch_metrics[2][1],
        "epoch_3_download_wait_min": epoch_metrics[2][2],
        "wait_reduction_ep1_to_ep2": round(wait_reduction_factor, 2),
        "eviction_fill_threshold_pct": eviction_fill_threshold_pct,
        "eviction_active_epochs": eviction_epochs,
    }
