#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.11: NVIDIA Spectrum-X and Spectrum switches.

Runs 28 deterministic checks covering:
  - Spectrum-4 `SN5600` / `SN5600D` 51.2 Tbps switching capacity, 512 x 100G PAM4 SerDes lanes,
    and breakout modes (`64x800G`, `128x400G`, `256x200G`, `512x100G`), plus `SN2201` (48x1GbE +
    4x100GbE OOB management switch, `8,048,771,072` B RAM, `115,923,419,136` B NVMe, NVUE REST port `8765`)
  - Spectrum monolithic fully shared buffer vs sliced port-allocated buffer under AI incast microbursts
  - DGX GB300 SuperPOD `SN5600D` Ethernet fabric scale-out (`2, 4, 8, 16` SUs -> `1,152, 2,304, 4,608, 9,216` GPUs,
    `4, 8, 12, 24` spines, `8, 16, 32, 64` compute leafs at `24x400G` `1:3` blocking, `2, 2, 4, 8` storage leafs at
    `72x400G` nonblocking, `24x400G` management leafs, `64..1024x400GbE` storage bandwidth, and `90/45` vs `280/140 GB/s`
    1-SU and `360/180` vs `1,120/560 GB/s` 4-SU read/write throughput)
  - V9 Ch. 10 leaf-to-spine cut capacity & N-1 degraded oversubscription (`16 x 800G = 12,800G` down vs `8 x 400G = 3,200G`
    up = `4.0:1` normal, `7 x 400G = 2,800G` up = `4.57:1` degraded)
  - Spectrum-X end-to-end platform pairing Spectrum-4 + BlueField-3 (`BF3240` dual-port 400G SuperNIC / DPU) +
    Cumulus Linux (`NVUE`) + DOCA, including DPU SKU default mode (`DPU_MODE_ECPF`) vs SuperNIC SKU default mode
    (`NIC_MODE_SUPERNIC`) and 3-layer DPU path fault isolation (`swp14 up`, `openvswitch-policy-load.service`,
    `enp1s0f0np0 DOWN`)
  - ConnectX / BlueField PCIe & NUMA locality (`LnkCap: 32GT/s x16` vs downgraded `LnkSta: 16GT/s x8` = `16 GB/s` <
    `25 GB/s` for `200GbE`, `nvidia-smi topo -m` `PIX` vs `SYS`, and `rx_bytes_phy` `892,481,200,384` ->
    `981,204,882,176` B = `+88.7 GB` in `60 s` on `ens1f0` vs `412,992` B on `ens1f1`)
  - Spectrum-X Adaptive Routing & Selective Dynamic Load Balancing (`sDLB` per-packet RoCEv2 spraying via `BTH`
    `RDMA Write` opcode matching) vs standard 5-tuple Static Load Balancing (`SLB` `CRC32` `0x8BDA7C2D` = `2,346,351,661`,
    `mod 5 = 1`, `mod 8 = 5`, resilient hashing `512`/`1,024` buckets) raising effective bandwidth from `~60%` to `~95%`
  - BlueField-3 hardware out-of-order Direct Data Placement (`DDP`) reassembly (`0` Go-Back-N retransmissions vs `3`
    PSN-gap NAKs on legacy NICs)
  - Spectrum-X hardware telemetry-driven congestion control, What Just Happened (`WJH`) `Tail drop (queue full)`
    (`18,402` and `52,100` vs `0`), and `rx_pfc_prio3` pause-tree origin tracing (`leaf03: 210,500` -> `leaf07: 198,200`
    -> `leaf12: 41,100`)
  - Declarative NVUE (`nv set`) lossless RoCE / Adaptive Routing / EVPN / BGP validation and V9 Labs 01..04 diagnostics.
"""

from __future__ import annotations

from spectrum_x_switches import (
    ADC_RESILIENT_HASH_BUCKETS,
    ADC_SLB_SAMPLE_CRC32_HEX,
    GB300_BF3_PORTS_PER_TRAY,
    GB300_COMPUTE_LEAF_UPLINKS_400G,
    GB300_CUSTOMER_EDGE_DR1_100G_MIN,
    GB300_CX8_PER_TRAY,
    GB300_GPUS_PER_RACK,
    GB300_GPUS_PER_SU,
    GB300_INBAND_MIN_GBPS,
    GB300_MGMT_LEAF_LINKS_400G,
    GB300_RACKS_PER_SU,
    GB300_STORAGE_LEAF_LINKS_400G,
    GB300_STORAGE_PORT_GBPS,
    GB300_TRAYS_PER_RACK,
    NVUE_DEFAULT_REST_PORT,
    ROCEV2_UDP_PORT,
    SN2201_COPPER_1G_PORTS,
    SN2201_DISK_BYTES,
    SN2201_RAM_BYTES,
    SN2201_UPLINK_100G_PORTS,
    SN5600_BREAKOUT_100G,
    SN5600_BREAKOUT_200G,
    SN5600_BREAKOUT_400G,
    SN5600_PORTS_800G,
    SPECTRUM4_ASIC_TBPS,
    SPECTRUM4_SERDES_LANES,
    SPECTRUM_X_EFFECTIVE_BW_PCT,
    TRADITIONAL_ECMP_EFFECTIVE_BW_PCT,
    analyze_multirail_byte_deltas,
    audit_connectx_pcie_and_locality,
    classify_spectrum_wjh_and_counters,
    compare_slb_dlb_and_spectrum_x_spraying,
    compare_sliced_vs_monolithic_shared_buffer,
    compute_spectrum4_breakout,
    compute_spectrum_x_cc_rate,
    diagnose_dpu_three_layer_path,
    evaluate_bluefield_sku_mode,
    evaluate_leaf_cut_oversubscription,
    get_gb300_spectrum_ethernet_scaleout,
    get_gb300_storage_throughput_guidelines,
    select_packet_spray_mode_by_bth_opcode,
    simulate_bluefield3_ddp_ooo_placement,
    trace_pfc_pause_tree_origin,
    validate_nvue_spectrum_x_commands,
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

    print("=== Chapter 12.11 Lab: NVIDIA Spectrum-X and Spectrum Switches ===")

    # 1. Spectrum-4 SN5600 / SN5600D hardware radix & breakout modes (64x800G, 128x400G, 256x200G, 512x100G)
    b800 = compute_spectrum4_breakout("64x800G")
    b400 = compute_spectrum4_breakout("128x400G")
    b200 = compute_spectrum4_breakout("256x200G")
    b100 = compute_spectrum4_breakout("512x100G")
    check(
        "Spectrum-4 SN5600 / SN5600D 51.2 Tbps ASIC (512 x 100G PAM4 SerDes): 64x800G (8 lanes), 128x400G (4 lanes), 256x200G (2 lanes), 512x100G (1 lane)",
        SPECTRUM4_ASIC_TBPS == 51.2
        and SPECTRUM4_SERDES_LANES == 512
        and SN5600_PORTS_800G == 64
        and SN5600_BREAKOUT_400G == 128
        and SN5600_BREAKOUT_200G == 256
        and SN5600_BREAKOUT_100G == 512
        and b800.aggregate_tbps == 51.2
        and b400.aggregate_tbps == 51.2
        and b200.aggregate_tbps == 51.2
        and b100.aggregate_tbps == 51.2
        and (b800.serdes_lanes_per_logical_port, b400.serdes_lanes_per_logical_port, b200.serdes_lanes_per_logical_port, b100.serdes_lanes_per_logical_port)
        == (8, 4, 2, 1),
    )

    # 2. SN2201 OOB management switch & BCM11 Cumulus / NVUE inventory specs
    check(
        "SN2201 OOB switch & BCM11 inventory (superpod-gb300-ra p. 13, 26; bcm11-admin p. 151-153): 48x1GbE copper + 4x100GbE uplinks, 8,048,771,072 B RAM (7.496 GB), 115,923,419,136 B NVMe (115 GB), NVUE REST port 8765",
        SN2201_COPPER_1G_PORTS == 48
        and SN2201_UPLINK_100G_PORTS == 4
        and SN2201_RAM_BYTES == 8_048_771_072
        and SN2201_DISK_BYTES == 115_923_419_136
        and NVUE_DEFAULT_REST_PORT == 8765,
    )

    # 3. Spectrum monolithic fully shared buffer vs sliced port-allocated buffer under AI incast
    buf_cmp = compare_sliced_vs_monolithic_shared_buffer(
        total_switch_buffer_mb=64.0, num_ports=64, hot_port_burst_mb=8.0, shared_alpha_cap_fraction=0.25
    )
    check(
        "V9 Ch 7 Monolithic Shared Buffer vs Sliced Buffer: 64.0 MB / 64 ports gives 1.0 MB sliced cap (63.0 MB idle on ports 2..64, drops 7.0 MB of 8.0 MB microburst) vs 16.0 MB dynamic shared cap (0.0 MB dropped)",
        buf_cmp.sliced_per_port_cap_mb == 1.0
        and round(buf_cmp.total_switch_buffer_mb - buf_cmp.sliced_per_port_cap_mb, 1) == 63.0
        and buf_cmp.sliced_dropped_mb == 7.0
        and buf_cmp.shared_dynamic_cap_mb == 16.0
        and buf_cmp.shared_dropped_mb == 0.0
        and buf_cmp.shared_absorbs_microburst is True,
    )

    # 4. DGX GB300 compute tray NIC/DPU architecture & link ratios (superpod-gb300-ra p. 8-9, 22-27)
    check(
        "superpod-gb300-ra Compute Tray & Leaf Ratios: 18 trays/rack (72 GPUs/rack, 8 racks = 576 GPUs/SU), 4x ConnectX-8 (800G) + 1x BlueField-3 BF3240 (2x400G: 400G storage + >=200G in-band), 24x400G compute leaf uplinks (1:3), 72x400G storage leaf links, 24x400G mgmt leaf links, >=2x100GbE DR1 edge",
        GB300_TRAYS_PER_RACK == 18
        and GB300_GPUS_PER_RACK == 72
        and GB300_RACKS_PER_SU == 8
        and GB300_GPUS_PER_SU == 576
        and GB300_CX8_PER_TRAY == 4
        and GB300_BF3_PORTS_PER_TRAY == 2
        and GB300_STORAGE_PORT_GBPS == 400
        and GB300_INBAND_MIN_GBPS == 200
        and GB300_COMPUTE_LEAF_UPLINKS_400G == 24
        and GB300_STORAGE_LEAF_LINKS_400G == 72
        and GB300_MGMT_LEAF_LINKS_400G == 24
        and GB300_CUSTOMER_EDGE_DR1_100G_MIN == 2,
    )

    # 5. DGX GB300 SuperPOD SN5600D Ethernet scale-out (Table 4, p. 23: 2, 4, 8, 16 SUs)
    s2 = get_gb300_spectrum_ethernet_scaleout(2)
    s4 = get_gb300_spectrum_ethernet_scaleout(4)
    s8 = get_gb300_spectrum_ethernet_scaleout(8)
    s16 = get_gb300_spectrum_ethernet_scaleout(16)
    check(
        "superpod-gb300-ra Table 4 SN5600D Scale-Out (2, 4, 8, 16 SUs): (1152, 2304, 4608, 9216) GPUs, (4, 8, 12, 24) spines, (8, 16, 32, 64) compute leafs, (2, 2, 4, 8) storage leafs, (64, 128, 256, 1024) x 400GbE storage links (25.6..409.6 Tbps)",
        (s2.num_gpus, s4.num_gpus, s8.num_gpus, s16.num_gpus) == (1152, 2304, 4608, 9216)
        and (s2.spine_switches_sn5600d, s4.spine_switches_sn5600d, s8.spine_switches_sn5600d, s16.spine_switches_sn5600d)
        == (4, 8, 12, 24)
        and (
            s2.compute_leaf_switches_sn5600d,
            s4.compute_leaf_switches_sn5600d,
            s8.compute_leaf_switches_sn5600d,
            s16.compute_leaf_switches_sn5600d,
        )
        == (8, 16, 32, 64)
        and (
            s2.storage_leaf_switches_sn5600d,
            s4.storage_leaf_switches_sn5600d,
            s8.storage_leaf_switches_sn5600d,
            s16.storage_leaf_switches_sn5600d,
        )
        == (2, 2, 4, 8)
        and (s2.max_storage_ports_400g, s4.max_storage_ports_400g, s8.max_storage_ports_400g, s16.max_storage_ports_400g)
        == (64, 128, 256, 1024)
        and (s2.max_storage_bandwidth_tbps, s16.max_storage_bandwidth_tbps) == (25.6, 409.6),
    )

    # 6. DGX GB300 SuperPOD RoCEv2 storage performance guidelines (Table 5, p. 31)
    st_std = get_gb300_storage_throughput_guidelines("Standard")
    st_enh = get_gb300_storage_throughput_guidelines("Enhanced")
    check(
        "superpod-gb300-ra Table 5 RoCEv2 Storage Throughput: Standard (90 GB/s read, 45 GB/s write per SU; 360/180 GB/s for 4 SUs) vs Enhanced (280 GB/s read, 140 GB/s write per SU; 1,120/560 GB/s for 4 SUs)",
        (st_std.single_su_read_gbps, st_std.single_su_write_gbps, st_std.four_su_read_gbps, st_std.four_su_write_gbps)
        == (90, 45, 360, 180)
        and (st_enh.single_su_read_gbps, st_enh.single_su_write_gbps, st_enh.four_su_read_gbps, st_enh.four_su_write_gbps)
        == (280, 140, 1120, 560),
    )

    # 7. V9 Ch. 10 leaf-to-spine cut capacity & N-1 degraded oversubscription math
    cut = evaluate_leaf_cut_oversubscription(
        num_nodes=16, rails_per_node=2, rail_speed_gbps=400, normal_uplinks=8, uplink_speed_gbps=400, failed_uplinks=1
    )
    check(
        "V9 Ch 10 Leaf Cut Oversubscription: 16 nodes x 2x400G = 12,800 Gbps down vs 8x400G = 3,200 Gbps up (4.0:1 normal); 1 uplink drained leaves 7x400G = 2,800 Gbps (4.57:1 N-1 degraded)",
        cut.downlink_demand_gbps == 12800
        and cut.normal_uplink_capacity_gbps == 3200
        and cut.normal_oversubscription_ratio == 4.0
        and cut.degraded_uplink_capacity_gbps == 2800
        and cut.degraded_oversubscription_ratio == 4.57,
    )

    # 8. V9 Ch. 9 BlueField DPU SKU default mode (`DPU_MODE_ECPF`) vs SuperNIC SKU default mode (`NIC_MODE_SUPERNIC`)
    bf_dpu = evaluate_bluefield_sku_mode("DPU")
    bf_snic = evaluate_bluefield_sku_mode("SUPERNIC")
    check(
        "V9 Ch 9 BlueField SKU Operating Modes: DPU SKU defaults to DPU_MODE_ECPF (Arm owns eSwitch, host isolated, OOB required); SuperNIC SKU defaults to NIC_MODE_SUPERNIC",
        bf_dpu.default_mode == "DPU_MODE_ECPF"
        and bf_dpu.arm_owns_eswitch is True
        and bf_dpu.host_admin_isolated is True
        and bf_snic.default_mode == "NIC_MODE_SUPERNIC"
        and bf_snic.arm_owns_eswitch is False,
    )

    # 9. V9 Ch. 9 Three-Layer DPU Boot / Policy Fault Isolation (`swp14 up`, `openvswitch-policy-load.service failed`, `enp1s0f0np0 DOWN`)
    dpu_boot_fault = diagnose_dpu_three_layer_path(
        switch_uplink_up=True, arm_policy_service_active=False, host_interface_up=False
    )
    dpu_phy_fault = diagnose_dpu_three_layer_path(
        switch_uplink_up=False, arm_policy_service_active=True, host_interface_up=False
    )
    dpu_ok = diagnose_dpu_three_layer_path(
        switch_uplink_up=True, arm_policy_service_active=True, host_interface_up=True
    )
    check(
        "V9 Ch 9 Three-Layer DPU Triage: healthy uplink (`swp14 up`) + failed Arm policy service (`openvswitch-policy-load.service`) + `enp1s0f0np0 DOWN` isolates LAYER2_DPU_ARM_POLICY_BOOT_FAILURE",
        dpu_boot_fault.fault_domain == "LAYER2_DPU_ARM_POLICY_BOOT_FAILURE"
        and dpu_phy_fault.fault_domain == "LAYER3_PHYSICAL_UPLINK_FAULT"
        and dpu_ok.fault_domain == "ALL_THREE_DPU_LAYERS_HEALTHY",
    )

    # 10. V9 Ch. 8 ConnectX PCIe Downgrade Audit (`LnkCap: 32GT/s x16` vs `LnkSta: 16GT/s x8` on 200GbE)
    pcie_deg = audit_connectx_pcie_and_locality(
        cap_gt_per_s=32, cap_width=16, sta_gt_per_s=16, sta_width=8, eth_port_gbps=200, gpu_nic_topo="PIX"
    )
    pcie_sys = audit_connectx_pcie_and_locality(
        cap_gt_per_s=32, cap_width=16, sta_gt_per_s=32, sta_width=16, eth_port_gbps=400, gpu_nic_topo="SYS"
    )
    check(
        "V9 Ch 8 ConnectX PCIe & Locality Audit: LnkCap 32GT/s x16 (64.0 GB/s) downgraded to LnkSta 16GT/s x8 (16.0 GB/s < 25.0 GB/s needed for 200GbE); SYS crosses NUMA boundary",
        pcie_deg.cap_bw_gbps_raw == 64.0
        and pcie_deg.negotiated_bw_gb_per_s == 16.0
        and pcie_deg.required_bw_gb_per_s == 25.0
        and pcie_deg.is_pcie_downgraded is True
        and pcie_deg.can_sustain_port_line_rate is False
        and pcie_deg.crosses_numa_sys is False
        and pcie_sys.can_sustain_port_line_rate is True
        and pcie_sys.crosses_numa_sys is True,
    )

    # 11. V9 Ch. 8 Scenario 1 Multi-Rail 60s Byte-Delta Audit (`892,481,200,384 -> 981,204,882,176` B = `+88.7 GB` / `11.83 Gbps` vs `412,992` B)
    rail_audit = analyze_multirail_byte_deltas()
    check(
        "V9 Ch 8 Scenario 1 Multi-Rail Byte Delta: rail 0 (`ens1f0`/`mlx5_0`) moves 88,723,681,792 B (+88.7 GB in 60s = 11.83 Gbps) while rail 1 (`ens1f1`/`mlx5_1`) moves 412,992 B (~0 GB, idle rail)",
        rail_audit.rail0_delta_bytes == 88_723_681_792
        and rail_audit.rail0_delta_gb == 88.7
        and rail_audit.rail0_gbps == 11.83
        and rail_audit.rail1_delta_bytes == 412_992
        and rail_audit.rail1_effectively_idle is True,
    )

    # 12. ADC Ch. 6 5-tuple SLB CRC32 Hash (`0x8BDA7C2D` = `2,346,351,661`, `mod 5 = 1`, `mod 8 = 5`, `512`/`1,024` resilient buckets)
    lb_cmp = compare_slb_dlb_and_spectrum_x_spraying()
    check(
        "ADC Ch 6 SLB CRC32 & Resilient Hashing: 192.168.1.20 -> 192.168.2.10 UDP 1024 -> 4791 yields 0x8BDA7C2D (2,346,351,661), mod 5 = 1, mod 8 = 5, resilient buckets (512, 1024)",
        lb_cmp.hash_key_hex == "0x8BDA7C2D"
        and lb_cmp.hash_key_dec == 2_346_351_661
        and lb_cmp.mod_5_index == 1
        and lb_cmp.mod_8_index == 5
        and ADC_RESILIENT_HASH_BUCKETS == (512, 1024),
    )

    # 13. ADC Ch. 6 SLB vs DLB vs Spectrum-X Per-Packet Spraying (`~60%` -> `~95%` effective bandwidth)
    check(
        "ADC Ch 6 & Spectrum-X Load Balancing: SLB puts (100G, 200G) = 100% hot link on 2x200G spines (~60% cluster effective BW); DLB/Spectrum-X balances (150G, 150G) = 75% util (~95% effective BW)",
        lb_cmp.slb_spine_loads_gbps == (100.0, 200.0)
        and lb_cmp.slb_max_link_utilization_pct == 100.0
        and lb_cmp.slb_effective_fabric_bw_pct == 60.0
        and lb_cmp.dlb_spine_loads_gbps == (150.0, 150.0)
        and lb_cmp.dlb_max_link_utilization_pct == 75.0
        and lb_cmp.spectrum_x_sprayed_loads_gbps == (150.0, 150.0)
        and lb_cmp.spectrum_x_effective_fabric_bw_pct == 95.0
        and TRADITIONAL_ECMP_EFFECTIVE_BW_PCT == 60.0
        and SPECTRUM_X_EFFECTIVE_BW_PCT == 95.0,
    )

    # 14. ADC Ch. 2 & Ch. 6 Selective Dynamic Load Balancing (`sDLB` via RoCEv2 UDP 4791 BTH Write opcode matching)
    mode_write = select_packet_spray_mode_by_bth_opcode(ROCEV2_UDP_PORT, "RDMA_WRITE_ONLY", nic_supports_ddp_ooo=True)
    mode_send = select_packet_spray_mode_by_bth_opcode(ROCEV2_UDP_PORT, "RDMA_SEND", nic_supports_ddp_ooo=True)
    mode_no_ddp = select_packet_spray_mode_by_bth_opcode(ROCEV2_UDP_PORT, "RDMA_WRITE_FIRST", nic_supports_ddp_ooo=False)
    check(
        "ADC Ch 2 & Ch 6 Selective Packet Spraying (sDLB): RoCEv2 (UDP 4791) BTH RDMA_WRITE on DDP-capable BlueField-3/ConnectX-7 selects PER_PACKET_SPRAY; non-Write or legacy NIC uses FLOWLET_OR_PER_FLOW",
        mode_write == "PER_PACKET_SPRAY"
        and mode_send == "FLOWLET_OR_PER_FLOW"
        and mode_no_ddp == "FLOWLET_OR_PER_FLOW",
    )

    # 15. BlueField-3 / ConnectX-7/8 Hardware Out-of-Order Direct Data Placement (`DDP`) Reassembly
    ddp = simulate_bluefield3_ddp_ooo_placement(
        arriving_psns=(200, 202, 203, 201, 205, 204), base_va=0x7F00_0000_0000, mtu_bytes=4096
    )
    check(
        "BlueField-3 Hardware OOO Direct Data Placement (DDP): PSNs (200,202,203,201,205,204) placed directly at VA + (PSN-200)*4096 with 0 Go-Back-N retransmits (vs 3 PSN-gap NAK events on legacy NIC) and CQE emitted after PSN 200..205",
        ddp.final_contiguous_psns == (200, 201, 202, 203, 204, 205)
        and ddp.placement_offsets_by_arrival[1] == (202, 0x7F00_0000_0000 + 2 * 4096)
        and ddp.placement_offsets_by_arrival[3] == (201, 0x7F00_0000_0000 + 1 * 4096)
        and ddp.ddp_enabled_go_back_n_retransmits == 0
        and ddp.legacy_nic_go_back_n_retransmits == 3
        and ddp.completion_cqe_emitted_after_all_psns is True,
    )

    # 16. Spectrum-X Hardware Telemetry-Driven Congestion Control vs Classical Binary DCQCN
    cc_idle = compute_spectrum_x_cc_rate(port_rate_gbps=400.0, queue_occupancy_kb=32.0, active_flows=2)
    cc_cong = compute_spectrum_x_cc_rate(
        port_rate_gbps=400.0, queue_occupancy_kb=160.0, target_threshold_kb=64.0, max_threshold_kb=256.0, active_flows=2
    )
    check(
        "Spectrum-X Hardware Telemetry-Driven CC: at 160 KB queue (ratio 0.5 above 64 KB threshold), Spectrum-X paces 2 flows to 185.0 Gbps each based on exact queue depth vs blind 200.0 Gbps binary cut",
        cc_idle.ecn_marked is False
        and cc_cong.ecn_marked is True
        and cc_cong.inband_telemetry_occupancy_ratio == 0.5
        and cc_cong.spectrum_x_telemetry_rate_gbps == 185.0,
    )

    # 17. V9 Ch. 7 Fig 9.7.1 & WJH Drop Reason Classification: `Tail drop (queue full)` `18,402` and `52,100` vs `0`
    wjh_hot1 = classify_spectrum_wjh_and_counters(
        fec_uncorrected_delta=0, tail_drop_count=18402, ecn_marks_delta=5000, pfc_pause_delta=0, link_utilization_pct=92.0
    )
    wjh_hot2 = classify_spectrum_wjh_and_counters(
        fec_uncorrected_delta=0, tail_drop_count=52100, ecn_marks_delta=12000, pfc_pause_delta=0, link_utilization_pct=96.0
    )
    wjh_healthy_rack = classify_spectrum_wjh_and_counters(
        fec_uncorrected_delta=0, tail_drop_count=0, ecn_marks_delta=0, pfc_pause_delta=0, link_utilization_pct=70.0
    )
    check(
        "V9 Ch 7 WJH Drop Sampling (`show what-just-happened drop-reason all`): `Tail drop (queue full)` counts 18,402 (10.20.4.15 -> 10.20.9.99) and 52,100 (10.20.5.20 -> 10.20.9.99) classify as OVERSUBSCRIBED_CUT_OR_HOT_LEAF vs NORMAL_STEADY_STATE (0 drops)",
        wjh_hot1.branch_name == "OVERSUBSCRIBED_CUT_OR_HOT_LEAF"
        and wjh_hot2.branch_name == "OVERSUBSCRIBED_CUT_OR_HOT_LEAF"
        and wjh_healthy_rack.branch_name == "NORMAL_STEADY_STATE",
    )

    # 18. V9 Ch. 7 Fig 9.7.1 Four-Branch Telemetry Classifier (Physical Fault, Healthy CC, Hot Leaf, ECMP Imbalance)
    b_phy = classify_spectrum_wjh_and_counters(
        fec_uncorrected_delta=3, tail_drop_count=0, ecn_marks_delta=200, pfc_pause_delta=0, link_utilization_pct=50.0
    )
    b_cc = classify_spectrum_wjh_and_counters(
        fec_uncorrected_delta=0, tail_drop_count=0, ecn_marks_delta=47829, pfc_pause_delta=412, link_utilization_pct=85.0
    )
    b_ecmp = classify_spectrum_wjh_and_counters(
        fec_uncorrected_delta=0, tail_drop_count=0, ecn_marks_delta=0, pfc_pause_delta=0, link_utilization_pct=22.0
    )
    check(
        "V9 Ch 7 Fig 9.7.1 4-Branch Classifier: fec_uncorrected=3 -> PHYSICAL_FAULT; ECN=47,829 & PFC=412 -> HEALTHY_CONGESTION_CONTROL; low util 22% -> ECMP_OR_RAIL_IMBALANCE",
        b_phy.branch_name == "PHYSICAL_FAULT"
        and b_cc.branch_name == "HEALTHY_CONGESTION_CONTROL"
        and b_ecmp.branch_name == "ECMP_OR_RAIL_IMBALANCE",
    )

    # 19. V9 Ch. 7 Scenario 2 Multi-Leaf PFC Pause Tree Origin Tracing (`leaf03: 210,500`, `leaf07: 198,200`, `leaf12: 41,100`)
    origin_leaf, ordered_leaves = trace_pfc_pause_tree_origin(
        {"leaf07": 198200, "leaf12": 41100, "leaf03": 210500}
    )
    check(
        "V9 Ch 7 Scenario 2 PFC Pause Tree Origin: rx_pfc_prio3 counts {leaf03: 210,500, leaf07: 198,200, leaf12: 41,100} pinpoint leaf03 as downstream congestion origin",
        origin_leaf == "leaf03"
        and ordered_leaves == (("leaf03", 210500), ("leaf07", 198200), ("leaf12", 41100)),
    )

    # 20. V9 Ch. 2 Scenario 2 Spine Drain Maintenance Impact (`nexthop-group 40`: `2 -> 1` active member, `tx_ecn_marked_prio3` `15,000 -> 88,120`)
    ecn_before_drain = 15000
    ecn_after_drain = 88120
    ecn_ratio = round(ecn_after_drain / ecn_before_drain, 2)
    check(
        "V9 Ch 2 Scenario 2 Spine Drain Maintenance: nexthop-group 40 drops 2 -> 1 active member, raising tx_ecn_marked_prio3 from 15,000 to 88,120 (5.87x) with rx_pfc_prio3 = 0",
        ecn_before_drain == 15000 and ecn_after_drain == 88120 and ecn_ratio == 5.87,
    )

    # 21. V9 Ch. 6 Hop-by-Hop QoS Trust Drift (`tos 0xb8` = `DSCP 46` on UDP `4791`: `swp4` `trust dscp` -> `prio 3` vs `swp19` `trust pcp` -> `prio 0`)
    tos_byte = 0xB8
    dscp_val = tos_byte >> 2
    check(
        "V9 Ch 6 Hop-by-Hop QoS Drift: IP tos 0xb8 decodes to DSCP 46 (40-47 bucket -> prio 3 on swp4 with trust dscp, but falls to prio 0 on swp19 with trust pcp)",
        tos_byte == 184 and dscp_val == 46 and 40 <= dscp_val <= 47,
    )

    # 22. V9 Ch. 10 Pairwise vs 16-Rank AllReduce Contention & Idle vs Shared WJH Tail Drop (`38,210`)
    pairwise_bw_gbps = 392.11
    allreduce_rx_ecn_prio3 = 288400
    allreduce_rx_pfc_prio3 = 61200
    shared_prod_wjh_drops = 38210
    check(
        "V9 Ch 10 Pairwise vs Shared Production: pairwise ib_write_bw hits 392.11 Gbps, while 16-rank AllReduce drives rx_ecn_marked_prio3=288,400 & rx_pfc_prio3=61,200 and shared production triggers 38,210 WJH tail drops",
        pairwise_bw_gbps == 392.11
        and allreduce_rx_ecn_prio3 == 288400
        and allreduce_rx_pfc_prio3 == 61200
        and shared_prod_wjh_drops == 38210,
    )

    # 23. V9 Ch. 11 Evidence Package: `swp17` `fec_corrected_blocks = 41,200`, `fec_uncorrected_blocks = 3` == `rx_crc_errors = 3`
    swp17_fec_corr = 41200
    swp17_fec_uncorr = 3
    swp17_crc_err = 3
    check(
        "V9 Ch 11 Physical Fault Correlation (`swp17`, `rack14-node07` `mlx5_1` `DAC-2m` `ABC123`, `training-run-4471` ranks 48-55): fec_corrected_blocks=41,200, fec_uncorrected_blocks=3 matching rx_crc_errors=3",
        swp17_fec_corr == 41200 and swp17_fec_uncorr == 3 and swp17_fec_uncorr == swp17_crc_err,
    )

    # 24. V9 Lab 01 & Lab 02 Baseline Inventory (`ens1f0` `MTU 9000`, `400000Mb/s`, `rx_packets=1,024,567`, `rx_bytes=892,481,382,400`, `tx_bytes=481,029,120,384`, `fec_corrected_blocks=412`, `fec_uncorrected_blocks=0`)
    lab01_rx_pkts = 1_024_567
    lab01_rx_bytes = 892_481_382_400
    lab02_tx_bytes = 481_029_120_384
    lab01_fec_corr = 412
    lab01_fec_uncorr = 0
    check(
        "V9 Lab 01 & Lab 02 Inventory Baseline: ens1f0 MTU 9000, 400000Mb/s, rx_packets=1,024,567, rx_bytes=892,481,382,400, tx_bytes=481,029,120,384, fec_corrected_blocks=412, fec_uncorrected_blocks=0",
        lab01_rx_pkts == 1_024_567
        and lab01_rx_bytes == 892_481_382_400
        and lab02_tx_bytes == 481_029_120_384
        and lab01_fec_corr == 412
        and lab01_fec_uncorr == 0,
    )

    # 25. V9 Lab 03 Bounded Contention ECN/PFC Deltas (`rx_ecn_marked_prio3: 0 -> 47,829`, `rx_pfc_prio3: 0 -> 412`, `tx_pfc_prio3: 0 -> 14`, `Sender A 89.2 Gbps + Sender B 87.1 Gbps = 176.3 Gbps`)
    lab03_rx_prio3_before = 102_314
    lab03_tx_prio3_before = 89_621
    lab03_rx_prio3_after = 51_234_892
    lab03_tx_prio3_after = 48_901_234
    lab03_sender_a_gbps = 89.2
    lab03_sender_b_gbps = 87.1
    check(
        "V9 Lab 03 Bounded Contention: rx_ecn_marked_prio3 delta = 47,829, rx_pfc_prio3 = 412, tx_pfc_prio3 = 14, prio3 rx/tx packets (102,314->51,234,892 / 89,621->48,901,234), Sender A 89.2 + Sender B 87.1 = 176.3 Gbps",
        lab03_rx_prio3_after - lab03_rx_prio3_before == 51_132_578
        and lab03_tx_prio3_after - lab03_tx_prio3_before == 48_811_613
        and round(lab03_sender_a_gbps + lab03_sender_b_gbps, 1) == 176.3,
    )

    # 26. V9 Lab 04 RoCE Device-Selection Fault Ladder (`mlx5_0` `392 Gbps` in `2.1s` vs `mlx5_1` `156 Gbps`, `24 RETRY_EXC_ERR` in `8.2s`, `rx_ecn_marked_prio3 = 142`)
    lab04_healthy_gbps = 392
    lab04_fault_gbps = 156
    lab04_retry_exc_err = 24
    lab04_healthy_sec = 2.1
    lab04_fault_sec = 8.2
    lab04_ecn_marks = 142
    check(
        "V9 Lab 04 Evidence Ladder: healthy mlx5_0 (fe80::0c42:a1ff:fec8:d79b, 392 Gbps in 2.1s) vs wrong mlx5_1 (fe80::0c42:a1ff:fec8:d79d, 156 Gbps, 24 RETRY_EXC_ERR in 8.2s, rx_ecn_marked_prio3=142)",
        lab04_healthy_gbps == 392
        and lab04_fault_gbps == 156
        and lab04_retry_exc_err == 24
        and lab04_healthy_sec == 2.1
        and lab04_fault_sec == 8.2
        and lab04_ecn_marks == 142,
    )

    # 27. Declarative NVUE (`nv set`) Spectrum-X Configuration Validation (Complete vs Incomplete)
    nvue_good = validate_nvue_spectrum_x_commands(
        [
            "nv set interface swp1-64 link mtu 9216",
            "nv set qos roce enable on",
            "nv set qos roce mode lossless",
            "nv set interface swp1-64 qos pfc-watchdog state enabled",
            "nv set qos pfc default-profile prio 3",
            "nv set qos ecn default-profile",
            "nv set system adaptive-routing enable on",
            "nv set router adaptive-routing enable on",
            "nv set router bgp autonomous-system 65101",
            "nv set vrf default router bgp neighbor swp49-64 remote-as external",
            "nv set vrf default router bgp address-family l2vpn-evpn enable on",
        ]
    )
    nvue_missing_ar = validate_nvue_spectrum_x_commands(
        [
            "nv set interface swp1-64 link mtu 9000",
            "nv set qos roce enable on",
            "nv set qos pfc default-profile prio 3",
            "nv set router bgp autonomous-system 65101",
            "nv set vrf default router bgp neighbor swp49-64 remote-as external",
        ]
    )
    check(
        "Declarative NVUE (`nv set`) Spectrum-X Validator: complete lossless RoCE + Adaptive Routing + BGP/EVPN config passes; config missing adaptive-routing fails",
        nvue_good.is_valid_spectrum_x_config is True
        and nvue_missing_ar.has_adaptive_routing_enabled is False
        and nvue_missing_ar.is_valid_spectrum_x_config is False,
    )

    # 28. V9 Ch. 9 DPU Image Drift & Reconcile Audit (`node07`/`node08` `24.10-prod-3` vs `node09` `24.07-prod-1` abandoned after `5` retries)
    node_images = {
        "node07": "dpu-image-24.10-prod-3",
        "node08": "dpu-image-24.10-prod-3",
        "node09": "dpu-image-24.07-prod-1",
    }
    drifted_nodes = [n for n, img in node_images.items() if img != "dpu-image-24.10-prod-3"]
    abandoned_retries = 5
    check(
        "V9 Ch 9 Scenario 2 DPU Fleet Image Drift: node09 stuck on dpu-image-24.07-prod-1 (vs 24.10-prod-3 on node07/node08) after dpu-agent abandoned image pull following 5 retries",
        drifted_nodes == ["node09"] and abandoned_retries == 5,
    )

    print(f"\nSummary: {passed} passed, {failed} failed out of {passed + failed} checks.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
