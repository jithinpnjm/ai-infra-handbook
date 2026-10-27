"""
Chapter 13.2 — Local NVMe and Data Staging
Deterministic models for DGX 2-tier NVMe topology, mdadm RAID 0 chunk and stripe
width alignment, multi-epoch dataset staging break-even math, asynchronous
checkpoint staging speedup, Linux blk-mq / read-ahead / XFS tuning validation,
SMART wear-leveling / DWPD endurance math, and Slurm prolog/epilog per-job
/raid/job_$SLURM_JOB_ID lifecycle management.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# 1. DGX 2-Tier NVMe Hardware Profiles (Cross-referenced with 9.2 and 9.5)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NVMeTierSpec:
    tier_name: str
    form_factor: str
    drive_count: int
    drive_size_tb: float
    raid_level: str
    mount_point: str
    raw_capacity_tb: float
    usable_capacity_tb: float
    sustained_seq_read_gbps: float
    sustained_seq_write_gbps: float
    ephemeral: bool


@dataclass(frozen=True)
class NodeNVMeProfile:
    platform_name: str
    gpu_count: int
    os_tier: NVMeTierSpec
    scratch_tier: NVMeTierSpec
    racks_or_trays: int = 1


def build_dgx_h100_nvme_profile() -> NodeNVMeProfile:
    """
    DGX H100 / H200 2-tier NVMe architecture (cross-referenced from 9.2):
      - OS Tier: 2x 1.92 TB M.2 NVMe in hardware RAID 1 (3.84 TB raw, 1.92 TB usable)
      - Scratch Tier: 8x 3.84 TB U.2 NVMe in software RAID 0 mounted at /raid
        (30.72 TB raw and usable, ~50 GB/s aggregate sequential read, ~28 GB/s write)
    """
    os_tier = NVMeTierSpec(
        tier_name="OS Boot Mirror",
        form_factor="M.2",
        drive_count=2,
        drive_size_tb=1.92,
        raid_level="RAID 1",
        mount_point="/",
        raw_capacity_tb=round(2 * 1.92, 2),
        usable_capacity_tb=1.92,
        sustained_seq_read_gbps=3.2,
        sustained_seq_write_gbps=2.6,
        ephemeral=False,
    )
    scratch_tier = NVMeTierSpec(
        tier_name="Ephemeral Scratch Array",
        form_factor="U.2",
        drive_count=8,
        drive_size_tb=3.84,
        raid_level="RAID 0",
        mount_point="/raid",
        raw_capacity_tb=round(8 * 3.84, 2),
        usable_capacity_tb=round(8 * 3.84, 2),
        sustained_seq_read_gbps=50.0,
        sustained_seq_write_gbps=28.0,
        ephemeral=True,
    )
    return NodeNVMeProfile(
        platform_name="DGX H100 / H200 (8-GPU Node)",
        gpu_count=8,
        os_tier=os_tier,
        scratch_tier=scratch_tier,
        racks_or_trays=1,
    )


def build_gb200_compute_tray_nvme_profile() -> NodeNVMeProfile:
    """
    DGX GB200 / GB300 NVL72 1U Compute Tray NVMe architecture (cross-referenced from 9.5):
      - OS Tier: 1x 1.92 TB M.2 NVMe (1.92 TB raw and usable)
      - Scratch Tier: 4x 3.84 TB E1.S (EDSFF) NVMe in RAID 0 mounted at /raid
        (15.36 TB per compute tray; 18 trays/rack = 276.48 TB per NVL72 rack)
    """
    os_tier = NVMeTierSpec(
        tier_name="OS Boot Drive",
        form_factor="M.2",
        drive_count=1,
        drive_size_tb=1.92,
        raid_level="Single",
        mount_point="/",
        raw_capacity_tb=1.92,
        usable_capacity_tb=1.92,
        sustained_seq_read_gbps=3.2,
        sustained_seq_write_gbps=2.6,
        ephemeral=False,
    )
    scratch_tier = NVMeTierSpec(
        tier_name="Ephemeral Scratch Array",
        form_factor="E1.S",
        drive_count=4,
        drive_size_tb=3.84,
        raid_level="RAID 0",
        mount_point="/raid",
        raw_capacity_tb=round(4 * 3.84, 2),
        usable_capacity_tb=round(4 * 3.84, 2),
        sustained_seq_read_gbps=25.0,
        sustained_seq_write_gbps=14.0,
        ephemeral=True,
    )
    return NodeNVMeProfile(
        platform_name="DGX GB200 / GB300 Compute Tray (18 Trays / NVL72 Rack)",
        gpu_count=4,
        os_tier=os_tier,
        scratch_tier=scratch_tier,
        racks_or_trays=18,
    )


# ---------------------------------------------------------------------------
# 2. mdadm RAID 0 Chunk Size and XFS Stripe Alignment Math
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Raid0Geometry:
    num_drives: int
    drive_size_tb: float
    chunk_size_kb: int
    filesystem_block_bytes: int
    full_stripe_kb: int
    full_stripe_mb: float
    xfs_sunit_blocks: int
    xfs_swidth_blocks: int
    ext4_stride_blocks: int
    ext4_stripe_width_blocks: int
    usable_capacity_tb: float
    aggregate_seq_read_gbps: float
    mkfs_xfs_cmd: str


def compute_raid0_geometry(
    num_drives: int = 8,
    drive_size_tb: float = 3.84,
    chunk_size_kb: int = 512,
    filesystem_block_bytes: int = 4096,
    per_drive_read_gbps: float = 6.25,
) -> Raid0Geometry:
    """
    Calculate mdadm RAID 0 full stripe width and XFS / ext4 alignment parameters:
      - Full stripe width (KB) = num_drives * chunk_size_kb
      - XFS sunit (in 4KiB FS blocks) = (chunk_size_kb * 1024) // filesystem_block_bytes
      - XFS swidth (in 4KiB FS blocks) = sunit * num_drives
      - ext4 stride = sunit, ext4 stripe-width = swidth
    For 8x 3.84 TB drives with 512 KB chunk and 4096B FS blocks:
      - Full stripe = 8 * 512 KB = 4096 KB (4.0 MB)
      - sunit = 128 blocks, swidth = 1024 blocks
    """
    if num_drives < 1:
        raise ValueError("num_drives must be >= 1")
    if (chunk_size_kb * 1024) % filesystem_block_bytes != 0:
        raise ValueError("chunk_size_kb must be an integer multiple of filesystem_block_bytes")

    full_stripe_kb = num_drives * chunk_size_kb
    full_stripe_mb = round(full_stripe_kb / 1024.0, 4)
    sunit_blocks = (chunk_size_kb * 1024) // filesystem_block_bytes
    swidth_blocks = sunit_blocks * num_drives
    usable_tb = round(num_drives * drive_size_tb, 2)
    agg_read_gbps = round(num_drives * per_drive_read_gbps, 2)
    mkfs_cmd = f"mkfs.xfs -f -d su={chunk_size_kb}k,sw={num_drives} /dev/md0"

    return Raid0Geometry(
        num_drives=num_drives,
        drive_size_tb=drive_size_tb,
        chunk_size_kb=chunk_size_kb,
        filesystem_block_bytes=filesystem_block_bytes,
        full_stripe_kb=full_stripe_kb,
        full_stripe_mb=full_stripe_mb,
        xfs_sunit_blocks=sunit_blocks,
        xfs_swidth_blocks=swidth_blocks,
        ext4_stride_blocks=sunit_blocks,
        ext4_stripe_width_blocks=swidth_blocks,
        usable_capacity_tb=usable_tb,
        aggregate_seq_read_gbps=agg_read_gbps,
        mkfs_xfs_cmd=mkfs_cmd,
    )


def evaluate_io_stripe_efficiency(
    io_request_kb: int,
    geometry: Raid0Geometry,
) -> Dict[str, float]:
    """
    Compute how many drives a single aligned I/O request of size `io_request_kb`
    activates in parallel and the fraction of full-stripe parallelism achieved.
    """
    active_drives = min(
        geometry.num_drives,
        max(1, (io_request_kb + geometry.chunk_size_kb - 1) // geometry.chunk_size_kb),
    )
    stripe_utilization = round(active_drives / geometry.num_drives, 4)
    is_full_stripe_multiple = (io_request_kb >= geometry.full_stripe_kb) and (
        io_request_kb % geometry.full_stripe_kb == 0
    )
    return {
        "io_request_kb": float(io_request_kb),
        "active_drives": float(active_drives),
        "stripe_utilization": stripe_utilization,
        "is_full_stripe_multiple": 1.0 if is_full_stripe_multiple else 0.0,
    }


# ---------------------------------------------------------------------------
# 3. Dataset Staging Break-Even Epoch Calculator & Async Checkpoint Staging
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StagingBreakEvenResult:
    dataset_gb: float
    nvme_capacity_gb: float
    fits_in_nvme: bool
    copy_stage_time_sec: float
    epoch_time_remote_sec: float
    epoch_time_local_sec: float
    per_epoch_savings_sec: float
    break_even_epochs_exact: float
    min_integer_epochs_to_pay_back: int
    total_time_no_staging_sec: float
    total_time_with_staging_sec: float
    net_wall_clock_saved_sec: float
    speedup_pct: float
    recommendation: str


def evaluate_staging_break_even(
    dataset_gb: float,
    nvme_capacity_gb: float,
    num_epochs: int,
    stage_copy_bw_gbps: float,
    epoch_time_remote_sec: float,
    epoch_time_local_sec: float,
    inline_epoch1_staging: bool = False,
) -> StagingBreakEvenResult:
    """
    Evaluate when staging a dataset from shared storage (Lustre / BeeGFS / S3)
    to local NVMe (/raid) pays back its staging overhead.

    Two operational modes:
    1. Pre-stage mode (`inline_epoch1_staging=False`):
       Job copies `dataset_gb` to `/raid` before epoch 1 at `stage_copy_bw_gbps`
       (`T_copy = dataset_gb / stage_copy_bw_gbps`), then runs all `num_epochs`
       at `epoch_time_local_sec`.
       Break-even epoch count: `N_be = T_copy / (T_remote - T_local)`.
    2. Inline Epoch-1 cache-fill mode (`inline_epoch1_staging=True`, V15 Ch 3):
       Epoch 1 reads from shared storage and writes to `/raid` (`epoch_time_remote_sec`),
       and Epochs 2..N run from warm `/raid` (`epoch_time_local_sec`).
    """
    fits = dataset_gb <= nvme_capacity_gb * 0.85  # keep <85% fill to avoid eviction/GC cliff
    per_epoch_savings = round(epoch_time_remote_sec - epoch_time_local_sec, 4)

    if not fits or per_epoch_savings <= 0:
        total_no_stage = round(num_epochs * epoch_time_remote_sec, 2)
        return StagingBreakEvenResult(
            dataset_gb=dataset_gb,
            nvme_capacity_gb=nvme_capacity_gb,
            fits_in_nvme=fits,
            copy_stage_time_sec=0.0,
            epoch_time_remote_sec=epoch_time_remote_sec,
            epoch_time_local_sec=epoch_time_local_sec,
            per_epoch_savings_sec=per_epoch_savings,
            break_even_epochs_exact=float("inf"),
            min_integer_epochs_to_pay_back=0,
            total_time_no_staging_sec=total_no_stage,
            total_time_with_staging_sec=total_no_stage,
            net_wall_clock_saved_sec=0.0,
            speedup_pct=0.0,
            recommendation="DO_NOT_STAGE_DATASET_EXCEEDS_SAFE_85PCT_NVME_OR_NO_EPOCH_GAIN",
        )

    if inline_epoch1_staging:
        copy_time = 0.0
        total_no_stage = round(num_epochs * epoch_time_remote_sec, 2)
        total_with_stage = round(
            epoch_time_remote_sec + max(0, num_epochs - 1) * epoch_time_local_sec, 2
        )
        be_exact = 1.0
        min_int_epochs = 2
    else:
        copy_time = round(dataset_gb / stage_copy_bw_gbps, 2)
        total_no_stage = round(num_epochs * epoch_time_remote_sec, 2)
        total_with_stage = round(copy_time + num_epochs * epoch_time_local_sec, 2)
        be_exact = round(copy_time / per_epoch_savings, 4)
        min_int_epochs = int(be_exact) + 1

    net_saved = round(total_no_stage - total_with_stage, 2)
    speedup_pct = round((net_saved / total_no_stage) * 100.0, 2) if total_no_stage > 0 else 0.0
    rec = (
        "STAGE_TO_LOCAL_NVME"
        if net_saved > 0
        else "DO_NOT_STAGE_TOO_FEW_EPOCHS"
    )

    return StagingBreakEvenResult(
        dataset_gb=dataset_gb,
        nvme_capacity_gb=nvme_capacity_gb,
        fits_in_nvme=fits,
        copy_stage_time_sec=copy_time,
        epoch_time_remote_sec=epoch_time_remote_sec,
        epoch_time_local_sec=epoch_time_local_sec,
        per_epoch_savings_sec=per_epoch_savings,
        break_even_epochs_exact=be_exact,
        min_integer_epochs_to_pay_back=min_int_epochs,
        total_time_no_staging_sec=total_no_stage,
        total_time_with_staging_sec=total_with_stage,
        net_wall_clock_saved_sec=net_saved,
        speedup_pct=speedup_pct,
        recommendation=rec,
    )


@dataclass(frozen=True)
class CheckpointStagingResult:
    checkpoint_gb: float
    sync_shared_write_sec: float
    local_nvme_write_sec: float
    async_visible_stall_sec: float
    background_flush_sec: float
    min_checkpoint_interval_sec: float
    critical_path_speedup_x: float


def evaluate_checkpoint_staging(
    checkpoint_gb: float = 500.0,
    shared_write_bw_gbps: float = 1.2,
    local_nvme_write_bw_gbps: float = 3.5,
    async_ack_sec: float = 1.0,
) -> CheckpointStagingResult:
    """
    Model checkpoint staging from V15 Ch 3:
      - Synchronous write to shared Lustre: 500 GB / 1.2 GB/s = 416.67 s (~417 s)
      - Local NVMe write time: 500 GB / 3.5 GB/s = 142.86 s (~143 s)
      - With async thread/process handoff to local NVMe + background flush to Lustre,
        training pause is ~1.0 s (417x critical-path speedup), provided checkpoint
        interval exceeds `local_nvme_write_sec + background_flush_sec` (or double-buffered
        `background_flush_sec`).
    """
    sync_sec = round(checkpoint_gb / shared_write_bw_gbps, 2)
    nvme_sec = round(checkpoint_gb / local_nvme_write_bw_gbps, 2)
    speedup_x = round(sync_sec / async_ack_sec, 2)
    return CheckpointStagingResult(
        checkpoint_gb=checkpoint_gb,
        sync_shared_write_sec=sync_sec,
        local_nvme_write_sec=nvme_sec,
        async_visible_stall_sec=async_ack_sec,
        background_flush_sec=sync_sec,
        min_checkpoint_interval_sec=sync_sec,
        critical_path_speedup_x=speedup_x,
    )


# ---------------------------------------------------------------------------
# 4. Linux NVMe Block Queue, Read-Ahead, and Filesystem Tuning Audit
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NVMeTuningAudit:
    device: str
    scheduler: str
    nr_requests: int
    read_ahead_kb: int
    mount_options: List[str]
    numa_node_nvme: int
    numa_node_workers: int
    status: str
    issues: List[str]
    remediations: List[str]


def audit_nvme_tuning(
    device: str = "nvme0n1",
    scheduler: str = "none",
    nr_requests: int = 1023,
    read_ahead_kb: int = 4096,
    mount_options: Optional[List[str]] = None,
    numa_node_nvme: int = 0,
    numa_node_workers: int = 0,
    workload_pattern: str = "large_sequential",
) -> NVMeTuningAudit:
    """
    Audit Linux NVMe block device and XFS/ext4 filesystem tuning per
    *AI Systems Performance Engineering* Ch 5 and V15 Ch 3:
      1. Scheduler: `none` (or `mq-deadline`) for NVMe blk-mq; `bfq`/`cfq` adds CPU lock overhead.
      2. Queue depth (`nr_requests`): >= 512 (typically 1023) to sustain deep NVMe queues.
      3. Read-ahead (`read_ahead_kb`): for `large_sequential` shard streaming, 2048..8192 KB
         (default 128 KB under-pipelines sequential reads; for `pure_random_o_direct`, 128 KB or lower).
      4. Mount options: must include `noatime` to avoid metadata write-back on every read.
      5. NUMA locality: DataLoader CPU workers must run on the same NUMA socket (`numa_node_nvme`)
         as the NVMe root complex.
    """
    opts = mount_options if mount_options is not None else ["rw", "noatime", "attr2", "inode64"]
    issues: List[str] = []
    remediations: List[str] = []

    if scheduler not in ("none", "mq-deadline"):
        issues.append(f"Suboptimal blk-mq scheduler '{scheduler}' on {device}")
        remediations.append(f"echo none > /sys/block/{device}/queue/scheduler")

    if nr_requests < 512:
        issues.append(f"Shallow queue depth nr_requests={nr_requests} (< 512)")
        remediations.append(f"echo 1023 > /sys/block/{device}/queue/nr_requests")

    if workload_pattern == "large_sequential" and read_ahead_kb < 2048:
        issues.append(
            f"read_ahead_kb={read_ahead_kb} KB is too small for large sequential shard streaming"
        )
        remediations.append(
            f"blockdev --setra 8192 /dev/{device}  # sets read_ahead_kb=4096 KB"
        )

    if "noatime" not in opts:
        issues.append("Filesystem mounted without 'noatime' (every read updates inode access time)")
        remediations.append("mount -o remount,noatime /raid")

    if numa_node_nvme != numa_node_workers:
        issues.append(
            f"Cross-socket NUMA mismatch: {device} on NUMA {numa_node_nvme} vs workers on NUMA {numa_node_workers}"
        )
        remediations.append(
            f"numactl --cpunodebind={numa_node_nvme} --membind={numa_node_nvme} python3 train.py"
        )

    status = "HEALTHY" if not issues else "DEGRADED"
    return NVMeTuningAudit(
        device=device,
        scheduler=scheduler,
        nr_requests=nr_requests,
        read_ahead_kb=read_ahead_kb,
        mount_options=list(opts),
        numa_node_nvme=numa_node_nvme,
        numa_node_workers=numa_node_workers,
        status=status,
        issues=issues,
        remediations=remediations,
    )


# ---------------------------------------------------------------------------
# 5. SMART Telemetry, Wear-Leveling, and DWPD Endurance Math
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NVMeEnduranceReport:
    drive_size_tb: float
    rated_dwpd: float
    warranty_years: int
    total_tbw_rating_tb: float
    daily_write_tb: float
    write_amplification_factor: float
    effective_nand_daily_tb: float
    effective_dwpd_used: float
    estimated_lifespan_years: float
    percentage_used: int
    available_spare_pct: int
    available_spare_threshold_pct: int
    composite_temp_c: int
    media_errors: int
    health_status: str
    recommended_action: str


def evaluate_nvme_endurance_and_smart(
    drive_size_tb: float = 3.84,
    rated_dwpd: float = 1.0,
    warranty_years: int = 5,
    daily_host_writes_tb: float = 2.5,
    write_amplification_factor: float = 1.2,
    percentage_used: int = 18,
    available_spare_pct: int = 100,
    available_spare_threshold_pct: int = 10,
    composite_temp_c: int = 46,
    media_errors: int = 0,
) -> NVMeEnduranceReport:
    """
    Calculate NVMe Total Terabytes Written (TBW) endurance rating, effective DWPD
    under Write Amplification Factor (WAF), and SMART health status (`nvme smart-log`):
      - TBW (TB) = drive_size_tb * rated_dwpd * 365 * warranty_years
      - Effective daily NAND writes (TB) = daily_host_writes_tb * WAF
      - Effective DWPD = effective_nand_daily_tb / drive_size_tb
      - Estimated lifespan (years) = total_tbw_rating_tb / (effective_nand_daily_tb * 365)
      - Thermal throttling threshold: >= 70 C composite temperature on enterprise U.2/E1.S NVMe
    """
    total_tbw = round(drive_size_tb * rated_dwpd * 365 * warranty_years, 2)
    eff_daily_tb = round(daily_host_writes_tb * write_amplification_factor, 4)
    eff_dwpd = round(eff_daily_tb / drive_size_tb, 4)
    est_years = round(total_tbw / (eff_daily_tb * 365.0), 2) if eff_daily_tb > 0 else float("inf")

    if media_errors > 0 or available_spare_pct <= available_spare_threshold_pct:
        status = "CRITICAL_REPLACE_DRIVE"
        action = "Drain node, fail/replace NVMe drive, and rebuild /raid array before scheduling jobs"
    elif composite_temp_c >= 70:
        status = "WARNING_THERMAL_THROTTLING"
        action = "Check front fan bay RPM, airflow obstruction, and smartctl thermal throttle counters"
    elif percentage_used >= 90 or est_years < 1.0:
        status = "WARNING_WEAR_OUT_NEAR"
        action = "Schedule proactive SSD replacement and reduce checkpoint staging frequency"
    else:
        status = "HEALTHY"
        action = "Continue normal operation and monitor nvme smart-log metrics"

    return NVMeEnduranceReport(
        drive_size_tb=drive_size_tb,
        rated_dwpd=rated_dwpd,
        warranty_years=warranty_years,
        total_tbw_rating_tb=total_tbw,
        daily_write_tb=daily_host_writes_tb,
        write_amplification_factor=write_amplification_factor,
        effective_nand_daily_tb=eff_daily_tb,
        effective_dwpd_used=eff_dwpd,
        estimated_lifespan_years=est_years,
        percentage_used=percentage_used,
        available_spare_pct=available_spare_pct,
        available_spare_threshold_pct=available_spare_threshold_pct,
        composite_temp_c=composite_temp_c,
        media_errors=media_errors,
        health_status=status,
        recommended_action=action,
    )


# ---------------------------------------------------------------------------
# 6. Slurm Prolog / Epilog Per-Job Scratch Lifecycle Simulator
# ---------------------------------------------------------------------------


@dataclass
class SlurmScratchNodeState:
    total_capacity_gb: float
    reserved_headroom_pct: float
    active_job_dirs: Dict[str, float]  # path -> allocated_gb
    orphan_dirs: Dict[str, float]      # path -> leaked_gb

    @property
    def used_gb(self) -> float:
        return round(
            sum(self.active_job_dirs.values()) + sum(self.orphan_dirs.values()), 2
        )

    @property
    def fill_pct(self) -> float:
        return round((self.used_gb / self.total_capacity_gb) * 100.0, 2)

    @property
    def max_safe_usable_gb(self) -> float:
        return round(self.total_capacity_gb * (1.0 - self.reserved_headroom_pct / 100.0), 2)


def run_slurm_prolog(
    state: SlurmScratchNodeState,
    job_id: int,
    requested_gb: float,
    purge_orphans: bool = True,
) -> Dict[str, object]:
    """
    Simulate Slurm `Prolog` execution on a compute node:
      1. Optionally purge any orphaned `/raid/job_*` directories left by crashed jobs.
      2. Verify that `used_gb + requested_gb <= max_safe_usable_gb` (keeping >=15% headroom
         so NVMe fill level stays <= 85%).
      3. Create `/raid/job_<job_id>` and export `LOCAL_SCRATCH=/raid/job_<job_id>`.
    """
    reclaimed_gb = 0.0
    if purge_orphans and state.orphan_dirs:
        reclaimed_gb = round(sum(state.orphan_dirs.values()), 2)
        state.orphan_dirs.clear()

    job_path = f"/raid/job_{job_id}"
    projected_gb = round(state.used_gb + requested_gb, 2)
    if projected_gb > state.max_safe_usable_gb:
        return {
            "admitted": False,
            "job_path": job_path,
            "reclaimed_orphan_gb": reclaimed_gb,
            "projected_fill_pct": round((projected_gb / state.total_capacity_gb) * 100.0, 2),
            "reason": "INSUFFICIENT_SAFE_NVME_SCRATCH_CAPACITY",
        }

    state.active_job_dirs[job_path] = requested_gb
    return {
        "admitted": True,
        "job_path": job_path,
        "env_var": f"LOCAL_SCRATCH={job_path}",
        "reclaimed_orphan_gb": reclaimed_gb,
        "used_gb": state.used_gb,
        "fill_pct": state.fill_pct,
    }


def run_slurm_epilog(
    state: SlurmScratchNodeState,
    job_id: int,
    epilog_enabled: bool = True,
) -> Dict[str, object]:
    """
    Simulate Slurm `Epilog` execution when a job completes, times out, or is SIGKILLed:
      - If `epilog_enabled=True`, removes `/raid/job_<job_id>` and reclaims space.
      - If `epilog_enabled=False` (common mistake when relying on user script cleanup),
        moves the directory into `orphan_dirs`, leaking NVMe capacity.
    """
    job_path = f"/raid/job_{job_id}"
    allocated_gb = state.active_job_dirs.pop(job_path, 0.0)
    if epilog_enabled:
        return {
            "cleaned": True,
            "job_path": job_path,
            "freed_gb": allocated_gb,
            "remaining_used_gb": state.used_gb,
            "fill_pct": state.fill_pct,
        }

    if allocated_gb > 0:
        state.orphan_dirs[job_path] = allocated_gb
    return {
        "cleaned": False,
        "job_path": job_path,
        "leaked_gb": allocated_gb,
        "remaining_used_gb": state.used_gb,
        "fill_pct": state.fill_pct,
    }
