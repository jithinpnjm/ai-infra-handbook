#!/usr/bin/env python3
"""Chapter 10.6 model: GPU Interconnects: PCIe, NVLink, NVSwitch and NVLink-C2C.

Encodes the verifiable interconnect bandwidths, topology path classes,
PCIe link-width downgrade math, NVLink generational specs, NVSwitch 8-GPU
and 72-GPU crossbar geometry, NV-HBI / NVLink-C2C coherence rules, and
peer-access / NUMA placement diagnostics from:
- AI Systems Performance Engineering (ASP) Chapter 2 (pp. 20-42):
  NV-HBI 10 TB/s on-package die-to-die link (Blackwell dual-die MCM),
  NVLink-C2C ~900 GB/s (450 GB/s/dir) cache-coherent Grace-to-GPU link
  (Unified CPU-GPU Memory / Extended GPU Memory EGM) vs PCIe Gen5 x16
  (64 GB/s/dir) and PCIe Gen6 x16 (128 GB/s/dir on B300), non-coherent
  GPU-to-GPU caches over NVLink requiring NCCL or NVSHMEM (PGAS), NVLink 5
  (18 links x 100 GB/s = 1.8 TB/s/GPU, 1-2 us latency), NVSwitch 72-GPU
  crossbar (18 NVSwitch ASICs across 9 switch trays = 129.6 ~ 130 TB/s),
  and NVLink SHARP (NVLS) in-switch reduction offload.
- nvidia-devops Volume 07 Chapters 2-3 & Labs 01-02, Volume 02 Chapter 10 & Lab 04:
  PCIe Gen4/Gen5/Gen6 bandwidths, LnkCap vs LnkSta lane downgrade (Gen5 x16
  64 GB/s -> Gen5 x4 16 GB/s = 4x drop), SLIT NUMA distance (10 local vs 21
  remote = 2.1x), nvidia-smi topo -m path labels (X, NV#, PIX, PXB, PHB,
  NODE, SYS), worked 500 MB AllReduce transfer (0.56 ms on 900 GB/s NVLink
  vs 17.86 ms on 28 GB/s SYS PCIe = 32.1x slower), MIG disabling P2P (CNS),
  NVLink single-lane replay/CRC error degradation (18 links x ~26.56 GB/s/dir
  raw in nvlink --status), and workload placement profiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


class InterconnectError(ValueError):
    """Raised when invalid interconnect parameters are supplied."""


@dataclass(frozen=True)
class NVLinkGenSpec:
    generation: int
    architecture: str
    example_gpu: str
    max_links_per_gpu: int
    per_link_bidirectional_gbps: float
    total_bidirectional_gbps: float


NVLINK_GENERATIONS: Dict[int, NVLinkGenSpec] = {
    1: NVLinkGenSpec(1, "Pascal", "P100", 4, 40.0, 160.0),
    2: NVLinkGenSpec(2, "Volta", "V100", 6, 50.0, 300.0),
    3: NVLinkGenSpec(3, "Ampere", "A100", 12, 50.0, 600.0),
    4: NVLinkGenSpec(4, "Hopper", "H100 / H200", 18, 50.0, 900.0),
    5: NVLinkGenSpec(5, "Blackwell", "B200 / B300", 18, 100.0, 1800.0),
}

PCIE_GEN_PER_LANE_UNIDIRECTIONAL_GBPS: Dict[int, float] = {
    3: 1.0,
    4: 2.0,
    5: 4.0,
    6: 8.0,
}

TOPO_PATH_RANK: Dict[str, int] = {
    "X": 0,
    "NV": 1,
    "PIX": 2,
    "PXB": 3,
    "PHB": 4,
    "NODE": 5,
    "SYS": 6,
}


def calc_pcie_link_bandwidth(
    pcie_gen: int,
    cap_width: int = 16,
    sta_width: int = 16,
) -> Dict[str, object]:
    """Calculate PCIe capability vs negotiated (`LnkSta`) bandwidth per V7 Ch 2, V7 Lab 01 Step 6, and ASP Ch 2 (p. 21).

    Rules:
    - Gen4 x16 = 32 GB/s unidirectional (64 GB/s bidirectional).
    - Gen5 x16 = 64 GB/s unidirectional (128 GB/s bidirectional).
    - Gen6 x16 = 128 GB/s unidirectional (256 GB/s bidirectional).
    - If `sta_width < cap_width` (e.g., `Width x4 (downgraded)` on a `Width x16` slot),
      available bandwidth drops proportionally (`64 GB/s -> 16 GB/s`, a 4x loss).
    """
    if pcie_gen not in PCIE_GEN_PER_LANE_UNIDIRECTIONAL_GBPS:
        raise InterconnectError(f"Unsupported PCIe generation: {pcie_gen}")
    if cap_width <= 0 or sta_width <= 0 or sta_width > cap_width:
        raise InterconnectError("sta_width must be in (0, cap_width]")

    per_lane = PCIE_GEN_PER_LANE_UNIDIRECTIONAL_GBPS[pcie_gen]
    cap_uni = per_lane * cap_width
    sta_uni = per_lane * sta_width
    downgrade_factor = cap_width / sta_width

    return {
        "pcie_gen": pcie_gen,
        "cap_width": cap_width,
        "sta_width": sta_width,
        "cap_unidirectional_gbps": round(cap_uni, 2),
        "cap_bidirectional_gbps": round(cap_uni * 2.0, 2),
        "sta_unidirectional_gbps": round(sta_uni, 2),
        "sta_bidirectional_gbps": round(sta_uni * 2.0, 2),
        "is_downgraded": sta_width < cap_width,
        "bandwidth_loss_factor": round(downgrade_factor, 2),
    }


def compare_peer_transfer_time(
    payload_gb: float,
    fast_bw_gbps: float = 900.0,
    slow_bw_gbps: float = 28.0,
) -> Dict[str, float]:
    """Compare transfer time over a fast direct link (NVLink) vs a weak host path (`SYS` PCIe) per V2 Ch 10 (line 196).

    Worked example in V2 Ch 10:
    - `0.5 GB` (500 MB) gradient buffer over `900 GB/s` NVLink takes `0.5 / 900 = 0.56 ms`.
    - `0.5 GB` over a `SYS` PCIe Gen4 path (`~28 GB/s`) takes `0.5 / 28 = 17.86 ms` (~18 ms),
      which is `32.14x` (>30x) slower.
    """
    if payload_gb <= 0 or fast_bw_gbps <= 0 or slow_bw_gbps <= 0:
        raise InterconnectError("payload_gb, fast_bw_gbps, and slow_bw_gbps must be positive")
    fast_ms = (payload_gb / fast_bw_gbps) * 1000.0
    slow_ms = (payload_gb / slow_bw_gbps) * 1000.0
    return {
        "payload_gb": round(payload_gb, 4),
        "fast_time_ms": round(fast_ms, 2),
        "slow_time_ms": round(slow_ms, 2),
        "slowdown_factor": round(slow_ms / fast_ms, 2),
    }


def evaluate_interconnect_scales() -> Dict[str, Dict[str, object]]:
    """Return the four NVIDIA interconnect tiers from ASP Ch 2 (pp. 20-31) and V7 Ch 2-3.

    1. On-package die-to-die (`NV-HBI`): 10,000 GB/s (10 TB/s) coherent across the two Blackwell dies.
    2. Chip-to-chip (`NVLink-C2C`): 900 GB/s bidirectional (450 GB/s/dir) hardware cache-coherent CPU-to-GPU (EGM).
    3. Scale-up GPU-to-GPU (`NVLink 4` 900 GB/s, `NVLink 5` 1,800 GB/s): Load/Store & PGAS (`NVSHMEM`) address space,
       NOT globally hardware cache-coherent across GPUs (requires NCCL/NVSHMEM synchronization), supports `NVLS` SHARP.
    4. Host I/O bus (`PCIe Gen5 x16`): 64 GB/s unidirectional (128 GB/s bidirectional).
    """
    return {
        "NV_HBI": {
            "scope": "On-package die-to-die (Blackwell dual-die MCM)",
            "bidirectional_gbps": 10000.0,
            "hardware_cache_coherent": True,
            "memory_model": "Single unified CUDA device (192 GB raw / 180 GB usable HBM3e, 126 MB L2)",
        },
        "NVLINK_C2C": {
            "scope": "Superchip CPU-to-GPU (Grace Hopper GH200 / Grace Blackwell GB200 & GB300)",
            "unidirectional_gbps": 450.0,
            "bidirectional_gbps": 900.0,
            "hardware_cache_coherent": True,
            "memory_model": "Unified CPU-GPU Memory / Extended GPU Memory (EGM); LPDDR5X is ~500 GB/s (~10x slower than HBM3e)",
        },
        "NVLINK_5_NVSWITCH": {
            "scope": "Scale-up GPU-to-GPU (8-GPU HGX B200 or 72-GPU NVL72 rack)",
            "per_gpu_bidirectional_gbps": 1800.0,
            "nvl72_aggregate_tbps": 129.6,
            "small_msg_latency_us": 1.5,
            "hardware_cache_coherent": False,
            "in_switch_reduction": "NVLink SHARP (NVLS)",
            "memory_model": "Global P2P / PGAS (NVSHMEM) load/store; non-coherent GPU caches synchronized by NCCL/NVSHMEM",
        },
        "PCIE_GEN5_X16": {
            "scope": "Host peripheral bus (CPU Root Complex / PCIe Switch to GPU, NIC, NVMe)",
            "unidirectional_gbps": 64.0,
            "bidirectional_gbps": 128.0,
            "hardware_cache_coherent": False,
            "memory_model": "DMA / P2P over PCIe switch (PIX/PXB) or host bridge (PHB/NODE/SYS)",
        },
    }


def classify_topo_path_label(label: str) -> Dict[str, object]:
    """Classify an `nvidia-smi topo -m` path label per V7 Ch 2, V7 Lab 01 Step 4, and V2 Ch 10."""
    clean = label.strip().upper()
    if clean == "X":
        return {"label": clean, "tier": "SELF", "rank": 0, "crosses_cpu_root_complex": False, "crosses_numa_socket": False, "preferred_for_tp_or_rdma": True}
    if clean.startswith("NV"):
        links_str = clean[2:]
        if not links_str.isdigit() or int(links_str) <= 0:
            raise InterconnectError(f"Invalid NVLink topo label: {label}")
        return {
            "label": clean,
            "tier": "NVLINK",
            "nvlink_bonded_lanes": int(links_str),
            "rank": 1,
            "crosses_cpu_root_complex": False,
            "crosses_numa_socket": False,
            "preferred_for_tp_or_rdma": True,
        }
    if clean == "PIX":
        return {"label": clean, "tier": "SINGLE_PCIE_BRIDGE", "rank": 2, "crosses_cpu_root_complex": False, "crosses_numa_socket": False, "preferred_for_tp_or_rdma": True}
    if clean == "PXB":
        return {"label": clean, "tier": "MULTI_PCIE_BRIDGE", "rank": 3, "crosses_cpu_root_complex": False, "crosses_numa_socket": False, "preferred_for_tp_or_rdma": True}
    if clean == "PHB":
        return {"label": clean, "tier": "PCIE_HOST_BRIDGE", "rank": 4, "crosses_cpu_root_complex": True, "crosses_numa_socket": False, "preferred_for_tp_or_rdma": False}
    if clean == "NODE":
        return {"label": clean, "tier": "INTRA_NUMA_HOST_BRIDGES", "rank": 5, "crosses_cpu_root_complex": True, "crosses_numa_socket": False, "preferred_for_tp_or_rdma": False}
    if clean == "SYS":
        return {"label": clean, "tier": "CROSS_SOCKET_SMP_UPI_XGMI", "rank": 6, "crosses_cpu_root_complex": True, "crosses_numa_socket": True, "preferred_for_tp_or_rdma": False}
    raise InterconnectError(f"Unknown nvidia-smi topo -m label: {label}")


def audit_interconnect_and_placement(
    workload_profile: str,
    gpu_pair_topo_label: str,
    gpu_to_nic_topo_label: str = "PIX",
    mig_enabled: bool = False,
    p2p_status: str = "OK",
    pcie_cap_width: int = 16,
    pcie_sta_width: int = 16,
    nvlink_inactive_lanes: int = 0,
    nvlink_crc_or_replay_errors: int = 0,
    cpu_numa_matches_gpu: bool = True,
    device_sysfs_numa: int = 0,
) -> Dict[str, object]:
    """Audit GPU interconnect health and topology placement (my inference synthesizing V2 Ch 10/Lab 04 & V7 Ch 2-3/Labs 01-02).

    Profiles (`V2 Lab 04 Step 7-8`):
    - `single_gpu_inference`: requires CPU NUMA locality; does not require a multi-GPU peer group.
    - `multi_gpu_training`: requires strong GPU peer group (`NV#`), P2P enabled (`OK`), 0 degraded NVLink lanes, and CPU NUMA locality.
    - `distributed_training`: adds requirement for local high-speed NIC (`PIX` or `PXB`) and full PCIe link width (`sta_width == cap_width`).
    """
    valid_profiles = {"single_gpu_inference", "multi_gpu_training", "distributed_training"}
    if workload_profile not in valid_profiles:
        raise InterconnectError(f"Unsupported workload_profile: {workload_profile}")

    gpu_path = classify_topo_path_label(gpu_pair_topo_label)
    nic_path = classify_topo_path_label(gpu_to_nic_topo_label)
    findings: List[str] = []

    if pcie_sta_width < pcie_cap_width:
        findings.append(
            f"PCIe link width downgraded: LnkSta Width x{pcie_sta_width} < LnkCap Width x{pcie_cap_width} ({pcie_cap_width // pcie_sta_width}x bandwidth loss)."
        )

    if device_sysfs_numa == -1:
        findings.append(
            "Linux sysfs numa_node is -1 (unknown locality); do not silently assume NUMA node 0 without checking BIOS/PCIe root mapping."
        )

    if not cpu_numa_matches_gpu:
        findings.append(
            "CPU/memory binding is on a remote NUMA socket from the GPU (incurs ~2.1x SLIT distance 21 vs 10 cross-socket UPI/xGMI penalty)."
        )

    if workload_profile in {"multi_gpu_training", "distributed_training"}:
        if mig_enabled or p2p_status.upper() == "CNS":
            findings.append(
                "Peer-to-Peer (P2P) access is disabled (topo -p2p reports CNS / MIG mode enabled); multi-GPU P2P is unsupported across MIG-enabled GPUs."
            )
        if not gpu_path["label"].startswith("NV"):
            findings.append(
                f"Multi-GPU training placed on weak GPU-to-GPU path '{gpu_path['label']}' instead of NVLink (e.g., L40S PCIe or cross-socket SYS pair)."
            )
        if nvlink_inactive_lanes > 0:
            findings.append(
                f"NVLink sub-link degradation: {nvlink_inactive_lanes} lane(s) reporting 0.000 GB/s in nvidia-smi nvlink --status."
            )
        if nvlink_crc_or_replay_errors > 0:
            findings.append(
                f"NVLink physical lane errors detected ({nvlink_crc_or_replay_errors} replay/CRC errors in nvidia-smi nvlink --errorcounters); escalate hardware RMA."
            )

    if workload_profile == "distributed_training":
        if not nic_path["preferred_for_tp_or_rdma"]:
            findings.append(
                f"GPU-to-NIC path is '{nic_path['label']}' (crosses CPU root complex or UPI/xGMI socket link); enable K8s Topology Manager single-numa-node or bind local NIC."
            )

    return {
        "workload_profile": workload_profile,
        "passed": len(findings) == 0,
        "gpu_pair_tier": gpu_path["tier"],
        "gpu_to_nic_tier": nic_path["tier"],
        "findings": findings,
    }
