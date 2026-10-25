"""Chapter 11.11 — NVIDIA Network Operator.

Deterministic models for:
1. NVIDIA Network Operator (`NicClusterPolicy`, `26.1.1`) operand state machine
   (`ofedDriver`, `nvPeerDriver`, `rdmaSharedDevicePlugin` vendor `15b3`,
   `sriovNetworkOperator`, `secondaryNetwork` Multus/CNI/Whereabouts).
2. InfiniBand vs RoCEv2 packet header overhead & `ibstat` / `ib_write_bw`
   validator (`LRH 8B`, `GRH 40B`, `BTH 12B`, `ICRC 4B`, `VCRC 2B`; RoCEv2 UDP
   port `4791`, `PFC` Priority `3` / DSCP `24`/`26`, `ECN` `150..1500`, `50ms`
   PFC watchdog; `ib_write_bw` `200` Gbps HDR `23450.5 MB/s` vs `25 GB/s` line rate).
3. GPUDirect Storage (`GDS`) & AI Storage Hierarchy model (`Tier 0` HBM `40GB`..`192GB`,
   `Tier 1` `8x 3.84TB` NVMe RAID 0, `Tier 2` PFS WEKA/Lustre, `Tier 3` Object;
   `/etc/cufile.json` `max_device_pinned_mem_size_kb: 33554432`, `poll_mode_max_size_kb: 4`,
   `/dev/shm` `400Gi`, and `WebDataset` `50,000`-to-`1` `stat()` reduction).
4. Fabric & Storage Incident Triage Engine (Microburst ECN vs PFC deadlock, IB
   Subnet Manager heavy sweeps, cascading `D`-state `rpc_wait_bit_killable` > `120s`,
   and MDS `85.12%` `stat` saturation).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class NetworkOperatorConfig:
    """Helm / `NicClusterPolicy` configuration for the NVIDIA Network Operator."""

    operator_version: str = "26.1.1"
    nfd_enabled: bool = True
    sriov_network_operator_enabled: bool = True
    ofed_driver_deploy: bool = True
    nv_peer_driver_deploy: bool = True
    rdma_shared_dp_deploy: bool = True
    rdma_shared_resource_name: str = "rdma_shared_device_a"
    nic_vendor_id: str = "15b3"
    multus_deploy: bool = True


def reconcile_network_operator_operands(
    cfg: NetworkOperatorConfig,
    node_has_mellanox_15b3: bool,
    host_gpu_driver_ready: bool,
) -> Dict[str, object]:
    """Reconcile NVIDIA Network Operator operands on a node."""
    if not node_has_mellanox_15b3:
        return {
            "operands_scheduled": [],
            "gpudirect_rdma_ready": False,
            "exposed_resource": None,
        }
    operands: List[str] = []
    if cfg.ofed_driver_deploy:
        operands.append("mofed-driver-daemonset")
    if cfg.nv_peer_driver_deploy and host_gpu_driver_ready:
        operands.append("nv-peer-mem-daemonset")
    if cfg.rdma_shared_dp_deploy:
        operands.append("rdma-shared-dp-daemonset")
    if cfg.sriov_network_operator_enabled:
        operands.append("sriov-device-plugin-daemonset")
    if cfg.multus_deploy:
        operands.append("kube-multus-ds")

    gdr_ready = (
        cfg.ofed_driver_deploy
        and cfg.nv_peer_driver_deploy
        and host_gpu_driver_ready
    )
    return {
        "operands_scheduled": operands,
        "gpudirect_rdma_ready": gdr_ready,
        "exposed_resource": f"rdma/{cfg.rdma_shared_resource_name}",
    }


def analyze_ib_vs_roce_port_and_headers(
    link_layer: str = "InfiniBand",
    rate_gbps: int = 200,
    base_lid: int = 32,
    sm_lid: int = 1,
    include_grh: bool = False,
) -> Dict[str, object]:
    """Validate `ibstat` fields and packet header bytes (`Volume 06` §3.1, §3.2, §5.1)."""
    # InfiniBand headers: LRH (8B) + optional GRH (40B) + BTH (12B) + ICRC (4B) + VCRC (2B)
    ib_header_bytes = 8 + (40 if include_grh else 0) + 12 + 4 + 2
    line_rate_gb_per_sec = rate_gbps / 8.0

    if link_layer == "InfiniBand":
        sm_healthy = base_lid > 0 and sm_lid > 0
        control_plane = "Centralized Subnet Manager (OpenSM / UFM)"
    else:
        sm_healthy = base_lid == 0 and sm_lid == 0
        control_plane = "Distributed IP/BGP/ECMP (UDP port 4791)"

    return {
        "link_layer": link_layer,
        "rate_gbps": rate_gbps,
        "line_rate_gb_per_sec": round(line_rate_gb_per_sec, 2),
        "ib_transport_framing_bytes": ib_header_bytes,
        "rocev2_udp_port": 4791,
        "cnp_bth_opcode_hex": "0x81",
        "lid_and_sm_valid": sm_healthy,
        "control_plane": control_plane,
    }


def evaluate_gds_and_storage_tiers(
    dgx_nvme_drives: int = 8,
    dgx_nvme_size_tb: float = 3.84,
    max_device_pinned_mem_kb: int = 33554432,
    poll_mode_max_size_kb: int = 4,
    raw_small_files_count: int = 14_000_000,
    images_per_webdataset_tar: int = 50_000,
) -> Dict[str, float]:
    """Compute Tier 1 NVMe capacity, GDS `/etc/cufile.json` limits, and WebDataset stat reduction."""
    tier1_raw_tb = round(dgx_nvme_drives * dgx_nvme_size_tb, 2)
    max_pinned_gib = round(max_device_pinned_mem_kb / (1024.0 * 1024.0), 2)
    tar_files_needed = raw_small_files_count // images_per_webdataset_tar
    stat_reduction_factor = float(images_per_webdataset_tar)
    return {
        "tier1_nvme_total_tb": tier1_raw_tb,
        "gds_max_pinned_gib": max_pinned_gib,
        "gds_poll_mode_max_kb": float(poll_mode_max_size_kb),
        "webdataset_tar_count": float(tar_files_needed),
        "stat_reduction_factor": stat_reduction_factor,
    }


def diagnose_fabric_or_storage_incident(
    pfc_pause_storm_zero_tx: bool = False,
    pfc_firing_low_ecn_marks: bool = False,
    sm_heavy_sweeps_flapping: bool = False,
    d_state_rpc_wait_120s: bool = False,
    mds_stat_pct: float = 0.0,
) -> Dict[str, str]:
    """Diagnose the 5 production network/storage scenarios from Volume 06 Ch 1 & Ch 3."""
    if pfc_pause_storm_zero_tx:
        return {
            "incident": "pfc_circular_buffer_deadlock",
            "action": "Enforce loop-free Clos topology and enable PFC Watchdog (e.g. 50ms drop timer)",
        }
    if pfc_firing_low_ecn_marks:
        return {
            "incident": "roce_microburst_ecn_threshold_too_high",
            "action": "Lower switch ECN minimum-absolute threshold (e.g. 150 KB) so CNPs (0x81) trigger DCQCN before PFC pauses",
        }
    if sm_heavy_sweeps_flapping:
        return {
            "incident": "ib_subnet_manager_heavy_sweep_storm",
            "action": "Run ibdiagnet -c 1000, inspect ibdiagnet2.pm, and disable flapping port/optic",
        }
    if d_state_rpc_wait_120s:
        return {
            "incident": "cascading_d_state_storage_hang",
            "action": "Check ibstat / symbol_error_counter > 1000, hard-reset wedged node via IPMI if kernel locked, use bounded timeouts on read mounts",
        }
    if mds_stat_pct >= 80.0:
        return {
            "incident": "mds_small_file_stat_saturation",
            "action": "Stop raw 20KB PNG job (85.12% time in stat); stage to Tier 1 NVMe or pack 50,000 images into 1GB WebDataset tar shards",
        }
    return {
        "incident": "healthy",
        "action": "Fabric and storage pipelines operating normally",
    }
