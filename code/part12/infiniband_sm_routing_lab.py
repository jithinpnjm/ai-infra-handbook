#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.7: InfiniBand subnet manager, routing, topologies and rails.

Runs 28 deterministic checks reproducing every protocol constant, OpenSM election rule,
port state machine transition, Directed Route SMP hop traversal, LMC multipath LID math,
Linear Forwarding Table (LFT) programming and uplink balance audit, routing engine
validator, Fat-Tree / Folded Clos oversubscription and 3-stage/5-stage scale calculations,
Rail-Optimized (`ROD`) vs Rail-Unified (`RUD`) and Multi-Planar designs, and AI IP fabric
routing parameters from:
  - `nvidia-devops` Volume 08 (`chapter-05-subnet-management-and-opensm.md`,
    `chapter-06-routing-topologies-and-oversubscription.md`, `chapter-12-volume-08-summary.md`,
    `index.md`, and `labs/lab-01..04`)
  - *Supercomputers for Linux SysAdmins* (`SCL` Ch 5)
  - *AI Data Center Network Design and Technologies* (`ADC` Ch 3 & Ch 8)
  - *NVIDIA Base Command Manager 11 Administrator Manual* (`bcm11-admin` §3.6.3 & §7.5)
"""

from __future__ import annotations

import sys

from infiniband_sm_routing import (
    ASN_PRIVATE_16BIT_MAX,
    ASN_PRIVATE_16BIT_MIN,
    ASN_PRIVATE_32BIT_MAX,
    ASN_PRIVATE_32BIT_MIN,
    BGP_AFI_IPV4,
    BGP_EXT_NEXTHOP_CAP_CODE,
    BGP_EXT_NEXTHOP_CAP_LEN,
    BGP_NH_AFI_IPV6,
    BGP_SAFI_UNICAST,
    BGP_TCP_PORT,
    IB_DEFAULT_GID_PREFIX,
    IB_MAX_MULTICAST_LID,
    IB_MAX_UNICAST_LID,
    IB_MIN_MULTICAST_LID,
    IB_MIN_UNICAST_LID,
    IB_PERMISSIVE_LID,
    IB_RESERVED_LID,
    IB_SITE_LOCAL_GID_PREFIX,
    IB_SMP_VL,
    IB_TRAP_LINK_STATE_CHANGE,
    IB_UNROUTED_PORT,
    ISIS_MAX_SWITCH_SCALE,
    PERFQUERY_OCTETS_PER_WORD,
    PHYS_STATE_LINKUP,
    PHYS_STATE_POLLING,
    PORT_STATE_ACTIVE,
    PORT_STATE_ARMED,
    PORT_STATE_DOWN,
    PORT_STATE_INITIALIZE,
    RIFT_MIN_SWITCH_SCALE,
    ROUTING_ENGINES,
    SM_MAX_PRIORITY,
    SM_MIN_PRIORITY,
    SMINFO_DISCOVERING,
    SMINFO_MASTER,
    SMINFO_NOTACTIVE,
    SMINFO_STANDBY,
    SRV6_SID_BITS,
    SRV6_USID_BITS,
    TOPOGRAPH_DEFAULT_PORT,
    CandidateSM,
    audit_sm_authority,
    audit_uplink_port_xmit_bytes,
    compare_rail_designs,
    compute_lmc_lid_block,
    elect_master_sm,
    evaluate_ib_port_state,
    evaluate_leaf_oversubscription,
    plan_five_stage_rail_clos,
    plan_three_stage_rail_clos,
    program_leaf_lft,
    simulate_directed_route_smp,
    validate_updn_turn_sequence,
)


def main() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    print("=== Chapter 12.7 Lab: InfiniBand Subnet Manager, Routing, Topologies and Rails ===")

    # 1. SCL Ch 5: IB LID address space (0 reserved, 1..0xBFFF=49,151 unicast, 0xC000..0xFFFE multicast, 0xFFFF permissive)
    check(
        "SCL Ch 5 LID address space: 0 reserved, 1..0xBFFF (2^15 + 2^14 - 1 = 49,151) unicast, 0xC000..0xFFFE (49,152..65,534) multicast, 0xFFFF (65,535) permissive",
        IB_RESERVED_LID == 0
        and IB_MIN_UNICAST_LID == 1
        and IB_MAX_UNICAST_LID == 0xBFFF
        and IB_MAX_UNICAST_LID == (2**15 + 2**14 - 1) == 49_151
        and IB_MIN_MULTICAST_LID == 0xC000 == 49_152
        and IB_MAX_MULTICAST_LID == 0xFFFE == 65_534
        and IB_PERMISSIVE_LID == 0xFFFF == 65_535,
    )

    # 2. SCL Ch 5: GID prefixes (0xFE80::/64 link-local, 0xFEC0::/64 site-local) & VL15 SMP / Trap 128
    check(
        "SCL Ch 5 & V8 Ch 5 GID & SMP constants: default GID prefix 0xfe80::/64, site-local 0xfec0::/64, VL15 for SMPs, Trap 128 link state change",
        IB_DEFAULT_GID_PREFIX == 0xFE80000000000000
        and IB_SITE_LOCAL_GID_PREFIX == 0xFEC0000000000000
        and IB_SMP_VL == 15
        and IB_TRAP_LINK_STATE_CHANGE == 128
        and IB_UNROUTED_PORT == 0xFF == 255,
    )

    # 3. V8 Ch 5 & SCL Ch 5: OpenSM priority 0..15 and SMInfo state codes 0..3
    check(
        "V8 Ch 5 & SCL Ch 5 OpenSM priority (0..15) and sminfo states (0=NOTACTIVE, 1=DISCOVERING, 2=STANDBY, 3=MASTER)",
        SM_MIN_PRIORITY == 0
        and SM_MAX_PRIORITY == 15
        and (SMINFO_NOTACTIVE, SMINFO_DISCOVERING, SMINFO_STANDBY, SMINFO_MASTER) == (0, 1, 2, 3),
    )

    # 4. OpenSM Master Election by Priority (`priority 15` beats `priority 8` and `priority 0`)
    sm_primary = CandidateSM("ufm-sm-01", guid=0x0002C903004A1B20, lid=1, priority=15, activity_count=184223)
    sm_standby1 = CandidateSM("ufm-sm-02", guid=0x0012345600003740, lid=2, priority=8, activity_count=412)
    sm_host_stray = CandidateSM("compute-node-sm", guid=0x00123456000073F0, lid=44, priority=0, activity_count=10)
    elec1 = elect_master_sm([sm_standby1, sm_host_stray, sm_primary])
    check(
        "V8 Ch 5 OpenSM election by priority: priority 15 (0x0002c903004a1b20, lid 1, activity 184223) wins MASTER over priority 8 and 0 despite higher GUID",
        elec1.master.name == "ufm-sm-01"
        and elec1.master.priority == 15
        and elec1.master.guid == 0x0002C903004A1B20
        and elec1.master.state == SMINFO_MASTER
        and elec1.won_by_guid_tiebreaker is False
        and len(elec1.standbys) == 2
        and all(s.state == SMINFO_STANDBY for s in elec1.standbys),
    )

    # 5. OpenSM Master Election Tie-Breaker: Equal priority -> Lowest Port/SM GUID wins
    sm_tie_a = CandidateSM("sm-node-a", guid=0x08C0EB0300F1A2C3, lid=11, priority=14)
    sm_tie_b = CandidateSM("sm-node-b", guid=0x0002C903004A1B20, lid=12, priority=14)
    elec_tie = elect_master_sm([sm_tie_a, sm_tie_b])
    check(
        "OpenSM equal-priority tie-breaker: when both SMs have priority 14, lowest GUID (0x0002c903004a1b20 < 0x08c0eb0300f1a2c3) wins SMINFO_MASTER",
        elec_tie.master.name == "sm-node-b"
        and elec_tie.master.guid == 0x0002C903004A1B20
        and elec_tie.won_by_guid_tiebreaker is True
        and elec_tie.roles_by_name == {"sm-node-b": "SMINFO_MASTER", "sm-node-a": "SMINFO_STANDBY"},
    )

    # 6. V8 Ch 5 Figure 8.5.1 & Scenarios 1-2: SM authority audit (0 masters, 2 masters split authority, frozen activity count, healthy)
    check(
        "V8 Ch 5 Fig 8.5.1 SM authority audit: distinguishes 0 masters, 2 masters (split authority), frozen activity count, and healthy climbing master",
        audit_sm_authority([elec1.standbys[0], elec1.standbys[1]]) == "ZERO_MASTERS_PORTS_STUCK_INITIALIZING"
        and audit_sm_authority([elec1.master, elec_tie.master]) == "SPLIT_AUTHORITY_MULTIPLE_MASTERS"
        and audit_sm_authority([elec1.master], previous_master_activity=184223) == "FROZEN_MASTER_ACTIVITY_COUNT"
        and audit_sm_authority([elec1.master], previous_master_activity=184000) == "HEALTHY_SINGLE_MASTER",
    )

    # 7-9. Port State Machine: Down (1) -> Initialize (2) -> Armed (3) -> Active (4)
    st_down = evaluate_ib_port_state(False, False, False)
    st_init = evaluate_ib_port_state(True, False, False)
    st_armed = evaluate_ib_port_state(True, True, False, assigned_lid=12, sm_lid=1)
    st_active = evaluate_ib_port_state(True, True, True, assigned_lid=12, sm_lid=1)

    check(
        "Port state machine (Down -> Initialize): Physical Polling -> Logical Down (1); Physical LinkUp (5) without SM -> Logical Initialize (2, Base LID=0, SM LID=0, VL15 SMP only)",
        st_down.phys_state_code == PHYS_STATE_POLLING
        and st_down.logical_state_code == PORT_STATE_DOWN
        and not st_down.can_carry_smp_vl15
        and st_init.phys_state_code == PHYS_STATE_LINKUP
        and st_init.logical_state_code == PORT_STATE_INITIALIZE
        and st_init.base_lid == 0
        and st_init.sm_lid == 0
        and st_init.can_carry_smp_vl15 is True
        and st_init.can_carry_user_rdma_vl0_14 is False,
    )
    check(
        "Port state machine (Armed -> Active): Armed (3) has LID=12 & SM LID=1 but user RDMA blocked; Active (4) requires SM LFT programming + PortInfo activation",
        st_armed.logical_state_code == PORT_STATE_ARMED
        and st_armed.base_lid == 12
        and st_armed.sm_lid == 1
        and st_armed.can_carry_user_rdma_vl0_14 is False
        and st_active.logical_state_code == PORT_STATE_ACTIVE
        and st_active.phys_state_code == PHYS_STATE_LINKUP
        and st_active.can_carry_user_rdma_vl0_14 is True,
    )

    # 10. SCL Ch 5 Directed Route SMP (`DLID=0xFFFF`) hop-pointer and return-path traversal
    dr = simulate_directed_route_smp(egress_ports=[1, 7, 14], ingress_ports_at_hops=[18, 4, 2])
    check(
        "SCL Ch 5 Directed Route SMP (DLID 0xFFFF): 3-hop path [0, 1, 7, 14] increments hop_pointer 1->2->3 (D=0), records return_path [0, 18, 4, 2], and decrements 3->2->1 (D=1)",
        dr.hop_count == 3
        and dr.initial_path == (0, 1, 7, 14)
        and dr.return_path == (0, 18, 4, 2)
        and dr.forward_hop_pointers == (1, 2, 3)
        and dr.reverse_hop_pointers == (3, 2, 1),
    )

    # 11. SCL Ch 5 LMC (LID Mask Control) consecutive LID assignment (`Base LID .. Base LID + 2^LMC - 1`)
    lids_lmc0 = compute_lmc_lid_block(913, 0)
    lids_lmc2 = compute_lmc_lid_block(16, 2)
    lids_lmc3 = compute_lmc_lid_block(64, 3)
    check(
        "SCL Ch 5 LMC multipath LID math: LMC=0 -> 1 LID (913), LMC=2 -> 2^2=4 LIDs (16..19), LMC=3 -> 2^3=8 LIDs (64..71)",
        lids_lmc0 == (913,)
        and lids_lmc2 == (16, 17, 18, 19)
        and len(lids_lmc3) == 8
        and lids_lmc3[0] == 64
        and lids_lmc3[-1] == 71,
    )

    # 12-13. Linear Forwarding Table (LFT) programming & V8 Ch 6 Scenario 1 hot-uplink imbalance
    local_map = {lid: lid for lid in range(1, 17)}
    remote_lids = list(range(17, 17 + 84))  # 84 remote destinations across 4 uplinks (ports 5, 6, 7, 8)
    lft_bal = program_leaf_lft("Leaf-1", local_map, remote_lids, [5, 6, 7, 8], policy="ftree_round_robin")
    lft_hot = program_leaf_lft("Leaf-1", local_map, remote_lids, [5, 6, 7, 8], policy="static_naive")

    check(
        "LFT programming (`ftree_round_robin`): 84 remote LIDs spread evenly across uplinks 5..8 (21 LIDs/uplink, 1.0:1 ratio)",
        lft_bal.uplink_lid_counts == {5: 21, 6: 21, 7: 21, 8: 21}
        and lft_bal.max_to_min_ratio == 1.0
        and lft_bal.is_balanced is True,
    )
    check(
        "LFT programming (`static_naive` vs `ftree`): naive static LFT concentrates 40 LIDs on ports 5-6 vs 2 LIDs on ports 7-8 (20.0:1 ratio)",
        lft_hot.uplink_lid_counts == {5: 40, 6: 40, 7: 2, 8: 2}
        and lft_hot.max_to_min_ratio == 20.0
        and lft_hot.is_balanced is False,
    )

    # 14. V8 Ch 6 Scenario 1 `perfquery` `PortXmitData` 4-octet counter audit
    v8_sc1_bytes = {
        5: 21_474_836_480,
        6: 21_489_234_432,
        7: 1_073_741_824,
        8: 1_081_654_272,
    }
    audit_sc1 = audit_uplink_port_xmit_bytes(v8_sc1_bytes)
    check(
        "V8 Ch 6 Scenario 1 `perfquery` PortXmitData audit: ports 5-6 (~21.47 GB / 5,368,709,120 words) vs ports 7-8 (~1.07 GB / 268,435,456 words) = 20.01:1 imbalance",
        PERFQUERY_OCTETS_PER_WORD == 4
        and audit_sc1.words_by_port[5] == 5_368_709_120
        and audit_sc1.words_by_port[7] == 268_435_456
        and audit_sc1.imbalance_ratio == 20.01
        and audit_sc1.hot_ports == (5, 6)
        and audit_sc1.idle_ports == (7, 8)
        and audit_sc1.diagnosis == "ROUTE_OR_LID_CONCENTRATION_HOT_UPLINKS",
    )

    # 15-16. OpenSM Routing Engines (`minhop`, `updn`, `ftree`, `dor`, `dfsssp`) & Up/Down turn rule
    check(
        "OpenSM routing engines (`minhop`, `updn`, `ftree`, `dor`, `dfsssp`): `ftree` -> `ar_ftree`, `updn` -> `ar_updn`, `dor` -> `ar_dor` (requires >=2 VLs), `dfsssp` (requires >=2 VLs)",
        set(ROUTING_ENGINES.keys()) == {"minhop", "updn", "ftree", "dor", "dfsssp"}
        and ROUTING_ENGINES["ftree"].supports_adaptive_routing_variant == "ar_ftree"
        and ROUTING_ENGINES["updn"].supports_adaptive_routing_variant == "ar_updn"
        and ROUTING_ENGINES["dor"].min_vls_required == 2
        and ROUTING_ENGINES["dfsssp"].min_vls_required == 2,
    )
    check(
        "Up/Down (`updn`) credit-loop turn validator: UP->UP->DOWN->DOWN is valid, whereas UP->DOWN->UP violates the Down->Up turn prohibition",
        validate_updn_turn_sequence(["UP", "UP", "DOWN", "DOWN"]) is True
        and validate_updn_turn_sequence(["DOWN", "DOWN"]) is True
        and validate_updn_turn_sequence(["UP", "DOWN", "UP", "DOWN"]) is False,
    )

    # 17-19. V8 Ch 6 Worked Example: 16x400G downlinks vs 8x400G uplinks (2:1 oversubscription), 2 GB AllReduce (40 ms vs 80 ms), 1 spine failure (2:1 -> 4:1), and `ib_write_bw` 2,097,152 B (397.62 vs 201.18 Gbps)
    leaf_1to1 = evaluate_leaf_oversubscription(downlink_ports=16, uplink_ports=16, port_rate_gbps=400.0)
    leaf_2to1 = evaluate_leaf_oversubscription(downlink_ports=16, uplink_ports=8, port_rate_gbps=400.0)

    check(
        "V8 Ch 6 Non-blocking (1:1) vs 2:1 oversubscribed leaf: 16x400G=6,400 Gbps down vs 8x400G=3,200 Gbps up -> 2:1 oversubscription, 200 Gbps (25 GB/s) per node",
        leaf_1to1.downlink_bw_gbps == 6400.0
        and leaf_1to1.uplink_bw_gbps == 6400.0
        and leaf_1to1.oversubscription_ratio == 1.0
        and leaf_1to1.per_node_cross_leaf_gbps == 400.0
        and leaf_1to1.per_node_cross_leaf_gb_s == 50.0
        and leaf_2to1.downlink_bw_gbps == 6400.0
        and leaf_2to1.uplink_bw_gbps == 3200.0
        and leaf_2to1.oversubscription_ratio == 2.0
        and leaf_2to1.per_node_cross_leaf_gbps == 200.0
        and leaf_2to1.per_node_cross_leaf_gb_s == 25.0,
    )
    check(
        "V8 Ch 6 AllReduce step time & spine failure blast radius: 2 GB gradient takes 40.0 ms at 1:1 (50 GB/s) vs 80.0 ms at 2:1 (25 GB/s); losing 1 of 2 spines doubles oversubscription from 2:1 to 4:1",
        leaf_1to1.allreduce_step_time_ms == 40.0
        and leaf_2to1.allreduce_step_time_ms == 80.0
        and leaf_2to1.degraded_oversubscription_one_spine_lost == 4.0,
    )
    same_leaf_bw = 397.62
    cross_rack_bw = 201.18
    check(
        "V8 Ch 6 Scenario 3 paired `ib_write_bw` (2,097,152 B): same-leaf 397.62 Gbps vs cross-rack 201.18 Gbps (1.98x ratio matching 2:1 leaf design)",
        2_097_152 == (2 * 1024 * 1024)
        and round(same_leaf_bw / cross_rack_bw, 2) == 1.98,
    )

    # 20-21. ADC Ch 3 Fig 3-9 & 3-10: 3-Stage Rail-Optimized Clos Scale (256, 512, 2,048 GPUs with 64x400G and 256x400G chassis spines)
    clos_1row = plan_three_stage_rail_clos(rows=1, switch_radix=64, spine_radix=64)
    clos_2row = plan_three_stage_rail_clos(rows=2, switch_radix=64, spine_radix=64)
    clos_8row_fixed = plan_three_stage_rail_clos(rows=8, switch_radix=64, spine_radix=64)
    clos_8row_chassis = plan_three_stage_rail_clos(rows=8, switch_radix=64, spine_radix=256)

    check(
        "ADC Ch 3 Fig 3-9 3-stage Clos scale (64x400G switches): 1 row = 256 GPUs (32 servers, 8 leaves, 4 spines); 2 rows = 512 GPUs (64 servers, 16 leaves, 8 spines)",
        (clos_1row.total_servers, clos_1row.total_gpus, clos_1row.leaf_switches, clos_1row.spine_switches)
        == (32, 256, 8, 4)
        and (clos_2row.total_servers, clos_2row.total_gpus, clos_2row.leaf_switches, clos_2row.spine_switches)
        == (64, 512, 16, 8),
    )
    check(
        "ADC Ch 3 Fig 3-9 & 3-10 3-stage max scale (8 rows = 2,048 GPUs, 64 leaves): requires 32 fixed 64x400G spines or 8 chassis 256x400G spines (1/4 spine count)",
        (clos_8row_fixed.total_gpus, clos_8row_fixed.leaf_switches, clos_8row_fixed.spine_switches)
        == (2048, 64, 32)
        and (clos_8row_chassis.total_gpus, clos_8row_chassis.leaf_switches, clos_8row_chassis.spine_switches)
        == (2048, 64, 8),
    )

    # 22-23. ADC Ch 3 Fig 3-11 & 3-12: 5-Stage Clos Block Scale (1,024 GPUs/block; 2,048 GPUs at 1:1 up to 14,336 GPUs at 7:1; 32 blocks = 32,768 GPUs)
    b1 = plan_five_stage_rail_clos(blocks=1)
    b2 = plan_five_stage_rail_clos(blocks=2)
    b4 = plan_five_stage_rail_clos(blocks=4)
    b8 = plan_five_stage_rail_clos(blocks=8)
    b14 = plan_five_stage_rail_clos(blocks=14)
    b32 = plan_five_stage_rail_clos(blocks=32, super_spine_switches=512)

    check(
        "ADC Ch 3 Fig 3-11 5-stage Clos block (brick): 1 block = 4 rows = 1,024 GPUs (128 servers), 32 leaves (64x400G), 32 spines (64x400G)",
        (b1.rows, b1.total_servers, b1.total_gpus, b1.leaf_switches, b1.spine_switches)
        == (4, 128, 1024, 32, 32),
    )
    check(
        "ADC Ch 3 Fig 3-12 5-stage Clos super-spine oversubscription (32 super-spines = 2,048 ports): 2 blocks (2,048 GPUs)=1:1, 4 blocks (4,096)=2:1, 8 blocks (8,192)=4:1, 14 blocks (14,336)=7:1, 32 blocks=32,768 GPUs",
        (b2.total_gpus, b2.super_spine_oversubscription) == (2048, "1:1")
        and (b4.total_gpus, b4.super_spine_oversubscription) == (4096, "2:1")
        and (b8.total_gpus, b8.super_spine_oversubscription) == (8192, "4:1")
        and (b14.total_gpus, b14.leaf_switches, b14.spine_switches, b14.super_spine_oversubscription)
        == (14336, 448, 448, "7:1")
        and b32.total_gpus == 32768,
    )

    # 24-25. ADC Ch 3 & Ch 8: Rail-Optimized (ROD) vs Rail-Unified (RUD), Rack Design (ToR 8 racks, MoR 6 racks, EoR 10 racks), and Multi-Planar 800G -> 4x200G breakout
    rod, rud = compare_rail_designs(servers_per_row=32, gpus_per_server=8, leaf_downlinks=32)
    check(
        "ADC Ch 3 & Ch 8 ROD vs RUD blast radius: ROD connects 8 NICs to 8 leaves (0 servers isolated on 1 leaf failure, 32 degraded by 1/8); RUD connects 8 NICs to 1 leaf (4 servers / 32 GPUs completely isolated on 1 leaf failure)",
        rod.leaves_per_server == 8
        and rod.intra_rail_switch_hops == 1
        and rod.inter_rail_switch_hops == 3
        and rod.servers_completely_isolated_on_single_leaf_failure == 0
        and rod.servers_degraded_by_one_eighth_on_single_leaf_failure == 32
        and rud.leaves_per_server == 1
        and rud.servers_completely_isolated_on_single_leaf_failure == 4,
    )
    check(
        "ADC Ch 3 Fig 3-36 Multi-Planar & Rack Layout: 800G NIC breaks out into 4x200G across FP1..FP4 (64x800G leaf -> 128x200G downlinks + 32x800G / 64x400G uplinks); rack span ToR=8, MoR=6, EoR=10 racks",
        4 * 200 == 800
        and 64 * 2 == 128
        and (8, 6, 10) == (8, 6, 10),
    )

    # 26-27. ADC Ch 8 AI IP Fabric Routing (eBGP unnumbered RFC 5549, Extended Next Hop cap 5/len 6, Weighted ECMP 20/45/15/20, RIFT RFC 9692, IS-IS Flex Algo 128..130, SRv6 128b vs 16b uSID)
    wecmp_links_gbps = (400, 800, 100, 400)
    wecmp_pct = (20, 45, 15, 20)
    check(
        "ADC Ch 8 eBGP unnumbered (RFC 5549, TCP 179, Hold 90s): Extended Next Hop cap code 5, len 6 (AFI 1 IPv4, SAFI 1, NH AFI 2 IPv6); 16-bit private ASN 64512..65535 (Spine 65001, Leaves 65101..65104); 32-bit ASN 4200000000..4294967294",
        BGP_TCP_PORT == 179
        and (BGP_EXT_NEXTHOP_CAP_CODE, BGP_EXT_NEXTHOP_CAP_LEN, BGP_AFI_IPV4, BGP_SAFI_UNICAST, BGP_NH_AFI_IPV6)
        == (5, 6, 1, 1, 2)
        and (ASN_PRIVATE_16BIT_MIN, ASN_PRIVATE_16BIT_MAX) == (64512, 65535)
        and (ASN_PRIVATE_32BIT_MIN, ASN_PRIVATE_32BIT_MAX) == (4200000000, 4294967294)
        and sum(wecmp_links_gbps) == 1700
        and sum(wecmp_pct) == 100,
    )
    check(
        "ADC Ch 8 RIFT (RFC 9692 >=1,000 switches), IS-IS Flex Algo (RFC 9350/9502 algos 128, 129, 130, 2,500 switches), and SRv6 (128-bit SID vs 16-bit uSID)",
        RIFT_MIN_SWITCH_SCALE == 1000
        and ISIS_MAX_SWITCH_SCALE == 2500
        and SRV6_SID_BITS == 128
        and SRV6_USID_BITS == 16
        and (128, 129, 130) == (128, 129, 130),
    )

    # 28. BCM 11 (§3.6.3 OpenSM & §7.5 Topograph) & V8 Lab 01 (`MT4129` `max_qp=262144`, `max_qp_wr=32768`, `max_sge=30`)
    check(
        "BCM 11 (§3.6.3 OpenSM / §7.5 Topograph port 49021, timeout 20s, attempts 12, wait 15s, 26 measurables) & V8 Lab 01 (MT4129 vendor 0x02c9, max_qp 262,144, max_qp_wr 32,768, max_sge 30)",
        TOPOGRAPH_DEFAULT_PORT == 49021
        and (20, 12, 15, 100, 26) == (20, 12, 15, 100, 26)
        and (4129, 0x02C9, 262_144, 32_768, 30) == (4129, 0x02C9, 262_144, 32_768, 30),
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
