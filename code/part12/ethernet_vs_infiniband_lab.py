#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.12: Ethernet versus InfiniBand: a design decision guide."""

from __future__ import annotations

import sys

from ethernet_vs_infiniband import (
    BCM_DEFAULT_NUM_VFS,
    DGX_H100_COST_PER_GPU_USD,
    DGX_H100_NODE_COST_USD,
    DGX_H100_SYSTEM_POWER_KW,
    ETH_400G_COST_PER_UNIT_USD,
    ETH_PFC_PRIORITIES,
    ETH_SWITCH_PORT_LATENCY_NS,
    GPU_HOUR_AMORTIZED_COST_USD,
    H100_PCIE_BF16_TFLOPS,
    H100_PCIE_TDP_W,
    H100_PCIE_UNIT_PRICE_USD,
    H100_SXM5_BF16_TFLOPS,
    H100_SXM5_BW_TBPS,
    H100_SXM5_FP8_TFLOPS,
    H100_SXM5_HBM3_GB,
    H100_SXM5_PRICE_PER_TFLOP_USD,
    H100_SXM5_TDP_W,
    H100_SXM5_UNIT_PRICE_USD,
    H200_SXM_BW_TBPS,
    H200_SXM_HBM3E_GB,
    H200_SXM_UNIT_PRICE_USD,
    IB_CBFC_CREDIT_BYTES,
    IB_EXACT_UNICAST_LIDS,
    IB_LID_BITS,
    IB_MAX_SCALE_GPUS,
    IB_MAX_SUBNET_NODES,
    IB_NDR_COST_PER_UNIT_USD,
    IB_SPEC_MAX_OPTICS_KM,
    IB_SWITCH_PORT_LATENCY_NS,
    IB_VIRTUAL_LANES,
    IB_WORKLOAD_QUEUES_MAX,
    IB_WORKLOAD_QUEUES_MIN,
    L40S_BF16_TFLOPS,
    L40S_GDDR6_GB,
    L40S_UNIT_PRICE_USD,
    MLXCONFIG_LINK_TYPE_ETH,
    MLXCONFIG_LINK_TYPE_IB,
    NDR_400G_PORT_GBPS_BYTES,
    NVLINK4_PER_GPU_GBPS,
    NVME_RDMA_WRITE_LATENCY_REDUCTION_PCT,
    NVME_TCP_DISCOVERY_PORT,
    PCIE_GEN5_GT_PER_SEC,
    PCIE_GEN5_LOCAL_SSD_LATENCY_NS,
    PCIE_GEN5_X16_PER_DIR_GBPS,
    PCIE_GEN5_X16_UNIDIR_GBPS,
    PCIE_H100_COST_PER_GPU_USD,
    PCIE_H100_NODE_COST_USD,
    QM9700_NDR_PORTS,
    QM9700_OSFP_CAGES,
    RDMA_PRTYPE_IB,
    RDMA_PRTYPE_IWARP,
    RDMA_PRTYPE_ROCEV2,
    ROCEV2_CM_UDP_PORT,
    ROCEV2_MIN_LARGE_SCALE_GPUS,
    ROCEV2_UDP_PORT,
    STORAGE_HOP_LATENCY_MAX_NS,
    STORAGE_HOP_LATENCY_MIN_NS,
    SWITCH_PARSE_DEPTH_BYTES,
    UEC_CBFC_VIRTUAL_CHANNELS,
    UEC_RCCC_ACK_CC_BITS,
    UEC_RCCC_CREDIT_UNIT_BYTES,
    UEC_SPEC_RELEASE_DATE,
    UEC_VENDOR_COUNT_MIN,
    UET_NATIVE_IP_PROTO,
    UET_TARGET_SCALE_GPUS,
    UET_UDP_PORT,
    WAN_LONG_DISTANCE_KM,
    build_fabric_comparison_matrix,
    calculate_64gpu_ib_vs_roce_tco,
    compute_rack_cut_and_pfc_buffer,
    diagnose_v9_ethernet_incident,
    evaluate_connectx_vpi_and_locality,
    select_ai_fabric_for_workload,
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

    print("=== Chapter 12.12 Lab: Ethernet versus InfiniBand Design Decision Guide ===")

    # 1. Architectural comparison matrix (ADC Ch 2, Ch 9 Table 9-2, Ch 12 Table 12-4)
    matrix = build_fabric_comparison_matrix()
    check(
        "ADC Ch 2/9/12 4-way architectural matrix: InfiniBand (<100K GPUs, 300 ns) vs Standard RoCEv2 (>100K, 800 ns) vs Spectrum-X vs UET (~1M GPUs)",
        set(matrix.keys()) == {"InfiniBand", "Standard_RoCEv2", "Spectrum_X", "UET_UEC"}
        and matrix["InfiniBand"].max_scale_gpus == IB_MAX_SCALE_GPUS == 100000
        and matrix["Standard_RoCEv2"].max_scale_gpus == ROCEV2_MIN_LARGE_SCALE_GPUS == 100000
        and matrix["UET_UEC"].max_scale_gpus == UET_TARGET_SCALE_GPUS == 1000000
        and matrix["InfiniBand"].switch_latency_ns == IB_SWITCH_PORT_LATENCY_NS == 300
        and matrix["Standard_RoCEv2"].switch_latency_ns == ETH_SWITCH_PORT_LATENCY_NS == 800,
    )

    # 2. InfiniBand vs RoCEv2 vs UET flow control & credit units (ADC Ch 9 & Ch 12)
    check(
        "ADC Ch 9 & Ch 12 flow control: IB 16 VLs (8..12 active queues, 64B CBFC credits in LLH, 16-bit LID 48,000/49,151 nodes) vs 8 PFC prios vs 32 UEC VCs & 256B RCCC credits (24-bit ACK_CC)",
        IB_LID_BITS == 16
        and IB_MAX_SUBNET_NODES == 48000
        and IB_EXACT_UNICAST_LIDS == 49151
        and IB_VIRTUAL_LANES == 16
        and IB_WORKLOAD_QUEUES_MIN == 8
        and IB_WORKLOAD_QUEUES_MAX == 12
        and IB_CBFC_CREDIT_BYTES == 64
        and ETH_PFC_PRIORITIES == 8
        and UEC_CBFC_VIRTUAL_CHANNELS == 32
        and UEC_RCCC_CREDIT_UNIT_BYTES == 256
        and UEC_RCCC_ACK_CC_BITS == 24,
    )

    # 3. UEC v1.0 protocol ports, parse depth, and delivery modes (ADC Ch 12)
    check(
        "ADC Ch 12 UEC v1.0 (2025-06-11, 70+ vendors): UDP 49150 vs IP proto 253, 128B switch parse depth, ROD/RUD/RUDI/UUD modes, TSS security, and INC over gRPC",
        UEC_SPEC_RELEASE_DATE == "2025-06-11"
        and UEC_VENDOR_COUNT_MIN == 70
        and ROCEV2_UDP_PORT == 4791
        and UET_UDP_PORT == 49150
        and UET_NATIVE_IP_PROTO == 253
        and SWITCH_PARSE_DEPTH_BYTES == 128
        and len(matrix["UET_UEC"].delivery_modes) == 4
        and "gRPC" in matrix["UET_UEC"].in_network_collectives,
    )

    # 4. Storage network latencies, ports, and NVMe-oF provider types (ADC Ch 9)
    check(
        "ADC Ch 9 storage constants: 100 ns PCIe Gen5 SSD (32 GT/s, ~63 Gbps x16), 300 ns IB vs 800 ns ETH switch (700-900 ns 1-3 hop), 66% lower RDMA write latency, TCP 8009 / UDP 4420 / UDP 4791, RDMA_PRTYPE 02/04/05, 40 km WAN vs 10 km IB spec",
        PCIE_GEN5_LOCAL_SSD_LATENCY_NS == 100
        and PCIE_GEN5_GT_PER_SEC == 32
        and PCIE_GEN5_X16_UNIDIR_GBPS == 63
        and STORAGE_HOP_LATENCY_MIN_NS == 700
        and STORAGE_HOP_LATENCY_MAX_NS == 900
        and NVME_RDMA_WRITE_LATENCY_REDUCTION_PCT == 66
        and NVME_TCP_DISCOVERY_PORT == 8009
        and ROCEV2_CM_UDP_PORT == 4420
        and RDMA_PRTYPE_IB == 2
        and RDMA_PRTYPE_ROCEV2 == 4
        and RDMA_PRTYPE_IWARP == 5
        and WAN_LONG_DISTANCE_KM == 40
        and IB_SPEC_MAX_OPTICS_KM == 10,
    )

    # 5. ConnectX VPI personality switching (LINK_TYPE_P1=1 IB vs =2 ETH) & BCM precedence
    vpi_ib = evaluate_connectx_vpi_and_locality(
        pci_bdf="0000:03:00.0",
        link_type_p1=MLXCONFIG_LINK_TYPE_IB,
        category_extra_link_type="ETH",
        node_extra_link_type="ETH",
        interface_extra_link_type="IB",
        pcie_speed_gt_s=32,
        pcie_width_lanes=16,
        port_rate_gbps=400,
        gpu_nic_topo_relation="PIX",
        rail0_rx_bytes_delta=88_700_000_000,
        rail1_rx_bytes_delta=87_900_000_000,
    )
    check(
        "ConnectX VPI LINK_TYPE_P1=1 (IB) + BCM11 §3.6.2 precedence (category < node < interface) + PCIe Gen5 x16 (64.0 >= 50.0 GB/s) + PIX locality -> HEALTHY_ENDPOINT_AND_LOCALITY",
        vpi_ib.effective_personality == "InfiniBand"
        and vpi_ib.resolved_bcm_source == "interface.extra_values"
        and vpi_ib.resolved_bcm_link_type == "IB"
        and vpi_ib.usable_pcie_bw_gbps_bytes == 64.0
        and vpi_ib.required_port_bw_gbps_bytes == 50.0
        and not vpi_ib.pcie_bottlenecked
        and not vpi_ib.numa_crossing_penalty
        and not vpi_ib.multi_rail_imbalanced
        and vpi_ib.verdict == "HEALTHY_ENDPOINT_AND_LOCALITY"
        and BCM_DEFAULT_NUM_VFS == 16,
    )

    # 6. ConnectX VPI LINK_TYPE_P1=2 (ETH) with V9 Ch 8 PCIe Gen4 x8 downgrade, SYS locality, and single-rail collision
    vpi_eth_bad = evaluate_connectx_vpi_and_locality(
        pci_bdf="0000:41:00.0",
        link_type_p1=MLXCONFIG_LINK_TYPE_ETH,
        category_extra_link_type="IB",
        node_extra_link_type="ETH",
        interface_extra_link_type=None,
        pcie_speed_gt_s=16,  # downgraded Gen4
        pcie_width_lanes=8,  # downgraded x8 -> 16.0 GB/s
        port_rate_gbps=200,  # 200 Gbps = 25.0 GB/s required
        gpu_nic_topo_relation="SYS",
        rail0_rx_bytes_delta=981_204_882_176 - 892_481_200_384,  # +88.7 GB in 60s
        rail1_rx_bytes_delta=412_992,  # ~0 GB on ens1f1
    )
    check(
        "V9 Ch 8 ConnectX-7 (LINK_TYPE_P1=2 ETH): LnkSta 16GT/s x8 (16.0 < 25.0 GB/s for 200GbE), SYS NUMA crossing, and ens1f0 (+88.7 GB) vs ens1f1 (412,992 B) collision",
        vpi_eth_bad.effective_personality == "Ethernet"
        and vpi_eth_bad.resolved_bcm_source == "node.extra_values"
        and vpi_eth_bad.usable_pcie_bw_gbps_bytes == 16.0
        and vpi_eth_bad.required_port_bw_gbps_bytes == 25.0
        and vpi_eth_bad.pcie_bottlenecked
        and vpi_eth_bad.numa_crossing_penalty
        and vpi_eth_bad.rail0_delta_gb == 88.7
        and vpi_eth_bad.multi_rail_imbalanced
        and vpi_eth_bad.verdict
        == "PCIE_DOWNGRADED_BELOW_LINE_RATE+SYS_NUMA_CROSSING_PENALTY+SINGLE_RAIL_IDLE_NCCL_DEVICE_COLLISION",
    )

    # 7. Edge-case validation for invalid mlxconfig LINK_TYPE_P1
    try:
        evaluate_connectx_vpi_and_locality(
            "0000:03:00.0", 99, None, None, None, 32, 16, 400, "PIX", 100, 100
        )
        invalid_vpi_rejected = False
    except ValueError:
        invalid_vpi_rejected = True
    check("Edge-case validation: evaluate_connectx_vpi_and_locality rejects LINK_TYPE_P1 not in {1, 2}", invalid_vpi_rejected)

    # 8. Volume 21 Ch 2 GPU & Node Reference Constants (H100 SXM5 vs PCIe vs H200 vs L40S, 128-GPU cluster)
    check(
        "V21 Ch 2 GPU & Node table: H100 SXM5 (80GB, 3.35 TB/s, 989 BF16 / 1,979 FP8 TFLOPS, 700W, $30K, $30/TFLOP, 900 GB/s NVLink, $285K/node = $35,625/GPU, 10.2 kW) vs H100 PCIe (756 TFLOPS, 350W, $20K, $215K/node = $26,875/GPU) vs H200 (141GB, 4.8 TB/s, $40K) vs L40S (48GB, 362 TFLOPS, $8K)",
        H100_SXM5_HBM3_GB == 80
        and H100_SXM5_BW_TBPS == 3.35
        and H100_SXM5_BF16_TFLOPS == 989
        and H100_SXM5_FP8_TFLOPS == 1979
        and H100_SXM5_TDP_W == 700
        and H100_SXM5_UNIT_PRICE_USD == 30000
        and H100_SXM5_PRICE_PER_TFLOP_USD == 30
        and NVLINK4_PER_GPU_GBPS == 900
        and PCIE_GEN5_X16_PER_DIR_GBPS == 64
        and NDR_400G_PORT_GBPS_BYTES == 50
        and DGX_H100_NODE_COST_USD == 285000
        and DGX_H100_COST_PER_GPU_USD == 35625.0
        and DGX_H100_SYSTEM_POWER_KW == 10.2
        and H100_PCIE_BF16_TFLOPS == 756
        and H100_PCIE_TDP_W == 350
        and H100_PCIE_UNIT_PRICE_USD == 20000
        and PCIE_H100_NODE_COST_USD == 215000
        and PCIE_H100_COST_PER_GPU_USD == 26875.0
        and H200_SXM_HBM3E_GB == 141
        and H200_SXM_BW_TBPS == 4.8
        and H200_SXM_UNIT_PRICE_USD == 40000
        and L40S_GDDR6_GB == 48
        and L40S_BF16_TFLOPS == 362
        and L40S_UNIT_PRICE_USD == 8000
        and QM9700_NDR_PORTS == 64
        and QM9700_OSFP_CAGES == 32,
    )

    # 9. Volume 21 Ch 2 Part 6: 64-GPU H100 IB NDR vs 400GbE RoCEv2 TCO & Break-Even Calculator
    tco64 = calculate_64gpu_ib_vs_roce_tco()
    check(
        "V21 Ch 2 Part 6 64-GPU CapEx delta: IB NDR ($15K * 64 = $960K) vs 400GbE ($8K * 64 = $512K) -> $7K * 64 = $448,000 upfront savings",
        tco64.ib_capex_usd == 960000
        and tco64.eth_capex_usd == 512000
        and tco64.upfront_ib_premium_usd == 448000
        and IB_NDR_COST_PER_UNIT_USD == 15000
        and ETH_400G_COST_PER_UNIT_USD == 8000,
    )

    check(
        "V21 Ch 2 Part 6 AllReduce step math: 100 ms base + 2 ms IB (102 ms, 2.0%) vs 10 ms ETH (110 ms, 10.0%) -> 8.0% throughput loss (7.84% exact step slowdown)",
        tco64.ib_step_ms == 102.0
        and tco64.eth_step_ms == 110.0
        and tco64.ib_comm_overhead_pct == 2.0
        and tco64.eth_comm_overhead_pct == 10.0
        and tco64.approx_throughput_loss_pct == 8.0
        and tco64.exact_step_slowdown_pct == 7.84,
    )

    check(
        "V21 Ch 2 Part 6 Llama-70B 7-day (168 h) run penalty: +13.4 h (181.4 h / 7.56 days) * 64 GPUs * $2.14/GPU-hr = $1,835/run -> $44,040/yr (24 runs) -> $132,120 over 3 yrs (< $448,000)",
        GPU_HOUR_AMORTIZED_COST_USD == 2.14
        and tco64.eth_extra_hours_per_run == 13.4
        and tco64.eth_total_run_hours == 181.4
        and tco64.eth_total_run_days == 7.56
        and tco64.extra_cost_per_run_usd == 1835
        and tco64.annual_extra_compute_cost_usd == 44040.0
        and tco64.three_year_extra_compute_cost_usd == 132120.0
        and tco64.runs_needed_to_break_even == 244.14
        and tco64.years_to_break_even_at_24_runs == 10.17
        and not tco64.pure_compute_math_justifies_ib_at_64_gpus
        and tco64.architectural_recommendation == "DEFENSIBLE_ETHERNET_AT_FIXED_64_GPUS",
    )

    check(
        "V21 Ch 2 Part 6 multi-model 2x gradient growth: 30 ms ETH AllReduce -> 130 ms vs 102 ms IB (27% overhead) -> ~$12,425/yr (~$12K/yr) for 2 extra runs",
        tco64.large_model_eth_step_ms == 130.0
        and tco64.large_model_overhead_pct == 27.0
        and tco64.large_model_extra_annual_usd == 12425.0,
    )

    # 10. Volume 09 Ch 10 Rack Bottleneck-Cut & Ch 4 PFC Buffer Hysteresis Math
    cut_buf = compute_rack_cut_and_pfc_buffer()
    check(
        "V9 Ch 10 16-node rack cut: 16 * 800 Gb/s = 12,800 Gb/s downlink vs 8 * 400 Gb/s = 3,200 Gb/s normal uplink (4.00:1) and 7 * 400 Gb/s = 2,800 Gb/s N-1 uplink (4.57:1)",
        cut_buf.downlink_demand_gbps == 12800
        and cut_buf.normal_uplink_capacity_gbps == 3200
        and cut_buf.normal_oversubscription_ratio == 4.0
        and cut_buf.degraded_uplink_capacity_gbps == 2800
        and cut_buf.degraded_oversubscription_ratio == 4.57,
    )

    check(
        "V9 Ch 4 mlnx_qos prio 3 buffer (65,536 B): Xoff 49,152 B (75.0%), Xon 32,768 B (50.0%), in-flight headroom 16,384 B (25.0%), hysteresis gap 16,384 B (25.0%)",
        cut_buf.prio3_buffer_bytes == 65536
        and cut_buf.xoff_threshold_bytes == 49152
        and cut_buf.xon_threshold_bytes == 32768
        and cut_buf.xoff_pct == 75.0
        and cut_buf.xon_pct == 50.0
        and cut_buf.headroom_bytes == 16384
        and cut_buf.headroom_pct == 25.0
        and cut_buf.hysteresis_bytes == 16384
        and cut_buf.hysteresis_pct == 25.0,
    )

    # 11. Workload-driven fabric selection rules
    sel_inf = select_ai_fabric_for_workload(
        workload_type="inference",
        gpu_scale=408,
        planned_growth_gpus=408,
        multi_tenant_untrusted_hosts=True,
        existing_ethernet_ops_maturity=True,
        wan_replication_distance_km=50,
    )
    check(
        "Workload selector (Inference + 50 km WAN + multi-tenant): selects Ethernet EVPN-VXLAN + NVMe-o-TCP (>=40 km) + BlueField-3 ECPF DPU mode",
        "EVPN-VXLAN" in sel_inf.recommended_primary_fabric
        and "NVMe-o-TCP" in sel_inf.storage_fabric_transport
        and "ECPF" in sel_inf.dpu_host_edge_mode,
    )

    sel_train64 = select_ai_fabric_for_workload(
        workload_type="synchronous_training",
        gpu_scale=64,
        planned_growth_gpus=64,
        multi_tenant_untrusted_hosts=False,
        existing_ethernet_ops_maturity=True,
        wan_replication_distance_km=0,
    )
    check(
        "Workload selector (Fixed 64-GPU training): selects 400GbE RoCEv2 (or single-pod leaf-only IB NDR) + NVMe-o-RDMA/GDS + SuperNIC/NIC mode",
        "400GbE RoCEv2" in sel_train64.recommended_primary_fabric
        and "NVMe-o-RDMA" in sel_train64.storage_fabric_transport
        and "NIC mode" in sel_train64.dpu_host_edge_mode,
    )

    sel_train512 = select_ai_fabric_for_workload(
        workload_type="synchronous_training",
        gpu_scale=64,
        planned_growth_gpus=512,
        multi_tenant_untrusted_hosts=False,
        existing_ethernet_ops_maturity=True,
        wan_replication_distance_km=0,
    )
    check(
        "Workload selector (64 GPUs growing to 512 GPUs): selects InfiniBand NDR/XDR Fat-Tree with AR, SHARP, and SHIELD",
        "InfiniBand NDR" in sel_train512.recommended_primary_fabric
        and "SHARP" in sel_train512.recommended_primary_fabric,
    )

    sel_multitenant_cloud = select_ai_fabric_for_workload(
        workload_type="synchronous_training",
        gpu_scale=2048,
        planned_growth_gpus=100000,
        multi_tenant_untrusted_hosts=True,
        existing_ethernet_ops_maturity=True,
        wan_replication_distance_km=0,
    )
    check(
        "Workload selector (Multi-tenant 100K-GPU AI cloud): selects Spectrum-X / UEC with BlueField-3 ECPF host-edge isolation",
        "Spectrum-X" in sel_multitenant_cloud.recommended_primary_fabric
        and "ECPF" in sel_multitenant_cloud.dpu_host_edge_mode,
    )

    # 12. Volume 09 7-Stage Diagnostic Ladder Scenarios
    g1_phy, _ = diagnose_v9_ethernet_incident(fec_uncorrected_delta=3, rx_crc_errors_delta=3)
    check(
        "V9 Ch 11 swp17 physical fault: fec_uncorrected_blocks=3 == rx_crc_errors=3 -> GATE1_PHYSICAL_LINK_OR_CABLE_FAULT",
        g1_phy == "GATE1_PHYSICAL_LINK_OR_CABLE_FAULT",
    )

    g1_dpu, _ = diagnose_v9_ethernet_incident(dpu_uplink_up=True, dpu_arm_policy_loaded=False)
    check(
        "V9 Ch 9 BlueField DPU outage: swp14 UP + openvswitch-policy-load.service failed -> GATE1_DPU_ARM_POLICY_LOAD_FAILURE",
        g1_dpu == "GATE1_DPU_ARM_POLICY_LOAD_FAILURE",
    )

    g2_verbs, _ = diagnose_v9_ethernet_incident(rdma_link_count=0)
    check(
        "V9 Ch 2 Scenario 1: mlx5_core loaded without mlx5_ib (rdma link show empty) -> GATE2_MISSING_RDMA_VERBS_DEVICE_SOCKET_FALLBACK",
        g2_verbs == "GATE2_MISSING_RDMA_VERBS_DEVICE_SOCKET_FALLBACK",
    )

    g3_rtr, _ = diagnose_v9_ethernet_incident(qp_rtr_success=False)
    check(
        "V9 Ch 3 & Ch 11: ping 0% loss but ib_write_bw 'Failed to modify QP to RTR' -> GATE3_ROCE_GID_OR_PATH_MTU_RTR_FAILURE",
        g3_rtr == "GATE3_ROCE_GID_OR_PATH_MTU_RTR_FAILURE",
    )

    g4_trust, _ = diagnose_v9_ethernet_incident(
        switch_trust_mode="pcp", roce_dscp_value=46, rx_prio0_discard_delta=18420
    )
    check(
        "V9 Ch 6 swp19 trust drift: tos 0xb8 (DSCP 46) into PCP-trust switch -> rx_prio0_discard=18,420 -> GATE4_QOS_TRUST_MODE_DRIFT_PRIO0_DROPS",
        g4_trust == "GATE4_QOS_TRUST_MODE_DRIFT_PRIO0_DROPS" and (0xB8 >> 2) == 46,
    )

    g4_pfc6, _ = diagnose_v9_ethernet_incident(pfc_enabled_priorities=(3, 6))
    check(
        "V9 Ch 1 Scenario 2 mlnx_qos swp12: PFC enabled on prio 3 AND prio 6 (sharing tc2) -> GATE4_BROAD_PFC_PAUSE_DOMAIN_CONTAMINATION",
        g4_pfc6 == "GATE4_BROAD_PFC_PAUSE_DOMAIN_CONTAMINATION",
    )

    g4_strict, _ = diagnose_v9_ethernet_incident(prio3_tsa_mode="strict", rx_pfc_prio3_delta=412)
    check(
        "V9 Ch 6 Scenario 2: tc1 prio 3 scheduled 'strict' over dwrr weight 5 management tc0 -> GATE4_STRICT_PRIORITY_MANAGEMENT_STARVATION",
        g4_strict == "GATE4_STRICT_PRIORITY_MANAGEMENT_STARVATION",
    )

    g5_healthy, _ = diagnose_v9_ethernet_incident(
        rx_ecn_marked_prio3_delta=312, rx_pfc_prio3_delta=0, np_cnp_handled_delta=298
    )
    check(
        "V9 Ch 5 healthy ECN/DCQCN loop: 312 switch ECN marks -> 298 CNPs handled -> 0 PFC pauses -> GATE5_HEALTHY_PROACTIVE_ECN_DCQCN_LOOP",
        g5_healthy == "GATE5_HEALTHY_PROACTIVE_ECN_DCQCN_LOOP",
    )

    g5_broken_cnp, _ = diagnose_v9_ethernet_incident(
        rx_ecn_marked_prio3_delta=15000, rx_pfc_prio3_delta=0, np_cnp_handled_delta=0
    )
    check(
        "V9 Ch 5 Fig 9.5.1 broken feedback: switch ECN marks climb (15,000) while np_cnp_handled=0 -> GATE5_BROKEN_CNP_RETURN_OR_NIC_DCQCN_DISABLED",
        g5_broken_cnp == "GATE5_BROKEN_CNP_RETURN_OR_NIC_DCQCN_DISABLED",
    )

    g5_congested, _ = diagnose_v9_ethernet_incident(
        rx_ecn_marked_prio3_delta=412880,
        rx_pfc_prio3_delta=93100,
        np_cnp_handled_delta=409500,
        rp_current_rate_gbps=98.0,
    )
    check(
        "V9 Ch 5 Scenario 1: rx_ecn_marked=412,880 + rx_pfc_prio3=93,100 + np_cnp_handled=409,500 at 98 Gbps -> GATE5_CONGESTED_CUT_OR_WEAK_DCQCN_THROTTLE",
        g5_congested == "GATE5_CONGESTED_CUT_OR_WEAK_DCQCN_THROTTLE",
    )

    g6_wjh, _ = diagnose_v9_ethernet_incident(wjh_tail_drop_count=52100)
    check(
        "V9 Ch 7 & Ch 10 Spectrum WJH: Tail drop (queue full) 52,100 / 18,402 / 38,210 -> GATE6_OVERSUBSCRIBED_LEAF_UPLINK_TAIL_DROP",
        g6_wjh == "GATE6_OVERSUBSCRIBED_LEAF_UPLINK_TAIL_DROP",
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
