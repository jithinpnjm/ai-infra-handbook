#!/usr/bin/env python3
"""
Chapter 13.9 — Storage Troubleshooting (Deterministic Reference Implementation)
===============================================================================
Standard-library-only analytical models and diagnostic triage engines for
production AI storage troubleshooting:

1. Eight-Layer AI Storage Triage Decision Tree:
   - GPU SM utilization (`nvidia-smi dmon -s puctem`, `< 70.0%` I/O-bound vs
     `>= 70.0%` compute/communication-bound)
   - DataLoader prefetch queue depth (`prefetch_queue.qsize()`, `0` empty vs
     non-empty) and batch wait time (`> 500 ms` critical stall)
   - Host CPU preprocessing (`perf record`, `cProfile`, `Image.open` `45.2 s`
     + `augmentation.apply` `12.1 s` = `57.3 s` / `57 s` per `120,000` calls)
   - Filesystem metadata storm (`lctl get_param llite.*.stats`, `950,000`
     opens in `60 s` = `15,833.33` / `15.8K` opens/sec, `45.0 ms` avg latency
     vs `2.0 ms` baseline, `50,000` ops/sec healthy ceiling per MDS, `> 100,000`
     saturated, `47` minutes idle GPU time per epoch before repackaging)
   - Storage network drops and ring buffer exhaustion (`ethtool -S eth0`,
     `rx_errors = 1240`, `rx_dropped = 856` in `10 s` at ring size `256` ->
     `< 5/sec` after `ethtool -G eth0 rx 4096 tx 4096`, `300/sec` retransmits
     from switch oversubscription with `5 x 128` GPUs = `640` GPUs -> `0`
     retransmits, `2.0 ms` metadata latency, `88.0%` GPU util with `3 x 128`
     = `384` GPUs; `25,000 Mb/s` = `25 Gbps` link, `20–25 Gbps` / `80–100%`
     healthy `iperf3`, `MTU 9000` jumbo frames)
   - Storage target fill imbalance (`lfs df -h`, `OST 0..4` at `30.0%` vs
     `OST 5..7` at `98.0%` compared to `50.0%` healthy baseline; single slow
     client `500 MB/s` vs `1,500 MB/s` peers)
   - Local NVMe staging cache exhaustion (`df /local-nvme`, `> 85.0%` fill
     triggering LRU eviction)
   - PCIe / CPU bounce-buffer bottleneck (`__memcpy_avx2 > 20.0%` CPU samples)

2. Communication-Bound vs Compute-Bound Batch-Size Scaling Test
   (AI Systems Performance Engineering, Chapter 5):
   - Baseline gradient all-reduce achieving `60.0 GB/s` on a `100.0 GB/s` NIC
   - Halving (`0.5x`) and doubling (`2.0x`) batch size while gradient payload
     stays fixed (scales with model parameters, not batch size)
   - Communication-bound signature: NIC stays pinned at `60.0 GB/s` at `0.5x`,
     `1.0x`, and `2.0x` batch size
   - Compute-bound signature: NIC drops from `60.0 GB/s` to `40.0 GB/s` when
     batch size is halved (`0.5x`), and communication time fraction shrinks
     when batch size is doubled (`2.0x`)

3. GPUDirect Storage (GDS) Silent Compatibility-Mode Fallback & Benchmark Triage:
   - 6-point GDS validation checklist (`nvidia_fs` module, `/proc/driver/nvidia-fs/stats`,
     `nvidia-smi topo -m` PCIe affinity `PIX`/`PXB` vs `PHB`/`SYS`, storage
     compatibility, driver `>= 470` / `535.29`, `cuFile` API with `4 KiB` NVMe /
     `8 KiB` Lustre alignment and `>= 1 MiB` request size)
   - Lab 03 `100 MiB` (`104,857,600` B) Python `kvikio.CuFile` vs CPU bounce
     benchmark (`[0.265, 0.250, 0.248, 0.247, 0.246] s` -> `0.2512 s` / `0.251 s`
     mean, `398 MB/s` CPU bounce; `> 20.0%` improvement rule to deploy GDS)
   - `gdsio` (`-d 0 -w 4 -s 10G -i 1M -I 0`) `-x 2` CPU path (`8.0 GB/s`,
     `1.25 ms` latency, `85.0%` CPU) vs `-x 0` GDS path (`9.6 GB/s`, `+20.0%`
     uplift, `1.00 ms` latency, `-20.0%` reduction, `25.0%` CPU)
   - Silent compatibility-mode fallback detection (`allow_compat_mode: true`
     in `/etc/cufile.json`, unaligned offsets, `FUSE` mounts, `SYS`/`PHB`
     cross-socket routing, `__memcpy_avx2 > 20.0%` in `perf record`, zero
     increment in `/proc/driver/nvidia-fs/stats`)

4. Lustre Client Eviction, OST Imbalance, and Synchronous Checkpoint Stall Triage:
   - `500 GB` synchronous checkpoint stall at `1.0 GB/s` (`500.0 s`) vs local
     NVMe staging (`3.5 GB/s` read, `2.8 GB/s` `64 KB` batch stream, `1.2 GB/s`
     `4 MB` random read, `2.1 GB/s` checkpoint write -> `238.10 s`, or `10x`
     faster staging saving `90.0%` = `450.0 s` of critical-path stall)
   - Lustre `OST` fill skew (`OST 0..4` at `30.0%`, `OST 5..7` at `98.0%`,
     `68.0%` spread vs `50.0%` healthy baseline; `stripe_count = 32` penalty
     on small files vs `1..4` default and `16` for checkpoints)
   - Lustre client eviction (`LNet` timeout / `ptlrpc` expired lock / `ENOSPC`
     on `OST` `98%` full)

5. Local NVMe Thermal Throttling, SMART Wear, and RAID-0 Member Failure Triage:
   - Linux block/process I/O observability (`iostat -xz 1`, `iotop`, `pidstat -d`,
     `nvme smart-log`, `smartctl -a /dev/nvme*n1`)
   - Thermal composite temperature thresholds (`>= 70 C` warning throttle,
     `>= 80 C` critical throttle dropping read bandwidth from `3.5 GB/s` to
     `< 0.8 GB/s`), media errors (`media_errors > 0`), `percentage_used >= 95%`,
     and `mdadm` RAID-0 degraded/failed array diagnosis

6. NFS Stale File Handle (`ESTALE`) and Soft-Mount Silent Corruption Triage:
   - `NFS` client tuning (`rsize=1048576,wsize=1048576,noatime,async,actimeo=60,lookupcache=pos`)
   - Why `soft,timeo=...` mounts cause silent `EIO` / truncated checkpoint writes
     under fabric congestion vs `hard,intr`/`hard` mounts
   - Why server-side directory recreation or export fsid changes trigger
     `Stale file handle` (`ESTALE`, errno `116`) on compute nodes
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. Eight-Layer AI Storage Triage Decision Tree & Real Incident Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IncidentTelemetry:
    """Node- and cluster-level telemetry captured during a slow training job."""
    job_hours_baseline: float
    job_hours_current: float
    gpu_util_baseline_pct: float
    gpu_util_current_pct: float
    memory_util_baseline_pct: float
    memory_util_current_pct: float
    queue_empty_pct: float
    batch_wait_ms: float
    cpu_decode_sec_per_120k: float
    cpu_augment_sec_per_120k: float
    cpu_memcpy_pct: float
    lustre_opens_per_min: int
    lustre_open_latency_ms: float
    lustre_open_latency_baseline_ms: float
    nic_speed_gbps: float
    iperf_client_gbps: float
    rx_errors_10s: int
    rx_dropped_10s: int
    rx_ring_size: int
    retransmits_per_sec_after_ring_fix: int
    concurrent_jobs: int
    gpus_per_job: int
    ost_fills_pct: Tuple[float, ...]
    local_nvme_fill_pct: float


@dataclass(frozen=True)
class DecisionTreeResult:
    """Structured output of the 8-layer storage troubleshooting decision tree."""
    slowdown_factor: float
    is_io_bound: bool
    primary_layer: str
    secondary_layers: Tuple[str, ...]
    opens_per_sec: float
    mds_saturated: bool
    ost_imbalanced: bool
    ost_max_spread_pct: float
    total_active_gpus: int
    recommended_actions: Tuple[str, ...]


def walk_storage_decision_tree(telemetry: IncidentTelemetry) -> DecisionTreeResult:
    """
    Walk the Volume 15 Chapter 11 8-layer troubleshooting decision tree:
      1. GPU utilization (< 70% => I/O-bound; >= 70% => Compute/Comm-bound)
      2. Prefetch queue depth (`prefetch.queue.qsize()`)
      3. DataLoader CPU profile (`Image.open`, `augmentation.apply`, `__memcpy_avx2`)
      4. Filesystem metadata (`lctl get_param llite.*.stats`, > 50K ops/s ceiling)
      5. Network fabric (`ethtool -S`, `ethtool -g`, switch oversubscription)
      6. Storage target fill & health (`lfs df -h`, `smartctl`)
      7. Local NVMe cache fill (`df /local-nvme`, > 85% LRU eviction)
      8. PCIe / Host memory bounce path (`__memcpy_avx2` > 20%)
    """
    slowdown_factor = round(
        telemetry.job_hours_current / telemetry.job_hours_baseline, 2
    )
    is_io_bound = telemetry.gpu_util_current_pct < 70.0
    opens_per_sec = round(telemetry.lustre_opens_per_min / 60.0, 2)
    mds_capacity_pct = round((opens_per_sec / 50_000.0) * 100.0, 1)  # 31.7% at 15,833.33 opens/s
    cpu_decode_per_img_ms = round(
        ((telemetry.cpu_decode_sec_per_120k + telemetry.cpu_augment_sec_per_120k) / 120_000.0)
        * 1000.0,
        2,
    )  # 0.48 ms per image across 120,000 calls
    rx_drop_rate_per_sec = round(telemetry.rx_dropped_10s / 10.0, 1)  # 85.6 drops/sec
    _ = (mds_capacity_pct, cpu_decode_per_img_ms, rx_drop_rate_per_sec)
    mds_saturated = opens_per_sec > 50_000.0

    min_ost = min(telemetry.ost_fills_pct) if telemetry.ost_fills_pct else 0.0
    max_ost = max(telemetry.ost_fills_pct) if telemetry.ost_fills_pct else 0.0
    ost_max_spread = round(max_ost - min_ost, 2)
    ost_imbalanced = ost_max_spread > 10.0 or max_ost >= 90.0

    total_active_gpus = telemetry.concurrent_jobs * telemetry.gpus_per_job
    client_bw_ratio = (
        telemetry.iperf_client_gbps / telemetry.nic_speed_gbps
        if telemetry.nic_speed_gbps > 0
        else 0.0
    )

    secondary: List[str] = []
    actions: List[str] = []

    if not is_io_bound:
        primary_layer = "Compute / Collective Communication (Not Storage)"
        actions.append(
            "Profile model kernels and NCCL collectives with Nsight Systems (nsys)"
        )
    elif telemetry.queue_empty_pct < 20.0:
        if telemetry.cpu_memcpy_pct > 20.0:
            primary_layer = "PCIe / CPU-to-GPU Bounce Copy Overhead"
            actions.append(
                "Verify GPUDirect Storage (GDS) topology and /proc/driver/nvidia-fs/stats or enable pin_memory=True"
            )
        else:
            primary_layer = "DataLoader CPU Preprocessing"
            actions.append(
                "Offload decode/augmentation to NVIDIA DALI / nvJPEG or preprocess offline with NeMo Curator"
            )
    else:
        # Queue is empty most of the time (GPU starving for batches)
        if client_bw_ratio >= 0.50 and (
            mds_saturated or telemetry.lustre_open_latency_ms >= 20.0
        ):
            primary_layer = "Filesystem Metadata Server (MDS)"
            actions.append(
                "Repackage small files into WebDataset (.tar), TFRecord, or .bin/.idx shards to cut opens 100x"
            )
        elif telemetry.rx_errors_10s > 0 or telemetry.rx_dropped_10s > 0:
            primary_layer = "Network Fabric & NIC Ring Buffer"
            if telemetry.rx_ring_size < 4096:
                actions.append(
                    "Increase NIC ring buffer: ethtool -G eth0 rx 4096 tx 4096"
                )
            if telemetry.retransmits_per_sec_after_ring_fix > 0:
                secondary.append("Switch Fabric Oversubscription")
                actions.append(
                    "Reduce concurrent jobs (e.g., 5 -> 3 jobs) or rebalance switch uplinks to eliminate RTO stalls"
                )
        elif ost_imbalanced:
            primary_layer = "Storage Target (OST) Imbalance"
            actions.append(
                "Migrate data off 95%+ full OSTs with lfs_migrate and set directory stripe_count appropriately"
            )
        elif telemetry.local_nvme_fill_pct >= 85.0:
            primary_layer = "Local NVMe Cache Eviction"
            actions.append(
                "Enlarge local NVMe cache or tune LRU eviction watermark below 85% fill"
            )
        else:
            primary_layer = "PCIe / Memory Bandwidth Bottleneck"
            actions.append(
                "Bind dataloader workers to GPU-affine NUMA node with numactl and verify PCIe link width"
            )

        if ost_imbalanced and primary_layer != "Storage Target (OST) Imbalance":
            secondary.append("Storage Target (OST) Imbalance")
        if (
            telemetry.lustre_open_latency_ms >= 20.0
            and primary_layer != "Filesystem Metadata Server (MDS)"
        ):
            secondary.append("Elevated Metadata Open Latency (RTO-induced)")

    return DecisionTreeResult(
        slowdown_factor=slowdown_factor,
        is_io_bound=is_io_bound,
        primary_layer=primary_layer,
        secondary_layers=tuple(secondary),
        opens_per_sec=opens_per_sec,
        mds_saturated=mds_saturated,
        ost_imbalanced=ost_imbalanced,
        ost_max_spread_pct=ost_max_spread,
        total_active_gpus=total_active_gpus,
        recommended_actions=tuple(actions),
    )


def default_production_incident() -> IncidentTelemetry:
    """
    Return the exact production incident telemetry from Volume 15 Chapter 11:
    - Job duration jumped from 2.0 hours to 8.0 hours (4.0x slowdown)
    - GPU SM utilization dropped from 92% (mem 40%) to 15% (mem 5%)
    - Prefetch queue empty 80% of the time
    - cProfile over 120,000 calls: Image.open = 45.2 s, augmentation.apply = 12.1 s
      (57.3 s / ~57 s total)
    - lctl stats: 950,000 opens in 1 minute (15,833.33 / ~15.8K opens/sec,
      45 ms avg latency vs 2 ms healthy baseline; under 50K MDS capacity)
    - ethtool -S eth0: rx_errors=1240, rx_dropped=856 in 10s with RX ring 256
      (increasing ring to 4096 cuts drops to < 5/sec, but 300/sec retransmits
      persist until concurrent 128-GPU jobs drop from 5 [640 GPUs] to 3 [384 GPUs],
      restoring 0 retransmits, 2 ms metadata latency, and 88% GPU utilization)
    - lfs df -h: OST 0..4 at 30% full, OST 5..7 at 98% full (baseline 50% full)
    """
    return IncidentTelemetry(
        job_hours_baseline=2.0,
        job_hours_current=8.0,
        gpu_util_baseline_pct=92.0,
        gpu_util_current_pct=15.0,
        memory_util_baseline_pct=40.0,
        memory_util_current_pct=5.0,
        queue_empty_pct=80.0,
        batch_wait_ms=620.0,
        cpu_decode_sec_per_120k=45.2,
        cpu_augment_sec_per_120k=12.1,
        cpu_memcpy_pct=8.0,
        lustre_opens_per_min=950_000,
        lustre_open_latency_ms=45.0,
        lustre_open_latency_baseline_ms=2.0,
        nic_speed_gbps=25.0,
        iperf_client_gbps=8.5,
        rx_errors_10s=1240,
        rx_dropped_10s=856,
        rx_ring_size=256,
        retransmits_per_sec_after_ring_fix=300,
        concurrent_jobs=5,
        gpus_per_job=128,
        ost_fills_pct=(30.0, 30.0, 30.0, 30.0, 30.0, 98.0, 98.0, 98.0),
        local_nvme_fill_pct=62.0,
    )


# ---------------------------------------------------------------------------
# 2. Communication-Bound vs Compute-Bound Batch-Size Scaling Diagnostic
#    (AI Systems Performance Engineering, Chapter 5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BatchScalingDiagnosis:
    """Result of the batch-size halving/doubling diagnostic test."""
    nic_peak_gbps: float
    nic_bw_baseline_gbps: float
    nic_bw_half_batch_gbps: float
    nic_bw_double_batch_gbps: float
    comm_fraction_baseline_pct: float
    comm_fraction_double_batch_pct: float
    regime: str
    explanation: str


def diagnose_comm_vs_compute_scaling(
    nic_peak_gbps: float,
    nic_bw_baseline_gbps: float,
    nic_bw_half_batch_gbps: float,
    nic_bw_double_batch_gbps: float,
    compute_ms_baseline: float,
    comm_ms_baseline: float,
) -> BatchScalingDiagnosis:
    """
    Implement the Chapter 5 diagnostic experiment separating communication-bound
    from compute-bound multi-GPU training:
    - Because gradient all-reduce volume depends only on model parameter count
      (not batch size), halving (0.5x) or doubling (2.0x) batch size changes
      compute work while keeping communication bytes constant.
    - If NIC bandwidth stays flat at `60.0 GB/s` across `0.5x`, `1.0x`, and
      `2.0x` batch size, the workload is `COMMUNICATION_BOUND`.
    - If NIC bandwidth drops from `60.0 GB/s` to `40.0 GB/s` when batch size is
      halved (`0.5x`) and the communication percentage of iteration time shrinks
      when batch size is doubled (`2.0x`), the workload is `COMPUTE_BOUND`.
    """
    total_base = compute_ms_baseline + comm_ms_baseline
    comm_frac_base = round((comm_ms_baseline / total_base) * 100.0, 2)

    if abs(nic_bw_half_batch_gbps - nic_bw_baseline_gbps) <= 2.0 and abs(
        nic_bw_double_batch_gbps - nic_bw_baseline_gbps
    ) <= 2.0:
        # Communication remains the bottleneck even as compute scales
        total_double = (compute_ms_baseline * 1.2) + comm_ms_baseline
        comm_frac_double = round((comm_ms_baseline / total_double) * 100.0, 2)
        regime = "COMMUNICATION_BOUND"
        explanation = (
            f"NIC throughput remains pinned at {nic_bw_baseline_gbps:.1f} GB/s "
            f"(on a {nic_peak_gbps:.1f} GB/s link) when batch size is halved or "
            f"doubled; network fabric/collectives limit iteration speed."
        )
    else:
        # Compute scales linearly with batch size while comm bytes stay constant
        total_double = (compute_ms_baseline * 2.0) + comm_ms_baseline
        comm_frac_double = round((comm_ms_baseline / total_double) * 100.0, 2)
        regime = "COMPUTE_BOUND"
        explanation = (
            f"NIC throughput drops from {nic_bw_baseline_gbps:.1f} GB/s to "
            f"{nic_bw_half_batch_gbps:.1f} GB/s when batch size is halved, and "
            f"all-reduce share shrinks from {comm_frac_base:.1f}% to "
            f"{comm_frac_double:.1f}% when batch size is doubled; GPU SMs are "
            f"the limiting factor."
        )

    return BatchScalingDiagnosis(
        nic_peak_gbps=nic_peak_gbps,
        nic_bw_baseline_gbps=nic_bw_baseline_gbps,
        nic_bw_half_batch_gbps=nic_bw_half_batch_gbps,
        nic_bw_double_batch_gbps=nic_bw_double_batch_gbps,
        comm_fraction_baseline_pct=comm_frac_base,
        comm_fraction_double_batch_pct=comm_frac_double,
        regime=regime,
        explanation=explanation,
    )


# ---------------------------------------------------------------------------
# 3. GPUDirect Storage (GDS) Validation & Silent Fallback Triage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GDSValidationState:
    """System state and counters for auditing a GPUDirect Storage deployment."""
    nvidia_fs_loaded: bool
    stats_file_present: bool
    pcie_topo_relation: str  # e.g., "PIX", "PXB", "PHB", "NODE", "SYS"
    storage_type: str        # e.g., "NVMe", "NVMe-oF", "Lustre", "FUSE", "NFS-TCP"
    driver_version: float    # e.g., 535.29 (requires >= 470.0)
    uses_cufile_api: bool
    io_offset_bytes: int
    io_request_bytes: int
    allow_compat_mode: bool
    nvidia_fs_io_deltas: int
    perf_memcpy_avx2_pct: float


@dataclass(frozen=True)
class GDSAuditReport:
    """Result of auditing GDS configuration, alignment, and runtime counters."""
    prerequisites_passed: bool
    required_alignment_bytes: int
    is_aligned: bool
    request_size_ok: bool
    active_path: str  # "GDS_DIRECT_DMA" or "POSIX_COMPAT_CPU_BOUNCE"
    fallback_reasons: Tuple[str, ...]


def audit_gds_deployment(state: GDSValidationState) -> GDSAuditReport:
    """
    Validate all 6 GDS requirements from Volume 15 Lab 03 and Chapter 12:
      1. `nvidia_fs` kernel module loaded
      2. `/proc/driver/nvidia-fs/stats` present and incrementing during reads
      3. PCIe topology supports direct P2P/root-complex DMA (`PIX`, `PXB`, or
         verified `PHB`; `NODE`/`SYS` cross-NUMA degrades or falls back)
      4. Storage backend supports GDS (`NVMe`, `NVMe-oF`, `Lustre`, `BeeGFS`,
         `WekaFS`, `VAST`; user-space `FUSE` cannot use kernel GDS)
      5. NVIDIA driver >= 470 (e.g., `535.29`)
      6. Application uses `cuFile` / `kvikio.CuFile` with `4096 B` (`4 KB`)
         alignment for NVMe/NVMe-oF or `8192 B` (`8 KB`) alignment for Lustre,
         and request size `>= 1 MiB` (`1,048,576 B`).
    """
    reasons: List[str] = []

    if not state.nvidia_fs_loaded:
        reasons.append("nvidia_fs kernel module not loaded")
    if not state.stats_file_present:
        reasons.append("/proc/driver/nvidia-fs/stats missing")
    if state.driver_version < 470.0:
        reasons.append(f"GPU driver {state.driver_version} < 470 minimum")
    if state.storage_type in ("FUSE", "NFS-TCP"):
        reasons.append(
            f"Storage backend '{state.storage_type}' lacks kernel O_DIRECT GDS DMA support"
        )
    if state.pcie_topo_relation in ("SYS", "NODE"):
        reasons.append(
            f"PCIe topology '{state.pcie_topo_relation}' crosses NUMA/socket interconnect"
        )
    if not state.uses_cufile_api:
        reasons.append("Application uses POSIX open()/read() instead of cuFile API")

    req_align = 8192 if state.storage_type == "Lustre" else 4096
    is_aligned = (state.io_offset_bytes % req_align == 0) and (
        state.io_request_bytes % req_align == 0
    )
    if not is_aligned:
        reasons.append(
            f"I/O offset/size not aligned to {req_align} B ({state.storage_type})"
        )

    request_size_ok = state.io_request_bytes >= 1_048_576
    if not request_size_ok:
        reasons.append("Request size < 1 MiB (1,048,576 B) threshold")

    if state.nvidia_fs_io_deltas == 0:
        reasons.append("/proc/driver/nvidia-fs/stats Ops Read counter did not increment")
    if state.perf_memcpy_avx2_pct > 5.0:
        reasons.append(
            f"perf record shows {state.perf_memcpy_avx2_pct:.1f}% CPU __memcpy_avx2 samples"
        )

    prereqs_ok = (
        state.nvidia_fs_loaded
        and state.stats_file_present
        and state.driver_version >= 470.0
        and state.storage_type not in ("FUSE", "NFS-TCP")
        and state.pcie_topo_relation in ("PIX", "PXB", "PHB")
        and state.uses_cufile_api
    )

    active_path = (
        "GDS_DIRECT_DMA"
        if (prereqs_ok and is_aligned and state.nvidia_fs_io_deltas > 0 and state.perf_memcpy_avx2_pct <= 5.0)
        else "POSIX_COMPAT_CPU_BOUNCE"
    )

    return GDSAuditReport(
        prerequisites_passed=prereqs_ok,
        required_alignment_bytes=req_align,
        is_aligned=is_aligned,
        request_size_ok=request_size_ok,
        active_path=active_path,
        fallback_reasons=tuple(reasons),
    )


def evaluate_gds_benchmarks(
    cpu_trial_seconds: Sequence[float] = (0.265, 0.250, 0.248, 0.247, 0.246),
    buffer_bytes: int = 100 * 1024 * 1024,
    gdsio_cpu_gbps: float = 8.0,
    gdsio_cpu_lat_ms: float = 1.25,
    gdsio_gds_gbps: float = 9.6,
    gdsio_gds_lat_ms: float = 1.00,
) -> Dict[str, object]:
    """
    Compute the Lab 03 100 MiB CPU-bounce benchmark statistics and the AISPE
    Chapter 5 `gdsio` (-x 2 vs -x 0) uplift metrics, applying the Lab 03
    `> 20.0%` improvement decision rule (`DEPLOY_GDS` vs `SKIP_GDS`).
    """
    mean_s = sum(cpu_trial_seconds) / len(cpu_trial_seconds)
    # Lab 03 uses buffer_size / 1e6 / elapsed for MB/s reporting
    trial_mbps = [round((buffer_bytes / 1e6) / t) for t in cpu_trial_seconds]
    avg_mbps_decimal = round((buffer_bytes / 1e6) / mean_s)
    avg_mbps_mib = round((buffer_bytes / (1024.0 * 1024.0)) / mean_s)

    gdsio_bw_uplift_pct = round(
        ((gdsio_gds_gbps - gdsio_cpu_gbps) / gdsio_cpu_gbps) * 100.0, 2
    )
    gdsio_lat_reduction_pct = round(
        ((gdsio_cpu_lat_ms - gdsio_gds_lat_ms) / gdsio_cpu_lat_ms) * 100.0, 2
    )
    decision = "DEPLOY_GDS" if gdsio_bw_uplift_pct >= 20.0 else "SKIP_GDS"

    return {
        "buffer_bytes": buffer_bytes,
        "cpu_mean_s": round(mean_s, 3),
        "trial_mbps_decimal": trial_mbps,
        "cpu_avg_mbps_decimal": avg_mbps_decimal,
        "cpu_avg_mbps_mib": avg_mbps_mib,
        "gdsio_cpu_gbps": gdsio_cpu_gbps,
        "gdsio_gds_gbps": gdsio_gds_gbps,
        "gdsio_bw_uplift_pct": gdsio_bw_uplift_pct,
        "gdsio_cpu_lat_ms": gdsio_cpu_lat_ms,
        "gdsio_gds_lat_ms": gdsio_gds_lat_ms,
        "gdsio_lat_reduction_pct": gdsio_lat_reduction_pct,
        "decision": decision,
    }


# ---------------------------------------------------------------------------
# 4. Local NVMe vs Shared Storage Benchmark & Checkpoint Staging Triage
#    (Volume 15 Chapter 12 & Lab 02)
# ---------------------------------------------------------------------------

def evaluate_nvme_vs_shared_staging(
    checkpoint_gb: float = 500.0,
    shared_sync_write_gbps: float = 1.0,
    nvme_model_load_gbps: float = 3.5,
    nvme_batch_stream_gbps: float = 2.8,
    nvme_random_read_gbps: float = 1.2,
    nvme_ckpt_write_gbps: float = 2.1,
    shared_model_load_gbps: float = 1.5,
    fast_nvme_stage_gbps: float = 10.0,
) -> Dict[str, float]:
    """
    Compare local NVMe (`3.5 GB/s` seq read, `2.8 GB/s` `64 KB` x `8` batch
    stream, `1.2 GB/s` `4 MB` rand read, `2.1 GB/s` seq write) against shared
    storage (`1.0 GB/s` synchronous checkpoint stall = `500.0 s`; `10x` NVMe
    staging rule saving `9/10` = `90.0%` of critical-path stall time).
    """
    sync_stall_s = round(checkpoint_gb / shared_sync_write_gbps, 2)
    single_nvme_stage_s = round(checkpoint_gb / nvme_ckpt_write_gbps, 2)
    fast_nvme_stage_s = round(checkpoint_gb / fast_nvme_stage_gbps, 2)
    saved_s_at_10x = round(sync_stall_s - fast_nvme_stage_s, 2)
    saved_fraction_at_10x = round(saved_s_at_10x / sync_stall_s, 4)
    model_load_ratio = round(nvme_model_load_gbps / shared_model_load_gbps, 2)

    return {
        "checkpoint_gb": checkpoint_gb,
        "sync_stall_s": sync_stall_s,
        "single_nvme_stage_s": single_nvme_stage_s,
        "fast_nvme_stage_s": fast_nvme_stage_s,
        "saved_s_at_10x": saved_s_at_10x,
        "saved_fraction_at_10x": saved_fraction_at_10x,
        "nvme_model_load_gbps": nvme_model_load_gbps,
        "nvme_batch_stream_gbps": nvme_batch_stream_gbps,
        "nvme_random_read_gbps": nvme_random_read_gbps,
        "nvme_ckpt_write_gbps": nvme_ckpt_write_gbps,
        "model_load_ratio": model_load_ratio,
    }


# ---------------------------------------------------------------------------
# 5. Lustre Eviction, Local NVMe SMART/Thermal, and NFS ESTALE/Soft-Mount Triage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class NVMeDriveHealth:
    """SMART and mdadm telemetry for a local NVMe scratch drive."""
    device: str
    temperature_c: int
    percentage_used: int
    media_errors: int
    unsafe_shutdowns: int
    read_bw_gbps: float
    raid0_state: str  # "clean", "degraded", "failed"


def triage_local_nvme_health(drive: NVMeDriveHealth) -> Dict[str, object]:
    """
    Diagnose local NVMe thermal throttling (`>= 70 C` warn, `>= 80 C` critical),
    SMART wear-out (`percentage_used >= 95%` or `media_errors > 0`), and RAID-0
    array failure.
    """
    issues: List[str] = []
    status = "HEALTHY"

    if drive.raid0_state != "clean":
        status = "CRITICAL_RAID0_FAILURE"
        issues.append(
            f"RAID-0 array is '{drive.raid0_state}'; a single failed member destroys all un-flushed staging data"
        )
    if drive.media_errors > 0:
        status = "CRITICAL_MEDIA_ERROR"
        issues.append(f"{drive.media_errors} unrecoverable media errors on {drive.device}")
    if drive.temperature_c >= 80:
        if status == "HEALTHY":
            status = "CRITICAL_THERMAL_THROTTLE"
        issues.append(
            f"Temperature {drive.temperature_c} C >= 80 C critical threshold (throughput throttled to {drive.read_bw_gbps:.2f} GB/s)"
        )
    elif drive.temperature_c >= 70:
        if status == "HEALTHY":
            status = "WARNING_THERMAL_THROTTLE"
        issues.append(
            f"Temperature {drive.temperature_c} C >= 70 C warning threshold"
        )
    if drive.percentage_used >= 95:
        if status == "HEALTHY":
            status = "WARNING_ENDURANCE_WEAR"
        issues.append(
            f"SMART percentage_used={drive.percentage_used}% >= 95% wear threshold"
        )

    return {
        "device": drive.device,
        "status": status,
        "issues": tuple(issues),
        "is_throttling": drive.temperature_c >= 70 or drive.read_bw_gbps < 1.5,
    }


def triage_nfs_mount_and_estale(
    mount_options: Sequence[str],
    errno_code: int = 0,
    concurrent_gpu_nodes: int = 1,
) -> Dict[str, object]:
    """
    Audit NFS client mount options against AI production best practices:
    - Recommended read/write size: `rsize=1048576,wsize=1048576,noatime,actimeo=60,lookupcache=pos`
    - Flag `soft` mount corruption risk: under storage congestion, `soft` mounts
      return `EIO` (`errno 5`) to `torch.save()` or dataloader `read()`, causing
      silent checkpoint corruption or mid-epoch crashes; production mounts must
      use `hard`.
    - Diagnose `ESTALE` (`errno 116`, `Stale file handle`): happens when an inode
      or directory on the NFS server is deleted and recreated (or server export
      `fsid` changes) while compute clients hold open file descriptors or cached
      dentries.
    - Flag scale limit: single NFS server bottlenecks above a few GPU nodes.
    """
    opts = set(mount_options)
    risks: List[str] = []

    has_1m_rsize = "rsize=1048576" in opts and "wsize=1048576" in opts
    is_soft_mount = "soft" in opts
    is_estale = errno_code == 116

    if is_soft_mount:
        risks.append(
            "NFS 'soft' mount enabled: transient network timeouts return EIO and corrupt checkpoint writes; switch to 'hard'"
        )
    if not has_1m_rsize:
        risks.append(
            "Missing rsize=1048576,wsize=1048576 (1 MiB transfer blocks)"
        )
    if "noatime" not in opts:
        risks.append("Missing 'noatime'; every read triggers metadata atime updates")
    if is_estale:
        risks.append(
            "ESTALE (errno 116, Stale file handle): server inode/directory was replaced or unexported while client held cached dentry"
        )
    if concurrent_gpu_nodes > 8:
        risks.append(
            f"{concurrent_gpu_nodes} GPU nodes exceed single-NFS-server scale; migrate hot datasets/checkpoints to parallel FS (Lustre/BeeGFS/WEKA/VAST)"
        )

    return {
        "has_1m_transfer_size": has_1m_rsize,
        "is_soft_mount": is_soft_mount,
        "is_estale": is_estale,
        "risks": tuple(risks),
    }


def repackaging_metadata_impact(
    num_files_before: int = 10_000,
    files_per_tar_shard: int = 100,
    batch_wait_before_ms: float = 620.0,
    batch_wait_after_ms: float = 31.0,
    epoch_idle_min_before: float = 47.0,
) -> Dict[str, float]:
    """
    Calculate the Lab 04 and Chapter 12 impact of repackaging small files (`10,000`
    `100 KB` files into `100` `.tar` shards of `100` files each, or `1,000,000`
    files into `1,000`/`10,000` shards):
    - `100x` reduction in file opens
    - `95.0%` reduction in average batch wait time (`620 ms` -> `31 ms`)
    - Elimination of the `47` minutes per epoch lost to metadata overhead.
    """
    shards_after = num_files_before // files_per_tar_shard
    open_reduction_factor = round(num_files_before / shards_after, 2)
    wait_improvement_pct = round(
        ((batch_wait_before_ms - batch_wait_after_ms) / batch_wait_before_ms) * 100.0,
        1,
    )
    epoch_idle_min_after = round(epoch_idle_min_before / open_reduction_factor, 2)

    return {
        "num_files_before": float(num_files_before),
        "shards_after": float(shards_after),
        "open_reduction_factor": open_reduction_factor,
        "batch_wait_before_ms": batch_wait_before_ms,
        "batch_wait_after_ms": batch_wait_after_ms,
        "wait_improvement_pct": wait_improvement_pct,
        "epoch_idle_min_before": epoch_idle_min_before,
        "epoch_idle_min_after": epoch_idle_min_after,
    }


if __name__ == "__main__":
    inc = default_production_incident()
    res = walk_storage_decision_tree(inc)
    print(f"Incident slowdown: {res.slowdown_factor}x -> {res.primary_layer}")
