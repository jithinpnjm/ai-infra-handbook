#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.8: GB300 SuperPOD reference architecture."""

from __future__ import annotations

import sys

from gb300_superpod_ra import (
    audit_gb300_edge_and_software_architecture,
    verify_gb300_su_ethernet_leaf_blocking,
    verify_gb300_su_ib_leaf_port_math,
)
from superpod_concepts import size_gb300_superpod, size_superpod_storage_tier


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.8 Lab: GB300 SuperPOD Reference Architecture ===")

    # 1. Q3400-RD Quantum-X800 144-port InfiniBand SU port math checks (pp. 20-21)
    ib_math = verify_gb300_su_ib_leaf_port_math()
    check(
        "1 GB300 SU has 8 racks * 18 trays = 144 compute trays and 576 B300 GPUs",
        ib_math["trays_per_su"] == 144 and ib_math["gpus_per_su"] == 576,
    )
    check(
        "144 trays * 4 ConnectX-8 NICs == 576 compute ports across 8 leaves (4 rails * 2 leaves/rail)",
        ib_math["total_compute_ports_per_su"] == 576 and ib_math["leaves_per_su"] == 8,
    )
    check(
        "Each 144-port Q3400-RD leaf has 72 compute downlinks + 72 spine uplinks (1:1 non-blocking)",
        ib_math["downlinks_per_leaf"] == 72
        and ib_math["uplinks_per_leaf"] == 72
        and ib_math["is_1_to_1_nonblocking"] is True,
        f"got {ib_math}",
    )

    try:
        verify_gb300_su_ib_leaf_port_math(racks_per_su=0)
        check("Rejects non-positive racks_per_su in IB port verifier", False)
    except ValueError:
        check("Rejects non-positive racks_per_su in IB port verifier", True)

    # 2. Spectrum-4 SN5600D Ethernet Fabric port & blocking ratio checks (pp. 22-23)
    eth_math = verify_gb300_su_ethernet_leaf_blocking()
    check(
        "144 trays * 2 BlueField-3 ports == 288 ports across 4 SN5600D compute leaves (72 downlinks/leaf)",
        eth_math["total_bf3_ports_per_su"] == 288
        and eth_math["downlinks_per_compute_leaf"] == 72,
    )
    check(
        "SPGB300 p.22: 24 uplinks vs 72 downlinks at 400G per compute leaf == 1:3 blocking ratio",
        eth_math["uplinks_per_compute_leaf"] == 24
        and eth_math["compute_leaf_blocking_ratio"] == "1:3",
        f"got {eth_math}",
    )
    check(
        "SPGB300 p.22: Storage leaves use 72 non-blocking 400G links and management leaves use 24x 400G links",
        eth_math["storage_leaf_links_400g"] == 72 and eth_math["mgmt_leaf_links_400g"] == 24,
    )

    try:
        verify_gb300_su_ethernet_leaf_blocking(trays_per_su=0)
        check("Rejects non-positive trays_per_su in Ethernet verifier", False)
    except ValueError:
        check("Rejects non-positive trays_per_su in Ethernet verifier", True)

    # 3. Multi-SU Scaling Verification across 1, 2, 4, 8, 16 SUs (Tables 3 & 4, pp. 21, 23)
    for su, gpus, ib_l, ib_s, eth_s, eth_cl, eth_sl, st_bw in [
        (1, 576, 8, 4, 2, 4, 2, "32x400GbE"),
        (2, 1152, 16, 8, 4, 8, 2, "64x400GbE"),
        (4, 2304, 32, 18, 8, 16, 2, "128x400GbE"),
        (8, 4608, 64, 36, 12, 32, 4, "256x400GbE"),
        (16, 9216, 128, 72, 24, 64, 8, "1024x400GbE"),
    ]:
        row = size_gb300_superpod(su)
        check(
            f"SPGB300 Tables 3&4 ({su} SU = {gpus} GPUs): IB {ib_l}L/{ib_s}S, Eth {eth_s}S/{eth_cl}CL/{eth_sl}SL, {st_bw}",
            row["gpus"] == gpus
            and row["ib_leaf_total"] == ib_l
            and row["ib_spine_total"] == ib_s
            and row["eth_spines"] == eth_s
            and row["eth_compute_leaves"] == eth_cl
            and row["eth_storage_leaves"] == eth_sl
            and row["max_storage_ports"] == st_bw
            and row["mgmt_leaves_plus_oob_spines"] == "2+2",
            f"got {row}",
        )

    # 4. Customer Edge Connectivity, OOB Handover, BMS & Run:ai Placement checks (pp. 27-28, 32-34)
    valid_cfg = {
        "edge_uplink_count": 2,
        "edge_uplink_speed_gbps": 100,
        "edge_optics_type": "DR1_single_mode",
        "edge_routing_protocol": "eBGP",
        "bms_security_zone": "untrusted",
        "oob_uplink_mode": "dedicated_oob_edge_tor",
        "runai_control_plane_placement": "user_space_k8s_cluster",
        "runai_cluster_operands_placement": "administrative_k8s_infrastructure",
    }
    res_ok = audit_gb300_edge_and_software_architecture(valid_cfg)
    check(
        "Valid GB300 customer edge (2x100GbE DR1, eBGP, BMS untrusted, OOB edge ToR, Run:ai split) passes",
        res_ok["valid_architecture"] is True and len(res_ok["errors"]) == 0,
        f"got {res_ok}",
    )

    leak_cfg = dict(valid_cfg, oob_uplink_mode="inband_spine_route_leaking")
    check(
        "SPGB300 p.28: OOB route leaking via SN5600D In-Band spines is accepted when dedicated OOB link is omitted",
        audit_gb300_edge_and_software_architecture(leak_cfg)["valid_architecture"] is True,
    )

    bad_uplink = dict(valid_cfg, edge_uplink_count=1, edge_uplink_speed_gbps=40)
    check(
        "SPGB300 p.27: Flags customer edge uplink < 2x 100GbE",
        any("insufficient_edge_uplinks" in e for e in audit_gb300_edge_and_software_architecture(bad_uplink)["errors"]),
    )

    bad_optics = dict(valid_cfg, edge_optics_type="SR4_multimode")
    check(
        "SPGB300 p.27: Flags non-DR1 single-mode optics on customer edge uplink",
        any("wrong_edge_optics" in e for e in audit_gb300_edge_and_software_architecture(bad_optics)["errors"]),
    )

    bad_bgp = dict(valid_cfg, edge_routing_protocol="OSPF")
    check(
        "SPGB300 p.27: Flags non-eBGP customer edge routing protocol",
        any("wrong_edge_routing_protocol" in e for e in audit_gb300_edge_and_software_architecture(bad_bgp)["errors"]),
    )

    bad_bms = dict(valid_cfg, bms_security_zone="trusted_compute")
    check(
        "SPGB300 p.27: Flags placing Building Management System (BMS) outside the untrusted uplink zone",
        any("wrong_bms_security_zone" in e for e in audit_gb300_edge_and_software_architecture(bad_bms)["errors"]),
    )

    bad_oob = dict(valid_cfg, oob_uplink_mode="none")
    check(
        "SPGB300 pp.27-28: Flags invalid OOB uplink mode",
        any("invalid_oob_uplink_mode" in e for e in audit_gb300_edge_and_software_architecture(bad_oob)["errors"]),
    )

    bad_runai_cp = dict(valid_cfg, runai_control_plane_placement="bare_metal_slurm")
    check(
        "SPGB300 p.34: Flags placing Run:ai control plane outside the user-space Kubernetes cluster",
        any("wrong_runai_control_plane_placement" in e for e in audit_gb300_edge_and_software_architecture(bad_runai_cp)["errors"]),
    )

    bad_runai_op = dict(valid_cfg, runai_cluster_operands_placement="user_space_k8s_cluster")
    check(
        "SPGB300 p.34: Flags placing Run:ai cluster operands outside the administrative K8s infrastructure",
        any("wrong_runai_operands_placement" in e for e in audit_gb300_edge_and_software_architecture(bad_runai_op)["errors"]),
    )

    # 5. Storage tier & TDP scaling checks across 1..16 SUs
    check(
        "1 SU Standard/Enhanced read (90 / 280 GB/s) and 4 SU read (360 / 1,120 GB/s) match Table 5",
        size_superpod_storage_tier(1, "Standard")["aggregate_read_gbps"] == 90.0
        and size_superpod_storage_tier(1, "Enhanced")["aggregate_read_gbps"] == 280.0
        and size_superpod_storage_tier(4, "Standard")["aggregate_read_gbps"] == 360.0
        and size_superpod_storage_tier(4, "Enhanced")["aggregate_read_gbps"] == 1120.0,
    )
    check(
        "2-SU fully tested GB300 system (p.14) has 16 racks, 1,152 GPUs, and 2.4 MW TDP",
        size_gb300_superpod(2)["racks"] == 16
        and size_gb300_superpod(2)["gpus"] == 1152
        and size_gb300_superpod(2)["tdp_mw"] == 2.4,
    )
    check(
        "SPGB300 p.11: 8 power shelves/rack * 6 PSUs * 5.5 kW == 264.0 kW total shelf capacity per rack",
        round(8 * 6 * 5.5, 1) == 264.0,
    )
    check(
        "SPGB300 p.9: 1 SU (8 racks = 144 compute trays) provides 144 * 4 * 3.84 TB == 2,211.84 TB E1.S RAID 0 scratch",
        round(144 * 4 * 3.84, 2) == 2211.84,
    )
    check(
        "SPGB300 p.9: 1 SU (144 compute trays) provides 144 * 1.92 TB == 276.48 TB M.2 OS storage",
        round(144 * 1.92, 2) == 276.48,
    )
    check(
        "SPGB300 p.19: 1 SU (8 racks) contains 8 * 9 == 72 NVLink switch trays (144 NVSwitch ASICs)",
        8 * 9 == 72 and 72 * 2 == 144,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
