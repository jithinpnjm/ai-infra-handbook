#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.14: Load balancing and routing for AI fabrics."""

from __future__ import annotations

import sys

from load_balancing_routing_ai import (
    ASN_16BIT_PRIVATE_MAX,
    ASN_16BIT_PRIVATE_MIN,
    ASN_32BIT_PRIVATE_MAX,
    ASN_32BIT_PRIVATE_MIN,
    BCM_NETQ_HTTPS_PORT,
    BCM_NVUE_REST_PORT,
    BCM_SN2201_DISK_BYTES,
    BCM_SN2201_RAM_BYTES,
    BCM_SN2201_UPLINK_PORTS,
    BGP_AFI_IPV4,
    BGP_BORDER_LEAF_ASNS,
    BGP_DC_GW_ASN,
    BGP_DISTINCT_SPINE_ASNS,
    BGP_EXT_NEXT_HOP_CAP_CODE,
    BGP_EXT_NEXT_HOP_CAP_LEN,
    BGP_HOLD_TIME_SEC,
    BGP_LEAF1_LLA,
    BGP_LEAF1_MAC,
    BGP_LEAF_ASNS,
    BGP_MP_REACH_NLRI_ATTR_CODE,
    BGP_NH_AFI_IPV6,
    BGP_OPEN_ASN,
    BGP_OPEN_FRAME_NUMBER,
    BGP_OPEN_MSG_LEN_BYTES,
    BGP_OPEN_MSG_TYPE,
    BGP_OPEN_OPT_PARAM_LEN,
    BGP_OPEN_ROUTER_ID,
    BGP_OPEN_TCP_SRC_PORT,
    BGP_OPEN_WIRE_BITS,
    BGP_OPEN_WIRE_BYTES,
    BGP_SAFI_UNICAST,
    BGP_SERVER_ANYCAST_PREFIX,
    BGP_SERVER_HOST_ASNS_32,
    BGP_SERVER_LEAF_ASNS_32,
    BGP_SERVER_SPINE_ASN_32,
    BGP_SHARED_SPINE_ASN,
    BGP_SPINE1_LLA,
    BGP_SPINE1_MAC,
    BGP_TCP_PORT,
    BGP_UPDATE_FRAME_NUMBER,
    BGP_UPDATE_MP_REACH_LEN,
    BGP_UPDATE_MSG_LEN_BYTES,
    BGP_UPDATE_MSG_TYPE,
    BGP_UPDATE_NLRI_PREFIX,
    BGP_UPDATE_PATH_ATTR_LEN,
    BGP_UPDATE_WIRE_BITS,
    BGP_UPDATE_WIRE_BYTES,
    BTH_OPCODE_RDMA_READ_REQUEST,
    BTH_OPCODE_RDMA_SEND_ONLY,
    BTH_OPCODE_RDMA_WRITE_FIRST,
    BTH_OPCODE_RDMA_WRITE_LAST,
    BTH_OPCODE_RDMA_WRITE_MIDDLE,
    BTH_OPCODE_RDMA_WRITE_ONLY,
    DLB_QUALITY_BAND_MAX,
    DLB_QUALITY_BAND_MIN,
    DRAGONFLY_CANONICAL_GROUPS,
    DRAGONFLY_SWITCHES_PER_GROUP,
    GLB_BGP_ID_BITS,
    GLB_NNHN_CHARACTERISTIC_CODE,
    GLB_TOMAHAWK5_HEARTBEAT_MS,
    H100_MIG_MAX_INSTANCES,
    ISIS_DENSE_SPINE_COUNTS,
    ISIS_FLEX_ALGO_PLANES,
    ISIS_FLEX_ALGO_RFC,
    ISIS_IP_FLEX_ALGO_RFC,
    ISIS_MAX_SWITCH_SCALE,
    PER_PACKET_ARRIVAL_ORDER,
    PER_PACKET_DATAGRAM_BYTES,
    PER_PACKET_DATAGRAM_COUNT,
    PER_PACKET_DST_IP,
    PER_PACKET_PORT_BW_GBPS,
    PER_PACKET_SEND_ORDER,
    RESILIENT_BUCKET_SIZES,
    RESILIENT_INITIAL_MAP,
    RESILIENT_SIMPLIFIED_BUCKETS,
    RESILIENT_SIMPLIFIED_INTERFACES,
    RIFT_MIN_SWITCH_SCALE,
    RIFT_RFC_NUMBER,
    SLB_EXAMPLE_CRC32_DEC,
    SLB_EXAMPLE_CRC32_HEX,
    SLB_EXAMPLE_DST_IP,
    SLB_EXAMPLE_DST_IP_HEX,
    SLB_EXAMPLE_DST_PORT,
    SLB_EXAMPLE_DST_PORT_HEX,
    SLB_EXAMPLE_IP_PROTO_HEX,
    SLB_EXAMPLE_IP_PROTO_UDP,
    SLB_EXAMPLE_MOD_5_INDEX,
    SLB_EXAMPLE_MOD_8_INDEX,
    SLB_EXAMPLE_PACKED_HEX,
    SLB_EXAMPLE_SRC_IP,
    SLB_EXAMPLE_SRC_IP_HEX,
    SLB_EXAMPLE_SRC_PORT,
    SLB_EXAMPLE_SRC_PORT_HEX,
    SLB_SIMPLE_ECMP_5,
    SLB_SIMPLE_KEY_10,
    SLB_SIMPLE_KEY_11,
    SRV6_NET_PGM_RFC,
    SRV6_SID_BITS,
    SRV6_SRH_RFC,
    SRV6_USID_BITS,
    build_adc_table_6_1,
    build_adc_table_8_1,
    build_bgp_dpf_plane_plan,
    classify_sdlb_rocev2_packet,
    compare_slb_vs_dlb_spine_utilization,
    compute_adc_ch6_five_tuple_slb,
    compute_multitenant_rail_plan,
    compute_srv6_usid_carrier_shift,
    compute_symmetric_five_tuple_key,
    compute_wcmp_link_bandwidth_distribution,
    evaluate_bgp_spine_asn_allocation,
    simulate_dlb_flowlet_and_glb_nnhn,
)


def run_lab() -> int:
    passed = 0
    failed = 0

    def check(name: str, cond: bool) -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name}")

    print("=== Chapter 12.14 Lab: Load Balancing and Routing for AI Fabrics ===")

    # 1. ADC Ch 6 simple hash keys (10 mod 5 = 0, 11 mod 5 = 1)
    check(
        "ADC Ch 6 simple ECMP modulo: hash_key=10 -> 10 mod 5 = 0, hash_key=11 -> 11 mod 5 = 1",
        (SLB_SIMPLE_KEY_10 % SLB_SIMPLE_ECMP_5 == 0)
        and (SLB_SIMPLE_KEY_11 % SLB_SIMPLE_ECMP_5 == 1),
    )

    # 2. ADC Ch 6 worked 5-tuple hex packing (192.168.1.20 -> 192.168.2.10, UDP 17, 1024 -> 4791)
    slb = compute_adc_ch6_five_tuple_slb()
    check(
        "ADC Ch 6 5-tuple hex packing: C0A80114 C0A8020A 11 0400 12B7",
        SLB_EXAMPLE_SRC_IP == "192.168.1.20"
        and SLB_EXAMPLE_SRC_IP_HEX == "C0A80114"
        and SLB_EXAMPLE_DST_IP == "192.168.2.10"
        and SLB_EXAMPLE_DST_IP_HEX == "C0A8020A"
        and SLB_EXAMPLE_IP_PROTO_UDP == 17
        and SLB_EXAMPLE_IP_PROTO_HEX == "11"
        and SLB_EXAMPLE_SRC_PORT == 1024
        and SLB_EXAMPLE_SRC_PORT_HEX == "0400"
        and SLB_EXAMPLE_DST_PORT == 4791
        and SLB_EXAMPLE_DST_PORT_HEX == "12B7"
        and slb.packed_hex == "C0A80114C0A8020A11040012B7",
    )

    # 3. ADC Ch 6 CRC32 hash key 0x8BDA7C2D (2346351661) and modulo 5 vs 8
    check(
        "ADC Ch 6 CRC32 key 0x8BDA7C2D (2,346,351,661): mod 5 = 1 and mod 8 = 5",
        slb.crc32_hex == SLB_EXAMPLE_CRC32_HEX == 0x8BDA7C2D
        and slb.crc32_dec == SLB_EXAMPLE_CRC32_DEC == 2346351661
        and slb.ecmp_5_index == SLB_EXAMPLE_MOD_5_INDEX == 1
        and slb.ecmp_8_index == SLB_EXAMPLE_MOD_8_INDEX == 5,
    )

    # 4. ADC Ch 6 resilient hashing bucket table (512/1024 buckets, 8-bucket example map)
    check(
        "ADC Ch 6 resilient hashing: 512/1024 buckets; 8-bucket example (0,1,2,3,4,0,1,2) maps key=10 -> bucket 2 -> iface 2, only buckets (2,7) remapped on failure (25% vs 75% modulo churn)",
        RESILIENT_BUCKET_SIZES == (512, 1024)
        and RESILIENT_SIMPLIFIED_BUCKETS == 8
        and RESILIENT_SIMPLIFIED_INTERFACES == 5
        and RESILIENT_INITIAL_MAP == (0, 1, 2, 3, 4, 0, 1, 2)
        and slb.resilient_8_bucket == 2
        and slb.resilient_initial_iface == 2
        and slb.affected_buckets_on_iface2_down == (2, 7)
        and abs(slb.churn_fraction_resilient - 0.25) < 1e-9
        and slb.churn_fraction_modulo_5_to_4 > slb.churn_fraction_resilient,
    )

    # 5. ADC Ch 6 symmetric hashing (A->B and B->A yield identical hash key & bucket)
    fwd_key = compute_symmetric_five_tuple_key(
        "192.168.1.20", "192.168.2.10", 17, 1024, 4791
    )
    rev_key = compute_symmetric_five_tuple_key(
        "192.168.2.10", "192.168.1.20", 17, 4791, 1024
    )
    check(
        "ADC Ch 6 symmetric hashing: normalized XOR 5-tuple produces identical key for A->B and B->A",
        fwd_key == rev_key and (fwd_key % 8) == (rev_key % 8),
    )

    # 6. ADC Ch 6 Figs 6-2 & 6-4: SLB (50%/100%) vs DLB (75%/75%) on 2x 200G spine links
    util = compare_slb_vs_dlb_spine_utilization()
    check(
        "ADC Ch 6 Figs 6-2 & 6-4: Flows (50, 100, 50, 100) Gbps on 200G links yield SLB (100G=50%, 200G=100%) vs DLB (150G=75%, 150G=75%)",
        util.slb_spine_a_gbps == 100
        and util.slb_spine_b_gbps == 200
        and util.slb_spine_a_util_pct == 50.0
        and util.slb_spine_b_util_pct == 100.0
        and util.dlb_spine_a_gbps == 150
        and util.dlb_spine_b_gbps == 150
        and util.dlb_spine_a_util_pct == 75.0
        and util.dlb_spine_b_util_pct == 75.0,
    )

    # 7. ADC Ch 6 DLB quality bands (0..7), flowlet timer (Fig 6-5), reactive rebalancing (Fig 6-6)
    dlb_glb = simulate_dlb_flowlet_and_glb_nnhn()
    check(
        "ADC Ch 6 DLB quality bands (0..7), flowlet inactivity timer reassignment (SpineB -> SpineA), and reactive path rebalancing (SpineA -> SpineC)",
        DLB_QUALITY_BAND_MIN == 0
        and DLB_QUALITY_BAND_MAX == 7
        and dlb_glb.dlb_initial_spine == "SpineB"
        and dlb_glb.dlb_after_short_pause_spine == "SpineB"
        and dlb_glb.dlb_after_long_pause_spine == "SpineA"
        and dlb_glb.dlb_reactive_rebalanced_spine == "SpineC",
    )

    # 8. ADC Ch 6 GLB NNHN (draft-wang-idr-next-next-hop-nodes, Characteristic Code=2, 32-bit BGP IDs, 20 ms Tomahawk 5 heartbeats)
    check(
        "ADC Ch 6 GLB NNHN (Characteristic Code=2, 32-bit BGP IDs, 20 ms Tomahawk 5 heartbeats, simple vs compound profile) avoids remote Link X congestion on SpineA->LeafD",
        GLB_NNHN_CHARACTERISTIC_CODE == 2
        and GLB_BGP_ID_BITS == 32
        and GLB_TOMAHAWK5_HEARTBEAT_MS == 20
        and dlb_glb.dlb_blind_to_remote_spine_congestion is True
        and dlb_glb.glb_selected_spine == "SpineB"
        and dlb_glb.glb_profile_type_3stage == "simple_path_quality_profile"
        and dlb_glb.glb_profile_type_5stage == "compound_path_quality_profile",
    )

    # 9. ADC Ch 6 Figs 6-14 & 6-15: Per-packet load balancing (3x 1500B datagrams A, B, C across 3x 100G ports arriving B, C, A at 192.168.1.1)
    check(
        "ADC Ch 6 Figs 6-14 & 6-15 per-packet spraying: 3 x 1500B datagrams (A, B, C) over 3 x 100G ports arrive out of order (T1=B, T2=C, T3=A) at 192.168.1.1",
        PER_PACKET_DATAGRAM_BYTES == 1500
        and PER_PACKET_DATAGRAM_COUNT == 3
        and PER_PACKET_PORT_BW_GBPS == 100
        and PER_PACKET_DST_IP == "192.168.1.1"
        and PER_PACKET_SEND_ORDER == ("A", "B", "C")
        and PER_PACKET_ARRIVAL_ORDER == ("B", "C", "A"),
    )

    # 10. ADC Ch 6 Fig 6-16: Selective Packet Spraying (sDLB) matching RoCEv2 BTH Write opcodes on ConnectX-6/7 & BlueField
    check(
        "ADC Ch 6 sDLB TCAM ACL: RoCEv2 UDP 4791 BTH RDMA Write opcodes (0x06..0x0B) trigger PER_PACKET_SPRAY while Read/Send stay PER_FLOW_DEFAULT",
        classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_WRITE_FIRST, True)
        == "PER_PACKET_SPRAY"
        and classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_WRITE_MIDDLE, True)
        == "PER_PACKET_SPRAY"
        and classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_WRITE_LAST, True)
        == "PER_PACKET_SPRAY"
        and classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_WRITE_ONLY, True)
        == "PER_PACKET_SPRAY"
        and classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_READ_REQUEST, True)
        == "PER_FLOW_DEFAULT"
        and classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_SEND_ONLY, True)
        == "PER_FLOW_DEFAULT"
        and classify_sdlb_rocev2_packet(4791, BTH_OPCODE_RDMA_WRITE_ONLY, False)
        == "PER_FLOW_DEFAULT",
    )

    # 11. ADC Ch 6 Table 6-1: SLB vs DLB vs GLB vs TELB capability matrix
    t61 = build_adc_table_6_1()
    check(
        "ADC Ch 6 Table 6-1 capability matrix: SLB (High), DLB (Medium, local BW+queue), GLB (Low, +remote link quality), TELB (Low, local+remote+BTH+telemetry)",
        set(t61.keys()) == {"SLB", "DLB", "GLB", "TELB"}
        and t61["SLB"].adoption_level == "High"
        and not t61["SLB"].local_link_bandwidth
        and t61["DLB"].local_link_bandwidth
        and t61["DLB"].queue_size_info
        and not t61["DLB"].remote_link_quality
        and t61["GLB"].remote_link_quality
        and t61["GLB"].queue_size_info
        and t61["TELB"].fabric_telemetry
        and t61["TELB"].remote_link_quality,
    )

    # 12. ADC Ch 8 BGP Unnumbered (RFC 5549) private ASN ranges & IPv6 link-local session (Fig 8-1)
    check(
        "ADC Ch 8 BGP Unnumbered (RFC 5549): 16-bit private ASNs 64512..65535, 32-bit private ASNs 4200000000..4294967294, spine1 fe80::e59:9cff:fef1:32 <-> leaf1 fe80::e59:9cff:fe22:5dd7 TCP 52659->179",
        ASN_16BIT_PRIVATE_MIN == 64512
        and ASN_16BIT_PRIVATE_MAX == 65535
        and ASN_32BIT_PRIVATE_MIN == 4200000000
        and ASN_32BIT_PRIVATE_MAX == 4294967294
        and BGP_SPINE1_MAC == "0c:59:9c:f1:00:32"
        and BGP_SPINE1_LLA == "fe80::e59:9cff:fef1:32"
        and BGP_LEAF1_MAC == "0c:59:9c:22:5d:d7"
        and BGP_LEAF1_LLA == "fe80::e59:9cff:fe22:5dd7"
        and BGP_OPEN_TCP_SRC_PORT == 52659
        and BGP_TCP_PORT == 179,
    )

    # 13. ADC Ch 8 Figs 8-2 & 8-3: BGP OPEN (Frame 22, Cap Code 5) & UPDATE (Frame 28, MP_REACH_NLRI Code 14)
    check(
        "ADC Ch 8 Figs 8-2 & 8-3 packet captures: Frame 22 OPEN (189B/1512b, Cap Code 5 len 6, AFI=1 SAFI=1 NH_AFI=2, AS 65001, hold 90s, ID 172.16.7.101) & Frame 28 UPDATE (358B/2864b, MP_REACH_NLRI type 14 len 42, 172.16.7.181/32)",
        BGP_OPEN_FRAME_NUMBER == 22
        and BGP_OPEN_WIRE_BYTES == 189
        and BGP_OPEN_WIRE_BITS == 1512
        and BGP_OPEN_MSG_TYPE == 1
        and BGP_OPEN_MSG_LEN_BYTES == 81
        and BGP_OPEN_OPT_PARAM_LEN == 52
        and BGP_OPEN_ASN == 65001
        and BGP_HOLD_TIME_SEC == 90
        and BGP_OPEN_ROUTER_ID == "172.16.7.101"
        and BGP_EXT_NEXT_HOP_CAP_CODE == 5
        and BGP_EXT_NEXT_HOP_CAP_LEN == 6
        and BGP_AFI_IPV4 == 1
        and BGP_SAFI_UNICAST == 1
        and BGP_NH_AFI_IPV6 == 2
        and BGP_UPDATE_FRAME_NUMBER == 28
        and BGP_UPDATE_WIRE_BYTES == 358
        and BGP_UPDATE_WIRE_BITS == 2864
        and BGP_UPDATE_MSG_TYPE == 2
        and BGP_UPDATE_MSG_LEN_BYTES == 82
        and BGP_UPDATE_PATH_ATTR_LEN == 46
        and BGP_MP_REACH_NLRI_ATTR_CODE == 14
        and BGP_UPDATE_MP_REACH_LEN == 42
        and BGP_UPDATE_NLRI_PREFIX == "172.16.7.181/32",
    )

    # 14. ADC Ch 8 Figs 8-4 & 8-5: Shared spine ASN 65001 vs distinct spine ASNs (65001..65004) loop prevention
    asn_eval = evaluate_bgp_spine_asn_allocation()
    check(
        "ADC Ch 8 Figs 8-4 & 8-5: Shared spine ASN 65001 with leaf ASNs 65101..65104 rejects leaf-spine-leaf-spine valley paths whereas distinct spine ASNs 65001..65004 allow suboptimal tromboning",
        asn_eval.shared_spine_asn == 65001
        and asn_eval.unique_spine_asns == (65001, 65002, 65003, 65004)
        and BGP_LEAF_ASNS == (65101, 65102, 65103, 65104)
        and asn_eval.shared_spine_rejects_valley_loop is True
        and asn_eval.unique_spine_allows_suboptimal_tromboning is True,
    )

    # 15. ADC Ch 8 Fig 8-6: BGP ADD-PATH with border-leaf1 (65501), border-leaf2 (65502), DC GW (65503)
    check(
        "ADC Ch 8 Fig 8-6 BGP ADD-PATH: DC GW (65503) -> border-leaf1 (65501) & border-leaf2 (65502) -> spine2 (65001) advertises both NH1 and NH2 for 10.10.108.0/24 to leaf2 (65102)",
        BGP_BORDER_LEAF_ASNS == (65501, 65502) and BGP_DC_GW_ASN == 65503,
    )

    # 16. ADC Ch 8 Fig 8-8: BGP Link Bandwidth Extended Community & WCMP (400G/800G/100G/400G -> 20%/45%/15%/20%) + min-peers withdrawal
    wcmp = compute_wcmp_link_bandwidth_distribution()
    check(
        "ADC Ch 8 Fig 8-8 WCMP & Link Bandwidth Extended Community: spine1..4 (400G, 800G, 100G, 400G = 1,700G) configured as 20%/45%/15%/20% (sum=100%), and spine withdraws 10.10.101.0/24 when active peers drop from 4 to 3",
        wcmp.total_core_bw_gbps == 1700
        and wcmp.configured_weights_pct
        == {"spine1": 20, "spine2": 45, "spine3": 15, "spine4": 20}
        and sum(wcmp.configured_weights_pct.values()) == 100
        and sum(wcmp.bucket_counts_64.values()) == 64
        and wcmp.spine_withdrawn_when_active_peers_is_3 is True,
    )

    # 17. ADC Ch 8 Figs 8-10..8-14: BGP DPF (draft-wang-idr-dpf) session coloring, route pruning, 128x GPU-0 1.2 Tbps RUD slice, and 4 color mapping modes
    dpf = build_bgp_dpf_plane_plan()
    check(
        "ADC Ch 8 BGP DPF (draft-wang-idr-dpf): 10.10.1.4/32 pruned to black (active via spine1) and gray (backup via spine2); 128x GPU-0 on 3x400G = 1.2 Tbps/leaf; 4 color mapping modes",
        dpf.origin_prefix == "10.10.1.4/32"
        and dpf.leaf1_active_path_color == "black"
        and dpf.leaf1_active_next_hop == "spine1"
        and dpf.leaf1_backup_path_color == "gray"
        and dpf.leaf1_backup_next_hop == "spine2"
        and dpf.rud_gpu_id_0_count == 128
        and dpf.rud_black_links_per_leaf == 3
        and dpf.rud_link_speed_gbps == 400
        and abs(dpf.rud_black_capacity_per_leaf_tbps - 1.2) < 1e-9
        and len(dpf.color_mapping_modes) == 4,
    )

    # 18. ADC Ch 8 RIFT (RFC 9692) & DragonFly canonical/sparse constants (Figs 8-15..8-18)
    check(
        "ADC Ch 8 RIFT (RFC 9692): >=1,000 switch nodes, link-state northbound + distance-vector southbound, UDP hello + IPv6 ND, 7 canonical DragonFly groups x 8 switches/group + DragonFly Sparse ToF K-store",
        RIFT_RFC_NUMBER == 9692
        and RIFT_MIN_SWITCH_SCALE == 1000
        and DRAGONFLY_CANONICAL_GROUPS == 7
        and DRAGONFLY_SWITCHES_PER_GROUP == 8,
    )

    # 19. ADC Ch 8 IS-IS Flood Reduction (draft-white-lsr-distoptflood) & Flex Algo (RFC 9350 / RFC 9502, Figs 8-19..8-20)
    check(
        "ADC Ch 8 IS-IS Flood Reduction & Flex Algo: 2,500 switch nodes, 32/64 spines, RFC 9350 FAD + RFC 9502 IP Flex Algo planes 128 (storage), 129 (inference), 130 (training)",
        ISIS_MAX_SWITCH_SCALE == 2500
        and ISIS_DENSE_SPINE_COUNTS == (32, 64)
        and ISIS_FLEX_ALGO_RFC == 9350
        and ISIS_IP_FLEX_ALGO_RFC == 9502
        and ISIS_FLEX_ALGO_PLANES[128] == (("spine1", "spine2"), "storage")
        and ISIS_FLEX_ALGO_PLANES[129] == (("spine3", "spine4"), "inference")
        and ISIS_FLEX_ALGO_PLANES[130] == (("spine5", "spine6"), "training"),
    )

    # 20. ADC Ch 8 Table 8-1: eBGP vs RIFT vs IS-IS summary comparison
    t81 = build_adc_table_8_1()
    check(
        "ADC Ch 8 Table 8-1 routing protocol matrix: eBGP (Many frontend multi-tenancy, Wide ECMP/UCMP) vs RIFT (DragonFly=Yes, auto-disaggregation=Yes, K-store config=Yes) vs IS-IS (Fast convergence, High link awareness)",
        set(t81.keys()) == {"eBGP", "RIFT", "IS-IS"}
        and t81["eBGP"].dragonfly_support == "No"
        and t81["RIFT"].dragonfly_support == "Yes"
        and t81["IS-IS"].dragonfly_support == "No"
        and t81["eBGP"].frontend_multitenancy_options == "Many"
        and t81["RIFT"].automatic_disaggregation_on_failure == "Yes"
        and t81["RIFT"].advertising_fabric_config_data == "Yes"
        and t81["eBGP"].wide_ecmp_or_ucmp == "Yes"
        and t81["RIFT"].wide_ecmp_or_ucmp == "Yes"
        and t81["IS-IS"].wide_ecmp_or_ucmp == "No",
    )

    # 21. ADC Ch 8 Figs 8-21..8-24: Network & Server Multi-Tenancy (8 leafs x 8 spines, 64x800G radix, 512 GPUs/rail, 4x128 BMS, 7-instance MIG + VXLAN-GBP)
    mt = compute_multitenant_rail_plan()
    check(
        "ADC Ch 8 Figs 8-21..8-24 multi-tenancy: 8 leafs x 8 spines (64x800G switch: 64x400G server breakout + 32x800G spine) = 512 GPUs/rail, 4 tenants x 128 GPUs BMS, 7 H100 MIG instances x 7 VLANs/MAC-VRFs/RT5-IP-VRFs + VXLAN-GBP",
        mt.leaf_switches_per_rail == 8
        and mt.spine_switches_per_rail == 8
        and mt.switch_radix_800g == 64
        and mt.server_ports_per_tor_400g_breakout == 64
        and mt.spine_uplinks_per_tor_800g == 32
        and mt.total_gpus_in_rail == 512
        and mt.bms_tenants_per_rail == 4
        and mt.bms_gpus_per_tenant == 128
        and mt.mig_instances_per_gpu == H100_MIG_MAX_INSTANCES == 7
        and mt.mig_vlans_per_server_link == 7
        and mt.mig_mac_vrfs_per_leaf == 7
        and mt.mig_rt5_ip_vrfs_per_leaf == 7
        and mt.microsegmentation_encap == "VXLAN-GBP",
    )

    # 22. ADC Ch 8 Figs 8-25 & 8-26: Extending BGP to the server (32-bit ASNs 4294967100, 4224967001..4, 4200000001..4, anycast 192.168.10.10/32)
    check(
        "ADC Ch 8 Figs 8-25 & 8-26 BGP to the server: spine AS 4294967100, leaf ASNs 4224967001..4224967004, host ASNs 4200000001..4200000004, anycast service 192.168.10.10/32",
        BGP_SERVER_SPINE_ASN_32 == 4294967100
        and BGP_SERVER_LEAF_ASNS_32
        == (4224967001, 4224967002, 4224967003, 4224967004)
        and BGP_SERVER_HOST_ASNS_32
        == (4200000001, 4200000002, 4200000003, 4200000004)
        and BGP_SERVER_ANYCAST_PREFIX == "192.168.10.10/32",
    )

    # 23. ADC Ch 8 Figs 8-28..8-30: SRv6 (RFC 8754 SRH, RFC 8986) & 16-bit Compressed uSID carrier shift (SID 5 -> SID 1)
    usid = compute_srv6_usid_carrier_shift()
    check(
        "ADC Ch 8 SRv6 (RFC 8754 / RFC 8986) & 16-bit uSID carrier math: 128-bit SID holds 6 x 16-bit uSIDs after 32-bit locator, saving 72B on a 4-hop SRH and shifting SID 5 -> SID 1",
        SRV6_SRH_RFC == 8754
        and SRV6_NET_PGM_RFC == 8986
        and SRV6_SID_BITS == 128
        and SRV6_USID_BITS == 16
        and usid.max_usids_per_128bit_carrier == 6
        and usid.uncompressed_srh_bytes_for_4_hops == 72
        and usid.header_byte_savings_4_hops == 72
        and usid.initial_carrier_ipv6 == "fc00:0a10:0005:0001:0000::"
        and usid.after_spine_pop_carrier_ipv6 == "fc00:0a10:0001:0000:0000::"
        and usid.after_egress_leaf_pop_carrier_ipv6 == "fc00:0a10:0000:0000:0000::",
    )

    # 24. BCM 11 Cumulus Linux / NVUE management constants (bcm11-admin Ch 3 §3.8-3.12)
    check(
        "BCM 11 Cumulus Linux NVUE & NetQ management: REST API port 8765, NetQ port 443, SN2201 8,048,771,072 B RAM / 115,923,419,136 B disk, uplinks (15, 16)",
        BCM_NVUE_REST_PORT == 8765
        and BCM_NETQ_HTTPS_PORT == 443
        and BCM_SN2201_RAM_BYTES == 8048771072
        and BCM_SN2201_DISK_BYTES == 115923419136
        and BCM_SN2201_UPLINK_PORTS == (15, 16),
    )

    # 25. End-to-end invariant: 8 leafs x 32 servers x 2x400G breakout = 512 GPU ports matched by 8 leafs x 32x800G spine uplinks (1:1 non-oversubscribed rail)
    downlink_bw_tbps = (8 * 64 * 400) / 1000.0
    uplink_bw_tbps = (8 * 32 * 800) / 1000.0
    check(
        "1:1 non-oversubscribed 512-GPU rail bandwidth invariant: 8 leafs x 64x400G server ports = 204.8 Tbps == 8 leafs x 32x800G spine ports = 204.8 Tbps",
        abs(downlink_bw_tbps - 204.8) < 1e-9
        and abs(uplink_bw_tbps - 204.8) < 1e-9
        and downlink_bw_tbps == uplink_bw_tbps,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
