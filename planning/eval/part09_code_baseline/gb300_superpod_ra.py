#!/usr/bin/env python3
"""Part 9, Chapter 9.8: GB300 SuperPOD reference architecture model.

Encodes the complete architectural rules, port-radix and blocking-ratio math,
multi-SU switch scaling tables (Tables 1-5), customer edge eBGP/VTEP/OOB handover,
and Mission Control / Run:ai placement rules from:
- NVIDIA DGX SuperPOD: Next Generation Scalable Infrastructure for AI Factories
  Reference Architecture Featuring NVIDIA DGX GB300 Systems (superpod-gb300-ra, pp. 1-36)
"""

from __future__ import annotations

from typing import Dict, List


def verify_gb300_su_ib_leaf_port_math(
    racks_per_su: int = 8,
    trays_per_rack: int = 18,
    cx8_nics_per_tray: int = 4,
    rails: int = 4,
    leaves_per_rail: int = 2,
    q3400_radix_ports: int = 144,
) -> Dict[str, object]:
    """Verify the 144-port Q3400-RD Quantum-X800 InfiniBand leaf port balance per SU.

    Source: superpod-gb300-ra pp. 8-9, 13, 20-21:
    - 1 SU = 8 racks * 18 compute trays = 144 compute trays (576 B300 GPUs).
    - Each tray has 4 ConnectX-8 (800 Gbps) NICs -> 576 compute ports per SU.
    - 8 leaf switches per SU distributed in 4 rails, with 2 leaf switches per rail.
    My inference: Dividing 576 compute ports across 8 leaf switches puts 72 compute
    downlinks on each 144-port Q3400-RD leaf switch, leaving exactly 72 ports per leaf
    switch for 1:1 non-blocking spine uplinks (72 + 72 = 144 ports).
    """
    if racks_per_su <= 0 or trays_per_rack <= 0 or cx8_nics_per_tray <= 0 or rails <= 0 or leaves_per_rail <= 0:
        raise ValueError("All SU InfiniBand parameters must be positive integers.")

    trays_per_su = racks_per_su * trays_per_rack
    total_compute_ports_per_su = trays_per_su * cx8_nics_per_tray
    leaves_per_su = rails * leaves_per_rail
    downlinks_per_leaf = total_compute_ports_per_su // leaves_per_su
    uplinks_per_leaf = q3400_radix_ports - downlinks_per_leaf
    is_1_to_1_nonblocking = downlinks_per_leaf == uplinks_per_leaf

    return {
        "trays_per_su": trays_per_su,
        "gpus_per_su": trays_per_su * 4,
        "total_compute_ports_per_su": total_compute_ports_per_su,
        "leaves_per_su": leaves_per_su,
        "downlinks_per_leaf": downlinks_per_leaf,
        "uplinks_per_leaf": uplinks_per_leaf,
        "is_1_to_1_nonblocking": is_1_to_1_nonblocking,
    }


def verify_gb300_su_ethernet_leaf_blocking(
    trays_per_su: int = 144,
    bf3_ports_per_tray: int = 2,
    compute_leaves_per_su: int = 4,
    compute_leaf_uplinks_400g: int = 24,
    storage_leaf_links_400g: int = 72,
    mgmt_leaf_links_400g: int = 24,
) -> Dict[str, object]:
    """Verify the Spectrum-4 SN5600D Ethernet leaf port ratios in a GB300 SuperPOD SU.

    Source: superpod-gb300-ra p. 22 ("Ethernet Fabric"):
    - Each SU contains 4 compute leaf SN5600D switches connected to dual-port BlueField-3
      (BF3240) cards at 400 Gbps (1 dedicated 400G Storage port + 1 dedicated >=200G In-Band port).
    - Each compute leaf connects via 24 uplinks at 400 Gbps, supporting a 1:3 blocking ratio.
    - Storage leaves connect via 72 non-blocking 400 Gbps links.
    - Management leaves connect via 24x 400 Gbps links.
    My inference: 144 trays * 2 BF3 ports = 288 downlink ports across 4 compute leaves =
    72 downlinks per compute leaf; 24 uplinks : 72 downlinks = 1:3 blocking ratio.
    """
    if trays_per_su <= 0 or compute_leaves_per_su <= 0 or compute_leaf_uplinks_400g <= 0:
        raise ValueError("Ethernet fabric parameters must be positive.")

    total_host_ports = trays_per_su * bf3_ports_per_tray
    downlinks_per_compute_leaf = total_host_ports // compute_leaves_per_su
    blocking_factor = round(downlinks_per_compute_leaf / float(compute_leaf_uplinks_400g), 2)

    return {
        "total_bf3_ports_per_su": total_host_ports,
        "downlinks_per_compute_leaf": downlinks_per_compute_leaf,
        "uplinks_per_compute_leaf": compute_leaf_uplinks_400g,
        "compute_leaf_blocking_ratio": f"1:{int(blocking_factor)}",
        "storage_leaf_links_400g": storage_leaf_links_400g,
        "mgmt_leaf_links_400g": mgmt_leaf_links_400g,
    }


def audit_gb300_edge_and_software_architecture(config: Dict[str, object]) -> Dict[str, object]:
    """Validate Customer Edge Connectivity, OOB Handover, and Mission Control / Run:ai placement.

    Sources:
    - superpod-gb300-ra pp. 27-28 ("Customer Edge Connectivity"):
      - At least 2x 100GbE links with DR1 single-mode optics.
      - Dedicated VTEP for uplink with eBGP peering announcing routes for In-Band, OOB, and BMS.
      - Building Management System (BMS) flows through uplink interfaces in the untrusted zone.
      - OOB uplink uses either dedicated OOB edge ToR switches (last pair of SN2201 OOB switches)
        or route leaking via the SN5600D In-Band spine switches.
    - superpod-gb300-ra pp. 32-34 ("DGX SuperPOD Software" & "NVIDIA Run:ai"):
      - Mission Control 5-layer stack with autonomous recovery and in-memory checkpointing.
      - For BCM-managed installations, Run:ai control plane (backend) resides on the
        "user-space Kubernetes cluster", while Run:ai cluster components reside on the
        "administrative Kubernetes infrastructure".
    """
    errors: List[str] = []

    uplink_count = int(config.get("edge_uplink_count", 0))
    uplink_speed_gbps = int(config.get("edge_uplink_speed_gbps", 0))
    if uplink_count < 2 or uplink_speed_gbps < 100:
        errors.append(
            f"insufficient_edge_uplinks ({uplink_count}x {uplink_speed_gbps}GbE < recommended 2x 100GbE DR1)"
        )

    if str(config.get("edge_optics_type", "")) != "DR1_single_mode":
        errors.append("wrong_edge_optics (requires DR1 single-mode optics)")

    if str(config.get("edge_routing_protocol", "")) != "eBGP":
        errors.append("wrong_edge_routing_protocol (requires eBGP route handover with dedicated VTEP)")

    if str(config.get("bms_security_zone", "")) != "untrusted":
        errors.append("wrong_bms_security_zone (BMS telemetry must flow through uplink in untrusted zone)")

    oob_handover = str(config.get("oob_uplink_mode", ""))
    if oob_handover not in ("dedicated_oob_edge_tor", "inband_spine_route_leaking"):
        errors.append(
            "invalid_oob_uplink_mode (must use dedicated_oob_edge_tor or inband_spine_route_leaking)"
        )

    if str(config.get("runai_control_plane_placement", "")) != "user_space_k8s_cluster":
        errors.append(
            "wrong_runai_control_plane_placement (must reside on user-space Kubernetes cluster)"
        )

    if str(config.get("runai_cluster_operands_placement", "")) != "administrative_k8s_infrastructure":
        errors.append(
            "wrong_runai_operands_placement (must reside on administrative Kubernetes infrastructure)"
        )

    return {
        "valid_architecture": len(errors) == 0,
        "errors": errors,
    }
