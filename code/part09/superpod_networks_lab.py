#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.9: Compute, storage, in-band and out-of-band networks in a SuperPOD."""

from __future__ import annotations

import sys

from superpod_networks import (
    calculate_clos_fabric_scale,
    classify_superpod_network_plane,
    compare_leaf_placement_strategy,
    evaluate_rocev2_load_balancing_and_dcqcn,
)


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

    print("=== Chapter 9.9 Lab: Compute, Storage, In-Band & OOB Networks in a SuperPOD ===")

    # 1. Five Logical Segments & Four Physical Fabrics Mapping checks (superpod-gb300-ra pp. 13, 18-28)
    p_nvl = classify_superpod_network_plane("intra_rack_gpu_p2p")
    check(
        "Intra-rack GPU P2P maps to NVLink 5 segment on MN-NVL fabric managed by NMX-M",
        p_nvl["logical_segment"] == "NVLink 5"
        and p_nvl["physical_fabric"] == "Multi-node NVLink Fabric (MN-NVL)"
        and p_nvl["fabric_manager"] == "NMX-M",
    )

    p_comp = classify_superpod_network_plane("inter_rack_nccl_collectives")
    check(
        "Inter-rack NCCL collectives map to Compute Network on Quantum InfiniBand managed by UFM Enterprise",
        p_comp["logical_segment"] == "Compute Network"
        and p_comp["physical_fabric"] == "Compute InfiniBand Fabric"
        and p_comp["fabric_manager"] == "UFM Enterprise",
    )

    p_stor = classify_superpod_network_plane("parallel_filesystem_rocev2")
    check(
        "Parallel filesystem RoCEv2 maps to Storage Network on SN5600D via unbonded BlueField-3 400G Port 1",
        p_stor["logical_segment"] == "Storage Network"
        and p_stor["physical_fabric"] == "Storage and In-band Ethernet Fabric"
        and "400 Gbps Dedicated Unbonded" in p_stor["host_interface"],
    )

    p_inband = classify_superpod_network_plane("slurm_k8s_nfs_home_and_ebgp_uplink")
    check(
        "Slurm/K8s/NFS/eBGP maps to In-Band Management Network on SN5600D via BlueField-3 >=200G Port 2",
        p_inband["logical_segment"] == "In-Band Management Network"
        and p_inband["physical_fabric"] == "Storage and In-band Ethernet Fabric",
    )

    p_oob = classify_superpod_network_plane("bmc_ipmi_redfish_and_nvos_come")
    check(
        "BMC/Redfish/NVOS COMe maps to OOB Management Network on SN2201 + VXLAN OOB Spines",
        p_oob["logical_segment"] == "Out-of-Band Management Network"
        and "SN2201" in p_oob["switch_hardware"],
    )

    try:
        classify_superpod_network_plane("unknown_flow")
        check("Rejects unknown traffic_type in network plane classifier", False)
    except KeyError:
        check("Rejects unknown traffic_type in network plane classifier", True)

    # 2. Leaf Switch Physical Placement (ToR vs MoR vs EoR) checks (AIDC Ch 3 Table 3-1)
    tor = compare_leaf_placement_strategy("ToR")
    mor = compare_leaf_placement_strategy("MoR")
    eor = compare_leaf_placement_strategy("EoR")
    check(
        "AIDC Ch3 Table 3-1: ToR spans max 8 racks, requires less rack space, more power/cooling per compute rack",
        tor["max_cable_span_racks"] == 8
        and tor["rack_space_requirement"] == "Less"
        and tor["power_cooling_per_compute_rack"] == "More"
        and tor["ideal_for_rud_with_dac"] is True,
    )
    check(
        "AIDC Ch3 Table 3-1: MoR achieves shortest max cable span (6 racks) and removes switch power/heat from compute racks",
        mor["max_cable_span_racks"] == 6
        and mor["power_cooling_per_compute_rack"] == "Less"
        and mor["cabling_within_compute_rack"] is False,
    )
    check(
        "AIDC Ch3 Table 3-1: EoR has longest max cable span (10 racks)",
        eor["max_cable_span_racks"] == 10 and eor["cabling_within_compute_rack"] is False,
    )

    try:
        compare_leaf_placement_strategy("BottomOfRack")
        check("Rejects unknown leaf placement strategy", False)
    except ValueError:
        check("Rejects unknown leaf placement strategy", True)

    # 3. 3-Stage vs 5-Stage Clos Scaling checks (AIDC Ch 3 Fig. 3-9, 3-11, 3-12 & SPGB300 Table 3)
    c_64_1row = calculate_clos_fabric_scale(64, stages=3, rows_or_su_count=1)
    check(
        "AIDC Fig 3-9: 1 row with 64x400G switches == 256 GPUs, 8 leaves, 4 spines",
        c_64_1row["total_gpus"] == 256
        and c_64_1row["leaf_switches"] == 8
        and c_64_1row["spine_switches"] == 4,
    )

    c_64_2row = calculate_clos_fabric_scale(64, stages=3, rows_or_su_count=2)
    check(
        "AIDC Fig 3-9: 2 rows with 64x400G switches == 512 GPUs, 16 leaves, 8 spines",
        c_64_2row["total_gpus"] == 512
        and c_64_2row["leaf_switches"] == 16
        and c_64_2row["spine_switches"] == 8,
    )

    c_64_max = calculate_clos_fabric_scale(64, stages=3, rows_or_su_count=8)
    check(
        "AIDC Fig 3-9: Max 3-stage Clos with 64x400G switches (8 rows) == 2,048 GPUs, 64 leaves, 32 spines",
        c_64_max["total_gpus"] == 2048
        and c_64_max["leaf_switches"] == 64
        and c_64_max["spine_switches"] == 32
        and c_64_max["max_nonblocking_3stage_gpus"] == 2048,
    )

    c_144_max = calculate_clos_fabric_scale(144, stages=3, rows_or_su_count=16)
    check(
        "SPGB300 Table 3: 3-stage (2-layer) Clos with 144x800G Q3400-RD (16 SUs) == 9,216 GPUs, 128 leaves, 72 spines",
        c_144_max["total_gpus"] == 9216
        and c_144_max["leaf_switches"] == 128
        and c_144_max["spine_switches"] == 72
        and c_144_max["max_nonblocking_3stage_gpus"] == 9216,
    )

    # 5-stage Clos oversubscription sweep (AIDC Fig 3-12: 1:1 -> 2048, 2:1 -> 4096, 4:1 -> 8192, 7:1 -> 14336)
    for os_ratio, exp_blocks, exp_gpus, exp_leaves in [
        (1, 2, 2048, 64),
        (2, 4, 4096, 128),
        (4, 8, 8192, 256),
        (7, 14, 14336, 448),
    ]:
        c5 = calculate_clos_fabric_scale(64, stages=5, super_spine_oversubscription=os_ratio)
        check(
            f"AIDC Fig 3-12 5-stage Clos at {os_ratio}:1 oversubscription == {exp_blocks} blocks, {exp_gpus} GPUs, {exp_leaves} leaves/spines, 32 super-spines",
            c5["blocks"] == exp_blocks
            and c5["total_gpus"] == exp_gpus
            and c5["leaf_switches"] == exp_leaves
            and c5["spine_switches"] == exp_leaves
            and c5["super_spine_switches"] == 32
            and c5["super_spine_ports"] == 2048,
            f"got {c5}",
        )

    # 4. RoCEv2 UDP 4791, Load Balancing (SLB/DLB/GLB/sDLB), and DCQCN checks (AIDC Ch 2)
    roce_good = {
        "rocev2_udp_dest_port": 4791,
        "load_balancing_mode": "GLB",
        "has_low_entropy_elephant_flows": True,
        "dcqcn_ecn_enabled": True,
        "pfc_enabled": True,
        "congested_switch_ecn_bits": "11",
        "roce_bonded_with_inband": False,
    }
    check(
        "RoCEv2 on UDP 4791 with GLB + DCQCN (ECN '11' + PFC) and unbonded 400G port passes audit",
        evaluate_rocev2_load_balancing_and_dcqcn(roce_good)["lossless_and_balanced"] is True,
    )

    roce_sdlb = dict(roce_good, load_balancing_mode="sDLB")
    check(
        "Selective DLB (sDLB BTH opcode matching) passes elephant-flow load balancing check",
        evaluate_rocev2_load_balancing_and_dcqcn(roce_sdlb)["lossless_and_balanced"] is True,
    )

    roce_bad_port = dict(roce_good, rocev2_udp_dest_port=8472)  # 8472/4789 is VXLAN, not RoCEv2 4791!
    check(
        "AIDC Ch2: Flags wrong UDP port (RoCEv2 uses UDP 4791)",
        any("wrong_rocev2_udp_port" in i for i in evaluate_rocev2_load_balancing_and_dcqcn(roce_bad_port)["issues"]),
    )

    roce_slb = dict(roce_good, load_balancing_mode="SLB")
    check(
        "AIDC Ch2: Flags Static Load Balancing (SLB 5-tuple hash) under low-entropy elephant flows",
        any("slb_elephant_flow_collision_risk" in i for i in evaluate_rocev2_load_balancing_and_dcqcn(roce_slb)["issues"]),
    )

    roce_no_pfc = dict(roce_good, pfc_enabled=False)
    check(
        "AIDC Ch2: Flags missing PFC/ECN lossless DCQCN configuration",
        any("missing_lossless_dcqcn" in i for i in evaluate_rocev2_load_balancing_and_dcqcn(roce_no_pfc)["issues"]),
    )

    roce_bad_ecn = dict(roce_good, congested_switch_ecn_bits="00")
    check(
        "AIDC Ch2 Fig 2-5: Flags congested switch not setting ECN bits to '11' (Congestion Experienced)",
        any("invalid_ecn_congestion_bits" in i for i in evaluate_rocev2_load_balancing_and_dcqcn(roce_bad_ecn)["issues"]),
    )

    roce_bonded = dict(roce_good, roce_bonded_with_inband=True)
    check(
        "SPGB300 p.24: Flags bonding RoCEv2 Storage port with In-Band Management port",
        any("bonded_roce_inband_violation" in i for i in evaluate_rocev2_load_balancing_and_dcqcn(roce_bonded)["issues"]),
    )

    try:
        calculate_clos_fabric_scale(32)
        check("Rejects unsupported switch radix in Clos calculator", False)
    except ValueError:
        check("Rejects unsupported switch radix in Clos calculator", True)

    try:
        calculate_clos_fabric_scale(64, stages=4)
        check("Rejects invalid stage count in Clos calculator", False)
    except ValueError:
        check("Rejects invalid stage count in Clos calculator", True)

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
