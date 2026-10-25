#!/usr/bin/env python3
"""Part 9, Chapter 9.9: Compute, storage, in-band and out-of-band networks in a SuperPOD.

Models the 5 network segments across 4 physical fabrics, Rail-Optimized (ROD) vs
Rail-Only vs Rail-Unified (RUD) designs, ToR/MoR/EoR leaf placement cable spans,
3-stage vs 5-stage Clos port/GPU scaling, RoCEv2 UDP 4791 load-balancing & DCQCN
congestion control, and In-Band / OOB / Customer Edge routing rules.

Sources:
- NVIDIA DGX SuperPOD Reference Architecture Featuring DGX GB300 Systems
  (superpod-gb300-ra, pp. 13-28)
- Data Center Best Practices with DGX B200 (superpod-b200-dc, pp. 5, 19-23)
- AI Data Center Network Design and Technologies, Chapters 2 and 3
"""

from __future__ import annotations

from typing import Dict, List


def compare_leaf_placement_strategy(placement: str) -> Dict[str, object]:
    """Compare Top-of-Rack (ToR), Middle-of-Row (MoR), and End-of-Row (EoR) leaf placement.

    Source: AI Data Center Network Design and Technologies Chapter 3 (Table 3-1, lines 130-184):
    In an 8-server-rack Rail-Optimized row (32 servers = 256 GPUs):
    - "ToR": Less rack space, More power/cooling per compute rack, max cable span = 8 racks.
    - "MoR": More rack space (switches in middle 2 racks), Less power/cooling per compute rack,
      no intra-rack switch cabling, shortest max cable span = 6 racks.
    - "EoR": More rack space (switches in end 2 racks), Less power/cooling per compute rack,
      no intra-rack switch cabling, longest max cable span = 10 racks.
    """
    table: Dict[str, Dict[str, object]] = {
        "ToR": {
            "rack_space_requirement": "Less",
            "power_cooling_per_compute_rack": "More",
            "cabling_within_compute_rack": True,
            "max_cable_span_racks": 8,
            "ideal_for_rud_with_dac": True,
        },
        "MoR": {
            "rack_space_requirement": "More",
            "power_cooling_per_compute_rack": "Less",
            "cabling_within_compute_rack": False,
            "max_cable_span_racks": 6,
            "ideal_for_rud_with_dac": False,
        },
        "EoR": {
            "rack_space_requirement": "More",
            "power_cooling_per_compute_rack": "Less",
            "cabling_within_compute_rack": False,
            "max_cable_span_racks": 10,
            "ideal_for_rud_with_dac": False,
        },
    }
    if placement not in table:
        raise ValueError(f"Unknown leaf placement: {placement}")
    return table[placement]


def calculate_clos_fabric_scale(
    switch_radix_ports: int,
    stages: int = 3,
    rows_or_su_count: int = 8,
    super_spine_oversubscription: int = 1,
) -> Dict[str, int]:
    """Calculate leaf, spine, super-spine, and max GPU counts for 3-stage and 5-stage Clos fabrics.

    Sources:
    - AI Data Center Network Design and Technologies Chapter 3 (Figures 3-9, 3-11, 3-12):
      - 3-stage (leaf-spine) Clos with 64x400G switches (32 down + 32 up):
        1 row = 256 GPUs (8 leaves, 4 spines); 2 rows = 512 GPUs (16 leaves, 8 spines);
        max 8 rows = 2,048 GPUs (64 leaves, 32 spines).
      - 5-stage (leaf-spine-super_spine) Clos with 64x400G switches:
        1 block = 4 rows = 1,024 GPUs (32 leaves, 32 spines, 1,024 super-spine facing ports).
        With 32 fixed 64-port super-spine switches (2,048 super-spine ports):
        2 blocks (2,048 GPUs) = 1:1; 4 blocks (4,096 GPUs) = 2:1; 6 blocks (6,144 GPUs) = 3:1;
        8 blocks (8,192 GPUs) = 4:1; up to 7:1 (14,336 GPUs).
    - superpod-gb300-ra Table 3 (p. 21):
      - 2-layer (3-stage Clos) with 144-port Q3400-RD switches (72 down + 72 up, 8 leaves/SU):
        scales up to 16 SUs = 9,216 GPUs (128 leaves, 72 spines).
    """
    if switch_radix_ports not in (64, 144):
        raise ValueError("Supported switch_radix_ports are 64 or 144.")
    if stages not in (3, 5):
        raise ValueError("Supported Clos stages are 3 (leaf-spine) or 5 (leaf-spine-superspine).")
    if rows_or_su_count <= 0 or super_spine_oversubscription <= 0:
        raise ValueError("rows_or_su_count and super_spine_oversubscription must be >= 1.")

    half_radix = switch_radix_ports // 2
    gpus_per_row_or_su = 8 * half_radix  # 256 GPUs for 64-port; 576 GPUs for 144-port

    if stages == 3:
        total_gpus = rows_or_su_count * gpus_per_row_or_su
        total_leaves = rows_or_su_count * 8
        # Total spine uplink ports = total_gpus; each spine provides switch_radix_ports (or 128/72 in GB300 Table 3)
        if switch_radix_ports == 64:
            total_spines = (total_gpus + switch_radix_ports - 1) // switch_radix_ports
            max_nonblocking_gpus = 64 * half_radix  # 2,048 GPUs
        else:
            # Matches superpod-gb300-ra Table 3: 2 SU->8, 4 SU->18, 8 SU->36, 16 SU->72
            total_spines = 4 if rows_or_su_count == 1 else (8 if rows_or_su_count == 2 else (rows_or_su_count * 9) // 2)
            max_nonblocking_gpus = 16 * gpus_per_row_or_su  # 9,216 GPUs
        return {
            "stages": 3,
            "switch_radix_ports": switch_radix_ports,
            "total_gpus": total_gpus,
            "leaf_switches": total_leaves,
            "spine_switches": total_spines,
            "super_spine_switches": 0,
            "max_nonblocking_3stage_gpus": max_nonblocking_gpus,
        }

    # 5-stage Clos (Figure 3-11 & 3-12 for 64-port switches: 1 block = 4 rows = 1,024 GPUs, 32 leaves, 32 spines)
    blocks = super_spine_oversubscription * 2  # 2 blocks at 1:1 (2,048 GPUs), 4 blocks at 2:1 (4,096 GPUs), etc.
    total_gpus = blocks * 1024
    total_leaves = blocks * 32
    total_spines = blocks * 32
    super_spines = 32  # Fixed 32 x 64-port super-spines = 2,048 ports (Fig. 3-12)
    return {
        "stages": 5,
        "switch_radix_ports": switch_radix_ports,
        "blocks": blocks,
        "oversubscription_ratio": super_spine_oversubscription,
        "total_gpus": total_gpus,
        "leaf_switches": total_leaves,
        "spine_switches": total_spines,
        "super_spine_switches": super_spines,
        "super_spine_ports": super_spines * switch_radix_ports,
    }


def evaluate_rocev2_load_balancing_and_dcqcn(config: Dict[str, object]) -> Dict[str, object]:
    """Audit RoCEv2 transport, load balancing (SLB/DLB/GLB/sDLB), and DCQCN settings.

    Sources:
    - AI Data Center Network Design and Technologies Chapter 2 (lines 34-98):
      - RoCEv2 uses UDP destination port 4791 encapsulating the IB Base Transport Header (BTH).
      - Low entropy + elephant flows cause collisions under Static Load Balancing (SLB 5-tuple hash).
      - Proactive load balancing: DLB (local link/queue), GLB (Next-to-Next-Hop NNH), or sDLB (BTH opcode spraying).
      - Reactive congestion control: DCQCN combining ECN (congested switch marks IP ECN bits = '11',
        receiver sends CNP with IP ECN = '01' back to source) and link-level PFC pause frames.
    - superpod-gb300-ra p. 24:
      - Storage RoCEv2 port (400 Gbps) must be dedicated and unbonded from the In-Band Management port.
    """
    issues: List[str] = []

    if int(config.get("rocev2_udp_dest_port", 0)) != 4791:
        issues.append("wrong_rocev2_udp_port (RoCEv2 standard UDP destination port is 4791)")

    lb_mode = str(config.get("load_balancing_mode", "SLB"))
    if lb_mode == "SLB" and bool(config.get("has_low_entropy_elephant_flows", True)):
        issues.append("slb_elephant_flow_collision_risk (use DLB, GLB, or sDLB instead of static 5-tuple SLB)")

    if not bool(config.get("dcqcn_ecn_enabled", False)) or not bool(config.get("pfc_enabled", False)):
        issues.append("missing_lossless_dcqcn (RoCEv2 requires both ECN marking/CNP and PFC pause flow control)")

    if str(config.get("congested_switch_ecn_bits", "")) != "11":
        issues.append("invalid_ecn_congestion_bits (congested switch must mark ECN bits as '11' CE)")

    if bool(config.get("roce_bonded_with_inband", False)):
        issues.append("bonded_roce_inband_violation (Storage RoCEv2 must use a dedicated unbonded 400G port)")

    return {
        "lossless_and_balanced": len(issues) == 0,
        "issues": issues,
    }


def classify_superpod_network_plane(traffic_type: str) -> Dict[str, str]:
    """Map a SuperPOD traffic flow to its logical segment, physical fabric, and switch model.

    Source: superpod-gb300-ra pp. 13, 18-28.
    """
    mapping: Dict[str, Dict[str, str]] = {
        "intra_rack_gpu_p2p": {
            "logical_segment": "NVLink 5",
            "physical_fabric": "Multi-node NVLink Fabric (MN-NVL)",
            "switch_hardware": "NVLink Switch Tray (18 ASICs/rack)",
            "fabric_manager": "NMX-M",
        },
        "inter_rack_nccl_collectives": {
            "logical_segment": "Compute Network",
            "physical_fabric": "Compute InfiniBand Fabric",
            "switch_hardware": "Quantum-X800 Q3400-RD (800G) / Quantum-2 QM9700 (400G)",
            "fabric_manager": "UFM Enterprise",
        },
        "parallel_filesystem_rocev2": {
            "logical_segment": "Storage Network",
            "physical_fabric": "Storage and In-band Ethernet Fabric",
            "switch_hardware": "Spectrum-4 SN5600D (Storage & Compute Leaves)",
            "host_interface": "BlueField-3 Port 1 (400 Gbps Dedicated Unbonded)",
        },
        "slurm_k8s_nfs_home_and_ebgp_uplink": {
            "logical_segment": "In-Band Management Network",
            "physical_fabric": "Storage and In-band Ethernet Fabric",
            "switch_hardware": "Spectrum-4 SN5600D (Compute & Management Leaves)",
            "host_interface": "BlueField-3 Port 2 (>=200 Gbps Dedicated)",
        },
        "bmc_ipmi_redfish_and_nvos_come": {
            "logical_segment": "Out-of-Band Management Network",
            "physical_fabric": "Out-of-Band network",
            "switch_hardware": "SN2201 (48x 1GbE Copper) + OOB Spines (VXLAN Rollup)",
            "host_interface": "1 GbE RJ45 BMC / COMe Ports",
        },
    }
    if traffic_type not in mapping:
        raise KeyError(f"Unknown traffic_type: {traffic_type}")
    return mapping[traffic_type]
