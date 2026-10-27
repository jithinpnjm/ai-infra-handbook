#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.5: Data center bridging and QoS for AI.

Runs 30 deterministic checks covering:
  1. IP ToS / Traffic Class byte encoding/decoding (`(dscp << 2) | ecn`), `tcpdump`
     `tos 0xb8` -> `DSCP 46` (`EF`), `DSCP 26` (`0x6a` with `ECT(0)`), `DSCP 48` (`0xc1`
     with `ECT(1)`), and `mlnx_qos` `8`-value DSCP buckets (`0-7` .. `56-63`).
  2. The 4-class + CNP AI Ethernet fabric QoS model (`TC0` Best Effort, `TC2`
     Infrastructure/Control, `TC3` Lossless RoCEv2 Compute, `TC4` Storage/Checkpointing,
     `TC6` Strict-Priority CNP Feedback) and `64`-entry DSCP-to-Priority mapping table.
  3. IEEE `802.1Qaz` Enhanced Transmission Selection (`ETS`) bandwidth allocation,
     strict-priority (`TSA 0` / LLQ) vs Deficit Weighted Round Robin (`TSA 2` / `dwrr`
     / CBWFQ), work-conserving weight redistribution (`2:1:1:4` clock cycles and unused
     share redistribution), LLQ policing cap under congestion (`1,024 Kbps` link,
     `512 Kbps` cap, `9 x 64 = 576 Kbps` -> `64 Kbps` dropped, `12 x 64 = 768 Kbps` ->
     `256 Kbps` dropped, `32 x 16 = 512 Kbps` -> `0` dropped, and `10 x 64 = 640 Kbps`
     uncongested pass-through), and Volume 09 Chapter 6 Scenario 2 (`tc: 1` `strict`
     RoCE starving `tc: 0` `dwrr` weight `5` management).
  4. IEEE `802.1Qaz` DCBX over LLDP (`EtherType 0x88CC`, destination MAC `01:80:C2:00:00:0E`,
     IEEE `802.1` OUI `00:80:C2`, subtypes `9` ETS Configuration, `10` ETS Recommendation,
     `11` PFC Configuration, `12` Application Priority for RoCEv2 UDP port `4791`),
     `Willing` bit state machine, and mismatch detection between host `lldptool`/`mlnx_qos`
     and switch port.
  5. Buffer pool carving across lossless RDMA `TC3` (`262,144` B port buffer, `65,536` B
     Priority `3` reservation [`25.0%`], `XOFF = 49,152` B [`75.0%`], `XON = 32,768` B
     [`50.0%`], `16,384` B headroom [`25.0%`], `196,608` B [`75.0%`] remaining for lossy
     TCs) vs buffer exhaustion when `4` priorities are configured lossless (`262,144` B
     [`100.0%`] consumed, `0` B [`0.0%`] remaining).
  6. End-to-end QoS trust boundary and configuration drift verification (`swp4` `trust: dscp`
     vs `swp19` `trust: pcp` -> untagged L3 RoCE packet falls into `Priority 0` with
     `rx_prio0_discard = 18,420` and `rx_pfc_prio3 = 0`) plus Volume 09 Labs 01-04
     operational verification checks.
"""

from __future__ import annotations

import sys

from dcb_qos_ai import (
    DCBX_APP_SELECTOR_UDP_OR_DCCP,
    DCBX_SUBTYPE_APP_PRIORITY,
    DCBX_SUBTYPE_ETS_CONFIG,
    DCBX_SUBTYPE_ETS_RECOMMEND,
    DCBX_SUBTYPE_PFC_CONFIG,
    DSCP_AF11,
    DSCP_AF21,
    DSCP_AF31_ROCE,
    DSCP_AF41,
    DSCP_CS0_DF,
    DSCP_CS6_CNP,
    DSCP_CS7,
    DSCP_EF,
    IEEE_8021_OUI,
    LLDP_DEST_MAC,
    LLDP_ETHERTYPE,
    NVME_TCP_PORT,
    ROCEV2_UDP_PORT,
    TSA_CBSHAPER,
    TSA_ETS_DWRR,
    TSA_STRICT_PRIORITY,
    TSA_VENDOR_SPECIFIC,
    DcbxTlvEndpointProfile,
    HopQoSConfig,
    build_ai_fabric_qos_model,
    build_dscp_to_priority_table,
    decode_ip_tos_byte,
    encode_ip_tos_byte,
    evaluate_buffer_pool_carving,
    evaluate_dcbx_negotiation,
    simulate_ets_scheduling,
    trace_end_to_end_qos_path,
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

    print("=== Chapter 12.5 Lab: Data Center Bridging and QoS for AI ===")

    # 1. V9 Ch 6: tcpdump tos 0xb8 decodes to DSCP 46 (EF, bucket 40-47) and ECN 00
    tos_b8 = decode_ip_tos_byte(0xB8)
    check(
        "V9 Ch 6 tcpdump decode: tos 0xb8 (184) -> DSCP 46 (EF, 0xb8 >> 2 == 46), ECN 00, mlnx_qos bucket 40-47",
        tos_b8.tos_byte == 184
        and tos_b8.tos_hex == "0xb8"
        and tos_b8.dscp == DSCP_EF == 46
        and tos_b8.ecn == 0
        and tos_b8.ecn_bits == "00"
        and tos_b8.mlnx_dscp_bucket == "40-47",
    )

    # 2. RoCEv2 DSCP 26 (AF31) + ECT(0) (10 = 2) -> ToS 0x6a (106), bucket 24-31
    tos_roce_26 = encode_ip_tos_byte(DSCP_AF31_ROCE, ecn=2)
    dec_roce_26 = decode_ip_tos_byte(tos_roce_26)
    check(
        "RoCEv2 DSCP 26 + ECT(0) (10): (26 << 2) | 2 == 106 (0x6a), decodes to DSCP 26 in bucket 24-31",
        tos_roce_26 == 106
        and dec_roce_26.tos_hex == "0x6a"
        and dec_roce_26.dscp == 26
        and dec_roce_26.ecn_bits == "10"
        and dec_roce_26.mlnx_dscp_bucket == "24-31",
    )

    # 3. RoCEv2 CE-marked packet DSCP 26 + CE (11 = 3) -> ToS 0x6b (107), and CNP DSCP 48 (CS6) + ECT(1) (01 = 1) -> ToS 0xc1 (193)
    tos_roce_ce = encode_ip_tos_byte(DSCP_AF31_ROCE, ecn=3)
    tos_cnp_48 = encode_ip_tos_byte(DSCP_CS6_CNP, ecn=1)
    dec_cnp_48 = decode_ip_tos_byte(tos_cnp_48)
    check(
        "RoCEv2 CE-marked ToS 0x6b (107) and CNP DSCP 48 + ECT(1) ToS 0xc1 (193) in bucket 48-55",
        tos_roce_ce == 107
        and decode_ip_tos_byte(tos_roce_ce).ecn_bits == "11"
        and tos_cnp_48 == 193
        and dec_cnp_48.tos_hex == "0xc1"
        and dec_cnp_48.dscp == 48
        and dec_cnp_48.ecn_bits == "01"
        and dec_cnp_48.mlnx_dscp_bucket == "48-55",
    )

    # 4. Storage DSCP 18 (AF21) -> ToS 0x48 (72 with ECN 00) or 0x4a (74 with ECT(0)), bucket 16-23
    tos_storage = encode_ip_tos_byte(DSCP_AF21, ecn=2)
    dec_storage = decode_ip_tos_byte(tos_storage)
    check(
        "Storage DSCP 18 (AF21) + ECT(0): (18 << 2) | 2 == 74 (0x4a), mlnx_qos bucket 16-23",
        DSCP_AF21 == 18
        and tos_storage == 74
        and dec_storage.tos_hex == "0x4a"
        and dec_storage.mlnx_dscp_bucket == "16-23",
    )

    # 5. Standard IETF DSCP codepoints and AI fabric 5-row class model (4 workload intents + CNP)
    qos_model = build_ai_fabric_qos_model()
    drr_weight_sum = sum(e.ets_weight_pct for e in qos_model if e.tsa_mode == "dwrr")
    lossless_entries = [e for e in qos_model if e.is_lossless_pfc]
    strict_entries = [e for e in qos_model if e.tsa_mode == "strict"]
    check(
        "AI fabric QoS class model: DWRR weights sum to 100% (10+10+50+30), exactly 1 lossless class (TC3), and 1 strict-priority CNP class (TC6 capped at 20 Gbps)",
        len(qos_model) == 5
        and drr_weight_sum == 100
        and len(lossless_entries) == 1
        and lossless_entries[0].traffic_class == 3
        and lossless_entries[0].pcp_priority == 3
        and len(strict_entries) == 1
        and strict_entries[0].traffic_class == 6
        and strict_entries[0].strict_rate_cap_gbps == 20.0,
    )

    # 6. 64-entry DSCP-to-Priority mapping table verification
    dscp_map = build_dscp_to_priority_table(qos_model)
    check(
        "64-entry DSCP-to-Priority table: DSCP 0/10 -> Prio 0, DSCP 18 -> Prio 4 (Storage), DSCP 24/34 -> Prio 2 (Control), DSCP 26/46 -> Prio 3 (RoCE), DSCP 48/56 -> Prio 6 (CNP)",
        len(dscp_map) == 64
        and dscp_map[DSCP_CS0_DF] == 0
        and dscp_map[DSCP_AF11] == 0
        and dscp_map[DSCP_AF21] == 4
        and dscp_map[24] == 2
        and dscp_map[DSCP_AF41] == 2
        and dscp_map[DSCP_AF31_ROCE] == 3
        and dscp_map[DSCP_EF] == 3
        and dscp_map[DSCP_CS6_CNP] == 6
        and dscp_map[DSCP_CS7] == 6,
    )

    # 7. IEEE 802.1Qaz TSA identifiers: Strict=0, CBShaper=1, ETS/DWRR=2, Vendor=255
    check(
        "IEEE 802.1Qaz Transmission Selection Algorithm (TSA) IDs: Strict=0, CBShaper=1, ETS/DWRR=2, Vendor=255",
        (TSA_STRICT_PRIORITY, TSA_CBSHAPER, TSA_ETS_DWRR, TSA_VENDOR_SPECIFIC) == (0, 1, 2, 255),
    )

    # 8. ETS scheduling under full 4-class + CNP contention on a 400 Gbps link
    tc_cfg_400g = [
        (0, "dwrr", 10, None),
        (2, "dwrr", 10, None),
        (3, "dwrr", 50, None),
        (4, "dwrr", 30, None),
        (6, "strict", 0, 20.0),
    ]
    ets_full = simulate_ets_scheduling(
        line_rate_gbps=400.0,
        tc_configs=tc_cfg_400g,
        offered_load_gbps={0: 100.0, 2: 50.0, 3: 400.0, 4: 200.0, 6: 10.0},
    )
    check(
        "ETS 400G full contention (10G CNP strict + 390G DWRR split 10:10:50:30): TC6=10G, TC0=39G, TC2=39G, TC3=195G, TC4=117G, 0 starved",
        ets_full.total_allocated_gbps == {6: 10.0, 0: 39.0, 2: 39.0, 3: 195.0, 4: 117.0}
        and ets_full.starved_classes == ()
        and ets_full.unallocated_link_gbps == 0.0,
    )

    # 9. ETS work-conserving redistribution when only RoCE (TC3) and Storage (TC4) contend on 400G (50:30 = 5:3 ratio -> 250G and 150G)
    ets_roce_storage = simulate_ets_scheduling(
        line_rate_gbps=400.0,
        tc_configs=tc_cfg_400g,
        offered_load_gbps={0: 0.0, 2: 0.0, 3: 400.0, 4: 400.0, 6: 0.0},
    )
    check(
        "ETS work-conserving 2-class contention (TC3 50% vs TC4 30% on 400G): unused 20% redistributed in 5:3 ratio -> TC3=250.0 Gbps, TC4=150.0 Gbps",
        ets_roce_storage.total_allocated_gbps[3] == 250.0
        and ets_roce_storage.total_allocated_gbps[4] == 150.0
        and ets_roce_storage.unallocated_link_gbps == 0.0,
    )

    # 10. ETS work-conserving single-class burst: Storage (TC4, 30% weight) alone on 400G gets all 400.0 Gbps (ETS is not a hard ceiling)
    ets_single = simulate_ets_scheduling(
        line_rate_gbps=400.0,
        tc_configs=tc_cfg_400g,
        offered_load_gbps={0: 0.0, 2: 0.0, 3: 0.0, 4: 400.0, 6: 0.0},
    )
    check(
        "ETS work-conserving single-class burst: TC4 (30% ETS minimum) gets full 400.0 Gbps when other queues are empty",
        ets_single.total_allocated_gbps[4] == 400.0 and ets_single.unallocated_link_gbps == 0.0,
    )

    # 11. V9 Ch 6 Scenario 2: Management starvation when RoCE (TC1, Prio 3) is configured `strict` without rate limit over Management (TC0, Prio 0, `dwrr` weight 5)
    v9_scen2_bad = simulate_ets_scheduling(
        line_rate_gbps=400.0,
        tc_configs=[(0, "dwrr", 5, None), (1, "strict", 0, None)],
        offered_load_gbps={0: 10.0, 1: 400.0},
    )
    v9_scen2_fixed = simulate_ets_scheduling(
        line_rate_gbps=400.0,
        tc_configs=[(0, "dwrr", 5, None), (1, "dwrr", 95, None)],
        offered_load_gbps={0: 50.0, 1: 400.0},
    )
    check(
        "V9 Ch 6 Scenario 2 starvation: TC1 (Prio 3) on `strict` takes 400.0 Gbps and starves TC0 (`dwrr` weight 5 -> 0.0 Gbps); moving to ETS 95/5 guarantees TC0 20.0 Gbps",
        v9_scen2_bad.total_allocated_gbps[1] == 400.0
        and v9_scen2_bad.total_allocated_gbps[0] == 0.0
        and v9_scen2_bad.starved_classes == (0,)
        and v9_scen2_fixed.total_allocated_gbps[0] == 20.0
        and v9_scen2_fixed.total_allocated_gbps[1] == 380.0
        and v9_scen2_fixed.starved_classes == (),
    )

    # 12. CNPS Ch 8 CBWFQ 1,024 Kbps link ratio 256:128:128:512 = 2:1:1:4 across 8 clock cycles
    cbwfq_1024 = simulate_ets_scheduling(
        line_rate_gbps=1024.0,
        tc_configs=[
            (41, "dwrr", 2, None),  # AF41: 256 Kbps (2/8)
            (31, "dwrr", 1, None),  # AF31: 128 Kbps (1/8)
            (21, "dwrr", 1, None),  # AF21: 128 Kbps (1/8)
            (0, "dwrr", 4, None),   # Unallocated/Best-effort: 512 Kbps (4/8)
        ],
        offered_load_gbps={41: 1024.0, 31: 1024.0, 21: 1024.0, 0: 1024.0},
    )
    check(
        "CNPS Ch 8 CBWFQ on 1,024 Kbps link (ratio 2:1:1:4 across 8 clock cycles): AF41=256 Kbps, AF31=128 Kbps, AF21=128 Kbps, Default=512 Kbps",
        cbwfq_1024.total_allocated_gbps == {41: 256.0, 31: 128.0, 21: 128.0, 0: 512.0},
    )

    # 13. CNPS Ch 8 LLQ policing on 1,024 Kbps link (512 Kbps LLQ cap = 8 x 64 Kbps calls; 9th call = 576 Kbps -> 64 Kbps dropped; 12 calls = 768 Kbps -> 256 Kbps dropped; 32 x 16 Kbps = 512 Kbps -> 0 dropped)
    llq_9_calls = simulate_ets_scheduling(
        line_rate_gbps=1024.0,
        tc_configs=[(1, "strict", 0, 512.0), (0, "dwrr", 100, None)],
        offered_load_gbps={1: 9 * 64.0, 0: 600.0},
    )
    llq_12_calls = simulate_ets_scheduling(
        line_rate_gbps=1024.0,
        tc_configs=[(1, "strict", 0, 512.0), (0, "dwrr", 100, None)],
        offered_load_gbps={1: 12 * 64.0, 0: 600.0},
    )
    llq_32_16k = simulate_ets_scheduling(
        line_rate_gbps=1024.0,
        tc_configs=[(1, "strict", 0, 512.0), (0, "dwrr", 100, None)],
        offered_load_gbps={1: 32 * 16.0, 0: 600.0},
    )
    check(
        "CNPS Ch 8 LLQ under congestion (1,024 Kbps link, 512 Kbps LLQ cap): 9x64=576 Kbps drops 64 Kbps; 12x64=768 Kbps drops 256 Kbps; 32x16=512 Kbps drops 0 Kbps",
        llq_9_calls.strict_allocated_gbps[1] == 512.0
        and llq_9_calls.strict_dropped_policed_gbps[1] == 64.0
        and llq_12_calls.strict_allocated_gbps[1] == 512.0
        and llq_12_calls.strict_dropped_policed_gbps[1] == 256.0
        and llq_32_16k.strict_allocated_gbps[1] == 512.0
        and llq_32_16k.strict_dropped_policed_gbps[1] == 0.0,
    )

    # 14. CNPS Ch 8 LLQ uncongested pass-through: 10 x 64 = 640 Kbps LLQ + 300 Kbps other (<= 384 Kbps remaining) = 940 Kbps <= 1,024 Kbps -> 0 dropped
    llq_uncongested = simulate_ets_scheduling(
        line_rate_gbps=1024.0,
        tc_configs=[(1, "strict", 0, 512.0), (0, "dwrr", 100, None)],
        offered_load_gbps={1: 10 * 64.0, 0: 300.0},
    )
    check(
        "CNPS Ch 8 LLQ uncongested link (640 Kbps LLQ + 300 Kbps other <= 1,024 Kbps, <= 384 Kbps remaining): all 640 Kbps passes without policing drops",
        llq_uncongested.strict_allocated_gbps[1] == 640.0
        and llq_uncongested.strict_dropped_policed_gbps[1] == 0.0
        and llq_uncongested.unallocated_link_gbps == 84.0,
    )

    # 15. CNPS Ch 17 serialization delay & jitter: 64B (0.00512 ms, printed as .05ms in CNPS Ch 17), 1500B (0.12 ms), 9000B (0.72 ms = 14x 0.05 ms) on 100 Mbps; at 400 Gbps, 9000B is 180 ns and 64B is 1.28 ns
    ser_64_100m_ms = (64 * 8) / 100_000.0
    ser_1500_100m_ms = (1500 * 8) / 100_000.0
    ser_9000_100m_ms = (9000 * 8) / 100_000.0
    ser_9000_400g_ns = (9000 * 8) / 400.0
    ser_64_400g_ns = (64 * 8) / 400.0
    check(
        "CNPS Ch 8/17 & Handbook 2.19 serialization delay: on 100 Mbps, 64B=0.00512 ms (0.05 ms in CNPS), 1500B=0.12 ms, 9000B=0.72 ms (14x 0.05 ms); on 400 Gbps, 9000B=180.0 ns and 64B=1.28 ns",
        abs(ser_64_100m_ms - 0.00512) < 1e-9
        and abs(ser_1500_100m_ms - 0.12) < 1e-9
        and abs(ser_9000_100m_ms - 0.72) < 1e-9
        and int(ser_9000_100m_ms // 0.05) == 14
        and abs(ser_9000_400g_ns - 180.0) < 1e-9
        and abs(ser_64_400g_ns - 1.28) < 1e-9,
    )

    # 16. IEEE 802.1Qaz DCBX over LLDP constants (EtherType 0x88CC, Dst MAC 01:80:C2:00:00:0E, OUI 00:80:C2, subtypes 9, 10, 11, 12, UDP 4791, NVMe/TCP 8009)
    check(
        "IEEE 802.1Qaz DCBX over LLDP constants: EtherType 0x88CC, MAC 01:80:C2:00:00:0E, OUI 00:80:C2, subtypes 9 (ETS Cfg), 10 (ETS Rec), 11 (PFC), 12 (App Prio), RoCE UDP 4791, NVMe/TCP 8009",
        LLDP_ETHERTYPE == 0x88CC
        and LLDP_DEST_MAC == "01:80:C2:00:00:0E"
        and IEEE_8021_OUI == "00:80:C2"
        and (
            DCBX_SUBTYPE_ETS_CONFIG,
            DCBX_SUBTYPE_ETS_RECOMMEND,
            DCBX_SUBTYPE_PFC_CONFIG,
            DCBX_SUBTYPE_APP_PRIORITY,
        )
        == (9, 10, 11, 12)
        and ROCEV2_UDP_PORT == 4791
        and NVME_TCP_PORT == 8009,
    )

    # 17. DCBX Negotiation Case A: Host Willing=True, Switch Willing=False -> Host adopts Switch profile cleanly (SWITCH_PEER)
    prio_to_tc_std = {0: 0, 1: 0, 2: 2, 3: 3, 4: 4, 5: 0, 6: 6, 7: 0}
    ets_weights_std = {0: 10, 2: 10, 3: 50, 4: 30, 6: 0}
    tsa_std = {0: "dwrr", 2: "dwrr", 3: "dwrr", 4: "dwrr", 6: "strict"}
    app_std = {(DCBX_APP_SELECTOR_UDP_OR_DCCP, ROCEV2_UDP_PORT): 3}

    host_willing = DcbxTlvEndpointProfile(
        role="host",
        ets_willing=True,
        pfc_willing=True,
        pfc_enabled_priorities=(0,),  # initial host default before LLDP DCBX sync
        pfc_mbc=False,
        prio_to_tc=prio_to_tc_std,
        tc_ets_weights={0: 100},
        tc_tsa=tsa_std,
        app_priority_table={},
        trust_mode="dscp",
    )
    switch_authoritative = DcbxTlvEndpointProfile(
        role="switch",
        ets_willing=False,
        pfc_willing=False,
        pfc_enabled_priorities=(3,),
        pfc_mbc=False,
        prio_to_tc=prio_to_tc_std,
        tc_ets_weights=ets_weights_std,
        tc_tsa=tsa_std,
        app_priority_table=app_std,
        trust_mode="dscp",
    )
    dcbx_synced = evaluate_dcbx_negotiation(host_willing, switch_authoritative)
    check(
        "DCBX Negotiation (Host Willing=1, Switch Willing=0): Host adopts Switch Priority 3 PFC, ETS weights (10/10/50/30), and UDP 4791 -> Prio 3 cleanly",
        dcbx_synced.operational_state_source == "SWITCH_PEER"
        and dcbx_synced.pfc_operational_host == (3,)
        and dcbx_synced.pfc_matched
        and dcbx_synced.ets_weights_matched
        and dcbx_synced.app_roce_priority_matched
        and dcbx_synced.is_healthy,
    )

    # 18. DCBX Negotiation Case B: Both Willing=False (Static Automation Mode) with matching profiles -> BOTH_LOCAL_STATIC healthy
    host_static_ok = DcbxTlvEndpointProfile(
        role="host",
        ets_willing=False,
        pfc_willing=False,
        pfc_enabled_priorities=(3,),
        pfc_mbc=False,
        prio_to_tc=prio_to_tc_std,
        tc_ets_weights=ets_weights_std,
        tc_tsa=tsa_std,
        app_priority_table=app_std,
        trust_mode="dscp",
    )
    dcbx_static_ok = evaluate_dcbx_negotiation(host_static_ok, switch_authoritative)
    check(
        "DCBX Static Automation Mode (Host Willing=0, Switch Willing=0, matching source of truth): BOTH_LOCAL_STATIC healthy",
        dcbx_static_ok.operational_state_source == "BOTH_LOCAL_STATIC"
        and dcbx_static_ok.is_healthy
        and dcbx_static_ok.mismatches == (),
    )

    # 19. DCBX Negotiation Case C: Both Willing=False with PFC & Trust Drift -> detects PFC_MISMATCH, ETS_WEIGHT_MISMATCH, APP_TLV_ROCE_4791_MISMATCH, TRUST_MODE_MISMATCH
    host_static_drifted = DcbxTlvEndpointProfile(
        role="host",
        ets_willing=False,
        pfc_willing=False,
        pfc_enabled_priorities=(4,),  # Host enabled PFC on Prio 4 instead of Prio 3
        pfc_mbc=False,
        prio_to_tc=prio_to_tc_std,
        tc_ets_weights={0: 50, 3: 50},
        tc_tsa=tsa_std,
        app_priority_table={(DCBX_APP_SELECTOR_UDP_OR_DCCP, ROCEV2_UDP_PORT): 4},
        trust_mode="pcp",
    )
    dcbx_drift = evaluate_dcbx_negotiation(host_static_drifted, switch_authoritative)
    check(
        "DCBX Static Drift Detection: catches PFC mismatch (Prio 4 vs 3), ETS weight mismatch, App TLV 4791 mismatch, and Trust mode mismatch (pcp vs dscp)",
        not dcbx_drift.is_healthy
        and not dcbx_drift.pfc_matched
        and not dcbx_drift.ets_weights_matched
        and not dcbx_drift.app_roce_priority_matched
        and not dcbx_drift.trust_mode_matched
        and len(dcbx_drift.mismatches) == 4,
    )

    # 20. DCBX Negotiation Case D: Both Host and Switch Willing=True -> flags WILLING_BIT_CONFLICT
    switch_also_willing = DcbxTlvEndpointProfile(
        role="switch",
        ets_willing=True,
        pfc_willing=True,
        pfc_enabled_priorities=(3,),
        pfc_mbc=False,
        prio_to_tc=prio_to_tc_std,
        tc_ets_weights=ets_weights_std,
        tc_tsa=tsa_std,
        app_priority_table=app_std,
        trust_mode="dscp",
    )
    dcbx_conflict = evaluate_dcbx_negotiation(host_willing, switch_also_willing)
    check(
        "DCBX Willing Conflict: when both Host and Switch set Willing=1, evaluator flags CONFLICT_BOTH_WILLING",
        dcbx_conflict.operational_state_source == "CONFLICT_BOTH_WILLING"
        and not dcbx_conflict.is_healthy
        and any("WILLING_BIT_CONFLICT" in m for m in dcbx_conflict.mismatches),
    )

    # 21. Buffer Pool Carving Case A: Healthy single lossless class (Priority 3) on 262,144 B port buffer (65,536 B [25.0%] lossless, 196,608 B [75.0%] lossy shared)
    buf_1_lossless = evaluate_buffer_pool_carving(
        total_port_buffer_bytes=262_144,
        lossless_priorities=(3,),
        per_lossless_prio_reserved_bytes=65_536,
        xoff_bytes=49_152,
        xon_bytes=32_768,
    )
    check(
        "Buffer Pool Carving (1 lossless class Prio 3 on 262,144B port): 65,536B (25.0%) lossless (XOFF=49,152B, XON=32,768B, headroom=16,384B), 196,608B (75.0%) lossy",
        buf_1_lossless.is_valid_carving
        and buf_1_lossless.total_lossless_reserved_bytes == 65_536
        and buf_1_lossless.remaining_lossy_shared_bytes == 196_608
        and buf_1_lossless.lossless_share_pct == 25.0
        and buf_1_lossless.lossy_share_pct == 75.0
        and buf_1_lossless.per_lossless_prio_headroom_bytes == 16_384,
    )

    # 22. Buffer Pool Carving Case B: Two lossless classes (Priority 3 RoCE + Priority 4 NVMe-o-RDMA) -> 131,072 B (50.0%) lossless, 131,072 B (50.0%) lossy
    buf_2_lossless = evaluate_buffer_pool_carving(
        total_port_buffer_bytes=262_144,
        lossless_priorities=(3, 4),
        per_lossless_prio_reserved_bytes=65_536,
        xoff_bytes=49_152,
        xon_bytes=32_768,
    )
    check(
        "Buffer Pool Carving (2 lossless classes Prio 3 + Prio 4): 131,072B (50.0%) lossless reserved, 131,072B (50.0%) remaining for lossy classes",
        buf_2_lossless.is_valid_carving
        and buf_2_lossless.total_lossless_reserved_bytes == 131_072
        and buf_2_lossless.remaining_lossy_shared_bytes == 131_072
        and buf_2_lossless.lossless_share_pct == 50.0
        and buf_2_lossless.lossy_share_pct == 50.0,
    )

    # 23. Buffer Pool Carving Case C: Four lossless classes -> 262,144 B (100.0%) locked in lossless reservations, 0 B (0.0%) left for lossy classes (BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES)
    buf_4_lossless = evaluate_buffer_pool_carving(
        total_port_buffer_bytes=262_144,
        lossless_priorities=(1, 2, 3, 4),
        per_lossless_prio_reserved_bytes=65_536,
        xoff_bytes=49_152,
        xon_bytes=32_768,
    )
    check(
        "Buffer Pool Carving Failure (4 lossless classes): 262,144B (100.0%) consumed, 0B (0.0%) left for lossy TCP/control/CNP queues -> BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES",
        not buf_4_lossless.is_valid_carving
        and buf_4_lossless.total_lossless_reserved_bytes == 262_144
        and buf_4_lossless.remaining_lossy_shared_bytes == 0
        and buf_4_lossless.lossless_share_pct == 100.0
        and buf_4_lossless.lossy_share_pct == 0.0
        and "BUFFER_EXHAUSTED_TOO_MANY_LOSSLESS_CLASSES" in buf_4_lossless.finding,
    )

    # 24. End-to-End QoS Path Trace Case A: Healthy 4-hop path (Host ens1f0 -> Leaf swp4 -> Spine swp1 -> Dest Leaf swp19, all trust=dscp)
    dscp_table = build_dscp_to_priority_table(qos_model)
    pcp_zero_table = {p: 0 for p in range(8)}
    hop_host = HopQoSConfig("host_ens1f0", "dscp", dscp_table, pcp_zero_table, (3,), (3,))
    hop_leaf_a = HopQoSConfig("leafA_swp4", "dscp", dscp_table, pcp_zero_table, (3,), (3,))
    hop_spine = HopQoSConfig("spine1_swp1", "dscp", dscp_table, pcp_zero_table, (3,), (3,))
    hop_leaf_b_ok = HopQoSConfig("leafB_swp19", "dscp", dscp_table, pcp_zero_table, (3,), (3,))

    trace_ok = trace_end_to_end_qos_path(
        initial_dscp=DSCP_EF,
        initial_pcp=None,
        expected_priority=3,
        hops=[hop_host, hop_leaf_a, hop_spine, hop_leaf_b_ok],
    )
    check(
        "End-to-End QoS Contract Verified: DSCP 46 (tos 0xb8) untagged L3 frame stays in lossless Priority 3 across host_ens1f0, leafA_swp4, spine1_swp1, and leafB_swp19",
        trace_ok.end_to_end_lossless
        and trace_ok.first_drift_hop is None
        and all(h.resolved_priority == 3 and h.is_lossless_pfc for h in trace_ok.hop_results),
    )

    # 25. End-to-End QoS Path Trace Case B: V9 Ch 6 Scenario 1 Drift — destination leaf `swp19` configured `trust: pcp` -> untagged L3 packet drops to Priority 0 (`rx_prio0_discard = 18,420`, `rx_pfc_prio3 = 0`)
    hop_leaf_b_pcp_drift = HopQoSConfig("leafB_swp19", "pcp", dscp_table, pcp_zero_table, (3,), (3,))
    trace_pcp_drift = trace_end_to_end_qos_path(
        initial_dscp=DSCP_EF,
        initial_pcp=None,
        expected_priority=3,
        hops=[hop_host, hop_leaf_a, hop_spine, hop_leaf_b_pcp_drift],
    )
    rx_prio0_discard_swp19 = 18_420
    rx_pfc_prio3_swp19 = 0
    check(
        "V9 Ch 6 Scenario 1 Trust-Mode Drift on swp19 (`trust: pcp`): untagged L3 RoCE packet falls to Priority 0 at leafB_swp19 (`rx_prio0_discard=18,420`, `rx_pfc_prio3=0`)",
        not trace_pcp_drift.end_to_end_lossless
        and trace_pcp_drift.first_drift_hop == "leafB_swp19"
        and trace_pcp_drift.hop_results[1].resolved_priority == 3  # swp4 ok
        and trace_pcp_drift.hop_results[3].resolved_priority == 0  # swp19 fell to prio 0
        and not trace_pcp_drift.hop_results[3].is_lossless_pfc
        and rx_prio0_discard_swp19 == 18_420
        and rx_pfc_prio3_swp19 == 0,
    )

    # 26. End-to-End QoS Path Trace Case C: Untrusted ingress port rewrites DSCP to 0 (`untrusted_rewrite_zero` in CNPS Ch 8 Fig 8-3 & V9 Ch 6 Fig 9.6.1)
    hop_leaf_untrusted = HopQoSConfig("leafA_swp4", "untrusted_rewrite_zero", dscp_table, pcp_zero_table, (3,), (3,))
    trace_rewrite = trace_end_to_end_qos_path(
        initial_dscp=DSCP_AF31_ROCE,
        initial_pcp=3,
        expected_priority=3,
        hops=[hop_host, hop_leaf_untrusted, hop_spine, hop_leaf_b_ok],
    )
    check(
        "CNPS Ch 8 Fig 8-3 & V9 Ch 6 Fig 9.6.1 Untrusted Ingress Rewrite: leafA_swp4 rewrites DSCP 26 -> 0, forcing all downstream hops into Priority 0",
        not trace_rewrite.end_to_end_lossless
        and trace_rewrite.first_drift_hop == "leafA_swp4"
        and trace_rewrite.hop_results[1].ingress_dscp == 0
        and trace_rewrite.hop_results[2].resolved_priority == 0,
    )

    # 27. ADC Ch 9 Storage & AI Fabric Latency Comparison: PCIe Gen5 32 GT/s x16 (~63 GB/s one-way, ~100 ns local SSD), IB (~300 ns), Ethernet switch (~800 ns, 700-900 ns port-to-port), IB 16 VLs (8-12 queues, 64B credit, 48,000 LIDs)
    pcie_gen5_gt_s = 32
    pcie_x16_lanes = 16
    pcie_gen5_one_way_gb_s = 63
    local_pcie_ssd_ns = 100
    ib_switch_ns = 300
    eth_switch_ns = 800
    ib_max_vls = 16
    ib_credit_bytes = 64
    ib_max_lids = 48_000
    check(
        "ADC Ch 9 Storage & QoS metrics: PCIe Gen5 32 GT/s x16 (~63 GB/s, 100 ns local SSD), IB ~300 ns (16 VLs, 64B credits, 48,000 LIDs), Ethernet ~800 ns (700-900 ns), NVMe/TCP port 8009",
        pcie_gen5_gt_s == 32
        and pcie_x16_lanes == 16
        and pcie_gen5_one_way_gb_s == 63
        and (local_pcie_ssd_ns, ib_switch_ns, eth_switch_ns) == (100, 300, 800)
        and (ib_max_vls, ib_credit_bytes, ib_max_lids) == (16, 64, 48_000),
    )

    # 28. BCM11 Admin Ch 3 Network Interface Priority Ladder & ConnectX PCIe Downgrade Check (V9 Ch 8)
    bcm_interface_priorities = {
        "Bridge": 80,
        "Bond": 70,
        "Physical": 60,
        "VLAN": 50,
        "Alias": 40,
        "Tunnel": 30,
        "Netmap": 20,
        "BMC": 10,
    }
    # V9 Ch 8 PCIe downgrade: LnkCap 32 GT/s x16 (~63 GB/s) downgraded to LnkSta 16 GT/s x8 (~16 GB/s < 25 GB/s needed for 200GbE)
    eth_200g_gb_s = 200.0 / 8.0  # 25.0 GB/s
    pcie_gen4_x8_gb_s = 16.0
    check(
        "BCM11 Ch 3 interface priority ladder (Bridge=80, Bond=70, Physical=60, VLAN=50, Alias=40, Tunnel=30, Netmap=20, BMC=10) & V9 Ch 8 PCIe Gen4 x8 (16 GB/s < 25 GB/s for 200GbE)",
        bcm_interface_priorities["Bridge"] == 80
        and bcm_interface_priorities["Bond"] == 70
        and bcm_interface_priorities["Physical"] == 60
        and bcm_interface_priorities["VLAN"] == 50
        and bcm_interface_priorities["BMC"] == 10
        and eth_200g_gb_s == 25.0
        and pcie_gen4_x8_gb_s < eth_200g_gb_s,
    )

    # 29. V9 Labs 01-03 Inventory & Bounded Contention Baseline (`ens1f0`, `10.20.4.15 -> 10.20.8.5` via `10.20.0.1`, `MTU 9000`, `400000Mb/s`, `fec_corrected=412`, `fec_uncorrected=0`, `47,829` ECN marks, `412` RX PFC, `14` TX PFC, `89.2 + 87.1 = 176.3 Gbps`)
    rx_prio3_delta = 51_234_892 - 102_314
    tx_prio3_delta = 48_901_234 - 89_621
    sender_sum_gbps = round(89.2 + 87.1, 1)
    check(
        "V9 Labs 01-03 Baseline & 60s Contention: MTU 9000, 400000Mb/s, fec_corrected=412, fec_uncorrected=0, rx_prio3 delta=51,132,578, tx_prio3 delta=48,811,613, ECN=47,829, RX PFC=412, TX PFC=14, 89.2+87.1=176.3 Gbps",
        rx_prio3_delta == 51_132_578
        and tx_prio3_delta == 48_811_613
        and sender_sum_gbps == 176.3,
    )

    # 30. V9 Lab 04 Evidence Ladder: `mlx5_0` (`392 Gbps` in `2.1 s`, `0` retries) vs `mlx5_1` (`156 Gbps` in `8.2 s`, `24` `RETRY_EXC_ERR`, `rx_ecn_marked_prio3=142`)
    healthy_bw, degraded_bw = 392.0, 156.0
    healthy_t, degraded_t = 2.1, 8.2
    check(
        "V9 Lab 04 Evidence Ladder: mlx5_0 (392 Gbps in 2.1s, 0 retries) vs mlx5_1 (156 Gbps in 8.2s, 2.51x slower, 24 RETRY_EXC_ERR, rx_ecn_marked_prio3=142)",
        round(healthy_bw / degraded_bw, 2) == 2.51
        and round(degraded_t / healthy_t, 2) == 3.90,
    )

    print(f"\nSummary: {passed} passed, {failed} failed out of {passed + failed} checks.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
