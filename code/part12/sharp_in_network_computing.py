"""Core models and verification math for Chapter 12.20: SHARP and In-Network Computing.

Covers:
1. Ring AllReduce / ReduceScatter / AllGather traffic volume (2*(N-1)/N * S and (N-1)/N * S)
   versus InfiniBand SHARP (CollNet) and NVLink SHARP (NVLS) in-network reduction (2 * S
   total per endpoint or S / N per endpoint in ReduceScatter/AllGather, giving a (N - 1)x
   fabric bandwidth reduction factor).
2. Two-level hierarchical NVLS (intra-node / intra-rack NVSwitch) + InfiniBand CollNet/SHARP
   (inter-node / inter-rack Quantum switch) reduction volume, step complexity, and wall-time math,
   plus overlapped NVLS AllGather + ReduceScatter (~1/2 phase wall time).
3. SHARP hardware generations (SHARPv1 Switch-IB 2, SHARPv2 Quantum-1 HDR, SHARPv3 Quantum-2 NDR,
   SHARPv4 Quantum-X800 XDR Q3400-RD, and NVSwitch Gen 3 / Gen 4 NVLS), supported data types
   (FP16, BF16, FP32, FP64, INT32/INT64), and DGX SuperPOD GB300 scale-out switch counts.
4. SHARP Aggregation Manager (sharp_am), daemon (sharp_daemons), UFM integration, and Aggregation
   Node (AN) tree / OST resource quota allocation, exhaustion, and fallback checks.
5. Floating-point non-associativity in IEEE-754 reductions: Ring rank-dependent summation order
   variance versus deterministic SHARP Aggregation Node (AN) fixed tree reduction order.
6. NCCL / HPC-X OpenMPI SHARP and NVLS configuration validation (NCCL_COLLNET_ENABLE,
   NCCL_NVLS_ENABLE, NCCL_SHARP_DISABLE, HCOLL_ENABLE_SHARP, persistent user buffers via
   ncclCommRegister, and UEC In-Network Collectives INC vs xCCL comparison).
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class CollectiveVolumeComparison:
    """Comparison of Ring vs In-Network SHARP / NVLS collective data movement."""

    num_ranks: int
    tensor_bytes: int
    # ReduceScatter per-rank received bytes
    ring_reduce_scatter_rx_bytes: float
    sharp_reduce_scatter_rx_bytes: float
    reduce_scatter_volume_ratio: float  # Ring / SHARP = (N - 1)
    # AllGather per-rank sent bytes
    ring_all_gather_tx_bytes: float
    nvls_all_gather_tx_bytes: float
    all_gather_volume_ratio: float  # Ring / NVLS = (N - 1)
    # Full AllReduce per-rank total (tx + rx) bytes across the fabric
    ring_allreduce_tx_Plus_rx_bytes: float
    sharp_allreduce_tx_plus_rx_bytes: float
    ring_steps: int
    tree_steps: int
    # Timing estimates (ms)
    ring_allreduce_ms: float
    sharp_allreduce_ms: float
    speedup_factor: float


def compare_ring_vs_sharp_volume(
    num_ranks: int,
    tensor_bytes: int,
    per_rank_link_gb_s: float = 50.0,
    ring_hop_latency_us: float = 2.0,
    sharp_tree_latency_us: float = 3.0,
    sharp_switch_efficiency: float = 1.0,
) -> CollectiveVolumeComparison:
    """Compute exact Ring vs SHARP / NVLS collective traffic volumes and wall times.

    - In Ring ReduceScatter on B bytes across N ranks, each rank receives B * (N - 1) / N bytes
      over (N - 1) hops. With in-network reduction (NVLS or SHARP), the switch aggregates and
      returns only B / N bytes to each rank -> 1 / (N - 1) of Ring receive volume.
    - In Ring AllGather, each rank sends B * (N - 1) / N bytes across (N - 1) hops. With NVLS
      hardware multicast, each rank sends its B / N shard once (B / N bytes) while the switch
      replicates it -> 1 / (N - 1) of Ring send volume.
    - For a full inter-node AllReduce of size S across N nodes:
      * Host-driven Ring transfers 2 * (N - 1) / N * S bytes out of and into each rank (so
        4 * (N - 1) / N * S combined tx+rx bytes, or 2 * (N - 1) / N * S unidirectional per link).
      * Switch-based SHARP tree requires each rank to send S bytes up to the leaf switch once and
        receive the reduced S bytes back down once (1 * S tx + 1 * S rx = 2 * S total unidirectional
        fabric traversal per rank, or S bytes per direction vs 2*(N-1)/N * S per direction in Ring).
    """
    if num_ranks < 2:
        raise ValueError("num_ranks must be >= 2")
    if tensor_bytes <= 0 or per_rank_link_gb_s <= 0:
        raise ValueError("tensor_bytes and per_rank_link_gb_s must be > 0")

    b = float(tensor_bytes)
    n = num_ranks

    ring_rs_rx = b * (n - 1) / n
    sharp_rs_rx = b / n
    rs_ratio = ring_rs_rx / sharp_rs_rx  # exactly (n - 1)

    ring_ag_tx = b * (n - 1) / n
    nvls_ag_tx = b / n
    ag_ratio = ring_ag_tx / nvls_ag_tx  # exactly (n - 1)

    # Unidirectional bottleneck bytes per rank in AllReduce:
    # Ring: 2 * (N - 1) / N * B bytes sent (and received) per rank.
    # SHARP AllReduce: 1 * B bytes sent up the tree and 1 * B bytes received down the tree
    # (1 * B bytes per direction, or 2 * B total tx+rx).
    ring_unidir_bytes = 2.0 * ((n - 1) / n) * b
    sharp_unidir_bytes = 1.0 * b  # 1x B up, 1x B down concurrently on full-duplex link

    ring_steps = 2 * (n - 1)
    tree_steps = 2 * math.ceil(math.log2(n))

    bw_bytes_per_ms = per_rank_link_gb_s * 1e6  # 1 GB/s = 1e9 B/s = 1e6 B/ms
    ring_ms = (ring_unidir_bytes / bw_bytes_per_ms) + (ring_steps * ring_hop_latency_us / 1000.0)
    sharp_ms = (
        (sharp_unidir_bytes / (bw_bytes_per_ms * sharp_switch_efficiency))
        + (tree_steps * sharp_tree_latency_us / 1000.0)
    )
    speedup = ring_ms / sharp_ms

    return CollectiveVolumeComparison(
        num_ranks=n,
        tensor_bytes=tensor_bytes,
        ring_reduce_scatter_rx_bytes=round(ring_rs_rx, 2),
        sharp_reduce_scatter_rx_bytes=round(sharp_rs_rx, 2),
        reduce_scatter_volume_ratio=round(rs_ratio, 4),
        ring_all_gather_tx_bytes=round(ring_ag_tx, 2),
        nvls_all_gather_tx_bytes=round(nvls_ag_tx, 2),
        all_gather_volume_ratio=round(ag_ratio, 4),
        ring_allreduce_tx_Plus_rx_bytes=round(ring_unidir_bytes, 2),
        sharp_allreduce_tx_plus_rx_bytes=round(2.0 * b, 2),
        ring_steps=ring_steps,
        tree_steps=tree_steps,
        ring_allreduce_ms=round(ring_ms, 4),
        sharp_allreduce_ms=round(sharp_ms, 4),
        speedup_factor=round(speedup, 4),
    )


@dataclass(frozen=True)
class OverlappedShardExchangeResult:
    """Wall time for FSDP / sharded training AllGather + ReduceScatter exchange."""

    all_gather_ms: float
    reduce_scatter_ms: float
    serial_total_ms: float
    overlapped_nvls_ms: float
    wall_time_reduction_fraction: float


def compute_overlapped_nvls_exchange(
    all_gather_ms: float,
    reduce_scatter_ms: float,
) -> OverlappedShardExchangeResult:
    """When overlapping an NVLS multicast AllGather with an in-network ReduceScatter,
    effective wall time is max(T_AG, T_RS) instead of T_AG + T_RS (~1/2 phase time when equal).
    """
    if all_gather_ms <= 0 or reduce_scatter_ms <= 0:
        raise ValueError("Phase durations must be > 0")
    serial = all_gather_ms + reduce_scatter_ms
    overlapped = max(all_gather_ms, reduce_scatter_ms)
    reduction = (serial - overlapped) / serial
    return OverlappedShardExchangeResult(
        all_gather_ms=round(all_gather_ms, 4),
        reduce_scatter_ms=round(reduce_scatter_ms, 4),
        serial_total_ms=round(serial, 4),
        overlapped_nvls_ms=round(overlapped, 4),
        wall_time_reduction_fraction=round(reduction, 4),
    )


@dataclass(frozen=True)
class HierarchicalSharpModel:
    """Two-level hierarchical collective model: intra-domain NVLS + inter-domain IB SHARP."""

    num_domains: int
    gpus_per_domain: int
    total_gpus: int
    tensor_bytes: int
    # Flat global ring over all GPUs crossing inter-domain links vs hierarchical NVLS + SHARP
    flat_ring_inter_domain_bytes_per_domain: float
    hier_ring_inter_domain_bytes_per_domain: float
    hier_sharp_inter_domain_bytes_per_domain: float
    intra_domain_nvls_rs_rx_bytes_per_gpu: float
    flat_vs_hier_sharp_wan_reduction: float
    ring_vs_sharp_inter_domain_ratio: float


def compute_hierarchical_nvls_ib_sharp(
    num_domains: int,
    gpus_per_domain: int,
    tensor_bytes: int,
) -> HierarchicalSharpModel:
    """Model a two-tier collective across `num_domains` nodes/racks, each with `gpus_per_domain` GPUs.

    1. Naive non-hierarchical ring across all N = D * G GPUs (poor placement where every step crosses
       domains) or multi-rail cross-domain ring.
    2. Hierarchical Ring (intra-domain NVLink ring + inter-domain IB ring):
       Each domain sends 2 * (D - 1) / D * S bytes across the inter-domain InfiniBand fabric.
    3. Hierarchical NVLS + IB SHARP (CollNet):
       - Stage 1 (Intra-domain NVLS ReduceScatter): NVSwitch reduces G GPUs' tensors so each of the
         G GPUs (or rail NICs) holds a 1/G shard of size S / G, receiving only S / G bytes.
       - Stage 2 (Inter-domain IB SHARP AllReduce): Each domain injects its reduced S bytes (striped
         across its G rail NICs as S / G per rail) into the Quantum switch SHARP tree once, and
         receives the globally reduced S bytes back down once (1.0 * S bytes per direction,
         which is 2 * (D - 1) / D times smaller than a hierarchical inter-domain Ring in unidirectional
         bytes when comparing 2*(D-1)/D*S vs 1*S, or (D - 1)x smaller in ReduceScatter receive volume).
       - Stage 3 (Intra-domain NVLS AllGather multicast): NVSwitch replicates the globally reduced
         shards across the G GPUs in 1 hop.
    """
    if num_domains < 2 or gpus_per_domain < 1:
        raise ValueError("num_domains >= 2 and gpus_per_domain >= 1 required")
    total_gpus = num_domains * gpus_per_domain
    s = float(tensor_bytes)

    # If a naive ring is not topology-grouped and crosses domains on every step:
    flat_inter_bytes = 2.0 * ((total_gpus - 1) / total_gpus) * s * gpus_per_domain
    # Standard hierarchical ring across D domains (unidirectional bytes sent per domain):
    hier_ring_inter = 2.0 * ((num_domains - 1) / num_domains) * s
    # Hierarchical NVLS + IB SHARP (unidirectional bytes sent up the IB tree per domain = 1.0 * S):
    hier_sharp_inter = 1.0 * s
    intra_nvls_rs_rx = s / gpus_per_domain

    return HierarchicalSharpModel(
        num_domains=num_domains,
        gpus_per_domain=gpus_per_domain,
        total_gpus=total_gpus,
        tensor_bytes=tensor_bytes,
        flat_ring_inter_domain_bytes_per_domain=round(flat_inter_bytes, 2),
        hier_ring_inter_domain_bytes_per_domain=round(hier_ring_inter, 2),
        hier_sharp_inter_domain_bytes_per_domain=round(hier_sharp_inter, 2),
        intra_domain_nvls_rs_rx_bytes_per_gpu=round(intra_nvls_rs_rx, 2),
        flat_vs_hier_sharp_wan_reduction=round(flat_inter_bytes / hier_sharp_inter, 4),
        ring_vs_sharp_inter_domain_ratio=round(hier_ring_inter / hier_sharp_inter, 4),
    )


@dataclass(frozen=True)
class SharpHardwareSpec:
    """Hardware specifications for InfiniBand SHARP and NVSwitch NVLS generations."""

    generation: str
    switch_platform: str
    port_rate_gbps: int
    switch_radix_ports: int
    supported_dtypes: Tuple[str, ...]
    supports_Multi_tree_ll: bool
    domain_scope: str


SHARP_HARDWARE_GENERATIONS: Dict[str, SharpHardwareSpec] = {
    "SHARPv1": SharpHardwareSpec(
        generation="SHARPv1",
        switch_platform="Switch-IB 2 (EDR InfiniBand)",
        port_rate_gbps=100,
        switch_radix_ports=36,
        supported_dtypes=("INT32", "INT64", "FP32", "FP64"),
        supports_Multi_tree_ll=False,
        domain_scope="InfiniBand scale-out (single tree, HPC MPI barriers/allreduce)",
    ),
    "SHARPv2": SharpHardwareSpec(
        generation="SHARPv2",
        switch_platform="Quantum-1 QM8700 (HDR InfiniBand)",
        port_rate_gbps=200,
        switch_radix_ports=40,
        supported_dtypes=("FP16", "BF16", "FP32", "FP64", "INT32", "INT64"),
        supports_Multi_tree_ll=True,
        domain_scope="InfiniBand scale-out (streaming aggregation, AI FP16/BF16 CollNet)",
    ),
    "SHARPv3": SharpHardwareSpec(
        generation="SHARPv3",
        switch_platform="Quantum-2 QM9700 (NDR InfiniBand)",
        port_rate_gbps=400,
        switch_radix_ports=64,
        supported_dtypes=("FP16", "BF16", "FP32", "FP64", "INT32", "INT64"),
        supports_Multi_tree_ll=True,
        domain_scope="InfiniBand scale-out (up to 64 concurrent trees/groups, LLT + SAT)",
    ),
    "SHARPv4": SharpHardwareSpec(
        generation="SHARPv4",
        switch_platform="Quantum-X800 Q3400-RD (XDR InfiniBand)",
        port_rate_gbps=800,
        switch_radix_ports=144,
        supported_dtypes=("FP8", "FP16", "BF16", "FP32", "FP64", "INT32", "INT64"),
        supports_Multi_tree_ll=True,
        domain_scope="InfiniBand scale-out (144-port 800G radix, 2-layer up to 16 SUs / 9,216 GPUs)",
    ),
    "NVLS_Gen3": SharpHardwareSpec(
        generation="NVLS (NVSwitch Gen 3)",
        switch_platform="HGX H100 / H200 NVSwitch 3.0",
        port_rate_gbps=3600,  # 900 GB/s bidir (450 GB/s unidir) per GPU
        switch_radix_ports=64,
        supported_dtypes=("FP8", "FP16", "BF16", "FP32", "INT32", "INT64"),
        supports_Multi_tree_ll=True,
        domain_scope="Intra-node (8 GPUs) or NVL256 NVLink Switch domain",
    ),
    "NVLS_Gen4": SharpHardwareSpec(
        generation="NVLS (NVSwitch Gen 4)",
        switch_platform="DGX GB200 / GB300 NVL72 (18 NVSwitch chips / 9 trays)",
        port_rate_gbps=7200,  # 1.8 TB/s bidir (900 GB/s unidir) per GPU over 18 NVLink 5 links
        switch_radix_ports=144,
        supported_dtypes=("FP4", "FP8", "FP16", "BF16", "FP32", "INT32", "INT64"),
        supports_Multi_tree_ll=True,
        domain_scope="Intra-rack NVL72 (72 GPUs, 130 TB/s bisection, 1-hop full crossbar)",
    ),
}


@dataclass(frozen=True)
class GB300SuperPodScaleSpec:
    """DGX GB300 SuperPOD Quantum-X800 Q3400-RD (144-port) 2-layer fabric scale-out table."""

    num_sus: int
    num_racks: int
    num_gpus: int
    ib_leaf_switches_per_su: int
    ib_leaf_switches_total: int
    ib_spine_switches_total: int
    compute_rails: int


GB300_SUPERPOD_SCALE_TABLE: Dict[int, GB300SuperPodScaleSpec] = {
    2: GB300SuperPodScaleSpec(
        num_sus=2,
        num_racks=16,
        num_gpus=1152,
        ib_leaf_switches_per_su=8,
        ib_leaf_switches_total=16,
        ib_spine_switches_total=8,
        compute_rails=4,
    ),
    4: GB300SuperPodScaleSpec(
        num_sus=4,
        num_racks=32,
        num_gpus=2304,
        ib_leaf_switches_per_su=8,
        ib_leaf_switches_total=32,
        ib_spine_switches_total=18,
        compute_rails=4,
    ),
    8: GB300SuperPodScaleSpec(
        num_sus=8,
        num_racks=64,
        num_gpus=4608,
        ib_leaf_switches_per_su=8,
        ib_leaf_switches_total=64,
        ib_spine_switches_total=36,
        compute_rails=4,
    ),
    16: GB300SuperPodScaleSpec(
        num_sus=16,
        num_racks=128,
        num_gpus=9216,
        ib_leaf_switches_per_su=8,
        ib_leaf_switches_total=128,
        ib_spine_switches_total=72,
        compute_rails=4,
    ),
}


@dataclass(frozen=True)
class SharpTreeQuotaDecision:
    """Result of requesting SHARP Aggregation Node (AN) trees and switch buffer slots from sharp_am."""

    job_id: int
    requested_trees: int
    message_size_mb: float
    allocated: bool
    mode: str  # "SHARP_COLLNET" or "HOST_RING_TREE_FALLBACK"
    remaining_trees: int
    reason: str


class SharpAggregationManagerSim:
    """Simulator for `sharp_am` (SHARP Aggregation Manager) tree and switch buffer quota allocation."""

    def __init__(
        self,
        max_concurrent_trees: int = 64,
        max_collective_mb_per_tree: float = 256.0,
        sm_ufm_active: bool = True,
        sharp_daemons_healthy: bool = True,
    ) -> None:
        self.max_concurrent_trees = max_concurrent_trees
        self.max_collective_mb_per_tree = max_collective_mb_per_tree
        self.sm_ufm_active = sm_ufm_active
        self.sharp_daemons_healthy = sharp_daemons_healthy
        self.active_job_trees: Dict[int, int] = {}

    @property
    def used_trees(self) -> int:
        return sum(self.active_job_trees.values())

    @property
    def available_trees(self) -> int:
        return self.max_concurrent_trees - self.used_trees

    def allocate_job_trees(
        self,
        job_id: int,
        requested_trees: int,
        message_size_mb: float,
    ) -> SharpTreeQuotaDecision:
        if not self.sm_ufm_active:
            return SharpTreeQuotaDecision(
                job_id=job_id,
                requested_trees=requested_trees,
                message_size_mb=message_size_mb,
                allocated=False,
                mode="HOST_RING_TREE_FALLBACK",
                remaining_trees=self.available_trees,
                reason="Subnet Manager / UFM sharp_am control plane is inactive",
            )
        if not self.sharp_daemons_healthy:
            return SharpTreeQuotaDecision(
                job_id=job_id,
                requested_trees=requested_trees,
                message_size_mb=message_size_mb,
                allocated=False,
                mode="HOST_RING_TREE_FALLBACK",
                remaining_trees=self.available_trees,
                reason="Compute node sharp_daemons (sharp_d) unreachable or not running",
            )
        if message_size_mb > self.max_collective_mb_per_tree:
            return SharpTreeQuotaDecision(
                job_id=job_id,
                requested_trees=requested_trees,
                message_size_mb=message_size_mb,
                allocated=False,
                mode="HOST_RING_TREE_FALLBACK",
                remaining_trees=self.available_trees,
                reason=(
                    f"Collective size {message_size_mb:.1f} MB exceeds switch AN buffer limit "
                    f"{self.max_collective_mb_per_tree:.1f} MB; falling back to non-SHARP aggregation"
                ),
            )
        if requested_trees > self.available_trees:
            return SharpTreeQuotaDecision(
                job_id=job_id,
                requested_trees=requested_trees,
                message_size_mb=message_size_mb,
                allocated=False,
                mode="HOST_RING_TREE_FALLBACK",
                remaining_trees=self.available_trees,
                reason=(
                    f"SHARP tree quota exhausted: requested {requested_trees}, "
                    f"available {self.available_trees} of {self.max_concurrent_trees}"
                ),
            )
        self.active_job_trees[job_id] = self.active_job_trees.get(job_id, 0) + requested_trees
        return SharpTreeQuotaDecision(
            job_id=job_id,
            requested_trees=requested_trees,
            message_size_mb=message_size_mb,
            allocated=True,
            mode="SHARP_COLLNET",
            remaining_trees=self.available_trees,
            reason="Allocated SHARP Aggregation Node (AN) trees on Quantum switches",
        )

    def release_job_trees(self, job_id: int) -> int:
        return self.active_job_trees.pop(job_id, 0)


def f32(val: float) -> float:
    """Round a Python float to exact IEEE-754 binary32 (FP32) precision."""
    return struct.unpack("<f", struct.pack("<f", float(val)))[0]


@dataclass(frozen=True)
class FloatAssociativityResult:
    """Comparison of Ring rank-rotated FP32 summation versus deterministic SHARP tree reduction."""

    num_ranks: int
    ring_sums_by_start_rank: Tuple[float, ...]
    ring_unique_outputs: int
    ring_max_spread: float
    sharp_tree_sum: float
    sharp_tree_repeatable: bool


def analyze_fp32_reduction_determinism(values: Sequence[float]) -> FloatAssociativityResult:
    """Demonstrate IEEE-754 floating-point non-associativity ((a + b) + c != a + (b + c)).

    - In a multi-chunk or rank-rotated Ring reduction (or dynamic adaptive tree where arrival order
      varies), starting accumulation at different rank offsets changes the parenthesization order
      (e.g., reaching intermediate sums 1000001.25, 10,000,000.0, and 10,000,002.0) and can yield
      bit-different IEEE-754 FP32 results across runs or ranks.
    - In a deterministic binary SHARP Aggregation Node (AN) tree where each switch port pair is
      reduced in a fixed port-indexed tree topology (e.g., leaf pairs 0.0, 1.25, 0.0, and 0.625
      summing to 1.875), repeated executions on identical inputs produce bit-identical FP32 outputs.
    - Across 8 GPUs (800 MB -> 700.0 MB vs 100.0 MB RS, 1,400.0 MB Ring AR), 32 nodes (1,024 MB ->
      992.0 MB vs 32.0 MB RS, 1,984.0 MB Ring AR vs 1,024.0 MB per direction / 2,048.0 MB total tx+rx,
      1.9375x ratio), 72 GPUs (720.0 MB -> 710.0 MB vs 10.0 MB RS, 1,420.0 MB Ring AR), and 16x72
      racks (720.0 MB vs 1,350.0 MB inter-rack Ring, 1.875x ratio), in-network reduction combines
      volume compression with deterministic tree parenthesization.
    """
    n = len(values)
    if n < 2 or (n & (n - 1)) != 0:
        raise ValueError("len(values) must be a power of 2 >= 2")

    f32_vals = [f32(v) for v in values]

    # Ring reduction starting at each rank offset k: (((v[k] + v[k+1]) + v[k+2]) + ...)
    ring_sums: List[float] = []
    for start in range(n):
        acc = f32_vals[start]
        for offset in range(1, n):
            acc = f32(acc + f32_vals[(start + offset) % n])
        ring_sums.append(acc)

    # Fixed binary SHARP Aggregation Node (AN) tree reduction: pairwise bottom-up
    def tree_reduce(level_vals: List[float]) -> float:
        cur = list(level_vals)
        while len(cur) > 1:
            cur = [f32(cur[i] + cur[i + 1]) for i in range(0, len(cur), 2)]
        return cur[0]

    sharp_run_1 = tree_reduce(f32_vals)
    sharp_run_2 = tree_reduce(f32_vals)

    unique_ring = len(set(ring_sums))
    spread = max(ring_sums) - min(ring_sums)

    return FloatAssociativityResult(
        num_ranks=n,
        ring_sums_by_start_rank=tuple(ring_sums),
        ring_unique_outputs=unique_ring,
        ring_max_spread=spread,
        sharp_tree_sum=sharp_run_1,
        sharp_tree_repeatable=(sharp_run_1 == sharp_run_2),
    )


@dataclass(frozen=True)
class SharpRuntimeConfigAudit:
    """Audit result for NCCL + HPC-X SHARP/NVLS environment and user-buffer configuration."""

    ib_sharp_active: bool
    nvls_active: bool
    zero_copy_user_buffer_active: bool
    mpi_hcoll_sharp_active: bool
    selected_inter_node_path: str
    selected_intra_node_path: str
    warnings: Tuple[str, ...]


def validate_sharp_nccl_config(
    env: Dict[str, str],
    fabric_type: str = "infiniband",  # "infiniband" or "spectrum-x-ethernet"
    has_nvswitch_nvls_hw: bool = True,
    has_sharp_plugin_and_am: bool = True,
    peermem_or_dmabuf_loaded: bool = True,
    all_ranks_registered_buffers: bool = True,
    symmetric_buffer_offsets: bool = True,
) -> SharpRuntimeConfigAudit:
    """Validate NCCL and OpenMPI HCOLL environment variables and hardware prerequisites."""
    warnings: List[str] = []

    collnet_enable = env.get("NCCL_COLLNET_ENABLE", "0") == "1"
    sharp_disable = env.get("NCCL_SHARP_DISABLE", "0") == "1"
    nvls_enable = env.get("NCCL_NVLS_ENABLE", "1") != "0"
    hcoll_sharp = env.get("HCOLL_ENABLE_SHARP", "0") == "1"
    p2p_disable = env.get("NCCL_P2P_DISABLE", "0") == "1"

    if p2p_disable:
        warnings.append("NCCL_P2P_DISABLE=1 forces intra-node GPU traffic through host CPU memory")

    # Evaluate InfiniBand SHARP (CollNet)
    ib_sharp_active = False
    if fabric_type != "infiniband":
        if collnet_enable:
            warnings.append(
                f"Fabric '{fabric_type}' does not expose switch-resident SHARP reduction silicon; "
                "falling back to standard RDMA Ring/Tree"
            )
    elif sharp_disable:
        warnings.append("NCCL_SHARP_DISABLE=1 explicitly disables InfiniBand SHARP offload")
    elif not collnet_enable:
        warnings.append("NCCL_COLLNET_ENABLE is not set to 1; InfiniBand SHARP (CollNet) is inactive")
    elif not has_sharp_plugin_and_am:
        warnings.append("Missing NCCL RDMA SHARP plugin or active sharp_am on Subnet Manager / UFM")
    elif not peermem_or_dmabuf_loaded:
        warnings.append("GPUDirect RDMA (nvidia-peermem / dma-buf) not loaded; SHARP requires GDR")
    else:
        ib_sharp_active = True

    # Evaluate NVLink SHARP (NVLS)
    nvls_active = bool(has_nvswitch_nvls_hw and nvls_enable and not p2p_disable)
    if has_nvswitch_nvls_hw and not nvls_enable:
        warnings.append("NCCL_NVLS_ENABLE=0 disables NVSwitch in-network reduction and multicast")

    # Evaluate persistent zero-copy user buffer registration (ncclCommRegister)
    zero_copy_active = bool(all_ranks_registered_buffers and symmetric_buffer_offsets)
    if not all_ranks_registered_buffers:
        warnings.append(
            "ncclCommRegister requires ALL ranks in the communicator to register user buffers; "
            "falling back to internal channel staging buffers"
        )
    elif not symmetric_buffer_offsets:
        warnings.append(
            "Buffer head offsets differ across ranks; symmetric NVLS/SHARP zero-copy disabled"
        )

    inter_path = "CollNet_IB_SHARP" if ib_sharp_active else "RDMA_Ring_Tree"
    intra_path = "NVSwitch_NVLS" if nvls_active else ("Host_Staged_SHM" if p2p_disable else "NVLink_Ring_Tree")
    mpi_sharp = bool(
        fabric_type == "infiniband"
        and hcoll_sharp
        and has_sharp_plugin_and_am
        and not sharp_disable
    )

    return SharpRuntimeConfigAudit(
        ib_sharp_active=ib_sharp_active,
        nvls_active=nvls_active,
        zero_copy_user_buffer_active=zero_copy_active,
        mpi_hcoll_sharp_active=mpi_sharp,
        selected_inter_node_path=inter_path,
        selected_intra_node_path=intra_path,
        warnings=tuple(warnings),
    )


# Ultra Ethernet Consortium (UEC) In-Network Collectives (INC) vs xCCL Table 12-3 reference model
UEC_INC_VS_XCCL_MATRIX: Dict[str, Tuple[str, str]] = {
    "Layer": ("Fabric level (hardware)", "Software library (user space)"),
    "Primary execution": ("Inside network switches (sFEPs)", "On host CPUs/GPUs using standard protocols"),
    "Integration": (
        "Needs Libfabric (fi_collective) and INC switches",
        "Integrates with MPI or AI frameworks; switch is transparent",
    ),
    "Offload capabilities": ("Yes (to the switches)", "When paired with INC / SHARP"),
    "Required infrastructure": (
        "INC-capable switches (sFEPs), INC manager (IM via gRPC OOB), and Libfabric",
        "Standard NICs and the MPI/xCCL stack",
    ),
}
