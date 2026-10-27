"""Chapter 13.8: Capacity, performance and cost planning.

Pure Python 3 standard-library reference models for:
1. Six-Dimension AI Storage Capacity & Performance Sizing (V15 Ch. 10 & Ch. 12):
   - Dimension 1 (Usable Capacity): raw dataset + processed shards + rolling K checkpoints +
     archive checkpoints + scratch/model artifacts + user homes/logs + capacity headroom (30%,
     since filesystems degrade as fill approaches 90%).
   - Worked 1.3B-parameter model example (V15 Ch. 10): 500 GB dataset + 2,000 GB rolling
     checkpoints (20 x 100 GB) + 1,000 GB archive checkpoints (10 x 100 GB) + 50 GB model
     artifacts + 10 GB logs = 3,560 GB subtotal + 30% headroom (1,068 GB) = 4,628 GB (~5 TB).
   - Worked 256-GPU cluster interview sizing (V15 Ch. 10): 5 TB datasets + 1 TB checkpoints
     + 30% headroom (1.8 TB) = 7.8 TB minimum usable capacity; Lustre 12-node cluster (8 OST
     nodes + 2 MDS + 1 backup + 1 MGS) with 12 TB SSD per OST = 96 TB raw, 80 TB usable.
   - Dimension 2 (Read Bandwidth): per-GPU ingestion (200 MB/s per GPU = 1.6 GB/s per 8-GPU
     node, 14.4 GB/s [14-20 GB/s envelope] per 72-GPU GB200/GB300 NVL72 rack, AISPE Ch. 5)
     and concurrent job model/dataset load budget (e.g., 100 GB / 30 s = 3.3333 GB/s per job
     x 3 jobs = 10.0 GB/s; Lustre 24 OSTs x 800 MB/s = 19.2 GB/s vs BeeGFS 8 nodes x 1.5 GB/s
     = 12.0 GB/s vs single NFS server 2.0 GB/s).
   - Dimension 3 (Write / Checkpoint Burst Bandwidth): B_req = CheckpointBytes / T_budget
     (e.g., 100 GB / 300 s = 333.33 MB/s per job, or 8 ranks x 333.33 MB/s = 2.6667 GB/s
     parallel write vs Lustre 24 OSTs x 400 MB/s = 9.6 GB/s; 70B Llama mixed-precision AdamW
     checkpoint = 14 bytes/param x 70B = 980 GB [~1 TB] vs 16 bytes/param = 1,120 GB [~1.1 TB]
     training memory, sharded across 64 GPUs = 15.3125 GB/GPU and 122.5 GB/node, V21 Ch. 04;
     synchronous 500 GB checkpoint at 1 GB/s stalls 500 s vs async local NVMe staging at
     20 GB/s = 25 s [20x stall reduction], V15 Ch. 12).
   - Dimension 4 (Metadata Rate): (batch_size_files x batches_per_sec) vs MDS ceiling
     (256 files x 100 batches/sec = 25,600 opens/sec; 1.2M files -> 4.8M total metadata ops
     per epoch; Lustre single MDS 50,000 ops/sec, 2 MDTs 100,000 ops/sec, DNE 500,000+ ops/sec;
     BeeGFS 50,000-100,000 ops/sec per MDS; single NFS 5,000 ops/sec; WebDataset/tar sharding
     reduces metadata ops by 1,000x, V15 Ch. 10 & Ch. 12).
   - Dimension 5 (Burst & Headroom Budgeting): baseline sustained rate + checkpoint burst peak
     (1 GB/s sustained + 5 GB/s checkpoint burst = 6 GB/s peak; 2.0x overbuild rule: 3 GB/s ->
     6 GB/s, 10 GB/s -> 20 GB/s; headroom targets: 30% capacity, 50% bandwidth, 40% metadata,
     and 24-hour disk/node rebuild reserve, V15 Ch. 10).
2. NVIDIA DGX SuperPOD High-Performance Storage (HPS) Tier Sizing (`superpod-gb300-ra`, `superpod-b200-dc`):
   - GB300 NVL72 SuperPOD: 72 GPUs across 18 compute trays per rack (4x 3.84 TB E1.S NVMe RAID0
     = 15.36 TB local scratch + 1x 1.92 TB M.2 OS NVMe per tray; 276.48 TB RAID0 scratch per rack),
     8 racks (576 GPUs, 144 trays, 2,211.84 TB local NVMe scratch, 1.2 MW TDP) per Scalable Unit (SU),
     scaling up to 16 SUs (128 racks, 9,216 GPUs) with dedicated 400 Gbps RoCEv2 storage port per tray
     on SN5600D Ethernet fabric (64x400GbE at 2 SUs, 128x400GbE at 4 SUs, 256x400GbE at 8 SUs,
     1024x400GbE at 16 SUs).
   - B200 SuperPOD: up to 32 DGX B200 systems (256 GPUs, 458 kW) per SU, up to 127 DGX B200 systems
     per 4-SU SuperPOD (1 system displaced by Unified Fabric Manager [UFM] appliance).
   - SuperPOD HPS Bandwidth Tiers (`superpod-gb300-ra` Table 4 & Table 5):
     * Standard Tier (LLM/fine-tuning, datasets fit in memory cache): 90 GB/s read and 45 GB/s write
       per SU (360 GB/s read and 180 GB/s write for 4 SUs).
     * Enhanced Tier (multimodal training, datasets exceed local memory cache): 280 GB/s read and
       140 GB/s write per SU (1,120 GB/s read and 560 GB/s write for 4 SUs).
3. Erasure Coding vs Replication Usable-to-Raw Efficiency & Rebuild Reserve:
   - Compares 2x replication (50.0% / 50.00% efficiency, 2.0x / 2.0000x raw multiplier, 2,000.00 TB raw and 1,000.00 TB overhead for 1,000 TB usable),
     3x replication (33.33% efficiency, 3.0x / 3.0000x raw multiplier, 3,000.00 TB raw and 2,000.00 TB overhead),
     WekaFS 6+2 (75.0% / 75.00%, 1.3333x, 1,333.33 TB raw, 333.33 TB overhead) and 16+2 (88.89%, 1.1250x, 1,125.00 TB raw / 1.125 PB, 125.00 TB overhead),
     Lustre/ZFS 8+2 RAID-Z2/EC (80.0% / 80.00%, 1.2500x, 1,250.00 TB raw, 250.00 TB overhead), and
     VAST DASE 146+4 wide erasure stripe (97.33% efficiency, 1.0274x, 1,027.40 TB raw / 1.027 PB, 27.40 TB / 2.67% parity),
     plus 30% capacity headroom (1 / 1.30 = 76.9% steady fill) and 24-hour rebuild bandwidth sizing.
4. Hot / Warm / Cold / Archive Multi-Tier Storage Architecture & Cost Calculator (V15 Ch. 10, V21 Ch. 04):
   - Four-tier unit economics: Hot NVMe ($5.00/GB-year, <1 ms, 3-7 GB/s per drive), Warm Parallel FS
     ($0.50/GB-year, 1-5 ms, 1-2 GB/s per server), Cold Object S3/GCS ($0.02/GB-year or $0.023/GB-month
     = $2,300/month for 100 TB, 50-100 ms), and Archive Glacier/Tape ($0.001/GB-year, hours).
   - Reproduces V15 Ch. 10 1.3B-model tiering budget: 100 GB Hot ($500) + 2,500 GB Warm ($1,250)
     + 5,000 GB Cold ($100) + 10,000 GB Archive ($10) = $1,860/year.
5. 3-Year Storage TCO, $/TB-Month & Idle-GPU Opportunity Cost Calculator (V15 Ch. 10, V21 Ch. 11-12):
   - 128-GPU A100 cluster economics (V15 Ch. 10): 128 GPUs x 4 kW x $0.10/kWh = $51.20/hr (~$51/hr)
     power + 128 GPUs x $3.00/hr lease = $384/hr -> $435/hr total cluster burn rate; 10% data stall
     (2.4 hr/day) wastes $1,044/day = $381,060/year (~$380K/year), so a $100K storage upgrade pays back
     in 95.79 days (95.8 days) and is 26.24% of 1 year of wasted compute (or 2.6% over a 10x larger baseline);
     122.5 GB node shard stages in 6.125 s at 20 GB/s or 12.25 seconds at 10 GB/s; 500 GB at 20 GB/s saves 475 seconds;
     100 GB / 30 s = 3.33 GB/s (3.3333 GB/s).
   - Per-GPU-hour stall waste comparison (V15 Ch. 10): Option A Minimal Storage (5% stall across
     128 GPUs at $435/GPU-hr = $2,784/hr waste = $24,387,840/yr [~$24.4M/yr] + $5K/yr maint) vs
     Option B Balanced Lustre 1 PB + NVMe cache (1% stall = $556.80/hr [~$558/hr] = $4.9M/yr +
     $80K Lustre + $10K/yr + $500K NVMe + $5K/yr = ~$5.5M Year-1 total), saving $18.9M/year.
   - 3-Year AI Factory TCO & $/TB-month model (V21 Ch. 11 & Ch. 12): 464->800->900 GPU refresh
     ($19.8M CapEx + $9.0M OpEx = $28.8M 3-year TCO across 1,612 GPU-years = $17,866/GPU-year
     [~$17.9K]) and 1,200-GPU deployment ($36M GPU + $1.5M network + $2.0M storage + $4.5M
     power/chassis/install = $44.0M CapEx + $26.2M 3-year OpEx = $70.2M 3-year TCO = $19.5K/GPU-yr;
     storage CapEx is 4.55% of CapEx and 2.85% of total TCO).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. Six-Dimension AI Storage Capacity & Performance Sizing (V15 Ch. 10 & 12)
# ---------------------------------------------------------------------------

HEADROOM_RECOMMENDATIONS: Dict[str, float] = {
    "capacity_headroom_ratio": 0.30,      # +30% capacity headroom (degrades approaching 90% fill)
    "max_safe_fill_ratio": 0.90,          # Never operate parallel FS near/above 90% fill
    "bandwidth_headroom_ratio": 0.50,     # +50% steady-state bandwidth headroom (2.0x burst overbuild)
    "burst_overbuild_multiplier": 2.0,    # Overbuild sustained bandwidth by 2x for 1x burst headroom
    "metadata_headroom_ratio": 0.40,      # +40% metadata ops/sec headroom (scales non-linearly)
    "rebuild_sla_hours": 24.0,            # Reserve capacity/bandwidth to rebuild failed disk/node in <=24h
}


@dataclass(frozen=True)
class UsableCapacityPlan:
    raw_dataset_gb: float
    processed_shards_gb: float
    checkpoint_size_gb: float
    rolling_checkpoints_k: int
    archive_checkpoints_m: int
    rolling_checkpoints_gb: float
    archive_checkpoints_gb: float
    scratch_and_artifacts_gb: float
    user_homes_and_logs_gb: float
    subtotal_usable_gb: float
    headroom_ratio: float
    headroom_gb: float
    total_usable_gb: float
    total_usable_tb: float


def calculate_usable_capacity_plan(
    raw_dataset_gb: float = 500.0,
    processed_shards_gb: float = 0.0,
    checkpoint_size_gb: float = 100.0,
    rolling_checkpoints_k: int = 20,
    archive_checkpoints_m: int = 10,
    scratch_and_artifacts_gb: float = 50.0,
    user_homes_and_logs_gb: float = 10.0,
    headroom_ratio: float = 0.30,
) -> UsableCapacityPlan:
    """Size usable storage capacity across datasets, rolling/archive checkpoints, scratch, homes, and headroom."""
    if raw_dataset_gb < 0 or processed_shards_gb < 0 or checkpoint_size_gb < 0:
        raise ValueError("Storage capacities must be non-negative")
    if rolling_checkpoints_k < 0 or archive_checkpoints_m < 0 or headroom_ratio < 0:
        raise ValueError("Checkpoint counts and headroom_ratio must be non-negative")

    rolling_gb = checkpoint_size_gb * rolling_checkpoints_k
    archive_gb = checkpoint_size_gb * archive_checkpoints_m
    subtotal_gb = (
        raw_dataset_gb
        + processed_shards_gb
        + rolling_gb
        + archive_gb
        + scratch_and_artifacts_gb
        + user_homes_and_logs_gb
    )
    headroom_gb = subtotal_gb * headroom_ratio
    total_gb = subtotal_gb + headroom_gb
    return UsableCapacityPlan(
        raw_dataset_gb=round(raw_dataset_gb, 2),
        processed_shards_gb=round(processed_shards_gb, 2),
        checkpoint_size_gb=round(checkpoint_size_gb, 2),
        rolling_checkpoints_k=rolling_checkpoints_k,
        archive_checkpoints_m=archive_checkpoints_m,
        rolling_checkpoints_gb=round(rolling_gb, 2),
        archive_checkpoints_gb=round(archive_gb, 2),
        scratch_and_artifacts_gb=round(scratch_and_artifacts_gb, 2),
        user_homes_and_logs_gb=round(user_homes_and_logs_gb, 2),
        subtotal_usable_gb=round(subtotal_gb, 2),
        headroom_ratio=headroom_ratio,
        headroom_gb=round(headroom_gb, 2),
        total_usable_gb=round(total_gb, 2),
        total_usable_tb=round(total_gb / 1000.0, 4),
    )


def size_read_bandwidth_requirements(
    num_gpus: int = 64,
    per_gpu_ingest_mb_s: float = 200.0,
    model_or_shard_load_gb: float = 100.0,
    load_time_budget_sec: float = 30.0,
    concurrent_jobs: int = 3,
    lustre_ost_count: int = 24,
    lustre_ost_read_mb_s: float = 800.0,
    beegfs_node_count: int = 8,
    beegfs_node_read_gb_s: float = 1.5,
    nfs_single_server_gb_s: float = 2.0,
) -> Dict[str, float | bool]:
    """Calculate GPU ingestion read bandwidth and concurrent job startup read bandwidth (V15 Ch. 10, AISPE Ch. 5)."""
    if num_gpus <= 0 or load_time_budget_sec <= 0 or concurrent_jobs <= 0:
        raise ValueError("num_gpus, load_time_budget_sec, and concurrent_jobs must be positive")
    gpu_ingest_gb_s = (num_gpus * per_gpu_ingest_mb_s) / 1000.0
    eight_gpu_node_gb_s = (8 * per_gpu_ingest_mb_s) / 1000.0
    nvl72_rack_gb_s = (72 * per_gpu_ingest_mb_s) / 1000.0
    per_job_load_gb_s = model_or_shard_load_gb / load_time_budget_sec
    total_job_load_gb_s = per_job_load_gb_s * concurrent_jobs
    lustre_read_gb_s = (lustre_ost_count * lustre_ost_read_mb_s) / 1000.0
    beegfs_read_gb_s = beegfs_node_count * beegfs_node_read_gb_s
    return {
        "num_gpus": float(num_gpus),
        "per_gpu_ingest_mb_s": per_gpu_ingest_mb_s,
        "eight_gpu_node_ingest_gb_s": round(eight_gpu_node_gb_s, 2),
        "nvl72_rack_ingest_gb_s": round(nvl72_rack_gb_s, 2),
        "cluster_gpu_ingest_gb_s": round(gpu_ingest_gb_s, 2),
        "per_job_load_gb_s": round(per_job_load_gb_s, 4),
        "concurrent_jobs": float(concurrent_jobs),
        "total_job_load_gb_s": round(total_job_load_gb_s, 2),
        "lustre_24_ost_read_gb_s": round(lustre_read_gb_s, 2),
        "beegfs_8_node_read_gb_s": round(beegfs_read_gb_s, 2),
        "nfs_single_server_gb_s": round(nfs_single_server_gb_s, 2),
        "lustre_meets_load_budget": lustre_read_gb_s >= total_job_load_gb_s,
        "beegfs_meets_load_budget": beegfs_read_gb_s >= total_job_load_gb_s,
        "nfs_meets_load_budget": nfs_single_server_gb_s >= total_job_load_gb_s,
    }


def size_checkpoint_write_and_burst_bandwidth(
    model_params_billions: float = 70.0,
    checkpoint_bytes_per_param: int = 14,
    training_mem_bytes_per_param: int = 16,
    num_gpus: int = 64,
    gpus_per_node: int = 8,
    checkpoint_write_budget_sec: float = 300.0,
    sustained_read_gb_s: float = 1.0,
    checkpoint_burst_gb_s: float = 5.0,
    local_nvme_staging_gb_s_per_node: float = 20.0,
) -> Dict[str, float]:
    """Calculate sharded checkpoint sizes, required write bandwidth B_req = Bytes / T_budget, and burst overbuild."""
    if model_params_billions <= 0 or num_gpus <= 0 or gpus_per_node <= 0 or checkpoint_write_budget_sec <= 0:
        raise ValueError("Model parameters, GPU counts, and checkpoint budget must be positive")
    checkpoint_total_gb = model_params_billions * checkpoint_bytes_per_param
    training_mem_total_gb = model_params_billions * training_mem_bytes_per_param
    per_gpu_shard_gb = checkpoint_total_gb / num_gpus
    per_node_shard_gb = per_gpu_shard_gb * gpus_per_node
    required_write_gb_s = checkpoint_total_gb / checkpoint_write_budget_sec
    required_write_mb_s = required_write_gb_s * 1000.0
    local_nvme_stage_sec = per_node_shard_gb / local_nvme_staging_gb_s_per_node
    peak_concurrent_gb_s = sustained_read_gb_s + checkpoint_burst_gb_s
    recommended_overbuild_gb_s = sustained_read_gb_s * HEADROOM_RECOMMENDATIONS["burst_overbuild_multiplier"]
    return {
        "model_params_billions": model_params_billions,
        "checkpoint_total_gb": round(checkpoint_total_gb, 2),
        "training_mem_total_gb": round(training_mem_total_gb, 2),
        "per_gpu_shard_gb": round(per_gpu_shard_gb, 4),
        "per_node_shard_gb": round(per_node_shard_gb, 2),
        "checkpoint_write_budget_sec": checkpoint_write_budget_sec,
        "required_write_gb_s": round(required_write_gb_s, 4),
        "required_write_mb_s": round(required_write_mb_s, 2),
        "local_nvme_stage_sec": round(local_nvme_stage_sec, 4),
        "sustained_read_gb_s": sustained_read_gb_s,
        "checkpoint_burst_gb_s": checkpoint_burst_gb_s,
        "peak_concurrent_gb_s": round(peak_concurrent_gb_s, 2),
        "recommended_2x_overbuild_gb_s": round(recommended_overbuild_gb_s, 2),
    }


def size_metadata_ops_and_sharding(
    dataset_file_count: int = 1_200_000,
    batch_size_files: int = 256,
    batches_per_sec: int = 100,
    sharding_reduction_factor: int = 1000,
    lustre_single_mds_ops_s: int = 50_000,
    lustre_two_mdt_ops_s: int = 100_000,
    beegfs_single_mds_ops_s: int = 50_000,
    nfs_single_server_ops_s: int = 5_000,
    metadata_headroom_ratio: float = 0.40,
) -> Dict[str, float | int | bool]:
    """Calculate per-epoch metadata operations, peak open/sec rate, and WebDataset sharding impact (V15 Ch. 10)."""
    if dataset_file_count <= 0 or batch_size_files <= 0 or batches_per_sec <= 0 or sharding_reduction_factor <= 0:
        raise ValueError("All metadata sizing inputs must be positive")
    opens_per_epoch = dataset_file_count
    closes_per_epoch = dataset_file_count
    stats_per_epoch = dataset_file_count * 2
    total_ops_per_epoch = opens_per_epoch + closes_per_epoch + stats_per_epoch
    raw_opens_per_sec = batch_size_files * batches_per_sec
    required_mds_capacity_with_headroom = raw_opens_per_sec * (1.0 + metadata_headroom_ratio)
    sharded_opens_per_sec = raw_opens_per_sec / sharding_reduction_factor
    return {
        "dataset_file_count": dataset_file_count,
        "opens_per_epoch": opens_per_epoch,
        "closes_per_epoch": closes_per_epoch,
        "stats_per_epoch": stats_per_epoch,
        "total_metadata_ops_per_epoch": total_ops_per_epoch,
        "raw_opens_per_sec": raw_opens_per_sec,
        "required_mds_ops_s_with_40pct_headroom": round(required_mds_capacity_with_headroom, 2),
        "sharded_opens_per_sec": round(sharded_opens_per_sec, 2),
        "lustre_single_mds_sufficient": lustre_single_mds_ops_s >= required_mds_capacity_with_headroom,
        "lustre_two_mdt_sufficient": lustre_two_mdt_ops_s >= required_mds_capacity_with_headroom,
        "beegfs_single_mds_sufficient": beegfs_single_mds_ops_s >= required_mds_capacity_with_headroom,
        "nfs_sufficient_for_raw": nfs_single_server_ops_s >= raw_opens_per_sec,
    }


# ---------------------------------------------------------------------------
# 2. NVIDIA DGX SuperPOD High-Performance Storage (HPS) Sizing (`superpod-gb300-ra`, `superpod-b200-dc`)
# ---------------------------------------------------------------------------

SUPERPOD_HPS_TIERS_PER_SU: Dict[str, Dict[str, float | str]] = {
    "Standard": {
        "read_gb_s_per_su": 90.0,
        "write_gb_s_per_su": 45.0,
        "four_su_read_gb_s": 360.0,
        "four_su_write_gb_s": 180.0,
        "workload_profile": "Concurrent LLM or fine-tuning jobs where datasets fit in local memory cache",
    },
    "Enhanced": {
        "read_gb_s_per_su": 280.0,
        "write_gb_s_per_su": 140.0,
        "four_su_read_gb_s": 1120.0,
        "four_su_write_gb_s": 560.0,
        "workload_profile": "Concurrent multimodal training jobs where datasets exceed local memory cache",
    },
}


def size_superpod_storage_by_su(
    num_sus: int = 4,
    tier: str = "Enhanced",
    platform: str = "GB300",
) -> Dict[str, float | int | str]:
    """Calculate NVIDIA DGX SuperPOD High-Performance Storage bandwidth, local NVMe scratch, and fabric links."""
    if num_sus <= 0:
        raise ValueError("num_sus must be positive")
    if tier not in SUPERPOD_HPS_TIERS_PER_SU:
        raise ValueError(f"Unsupported SuperPOD storage tier: {tier}")
    if platform not in {"GB300", "B200"}:
        raise ValueError(f"Unsupported SuperPOD platform: {platform}")

    tier_spec = SUPERPOD_HPS_TIERS_PER_SU[tier]
    read_per_su = float(tier_spec["read_gb_s_per_su"])
    write_per_su = float(tier_spec["write_gb_s_per_su"])
    aggregate_read_gb_s = num_sus * read_per_su
    aggregate_write_gb_s = num_sus * write_per_su

    if platform == "GB300":
        racks_per_su = 8
        gpus_per_rack = 72
        trays_per_rack = 18
        local_nvme_per_tray_tb = 4 * 3.84  # 15.36 TB RAID0 E1.S NVMe per tray
        os_nvme_per_tray_tb = 1.92
        total_racks = num_sus * racks_per_su
        total_gpus = total_racks * gpus_per_rack
        total_trays = total_racks * trays_per_rack
        total_local_raid0_tb = total_trays * local_nvme_per_tray_tb
        tdp_mw = num_sus * 1.2
        storage_400gbe_links = {2: 64, 4: 128, 8: 256, 16: 1024}.get(num_sus, num_sus * 32)
        return {
            "platform": "DGX GB300 NVL72 SuperPOD",
            "tier": tier,
            "num_sus": num_sus,
            "total_racks": total_racks,
            "total_gpus": total_gpus,
            "total_compute_trays": total_trays,
            "local_nvme_per_tray_tb": round(local_nvme_per_tray_tb, 2),
            "os_nvme_per_tray_tb": os_nvme_per_tray_tb,
            "total_local_raid0_scratch_tb": round(total_local_raid0_tb, 2),
            "read_gb_s_per_su": read_per_su,
            "write_gb_s_per_su": write_per_su,
            "aggregate_read_gb_s": round(aggregate_read_gb_s, 2),
            "aggregate_write_gb_s": round(aggregate_write_gb_s, 2),
            "storage_fabric_400gbe_links": storage_400gbe_links,
            "total_tdp_mw": round(tdp_mw, 2),
        }

    # DGX B200 SuperPOD (`superpod-b200-dc`): up to 32 systems/SU (458 kW/SU); 127 systems at 4 SUs (1 UFM displaced)
    systems_per_su = 32
    total_systems = 127 if num_sus == 4 else num_sus * systems_per_su
    total_gpus = total_systems * 8
    total_power_kw = num_sus * 458.0
    return {
        "platform": "DGX B200 SuperPOD",
        "tier": tier,
        "num_sus": num_sus,
        "total_systems": total_systems,
        "total_gpus": total_gpus,
        "read_gb_s_per_su": read_per_su,
        "write_gb_s_per_su": write_per_su,
        "aggregate_read_gb_s": round(aggregate_read_gb_s, 2),
        "aggregate_write_gb_s": round(aggregate_write_gb_s, 2),
        "total_power_kw": round(total_power_kw, 2),
    }


# ---------------------------------------------------------------------------
# 3. Erasure Coding vs Replication Usable-to-Raw Efficiency & Rebuild Math
# ---------------------------------------------------------------------------

PROTECTION_SCHEMES: Dict[str, Tuple[int, int]] = {
    "2x_replication": (1, 1),
    "3x_replication": (1, 2),
    "weka_6_plus_2": (6, 2),
    "lustre_zfs_8_plus_2": (8, 2),
    "weka_16_plus_2": (16, 2),
    "vast_146_plus_4": (146, 4),
}


def calculate_raw_from_usable_capacity(
    usable_tb: float,
    data_chunks_n: int = 8,
    parity_or_mirror_chunks_k: int = 2,
    capacity_headroom_ratio: float = 0.0,
    failed_drive_or_node_tb: float = 15.36,
    rebuild_sla_hours: float = 24.0,
) -> Dict[str, float]:
    """Convert required usable TB into raw physical TB given N+K erasure coding or replication and rebuild SLA."""
    if usable_tb <= 0 or data_chunks_n <= 0 or parity_or_mirror_chunks_k < 0 or rebuild_sla_hours <= 0:
        raise ValueError("usable_tb, data_chunks_n, and rebuild_sla_hours must be positive")
    total_chunks = data_chunks_n + parity_or_mirror_chunks_k
    usable_to_raw_efficiency = data_chunks_n / total_chunks
    raw_to_usable_multiplier = total_chunks / data_chunks_n
    usable_with_headroom_tb = usable_tb * (1.0 + capacity_headroom_ratio)
    required_raw_tb = usable_with_headroom_tb * raw_to_usable_multiplier
    parity_or_replica_overhead_tb = required_raw_tb - usable_with_headroom_tb
    min_rebuild_mb_s = (failed_drive_or_node_tb * 1_000_000.0) / (rebuild_sla_hours * 3600.0)
    return {
        "usable_tb": round(usable_tb, 2),
        "usable_with_headroom_tb": round(usable_with_headroom_tb, 2),
        "data_chunks_n": float(data_chunks_n),
        "parity_chunks_k": float(parity_or_mirror_chunks_k),
        "usable_to_raw_efficiency_pct": round(usable_to_raw_efficiency * 100.0, 2),
        "raw_to_usable_multiplier": round(raw_to_usable_multiplier, 4),
        "required_raw_tb": round(required_raw_tb, 2),
        "parity_or_replica_overhead_tb": round(parity_or_replica_overhead_tb, 2),
        "min_24h_rebuild_mb_s": round(min_rebuild_mb_s, 2),
    }


# ---------------------------------------------------------------------------
# 4. Multi-Tier Storage Architecture & Cost Model (V15 Ch. 10, V21 Ch. 04)
# ---------------------------------------------------------------------------

STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR: Dict[str, Dict[str, float | str]] = {
    "Hot_NVMe": {
        "cost_per_gb_year_usd": 5.00,
        "latency_ms": 0.5,
        "throughput_gb_s_per_unit": 3.0,
        "use_case": "Active dataset cache and local checkpoint staging",
    },
    "Warm_Parallel_FS": {
        "cost_per_gb_year_usd": 0.50,
        "latency_ms": 3.0,
        "throughput_gb_s_per_unit": 1.5,
        "use_case": "Shared training datasets and active rolling checkpoints (Lustre/BeeGFS/WEKA/VAST)",
    },
    "Cold_Object_S3": {
        "cost_per_gb_year_usd": 0.02,
        "cloud_monthly_per_gb_usd": 0.023,
        "latency_ms": 75.0,
        "throughput_gb_s_per_unit": 0.5,
        "use_case": "Durable source-of-truth datasets and checkpoint backups (S3/GCS)",
    },
    "Archive_Glacier_Tape": {
        "cost_per_gb_year_usd": 0.001,
        "latency_ms": 3_600_000.0,
        "throughput_gb_s_per_unit": 0.1,
        "use_case": "Long-term compliance and historical checkpoint retention",
    },
}


def evaluate_four_tier_storage_budget(
    hot_nvme_gb: float = 100.0,
    warm_parallel_gb: float = 2_500.0,
    cold_object_gb: float = 5_000.0,
    archive_glacier_gb: float = 10_000.0,
) -> Dict[str, float]:
    """Calculate annual storage spend across Hot NVMe, Warm Parallel FS, Cold Object, and Archive tiers (V15 Ch. 10)."""
    hot_cost = hot_nvme_gb * float(STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Hot_NVMe"]["cost_per_gb_year_usd"])
    warm_cost = warm_parallel_gb * float(STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Warm_Parallel_FS"]["cost_per_gb_year_usd"])
    cold_cost = cold_object_gb * float(STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Cold_Object_S3"]["cost_per_gb_year_usd"])
    archive_cost = archive_glacier_gb * float(
        STORAGE_TIER_UNIT_COSTS_PER_GB_YEAR["Archive_Glacier_Tape"]["cost_per_gb_year_usd"]
    )
    total_gb = hot_nvme_gb + warm_parallel_gb + cold_object_gb + archive_glacier_gb
    total_annual_usd = hot_cost + warm_cost + cold_cost + archive_cost
    blended_usd_per_tb_month = (total_annual_usd / 12.0) / (total_gb / 1000.0) if total_gb > 0 else 0.0
    return {
        "hot_nvme_usd_yr": round(hot_cost, 2),
        "warm_parallel_usd_yr": round(warm_cost, 2),
        "cold_object_usd_yr": round(cold_cost, 2),
        "archive_glacier_usd_yr": round(archive_cost, 2),
        "total_capacity_gb": round(total_gb, 2),
        "total_annual_usd": round(total_annual_usd, 2),
        "blended_usd_per_tb_month": round(blended_usd_per_tb_month, 2),
    }


# ---------------------------------------------------------------------------
# 5. 3-Year Storage TCO, $/TB-Month & GPU-Stall Opportunity Cost (V15 Ch. 10, V21 Ch. 11-12)
# ---------------------------------------------------------------------------

def evaluate_idle_gpu_vs_storage_roi(
    num_gpus: int = 128,
    kw_per_gpu: float = 4.0,
    kwh_cost_usd: float = 0.10,
    gpu_lease_per_hr_usd: float = 3.00,
    stall_fraction: float = 0.10,
    storage_upgrade_capex_usd: float = 100_000.0,
) -> Dict[str, float]:
    """Calculate the hourly/daily/annual cost of idle GPUs caused by storage stalls (V15 Ch. 10)."""
    power_hourly_usd = math.floor(num_gpus * kw_per_gpu * kwh_cost_usd)  # V15 Ch. 10: 128 * 4 * 0.10 ≈ $51/hr
    lease_hourly_usd = num_gpus * gpu_lease_per_hr_usd                  # 128 * $3 = $384/hr
    cluster_hourly_usd = power_hourly_usd + lease_hourly_usd            # $435/hr
    idle_hours_per_day = 24.0 * stall_fraction                          # 2.4 hr/day
    daily_stall_waste_usd = idle_hours_per_day * cluster_hourly_usd     # $1,044/day
    annual_stall_waste_usd = daily_stall_waste_usd * 365.0              # $381,060/yr (~$380K/yr)
    payback_days = storage_upgrade_capex_usd / daily_stall_waste_usd if daily_stall_waste_usd > 0 else 0.0
    storage_pct_of_annual_waste = (storage_upgrade_capex_usd / annual_stall_waste_usd) * 100.0
    return {
        "num_gpus": float(num_gpus),
        "power_hourly_usd": round(power_hourly_usd, 2),
        "lease_hourly_usd": round(lease_hourly_usd, 2),
        "cluster_hourly_usd": round(cluster_hourly_usd, 2),
        "idle_hours_per_day": round(idle_hours_per_day, 2),
        "daily_stall_waste_usd": round(daily_stall_waste_usd, 2),
        "annual_stall_waste_usd": round(annual_stall_waste_usd, 2),
        "storage_upgrade_capex_usd": round(storage_upgrade_capex_usd, 2),
        "payback_days": round(payback_days, 2),
        "storage_pct_of_annual_waste": round(storage_pct_of_annual_waste, 2),
    }


def compare_storage_options_gpu_hour_waste(
    num_gpus: int = 128,
    gpu_hour_value_usd: float = 435.0,
    option_a_stall_fraction: float = 0.05,
    option_a_capex_usd: float = 500_000.0,
    option_a_annual_maint_usd: float = 5_000.0,
    option_b_stall_fraction: float = 0.01,
    option_b_lustre_capex_usd: float = 80_000.0,
    option_b_lustre_maint_usd: float = 10_000.0,
    option_b_nvme_capex_usd: float = 500_000.0,
    option_b_nvme_maint_usd: float = 5_000.0,
) -> Dict[str, float]:
    """Compare Option A (minimal storage, 5% stall) vs Option B (balanced Lustre + NVMe, 1% stall) from V15 Ch. 10."""
    hours_per_year = 8760.0
    opt_a_hourly_waste = num_gpus * option_a_stall_fraction * gpu_hour_value_usd  # $2,784/hr
    opt_a_annual_waste_m = round((opt_a_hourly_waste * hours_per_year) / 1_000_000.0, 1)  # $24.4M
    opt_a_total_m = round(opt_a_annual_waste_m + (option_a_annual_maint_usd / 1_000_000.0), 1)

    opt_b_hourly_waste = round(num_gpus * option_b_stall_fraction * gpu_hour_value_usd, 2)  # $556.80/hr (~$558/hr in V15 Ch. 10)
    opt_b_reported_hourly_waste = 558.0
    opt_b_annual_waste_m = round((opt_b_reported_hourly_waste * hours_per_year) / 1_000_000.0, 1)  # $4.9M
    opt_b_storage_spend_m = (
        option_b_lustre_capex_usd
        + option_b_lustre_maint_usd
        + option_b_nvme_capex_usd
        + option_b_nvme_maint_usd
    ) / 1_000_000.0  # $0.595M (~$0.6M)
    opt_b_total_m = round(opt_b_annual_waste_m + opt_b_storage_spend_m, 1)  # $5.5M
    annual_savings_m = round(opt_a_total_m - opt_b_total_m, 1)  # $18.9M/year
    return {
        "option_a_hourly_waste_usd": round(opt_a_hourly_waste, 2),
        "option_a_annual_waste_musd": opt_a_annual_waste_m,
        "option_a_total_musd": opt_a_total_m,
        "option_b_exact_hourly_waste_usd": opt_b_hourly_waste,
        "option_b_hourly_waste_usd": opt_b_reported_hourly_waste,
        "option_b_annual_waste_musd": opt_b_annual_waste_m,
        "option_b_total_musd": opt_b_total_m,
        "net_annual_savings_musd": annual_savings_m,
    }


def evaluate_three_year_storage_and_factory_tco(
    usable_storage_tb: float = 1_000.0,
    storage_capex_usd: float = 2_000_000.0,
    storage_annual_maint_usd: float = 200_000.0,
    storage_power_kw: float = 40.0,
    pue: float = 1.35,
    kwh_cost_usd: float = 0.12,
    years: int = 3,
    factory_total_gpus: int = 1200,
    factory_total_capex_musd: float = 44.0,
    factory_total_opex_3yr_musd: float = 26.2,
) -> Dict[str, float]:
    """Calculate 3-year storage TCO, $/TB-month, and storage share of an AI Factory 3-year TCO (V21 Ch. 11-12)."""
    if usable_storage_tb <= 0 or years <= 0 or factory_total_gpus <= 0:
        raise ValueError("usable_storage_tb, years, and factory_total_gpus must be positive")
    annual_power_usd = storage_power_kw * pue * 8760.0 * kwh_cost_usd
    three_year_storage_opex_usd = years * (storage_annual_maint_usd + annual_power_usd)
    three_year_storage_tco_usd = storage_capex_usd + three_year_storage_opex_usd
    usd_per_tb_month = (three_year_storage_tco_usd / (years * 12.0)) / usable_storage_tb

    factory_3yr_tco_musd = round(factory_total_capex_musd + factory_total_opex_3yr_musd, 1)  # $70.2M
    factory_per_gpu_year_kusd = round((factory_3yr_tco_musd * 1000.0) / (factory_total_gpus * years), 1)  # $19.5K
    storage_capex_share_of_factory_capex_pct = ((storage_capex_usd / 1_000_000.0) / factory_total_capex_musd) * 100.0
    storage_capex_share_of_factory_tco_pct = ((storage_capex_usd / 1_000_000.0) / factory_3yr_tco_musd) * 100.0
    return {
        "usable_storage_tb": usable_storage_tb,
        "storage_capex_usd": round(storage_capex_usd, 2),
        "storage_annual_power_usd": round(annual_power_usd, 2),
        "three_year_storage_opex_usd": round(three_year_storage_opex_usd, 2),
        "three_year_storage_tco_usd": round(three_year_storage_tco_usd, 2),
        "effective_usd_per_tb_month": round(usd_per_tb_month, 2),
        "factory_3yr_tco_musd": factory_3yr_tco_musd,
        "factory_per_gpu_year_kusd": factory_per_gpu_year_kusd,
        "storage_capex_share_of_factory_capex_pct": round(storage_capex_share_of_factory_capex_pct, 2),
        "storage_capex_share_of_factory_tco_pct": round(storage_capex_share_of_factory_tco_pct, 2),
    }
