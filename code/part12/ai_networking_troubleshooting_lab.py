"""Self-checking verification lab for Chapter 12.24: AI networking troubleshooting playbook.

Run with:
    python3 -B code/part12/ai_networking_troubleshooting_lab.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_networking_troubleshooting import (
    IBPortEvidence,
    RoCEPathEvidence,
    analyze_cross_layer_iteration,
    audit_pcie_link_and_dma,
    bisect_straggler_node,
    classify_nccl_timeout,
    classify_xid_sequence,
    compare_ib_write_lat_tail,
    diagnose_nvlink_pair,
    evaluate_ib_layered_gates,
    evaluate_roce_layered_gates,
    evaluate_thermal_power_ecc_health,
    trace_pfc_pause_root_port,
)


def _baseline_ib_evidence(**overrides: object) -> IBPortEvidence:
    base = dict(
        hca_id="mlx5_0",
        port=1,
        physical_state="LinkUp",
        logical_state="Active",
        negotiated_rate_gbps=400,
        expected_rate_gbps=400,
        negotiated_width=4,
        expected_width=4,
        base_lid=12,
        sm_lid=1,
        sm_master_count=1,
        sm_activity_advancing=True,
        pkey_compatible=True,
        route_valid=True,
        credit_loop_detected=False,
        symbol_error_delta=0,
        link_downed_delta=0,
        port_rcv_errors_delta=0,
        port_xmit_discards_delta=0,
        port_xmit_wait_delta=0,
        host_rdma_bw_gbps=392.0,
        expected_host_rdma_bw_gbps=400.0,
        host_rdma_p999_lat_us=1.98,
        baseline_p999_lat_us=1.98,
        gdr_bw_gbps=390.0,
        expected_gdr_bw_gbps=400.0,
        pcie_topo_distance="PIX",
        collective_bw_gbps=360.0,
        expected_collective_bw_gbps=380.0,
    )
    base.update(overrides)
    return IBPortEvidence(**base)


def _baseline_roce_evidence(**overrides: object) -> RoCEPathEvidence:
    base = dict(
        netdev="ens1f0",
        rdma_dev="mlx5_0",
        link_up=True,
        speed_gbps=400,
        expected_speed_gbps=400,
        fec_corrected_delta=412,
        fec_uncorrected_delta=0,
        rx_crc_errors_delta=0,
        icmp_ping_ok=True,
        local_mtu=9000,
        path_mtu=9000,
        expected_mtu=9000,
        gid_index=3,
        expected_gid_index=3,
        gid_subnet_matches_route=True,
        qp_rtr_success=True,
        retry_exc_err_count=0,
        dscp_value=26,
        expected_dscp_value=26,
        prio3_packets_delta=51234892,
        rx_ecn_marked_prio3_delta=47829,
        rx_pfc_prio3_delta=412,
        tx_pfc_prio3_delta=14,
        cnp_packets_handled_delta=4500,
        sender_rate_reduced=True,
        pfc_pause_pinned_100pct=False,
    )
    base.update(overrides)
    return RoCEPathEvidence(**base)


def run_lab() -> int:
    passed = 0
    failed = 0

    def check(name: str, cond: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if cond:
            passed += 1
            print(f"  [PASS] {name}")
        else:
            failed += 1
            print(f"  [FAIL] {name} :: {detail}")

    print("=== Chapter 12.24 Lab: AI Networking Troubleshooting Playbook ===")

    # ------------------------------------------------------------------
    # Section 1: InfiniBand 7-Gate Decision Tree (Volume 08 Ch. 10 & 12)
    # ------------------------------------------------------------------
    ib_down = evaluate_ib_layered_gates(_baseline_ib_evidence(physical_state="Polling", logical_state="Down"))
    check(
        "1. IB Gate 1 stops immediately when Physical state != LinkUp",
        ib_down.first_failed_gate == "Gate 1: Physical Layer"
        and ib_down.root_cause_category == "port_down_no_carrier",
        f"got {ib_down}",
    )

    ib_width = evaluate_ib_layered_gates(
        _baseline_ib_evidence(negotiated_rate_gbps=200, negotiated_width=2)
    )
    check(
        "2. IB Gate 1 catches down-trained 200 Gbps (2x) port on a 400 Gbps (4x) NDR link even when State is Active",
        ib_width.first_failed_gate == "Gate 1: Physical Layer"
        and ib_width.root_cause_category == "reduced_rate_or_width",
        f"got {ib_width}",
    )

    ib_sym = evaluate_ib_layered_gates(
        _baseline_ib_evidence(symbol_error_delta=1540, link_downed_delta=2)
    )
    check(
        "3. IB Gate 1 distinguishes rising SymbolErrorCounter/LinkDownedCounter as a physical fault",
        ib_sym.first_failed_gate == "Gate 1: Physical Layer"
        and ib_sym.root_cause_category == "rising_physical_link_errors",
        f"got {ib_sym}",
    )

    ib_init = evaluate_ib_layered_gates(
        _baseline_ib_evidence(logical_state="Initializing", base_lid=0, sm_master_count=0, sm_activity_advancing=False)
    )
    check(
        "4. IB Gate 2 identifies Physical LinkUp + State Initializing + Base lid 0 as Subnet Manager fault",
        ib_init.first_failed_gate == "Gate 2: Subnet Management (Control Plane)"
        and ib_init.root_cause_category == "sm_or_lid_unprogrammed",
        f"got {ib_init}",
    )

    ib_pkey = evaluate_ib_layered_gates(_baseline_ib_evidence(pkey_compatible=False))
    ib_loop = evaluate_ib_layered_gates(_baseline_ib_evidence(credit_loop_detected=True))
    check(
        "5. IB Gate 3 catches P_Key partition mismatch and cyclic credit-loop deadlocks before QP debugging",
        ib_pkey.first_failed_gate == "Gate 3: Routing, Partition (P_Key), and Credit Loop"
        and ib_pkey.root_cause_category == "pkey_mismatch"
        and ib_loop.root_cause_category == "credit_loop_deadlock",
        f"got pkey={ib_pkey}, loop={ib_loop}",
    )

    lat_cmp = compare_ib_write_lat_tail()
    ib_tail = evaluate_ib_layered_gates(_baseline_ib_evidence(host_rdma_p999_lat_us=5.77, baseline_p999_lat_us=1.98))
    check(
        "6. IB Gate 4 catches ib_write_lat p99.9 tail spike (5.77 us vs 1.98 us = 2.9141x) while t_typical looks healthy (1.58 vs 1.55 us)",
        lat_cmp.averages_look_healthy is True
        and lat_cmp.tail_is_degraded is True
        and lat_cmp.p999_ratio == 2.9141
        and ib_tail.first_failed_gate == "Gate 4: Host-Memory RDMA Transport",
        f"got lat_cmp={lat_cmp}, ib_tail={ib_tail}",
    )

    ib_gdr = evaluate_ib_layered_gates(
        _baseline_ib_evidence(gdr_bw_gbps=50.0, pcie_topo_distance="SYS")
    )
    check(
        "7. IB Gate 5 isolates GPUDirect RDMA fallback (50 Gbps on 400G link, SYS topology) when Host RDMA is 392 Gbps",
        ib_gdr.first_failed_gate == "Gate 5: GPUDirect RDMA and Locality"
        and ib_gdr.root_cause_category == "gpudirect_fallback_or_locality_mismatch",
        f"got {ib_gdr}",
    )

    ib_cong = evaluate_ib_layered_gates(
        _baseline_ib_evidence(
            collective_bw_gbps=210.0,
            port_xmit_wait_delta=984500,
            symbol_error_delta=0,
            link_downed_delta=0,
        )
    )
    check(
        "8. IB Gate 6 separates congestion without errors (PortXmitWait > 0, SymbolError == 0, LinkDowned == 0) from bad cables",
        ib_cong.first_failed_gate == "Gate 6: Multi-Node Collective / Fabric Congestion"
        and ib_cong.root_cause_category == "fabric_congestion_without_physical_errors",
        f"got {ib_cong}",
    )

    # ------------------------------------------------------------------
    # Section 2: RoCEv2 / AI Ethernet 6-Gate Decision Tree (Volume 09 Ch. 11)
    # ------------------------------------------------------------------
    roce_fec = evaluate_roce_layered_gates(
        _baseline_roce_evidence(
            fec_corrected_delta=41200,
            fec_uncorrected_delta=3,
            rx_crc_errors_delta=3,
            rx_ecn_marked_prio3_delta=1280,
        )
    )
    check(
        "9. RoCE Gate 1 flags fec_uncorrected_blocks=3 matching rx_crc_errors=3 even when ECN rises secondarily from RDMA retries",
        roce_fec.first_failed_gate == "Gate 1: Physical Layer (Uncorrectable FEC / CRC)"
        and roce_fec.fault_class == "physical_bit_errors_with_crc_loss"
        and "rose secondarily" in roce_fec.explanation,
        f"got {roce_fec}",
    )

    roce_mtu = evaluate_roce_layered_gates(
        _baseline_roce_evidence(icmp_ping_ok=True, local_mtu=9000, path_mtu=1500, expected_mtu=9000)
    )
    check(
        "10. RoCE Gate 2 catches path MTU mismatch (1500 vs 9000) where 64B ping succeeds with 0% loss",
        roce_mtu.first_failed_gate == "Gate 2: L3 IP and MTU Path"
        and roce_mtu.fault_class == "mtu_mismatch_silent_drop",
        f"got {roce_mtu}",
    )

    roce_rtr = evaluate_roce_layered_gates(
        _baseline_roce_evidence(icmp_ping_ok=True, qp_rtr_success=False, gid_index=0, expected_gid_index=3)
    )
    roce_lab04 = evaluate_roce_layered_gates(
        _baseline_roce_evidence(gid_subnet_matches_route=False, retry_exc_err_count=24)
    )
    check(
        "11. RoCE Gate 3 catches Failed to modify QP to RTR (wrong GID index) and Lab 04's 24 RETRY_EXC_ERR device mismatch",
        roce_rtr.first_failed_gate == "Gate 3: RoCEv2 Endpoint / GID / QP State"
        and roce_lab04.first_failed_gate == "Gate 3: RoCEv2 Endpoint / GID / QP State",
        f"got rtr={roce_rtr}, lab04={roce_lab04}",
    )

    roce_qos = evaluate_roce_layered_gates(
        _baseline_roce_evidence(dscp_value=0, prio3_packets_delta=0)
    )
    check(
        "12. RoCE Gate 4 catches DSCP trust boundary drop into lossy Priority 0 queue",
        roce_qos.first_failed_gate == "Gate 4: QoS Classification and Trust Boundary"
        and roce_qos.fault_class == "qos_dscp_trust_mismatch",
        f"got {roce_qos}",
    )

    roce_dcqcn = evaluate_roce_layered_gates(
        _baseline_roce_evidence(rx_ecn_marked_prio3_delta=47829, sender_rate_reduced=False)
    )
    roce_pfc = evaluate_roce_layered_gates(
        _baseline_roce_evidence(pfc_pause_pinned_100pct=True)
    )
    check(
        "13. RoCE Gate 5 distinguishes ECN marks without sender backoff (DCQCN/CNP fault) from persistent PFC pause storms",
        roce_dcqcn.fault_class == "ecn_marks_without_sender_backoff"
        and roce_pfc.fault_class == "persistent_pfc_pause_tree",
        f"got dcqcn={roce_dcqcn}, pfc={roce_pfc}",
    )

    roce_healthy = evaluate_roce_layered_gates(_baseline_roce_evidence())
    check(
        "14. RoCE Lab 03 bounded contention (47,829 ECN marks, 412 rx_pfc, 14 tx_pfc, senders backing off to 89.2/87.1 Gbps) passes to Gate 6",
        roce_healthy.first_failed_gate == "Gate 6: Host / GPU / Collective Layer"
        and roce_healthy.fault_class == "roce_fabric_healthy_or_bounded_contention",
        f"got {roce_healthy}",
    )

    root_port = trace_pfc_pause_root_port(
        [
            {"port_id": "leafA-swp1", "hop_order_from_sender": 1, "queue3_occupancy_pct": 95, "tx_pfc_prio3_delta": 9000, "rx_pfc_prio3_delta": 9200},
            {"port_id": "spine1-swp8", "hop_order_from_sender": 2, "queue3_occupancy_pct": 96, "tx_pfc_prio3_delta": 9200, "rx_pfc_prio3_delta": 9500},
            {"port_id": "leafB-swp17", "hop_order_from_sender": 3, "queue3_occupancy_pct": 98, "tx_pfc_prio3_delta": 9500, "rx_pfc_prio3_delta": 0},
        ]
    )
    check(
        "15. PFC pause-tree tracer identifies the most downstream congested egress port (leafB-swp17 at hop 3, 98% occupancy)",
        root_port == "leafB-swp17",
        f"got {root_port}",
    )

    # ------------------------------------------------------------------
    # Section 3: Xid 3-Tier + Xid 74, NVLink, and PCIe DMA Triage (Volume 20)
    # ------------------------------------------------------------------
    xid_chain = classify_xid_sequence([92, 45, 79])
    check(
        "16. Xid sequence [92, 45, 79] classifies Xid 79 as Tier 3 immediate drain, Xid 92 as precursor, and Xid 45 as preemptive cleanup",
        xid_chain["terminal_xid"] == 79
        and xid_chain["terminal_tier"] == "Tier 3"
        and xid_chain["precursor_xids"] == [92]
        and xid_chain["had_preemptive_cleanup_45"] is True
        and xid_chain["immediate_drain_required"] is True,
        f"got {xid_chain}",
    )

    xid_94 = classify_xid_sequence([94])
    xid_63 = classify_xid_sequence([63])
    xid_48 = classify_xid_sequence([48])
    check(
        "17. Xid 63 is Tier 1 (self-healing remap), Xid 94 is Tier 2 (contained ECC), and Xid 48 is Tier 3 (uncorrectable DBE)",
        xid_63["terminal_tier"] == "Tier 1"
        and xid_94["terminal_tier"] == "Tier 2"
        and xid_48["terminal_tier"] == "Tier 3"
        and xid_48["immediate_drain_required"] is True,
        f"got 63={xid_63}, 94={xid_94}, 48={xid_48}",
    )

    nvl_mig = diagnose_nvlink_pair(2, 3, topo_entry="PIX", expected_topo_entry="NV12", mig_enabled=True)
    nvl_hw = diagnose_nvlink_pair(
        2,
        3,
        topo_entry="PIX",
        expected_topo_entry="NV12",
        mig_enabled=False,
        gpu_a_crc_errors=184213,
        gpu_a_replay_errors=92104,
        gpu_b_crc_errors=0,
        gpu_b_replay_errors=0,
        xid_74_present=True,
    )
    check(
        "18. NVLink PIX fallback is working-as-designed when MIG is enabled, but isolates GPU2_transceiver when MIG is disabled and GPU2 has 184,213 CRC / 92,104 replay errors (Xid 74)",
        nvl_mig.status == "working_as_designed_mig_isolation"
        and nvl_hw.status == "nvlink_hardware_fallback_to_pcie"
        and nvl_hw.faulty_side == "GPU2_transceiver",
        f"got mig={nvl_mig}, hw={nvl_hw}",
    )

    pcie_deg = audit_pcie_link_and_dma(
        bdf="0000:08:00.0",
        cap_gen=4,
        cap_width=16,
        sta_gen=3,
        sta_width=8,
        measured_h2d_gb_s=2.3,
        expected_baseline_gb_s=22.0,
        pcie_replay_counter=127,
    )
    pcie_ok = audit_pcie_link_and_dma(
        bdf="0000:08:00.0",
        cap_gen=4,
        cap_width=16,
        sta_gen=4,
        sta_width=16,
        measured_h2d_gb_s=22.0,
        expected_baseline_gb_s=22.0,
        pcie_replay_counter=0,
    )
    check(
        "19. PCIe audit detects Gen4 x16 -> Gen3 x8 down-training (2.3 GB/s vs 22.0 GB/s baseline, 127 PCIe replays) and verifies full recovery",
        pcie_deg.is_downtrained is True
        and pcie_deg.status == "degraded_pcie_link_or_dma"
        and pcie_ok.is_downtrained is False
        and pcie_ok.status == "healthy_pcie_link",
        f"got deg={pcie_deg}, ok={pcie_ok}",
    )

    # ------------------------------------------------------------------
    # Section 4: NCCL Timeout, Straggler Bisection & Cross-Layer Triage
    # ------------------------------------------------------------------
    nccl_starved = classify_nccl_timeout(
        rank_op_counts={0: 4821, 1: 4821, 2: 4821, 3: 4820},
        lagging_rank_gpu_util_pct=2.0,
        lagging_rank_xid=None,
        lagging_rank_batch_fetch_s=47.31,
    )
    check(
        "20. NCCL timeout with ranks 0-2 at opCount 4821 and rank 3 at opCount 4820 (2% SM util, 47.31s batch fetch) diagnoses data-pipeline starvation on rank 3",
        nccl_starved.failure_mode == "starved_or_straggler_rank"
        and nccl_starved.lagging_ranks == (3,)
        and "data loader" in nccl_starved.recommended_fix,
        f"got {nccl_starved}",
    )

    nccl_deadlock = classify_nccl_timeout(
        rank_op_counts={0: 102, 1: 101, 2: 101, 3: 101},
        rank_op_types={0: "AllReduce_tensor_b", 1: "AllGather_logits", 2: "AllGather_logits", 3: "AllGather_logits"},
    )
    check(
        "21. Divergent collective call types across ranks classify as a permanent code-level deadlock",
        nccl_deadlock.failure_mode == "code_level_deadlock",
        f"got {nccl_deadlock}",
    )

    nccl_fabric = classify_nccl_timeout(
        rank_op_counts={0: 4821, 1: 4821, 2: 4821, 3: 4821},
    )
    check(
        "22. All ranks stalling simultaneously on identical opCount 4821 classifies as a fabric/network stall",
        nccl_fabric.failure_mode == "fabric_stall_all_ranks"
        and nccl_fabric.lagging_ranks == (),
        f"got {nccl_fabric}",
    )

    nccl_xid = classify_nccl_timeout(
        rank_op_counts={0: 4821, 1: 4821, 2: 4821, 3: 4820},
        lagging_rank_xid=79,
    )
    check(
        "23. Lagging rank with Xid 79 classifies as crashed_or_xid_rank rather than network timeout",
        nccl_xid.failure_mode == "crashed_or_xid_rank" and nccl_xid.lagging_ranks == (3,),
        f"got {nccl_xid}",
    )

    # 16-node and 64-node binary search straggler isolation
    nodes_16 = [f"node-{i:02d}" for i in range(16)]
    bisect_16 = bisect_straggler_node(
        nodes_16,
        measure_subset_bw_gb_s=lambda subset: 45.0 if "node-11" in subset else 180.0,
        healthy_threshold_gb_s=150.0,
    )
    nodes_64 = [f"node-{i:02d}" for i in range(64)]
    bisect_64 = bisect_straggler_node(
        nodes_64,
        measure_subset_bw_gb_s=lambda subset: 42.0 if "node-47" in subset else 180.0,
        healthy_threshold_gb_s=150.0,
    )
    check(
        "24. O(log2 N) straggler bisection isolates node-11 in 4 tests across 16 nodes (saving 12 tests) and node-47 in 6 tests across 64 nodes (saving 58 tests)",
        bisect_16.isolated_node == "node-11"
        and bisect_16.tests_executed == 4
        and bisect_16.linear_tests_saved == 12
        and bisect_64.isolated_node == "node-47"
        and bisect_64.tests_executed == 6
        and bisect_64.linear_tests_saved == 58,
        f"got 16={bisect_16}, 64={bisect_64}",
    )

    # Cross-layer iteration breakdown & Heisenbug analysis (Volume 20 Chapter 12)
    cross = analyze_cross_layer_iteration(
        timings_ms={
            "data_load_cpu": 450.0,
            "allreduce_network": 150.0,
            "backward_gpu": 60.0,
            "forward_gpu": 30.0,
            "data_transfer_pcie": 10.0,
            "optimizer_gpu": 10.0,
            "loss_gpu": 8.0,
        },
        nvidia_smi_util_pct=100.0,
        kernel_launch_rate_hz=50.0,
        expected_launch_rate_hz=1000.0,
        throughput_no_profiler=500.0,
        throughput_smi_poll=450.0,
        throughput_nsys=250.0,
    )
    check(
        "25. Cross-layer analyzer identifies data_load_cpu (450.0 ms, 62.67% of 718.0 ms sum) and detects the 100% nvidia-smi utilization lie (50 vs 1000 kernels/sec)",
        cross["dominant_layer"] == "data_load_cpu"
        and cross["dominant_ms"] == 450.0
        and cross["gpu_compute_ms"] == 108.0
        and cross["utilization_lie_detected"] is True,
        f"got {cross}",
    )
    check(
        "26. Profiler Heisenbug calculator quantifies 10.0% overhead for nvidia-smi polling (450 vs 500 samples/s) and 50.0% for Nsight Systems (250 vs 500 samples/s)",
        cross["smi_overhead_pct"] == 10.0
        and cross["nsys_overhead_pct"] == 50.0
        and cross["heisenbug_risk"] is True,
        f"got {cross}",
    )

    # Thermal, power, and ECC rate disambiguation (Volume 20 Labs 02, 03, 04)
    therm_storm = evaluate_thermal_power_ecc_health(
        temp_start_c=55.0,
        temp_end_c=83.0,
        window_s=30.0,
        throttle_reason="HW Thermal Slowdown: Active",
        power_limit_w=300.0,
        default_power_limit_w=300.0,
        ecc_sbe_delta=50,
        ecc_window_minutes=30.0,
    )
    power_cap = evaluate_thermal_power_ecc_health(
        temp_start_c=65.0,
        temp_end_c=67.0,
        window_s=30.0,
        throttle_reason="SW Power Cap: Active",
        power_limit_w=200.0,
        default_power_limit_w=300.0,
        ecc_sbe_delta=1,
        ecc_window_minutes=60.0,
    )
    check(
        "27. Thermal rise (83C - 55C)/30s = 0.9333 C/s (> 0.20 C/s) and ECC rate 50/30min = 100.0/hr (> 10/hr) trigger immediate job stop and GPU drain",
        therm_storm["temp_rise_c_per_s"] == 0.9333
        and therm_storm["cooling_degraded"] is True
        and therm_storm["clock_drop_cause"] == "thermal_slowdown"
        and therm_storm["ecc_rate_per_hour"] == 100.0
        and therm_storm["ecc_action"] == "stop_job_and_drain_gpu_immediately",
        f"got {therm_storm}",
    )
    check(
        "28. Throttle bitmask separates SW Power Cap (200W < 300W default) with 1.0 ECC/hr (warning/monitor) from thermal slowdown",
        power_cap[" cooling_degraded" if " cooling_degraded" in power_cap else "cooling_degraded"] is False
        and power_cap["clock_drop_cause"] == "software_power_cap_below_default"
        and power_cap["ecc_rate_per_hour"] == 1.0,
        f"got {power_cap}",
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(run_lab())
