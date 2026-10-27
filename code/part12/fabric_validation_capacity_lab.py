#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.23: Fabric validation and capacity planning."""

from __future__ import annotations

import math
import sys

from fabric_validation_capacity import (
    AcceptanceStageInput,
    B200_AOC_MAX_M,
    B200_CABLE_MAX_DISTANCE_FRACTION,
    B200_PASSIVE_DAC_100G_MAX_M,
    B200_PASSIVE_DAC_400G_MAX_M,
    B200_PSU_REQUIRED,
    B200_PSU_TOTAL,
    BCM_TOPOGRAPH_AGGREGATION_DELAY_S,
    BCM_TOPOGRAPH_FETCH_ATTEMPTS,
    BCM_TOPOGRAPH_FETCH_TIMEOUT_S,
    BCM_TOPOGRAPH_FETCH_WAIT_S,
    BCM_TOPOGRAPH_MEASURABLES,
    BCM_TOPOGRAPH_PAGE_SIZE,
    BCM_TOPOGRAPH_PORT,
    CableLinkSpec,
    GB300_BF3_PORT_BW_GBPS,
    GB300_BF3_PORTS_PER_TRAY,
    GB300_CX8_BW_GBPS,
    GB300_CX8_NICS_PER_TRAY,
    GB300_ETH_COMPUTE_LEAF_BLOCKING_RATIO,
    GB300_ETH_COMPUTE_LEAF_UPLINKS_400G,
    GB300_ETH_MGMT_LEAF_UPLINKS_400G,
    GB300_ETH_STORAGE_LEAF_UPLINKS_400G,
    GB300_GPUS_PER_RACK,
    GB300_GPUS_PER_TRAY,
    GB300_INBAND_MGMT_BW_GBPS,
    GB300_NVLINK5_BW_TBPS,
    GB300_NVLINK5_LINKS_PER_GPU,
    GB300_NVLINK_C2C_BW_GBPS,
    GB300_NVLINK_CHIPS_PER_SWITCH_TRAY,
    GB300_NVLINK_SWITCH_TRAYS_PER_RACK,
    GB300_OOB_SWITCH_PORTS_1G,
    GB300_POWER_SHELVES_PER_RACK,
    GB300_PSU_KW,
    GB300_PSUS_PER_SHELF,
    GB300_Q3400_RADIX,
    GB300_RACKS_PER_SU,
    GB300_SHELF_POWER_KW,
    GB300_SN5600_RADIX,
    GB300_SU_TDP_MW,
    GB300_SUPERCHIPS_PER_TRAY,
    GB300_TRAYS_PER_RACK,
    L1_DOM_RX_POWER_MIN_DBM,
    L1_DOM_TEMP_MAX_C,
    L1_DOM_TX_POWER_MIN_DBM,
    L1_POST_FEC_BER_CEILING,
    L1_PRE_FEC_BER_CEILING,
    SUPERPOD_B200_BOM_TABLE,
    SUPERPOD_GB300_SCALE_TABLE,
    SUPERPOD_GB300_STORAGE_PERF_GBPS,
    V8_CH11_CONSTRAINED_LEAF_RADIX,
    V8_CH11_DOWNLINK_CAP_GBPS,
    V8_CH11_ENDPOINTS_PER_RACK,
    V8_CH11_INFERENCE_P99_ISOLATED_MS,
    V8_CH11_INFERENCE_P99_SEPARATED_VL_MS,
    V8_CH11_INFERENCE_P99_SHARED_VL_MS,
    V8_CH11_NONBLOCKING_LEAF_RADIX,
    V8_CH11_OVERSUB_2TO1_CAP_GBPS,
    V8_CH11_OVERSUB_2TO1_UPLINKS,
    V8_CH11_RACKS,
    V8_CH11_TOTAL_GPUS,
    V8_INDEX_CLUSTER_NODES,
    V8_INDEX_STEP_TIME_VARIATION_PCT,
    V8_LAB01_BASE_LID,
    V8_LAB01_CAP_MASK_HEX,
    V8_LAB01_FW_VER,
    V8_LAB01_MAX_QP,
    V8_LAB01_MAX_QP_WR,
    V8_LAB01_MAX_SGE,
    V8_LAB01_MT4129_PART_ID,
    V8_LAB01_NODE_GUID,
    V8_LAB01_PORT_GUID_HEX,
    V8_LAB01_RATE_GBPS,
    V8_LAB01_SM_LID,
    V8_LAB01_VENDOR_ID_HEX,
    V9_CH10_COLLECTIVE_RANKS,
    V9_CH10_COLLECTIVE_RX_ECN_PRIO3,
    V9_CH10_COLLECTIVE_RX_PFC_PRIO3,
    V9_CH10_DOWNLINK_DEMAND_GBPS,
    V9_CH10_IDLE_TAIL_DROPS,
    V9_CH10_NODE_INJECTION_GBPS,
    V9_CH10_OVERSUB_DEGRADED,
    V9_CH10_OVERSUB_NORMAL,
    V9_CH10_PAIRWISE_BW_GBPS,
    V9_CH10_RACK_NODES,
    V9_CH10_RAIL_BW_GBPS,
    V9_CH10_RAILS_PER_NODE,
    V9_CH10_SHARED_TAIL_DROPS,
    V9_CH10_UPLINK_CAP_DEGRADED_GBPS,
    V9_CH10_UPLINK_CAP_NORMAL_GBPS,
    V9_CH10_UPLINKS_DEGRADED,
    V9_CH10_UPLINKS_NORMAL,
    V9_LAB01_FEC_CORRECTED_BASELINE,
    V9_LAB01_FEC_UNCORRECTED_BASELINE,
    V9_LAB01_MTU_BYTES,
    V9_LAB01_RX_BYTES,
    V9_LAB01_RX_PACKETS,
    V9_LAB01_SPEED_MBPS,
    V9_LAB02_TX_BYTES,
    V9_LAB03_CONTENTION_DURATION_S,
    V9_LAB03_CONTENTION_RX_ECN_PRIO3,
    V9_LAB03_CONTENTION_RX_PFC_PRIO3,
    V9_LAB03_CONTENTION_RX_PRIO3_PKTS,
    V9_LAB03_CONTENTION_TX_PFC_PRIO3,
    V9_LAB03_CONTENTION_TX_PRIO3_PKTS,
    V9_LAB03_IDLE_RX_PRIO3_PKTS,
    V9_LAB03_IDLE_TX_PRIO3_PKTS,
    V9_LAB03_SENDER_A_BW_GBPS,
    V9_LAB03_SENDER_B_BW_GBPS,
    V9_LAB04_BROKEN_BW_GBPS,
    V9_LAB04_BROKEN_DURATION_S,
    V9_LAB04_BROKEN_RETRY_EXC_ERR,
    V9_LAB04_BROKEN_RX_ECN_PRIO3,
    V9_LAB04_HEALTHY_BW_GBPS,
    V9_LAB04_HEALTHY_DURATION_S,
    calculate_clos_bom,
    evaluate_acceptance_ladder,
    generate_slurm_topology_conf,
    model_cut_and_collective_impact,
    validate_cable_matrix_diff,
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

    print("=== Chapter 12.23 Lab: Fabric Validation and Capacity Planning ===")

    # 1. Multi-stage acceptance gating (L1 -> L5): healthy baseline passes all 5 stages
    healthy_input = AcceptanceStageInput(
        active_links=1024,
        expected_links=1024,
        min_negotiated_rate_gbps=400,
        expected_rate_gbps=400,
        min_lane_width=4,
        expected_lane_width=4,
        max_pre_fec_ber=2.5e-7,
        max_post_fec_ber=0.0,
        min_dom_rx_dbm=-2.1,
        max_dom_temp_c=54.0,
        uncorrected_fec_delta=0,
        symbol_error_delta=0,
        p2p_host_bw_gbps=392.11,
        p2p_gdr_bw_gbps=390.40,
        p2p_min_required_bw_gbps=380.0,
        p2p_lat_us=1.85,
        p2p_max_lat_us=2.50,
        retry_exc_err_delta=0,
        bisection_per_pair_bw_gbps=388.0,
        bisection_min_required_bw_gbps=370.0,
        ring_min_pair_bw_gbps=389.5,
        allreduce_busbw_gbps=361.36,
        allreduce_min_busbw_gbps=340.0,
        alltoall_busbw_gbps=348.0,
        alltoall_min_busbw_gbps=320.0,
        nccl_wrong_elements=0,
        burnin_hours=24.0,
        min_burnin_hours=12.0,
        link_flaps_during_burnin=0,
        tail_drops_during_burnin=0,
        step_time_p99_regression_pct=1.8,
        max_step_time_p99_regression_pct=5.0,
        n_minus_1_verified=True,
    )
    rep_ok = evaluate_acceptance_ladder(healthy_input)
    check(
        "L1-L5 acceptance ladder: healthy 1024-link 400G cluster passes all 5 gates",
        rep_ok.overall_accepted
        and rep_ok.first_failed_stage is None
        and all(rep_ok.stage_results.values()),
    )

    # 2. L1 physical/DOM/BER failure: passing L4 collective cannot excuse failed L1 (V9 Ch 10 Fig 9.10.1 trap)
    l1_trap_input = AcceptanceStageInput(**{**healthy_input.__dict__, "uncorrected_fec_delta": 12, "min_dom_rx_dbm": -8.4})
    rep_l1_trap = evaluate_acceptance_ladder(l1_trap_input)
    check(
        "V9 Ch 10 Fig 9.10.1 acceptance trap: passing L4 collective rejected when L1 FEC/DOM fails",
        not rep_l1_trap.overall_accepted
        and rep_l1_trap.first_failed_stage == "L1"
        and rep_l1_trap.stage_results["L4"] is True
        and L1_PRE_FEC_BER_CEILING == 1e-5
        and L1_POST_FEC_BER_CEILING == 1e-15
        and L1_DOM_RX_POWER_MIN_DBM == -6.0
        and L1_DOM_TX_POWER_MIN_DBM == -4.0
        and L1_DOM_TEMP_MAX_C == 70.0,
    )

    # 3. L2 GPUDirect RDMA / wrong device selection fault (V9 Lab 04: 392 Gbps in 2.1s vs 156 Gbps in 8.2s, 24 RETRY_EXC_ERR)
    l2_fault_input = AcceptanceStageInput(
        **{
            **healthy_input.__dict__,
            "p2p_gdr_bw_gbps": V9_LAB04_BROKEN_BW_GBPS,
            "retry_exc_err_delta": V9_LAB04_BROKEN_RETRY_EXC_ERR,
        }
    )
    rep_l2 = evaluate_acceptance_ladder(l2_fault_input)
    check(
        "V9 Lab 04 L2 RoCE device-selection fault: 392 Gbps (2.1s) -> 156 Gbps (8.2s) with 24 RETRY_EXC_ERR & 142 ECN marks caught at L2",
        not rep_l2.overall_accepted
        and rep_l2.first_failed_stage == "L2"
        and math.isclose(V9_LAB04_HEALTHY_BW_GBPS / V9_LAB04_BROKEN_BW_GBPS, 2.5128, rel_tol=1e-3)
        and V9_LAB04_HEALTHY_DURATION_S == 2.1
        and V9_LAB04_BROKEN_DURATION_S == 8.2
        and V9_LAB04_BROKEN_RX_ECN_PRIO3 == 142,
    )

    # 4. L3 Bisection cut fault: pairwise healthy (392.11 Gbps) but 2:1 cross-rack cut halves bisection to 201.18 Gbps
    l3_fault_input = AcceptanceStageInput(**{**healthy_input.__dict__, "bisection_per_pair_bw_gbps": 201.18})
    rep_l3 = evaluate_acceptance_ladder(l3_fault_input)
    check(
        "L3 half-bisection gate catches 2:1 cross-rack cut (201.18 Gbps vs 370.0 Gbps gate) even when L2 pairwise is 392.11 Gbps",
        not rep_l3.overall_accepted
        and rep_l3.first_failed_stage == "L3"
        and rep_l3.stage_results["L1"]
        and rep_l3.stage_results["L2"],
    )

    # 5. L4 Full-scale collective gate: #wrong > 0 or low alltoall_perf busbw fails L4
    l4_fault_input = AcceptanceStageInput(**{**healthy_input.__dict__, "nccl_wrong_elements": 3})
    rep_l4 = evaluate_acceptance_ladder(l4_fault_input)
    check(
        "L4 collective gate rejects silent data corruption (#wrong = 3 > 0) despite high busbw",
        not rep_l4.overall_accepted and rep_l4.first_failed_stage == "L4",
    )

    # 6. L5 Multi-hour burn-in & shared contention gate (V9 Ch 10: 0 idle tail drops vs 38,210 shared tail drops)
    l5_fault_input = AcceptanceStageInput(
        **{
            **healthy_input.__dict__,
            "tail_drops_during_burnin": V9_CH10_SHARED_TAIL_DROPS,
            "n_minus_1_verified": False,
        }
    )
    rep_l5 = evaluate_acceptance_ladder(l5_fault_input)
    check(
        "V9 Ch 10 L5 burn-in gate catches 38,210 shared-production tail drops (vs 0 idle) and unverified N-1 claim",
        not rep_l5.overall_accepted
        and rep_l5.first_failed_stage == "L5"
        and V9_CH10_IDLE_TAIL_DROPS == 0
        and V9_CH10_SHARED_TAIL_DROPS == 38210,
    )

    # 7. V9 Ch 10 pairwise vs 16-rank collective congestion evidence
    check(
        "V9 Ch 10 pairwise vs collective: 392.11 Gb/s pairwise vs 16-rank all-reduce rx_ecn_marked_prio3=288,400 & rx_pfc_prio3=61,200",
        V9_CH10_PAIRWISE_BW_GBPS == 392.11
        and V9_CH10_COLLECTIVE_RANKS == 16
        and V9_CH10_COLLECTIVE_RX_ECN_PRIO3 == 288400
        and V9_CH10_COLLECTIVE_RX_PFC_PRIO3 == 61200,
    )

    # 8. V8 Index & Lab 01 InfiniBand inventory constants
    check(
        "V8 Index (128 nodes, >20% step-time variation) & Lab 01 inventory (MT4129, fw 28.39.2048, GUID 08c0:eb03:00f1:a2c3, vendor 0x02c9, max_qp 262144, max_qp_wr 32768, max_sge 30, Base lid 12, SM lid 1, Rate 400)",
        V8_INDEX_CLUSTER_NODES == 128
        and V8_INDEX_STEP_TIME_VARIATION_PCT == 20.0
        and V8_LAB01_MT4129_PART_ID == 4129
        and V8_LAB01_VENDOR_ID_HEX == "0x02c9"
        and V8_LAB01_FW_VER == "28.39.2048"
        and V8_LAB01_NODE_GUID == "08c0:eb03:00f1:a2c3"
        and V8_LAB01_PORT_GUID_HEX == "0x08c0eb0300f1a2c3"
        and V8_LAB01_CAP_MASK_HEX == "0x2651e848"
        and V8_LAB01_MAX_QP == 262144
        and V8_LAB01_MAX_QP_WR == 32768
        and V8_LAB01_MAX_SGE == 30
        and V8_LAB01_BASE_LID == 12
        and V8_LAB01_SM_LID == 1
        and V8_LAB01_RATE_GBPS == 400,
    )

    # 9. V9 Labs 01-03 Ethernet inventory & 60s bounded contention deltas
    rx_pkt_delta = V9_LAB03_CONTENTION_RX_PRIO3_PKTS - V9_LAB03_IDLE_RX_PRIO3_PKTS
    tx_pkt_delta = V9_LAB03_CONTENTION_TX_PRIO3_PKTS - V9_LAB03_IDLE_TX_PRIO3_PKTS
    total_sender_bw = round(V9_LAB03_SENDER_A_BW_GBPS + V9_LAB03_SENDER_B_BW_GBPS, 1)
    check(
        "V9 Labs 01-03 counter baselines & 60s contention deltas: 892,481,382,400 rx_bytes, 481,029,120,384 tx_bytes, 47,829 ECN marks, 412 rx_pfc, 14 tx_pfc, 89.2 + 87.1 = 176.3 Gb/s",
        V9_LAB01_RX_PACKETS == 1024567
        and V9_LAB01_RX_BYTES == 892481382400
        and V9_LAB02_TX_BYTES == 481029120384
        and V9_LAB01_FEC_CORRECTED_BASELINE == 412
        and V9_LAB01_FEC_UNCORRECTED_BASELINE == 0
        and V9_LAB01_SPEED_MBPS == 400000
        and V9_LAB01_MTU_BYTES == 9000
        and V9_LAB03_CONTENTION_DURATION_S == 60
        and V9_LAB03_CONTENTION_RX_ECN_PRIO3 == 47829
        and V9_LAB03_CONTENTION_RX_PFC_PRIO3 == 412
        and V9_LAB03_CONTENTION_TX_PFC_PRIO3 == 14
        and rx_pkt_delta == 51132578
        and tx_pkt_delta == 48811613
        and total_sender_bw == 176.3,
    )

    # 10. V9 Ch 10 worked capacity cut: 16 nodes x 800G = 12,800G vs 8x400G = 3,200G (4.00:1) & 7x400G = 2,800G (4.57:1)
    cut_v9 = model_cut_and_collective_impact(
        nodes_per_leaf=V9_CH10_RACK_NODES,
        injection_per_node_gbps=V9_CH10_NODE_INJECTION_GBPS,
        uplinks_normal=V9_CH10_UPLINKS_NORMAL,
        uplinks_degraded=V9_CH10_UPLINKS_DEGRADED,
        uplink_rate_gbps=V9_CH10_RAIL_BW_GBPS,
        collective_payload_bytes=2_000_000_000,
        total_ranks=16,
    )
    check(
        "V9 Ch 10 capacity cut math: 16 x 800G = 12,800 Gb/s vs 8x400G = 3,200 Gb/s (4.00:1) and N-1 7x400G = 2,800 Gb/s (4.57:1)",
        cut_v9.downlink_demand_gbps == 12800.0
        and cut_v9.uplink_capacity_normal_gbps == 3200.0
        and cut_v9.uplink_capacity_degraded_gbps == 2800.0
        and cut_v9.oversub_normal == 4.00
        and cut_v9.oversub_degraded == 4.57
        and V9_CH10_OVERSUB_NORMAL == 4.0
        and V9_CH10_OVERSUB_DEGRADED == 4.57,
    )

    # 11. V8 Ch 6 & Ch 11 leaf radix and 2 GB AllReduce step time under 1:1 (40 ms), 2:1 (80 ms), and N-1 4:1 (160 ms)
    cut_v8 = model_cut_and_collective_impact(
        nodes_per_leaf=V8_CH11_ENDPOINTS_PER_RACK,
        injection_per_node_gbps=400.0,
        uplinks_normal=V8_CH11_OVERSUB_2TO1_UPLINKS,
        uplinks_degraded=4,  # 1 of 2 spines lost -> 4 uplinks left (1,600 Gbps)
        uplink_rate_gbps=400.0,
        collective_payload_bytes=2_000_000_000,
        total_ranks=V8_CH11_TOTAL_GPUS,
    )
    check(
        "V8 Ch 6 & Ch 11 256-GPU sizing & 2 GB AllReduce: 16x400G = 6,400G requires 32-port leaf for 1:1 (40 ms); 24-port leaf w/ 8 uplinks = 3,200G (2:1, 200G/node, 80 ms); 1-spine loss = 1,600G (4:1, 100G/node, 160 ms)",
        V8_CH11_RACKS == 16
        and V8_CH11_TOTAL_GPUS == 256
        and V8_CH11_DOWNLINK_CAP_GBPS == 6400
        and V8_CH11_NONBLOCKING_LEAF_RADIX == 32
        and V8_CH11_CONSTRAINED_LEAF_RADIX == 24
        and V8_CH11_OVERSUB_2TO1_CAP_GBPS == 3200
        and cut_v8.oversub_normal == 2.00
        and cut_v8.oversub_degraded == 4.00
        and cut_v8.effective_node_bw_normal_gbps == 200.0
        and cut_v8.effective_node_bw_degraded_gbps == 100.0
        and cut_v8.allreduce_time_uncongested_ms == 40.0
        and cut_v8.allreduce_time_normal_ms == 80.0
        and cut_v8.allreduce_time_degraded_ms == 160.0,
    )

    # 12. V8 Ch 11 Scenario 3 shared vs separated VL inference p99 latency
    check(
        "V8 Ch 11 Scenario 3 shared training/inference VL isolation: 1.8 ms (isolated) -> 14.2 ms (shared VL, 7.89x) -> 3.1 ms (separated VL)",
        V8_CH11_INFERENCE_P99_ISOLATED_MS == 1.8
        and V8_CH11_INFERENCE_P99_SHARED_VL_MS == 14.2
        and V8_CH11_INFERENCE_P99_SEPARATED_VL_MS == 3.1
        and math.isclose(V8_CH11_INFERENCE_P99_SHARED_VL_MS / V8_CH11_INFERENCE_P99_ISOLATED_MS, 7.8889, rel_tol=1e-3),
    )

    # 13. 2-Tier (3-stage) Clos BOM calculator: 1,024 GPUs (128 nodes) on 64-port 400G switches with 5% spares
    bom_1024 = calculate_clos_bom(gpus=1024, gpus_per_node=8, switch_radix=64, tiers=2, spare_rate=0.05)
    check(
        "2-Tier 1:1 Clos BOM (1,024 GPUs, 64-port switches, 5% spares): 32 leaves, 16 spines (48 active, 51 w/ spares), 2,048 active cables (2,151 w/ spares), 4,096 active optics (4,301 w/ spares)",
        bom_1024.nodes == 128
        and bom_1024.leaf_switches == 32
        and bom_1024.spine_switches == 16
        and bom_1024.superspine_switches == 0
        and bom_1024.total_switches_active == 48
        and bom_1024.total_switches_with_spares == 51
        and bom_1024.host_to_leaf_cables_active == 1024
        and bom_1024.leaf_to_spine_cables_active == 1024
        and bom_1024.total_cables_active == 2048
        and bom_1024.total_cables_with_spares == 2151
        and bom_1024.total_transceivers_active == 4096
        and bom_1024.total_transceivers_with_spares == 4301,
    )

    # 14. 2-Tier (3-stage) Clos BOM calculator: 2,048 GPUs (256 nodes, max 64-port 2-tier) with 5% spares
    bom_2048 = calculate_clos_bom(gpus=2048, gpus_per_node=8, switch_radix=64, tiers=2, spare_rate=0.05)
    check(
        "2-Tier 1:1 Clos BOM (2,048 GPUs, 64-port switches, 5% spares): 64 leaves, 32 spines (96 active, 101 w/ spares), 4,096 active cables (4,301 w/ spares), 8,192 active optics (8,602 w/ spares)",
        bom_2048.nodes == 256
        and bom_2048.leaf_switches == 64
        and bom_2048.spine_switches == 32
        and bom_2048.total_switches_active == 96
        and bom_2048.total_switches_with_spares == 101
        and bom_2048.total_cables_active == 4096
        and bom_2048.total_cables_with_spares == 4301
        and bom_2048.total_transceivers_active == 8192
        and bom_2048.total_transceivers_with_spares == 8602,
    )

    # 15. 3-Tier (5-stage) Clos BOM calculator: 4,096 GPUs (512 nodes) at 1:1 vs 2:1 spine-to-superspine oversubscription
    bom_4096_1to1 = calculate_clos_bom(
        gpus=4096, gpus_per_node=8, switch_radix=64, tiers=3, spine_oversubscription=1.0, spare_rate=0.05
    )
    bom_4096_2to1 = calculate_clos_bom(
        gpus=4096, gpus_per_node=8, switch_radix=64, tiers=3, spine_oversubscription=2.0, spare_rate=0.05
    )
    check(
        "3-Tier Clos BOM (4,096 GPUs, 64-port, 5% spares): 1:1 needs 128L + 128S + 64SS = 320 switches (336 w/ spares) & 12,288 cables (12,903 w/ spares) & 24,576 optics (25,805 w/ spares); 2:1 super-spine cuts SS to 32 (288/303 switches), 10,240 cables (10,752 w/ spares), & 20,480 optics (21,504 w/ spares)",
        bom_4096_1to1.leaf_switches == 128
        and bom_4096_1to1.spine_switches == 128
        and bom_4096_1to1.superspine_switches == 64
        and bom_4096_1to1.total_switches_active == 320
        and bom_4096_1to1.total_switches_with_spares == 336
        and bom_4096_1to1.total_cables_active == 12288
        and bom_4096_1to1.total_cables_with_spares == 12903
        and bom_4096_1to1.total_transceivers_active == 24576
        and bom_4096_1to1.total_transceivers_with_spares == 25805
        and bom_4096_2to1.superspine_switches == 32
        and bom_4096_2to1.total_switches_active == 288
        and bom_4096_2to1.total_switches_with_spares == 303
        and bom_4096_2to1.total_cables_active == 10240
        and bom_4096_2to1.total_cables_with_spares == 10752
        and bom_4096_2to1.total_transceivers_active == 20480
        and bom_4096_2to1.total_transceivers_with_spares == 21504,
    )

    # 16. 3-Tier (5-stage) Clos BOM calculator: 8,192 GPUs (1,024 nodes) at 1:1 non-blocking with 5% spares
    bom_8192 = calculate_clos_bom(
        gpus=8192, gpus_per_node=8, switch_radix=64, tiers=3, spine_oversubscription=1.0, spare_rate=0.05
    )
    check(
        "3-Tier 1:1 Clos BOM (8,192 GPUs, 64-port, 5% spares): 256L + 256S + 128SS = 640 switches (672 w/ spares), 24,576 cables (25,805 w/ spares), 49,152 optics (51,610 w/ spares)",
        bom_8192.leaf_switches == 256
        and bom_8192.spine_switches == 256
        and bom_8192.superspine_switches == 128
        and bom_8192.total_switches_active == 640
        and bom_8192.total_switches_with_spares == 672
        and bom_8192.total_cables_active == 24576
        and bom_8192.total_cables_with_spares == 25805
        and bom_8192.total_transceivers_active == 49152
        and bom_8192.total_transceivers_with_spares == 51610,
    )

    # 17. SuperPOD B200 cabling & switch BOM table (superpod-b200-dc p. 19-21)
    check(
        "superpod-b200-dc cabling BOM (1-4 SUs): 31/63/95/127 nodes, 248/504/760/1016 GPUs, 8/16/24/32 leaves, 4/8/16/16 spines, 252/508/764/1020 compute+UFM cables, 256/512/768/1024 ISL cables",
        SUPERPOD_B200_BOM_TABLE[1] == {"nodes": 31, "gpus": 248, "leaves": 8, "spines": 4, "compute_ufm_cables": 252, "isl_cables": 256}
        and SUPERPOD_B200_BOM_TABLE[2] == {"nodes": 63, "gpus": 504, "leaves": 16, "spines": 8, "compute_ufm_cables": 508, "isl_cables": 512}
        and SUPERPOD_B200_BOM_TABLE[3] == {"nodes": 95, "gpus": 760, "leaves": 24, "spines": 16, "compute_ufm_cables": 764, "isl_cables": 768}
        and SUPERPOD_B200_BOM_TABLE[4] == {"nodes": 127, "gpus": 1016, "leaves": 32, "spines": 16, "compute_ufm_cables": 1020, "isl_cables": 1024},
    )

    # 18. SuperPOD B200 DAC/AOC reach, 90% distance rule, and 5-of-6 PSU requirement (superpod-b200-dc p. 15, 20-21)
    check(
        "superpod-b200-dc physical rules: 5 of 6 PSUs required, Passive DAC <=5m (100G) / <=3m (400G), AOC <=30m, cable runs <=90% of max distance (27m for 30m AOC)",
        B200_PSU_TOTAL == 6
        and B200_PSU_REQUIRED == 5
        and B200_PASSIVE_DAC_100G_MAX_M == 5
        and B200_PASSIVE_DAC_400G_MAX_M == 3
        and B200_AOC_MAX_M == 30
        and B200_CABLE_MAX_DISTANCE_FRACTION == 0.90
        and round(B200_AOC_MAX_M * B200_CABLE_MAX_DISTANCE_FRACTION, 1) == 27.0,
    )

    # 19. SuperPOD GB300 NVL72 rack, tray, NVLink5, and power shelf architecture (superpod-gb300-ra p. 5, 8-13, 19)
    check(
        "superpod-gb300-ra rack architecture: 1.2 MW/SU (8 racks x 72 GPUs = 576 GPUs/SU), 18 trays x 4 B300 GPUs + 9 NVLink switch trays (18 chips, 1.8 TB/s/GPU, 900 GB/s C2C), 8 power shelves x 6x5.5kW = 33kW, 4x CX-8 800G + 1x BF-3 2x400G",
        GB300_SU_TDP_MW == 1.2
        and GB300_RACKS_PER_SU == 8
        and GB300_GPUS_PER_RACK == 72
        and GB300_TRAYS_PER_RACK == 18
        and GB300_SUPERCHIPS_PER_TRAY == 2
        and GB300_GPUS_PER_TRAY == 4
        and GB300_NVLINK_SWITCH_TRAYS_PER_RACK == 9
        and GB300_NVLINK_CHIPS_PER_SWITCH_TRAY == 2
        and GB300_NVLINK5_LINKS_PER_GPU == 18
        and GB300_NVLINK5_BW_TBPS == 1.8
        and GB300_NVLINK_C2C_BW_GBPS == 900
        and GB300_POWER_SHELVES_PER_RACK == 8
        and GB300_PSUS_PER_SHELF == 6
        and GB300_PSU_KW == 5.5
        and GB300_SHELF_POWER_KW == 33.0
        and GB300_CX8_NICS_PER_TRAY == 4
        and GB300_CX8_BW_GBPS == 800
        and GB300_BF3_PORTS_PER_TRAY == 2
        and GB300_BF3_PORT_BW_GBPS == 400
        and GB300_INBAND_MGMT_BW_GBPS == 200
        and GB300_OOB_SWITCH_PORTS_1G == 48,
    )

    # 20. SuperPOD GB300 Table 3 (Q3400-RD 144x800G IB) & Table 4 (SN5600D 64x800G Ethernet) scaling (2, 4, 8, 16 SUs)
    check(
        "superpod-gb300-ra Table 3 & Table 4 (2, 4, 8, 16 SUs -> 1152, 2304, 4608, 9216 GPUs): IB leaves 16/32/64/128, IB spines 8/18/36/72; Eth spines 4/8/12/24, compute leaves 8/16/32/64 (24x400G 1:3), storage leaves 2/2/4/8 (72x400G 1:1, 64/128/256/1024x400GbE), 2+2 mgmt/OOB",
        GB300_Q3400_RADIX == 144
        and GB300_SN5600_RADIX == 64
        and GB300_ETH_COMPUTE_LEAF_UPLINKS_400G == 24
        and GB300_ETH_COMPUTE_LEAF_BLOCKING_RATIO == 3
        and GB300_ETH_STORAGE_LEAF_UPLINKS_400G == 72
        and GB300_ETH_MGMT_LEAF_UPLINKS_400G == 24
        and SUPERPOD_GB300_SCALE_TABLE[2]["gpus"] == 1152
        and SUPERPOD_GB300_SCALE_TABLE[2]["ib_spines_total"] == 8
        and SUPERPOD_GB300_SCALE_TABLE[4]["ib_spines_total"] == 18
        and SUPERPOD_GB300_SCALE_TABLE[8]["ib_spines_total"] == 36
        and SUPERPOD_GB300_SCALE_TABLE[16]["ib_leaves_total"] == 128
        and SUPERPOD_GB300_SCALE_TABLE[16]["ib_spines_total"] == 72
        and SUPERPOD_GB300_SCALE_TABLE[16]["eth_spines"] == 24
        and SUPERPOD_GB300_SCALE_TABLE[16]["eth_compute_leaves"] == 64
        and SUPERPOD_GB300_SCALE_TABLE[16]["eth_storage_leaves"] == 8
        and SUPERPOD_GB300_SCALE_TABLE[16]["max_storage_400g_links"] == 1024,
    )

    # 21. SuperPOD GB300 Table 5 storage throughput targets (Standard vs Enhanced, 1 SU vs 4 SU)
    check(
        "superpod-gb300-ra Table 5 storage throughput (GB/s): 1 SU read 90/280, 1 SU write 45/140; 4 SU read 360/1,120, 4 SU write 180/560",
        SUPERPOD_GB300_STORAGE_PERF_GBPS["1_su_read"] == {"standard": 90, "enhanced": 280}
        and SUPERPOD_GB300_STORAGE_PERF_GBPS["1_su_write"] == {"standard": 45, "enhanced": 140}
        and SUPERPOD_GB300_STORAGE_PERF_GBPS["4_su_read"] == {"standard": 360, "enhanced": 1120}
        and SUPERPOD_GB300_STORAGE_PERF_GBPS["4_su_write"] == {"standard": 180, "enhanced": 560},
    )

    # 22. Cable matrix diff validator: clean BOM matches discovered LLDP / ibnetdiscover topology with 0 discrepancies
    expected_cables = [
        CableLinkSpec("dgx-01", "mlx5_0", 0, "leaf-r0-01", "Port1", 400, 4),
        CableLinkSpec("dgx-01", "mlx5_1", 1, "leaf-r1-01", "Port1", 400, 4),
        CableLinkSpec("dgx-02", "mlx5_0", 0, "leaf-r0-01", "Port2", 400, 4),
        CableLinkSpec("dgx-02", "mlx5_1", 1, "leaf-r1-01", "Port2", 400, 4),
    ]
    clean_diff = validate_cable_matrix_diff(expected_cables, expected_cables)
    check(
        "Topograph / LLDP / ibnetdiscover cable matrix diff: matching BOM yields 0 discrepancies",
        len(clean_diff) == 0,
    )

    # 23. Cable matrix diff validator: detects RAIL_SWITCH_MISMATCH, PORT_SWAP, SPEED_OR_WIDTH_DOWNTRAIN, and MISSING_LINK
    faulty_discovered = [
        # dgx-01 mlx5_0 plugged into wrong rail switch leaf-r1-01 instead of leaf-r0-01
        CableLinkSpec("dgx-01", "mlx5_0", 0, "leaf-r1-01", "Port1", 400, 4),
        # dgx-01 mlx5_1 plugged into wrong port Port9 on leaf-r1-01
        CableLinkSpec("dgx-01", "mlx5_1", 1, "leaf-r1-01", "Port9", 400, 4),
        # dgx-02 mlx5_0 downtrained to 200G x2 lanes
        CableLinkSpec("dgx-02", "mlx5_0", 0, "leaf-r0-01", "Port2", 200, 2),
        # dgx-02 mlx5_1 missing (unplugged)
    ]
    diffs = validate_cable_matrix_diff(expected_cables, faulty_discovered)
    cats = {d.src_host + ":" + d.src_port: d.category for d in diffs}
    check(
        "Cable matrix diff validator detects RAIL_SWITCH_MISMATCH, PORT_SWAP, SPEED_OR_WIDTH_DOWNTRAIN, and MISSING_LINK",
        len(diffs) == 4
        and cats["dgx-01:mlx5_0"] == "RAIL_SWITCH_MISMATCH"
        and cats["dgx-01:mlx5_1"] == "PORT_SWAP"
        and cats["dgx-02:mlx5_0"] == "SPEED_OR_WIDTH_DOWNTRAIN"
        and cats["dgx-02:mlx5_1"] == "MISSING_LINK",
    )

    # 24. BCM 11 Topograph service parameters & Slurm topology.conf generation (bcm11-admin §7.5)
    topo_lines = generate_slurm_topology_conf(
        spine_to_leaves={"switch03": ["switch03-switch01", "switch03-switch02"]},
        leaf_to_nodes={
            "switch03-switch01": ["node001", "node002", "node003"],
            "switch03-switch02": ["node004", "node005", "node006"],
        },
    )
    check(
        "BCM 11 Topograph §7.5: port 49021, timeout 20s, 12 attempts, 15s wait/aggregation, PageSize 100, 26 measurables & Slurm topology.conf generation",
        BCM_TOPOGRAPH_PORT == 49021
        and BCM_TOPOGRAPH_FETCH_TIMEOUT_S == 20
        and BCM_TOPOGRAPH_FETCH_ATTEMPTS == 12
        and BCM_TOPOGRAPH_FETCH_WAIT_S == 15
        and BCM_TOPOGRAPH_AGGREGATION_DELAY_S == 15
        and BCM_TOPOGRAPH_PAGE_SIZE == 100
        and BCM_TOPOGRAPH_MEASURABLES == 26
        and topo_lines[0] == "SwitchName=switch03 Switches=switch03-switch01,switch03-switch02"
        and topo_lines[1] == "SwitchName=switch03-switch01 Nodes=node001,node002,node003"
        and topo_lines[2] == "SwitchName=switch03-switch02 Nodes=node004,node005,node006",
    )

    # 25. Partial rack locality impact on oversubscribed cut: 50% intra-rack locality cuts effective oversubscription in half
    cut_local = model_cut_and_collective_impact(
        nodes_per_leaf=16,
        injection_per_node_gbps=800.0,
        uplinks_normal=8,
        uplinks_degraded=7,
        uplink_rate_gbps=400.0,
        collective_payload_bytes=2_000_000_000,
        total_ranks=16,
        cross_cut_traffic_fraction=0.5,
    )
    check(
        "Locality-aware cut model: 50% intra-rack locality reduces 4.00:1 cut to 2.00:1 normal (400 Gbps/node) and 2.29:1 N-1 degraded",
        cut_local.downlink_demand_gbps == 6400.0
        and cut_local.oversub_normal == 2.00
        and cut_local.oversub_degraded == 2.29
        and cut_local.effective_node_bw_normal_gbps == 400.0,
    )

    # 26. AOC vs Transceiver BOM comparison: AOC cables integrate transceivers (0 standalone optics) vs fiber patch cords (2 optics/cable)
    bom_aoc = calculate_clos_bom(
        gpus=1024,
        gpus_per_node=8,
        switch_radix=64,
        tiers=2,
        spare_rate=0.05,
        standalone_transceivers_per_cable=0,
    )
    check(
        "AOC vs MPO/LC fiber BOM: bonded AOC assembly requires 0 standalone transceivers vs 4,096 active (4,301 w/ spares) for patch fiber",
        bom_aoc.total_cables_active == 2048
        and bom_aoc.total_cables_with_spares == 2151
        and bom_aoc.total_transceivers_active == 0
        and bom_aoc.total_transceivers_with_spares == 0,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
