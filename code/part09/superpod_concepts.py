#!/usr/bin/env python3
"""Part 9, Chapter 9.6: DGX SuperPOD concepts: scalable units, fabrics and tiers.

Models Scalable Unit (SU) sizing across DGX B200 (node-based with UFM displacement)
and DGX GB300 NVL72 (rack-scale with 144-port Q3400-RD Quantum-X800 and SN5600D
switches), the partial-SU fabric rule, Standard vs Enhanced storage performance
tiers, 14-byte/parameter AdamW checkpoint sizing, and collective/TCO economics.

Sources:
- Data Center Best Practices with DGX B200 (superpod-b200-dc, pp. 5, 19, 23)
- NVIDIA DGX SuperPOD Reference Architecture Featuring DGX GB300 Systems
  (superpod-gb300-ra, pp. 1-35, Tables 1-5)
- nvidia-devops Volume 21 Chapters 1-4
"""

from __future__ import annotations

from typing import Dict, List, Tuple

# Exact DGX B200 SuperPOD Cabling & Switch Table from superpod-b200-dc p. 19
B200_SUPERPOD_SU_TABLE: Dict[int, Dict[str, int]] = {
    1: {
        "dgx_b200_nodes": 31,  # 32 minus 1 displaced by UFM appliance
        "gpus": 248,
        "ib_leaf_switches": 8,
        "ib_spine_switches": 4,
        "compute_plus_ufm_cables": 252,
        "spine_leaf_cables": 256,
    },
    2: {
        "dgx_b200_nodes": 63,
        "gpus": 504,
        "ib_leaf_switches": 16,
        "ib_spine_switches": 8,
        "compute_plus_ufm_cables": 508,
        "spine_leaf_cables": 512,
    },
    3: {
        "dgx_b200_nodes": 95,
        "gpus": 760,
        "ib_leaf_switches": 24,
        "ib_spine_switches": 16,
        "compute_plus_ufm_cables": 764,
        "spine_leaf_cables": 768,
    },
    4: {
        "dgx_b200_nodes": 127,
        "gpus": 1016,
        "ib_leaf_switches": 32,
        "ib_spine_switches": 16,
        "compute_plus_ufm_cables": 1020,
        "spine_leaf_cables": 1024,
    },
}

# Exact DGX GB300 SuperPOD Switch Tables from superpod-gb300-ra Table 3 (p. 21) & Table 4 (p. 23)
GB300_SUPERPOD_SU_TABLE: Dict[int, Dict[str, object]] = {
    1: {
        "racks": 8,
        "gpus": 576,
        "tdp_mw": 1.2,
        "ib_leaf_per_su": 8,
        "ib_leaf_total": 8,
        "ib_spine_total": 4,
        "eth_spines": 2,
        "eth_compute_leaves": 4,
        "eth_storage_leaves": 2,
        "max_storage_ports": "32x400GbE",
        "mgmt_leaves_plus_oob_spines": "2+2",
    },
    2: {
        "racks": 16,
        "gpus": 1152,
        "tdp_mw": 2.4,
        "ib_leaf_per_su": 8,
        "ib_leaf_total": 16,
        "ib_spine_total": 8,
        "eth_spines": 4,
        "eth_compute_leaves": 8,
        "eth_storage_leaves": 2,
        "max_storage_ports": "64x400GbE",
        "mgmt_leaves_plus_oob_spines": "2+2",
    },
    4: {
        "racks": 32,
        "gpus": 2304,
        "tdp_mw": 4.8,
        "ib_leaf_per_su": 8,
        "ib_leaf_total": 32,
        "ib_spine_total": 18,
        "eth_spines": 8,
        "eth_compute_leaves": 16,
        "eth_storage_leaves": 2,
        "max_storage_ports": "128x400GbE",
        "mgmt_leaves_plus_oob_spines": "2+2",
    },
    8: {
        "racks": 64,
        "gpus": 4608,
        "tdp_mw": 9.6,
        "ib_leaf_per_su": 8,
        "ib_leaf_total": 64,
        "ib_spine_total": 36,
        "eth_spines": 12,
        "eth_compute_leaves": 32,
        "eth_storage_leaves": 4,
        "max_storage_ports": "256x400GbE",
        "mgmt_leaves_plus_oob_spines": "2+2",
    },
    16: {
        "racks": 128,
        "gpus": 9216,
        "tdp_mw": 19.2,
        "ib_leaf_per_su": 8,
        "ib_leaf_total": 128,
        "ib_spine_total": 72,
        "eth_spines": 24,
        "eth_compute_leaves": 64,
        "eth_storage_leaves": 8,
        "max_storage_ports": "1024x400GbE",
        "mgmt_leaves_plus_oob_spines": "2+2",
    },
}

FIVE_NETWORK_SEGMENTS: Tuple[str, ...] = (
    "NVLink 5",
    "Compute Network",
    "Storage Network",
    "In-Band Management Network",
    "Out-of-Band Management Network",
)

FOUR_PHYSICAL_FABRICS: Tuple[str, ...] = (
    "Multi-node NVLink Fabric (MN-NVL)",
    "Compute InfiniBand Fabric",
    "Storage and In-band Ethernet Fabric",
    "Out-of-Band network",
)


def size_b200_superpod(su_count: int) -> Dict[str, object]:
    """Return node, GPU, switch, cable, and kW specs for a 1-to-4 SU DGX B200 SuperPOD.

    Sources:
    - superpod-b200-dc p. 5: 1 SU = up to 32 DGX B200 systems = 458 kW per SU;
      1 UFM appliance displaces 1 DGX B200 server -> max 127 DGX B200 servers in 4 SUs.
    - superpod-b200-dc p. 19: exact node, GPU, switch, and cable counts for 1..4 SUs.
    """
    if su_count not in B200_SUPERPOD_SU_TABLE:
        raise ValueError(f"DGX B200 SuperPOD table supports 1..4 SUs; got {su_count}")
    row = dict(B200_SUPERPOD_SU_TABLE[su_count])
    row["su_count"] = su_count
    row["nominal_slots"] = su_count * 32
    row["ufm_displaced_nodes"] = 1
    row["estimated_power_kw"] = su_count * 458
    return row


def size_gb300_superpod(su_count: int) -> Dict[str, object]:
    """Return rack, GPU, MW, and IB/Ethernet switch counts for a DGX GB300 SuperPOD.

    Source: superpod-gb300-ra pp. 2, 5, 20-23 (Table 3 & Table 4).
    """
    if su_count not in GB300_SUPERPOD_SU_TABLE:
        raise ValueError(f"DGX GB300 SuperPOD table supports 1, 2, 4, 8, or 16 SUs; got {su_count}")
    row = dict(GB300_SUPERPOD_SU_TABLE[su_count])
    row["su_count"] = su_count
    return row


def size_superpod_storage_tier(su_count: int, tier: str) -> Dict[str, float]:
    """Return aggregate storage read and write targets (GB/s) for a SuperPOD.

    Source: superpod-gb300-ra Table 5 (p. 31, "Guidelines for storage performance"):
    - Standard tier: 90 GB/s read, 45 GB/s write per SU (360 GB/s read, 180 GB/s write for 4 SUs).
    - Enhanced tier: 280 GB/s read, 140 GB/s write per SU (1,120 GB/s read, 560 GB/s write for 4 SUs).
    My inference: linear scaling with `su_count` matches both the 1-SU and 4-SU rows of Table 5.
    """
    if su_count <= 0:
        raise ValueError("su_count must be >= 1.")
    if tier == "Standard":
        read_per_su = 90.0
        write_per_su = 45.0
    elif tier == "Enhanced":
        read_per_su = 280.0
        write_per_su = 140.0
    else:
        raise ValueError(f"Unknown storage tier: {tier}")

    return {
        "su_count": su_count,
        "tier": tier,
        "aggregate_read_gbps": round(read_per_su * su_count, 1),
        "aggregate_write_gbps": round(write_per_su * su_count, 1),
        "read_to_write_ratio": round(read_per_su / write_per_su, 1),
    }


def calculate_adamw_checkpoint_footprint(
    params_billions: float,
    num_gpus: int,
    gpus_per_node: int = 8,
    shared_storage_write_gbps: float = 10.0,
    local_nvme_write_gbps_per_node: float = 15.0,
) -> Dict[str, float]:
    """Calculate mixed-precision AdamW checkpoint footprint and write times.

    Source: nvidia-devops Volume 21 Chapter 4 ("Part 3: Checkpoint Management"):
    - Checkpoint state per parameter = 2 B (BF16 weights) + 4 B (FP32 master weights)
      + 4 B (Adam m) + 4 B (Adam v) = 14 bytes/parameter.
      (Active training memory adds 2 B BF16 gradients = 16 bytes/parameter.)
    - For 70B parameters: 70e9 * 14 B = 980 GB (~1 TB) total checkpoint size.
    - Sharded across 64 GPUs (ZeRO-3 / FSDP): 980 / 64 = 15.31 GB per GPU,
      or 122.5 GB per 8-GPU node.
    """
    if params_billions <= 0 or num_gpus <= 0 or gpus_per_node <= 0:
        raise ValueError("params_billions, num_gpus, and gpus_per_node must be positive.")

    checkpoint_gb = round(params_billions * 14.0, 2)
    training_state_gb = round(params_billions * 16.0, 2)
    per_gpu_shard_gb = round(checkpoint_gb / num_gpus, 2)
    per_node_shard_gb = round(per_gpu_shard_gb * gpus_per_node, 2)

    shared_write_sec = round(checkpoint_gb / shared_storage_write_gbps, 2)
    local_nvme_write_sec = round(per_node_shard_gb / local_nvme_write_gbps_per_node, 2)

    return {
        "checkpoint_total_gb": checkpoint_gb,
        "training_state_total_gb": training_state_gb,
        "per_gpu_shard_gb": per_gpu_shard_gb,
        "per_node_shard_gb": per_node_shard_gb,
        "shared_storage_write_sec": shared_write_sec,
        "local_nvme_stage_sec": local_nvme_write_sec,
    }


def audit_superpod_design_rules(design: Dict[str, object]) -> Dict[str, object]:
    """Validate SuperPOD fabric, cabling, and facility rules from SPB200 and SPGB300.

    Sources:
    - superpod-gb300-ra p. 5: Data center must meet Tier 3 / Rated 3 / Class 3 concurrent maintainability.
    - superpod-gb300-ra p. 18: Partial-SU deployments must still provision full-SU leaf switches
      and leaf-spine cables, leaving unpopulated node ports unused.
    - superpod-gb300-ra p. 24: RoCE storage traffic must use a dedicated 400G port and never share
      a bonded interface with In-Band management traffic.
    - superpod-b200-dc p. 23 FAQ #2 & #5: Never use patch panels or intermediary ToR switches to
      extend InfiniBand cables; never cohabitate unrelated IT equipment in DGX racks or cooling gaps.
    """
    violations: List[str] = []

    if int(design.get("datacenter_tier", 3)) < 3:
        violations.append("datacenter_below_tier3 (requires Tier 3 / Rated 3 concurrent maintainability)")

    if bool(design.get("is_partial_su", False)) and not bool(design.get("full_su_switches_and_isl_provisioned", False)):
        violations.append("partial_su_fabric_underprovisioned (must build full-SU leaf switches and leaf-spine cables)")

    if bool(design.get("roce_storage_bonded_with_inband", False)):
        violations.append("roce_bonded_with_inband (storage RoCEv2 must use dedicated 400G port, not bonded with in-band)")

    if bool(design.get("infiniband_uses_patch_panels", False)):
        violations.append("infiniband_patch_panel_violation (patch panels add attenuation and break IB signal integrity)")

    if bool(design.get("unrelated_it_gear_in_dgx_racks", False)):
        violations.append("unrelated_equipment_cohabitation (DGX SU racks and cooling spaces must not host unrelated IT gear)")

    return {
        "compliant": len(violations) == 0,
        "violations": violations,
    }
