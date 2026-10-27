"""GPUDirect Storage (GDS) architecture simulator and verification toolkit.

Covers Chapter 13.3:
1. CPU bounce-buffer path vs GPUDirect Storage zero-copy path (100 MB fetch
   math, PCIe traffic amplification, and lab 5-trial baseline).
2. 7-step cuFile API lifecycle (cuFileDriverOpen -> cuFileHandleRegister ->
   cuFileBufRegister -> cuFileRead/cuFileWrite -> cuFileBufDeregister ->
   cuFileHandleDeregister -> cuFileDriverClose) and 10-stage full OS/CUDA flow.
3. BAR1 / nvidia-fs.ko P2P DMA eligibility vs POSIX compatibility-mode fallback
   when allow_compat_mode=true (including FUSE user-space block, PCIe topology
   PIX/PXB vs PHB/SYS, and /proc/driver/nvidia-fs/stats vs __memcpy_avx2).
4. 4 KiB (4,096 B) O_DIRECT alignment validator for file offsets, transfer
   sizes, and GPU HBM buffer addresses (plus 8 KiB Lustre stripe check).
5. gdsio transfer modes (-x 0 through -x 6) and Table 5-1 throughput, latency,
   and CPU utilization efficiency math (8.0 GB/s @ 1.25 ms & 85% CPU vs
   9.6 GB/s @ 1.00 ms & 25% CPU; VAST +20% on A100 and +30%+ on H100).
6. /etc/cufile.json linter (max_device_pinned_mem_size_kb, poll_mode_max_size_kb,
   allow_compat_mode, posix_unaligned_kb, static tracepoints for nsys).
7. Blackwell hardware Decompression Engine (LZ4, Snappy, Deflate at up to
   800 GB/s) + GDS storage-to-GPU pipeline and DeepSeek 3FS throughput math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. cuFile 7-Step Core API Lifecycle & 10-Stage OS/CUDA Sequence
# ---------------------------------------------------------------------------

CUFILE_SEVEN_STEP_API: Tuple[str, ...] = (
    "cuFileDriverOpen",
    "cuFileHandleRegister",
    "cuFileBufRegister",
    "cuFileRead_or_cuFileWrite",
    "cuFileBufDeregister",
    "cuFileHandleDeregister",
    "cuFileDriverClose",
)

CUFILE_TEN_STAGE_FLOW: Tuple[str, ...] = (
    "cuFileDriverOpen",
    "open_O_DIRECT",
    "cuFileHandleRegister",
    "cudaMalloc",
    "cuFileBufRegister",
    "cuFileRead_or_cuFileWrite",
    "cuFileBufDeregister",
    "cuFileHandleDeregister",
    "close_fd",
    "cuFileDriverClose",
)

SUPPORTED_KERNEL_GDS_FILESYSTEMS: Tuple[str, ...] = (
    "ext4",
    "xfs",
    "nvme",
    "nvme-of",
    "lustre",
    "wekafs",
    "vast",
    "beegfs",
    "gpfs",
    "ibm-storage-scale",
    "nfs-rdma",
    "3fs",
)


def validate_cufile_lifecycle(calls: List[str] | Tuple[str, ...]) -> Tuple[bool, str]:
    """Validate that a sequence of cuFile API calls follows the 7-step lifecycle."""
    seq = tuple(calls)
    if seq == CUFILE_SEVEN_STEP_API:
        return True, "Valid 7-step cuFile API lifecycle"
    if len(seq) != len(CUFILE_SEVEN_STEP_API):
        return (
            False,
            f"Expected {len(CUFILE_SEVEN_STEP_API)} steps, got {len(seq)}",
        )
    for idx, (got, exp) in enumerate(zip(seq, CUFILE_SEVEN_STEP_API), start=1):
        if got != exp:
            return False, f"Step {idx} mismatch: expected {exp}, got {got}"
    return True, "Valid 7-step cuFile API lifecycle"


# ---------------------------------------------------------------------------
# 2. CPU Bounce-Buffer vs GPUDirect Storage Fetch & Trial Math
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ModelFetchComparison:
    payload_mb: float
    storage_read_latency_us: float
    cpu_gpu_copy_bw_mb_s: float
    gds_dma_bw_mb_s: float
    traditional_copy_ms: float
    gds_dma_ms: float
    traditional_total_ms: float
    gds_total_ms: float
    speedup_ratio: float
    pcie_traversals_traditional: int
    pcie_traversals_gds: int


def compare_model_weight_fetch(
    payload_mb: float = 100.0,
    storage_read_latency_us: float = 100.0,
    cpu_gpu_copy_bw_mb_s: float = 3000.0,
    gds_dma_bw_mb_s: float = 6000.0,
) -> ModelFetchComparison:
    """Compare a 100 MB model-weight fetch via CPU bounce vs GDS direct DMA.

    Matches Volume 15 Chapter 4:
      - Traditional: 100 MB / 3,000 MB/s = 33.33 ms (~33 ms) + 100 us storage latency,
        with 500 us per 1 MB CPU-to-GPU copy overhead and 2 PCIe bus traversals.
      - GDS direct: 100 MB / 6,000 MB/s = 16.67 ms (~16 ms) + 100 us storage latency,
        with 1 PCIe switch traversal and ~2.0x speedup.
    """
    storage_ms = storage_read_latency_us / 1000.0
    trad_copy_ms = (payload_mb / cpu_gpu_copy_bw_mb_s) * 1000.0
    gds_dma_ms = (payload_mb / gds_dma_bw_mb_s) * 1000.0
    trad_total = trad_copy_ms + storage_ms
    gds_total = gds_dma_ms + storage_ms

    # Traditional: 33.33 ms copy + 0.10 ms storage = 33.43 ms (~33 ms)
    # GDS direct: 16.67 ms DMA + 0.10 ms storage = 16.77 ms (~16 ms)
    return ModelFetchComparison(
        payload_mb=payload_mb,
        storage_read_latency_us=storage_read_latency_us,
        cpu_gpu_copy_bw_mb_s=cpu_gpu_copy_bw_mb_s,
        gds_dma_bw_mb_s=gds_dma_bw_mb_s,
        traditional_copy_ms=round(trad_copy_ms, 2),
        gds_dma_ms=round(gds_dma_ms, 2),
        traditional_total_ms=round(trad_total, 2),
        gds_total_ms=round(gds_total, 2),
        speedup_ratio=round(trad_copy_ms / gds_dma_ms, 2),
        pcie_traversals_traditional=2,
        pcie_traversals_gds=1,
    )


def evaluate_lab03_decision(
    cpu_trial_times_s: Tuple[float, ...] = (0.265, 0.250, 0.248, 0.247, 0.246),
    buffer_size_mb: float = 100.0,
    gds_avg_throughput_mb_s: float = 960.0,
    deploy_threshold_pct: float = 20.0,
) -> Dict[str, float | str | bool]:
    """Compute Volume 15 Lab 03 5-trial CPU bounce baseline and GDS deploy decision.

    Trials (100 MB): 0.265s (378 MB/s), 0.250s (400 MB/s), 0.248s (403 MB/s),
    0.247s (404 MB/s), 0.246s (407 MB/s) -> Average 0.2512s (0.251s), 398 MB/s.
    """
    avg_time_s = sum(cpu_trial_times_s) / len(cpu_trial_times_s)
    # 100 * 1024^2 bytes / 1e6 / avg_time_s or 100 MB / avg_time_s
    cpu_tp_mb_s = round(buffer_size_mb / round(avg_time_s, 3))
    improvement_pct = ((gds_avg_throughput_mb_s - cpu_tp_mb_s) / cpu_tp_mb_s) * 100.0
    deploy = improvement_pct > deploy_threshold_pct
    return {
        "cpu_avg_time_s": round(avg_time_s, 3),
        "cpu_avg_throughput_mb_s": float(cpu_tp_mb_s),
        "gds_avg_throughput_mb_s": round(gds_avg_throughput_mb_s, 1),
        "improvement_pct": round(improvement_pct, 1),
        "deploy_gds": deploy,
        "recommendation": "DEPLOY GDS" if deploy else "SKIP GDS",
    }


# ---------------------------------------------------------------------------
# 3. 4 KiB O_DIRECT Alignment Validator (Offsets, Sizes, GPU Buffers, Lustre)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AlignmentValidation:
    file_offset_bytes: int
    transfer_size_bytes: int
    gpu_buffer_addr: int
    required_alignment_bytes: int
    offset_aligned: bool
    size_aligned: bool
    buffer_aligned: bool
    all_aligned: bool
    realigned_offset_bytes: int
    realigned_size_bytes: int
    bounce_penalty_if_unaligned: bool


def validate_o_direct_alignment(
    file_offset_bytes: int,
    transfer_size_bytes: int,
    gpu_buffer_addr: int,
    required_alignment_bytes: int = 4096,
) -> AlignmentValidation:
    """Validate 4 KiB (4,096 B) O_DIRECT alignment (or 8 KiB = 8,192 B for Lustre).

    NVMe / O_DIRECT DMA requires file offset, I/O length, and memory address to
    be integer multiples of the logical block / page size (4,096 bytes; 8,192
    bytes for some Lustre OST configurations). If unaligned, cuFile must either
    return CU_FILE_IO_NOT_SUPPORTED / invalid buffer alignment or allocate an
    internal bounce buffer when posix_unaligned_kb is enabled.
    """
    if required_alignment_bytes <= 0 or (
        required_alignment_bytes & (required_alignment_bytes - 1)
    ) != 0:
        raise ValueError("required_alignment_bytes must be a positive power of two")

    mask = required_alignment_bytes - 1
    off_ok = (file_offset_bytes & mask) == 0
    size_ok = transfer_size_bytes > 0 and ((transfer_size_bytes & mask) == 0)
    buf_ok = (gpu_buffer_addr & mask) == 0
    all_ok = off_ok and size_ok and buf_ok

    # Example: file_offset = 4,100, size = 1,000,000 -> end_byte = 1,004,100
    # realigned_off = 4,096, realigned_end = 1,007,616, realigned_size = 1,003,520
    realigned_off = file_offset_bytes & ~mask
    end_byte = file_offset_bytes + transfer_size_bytes
    realigned_end = (end_byte + mask) & ~mask
    realigned_size = max(required_alignment_bytes, realigned_end - realigned_off)

    return AlignmentValidation(
        file_offset_bytes=file_offset_bytes,
        transfer_size_bytes=transfer_size_bytes,
        gpu_buffer_addr=gpu_buffer_addr,
        required_alignment_bytes=required_alignment_bytes,
        offset_aligned=off_ok,
        size_aligned=size_ok,
        buffer_aligned=buf_ok,
        all_aligned=all_ok,
        realigned_offset_bytes=realigned_off,
        realigned_size_bytes=realigned_size,
        bounce_penalty_if_unaligned=not all_ok,
    )


# ---------------------------------------------------------------------------
# 4. BAR1 / nvidia-fs P2P DMA Eligibility vs Compatibility-Mode Fallback
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GdsPathResolution:
    selected_path: str  # "gds-p2p-dma", "gds-root-complex-degraded", "compat-posix-fallback", "error-io-rejected"
    nvidia_fs_stats_increment: bool
    cpu_memcpy_avx2_active: bool
    bar1_pinned_kb: int
    reason: str


def resolve_gds_execution_path(
    nvidia_fs_loaded: bool,
    filesystem_type: str,
    is_fuse_mount: bool,
    o_direct_enabled: bool,
    uses_cufile_api: bool,
    pcie_topology: str,  # "PIX", "PXB", "PHB", "SYS"
    alignment_ok: bool,
    allow_compat_mode: bool,
    bar1_free_kb: int,
    requested_buf_kb: int,
) -> GdsPathResolution:
    """Determine whether an I/O executes via nvidia-fs P2P DMA or falls back to CPU.

    Rules from Volume 15 Ch 4 & ASP Ch 5:
    1. If application uses standard open()/read() or torch.load(..., map_location='cpu')
       instead of cuFile API, it always takes the CPU bounce path (__memcpy_avx2 active,
       /proc/driver/nvidia-fs/stats unchanged).
    2. FUSE user-space filesystems cannot support kernel O_DIRECT DMA for GDS.
    3. If nvidia-fs.ko is not loaded, filesystem is unsupported, O_DIRECT is off,
       alignment fails, or BAR1 pinned quota is exceeded:
         - If allow_compat_mode=True in /etc/cufile.json, libcufile silently falls
           back to POSIX pread()/pwrite() + cudaMemcpyAsync (CPU bounce).
         - If allow_compat_mode=False, cuFileRead/cuFileWrite fails loudly.
    4. If all GDS prerequisites pass:
         - On PIX or PXB topology, NIC/NVMe performs direct P2P DMA into GPU BAR1.
         - On PHB or SYS topology, nvidia-fs is active but PCIe TLPs traverse the
           CPU Root Complex / UPI interconnect (degraded P2P).
    """
    fs_norm = filesystem_type.lower().strip()
    topo_norm = pcie_topology.upper().strip()

    if not uses_cufile_api:
        return GdsPathResolution(
            selected_path="compat-posix-fallback",
            nvidia_fs_stats_increment=False,
            cpu_memcpy_avx2_active=True,
            bar1_pinned_kb=0,
            reason="Application did not call cuFile API (standard POSIX/torch.load CPU bounce)",
        )

    failure_reasons: List[str] = []
    if is_fuse_mount or fs_norm == "fuse":
        failure_reasons.append("FUSE user-space mount lacks kernel O_DIRECT DMA integration")
    if not nvidia_fs_loaded:
        failure_reasons.append("nvidia-fs.ko kernel driver is not loaded")
    if fs_norm not in SUPPORTED_KERNEL_GDS_FILESYSTEMS:
        failure_reasons.append(f"Filesystem '{filesystem_type}' is not registered with nvidia-fs")
    if not o_direct_enabled:
        failure_reasons.append("File descriptor opened without O_DIRECT")
    if not alignment_ok:
        failure_reasons.append("Buffer/offset/size violates 4 KiB O_DIRECT alignment")
    if requested_buf_kb > bar1_free_kb:
        failure_reasons.append(
            f"Requested buffer ({requested_buf_kb} KB) exceeds available BAR1 pinned quota ({bar1_free_kb} KB)"
        )

    if failure_reasons:
        joined = "; ".join(failure_reasons)
        if allow_compat_mode:
            return GdsPathResolution(
                selected_path="compat-posix-fallback",
                nvidia_fs_stats_increment=False,
                cpu_memcpy_avx2_active=True,
                bar1_pinned_kb=0,
                reason=f"Silent fallback to POSIX compatibility mode ({joined})",
            )
        return GdsPathResolution(
            selected_path="error-io-rejected",
            nvidia_fs_stats_increment=False,
            cpu_memcpy_avx2_active=False,
            bar1_pinned_kb=0,
            reason=f"Strict GDS failure (allow_compat_mode=false): {joined}",
        )

    if topo_norm in ("PIX", "PXB"):
        return GdsPathResolution(
            selected_path="gds-p2p-dma",
            nvidia_fs_stats_increment=True,
            cpu_memcpy_avx2_active=False,
            bar1_pinned_kb=requested_buf_kb,
            reason=f"Direct PCIe switch P2P DMA into GPU BAR1 over {topo_norm}",
        )

    return GdsPathResolution(
        selected_path="gds-root-complex-degraded",
        nvidia_fs_stats_increment=True,
        cpu_memcpy_avx2_active=False,
        bar1_pinned_kb=requested_buf_kb,
        reason=f"GDS active via nvidia-fs but degraded by root-complex/cross-socket topology ({topo_norm})",
    )


# ---------------------------------------------------------------------------
# 5. gdsio Transfer Modes (-x 0..6) & Table 5-1 Throughput / CPU Efficiency
# ---------------------------------------------------------------------------

GDSIO_TRANSFER_MODES: Dict[int, Dict[str, str | bool]] = {
    0: {
        "flag": "-x 0",
        "name": "GDS_STORAGE_TO_GPU",
        "description": "Storage <-> GPU HBM direct via cuFile and nvidia-fs P2P DMA",
        "uses_gds": True,
        "uses_host_bounce": False,
    },
    1: {
        "flag": "-x 1",
        "name": "STORAGE_TO_CPU_ONLY",
        "description": "Storage <-> Host CPU RAM only (no GPU transfer)",
        "uses_gds": False,
        "uses_host_bounce": True,
    },
    2: {
        "flag": "-x 2",
        "name": "STORAGE_TO_CPU_TO_GPU_PINNED_ASYNC",
        "description": "Storage -> Pinned Host RAM -> GPU HBM via cudaMemcpyAsync",
        "uses_gds": False,
        "uses_host_bounce": True,
    },
    3: {
        "flag": "-x 3",
        "name": "STORAGE_TO_CPU_PAGEABLE_TO_GPU",
        "description": "Storage -> Pageable Host RAM -> GPU HBM via synchronous cudaMemcpy",
        "uses_gds": False,
        "uses_host_bounce": True,
    },
    4: {
        "flag": "-x 4",
        "name": "STORAGE_MMAP_TO_CPU_TO_GPU",
        "description": "Memory-mapped file (mmap) -> Host RAM -> GPU HBM",
        "uses_gds": False,
        "uses_host_bounce": True,
    },
    5: {
        "flag": "-x 5",
        "name": "GDS_BATCH_API",
        "description": "Storage <-> GPU HBM direct via cuFileBatchIOSubmit",
        "uses_gds": True,
        "uses_host_bounce": False,
    },
    6: {
        "flag": "-x 6",
        "name": "GDS_ASYNC_STREAM_API",
        "description": "Storage <-> GPU HBM direct via cuFileReadAsync / cuFileWriteAsync on CUDA stream",
        "uses_gds": True,
        "uses_host_bounce": False,
    },
}


@dataclass(frozen=True)
class GdsioComparisonReport:
    cpu_mode_flag: str
    gds_mode_flag: str
    file_size_gb: float
    num_workers: int
    io_size_kb: int
    cpu_throughput_gb_s: float
    gds_throughput_gb_s: float
    throughput_improvement_pct: float
    cpu_latency_ms: float
    gds_latency_ms: float
    latency_reduction_pct: float
    cpu_utilization_before_pct: float
    cpu_utilization_after_pct: float
    cpu_utilization_saved_pct_points: float
    gb_per_sec_per_cpu_pct_before: float
    gb_per_sec_per_cpu_pct_after: float
    cpu_efficiency_multiplier: float
    vast_a100_gain_pct: float
    vast_h100_gain_pct: float


def evaluate_gdsio_table_5_1(
    file_size_gb: float = 10.0,
    num_workers: int = 4,
    io_size_kb: int = 1024,
    cpu_throughput_gb_s: float = 8.0,
    gds_throughput_gb_s: float = 9.6,
    cpu_latency_ms: float = 1.25,
    gds_latency_ms: float = 1.00,
    cpu_util_before_pct: float = 85.0,
    cpu_util_after_pct: float = 25.0,
) -> GdsioComparisonReport:
    """Evaluate ASP Ch 5 Table 5-1 gdsio benchmark and CPU efficiency metrics.

    Commands from ASP Ch 5:
      Before (-x 2): /usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 2
        -> Total Throughput: 8.0 GB/s, Average Latency: 1.25 ms, ~85% CPU util
      After  (-x 0): /usr/local/cuda/gds/tools/gdsio -f /mnt/data/large_file -d 0 -w 4 -s 10G -i 1M -I 0 -x 0
        -> Total Throughput: 9.6 GB/s (+20%), Average Latency: 1.00 ms (-20%), ~25% CPU util
      VAST Data report: +20% on NVIDIA Ampere A100 and +30%+ on Hopper H100.
    """
    tp_gain = ((gds_throughput_gb_s - cpu_throughput_gb_s) / cpu_throughput_gb_s) * 100.0
    lat_red = ((cpu_latency_ms - gds_latency_ms) / cpu_latency_ms) * 100.0
    cpu_saved = cpu_util_before_pct - cpu_util_after_pct

    # For a 10.0 GB file: 10.0 / 8.0 = 1.2500 s vs 10.0 / 9.6 = 1.0417 s (0.2083 s saved)
    eff_before = cpu_throughput_gb_s / cpu_util_before_pct
    eff_after = gds_throughput_gb_s / cpu_util_after_pct

    return GdsioComparisonReport(
        cpu_mode_flag="-x 2",
        gds_mode_flag="-x 0",
        file_size_gb=file_size_gb,
        num_workers=num_workers,
        io_size_kb=io_size_kb,
        cpu_throughput_gb_s=round(cpu_throughput_gb_s, 2),
        gds_throughput_gb_s=round(gds_throughput_gb_s, 2),
        throughput_improvement_pct=round(tp_gain, 2),
        cpu_latency_ms=round(cpu_latency_ms, 2),
        gds_latency_ms=round(gds_latency_ms, 2),
        latency_reduction_pct=round(lat_red, 2),
        cpu_utilization_before_pct=round(cpu_util_before_pct, 1),
        cpu_utilization_after_pct=round(cpu_util_after_pct, 1),
        cpu_utilization_saved_pct_points=round(cpu_saved, 1),
        gb_per_sec_per_cpu_pct_before=round(eff_before, 4),
        gb_per_sec_per_cpu_pct_after=round(eff_after, 4),
        cpu_efficiency_multiplier=round(eff_after / eff_before, 2),
        vast_a100_gain_pct=20.0,
        vast_h100_gain_pct=30.0,
    )


# ---------------------------------------------------------------------------
# 6. /etc/cufile.json Configuration Linter
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CufileJsonLintResult:
    valid_for_strict_gds_verification: bool
    max_pinned_mem_gib: float
    poll_threshold_kb: int
    poll_triggers_for_io_kb: bool
    nsys_tracepoints_enabled: bool
    issues: Tuple[str, ...]


def lint_cufile_json(
    config: Dict[str, object],
    expected_io_size_kb: int = 1024,
) -> CufileJsonLintResult:
    """Lint a parsed /etc/cufile.json dictionary for production and verification traps."""
    props = config.get("properties", {})
    if not isinstance(props, dict):
        props = {}
    prof = config.get("profile", {})
    if not isinstance(prof, dict):
        prof = {}
    fs_cfg = config.get("fs", {})
    if not isinstance(fs_cfg, dict):
        fs_cfg = {}

    max_pinned_kb = int(props.get("max_device_pinned_mem_size_kb", 33_554_432))
    use_poll = bool(props.get("use_poll_mode", False))
    poll_max_kb = int(props.get("poll_mode_max_size_kb", 4))
    allow_compat = bool(props.get("allow_compat_mode", True))

    nvtx_on = bool(prof.get("nvtx", False))
    stats_level = int(prof.get("cufile_stats", 0))

    generic_fs = fs_cfg.get("generic", {})
    if not isinstance(generic_fs, dict):
        generic_fs = {}
    unaligned_kb = bool(generic_fs.get("posix_unaligned_kb", False))

    issues: List[str] = []
    if allow_compat:
        issues.append(
            "properties.allow_compat_mode is true: cuFile will silently fall back to POSIX CPU bounce on error"
        )
    if use_poll and expected_io_size_kb > poll_max_kb:
        issues.append(
            f"properties.use_poll_mode is true with poll_mode_max_size_kb={poll_max_kb}, "
            f"which is smaller than workload I/O ({expected_io_size_kb} KB)"
        )
    if max_pinned_kb < 1_048_576:
        issues.append(
            f"properties.max_device_pinned_mem_size_kb ({max_pinned_kb} KB) is below 1 GiB"
        )
    if unaligned_kb:
        issues.append(
            "fs.generic.posix_unaligned_kb is true: unaligned I/Os will stage through an internal bounce buffer"
        )

    return CufileJsonLintResult(
        valid_for_strict_gds_verification=(not allow_compat and not unaligned_kb),
        max_pinned_mem_gib=round(max_pinned_kb / (1024.0 * 1024.0), 2),
        poll_threshold_kb=poll_max_kb,
        poll_triggers_for_io_kb=(use_poll and expected_io_size_kb <= poll_max_kb),
        nsys_tracepoints_enabled=(nvtx_on and stats_level >= 1),
        issues=tuple(issues),
    )


# ---------------------------------------------------------------------------
# 7. Blackwell Hardware Decompression Engine (800 GB/s) & 3FS Pipeline Math
# ---------------------------------------------------------------------------

BLACKWELL_DECOMPRESSION_FORMATS: Tuple[str, ...] = ("LZ4", "Snappy", "Deflate")
BLACKWELL_DECOMP_PEAK_GB_S: float = 800.0


@dataclass(frozen=True)
class DecompressionPipelineResult:
    compression_format: str
    supported_by_hw_engine: bool
    uncompressed_batch_gb: float
    compression_ratio: float
    compressed_storage_read_gb: float
    storage_gds_bw_gb_s: float
    hw_decomp_engine_bw_gb_s: float
    uncompressed_gds_read_time_ms: float
    compressed_gds_read_time_ms: float
    hw_decompression_time_ms: float
    pipelined_total_time_ms: float
    effective_uncompressed_throughput_gb_s: float
    end_to_end_speedup: float


def simulate_blackwell_gds_decompression(
    compression_format: str = "LZ4",
    uncompressed_batch_gb: float = 4.0,
    compression_ratio: float = 2.5,
    storage_gds_bw_gb_s: float = 50.0,
    hw_decomp_engine_bw_gb_s: float = BLACKWELL_DECOMP_PEAK_GB_S,
) -> DecompressionPipelineResult:
    """Model GDS read of compressed batches + Blackwell Hardware Decompression Engine.

    From ASP Ch 5:
    - Modern Blackwell GPUs include an on-die Hardware Decompression Engine
      supporting LZ4, Snappy, and Deflate at up to 800 GB/s (plus 900 GB/s
      bidirectional NVLink-C2C on Grace Blackwell), freeing GPU SMs for
      compute kernels.
    - Reading compressed data via GDS cuts storage I/O time by `compression_ratio`,
      and the 800 GB/s hardware decompression engine unpacks it in-pipeline in
      HBM without becoming the bottleneck.
    """
    fmt_clean = compression_format.strip()
    supported = any(fmt_clean.lower() == f.lower() for f in BLACKWELL_DECOMPRESSION_FORMATS)
    if not supported:
        raise ValueError(
            f"Unsupported hardware decompression format '{compression_format}'; "
            f"supported formats: {BLACKWELL_DECOMPRESSION_FORMATS}"
        )

    compressed_gb = uncompressed_batch_gb / compression_ratio
    uncomp_read_ms = (uncompressed_batch_gb / storage_gds_bw_gb_s) * 1000.0
    comp_read_ms = (compressed_gb / storage_gds_bw_gb_s) * 1000.0
    decomp_ms = (uncompressed_batch_gb / hw_decomp_engine_bw_gb_s) * 1000.0

    # Serial sum (conservative): 32.0 ms + 5.0 ms = 37.0 ms (0.037 s) -> 4.0 / 0.037 = 108.11 GB/s
    total_ms = comp_read_ms + decomp_ms
    eff_gb_s = uncompressed_batch_gb / (total_ms / 1000.0)
    speedup = uncomp_read_ms / total_ms

    return DecompressionPipelineResult(
        compression_format=fmt_clean,
        supported_by_hw_engine=supported,
        uncompressed_batch_gb=round(uncompressed_batch_gb, 4),
        compression_ratio=round(compression_ratio, 2),
        compressed_storage_read_gb=round(compressed_gb, 4),
        storage_gds_bw_gb_s=round(storage_gds_bw_gb_s, 2),
        hw_decomp_engine_bw_gb_s=round(hw_decomp_engine_bw_gb_s, 2),
        uncompressed_gds_read_time_ms=round(uncomp_read_ms, 3),
        compressed_gds_read_time_ms=round(comp_read_ms, 3),
        hw_decompression_time_ms=round(decomp_ms, 3),
        pipelined_total_time_ms=round(total_ms, 3),
        effective_uncompressed_throughput_gb_s=round(eff_gb_s, 2),
        end_to_end_speedup=round(speedup, 2),
    )


def evaluate_deepseek_3fs_vs_ceph(
    nodes: int = 68,
    nvme_drives_per_node: int = 10,
    nvme_drive_size_tb: int = 16,
    three_fs_fg_tb_s: float = 6.6,
    three_fs_bg_tb_s: float = 1.4,
    three_fs_peak_tb_s: float = 7.3,
    ceph_tb_s: float = 1.1,
) -> Dict[str, float | int]:
    """Compute DeepSeek Fire-Flyer File System (3FS) cluster metrics from ASP Ch 5."""
    total_drives = nodes * nvme_drives_per_node
    raw_capacity_tb = total_drives * nvme_drive_size_tb
    combined_tb_s = three_fs_fg_tb_s + three_fs_bg_tb_s
    per_node_fg_gb_s = (three_fs_fg_tb_s * 1000.0) / nodes
    vs_ceph_ratio = three_fs_fg_tb_s / ceph_tb_s
    return {
        "nodes": nodes,
        "total_nvme_drives": total_drives,
        "raw_capacity_tb": raw_capacity_tb,
        "three_fs_fg_tb_s": round(three_fs_fg_tb_s, 2),
        "three_fs_bg_tb_s": round(three_fs_bg_tb_s, 2),
        "three_fs_combined_tb_s": round(combined_tb_s, 2),
        "three_fs_peak_tb_s": round(three_fs_peak_tb_s, 2),
        "ceph_tb_s": round(ceph_tb_s, 2),
        "per_node_fg_gb_s": round(per_node_fg_gb_s, 2),
        "speedup_over_ceph": round(vs_ceph_ratio, 2),
    }


def evaluate_gpu_io_wait_speedup(
    initial_io_wait_fraction: float = 0.30,
    tuned_io_wait_fraction: float = 0.05,
) -> Dict[str, float]:
    """Model ASP Ch 5 GPU I/O wait reduction (30% wait -> 5% wait = 6x reduction in wait)."""
    wait_reduction_factor = initial_io_wait_fraction / tuned_io_wait_fraction
    compute_active_before = 1.0 - initial_io_wait_fraction
    compute_active_after = 1.0 - tuned_io_wait_fraction
    step_throughput_gain_pct = (
        (compute_active_after - compute_active_before) / compute_active_before
    ) * 100.0
    return {
        "initial_wait_pct": round(initial_io_wait_fraction * 100.0, 1),
        "tuned_wait_pct": round(tuned_io_wait_fraction * 100.0, 1),
        "wait_reduction_factor": round(wait_reduction_factor, 2),
        "step_throughput_gain_pct": round(step_throughput_gain_pct, 2),
    }


if __name__ == "__main__":
    rep = evaluate_gdsio_table_5_1()
    print(
        f"[gdsio Table 5-1] {rep.cpu_mode_flag}: {rep.cpu_throughput_gb_s} GB/s @ {rep.cpu_latency_ms} ms "
        f"({rep.cpu_utilization_before_pct}% CPU) -> "
        f"{rep.gds_mode_flag}: {rep.gds_throughput_gb_s} GB/s (+{rep.throughput_improvement_pct}%) @ "
        f"{rep.gds_latency_ms} ms (-{rep.latency_reduction_pct}%, {rep.cpu_utilization_after_pct}% CPU)"
    )
    decomp = simulate_blackwell_gds_decompression()
    print(
        f"[Blackwell Decompression] {decomp.compression_format}: {decomp.uncompressed_batch_gb} GB batch "
        f"({decomp.compressed_storage_read_gb} GB on disk) read+unpacked in {decomp.pipelined_total_time_ms} ms "
        f"({decomp.effective_uncompressed_throughput_gb_s} GB/s effective, {decomp.end_to_end_speedup}x vs uncompressed)"
    )
