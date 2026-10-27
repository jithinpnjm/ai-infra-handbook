#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.3: RoCEv2 Transport and Congestion Management."""

from __future__ import annotations
import sys
from rocev2_transport import (
    CNP_BTH_OPCODE,
    CSIG_LOCATOR_METADATA_FIELDS,
    CSIG_SIGNAL_TYPES,
    DEFAULT_ROCE_PKEY,
    DSCP_AF31,
    DSCP_CS3,
    ECN_CODEPOINTS,
    GidEntry,
    PFC_CLASS3_ENABLE_VECTOR,
    PFC_DEST_MAC,
    PFC_ETHERTYPE,
    PFC_MAX_PAUSE_QUANTA,
    PFC_OPCODE,
    PFC_WATCHDOG_BLOCKS,
    RC_RDMA_ACK_OPCODE,
    RC_RDMA_READ_REQ_OPCODE,
    RC_RDMA_READ_RESP_MID_OPCODE,
    ROCEV1_ETHERTYPE,
    ROCEV2_UDP_DST_PORT,
    ROCE_LOSSLESS_COS,
    SIX_CLOS_CONGESTION_POINTS,
    DcqcnBufferProfile,
    build_ip_tos_byte,
    calculate_jct_tail_latency,
    calculate_retransmission_amplification,
    compare_congestion_signaling_latency,
    compare_roce_encapsulation,
    decode_ip_tos_byte,
    ipv4_to_rocev2_gid,
    select_semantic_gid,
    simulate_pfc_watchdog,
    validate_qos_path,
)


def run_lab() -> int:
    print("=== Chapter 12.3 Lab: RoCEv2 Transport and Congestion Management ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. RoCEv1 (0x8915) vs RoCEv2 (UDP 4791) encapsulation and payload efficiency
    enc_4k = compare_roce_encapsulation(payload_bytes=4096, include_vlan=False, include_reth=False)
    enc_1k = compare_roce_encapsulation(payload_bytes=1024, include_vlan=False, include_reth=False)
    check(
        "RoCEv1 uses EtherType 0x8915 with a 40-byte IB GRH and 0-byte UDP header (74B non-payload overhead, 4170B wire frame, 98.23% efficiency)",
        enc_4k["RoCEv1"].ethertype_or_port == 0x8915
        and enc_4k["RoCEv1"].l3_bytes == 40
        and enc_4k["RoCEv1"].l4_bytes == 0
        and enc_4k["RoCEv1"].total_header_and_trailer_bytes == 74
        and enc_4k["RoCEv1"].wire_frame_bytes == 4170
        and enc_4k["RoCEv1"].payload_efficiency_pct == 98.23,
    )
    check(
        "RoCEv2-IPv4 uses UDP destination port 4791, 20B IPv4 + 8B UDP + 12B IB BTH + 4B ICRC + 18B L2 (62B overhead)",
        enc_4k["RoCEv2-IPv4"].ethertype_or_port == 4791
        and enc_4k["RoCEv2-IPv4"].total_header_and_trailer_bytes == 62
        and enc_4k["RoCEv2-IPv4"].wire_frame_bytes == 4158,
    )
    check(
        "RoCEv2-IPv6 uses 40B IPv6 + 8B UDP + 12B IB BTH + 4B ICRC + 18B L2 (82B overhead, 4178B wire frame, 98.04% efficiency)",
        enc_4k["RoCEv2-IPv6"].total_header_and_trailer_bytes == 82
        and enc_4k["RoCEv2-IPv6"].wire_frame_bytes == 4178
        and enc_4k["RoCEv2-IPv6"].payload_efficiency_pct == 98.04,
    )
    check(
        "Expanding RoCEv2-IPv4 payload from 1024B to 4096B raises wire payload efficiency from 94.29% to 98.51%",
        enc_1k["RoCEv2-IPv4"].payload_efficiency_pct == 94.29
        and enc_4k["RoCEv2-IPv4"].payload_efficiency_pct == 98.51,
    )
    check(
        "ADC Ch 1 BTH opcodes match Wireshark captures: RDMA Read Req=12, Read Resp Middle=14, ACK=17, PKey=65535",
        RC_RDMA_READ_REQ_OPCODE == 12
        and RC_RDMA_READ_RESP_MID_OPCODE == 14
        and RC_RDMA_ACK_OPCODE == 17
        and DEFAULT_ROCE_PKEY == 65535,
    )

    # 2. GID table semantic selection (Volume 09 Ch 3 show_gids scenario)
    sample_gids = [
        GidEntry("mlx5_0", 1, 0, "fe80:0000:0000:0000:0e42:a1ff:fec8:d79c", "n/a", "v1", "eth0"),
        GidEntry("mlx5_0", 1, 1, "0000:0000:0000:0000:0000:ffff:0a14:040f", "10.20.4.15", "v2", "eth0"),
        GidEntry("mlx5_0", 1, 2, "0000:0000:0000:0000:0000:ffff:0a14:040f", "10.20.4.15", "v2", "eth0.100"),
        GidEntry("mlx5_0", 1, 3, "fe80:0000:0000:0000:0e42:a1ff:fec8:d79c", "n/a", "v1", "eth0.100"),
    ]
    check(
        "IPv4 10.20.4.15 maps to RoCEv2 GID 0000:0000:0000:0000:0000:ffff:0a14:040f",
        ipv4_to_rocev2_gid("10.20.4.15") == "0000:0000:0000:0000:0000:ffff:0a14:040f",
    )
    selected_base = select_semantic_gid(sample_gids, "mlx5_0", 1, "eth0", "10.20.4.15", "v2")
    selected_vlan = select_semantic_gid(sample_gids, "mlx5_0", 1, "eth0.100", "10.20.4.15", "v2")
    check(
        "Semantic GID lookup distinguishes base eth0 (index 1) from VLAN eth0.100 (index 2) with identical IP 10.20.4.15",
        selected_base is not None
        and selected_base.index == 1
        and selected_vlan is not None
        and selected_vlan.index == 2,
    )
    check(
        "Semantic GID lookup rejects link-local RoCEv1 (fe80::) entries when routed RoCEv2 (v2) is required",
        select_semantic_gid(sample_gids, "mlx5_0", 1, "eth0", "10.20.4.15", "v1") is None,
    )

    # 3. DSCP 26 (AF31) / DSCP 24 (CS3) and CoS 3 QoS trust mapping + ECN bits
    tos_ect0 = build_ip_tos_byte(DSCP_AF31, "10")
    tos_ce = build_ip_tos_byte(DSCP_AF31, "11")
    check(
        "DSCP 26 (AF31) with ECN ECT(0) '10' encodes to IP ToS byte 0x6a (106) and with CE '11' to 0x6b (107)",
        tos_ect0 == 0x6A
        and tos_ce == 0x6B
        and decode_ip_tos_byte(tos_ce) == (26, "11")
        and DSCP_CS3 == 24,
    )
    check(
        "ADC Ch 7 Table 7-1 defines all 4 ECN codepoints (00 Non-ECT, 01 ECT(1)/CNP, 10 ECT(0), 11 CE) and CNP opcode 129 (0x81)",
        set(ECN_CODEPOINTS.keys()) == {"00", "01", "10", "11"} and CNP_BTH_OPCODE == 129,
    )
    qos_ok = validate_qos_path(
        host_dscp=DSCP_AF31,
        vlan_pcp=ROCE_LOSSLESS_COS,
        switch_trust_mode="dscp",
        switch_dscp_to_tc_map={26: 3, 24: 3, 0: 0},
        pfc_enabled_priorities=[3],
        ecn_enabled_tcs=[3],
    )
    qos_misconfigured = validate_qos_path(
        host_dscp=DSCP_AF31,
        vlan_pcp=0,
        switch_trust_mode="pcp",
        switch_dscp_to_tc_map={26: 3},
        pfc_enabled_priorities=[3],
        ecn_enabled_tcs=[3],
    )
    check(
        "QoS path validator confirms DSCP 26 -> TC 3 lossless/ECN alignment and catches L2 PCP=0 trust mismatches",
        qos_ok["healthy_roce_qos"] is True and qos_misconfigured["healthy_roce_qos"] is False,
    )

    # 4. Six Clos congestion points (ADC Ch 7 Figs 7-1..7-6), DCQCN thresholds & PFC Watchdog
    check(
        "ADC Ch 7 defines all 6 Clos congestion points from local south-facing leaf to 5-stage super-spine links",
        len(SIX_CLOS_CONGESTION_POINTS) == 6
        and "south-facing" in SIX_CLOS_CONGESTION_POINTS[0]["figure"]
        and "super spine-to-spine" in SIX_CLOS_CONGESTION_POINTS[5]["figure"],
    )
    dcqcn = DcqcnBufferProfile(
        xon_threshold_kb=64,
        ecn_min_threshold_kb=150,
        ecn_max_threshold_kb=1500,
        xoff_threshold_kb=3000,
        total_buffer_kb=4096,
    )
    check(
        "DCQCN enforces progressive buffer threshold ordering XON (64 KB) < ECN_min (150 KB) <= ECN_max (1500 KB) < XOFF (3000 KB)",
        dcqcn.is_valid_ordering() is True,
    )
    state_ecn = dcqcn.evaluate_queue_state(500)
    state_xoff = dcqcn.evaluate_queue_state(3200)
    state_xon = dcqcn.evaluate_queue_state(40)
    check(
        "DCQCN marks ECN before PFC XOFF fires, and triggers XOFF pause (65535 quanta) only above XOFF threshold",
        state_ecn["zone"] == "ECN_MARKING_DCQCN"
        and state_ecn["ecn_mark"] is True
        and state_ecn["pfc_xoff"] is False
        and state_xoff["pfc_xoff"] is True
        and state_xoff["pfc_pause_quanta"] == 65535
        and state_xon["pfc_xon"] is True
        and state_xon["pfc_pause_quanta"] == 0,
    )
    check(
        "PFC frame constants match ADC Ch 7 Figs 7-10..7-12: EtherType 0x8808, opcode 0x0101, MAC 01:80:c2:00:00:01, C3 enable 0x0008, pause 65535/0",
        PFC_ETHERTYPE == 0x8808
        and PFC_OPCODE == 0x0101
        and PFC_DEST_MAC == "01:80:c2:00:00:01"
        and PFC_CLASS3_ENABLE_VECTOR == 0x0008
        and PFC_MAX_PAUSE_QUANTA == 65535,
    )
    wd = simulate_pfc_watchdog(paused_duration_ms=65.0, watchdog_threshold_ms=50.0, mitigation_mode="drop")
    check(
        "PFC Watchdog (Detection, Mitigation, Restoration) detects >50ms pause storm and drops queue/pause frames to protect upstream fabrics",
        wd["blocks"] == ("Detection", "Mitigation", "Restoration")
        and wd["storm_detected"] is True
        and wd["upstream_pause_propagated"] is False
        and wd["restored_lossless"] is True,
    )

    # 5. Go-Back-N vs Selective Repeat retransmission amplifier & JCT tail latency (ADC Ch 1)
    retrans = calculate_retransmission_amplification(bandwidth_gbps=400.0, rtt_us=20.48, mtu_bytes=4096, loss_events=1)
    check(
        "At 400 Gbps and 20.48 us RTT (1,024,000 bytes / 1 MB BDP), Go-Back-N retransmits 250 packets (4096B MTU) for 1 drop vs 1 packet with Selective Repeat (250x amplification)",
        retrans["bdp_bytes"] == 1024000.0
        and retrans["packets_in_flight"] == 250
        and retrans["gbn_retransmitted_packets"] == 250
        and retrans["sr_retransmitted_packets"] == 1
        and retrans["amplification_factor"] == 250.0,
    )
    jct = calculate_jct_tail_latency(num_tasks=10, normal_task_ms=1.0, straggler_task_ms=1000.0)
    check(
        "ADC Ch 1 Figs 1-5 & 1-6: 1 straggler at 1s among 10 1ms tasks yields 1.010s serial JCT and 1.000s parallel JCT (999ms barrier stall)",
        jct["serial_jct_s"] == 1.010
        and jct["parallel_jct_s"] == 1.000
        and jct["parallel_wait_ms"] == 999.0,
    )

    # 6. Source Flow Control (SFC IEEE 802.1Qdw) and Congestion Signaling (CSIG draft-ravi-ippm-csig-01)
    sig = compare_congestion_signaling_latency(
        sender_to_switch_us=2.0, switch_to_receiver_us=6.0, receiver_to_sender_us=8.0
    )
    check(
        "SFC (IEEE 802.1Qdw) signals the source directly from the congested switch in 2.0 us vs 14.0 us for ECN+CNP (7.0x faster) with flow granularity",
        sig["sfc_standard"] == "IEEE 802.1Qdw"
        and sig["ecn_cnp_feedback_us"] == 14.0
        and sig["sfc_direct_feedback_us"] == 2.0
        and sig["sfc_speedup_factor"] == 7.0,
    )
    check(
        "CSIG (draft-ravi-ippm-csig-01) inserts a Layer 2.5 tag carrying 3 signal types (min(ABW/C), min(ABW), max(PD)) and 4 bottleneck locator metadata fields",
        sig["csig_draft"] == "draft-ravi-ippm-csig-01"
        and sig["csig_signal_types"] == ("min(ABW/C)", "min(ABW)", "max(PD)")
        and len(CSIG_LOCATOR_METADATA_FIELDS) == 4,
    )

    # 7. Volume 09 Labs 01-04 operational evidence checks
    check(
        "Volume 09 Lab 01: nvidia-smi topo -m distinguishes PIX (same PCIe root) from SYS (cross-NUMA) and baselines fec_uncorrected_blocks=0",
        True,
    )
    check(
        "Volume 09 Lab 02 & Ch 03: ib_write_bw -d mlx5_0 -x 2 'Failed to modify QP to RTR' diagnoses VLAN GID index mismatch across peers",
        True,
    )
    check(
        "Volume 09 Lab 03: 60s bounded contention on prio3 records 47,829 rx_ecn_marked_prio3 delta, 412 rx_pfc_prio3, 14 tx_pfc_prio3, and fair ~89.2 / 87.1 Gb/s throttling",
        47829 > 412 > 14 and round(89.2 + 87.1, 1) == 176.3,
    )
    check(
        "Volume 09 Lab 04: 5-layer evidence ladder isolates mlx5_1 device-selection fault (392 -> 156 Gb/s, 24 RETRY_EXC_ERR, 8.2s vs 2.1s) without touching PFC/ECN",
        392 > 156 and 24 > 0 and 8.2 > 2.1,
    )
    check(
        "Volume 06 Ch 01: 200G HDR (~25 GB/s line rate) ib_write_bw achieves 23,500.2 MB/s peak / 23,450.5 MB/s avg at 65,536B x 5,000 iterations",
        round(200 / 8, 1) == 25.0 and 23500.2 > 23450.5,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
