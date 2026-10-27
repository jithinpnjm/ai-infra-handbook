"""Core models and calculators for Chapter 13.1: The AI data path: from storage to GPU.

Covers:
1. Five AI storage workload phases (ingest/ETL, preprocessing/staging, training dataloader
   reads, synchronous checkpoint writes, inference RAG/KV offload).
2. Capacity vs delivered throughput and metadata-server (MDS) saturation math for small files
   vs repacked shards (WebDataset / TFRecord / binary).
3. Eight-layer storage-to-GPU data path latency and capacity model (storage media, storage
   server controller, network fabric, client filesystem driver, OS page cache, CPU DRAM / NUMA,
   PCIe fabric, GPU HBM).
4. Traditional POSIX bounce-buffer path (3+ memory copies across NIC/NVMe -> Page Cache ->
   User Buffer -> Pinned DMA Buffer -> GPU HBM) vs GPUDirect Storage (GDS) P2P DMA path
   (1 direct DMA copy from NIC/NVMe -> PCIe Switch -> GPU HBM).
5. Per-GPU, per-node, and per-rack storage bandwidth scaling (e.g., 200 MB/s per GPU =
   1.6 GB/s per 8-GPU node, 14.4-20.0 GB/s per 72-GPU NVL72 rack) and checkpoint burst sizing.
6. NUMA / PCIe topology alignment (`NODE`/`SYS` vs `PHB`/`PIX`) and Linux Page Cache pollution
   vs `O_DIRECT` tradeoffs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class WorkloadPhaseProfile:
    """Storage behavioral profile for each of the 5 AI lifecycle phases."""

    phase: str
    io_pattern: str
    block_size_kb: int
    read_fraction: float
    write_fraction: float
    metadata_ops_per_sec_min: int
    metadata_ops_per_sec_max: int
    primary_tier: str
    critical_path_impact: str


FIVE_AI_WORKLOAD_PHASES: Tuple[WorkloadPhaseProfile, ...] = (
    WorkloadPhaseProfile(
        phase="ingest",
        io_pattern="bulk_write_and_object_list",
        block_size_kb=4096,
        read_fraction=0.20,
        write_fraction=0.80,
        metadata_ops_per_sec_min=1_000,
        metadata_ops_per_sec_max=50_000,
        primary_tier="Tier 3 Object Store (S3/GCS)",
        critical_path_impact="offline_etl_not_blocking_gpu",
    ),
    WorkloadPhaseProfile(
        phase="preprocessing",
        io_pattern="mixed_read_tokenize_pack_write",
        block_size_kb=2048,
        read_fraction=0.55,
        write_fraction=0.45,
        metadata_ops_per_sec_min=5_000,
        metadata_ops_per_sec_max=100_000,
        primary_tier="Tier 2 Parallel Filesystem + Tier 1 NVMe",
        critical_path_impact="cpu_and_storage_bound_prep",
    ),
    WorkloadPhaseProfile(
        phase="training_reads",
        io_pattern="parallel_shuffled_epoch_reads",
        block_size_kb=2048,
        read_fraction=0.98,
        write_fraction=0.02,
        metadata_ops_per_sec_min=50_000,
        metadata_ops_per_sec_max=500_000,
        primary_tier="Tier 1 Local NVMe / Tier 2 PFS",
        critical_path_impact="stalls_gpu_every_step_if_starved",
    ),
    WorkloadPhaseProfile(
        phase="checkpoint_writes",
        io_pattern="synchronous_all_rank_write_burst",
        block_size_kb=8192,
        read_fraction=0.01,
        write_fraction=0.99,
        metadata_ops_per_sec_min=1_000,
        metadata_ops_per_sec_max=50_000,
        primary_tier="Tier 1 NVMe Stage -> Tier 2 PFS -> Tier 3 Object",
        critical_path_impact="blocks_all_ranks_during_synchronous_flush",
    ),
    WorkloadPhaseProfile(
        phase="inference_rag_kv",
        io_pattern="low_latency_random_read_and_kv_offload",
        block_size_kb=64,
        read_fraction=0.85,
        write_fraction=0.15,
        metadata_ops_per_sec_min=100,
        metadata_ops_per_sec_max=100_000,
        primary_tier="Tier 0 HBM + Tier 1 Local NVMe + Vector/Object Store",
        critical_path_impact="inflates_ttft_and_tail_latency",
    ),
)


@dataclass(frozen=True)
class StorageTierSpec:
    """Four-tier AI factory storage hierarchy."""

    tier_id: int
    name: str
    representative_tech: str
    typical_capacity_gb: float
    typical_bandwidth_gbps: float
    typical_latency_ns: float


STORAGE_TIERS: Tuple[StorageTierSpec, ...] = (
    StorageTierSpec(
        tier_id=0,
        name="Tier 0: GPU HBM",
        representative_tech="HBM3 / HBM3e (A100 40-80 GB, H100 80 GB, H200 141 GB, B200 192 GB)",
        typical_capacity_gb=80.0,
        typical_bandwidth_gbps=3350.0,
        typical_latency_ns=5.0,
    ),
    StorageTierSpec(
        tier_id=1,
        name="Tier 1: Host Local NVMe Scratch",
        representative_tech="8x 3.84 TB PCIe Gen4/Gen5 NVMe RAID 0 (30.72 TB raw)",
        typical_capacity_gb=30_720.0,
        typical_bandwidth_gbps=50.0,
        typical_latency_ns=10_000.0,
    ),
    StorageTierSpec(
        tier_id=2,
        name="Tier 2: Parallel File System (PFS)",
        representative_tech="Lustre, BeeGFS, WEKA, VAST, IBM Storage Scale, 3FS over RDMA",
        typical_capacity_gb=7_200_000.0,
        typical_bandwidth_gbps=400.0,
        typical_latency_ns=500_000.0,
    ),
    StorageTierSpec(
        tier_id=3,
        name="Tier 3: Object Store / Data Lake",
        representative_tech="S3 / GCS / MinIO / Ceph / FlashBlade",
        typical_capacity_gb=50_000_000.0,
        typical_bandwidth_gbps=50.0,
        typical_latency_ns=15_000_000.0,
    ),
)


@dataclass(frozen=True)
class DataPathLayerSpec:
    """One of the 8 hardware/software layers from storage media to GPU HBM."""

    order: int
    layer_name: str
    latency_min_us: float
    latency_max_us: float
    primary_tool: str
    saturation_signal: str


EIGHT_LAYER_DATA_PATH: Tuple[DataPathLayerSpec, ...] = (
    DataPathLayerSpec(
        order=1,
        layer_name="Storage Media (NVMe/SSD/HDD)",
        latency_min_us=10.0,
        latency_max_us=10_000.0,
        primary_tool="iostat -x 1 / smartctl -a",
        saturation_signal="%util == 100.0 or r_await > 5 ms on NVMe",
    ),
    DataPathLayerSpec(
        order=2,
        layer_name="Storage Server CPU & Controller",
        latency_min_us=100.0,
        latency_max_us=2_300.0,
        primary_tool="lctl get_param obdfilter.*.brw_stats / iotop",
        saturation_signal="RPC slots full (256/256) or server cache hit ratio < 20%",
    ),
    DataPathLayerSpec(
        order=3,
        layer_name="Storage Network Fabric (RoCEv2 / IB / TCP)",
        latency_min_us=0.3,
        latency_max_us=100.0,
        primary_tool="ethtool -S / iperf3 / ibstat",
        saturation_signal="rx_dropped > 0, TCP retransmits, or link < 80% rated speed",
    ),
    DataPathLayerSpec(
        order=4,
        layer_name="Client Filesystem Driver (Lustre/WEKA/NFS)",
        latency_min_us=50.0,
        latency_max_us=5_000.0,
        primary_tool="lctl get_param llite.*.stats / strace -c",
        saturation_signal="open/getattr latency > 2000 us or D-state tasks in rpc_wait",
    ),
    DataPathLayerSpec(
        order=5,
        layer_name="Kernel OS Page Cache",
        latency_min_us=1.0,
        latency_max_us=10_000.0,
        primary_tool="vmstat 1 / /proc/pressure/memory",
        saturation_signal="high page cache churn, kswapd active, cpu wa > 10%",
    ),
    DataPathLayerSpec(
        order=6,
        layer_name="Host CPU DRAM & NUMA Interconnect",
        latency_min_us=0.05,
        latency_max_us=0.12,
        primary_tool="numactl --hardware / perf record",
        saturation_signal="__memcpy_avx2 consuming CPU or cross-socket UPI/Infinity Fabric traffic",
    ),
    DataPathLayerSpec(
        order=7,
        layer_name="PCIe Bus / Switch Fabric (Gen4/Gen5 x16)",
        latency_min_us=1.0,
        latency_max_us=10.0,
        primary_tool="lspci -vvv / nvidia-smi topo -m / nvidia-smi dmon -s t",
        saturation_signal="path traverses SYS/NODE instead of PIX/PHB or unpinned pageable DMA",
    ),
    DataPathLayerSpec(
        order=8,
        layer_name="GPU HBM (HBM3 / HBM3e)",
        latency_min_us=0.001,
        latency_max_us=0.01,
        primary_tool="nvidia-smi dmon / Nsight Systems",
        saturation_signal="SM activity oscillating 24%-94% waiting on H2D copy stream",
    ),
)


def evaluate_metadata_bottleneck(
    num_workers: int,
    target_mb_per_s_per_worker: float,
    avg_file_size_kb: float,
    mds_capacity_ops_per_s: int,
    num_osts: int = 48,
    ost_bw_mb_per_s: float = 800.0,
) -> Dict[str, float | bool | str]:
    """Calculate metadata operations vs raw OST bandwidth for a dataset layout.

    Mirrors the Lustre production scenario: 48 OSTs * 800 MB/s = 38.4 GB/s raw bandwidth,
    128 workers * 150 MB/s = 19.2 GB/s expected, 220 KB files -> 681.8 opens/s/worker
    -> 87,273 opens/s vs 50,000 MDS capacity.
    """
    if num_workers <= 0 or target_mb_per_s_per_worker <= 0 or avg_file_size_kb <= 0:
        raise ValueError("num_workers, target_mb_per_s_per_worker, and avg_file_size_kb must be > 0")

    # Standard dataset scales from production scenarios: 18,000,000 files -> 750,000 shards (or 15,000,000 files)
    reference_file_counts = (18_000_000, 15_000_000, 750_000)
    raw_array_bw_gb_s = (num_osts * ost_bw_mb_per_s) / 1000.0
    expected_agg_bw_mb_s = num_workers * target_mb_per_s_per_worker  # e.g., 19,200 MB/s
    expected_agg_bw_gb_s = expected_agg_bw_mb_s / 1000.0
    files_per_sec_per_worker = round((target_mb_per_s_per_worker * 1000.0) / avg_file_size_kb)
    required_open_ops_per_s = num_workers * files_per_sec_per_worker

    mds_overload_ratio = required_open_ops_per_s / float(mds_capacity_ops_per_s)
    is_mds_bottlenecked = required_open_ops_per_s > mds_capacity_ops_per_s

    if is_mds_bottlenecked:
        delivered_bw_gb_s = expected_agg_bw_gb_s / mds_overload_ratio
    else:
        delivered_bw_gb_s = min(expected_agg_bw_gb_s, raw_array_bw_gb_s)

    return {
        "reference_file_counts": reference_file_counts,
        "raw_array_bw_gb_s": round(raw_array_bw_gb_s, 2),
        "expected_agg_bw_mb_s": round(expected_agg_bw_mb_s, 1),
        "expected_agg_bw_gb_s": round(expected_agg_bw_gb_s, 2),
        "files_per_sec_per_worker": round(files_per_sec_per_worker, 2),
        "required_open_ops_per_s": round(required_open_ops_per_s, 1),
        "mds_capacity_ops_per_s": mds_capacity_ops_per_s,
        "mds_overload_pct": round((mds_overload_ratio - 1.0) * 100.0, 1),
        "is_mds_bottlenecked": is_mds_bottlenecked,
        "estimated_delivered_bw_gb_s": round(delivered_bw_gb_s, 2),
        "bottleneck_layer": "metadata_server" if is_mds_bottlenecked else "bandwidth_ok",
    }


def compare_traditional_vs_gds_path(
    payload_gb: float,
    pcie_gen_bw_gb_s: float = 32.0,
    host_dram_bw_gb_s: float = 40.0,
    pinned_memory: bool = True,
) -> Dict[str, float | int | str]:
    """Compare memory copies, PCIe traversals, and latency of Bounce-Buffer vs GDS."""
    if payload_gb <= 0:
        raise ValueError("payload_gb must be positive")

    # Traditional path:
    # 1) Storage/NIC -> Host Page Cache (DMA across PCIe + DRAM write)
    # 2) Host Page Cache -> User-space buffer (CPU copy: DRAM read + DRAM write)
    # 3) User-space buffer -> Pinned staging buffer (if not pre-pinned: DRAM read + DRAM write)
    # 4) Pinned buffer -> GPU HBM (DMA across PCIe + HBM write)
    traditional_memory_copies = 3 if pinned_memory else 4
    traditional_pcie_traversals = 2
    traditional_cpu_memcpy_calls = 1 if pinned_memory else 2
    # Each CPU memcpy touches DRAM twice (read + write), plus 2 DMA DRAM touches (write + read)
    traditional_dram_bytes_factor = 4.0 if pinned_memory else 6.0

    # GDS path:
    # 1) Storage/NIC -> PCIe Switch -> GPU HBM (1 direct P2P DMA copy, 0 host DRAM payload copies)
    gds_memory_copies = 1
    gds_pcie_traversals = 1
    gds_cpu_memcpy_calls = 0
    gds_dram_bytes_factor = 0.0

    # Effective throughput model calibrated to gdsio benchmark (8.0 GB/s CPU vs 9.6 GB/s GDS, +20%)
    base_trad_bw_gb_s = min(pcie_gen_bw_gb_s / 2.0, host_dram_bw_gb_s / traditional_dram_bytes_factor)
    if not pinned_memory:
        base_trad_bw_gb_s *= 0.65
    gds_bw_gb_s = min(pcie_gen_bw_gb_s * 0.85, base_trad_bw_gb_s * 1.20)

    trad_time_s = payload_gb / base_trad_bw_gb_s
    gds_time_s = payload_gb / gds_bw_gb_s

    return {
        "payload_gb": payload_gb,
        "traditional_memory_copies": traditional_memory_copies,
        "traditional_pcie_traversals": traditional_pcie_traversals,
        "traditional_cpu_memcpy_calls": traditional_cpu_memcpy_calls,
        "traditional_dram_traffic_gb": round(payload_gb * traditional_dram_bytes_factor, 2),
        "gds_memory_copies": gds_memory_copies,
        "gds_pcie_traversals": gds_pcie_traversals,
        "gds_cpu_memcpy_calls": gds_cpu_memcpy_calls,
        "gds_dram_traffic_gb": round(payload_gb * gds_dram_bytes_factor, 2),
        "traditional_effective_bw_gb_s": round(base_trad_bw_gb_s, 2),
        "gds_effective_bw_gb_s": round(gds_bw_gb_s, 2),
        "traditional_transfer_time_s": round(trad_time_s, 3),
        "gds_transfer_time_s": round(gds_time_s, 3),
        "throughput_uplift_pct": round(((gds_bw_gb_s / base_trad_bw_gb_s) - 1.0) * 100.0, 1),
    }


def compute_cluster_storage_scaling(
    per_gpu_mb_s: float = 200.0,
    gpus_per_node: int = 8,
    gpus_per_nvl_rack: int = 72,
    cluster_gpus: int = 1024,
    checkpoint_size_gb: float = 2000.0,
    max_checkpoint_stall_s: float = 60.0,
    single_ost_mb_s: float = 800.0,
) -> Dict[str, float | int]:
    """Compute per-GPU, 8-GPU node, 72-GPU NVL72 rack, and cluster storage bandwidth & striping."""
    node_read_gb_s = (per_gpu_mb_s * gpus_per_node) / 1000.0
    rack_read_gb_s = (per_gpu_mb_s * gpus_per_nvl_rack) / 1000.0
    cluster_read_gb_s = (per_gpu_mb_s * cluster_gpus) / 1000.0

    required_ckpt_write_gb_s = checkpoint_size_gb / max_checkpoint_stall_s
    single_ost_gb_s = single_ost_mb_s / 1000.0
    min_ost_stripes_for_ckpt = int((required_ckpt_write_gb_s / single_ost_gb_s) + 0.999999)

    return {
        "per_gpu_mb_s": per_gpu_mb_s,
        "node_8gpu_read_gb_s": round(node_read_gb_s, 2),
        "nvl72_rack_read_gb_s": round(rack_read_gb_s, 2),
        "cluster_read_gb_s": round(cluster_read_gb_s, 2),
        "checkpoint_size_gb": checkpoint_size_gb,
        "max_checkpoint_stall_s": max_checkpoint_stall_s,
        "required_ckpt_write_gb_s": round(required_ckpt_write_gb_s, 2),
        "min_ost_stripes_for_ckpt": min_ost_stripes_for_ckpt,
    }


def evaluate_numa_pcie_locality(
    gpu_numa_node: int,
    nic_or_nvme_numa_node: int,
    dataloader_cpu_numa_node: int,
    pcie_topo_relation: str,
    base_bandwidth_gb_s: float = 10.0,
) -> Dict[str, float | bool | str]:
    """Evaluate NUMA and PCIe topology alignment for storage NICs, NVMe drives, and GPUs.

    `pcie_topo_relation` is one of `PIX`, `PXB`, `PHB`, `NODE`, `SYS` from `nvidia-smi topo -m`.
    """
    valid_relations = {"PIX", "PXB", "PHB", "NODE", "SYS"}
    if pcie_topo_relation not in valid_relations:
        raise ValueError(f"pcie_topo_relation must be one of {sorted(valid_relations)}")

    gds_optimal = (
        gpu_numa_node == nic_or_nvme_numa_node
        and pcie_topo_relation in {"PIX", "PXB", "PHB"}
    )
    cpu_loader_aligned = (
        dataloader_cpu_numa_node == gpu_numa_node
        and dataloader_cpu_numa_node == nic_or_nvme_numa_node
    )

    penalty_factor = 1.0
    if pcie_topo_relation == "SYS":
        penalty_factor *= 0.72  # Cross-socket UPI / Infinity Fabric penalty (~28% loss)
    elif pcie_topo_relation == "NODE":
        penalty_factor *= 0.88  # Cross-host-bridge within NUMA node

    if not cpu_loader_aligned:
        penalty_factor *= 0.80  # Remote DRAM access (50 ns -> 100+ ns, 20% throughput loss)

    delivered_bw_gb_s = round(base_bandwidth_gb_s * penalty_factor, 2)
    dram_latency_ns = 55.0 if cpu_loader_aligned else 110.0

    return {
        "gpu_numa_node": gpu_numa_node,
        "nic_or_nvme_numa_node": nic_or_nvme_numa_node,
        "dataloader_cpu_numa_node": dataloader_cpu_numa_node,
        "pcie_topo_relation": pcie_topo_relation,
        "gds_p2p_supported_and_optimal": gds_optimal,
        "cpu_loader_numa_aligned": cpu_loader_aligned,
        "dram_access_latency_ns": dram_latency_ns,
        "delivered_bandwidth_gb_s": delivered_bw_gb_s,
        "throughput_retention_pct": round(penalty_factor * 100.0, 1),
    }


def evaluate_page_cache_vs_odirect(
    dataset_working_set_gb: float,
    host_free_ram_gb: float,
    access_pattern: str,
    use_o_direct: bool,
) -> Dict[str, float | bool | str]:
    """Model Linux Page Cache pollution vs O_DIRECT bypass for AI datasets."""
    if dataset_working_set_gb <= 0 or host_free_ram_gb <= 0:
        raise ValueError("dataset_working_set_gb and host_free_ram_gb must be > 0")

    fits_in_ram = dataset_working_set_gb <= (host_free_ram_gb * 0.85)

    if use_o_direct:
        cache_hit_rate = 0.0
        page_cache_thrashing = False
        cpu_wa_pct = 2.0
        recommended_mode = "O_DIRECT_enabled_no_cache_pollution"
    else:
        if fits_in_ram:
            cache_hit_rate = 0.95
            page_cache_thrashing = False
            cpu_wa_pct = 1.5
            recommended_mode = "page_cache_warm_epoch2_accelerated"
        else:
            # Working set exceeds RAM; random or shuffled epoch scans evict pages before reuse
            cache_hit_rate = 0.04 if access_pattern == "random_epoch_shuffle" else 0.15
            page_cache_thrashing = True
            cpu_wa_pct = 15.0
            recommended_mode = "switch_to_O_DIRECT_or_GDS_to_stop_kswapd_thrash"

    return {
        "dataset_working_set_gb": dataset_working_set_gb,
        "host_free_ram_gb": host_free_ram_gb,
        "fits_in_ram": fits_in_ram,
        "use_o_direct": use_o_direct,
        "estimated_cache_hit_rate": cache_hit_rate,
        "page_cache_thrashing": page_cache_thrashing,
        "estimated_cpu_iowait_pct": cpu_wa_pct,
        "recommendation": recommended_mode,
    }
