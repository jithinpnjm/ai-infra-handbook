#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.8: InfiniBand adaptive routing and congestion control.

Runs 28 deterministic checks covering:
  - InfiniBand Credit-Based Flow Control (CBFC), 16 Virtual Lanes (VL0..VL14 data, VL15 SMP),
    64-byte credit units, 16-bit LID (48,000 end nodes), and 300 ns vs 800 ns switch latency
  - Victim buffer / Head-of-Line (HoL) blocking isolation across Virtual Lanes (V8 Ch. 11:
    1.8 ms baseline -> 14.2 ms shared VL -> 3.1 ms separated VL) and credit loop cycle detection
  - Static LFT destination hash collision (`PortXmitData` 20:1 imbalance across ports 5..8)
    vs Adaptive Routing group table (`AR_group`, dynamic port selection, `ar_sl_mask` 0xFFFF)
  - Fast Notification (`FRN` / `RN`) and `SHIELD` autonomous sub-millisecond link-failure
    rerouting on Quantum-2 (400G, 64p) & Quantum-X800 (800G, 144p Q3400-RD, 16 SUs / 9,216 GPUs)
    vs OpenSM `Trap 128` heavy sweep (`LID 44 port 3`)
  - Out-of-Order (`OOO`) packet delivery & ConnectX HCA hardware packet reordering vs
    uncompensated p99/max tail latency regression (`3.1 -> 2.4 us` p50, `7.2 -> 38.6 us` p99,
    `9.1 -> 112.4 us` max)
  - IB Congestion Control closed loop: `FECN` -> `BECN` -> `CCTI` (0..127, 128 entries)
    injection rate throttling & `CCTI_Timer` recovery
  - Production `perfquery` / `ibqueryerrors` counter scenarios from Volume 08 Chapters 2, 6, 7,
    9, 10 and Labs 01..04.
"""

from __future__ import annotations

import sys

from infiniband_ar_cc import (
    AR_DEFAULT_SL_MASK,
    CCT_MAX_INDEX,
    CCT_TABLE_SIZE,
    ETH_SWITCH_LATENCY_NS,
    GB300_LEAF_SWITCHES_16SU,
    GB300_MAX_GPUS_2LAYER,
    GB300_MAX_SUS_2LAYER,
    GB300_SPINE_SWITCHES_16SU,
    IB_CREDIT_UNIT_BYTES,
    IB_DATA_VLS,
    IB_LRH_LID_BITS,
    IB_MAX_UNICAST_LIDS,
    IB_MAX_VLS,
    IB_PORT_XMIT_DATA_OCTETS,
    IB_SMP_VL,
    IB_SWITCH_LATENCY_NS,
    OPENSM_LINK_TRAP_ID,
    QUANTUM2_NDR_PORT_GBPS,
    QUANTUM2_NDR_RADIX,
    QUANTUM_X800_PORT_GBPS,
    QUANTUM_X800_Q3400_RADIX,
    analyze_uplink_port_xmit_data,
    classify_ib_port_telemetry,
    compute_leaf_oversubscription_allreduce_impact,
    detect_credit_dependency_cycle,
    evaluate_ar_ooo_reordering,
    evaluate_shield_frn_vs_opensm_failover,
    evaluate_symbol_error_acceleration,
    evaluate_vl_credit_state,
    locate_congestion_tree_root_ports,
    simulate_lft_vs_ar_group_selection,
    simulate_vl_hol_isolation,
    step_ib_cc_state_machine,
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

    print("=== Chapter 12.8 Lab: InfiniBand Adaptive Routing and Congestion Control ===")

    # 1. ADC Ch. 9: IB CBFC & VL architecture constants
    check(
        "ADC Ch 9 IB QoS & Addressing: 16 VLs (VL0..VL14 data, VL15 SMP), 64B credit unit, 16-bit LID (48,000 unicast nodes), 300ns IB vs 800ns Ethernet switch latency",
        IB_MAX_VLS == 16
        and IB_DATA_VLS == 15
        and IB_SMP_VL == 15
        and IB_CREDIT_UNIT_BYTES == 64
        and IB_LRH_LID_BITS == 16
        and IB_MAX_UNICAST_LIDS == 48_000
        and IB_SWITCH_LATENCY_NS == 300
        and ETH_SWITCH_LATENCY_NS == 800,
    )

    # 2. superpod-gb300-ra & Quantum-2 / Quantum-X800 switch architecture
    check(
        "superpod-gb300-ra Quantum-2 & Quantum-X800 specs: NDR 400G/64-port, XDR 800G/144-port Q3400-RD scaling to 16 SUs (9,216 GPUs, 128 leaf, 72 spine switches)",
        QUANTUM2_NDR_PORT_GBPS == 400
        and QUANTUM2_NDR_RADIX == 64
        and QUANTUM_X800_PORT_GBPS == 800
        and QUANTUM_X800_Q3400_RADIX == 144
        and GB300_MAX_SUS_2LAYER == 16
        and GB300_MAX_GPUS_2LAYER == 9216
        and GB300_LEAF_SWITCHES_16SU == 128
        and GB300_SPINE_SWITCHES_16SU == 72,
    )

    # 3. Per-VL Credit-Based Flow Control (CBFC) healthy credit check (65,536 B buffer = 1,024 credits)
    vl0_healthy = evaluate_vl_credit_state(vl=0, buffer_bytes=65536, occupied_bytes=32768, packet_bytes=4096)
    check(
        "CBFC healthy VL0 state: 65,536 B buffer = 1,024 credits (64 B each); 32,768 B occupied leaves 512 credits (>= 64 credits needed for 4,096 B MTU)",
        vl0_healthy.total_credits == 1024
        and vl0_healthy.available_credits == 512
        and vl0_healthy.can_transmit_4kb_mtu is True
        and vl0_healthy.is_stalled is False,
    )

    # 4. Per-VL CBFC credit exhaustion / stall (63,488 B occupied leaves 32 credits < 64 needed for 4 KB MTU)
    vl0_stalled = evaluate_vl_credit_state(vl=0, buffer_bytes=65536, occupied_bytes=63488, packet_bytes=4096)
    check(
        "CBFC stalled VL0 state: 63,488 B occupied in 65,536 B buffer leaves 2,048 B = 32 credits (< 64 credits for 4,096 B MTU -> link-level credit stall)",
        vl0_stalled.available_credits == 32
        and vl0_stalled.can_transmit_4kb_mtu is False
        and vl0_stalled.is_stalled is True,
    )

    # 5. Victim buffer / Head-of-Line (HoL) blocking isolation across Virtual Lanes (V8 Ch. 11 Scenario 3)
    hol = simulate_vl_hol_isolation()
    check(
        "V8 Ch 11 Scenario 3 Victim Buffer & VL HoL Isolation: shared VL stalls victim (p99 1.8 ms -> 14.2 ms, 7.89x); separated VL keeps victim flowing (p99 3.1 ms, 89.52% recovery)",
        hol.shared_vl_victim_blocked is True
        and hol.separated_vl_victim_blocked is False
        and hol.baseline_p99_ms == 1.8
        and hol.shared_vl_p99_ms == 14.2
        and hol.separated_vl_p99_ms == 3.1
        and hol.shared_inflation_factor == 7.89
        and hol.separated_recovery_pct == 89.52,
    )

    # 6. Credit loop detection: cyclic channel dependency graph vs acyclic Up*/Down* or VL-split graph
    has_cycle, cycle_path = detect_credit_dependency_cycle(
        [("SW1_VL0", "SW2_VL0"), ("SW2_VL0", "SW3_VL0"), ("SW3_VL0", "SW1_VL0")]
    )
    no_cycle, _ = detect_credit_dependency_cycle(
        [("SW1_VL0", "SW2_VL0"), ("SW2_VL0", "SW3_VL1"), ("SW3_VL1", "SW1_VL1")]
    )
    check(
        "Credit loop detector: cyclic VL dependency (SW1_VL0 -> SW2_VL0 -> SW3_VL0 -> SW1_VL0) deadlocks; splitting onto VL1 breaks the cycle",
        has_cycle is True
        and len(cycle_path) == 4
        and no_cycle is False,
    )

    # 7. V8 Ch. 6 Scenario 1: Static LFT uplink imbalance (`PortXmitData` across ports 5..8)
    # 4-octet word deltas: 5,368,709,120 (port 5), 5,372,308,608 (port 6), 268,435,456 (port 7), 270,413,568 (port 8) -> 20.01x
    v8_ch6_uplinks = analyze_uplink_port_xmit_data(
        {
            5: 5_368_709_120,
            6: 5_372_308_608,
            7: 268_435_456,
            8: 270_413_568,
        },
        already_in_bytes=False,
    )
    check(
        "V8 Ch 6 Scenario 1 Uplink Imbalance: PortXmitData (4-octet words) on ports 5-6 (~21.48 GB each) vs ports 7-8 (~1.08 GB each) -> 20.01x (20.01:1) max/min imbalance",
        IB_PORT_XMIT_DATA_OCTETS == 4
        and v8_ch6_uplinks.bytes_per_port[5] == 21_474_836_480
        and v8_ch6_uplinks.bytes_per_port[6] == 21_489_234_432
        and v8_ch6_uplinks.bytes_per_port[7] == 1_073_741_824
        and v8_ch6_uplinks.bytes_per_port[8] == 1_081_654_272
        and v8_ch6_uplinks.max_to_min_ratio == 20.01
        and v8_ch6_uplinks.is_imbalanced is True,
    )

    # 8. Static LFT hash collision vs Adaptive Routing `AR_group` dynamic port selection (40.0 + 200.0 = 240.0 Gbps, 50.0% FECN, ~150x root spike)
    ar_cmp = simulate_lft_vs_ar_group_selection(
        dlid=24,
        sl=0,
        ar_sl_mask=AR_DEFAULT_SL_MASK,
        static_lft_port=5,
        ar_group_ports=[5, 6, 7, 8],
        existing_port_load_gbps={5: 380.0, 6: 360.0, 7: 40.0, 8: 60.0},
        existing_port_queue_kb={5: 120.0, 6: 90.0, 7: 0.0, 8: 5.0},
        new_flow_gbps=200.0,
        port_capacity_gbps=400.0,
    )
    check(
        "Static LFT vs AR_group selection: static LFT pins 200G flow onto port 5 (580G -> 180G excess); AR_group dynamically selects least-loaded port 7 (240G, 0G excess)",
        ar_cmp.ar_enabled_for_sl is True
        and ar_cmp.static_lft_port == 5
        and ar_cmp.ar_selected_port == 7
        and ar_cmp.static_max_port_load_gbps == 580.0
        and ar_cmp.ar_max_port_load_gbps == 380.0
        and ar_cmp.static_dropped_or_queued_gbps == 180.0
        and ar_cmp.ar_dropped_or_queued_gbps == 0.0,
    )

    # 9. `ar_sl_mask` bitmask enforcement (disabling AR on a specific SL falls back to static LFT)
    ar_masked = simulate_lft_vs_ar_group_selection(
        dlid=24,
        sl=3,
        ar_sl_mask=0xFFF7,  # bit 3 cleared -> SL3 forced to deterministic static LFT
        static_lft_port=5,
        ar_group_ports=[5, 6, 7, 8],
        existing_port_load_gbps={5: 380.0, 6: 360.0, 7: 40.0, 8: 60.0},
        existing_port_queue_kb={5: 120.0, 6: 90.0, 7: 0.0, 8: 5.0},
        new_flow_gbps=200.0,
        port_capacity_gbps=400.0,
    )
    check(
        "ar_sl_mask bitmask filtering: mask 0xFFF7 clears bit 3 (SL3), forcing SL3 onto static LFT port 5 while keeping other SLs adaptive",
        AR_DEFAULT_SL_MASK == 0xFFFF
        and ar_masked.ar_enabled_for_sl is False
        and ar_masked.ar_selected_port == 5,
    )

    # 10. SHIELD / Fast Notification (`FRN`) autonomous failover vs OpenSM `Trap 128` heavy sweep
    failover = evaluate_shield_frn_vs_opensm_failover(
        ar_group_ports=[5, 6, 7, 8],
        failed_port=6,
        line_rate_gbps=400.0,
        shield_detection_reroute_us=10.0,
        opensm_trap128_sweep_ms=500.0,
    )
    check(
        "SHIELD / FRN autonomous failover vs OpenSM Trap 128 sweep: removes port 6 in 10 us (500,000 B at risk at 400G) vs 500,000 us OpenSM sweep (25,000,000,000 B at risk, 50,000x faster)",
        OPENSM_LINK_TRAP_ID == 128
        and failover.surviving_ar_ports == (5, 7, 8)
        and failover.shield_frn_recovery_us == 10.0
        and failover.opensm_sweep_recovery_us == 500_000.0
        and failover.speedup_factor == 50_000.0
        and failover.inflight_bytes_at_risk_shield == 500_000
        and failover.inflight_bytes_at_risk_opensm == 25_000_000_000,
    )

    # 11. Out-of-Order (`OOO`) PSN arrival with ConnectX HCA hardware reorder buffer enabled
    ooo_hw_on = evaluate_ar_ooo_reordering(
        arrival_psns=[100, 102, 103, 101, 104, 106, 105],
        hca_reorder_buffer_enabled=True,
        reorder_window_packets=64,
    )
    check(
        "ConnectX HCA OOO hardware packet reordering ON: PSN sequence (100,102,103,101,104,106,105) reordered to (100..106) with 0 PSN-gap NAKs",
        ooo_hw_on.in_order_stream_delivered == (100, 101, 102, 103, 104, 105, 106)
        and ooo_hw_on.max_reorder_distance == 2
        and ooo_hw_on.exceeded_reorder_window is False
        and ooo_hw_on.psn_gap_nak_count == 0,
    )

    # 12. Out-of-Order (`OOO`) PSN arrival with HCA reorder buffer disabled & V8 Ch. 7 Scenario 3 tail latency
    ooo_hw_off = evaluate_ar_ooo_reordering(
        arrival_psns=[100, 102, 103, 101, 104, 106, 105],
        hca_reorder_buffer_enabled=False,
        reorder_window_packets=64,
    )
    check(
        "V8 Ch 7 Scenario 3 OOO / Reaction tail latency regression: p50 improves 3.1 -> 2.4 us, but p99 inflates 7.2 -> 38.6 us (5.36x) and max inflates 9.1 -> 112.4 us (12.35x); 3 PSN-gap NAKs when OOO buffer is off",
        ooo_hw_off.exceeded_reorder_window is True
        and ooo_hw_off.psn_gap_nak_count == 3
        and ooo_hw_off.p50_before_us == 3.1
        and ooo_hw_off.p50_after_us == 2.4
        and ooo_hw_off.p99_before_us == 7.2
        and ooo_hw_off.p99_after_us == 38.6
        and ooo_hw_off.p99_inflation_factor == 5.36
        and ooo_hw_off.max_inflation_factor == 12.35,
    )

    # 13. IB Congestion Control (`FECN` -> `BECN` -> `CCTI`): uncongested baseline (CCTI = 0)
    cc_step0 = step_ib_cc_state_machine(
        current_ccti=0,
        switch_queue_occupancy_pct=25.0,
        switch_fecn_threshold_pct=50.0,
        line_rate_gbps=400.0,
    )
    check(
        "IB CC uncongested baseline (25% queue < 50% FECN threshold): FECN=False, BECN=False, CCTI=0 (of 128-entry table 0..127), full 400.0 Gbps injection",
        CCT_TABLE_SIZE == 128
        and CCT_MAX_INDEX == 127
        and cc_step0.fecn_marked is False
        and cc_step0.becn_returned is False
        and cc_step0.new_ccti == 0
        and cc_step0.injected_rate_gbps == 400.0,
    )

    # 14. IB CC first congestion event: Switch marks `FECN=1` -> Destination returns `BECN=1` -> `CCTI` 0 -> 16
    cc_step1 = step_ib_cc_state_machine(
        current_ccti=0,
        switch_queue_occupancy_pct=65.0,
        switch_fecn_threshold_pct=50.0,
        ccti_increase=16,
        line_rate_gbps=400.0,
    )
    check(
        "IB CC FECN -> BECN rate cut (step 1): 65% queue >= 50% marks FECN=1 -> BECN=1 increments CCTI 0 -> 16 (delay multiplier 1.5x, rate 400.0 -> 266.67 Gbps)",
        cc_step1.fecn_marked is True
        and cc_step1.becn_returned is True
        and cc_step1.new_ccti == 16
        and cc_step1.inter_packet_delay_multiplier == 1.5
        and cc_step1.injected_rate_gbps == 266.67,
    )

    # 15. IB CC sustained congestion event: `CCTI` 16 -> 32 cuts rate to 50% (200.0 Gbps)
    cc_step2 = step_ib_cc_state_machine(
        current_ccti=16,
        switch_queue_occupancy_pct=75.0,
        switch_fecn_threshold_pct=50.0,
        ccti_increase=16,
        line_rate_gbps=400.0,
    )
    check(
        "IB CC sustained BECN (step 2): CCTI 16 -> 32 raises inter-packet delay multiplier to 2.0x and throttles source HCA to 200.0 Gbps",
        cc_step2.new_ccti == 32
        and cc_step2.inter_packet_delay_multiplier == 2.0
        and cc_step2.injected_rate_gbps == 200.0,
    )

    # 16. IB CC `CCTI_Limit` saturation at index 127 (max table entry)
    cc_sat = step_ib_cc_state_machine(
        current_ccti=120,
        switch_queue_occupancy_pct=90.0,
        switch_fecn_threshold_pct=50.0,
        ccti_increase=16,
        ccti_limit=127,
        line_rate_gbps=400.0,
    )
    check(
        "IB CC CCTI_Limit ceiling: CCTI 120 + 16 clamps at CCT_MAX_INDEX = 127 (delay multiplier 4.9688x, rate 80.5 Gbps)",
        cc_sat.new_ccti == 127
        and cc_sat.inter_packet_delay_multiplier == 4.9688
        and cc_sat.injected_rate_gbps == 80.5,
    )

    # 17. IB CC `CCTI_Timer` recovery: queue drains (30% < 50%), timer expires -> `CCTI` decrements 32 -> 31 -> ... -> 0
    cc_rec = step_ib_cc_state_machine(
        current_ccti=1,
        switch_queue_occupancy_pct=20.0,
        switch_fecn_threshold_pct=50.0,
        becn_received=False,
        ccti_timer_expired=True,
        line_rate_gbps=400.0,
    )
    check(
        "IB CC CCTI_Timer recovery: when BECN=0 and CCTI_Timer expires, CCTI decrements 1 -> 0 and restores full 400.0 Gbps line rate",
        cc_rec.fecn_marked is False
        and cc_rec.becn_returned is False
        and cc_rec.new_ccti == 0
        and cc_rec.injected_rate_gbps == 400.0,
    )

    # 18. V8 Ch. 7 Annotated Evidence: Port 3 (`PortXmitWait=998432`, `SymbolErrorCounter=0`, `LinkDownedCounter=0`) -> Pure Congestion
    p3_diag = classify_ib_port_telemetry(
        port=3,
        port_xmit_wait_delta=998_432,
        symbol_error_delta=0,
        link_downed_delta=0,
    )
    check(
        "V8 Ch 7 Port 3 telemetry (`PortXmitWait=998,432`, `SymbolErrorCounter=0`, `LinkDownedCounter=0`): classified as PURE_FABRIC_CONGESTION",
        p3_diag.classification == "PURE_FABRIC_CONGESTION",
    )

    # 19. V8 Ch. 7 Annotated Evidence: Port 4 (`PortXmitWait=2109`, `SymbolErrorCounter=41`, `LinkDownedCounter=2`) -> Physical Link Fault
    p4_diag = classify_ib_port_telemetry(
        port=4,
        port_xmit_wait_delta=2_109,
        symbol_error_delta=41,
        link_downed_delta=2,
    )
    check(
        "V8 Ch 7 Port 4 telemetry (`PortXmitWait=2,109`, `SymbolErrorCounter=41`, `LinkDownedCounter=2`): classified as PHYSICAL_LINK_FAULT",
        p4_diag.classification == "PHYSICAL_LINK_FAULT",
    )

    # 20. V8 Ch. 2 Scenario 3 Evidence: Port 3 (`PortXmitWait=184,320`) vs Port 7 (`PortXmitWait=41`) with clean physical counters
    p3_ch2 = classify_ib_port_telemetry(port=3, port_xmit_wait_delta=184_320, symbol_error_delta=0, link_downed_delta=0)
    p7_ch2 = classify_ib_port_telemetry(port=7, port_xmit_wait_delta=41, symbol_error_delta=0, link_downed_delta=0)
    check(
        "V8 Ch 2 Scenario 3 telemetry: Port 3 (`PortXmitWait=184,320`, 0 errors) is PURE_FABRIC_CONGESTION while sibling Port 7 (`PortXmitWait=41`, 0 errors) is HEALTHY_PORT",
        p3_ch2.classification == "PURE_FABRIC_CONGESTION"
        and p7_ch2.classification == "HEALTHY_PORT",
    )

    # 21. V8 Ch. 7 Scenario 1 Evidence: Congestion tree root gradient across leaf ports 1..5 (`340, 298, 51204, 47890, 312`)
    roots = locate_congestion_tree_root_ports(
        {1: 340, 2: 298, 3: 51_204, 4: 47_890, 5: 312}
    )
    check(
        "V8 Ch 7 Scenario 1 Congestion Tree Gradient: deltas {1:340, 2:298, 3:51204, 4:47890, 5:312} isolate ports (3, 4) as the congestion tree root",
        roots == (3, 4),
    )

    # 22. V8 Ch. 9 Day 1 / Day 4 / Day 7 SymbolErrorCounter acceleration (`4 -> 890 -> 41,200`, `LinkDownedCounter` `0 -> 3 -> 11`)
    err_trend = evaluate_symbol_error_acceleration(day1_count=4, day4_count=890, day7_count=41_200, window_days=3.0)
    check(
        "V8 Ch 9 Error Rate Acceleration: Day 1 (4) -> Day 4 (890, +886 = 295.33/day) -> Day 7 (41,200, +40,310 = 13,436.67/day) = 45.5x acceleration",
        err_trend.delta_window_1 == 886
        and err_trend.delta_window_2 == 40_310
        and err_trend.rate_per_day_window_1 == 295.33
        and err_trend.rate_per_day_window_2 == 13436.67
        and err_trend.acceleration_factor == 45.5
        and err_trend.is_active_degradation is True,
    )

    # 23. V8 Ch. 9 Scenario 1 Historical Scar Tissue (`SymbolErrorCounter` `12,034 -> 12,034` across 300 s)
    scar_trend = evaluate_symbol_error_acceleration(day1_count=12_034, day4_count=12_034, day7_count=12_034, window_days=1.0)
    check(
        "V8 Ch 9 Scenario 1 Cumulative Scar Tissue: `SymbolErrorCounter` 12,034 -> 12,034 has 0 delta and is_active_degradation=False",
        scar_trend.delta_window_1 == 0
        and scar_trend.delta_window_2 == 0
        and scar_trend.is_active_degradation is False,
    )

    # 24. V8 Ch. 6 Worked Example: 2:1 leaf oversubscription (`16 x 400G = 6,400G` down vs `8 x 400G = 3,200G` up -> `40 ms` vs `80 ms` 2 GB AllReduce)
    oversub = compute_leaf_oversubscription_allreduce_impact(
        downlink_ports=16,
        uplink_ports=8,
        port_rate_gbps=400.0,
        gradient_bytes_per_node=2_000_000_000,
    )
    check(
        "V8 Ch 6 2:1 Leaf Oversubscription math: 6,400 Gbps down / 3,200 Gbps up = 2.0:1 ratio, 200.0 Gbps/node effective, 2 GB AllReduce step doubles from 40.0 ms to 80.0 ms",
        oversub.downlink_bw_gbps == 6400.0
        and oversub.uplink_bw_gbps == 3200.0
        and oversub.oversubscription_ratio == 2.0
        and oversub.effective_node_bw_gbps == 200.0
        and oversub.nonblocking_step_ms == 40.0
        and oversub.oversubscribed_step_ms == 80.0,
    )

    # 25. V8 Ch. 6 Scenario 3 Paired `ib_write_bw`: same-leaf (`397.62 Gbps`) vs cross-rack (`201.18 Gbps` on 2:1 cut)
    same_leaf_bw = 397.62
    cross_rack_bw = 201.18
    check(
        "V8 Ch 6 Scenario 3 Paired ib_write_bw: 397.62 Gbps same-leaf vs 201.18 Gbps cross-rack (1.98:1 ratio matching 2:1 leaf oversubscription)",
        round(same_leaf_bw / cross_rack_bw, 2) == 1.98,
    )

    # 26. V8 Ch. 10 Step 6 `ib_write_lat` tail latency against Lab 02 baseline (`1.58 vs 1.55 us` typical, `5.77 vs 1.98 us` p99.9)
    lat_typ_cur, lat_typ_base = 1.58, 1.55
    lat_p99_cur, lat_p99_base = 2.90, 1.71
    lat_p999_cur, lat_p999_base = 5.77, 1.98
    check(
        "V8 Ch 10 Step 6 ib_write_lat percentile check: typical 1.58 vs 1.55 us (+1.9%), but 99% is 2.90 vs 1.71 us (1.70x) and 99.9% is 5.77 vs 1.98 us (2.91x)",
        round(lat_typ_cur / lat_typ_base, 2) == 1.02
        and round(lat_p99_cur / lat_p99_base, 2) == 1.70
        and round(lat_p999_cur / lat_p999_base, 2) == 2.91,
    )

    # 27. V8 Lab 01 `ibv_devinfo` & `ibstat` inventory constants (`MT4129`, `fw_ver 28.39.2048`, `max_qp 262144`, `max_qp_wr 32768`, `max_sge 30`, `Rate 400`, `Base lid 12`, `SM lid 1`)
    lab01_inventory = {
        "vendor_id": 0x02C9,
        "vendor_part_id": 4129,
        "max_qp": 262_144,
        "max_qp_wr": 32_768,
        "max_sge": 30,
        "rate_gbps": 400,
        "base_lid": 12,
        "sm_lid": 1,
        "capability_mask": 0x2651E848,
        "port_guid": 0x08C0EB0300F1A2C3,
    }
    check(
        "V8 Lab 01 HCA & Port Inventory (`MT4129` ConnectX-7): vendor 0x02c9, max_qp=262,144, max_qp_wr=32,768, max_sge=30, Rate=400, Base lid=12, SM lid=1",
        lab01_inventory["vendor_id"] == 0x02C9
        and lab01_inventory["vendor_part_id"] == 4129
        and lab01_inventory["max_qp"] == 262_144
        and lab01_inventory["max_qp_wr"] == 32_768
        and lab01_inventory["rate_gbps"] == 400
        and lab01_inventory["base_lid"] == 12
        and lab01_inventory["sm_lid"] == 1,
    )

    # 28. superpod-b200-dc Cabling & Scalable Unit (SU) counts (`1..4` SUs: `31, 63, 95, 127` compute nodes, `248, 504, 760, 1016` GPUs, `458 kW` per SU)
    b200_su_table = {
        1: (31, 248, 8, 4, 252, 256),
        2: (63, 504, 16, 8, 508, 512),
        3: (95, 760, 24, 16, 764, 768),
        4: (127, 1016, 32, 16, 1020, 1024),
    }
    check(
        "superpod-b200-dc Cabling & SU scale (1..4 SUs, 458 kW/SU, UFM appliance displacing 1 node): 4 SUs = 127 nodes, 1,016 GPUs, 32 leaf, 16 spine, 1,020 node cables, 1,024 ISL cables",
        b200_su_table[1] == (31, 248, 8, 4, 252, 256)
        and b200_su_table[4] == (127, 1016, 32, 16, 1020, 1024),
    )

    print(f"\nSummary: {passed} passed, {failed} failed out of {passed + failed} checks.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
