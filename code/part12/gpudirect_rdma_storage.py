"""GPUDirect RDMA and GPUDirect Storage (GDS) simulator and analysis toolkit.

Covers Chapter 12.19:
1. Host bounce-buffer staging (5-step inter-node / 2-hop PCIe + DRAM per node)
   vs GPUDirect RDMA zero-copy PCIe P2P (BAR1 DMA via PCIe switch).
2. Kernel memory-pinning backends: nvidia-peermem vs Linux dma-buf eligibility,
   Large BAR1 / Above 4G Decoding requirements.
3. NCCL_NET_GDR_LEVEL distance cutoffs (LOC, PIX, PXB, PHB, NODE, SYS) and
   NCCL_NET_GDR_READ rules.
4. PCIe Access Control Services (ACS) SrcValid+/ReqRedir+/CmpltRedir+/UpFwd+
   P2P trap and setpci ECAP_ACS+0x6.w=0000 remediation.
5. GPUDirect Storage (GDS) cuFile + nvidia-fs.ko pipeline, /etc/cufile.json
   validation, gdsio Table 5-1 (-x 2 vs -x 0) benchmarks, checkpoint burst
   sizing, and WebDataset metadata reduction math.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# ---------------------------------------------------------------------------
# 1. Host Bounce-Buffer vs GPUDirect RDMA Bandwidth & Latency Model
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DataPathComparison:
    payload_gb: float
    nic_rate_gbps: float
    pcie_link_gb_s: float
    host_dram_bw_gb_s: float
    # Per-node PCIe traversals per byte of payload
    staged_pcie_hops_per_node: int
    gdr_pcie_hops_per_node: int
    # Per-node DRAM traversals per byte of payload (write + read = 2)
    staged_dram_ops_per_node: int
    gdr_dram_ops_per_node: int
    # Effective achieved single-stream throughput (GB/s)
    staged_effective_gb_s: float
    gdr_effective_gb_s: float
    # Total transfer time (seconds) for payload_gb
    staged_transfer_time_s: float
    gdr_transfer_time_s: float
    speedup_factor: float
    # Aggregate PCIe and DRAM byte volume per node (GB)
    staged_pcie_volume_gb_per_node: float
    gdr_pcie_volume_gb_per_node: float
    staged_dram_volume_gb_per_node: float
    gdr_dram_volume_gb_per_node: float


def compare_bounce_buffer_vs_gdr(
    payload_gb: float = 10.0,
    nic_rate_gbps: float = 400.0,
    pcie_link_gb_s: float = 64.0,
    host_dram_per_channel_gb_s: float = 12.5,
    base_staged_lat_us: float = 18.0,
    base_gdr_lat_us: float = 2.0,
) -> DataPathComparison:
    """Compare CPU bounce-buffer staging against GPUDirect RDMA zero-copy P2P.

    Without GPUDirect RDMA (5-step path across two nodes):
      1. GPU A -> Host RAM A (PCIe hop 1, DRAM write)
      2. Host RAM A -> NIC A (PCIe hop 2, DRAM read)
      3. NIC A -> Network -> NIC B (fabric transit)
      4. NIC B -> Host RAM B (PCIe hop 1 on B, DRAM write)
      5. Host RAM B -> GPU B (PCIe hop 2 on B, DRAM read)
    Each node executes 2 PCIe traversals and 2 DRAM operations (write + read)
    through the CPU root complex. If root-complex / bounce-buffer copy limits
    each stream to host_dram_per_channel_gb_s / 2 (e.g., 6.25 GB/s = 50 Gbps),
    a 400 Gbps (50 GB/s) link is throttled to 6.25 GB/s (8x slower).

    With GPUDirect RDMA:
      1. NIC A DMAs directly from GPU A BAR1 over the shared PCIe switch (1 hop)
      2. NIC A -> Network -> NIC B
      3. NIC B DMAs directly into GPU B BAR1 over the shared PCIe switch (1 hop)
    Each node executes 1 PCIe switch hop and 0 host DRAM operations.
    """
    nic_gb_s = nic_rate_gbps / 8.0
    # Staged path is bounded by min(NIC, PCIe/2, DRAM/2)
    staged_bw = min(nic_gb_s, pcie_link_gb_s / 2.0, host_dram_per_channel_gb_s / 2.0)
    # GDR path runs at min(NIC, PCIe_switch_link)
    gdr_bw = min(nic_gb_s, pcie_link_gb_s)

    staged_time_s = (base_staged_lat_us * 1e-6) + (payload_gb / staged_bw)
    gdr_time_s = (base_gdr_lat_us * 1e-6) + (payload_gb / gdr_bw)

    return DataPathComparison(
        payload_gb=payload_gb,
        nic_rate_gbps=nic_rate_gbps,
        pcie_link_gb_s=pcie_link_gb_s,
        host_dram_bw_gb_s=host_dram_per_channel_gb_s,
        staged_pcie_hops_per_node=2,
        gdr_pcie_hops_per_node=1,
        staged_dram_ops_per_node=2,
        gdr_dram_ops_per_node=0,
        staged_effective_gb_s=round(staged_bw, 4),
        gdr_effective_gb_s=round(gdr_bw, 4),
        staged_transfer_time_s=round(staged_time_s, 6),
        gdr_transfer_time_s=round(gdr_time_s, 6),
        speedup_factor=round(gdr_bw / staged_bw, 4),
        staged_pcie_volume_gb_per_node=round(payload_gb * 2, 4),
        gdr_pcie_volume_gb_per_node=round(payload_gb * 1, 4),
        staged_dram_volume_gb_per_node=round(payload_gb * 2, 4),
        gdr_dram_volume_gb_per_node=0.0,
    )


def pcie_gen_bandwidth_gb_s(gen: int, lanes: int = 16) -> Tuple[float, float]:
    """Return (gt_per_s_per_lane, unidirectional_gb_s) for PCIe Gen3/4/5/6.

    Gen3: 8 GT/s (128b/130b) -> ~0.9846 GB/s/lane -> 15.754 GB/s x16
    Gen4: 16 GT/s (128b/130b) -> ~1.9692 GB/s/lane -> 31.508 GB/s x16
    Gen5: 32 GT/s (128b/130b) -> ~3.9385 GB/s/lane -> 63.015 GB/s x16 (~63 Gbps/lane raw = ~64 GB/s nominal)
    Gen6: 64 GT/s (PAM4 FLIT) -> ~7.56 GB/s/lane -> 121.0 GB/s x16
    """
    table = {
        3: (8.0, round(8.0 * (128.0 / 130.0) / 8.0 * lanes, 2)),
        4: (16.0, round(16.0 * (128.0 / 130.0) / 8.0 * lanes, 2)),
        5: (32.0, round(32.0 * (128.0 / 130.0) / 8.0 * lanes, 2)),
        6: (64.0, round(64.0 * (242.0 / 256.0) / 8.0 * lanes, 2)),
    }
    if gen not in table:
        raise ValueError(f"Unsupported PCIe generation: {gen}")
    return table[gen]


# ---------------------------------------------------------------------------
# 2. Kernel Memory Registration: nvidia-peermem vs Linux dma-buf Eligibility
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GdrKernelEligibility:
    mode: str  # "dma-buf", "nvidia-peermem", or "host-staging-fallback"
    gdr_supported: bool
    reason: str


def evaluate_gdr_kernel_backend(
    kernel_major: int,
    kernel_minor: int,
    is_open_gpu_kmod: bool,
    rdma_core_version: int,
    peermem_loaded: bool,
    large_bar1_enabled: bool,
    prefer_dmabuf: bool = True,
) -> GdrKernelEligibility:
    """Determine whether GPUDirect RDMA uses dma-buf, nvidia-peermem, or falls back.

    Rules:
    - Large BAR1 (Above 4G Decoding / Resizable BAR) is mandatory for both paths
      so the GPU can expose HBM aperture on the PCIe bus.
    - Linux dma-buf path requires:
        * Linux kernel >= 5.12
        * NVIDIA Open GPU Kernel Modules (nvidia.ko -open)
        * rdma-core / libibverbs >= 34 (ibv_reg_dmabuf_mr support)
    - nvidia-peermem path requires:
        * nvidia-peermem.ko loaded and registered with MLNX_OFED / DOCA-OFED ib_core
    """
    if not large_bar1_enabled:
        return GdrKernelEligibility(
            mode="host-staging-fallback",
            gdr_supported=False,
            reason="BAR1 aperture too small (Above 4G Decoding / Large BAR disabled in BIOS)",
        )

    kver = (kernel_major, kernel_minor)
    dmabuf_capable = (
        kver >= (5, 12)
        and is_open_gpu_kmod
        and rdma_core_version >= 34
    )

    if prefer_dmabuf and dmabuf_capable:
        return GdrKernelEligibility(
            mode="dma-buf",
            gdr_supported=True,
            reason="Upstream Linux dma-buf (kernel >= 5.12, OpenRM, ibv_reg_dmabuf_mr)",
        )

    if peermem_loaded:
        return GdrKernelEligibility(
            mode="nvidia-peermem",
            gdr_supported=True,
            reason="Peer-memory client API via nvidia-peermem.ko + OFED ib_core",
        )

    if dmabuf_capable:
        return GdrKernelEligibility(
            mode="dma-buf",
            gdr_supported=True,
            reason="Upstream Linux dma-buf fallback (nvidia-peermem not loaded)",
        )

    return GdrKernelEligibility(
        mode="host-staging-fallback",
        gdr_supported=False,
        reason="Neither dma-buf prerequisites nor nvidia-peermem.ko are active",
    )


# ---------------------------------------------------------------------------
# 3. NCCL_NET_GDR_LEVEL Topology Distance Cutoffs & NCCL_NET_GDR_READ
# ---------------------------------------------------------------------------

NCCL_PATH_DISTANCE: Dict[str, int] = {
    "LOC": 0,   # Same device (never applies to separate GPU+NIC, reference baseline)
    "PIX": 1,   # Traverse at most a single PCIe switch
    "PXB": 2,   # Traverse multiple cascaded PCIe switches without reaching host bridge
    "PHB": 3,   # Traverse PCIe Host Bridge (CPU Root Complex) within same NUMA node
    "NODE": 4,  # Traverse interconnect between PCIe host bridges inside one NUMA node
    "SYS": 5,   # Traverse inter-socket NUMA interconnect (UPI / QPI / xGMI)
}


@dataclass(frozen=True)
class GdrTopologyDecision:
    gpu_nic_path: str
    gdr_level_cutoff: str
    acs_enabled: bool
    effective_path: str
    gdr_write_enabled: bool
    gdr_read_enabled: bool
    transport_summary: str


def evaluate_nccl_gdr_level(
    gpu_nic_path: str,
    gdr_level_cutoff: str = "PXB",
    gdr_read_env: int | None = None,
    acs_enabled: bool = False,
) -> GdrTopologyDecision:
    """Evaluate NCCL GPUDirect RDMA eligibility given PCIe topology and ACS state.

    - Physical path is one of PIX, PXB, PHB, NODE, SYS.
    - If PCIe ACS (Access Control Services) is enabled on the switch port, P2P
      packets are redirected upstream to the CPU Root Complex (PHB/SYS), which
      degrades PIX/PXB into PHB (or SYS across sockets).
    - NCCL enables GDR when distance(effective_path) <= distance(gdr_level_cutoff).
    - By default (gdr_read_env is None), NCCL enables GDR DMA reads only when
      effective_path is PIX or PXB (not PHB/SYS, because PCIe P2P reads across
      a root complex suffer severe request-completion round-trip penalties).
    """
    path_u = gpu_nic_path.upper()
    cutoff_u = gdr_level_cutoff.upper()
    if path_u not in NCCL_PATH_DISTANCE:
        raise ValueError(f"Unknown GPU-NIC path: {gpu_nic_path}")
    if cutoff_u not in NCCL_PATH_DISTANCE:
        raise ValueError(f"Unknown NCCL_NET_GDR_LEVEL: {gdr_level_cutoff}")

    # ACS redirects P2P switch traffic up to the CPU Root Complex (PHB)
    if acs_enabled and NCCL_PATH_DISTANCE[path_u] <= NCCL_PATH_DISTANCE["PXB"]:
        effective_path = "PHB"
    else:
        effective_path = path_u

    eff_dist = NCCL_PATH_DISTANCE[effective_path]
    cut_dist = NCCL_PATH_DISTANCE[cutoff_u]

    gdr_write = eff_dist <= cut_dist
    if not gdr_write:
        gdr_read = False
    elif gdr_read_env is not None:
        gdr_read = bool(gdr_read_env == 1)
    else:
        # Default: GDR read only enabled on direct PCIe switch paths (PIX/PXB)
        gdr_read = eff_dist <= NCCL_PATH_DISTANCE["PXB"]

    if gdr_write and gdr_read:
        summary = f"NET/IB : GPU Direct RDMA Enabled (Read+Write) on path {effective_path}"
    elif gdr_write and not gdr_read:
        summary = f"NET/IB : GPU Direct RDMA Enabled (Write-only, Read host-staged) on path {effective_path}"
    else:
        summary = f"NET/IB : GPU Direct RDMA Disabled on path {effective_path} > cutoff {cutoff_u} (Host Bounce Buffer)"

    return GdrTopologyDecision(
        gpu_nic_path=path_u,
        gdr_level_cutoff=cutoff_u,
        acs_enabled=acs_enabled,
        effective_path=effective_path,
        gdr_write_enabled=gdr_write,
        gdr_read_enabled=gdr_read,
        transport_summary=summary,
    )


# ---------------------------------------------------------------------------
# 4. PCIe ACS (Access Control Services) Audit & Remediation Helper
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AcsPortStatus:
    bdf: str
    acs_ctl_line: str
    has_blocking_bits: bool
    blocking_flags: Tuple[str, ...]
    setpci_fix_cmd: str


def parse_lspci_acs_output(lspci_map: Dict[str, str]) -> List[AcsPortStatus]:
    """Inspect PCIe bridge BDFs and their ACSCtl lines for P2P-blocking flags.

    Blocking flags when '+' (enabled):
      SrcValid+, TransBlk+, ReqRedir+, CmpltRedir+, UpFwd+
    Remediation command:
      setpci -s <bdf> ECAP_ACS+0x6.w=0000
    """
    monitored = ("SrcValid+", "TransBlk+", "ReqRedir+", "CmpltRedir+", "UpFwd+")
    results: List[AcsPortStatus] = []
    for bdf, line in lspci_map.items():
        active = tuple(flag for flag in monitored if flag in line)
        results.append(
            AcsPortStatus(
                bdf=bdf,
                acs_ctl_line=line.strip(),
                has_blocking_bits=len(active) > 0,
                blocking_flags=active,
                setpci_fix_cmd=f"setpci -s {bdf} ECAP_ACS+0x6.w=0000",
            )
        )
    return results


# ---------------------------------------------------------------------------
# 5. GPUDirect Storage (GDS): cuFile Lifecycle, gdsio Table 5-1, & Pipelines
# ---------------------------------------------------------------------------

CUFILE_EXPECTED_LIFECYCLE: Tuple[str, ...] = (
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


@dataclass(frozen=True)
class GdsBenchmarkResult:
    mode_flag: str            # "-x 2" (Storage->CPU->GPU) or "-x 0" (GDS Storage->GPU)
    path_description: str
    throughput_gb_s: float
    avg_latency_ms: float
    throughput_gain_pct: float
    latency_reduction_pct: float
    time_for_dataset_s: float


def simulate_gdsio_benchmark(
    dataset_size_gb: float = 10.0,
    workers: int = 4,
    io_size_kb: int = 1024,
    cpu_staged_gb_s: float = 8.0,
    cpu_staged_lat_ms: float = 1.25,
    gds_direct_gb_s: float = 9.6,
    gds_direct_lat_ms: float = 1.00,
) -> Tuple[GdsBenchmarkResult, GdsBenchmarkResult]:
    """Model NVIDIA gdsio Table 5-1 benchmark comparing -x 2 (CPU staged) vs -x 0 (GDS).

    Default values match AI Systems Performance Engineering Ch. 5 Table 5-1:
      - Before (-x 2, Storage -> CPU -> GPU): 8.0 GB/s, 1.25 ms average latency
      - After  (-x 0, Storage -> GPU via GDS): 9.6 GB/s (+20%), 1.00 ms (-20%)
    """
    tp_gain_pct = ((gds_direct_gb_s - cpu_staged_gb_s) / cpu_staged_gb_s) * 100.0
    lat_red_pct = ((cpu_staged_lat_ms - gds_direct_lat_ms) / cpu_staged_lat_ms) * 100.0

    before = GdsBenchmarkResult(
        mode_flag="-x 2",
        path_description="Storage -> CPU Pinned Memory -> GPU (without GDS)",
        throughput_gb_s=round(cpu_staged_gb_s, 2),
        avg_latency_ms=round(cpu_staged_lat_ms, 2),
        throughput_gain_pct=0.0,
        latency_reduction_pct=0.0,
        time_for_dataset_s=round(dataset_size_gb / cpu_staged_gb_s, 4),
    )
    after = GdsBenchmarkResult(
        mode_flag="-x 0",
        path_description="Storage -> GPU HBM Direct via cuFile/nvidia-fs (with GDS)",
        throughput_gb_s=round(gds_direct_gb_s, 2),
        avg_latency_ms=round(gds_direct_lat_ms, 2),
        throughput_gain_pct=round(tp_gain_pct, 2),
        latency_reduction_pct=round(lat_red_pct, 2),
        time_for_dataset_s=round(dataset_size_gb / gds_direct_gb_s, 4),
    )
    return before, after


@dataclass(frozen=True)
class CufileConfigAudit:
    is_strict_zero_copy_test: bool
    poll_mode_effective_for_large_io: bool
    max_pinned_gpu_mem_gib: float
    warnings: Tuple[str, ...]


def audit_cufile_json(
    use_poll_mode: bool,
    poll_mode_max_size_kb: int,
    max_device_pinned_mem_size_kb: int,
    allow_compat_mode: bool,
    workload_io_size_kb: int = 1024,
) -> CufileConfigAudit:
    """Validate /etc/cufile.json properties for AI training/checkpoint I/O."""
    warnings: List[str] = []
    if allow_compat_mode:
        warnings.append(
            "allow_compat_mode=true permits silent POSIX host-staging fallback; "
            "set allow_compat_mode=false during GDS validation."
        )
    poll_effective = use_poll_mode and (workload_io_size_kb <= poll_mode_max_size_kb)
    if use_poll_mode and workload_io_size_kb > poll_mode_max_size_kb:
        warnings.append(
            f"use_poll_mode=true only polls I/Os <= {poll_mode_max_size_kb} KB; "
            f"workload I/O size {workload_io_size_kb} KB will still use interrupts."
        )
    max_gib = max_device_pinned_mem_size_kb / (1024.0 * 1024.0)
    return CufileConfigAudit(
        is_strict_zero_copy_test=not allow_compat_mode,
        poll_mode_effective_for_large_io=poll_effective,
        max_pinned_gpu_mem_gib=round(max_gib, 2),
        warnings=tuple(warnings),
    )


@dataclass(frozen=True)
class StoragePipelineSizing:
    checkpoint_size_tb: float
    target_window_s: float
    required_write_bw_gb_s: float
    min_400g_links_needed: int
    raw_file_count: int
    tar_shard_count: int
    metadata_stat_reduction_factor: int


def size_checkpoint_and_metadata(
    checkpoint_size_tb: float = 2.0,
    target_window_s: float = 60.0,
    total_small_files: int = 50_000,
    files_per_webdataset_tar: int = 50_000,
) -> StoragePipelineSizing:
    """Compute checkpoint write burst bandwidth and WebDataset metadata reduction.

    - 2 TB (2,000 GB decimal) in 60 s -> 33.33 GB/s minimum sustained write bandwidth.
    - Each 400 Gbps storage link provides 50 GB/s line rate.
    - Packing 50,000 small 20 KB files into 1 GB WebDataset tar shards reduces
      MDS stat()/open() syscalls by 50,000x.
    """
    checkpoint_gb = checkpoint_size_tb * 1000.0
    bw_gb_s = checkpoint_gb / target_window_s
    links_400g = max(1, int((bw_gb_s + 49.9999) // 50.0))
    tar_shards = max(1, total_small_files // files_per_webdataset_tar)
    reduction = total_small_files // tar_shards
    return StoragePipelineSizing(
        checkpoint_size_tb=checkpoint_size_tb,
        target_window_s=target_window_s,
        required_write_bw_gb_s=round(bw_gb_s, 2),
        min_400g_links_needed=links_400g,
        raw_file_count=total_small_files,
        tar_shard_count=tar_shards,
        metadata_stat_reduction_factor=reduction,
    )


if __name__ == "__main__":
    cmp_res = compare_bounce_buffer_vs_gdr()
    print(
        f"[GDR vs Staged] Staged: {cmp_res.staged_effective_gb_s} GB/s "
        f"({cmp_res.staged_pcie_hops_per_node} PCIe hops/node) | "
        f"GDR: {cmp_res.gdr_effective_gb_s} GB/s "
        f"({cmp_res.gdr_pcie_hops_per_node} PCIe hop/node, {cmp_res.speedup_factor}x)"
    )
    b_res, a_res = simulate_gdsio_benchmark()
    print(
        f"[gdsio Table 5-1] {b_res.mode_flag}: {b_res.throughput_gb_s} GB/s @ {b_res.avg_latency_ms} ms -> "
        f"{a_res.mode_flag}: {a_res.throughput_gb_s} GB/s (+{a_res.throughput_gain_pct}%) @ "
        f"{a_res.avg_latency_ms} ms (-{a_res.latency_reduction_pct}%)"
    )
