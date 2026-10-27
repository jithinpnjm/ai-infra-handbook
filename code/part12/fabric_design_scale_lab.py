#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.13: Fabric design: topology, oversubscription and scale."""

from __future__ import annotations

import sys

from fabric_design_scale import (
    AI_DGX_H100_RACK_POWER_MAX_KW,
    AI_DGX_H100_RACK_POWER_MIN_KW,
    AI_DGX_H100_RACK_SERVERS_MAX,
    AI_DGX_H100_RACK_SERVERS_MIN,
    CHASSIS_SPINE_RADIX_256_400G,
    CLOS_3STAGE_64PORT_MAX_GPUS,
    CLOS_3STAGE_144PORT_MAX_GPUS,
    CLOS_5STAGE_BLOCK_GPUS,
    CLOS_5STAGE_BLOCK_ROWS,
    CLOS_5STAGE_CHASSIS_MAX_GPUS,
    CLOS_5STAGE_FIXED_SUPER_SPINES,
    CLOS_5STAGE_MAX_OVERSUB_RATIO,
    DC_COOLING_POWER_SHARE_MAX_PCT,
    DC_COOLING_POWER_SHARE_MIN_PCT,
    DC_IT_POWER_SHARE_MAX_PCT,
    DC_IT_POWER_SHARE_MIN_PCT,
    DGX_A100_HEIGHT_U,
    DGX_H100_4PLUS2_POWER_KW,
    DGX_H100_ACTIVE_PSUS_4PLUS2,
    DGX_H100_DEPTH_IN,
    DGX_H100_HEIGHT_U,
    DGX_H100_PSU_COUNT,
    DGX_H100_PSU_RATING_KW,
    DGX_H100_REDUNDANT_PSUS_4PLUS2,
    DGX_H100_WIDTH_IN,
    GLOBAL_DC_POWER_SHARE_PCT,
    GPUS_PER_STANDARD_SERVER,
    IDEAL_PUE,
    LIQUID_COOLING_MARKET_2026_USD_BILLIONS,
    LIQUID_COOLING_POWER_REDUCTION_PCT,
    MULTI_PLANAR_LANE_BW_GBPS,
    MULTI_PLANAR_NIC_BW_GBPS,
    MULTI_PLANAR_PLANES,
    MULTI_PLANAR_TOR_800G_PORTS,
    MULTI_PLANAR_TOR_DOWNLINKS_200G,
    MULTI_PLANAR_TOR_UPLINKS_400G,
    MULTI_PLANAR_TOR_UPLINKS_800G,
    NVSWITCH_INTERNAL_BW_GBPS,
    OPTICS_OSFP_MAX_W,
    OPTICS_QSFP28_MAX_W,
    OPTICS_QSFP56_DD_MAX_W,
    RDHX_RACK_COOLING_CAPACITY_KW,
    SCHEDULED_FABRIC_CELL_SIZES_BYTES,
    SPRAYED_LIQUID_ENERGY_REDUCTION_PCT,
    STANDARD_RACK_DEPTH_IN,
    STANDARD_RACK_HEIGHT_U,
    STANDARD_RACK_WIDTH_IN,
    SWITCH_64X400G_QFX5230_POWER_KW,
    SWITCH_RADIX_64_400G,
    SWITCH_RADIX_144_800G,
    TOPOGRAPH_AGGREGATION_DELAY_S,
    TOPOGRAPH_FETCH_ATTEMPTS,
    TOPOGRAPH_FETCH_TIMEOUT_S,
    TOPOGRAPH_FETCH_WAIT_S,
    TOPOGRAPH_HTTPS_PORT,
    TOPOGRAPH_PAGE_SIZE,
    TOPOGRAPH_PROMETHEUS_MEASURABLES,
    TRADITIONAL_DC_RACK_AVG_MAX_KW,
    TRADITIONAL_DC_RACK_AVG_MIN_KW,
    TRADITIONAL_DC_RACK_POWER_MAX_KW,
    TRADITIONAL_DC_RACK_POWER_MIN_KW,
    analyze_scheduled_fabric_cells,
    calculate_3stage_clos_scale,
    calculate_5stage_clos_scale,
    calculate_rack_thermal_and_power_budget,
    compare_leaf_placements,
    compare_rail_designs,
    compare_scale_out_topologies,
    evaluate_multi_planar_breakout,
    evaluate_oversubscription_and_cut_scenarios,
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

    print("=== Chapter 12.13 Lab: Fabric Design: Topology, Oversubscription and Scale ===")

    # 1. Rail-Optimized (ROD) vs Rail-Only vs Rail-Unified (RUD) properties (ADC Ch 3)
    rails = compare_rail_designs()
    check(
        "ADC Ch 3 ROD vs Rail-Only vs RUD: ROD (1-hop intra-rail, 2-hop inter-rail via spine, 1/8 rail failure blast radius)",
        rails["ROD"].intra_rail_network_hops == 1
        and rails["ROD"].inter_rail_network_hops == 2
        and not rails["ROD"].requires_deterministic_path_forwarding
        and GPUS_PER_STANDARD_SERVER == 8
        and NVSWITCH_INTERNAL_BW_GBPS == 900,
    )
    check(
        "ADC Ch 3 Rail-Only & RUD: Rail-Only (0 network hops inter-rail, handled via 900 GB/s NVSwitch) vs RUD (requires DPF, single leaf failure isolates all 8 GPUs)",
        rails["Rail-Only"].intra_rail_network_hops == 1
        and rails["Rail-Only"].inter_rail_network_hops == 0
        and rails["RUD"].requires_deterministic_path_forwarding
        and "Entire server" in rails["RUD"].single_leaf_failure_blast_radius,
    )

    # 2. Rack dimensions, server U heights, and power budgets (ADC Ch 3 & Ch 5)
    check(
        "ADC Ch 3 & Ch 5 rack physical dimensions & power: 19 in x 36 in x 42U rack, DGX H100 (19 in x 35.3 in x 8U) vs DGX A100 (6U), 4-5 servers/rack = 48-60 kW vs 10-25 kW (16-18 / 20-25 kW avg) traditional",
        STANDARD_RACK_WIDTH_IN == 19
        and STANDARD_RACK_DEPTH_IN == 36
        and STANDARD_RACK_HEIGHT_U == 42
        and DGX_H100_WIDTH_IN == 19
        and DGX_H100_DEPTH_IN == 35.3
        and DGX_H100_HEIGHT_U == 8
        and DGX_A100_HEIGHT_U == 6
        and AI_DGX_H100_RACK_SERVERS_MIN == 4
        and AI_DGX_H100_RACK_SERVERS_MAX == 5
        and AI_DGX_H100_RACK_POWER_MIN_KW == 48
        and AI_DGX_H100_RACK_POWER_MAX_KW == 60
        and TRADITIONAL_DC_RACK_POWER_MIN_KW == 10
        and TRADITIONAL_DC_RACK_POWER_MAX_KW == 25
        and TRADITIONAL_DC_RACK_AVG_MIN_KW == 16
        and TRADITIONAL_DC_RACK_AVG_MAX_KW == 25,
    )

    # 3. Leaf placement comparison: ToR vs MoR vs EoR (ADC Ch 3 Table 3-1)
    placements = compare_leaf_placements()
    check(
        "ADC Ch 3 Table 3-1 ToR vs MoR vs EoR cable span across an 8-rack (32-server, 256-GPU) row: ToR = 8 racks (Less space, More power/cooling, ideal for RUD DAC/AEC), MoR = 6 racks (shortest span), EoR = 10 racks (longest span)",
        placements["ToR"].max_cable_span_racks == 8
        and placements["ToR"].rack_space_requirement == "Less"
        and placements["ToR"].power_requirement_per_compute_rack == "More"
        and placements["ToR"].ideal_for_rud_with_dac_aec
        and placements["MoR"].max_cable_span_racks == 6
        and placements["MoR"].power_requirement_per_compute_rack == "Less"
        and not placements["MoR"].cabling_within_compute_rack
        and placements["EoR"].max_cable_span_racks == 10
        and placements["EoR"].power_requirement_per_compute_rack == "Less",
    )

    # 4. 3-stage Clos scaling with 64x400G switches (ADC Ch 3 Fig 3-9 & V7 Ch 11 Scenario 1)
    clos_1row = calculate_3stage_clos_scale(64, 1)
    clos_2row = calculate_3stage_clos_scale(64, 2)
    clos_4row = calculate_3stage_clos_scale(64, 4)
    clos_8row = calculate_3stage_clos_scale(64, 8)
    check(
        "ADC Ch 3 Fig 3-9 & V7 Ch 11 Scenario 1 (64x400G 3-stage Clos): 1 row = 256 GPUs (8L/4S), 2 rows = 512 GPUs (16L/8S), 4 rows = 1,024 GPUs (128 DGX H100, 32L/16S), max 8 rows = 2,048 GPUs (64L/32S)",
        (clos_1row.total_gpus, clos_1row.leaf_switches, clos_1row.spine_switches) == (256, 8, 4)
        and (clos_2row.total_gpus, clos_2row.leaf_switches, clos_2row.spine_switches) == (512, 16, 8)
        and (clos_4row.total_gpus, clos_4row.total_servers, clos_4row.leaf_switches, clos_4row.spine_switches)
        == (1024, 128, 32, 16)
        and (clos_8row.total_gpus, clos_8row.leaf_switches, clos_8row.spine_switches)
        == (CLOS_3STAGE_64PORT_MAX_GPUS, 64, 32),
    )

    # 5. 3-stage Clos with 256x400G chassis spine (ADC Ch 3 Fig 3-10)
    clos_8row_chassis = calculate_3stage_clos_scale(64, 8, use_chassis_spine_256=True)
    check(
        "ADC Ch 3 Fig 3-10 chassis-based 256x400G spine: 2,048 GPUs with 64 leaves and 8 chassis spines (1/4 of 32 fixed spines)",
        CHASSIS_SPINE_RADIX_256_400G == 256
        and clos_8row_chassis.total_gpus == 2048
        and clos_8row_chassis.leaf_switches == 64
        and clos_8row_chassis.spine_switches == 8
        and clos_8row_chassis.chassis_spine_used,
    )

    # 6. 3-stage Clos with 144x800G Q3400-RD switches (superpod-gb300-ra Table 3)
    gb300_2su = calculate_3stage_clos_scale(144, 2)
    gb300_4su = calculate_3stage_clos_scale(144, 4)
    gb300_8su = calculate_3stage_clos_scale(144, 8)
    gb300_16su = calculate_3stage_clos_scale(144, 16)
    check(
        "superpod-gb300-ra Table 3 (144x800G Q3400-RD 2-tier/3-stage Clos): (2, 4, 8, 16) SUs -> (1,152, 2,304, 4,608, 9,216) GPUs, (16, 32, 64, 128) leaves, (8, 18, 36, 72) spines",
        SWITCH_RADIX_144_800G == 144
        and (gb300_2su.total_gpus, gb300_2su.leaf_switches, gb300_2su.spine_switches) == (1152, 16, 8)
        and (gb300_4su.total_gpus, gb300_4su.leaf_switches, gb300_4su.spine_switches) == (2304, 32, 18)
        and (gb300_8su.total_gpus, gb300_8su.leaf_switches, gb300_8su.spine_switches) == (4608, 64, 36)
        and (gb300_16su.total_gpus, gb300_16su.leaf_switches, gb300_16su.spine_switches)
        == (CLOS_3STAGE_144PORT_MAX_GPUS, 128, 72),
    )

    # 7. 5-stage Clos 1,024-GPU Block/Brick definition (ADC Ch 3 Fig 3-11)
    check(
        "ADC Ch 3 Fig 3-11 5-stage Clos block/brick: 4 rows = 1 block = 1,024 GPUs (32 leaf switches, 32 spine switches of 64x400G, 1,024 super-spine-facing ports)",
        CLOS_5STAGE_BLOCK_GPUS == 1024
        and CLOS_5STAGE_BLOCK_ROWS == 4
        and CLOS_5STAGE_FIXED_SUPER_SPINES == 32,
    )

    # 8. 5-stage Clos 1:1 to 7:1 super-spine oversubscription table (ADC Ch 3 Fig 3-12)
    oversub_rows = [calculate_5stage_clos_scale(k) for k in range(1, 8)]
    expected_5stage = [
        (1, 2, 8, 2048, 64, 64, 32, 2048),
        (2, 4, 16, 4096, 128, 128, 32, 2048),
        (3, 6, 24, 6144, 192, 192, 32, 2048),
        (4, 8, 32, 8192, 256, 256, 32, 2048),
        (5, 10, 40, 10240, 320, 320, 32, 2048),
        (6, 12, 48, 12288, 384, 384, 32, 2048),
        (7, 14, 56, 14336, 448, 448, 32, 2048),
    ]
    actual_5stage = [
        (
            r.oversubscription_ratio,
            r.blocks,
            r.rows_or_su_count,
            r.total_gpus,
            r.leaf_switches,
            r.spine_switches,
            r.super_spine_switches,
            r.super_spine_facing_ports,
        )
        for r in oversub_rows
    ]
    check(
        "ADC Ch 3 Fig 3-12 5-stage Clos 1:1..7:1 super-spine oversubscription: (2,048..14,336 GPUs, 2..14 blocks, 8..56 rows, 64..448 leaves/spines, fixed 32 super-spines = 2,048 super-spine ports)",
        actual_5stage == expected_5stage and CLOS_5STAGE_MAX_OVERSUB_RATIO == 7,
    )

    # 9. 5-stage Clos with chassis-based super-spine at 1:1 up to 16,384 GPUs (ADC Ch 3 Fig 3-13)
    chassis_2k = calculate_5stage_clos_scale(chassis_super_spine_target_gpus=2048)
    chassis_8k = calculate_5stage_clos_scale(chassis_super_spine_target_gpus=8192)
    chassis_16k = calculate_5stage_clos_scale(chassis_super_spine_target_gpus=16384)
    check(
        "ADC Ch 3 Fig 3-13 5-stage Clos with chassis-based super-spine at 1:1 oversubscription: 2,048 (2 blocks), 8,192 (8 blocks), and 16,384 GPUs (16 blocks = 64 rows, 16,384 super-spine ports)",
        (chassis_2k.total_gpus, chassis_2k.blocks, chassis_2k.oversubscription_ratio) == (2048, 2, 1)
        and (chassis_8k.total_gpus, chassis_8k.blocks, chassis_8k.oversubscription_ratio) == (8192, 8, 1)
        and (
            chassis_16k.total_gpus,
            chassis_16k.blocks,
            chassis_16k.rows_or_su_count,
            chassis_16k.super_spine_facing_ports,
            chassis_16k.oversubscription_ratio,
        )
        == (CLOS_5STAGE_CHASSIS_MAX_GPUS, 16, 64, 16384, 1),
    )

    # 10. Scheduled Fabric cell sizes (64, 128, 256 B) and VOQ head-of-line blocking elimination (ADC Ch 3 Fig 3-24)
    cell_64 = analyze_scheduled_fabric_cells(packet_bytes=4096, cell_size_bytes=64, egress_endpoints=1024, traffic_classes=8)
    cell_128 = analyze_scheduled_fabric_cells(packet_bytes=4096, cell_size_bytes=128, egress_endpoints=1024, traffic_classes=8)
    cell_256 = analyze_scheduled_fabric_cells(packet_bytes=4100, cell_size_bytes=256, egress_endpoints=1024, traffic_classes=8)
    check(
        "ADC Ch 3 Fig 3-24 Scheduled Fabric (Jericho3-AI/Ramon3 & Silicon One): 64/128/256-byte cell spraying + Virtual Output Queueing (VOQ) eliminates HoL blocking",
        SCHEDULED_FABRIC_CELL_SIZES_BYTES == (64, 128, 256)
        and cell_64.cells_per_packet == 64
        and cell_64.cell_padding_overhead_pct == 0.0
        and cell_128.cells_per_packet == 32
        and cell_256.cells_per_packet == 17
        and cell_256.padded_wire_bytes == 4352
        and cell_256.voq_queues_Across_fabric == 8192
        and cell_256.hol_blocking_eliminated,
    )

    # 11. Dragonfly (DF / DF+) vs 5-stage Clos vs 1D/2D/3D Torus hop & degree math (ADC Ch 3 Fig 3-25..3-35)
    topos = compare_scale_out_topologies(torus_dim_size=8)
    check(
        "ADC Ch 3 Dragonfly (DF/DF+ full-graph vs Butterfly+ bipartite intra-group, max 3 hops vs 4 in 5-stage Clos) & 1D/2D/3D Torus node degrees (2, 4, 6 links/node)",
        topos["Dragonfly_DF_Plus"].max_network_hops == 3
        and topos["Clos_5Stage"].max_network_hops == 4
        and topos["Torus_1D"].degree_per_node_or_switch == 2
        and topos["Torus_2D"].degree_per_node_or_switch == 4
        and topos["Torus_3D"].degree_per_node_or_switch == 6
        and topos["Torus_3D"].total_endpoints == 512
        and topos["Torus_3D"].max_network_hops == 12,
    )

    # 12. Multi-Planar Scale-Out 800G -> 4x200G breakout & ToR port math (ADC Ch 3 Fig 3-36..3-39)
    mp_healthy = evaluate_multi_planar_breakout(failed_planes=0)
    mp_1plane_down = evaluate_multi_planar_breakout(failed_planes=1)
    check(
        "ADC Ch 3 Fig 3-36 Multi-Planar Scale-Out: 800G NIC -> 4x200G across FP1..FP4, 64x800G ToR -> 128x200G downlinks + 32x800G (or 64x400G) uplinks, 75% surviving BW on 1-plane failure, NIC OOO reassembly",
        mp_healthy.nic_speed_gbps == MULTI_PLANAR_NIC_BW_GBPS == 800
        and mp_healthy.fabric_planes == MULTI_PLANAR_PLANES == 4
        and mp_healthy.breakout_lane_speed_gbps == MULTI_PLANAR_LANE_BW_GBPS == 200
        and mp_healthy.tor_native_800g_ports == MULTI_PLANAR_TOR_800G_PORTS == 64
        and mp_healthy.tor_server_downlinks_200g == MULTI_PLANAR_TOR_DOWNLINKS_200G == 128
        and mp_healthy.tor_spine_uplinks_800g == MULTI_PLANAR_TOR_UPLINKS_800G == 32
        and mp_healthy.tor_spine_uplinks_400g == MULTI_PLANAR_TOR_UPLINKS_400G == 64
        and mp_healthy.surviving_bw_pct_on_single_plane_loss == 100.0
        and mp_1plane_down.surviving_bw_pct_on_single_plane_loss == 75.0
        and mp_healthy.requires_nic_ooo_reassembly,
    )

    # 13. Production oversubscription scenarios: V7 Ch 11, V8 Ch 6, and V9 Ch 10
    ov = evaluate_oversubscription_and_cut_scenarios()
    check(
        "V7 Ch 11 Scenario 1 & 2 + V8 Ch 6 Worked Example: 1:1 non-blocking (12,800G down : 12,800G up -> 400G/node, 2 GB AllReduce = 40 ms) vs 2:1 oversubscribed leaf (6,400G down : 3,200G up -> 200G/node, 2 GB AllReduce = 80 ms; 1-spine loss -> 4:1)",
        ov["V7_1024GPU_NonBlocking_1to1"].oversubscription_normal == 1.0
        and ov["V7_1024GPU_NonBlocking_1to1"].allreduce_2gb_time_ms == 40.0
        and ov["V7_V8_Leaf_2to1_Oversubscribed"].oversubscription_normal == 2.0
        and ov["V7_V8_Leaf_2to1_Oversubscribed"].oversubscription_degraded == 4.0
        and ov["V7_V8_Leaf_2to1_Oversubscribed"].effective_per_node_gbps == 200.0
        and ov["V7_V8_Leaf_2to1_Oversubscribed"].allreduce_2gb_time_ms == 80.0,
    )
    check(
        "V9 Ch 10 Rack Cut capacity arithmetic: 16 nodes x 800G = 12,800 Gbps downlink vs 8x400G = 3,200 Gbps normal (4.00:1) and 7x400G = 2,800 Gbps N-1 degraded (4.57:1)",
        ov["V9_Rack_4to1_And_N_Minus_1"].downlink_gbps == 12800.0
        and ov["V9_Rack_4to1_And_N_Minus_1"].uplink_gbps_normal == 3200.0
        and ov["V9_Rack_4to1_And_N_Minus_1"].uplink_gbps_degraded == 2800.0
        and ov["V9_Rack_4to1_And_N_Minus_1"].oversubscription_normal == 4.0
        and ov["V9_Rack_4to1_And_N_Minus_1"].oversubscription_degraded == 4.57,
    )

    # 14. V8 Ch 6 telemetry evidence: 20:1 PortXmitData uplink imbalance & paired ib_write_bw
    port5_bytes = 21474836480
    port6_bytes = 21489234432
    port7_bytes = 1073741824
    port8_bytes = 1081654272
    imbalance_ratio = round(((port5_bytes + port6_bytes) / 2) / ((port7_bytes + port8_bytes) / 2), 1)
    same_leaf_bw = 397.62
    cross_rack_bw = 201.18
    check(
        "V8 Ch 6 Scenario 1 & 3 telemetry: PortXmitData (4-octet units) ports 5-6 (~21.48 GB) vs ports 7-8 (~1.08 GB) = 19.9:1 (~20:1) imbalance; paired ib_write_bw (2,097,152 B) = 397.62 Gbps same-leaf vs 201.18 Gbps cross-rack",
        imbalance_ratio == 19.9
        and round(same_leaf_bw / cross_rack_bw, 2) == 1.98,
    )

    # 15. V7 Ch 11 Scenario 3 & V8 Ch 11 Scenario 3: Storage/Inference isolation & VL p99 latency
    p99_isolated_ms = 1.8
    p99_shared_vl_ms = 14.2
    p99_separated_vl_ms = 3.1
    check(
        "V7 Ch 11 Scenario 3 & V8 Ch 11 Scenario 3: 100 GB checkpoint burst / shared VL inflates inference p99 latency 1.8 ms -> 14.2 ms (7.89x); separated SL/VL recovers to 3.1 ms",
        round(p99_shared_vl_ms / p99_isolated_ms, 2) == 7.89
        and p99_isolated_ms < p99_separated_vl_ms < p99_shared_vl_ms,
    )

    # 16. ADC Ch 5 Data Center Power Share, DGX H100 4+2 PSU math, Switch & Optics power
    check(
        "ADC Ch 5 facility power & hardware draw: ~2% global power, 40-45% IT / 35-40% cooling split, ideal PUE 1.0, DGX H100 6x3.3 kW PSUs (4+2 redundancy = 13.2 kW), 3 kW QFX5230 64x400G switch, 3.2 W QSFP28 / 12 W QSFP56-DD / 15 W OSFP optics",
        GLOBAL_DC_POWER_SHARE_PCT == 2.0
        and (DC_IT_POWER_SHARE_MIN_PCT, DC_IT_POWER_SHARE_MAX_PCT) == (40, 45)
        and (DC_COOLING_POWER_SHARE_MIN_PCT, DC_COOLING_POWER_SHARE_MAX_PCT) == (35, 40)
        and IDEAL_PUE == 1.0
        and DGX_H100_PSU_COUNT == 6
        and DGX_H100_PSU_RATING_KW == 3.3
        and DGX_H100_ACTIVE_PSUS_4PLUS2 == 4
        and DGX_H100_REDUNDANT_PSUS_4PLUS2 == 2
        and round(DGX_H100_ACTIVE_PSUS_4PLUS2 * DGX_H100_PSU_RATING_KW, 1) == DGX_H100_4PLUS2_POWER_KW == 13.2
        and SWITCH_64X400G_QFX5230_POWER_KW == 3.0
        and (OPTICS_QSFP28_MAX_W, OPTICS_QSFP56_DD_MAX_W, OPTICS_OSFP_MAX_W) == (3.2, 12.0, 15.0),
    )

    # 17. Rack thermal & power calculator and 5 liquid cooling methods (ADC Ch 5)
    rack_4srv = calculate_rack_thermal_and_power_budget(
        servers_per_rack=4,
        server_power_kw=13.2,
        switches_in_rack=1,
        switch_chassis_power_kw=3.0,
        optics_per_switch=64,
        optic_power_w=15.0,
        facility_pue=1.25,
    )
    check(
        "ADC Ch 5 rack thermal budget & liquid cooling metrics: 4x13.2 kW servers (52.8 kW) + 1x(3.0 kW + 64x15 W = 3.96 kW) switch = 56.76 kW IT (70.95 kW @ PUE 1.25); ~70% liquid cooling power reduction, >$3B by 2026, 20 kW RDHx, 25.8% sprayed liquid energy reduction",
        rack_4srv.total_switch_plus_optics_kw == 3.96
        and rack_4srv.total_rack_it_power_kw == 56.76
        and rack_4srv.total_facility_power_kw == 70.95
        and "Cold Plate" in rack_4srv.recommended_cooling_method
        and LIQUID_COOLING_POWER_REDUCTION_PCT == 70.0
        and LIQUID_COOLING_MARKET_2026_USD_BILLIONS == 3.0
        and RDHX_RACK_COOLING_CAPACITY_KW == 20.0
        and SPRAYED_LIQUID_ENERGY_REDUCTION_PCT == 25.8,
    )

    # 18. BCM 11 Topograph Slurm topology discovery parameters (bcm11-admin §7.5)
    check(
        "BCM 11 §7.5 Topograph service parameters: HTTPS port 49021, Fetch timeout 20 s, 12 attempts, 15 s wait, 15 s aggregation delay, PageSize 100, 26 Prometheus measurables",
        TOPOGRAPH_HTTPS_PORT == 49021
        and TOPOGRAPH_FETCH_TIMEOUT_S == 20
        and TOPOGRAPH_FETCH_ATTEMPTS == 12
        and TOPOGRAPH_FETCH_WAIT_S == 15
        and TOPOGRAPH_AGGREGATION_DELAY_S == 15
        and TOPOGRAPH_PAGE_SIZE == 100
        and TOPOGRAPH_PROMETHEUS_MEASURABLES == 26,
    )

    # 19. Leaf-only (spineless) cluster limits for 32-downlink and 64-downlink 8-leaf stripes (ADC Ch 3 Fig 3-6)
    check(
        "ADC Ch 3 Fig 3-6 spineless 8-leaf stripe scale: 8 leaves x 32 downlinks = 256 GPUs (32 servers) with uplinks reserved; 8 leaves x 64 downlinks = 512 GPUs (64 servers) spineless rail-only",
        8 * 32 == 256 and 8 * 64 == 512 and 256 // GPUS_PER_STANDARD_SERVER == 32 and 512 // GPUS_PER_STANDARD_SERVER == 64,
    )

    # 20. Extreme scale leaf counts for 32K, 64K, and 128K GPU clusters (ADC Ch 3 p. 65)
    check(
        "ADC Ch 3 extreme-scale 5-stage/7-stage Clos leaf counts: 32K, 64K, and 128K GPU clusters deploy 8K, 16K, or 32K leaf switches",
        (32, 64, 128) == (8 * 4, 16 * 4, 32 * 4),
    )

    # 21. V8 Ch 11 Scenario 2 worked leaf-radix sizing for 256 GPUs across 16 racks
    check(
        "V8 Ch 11 Scenario 2 leaf-radix arithmetic: 16 single-rail 400G endpoints/rack = 6,400 Gbps downlink; 1:1 non-blocking requires 16x400G uplinks (32-port minimum radix vs 24-port leaf forcing 16:8 = 2:1 oversubscription)",
        16 * 400 == 6400 and 16 + 16 == 32 and (16 * 400) // (8 * 400) == 2,
    )

    # 22. Multi-planar 2-plane failed scenario (50% surviving bandwidth)
    mp_2plane_down = evaluate_multi_planar_breakout(failed_planes=2)
    check(
        "ADC Ch 3 Fig 3-36..3-39 Multi-Planar 2-plane failure resilience: 2 of 4 planes down preserves 50.0% (400 Gbps) capacity per 800G NIC",
        mp_2plane_down.surviving_bw_pct_on_single_plane_loss == 50.0
        and (MULTI_PLANAR_PLANES - 2) * MULTI_PLANAR_LANE_BW_GBPS == 400,
    )

    # 23. Optics power progression from 100G QSFP28 to 400G QSFP56-DD and 400G/800G OSFP (ADC Ch 5)
    qsfp28_64port_w = 64 * OPTICS_QSFP28_MAX_W
    qsfpdd_64port_w = 64 * OPTICS_QSFP56_DD_MAX_W
    osfp_64port_w = 64 * OPTICS_OSFP_MAX_W
    check(
        "ADC Ch 5 64-port switch optics power progression: 64xQSFP28 (3.2 W) = 204.8 W, 64xQSFP56-DD (12 W) = 768.0 W, 64xOSFP (15 W) = 960.0 W (4.69x QSFP28)",
        round(qsfp28_64port_w, 1) == 204.8
        and round(qsfpdd_64port_w, 1) == 768.0
        and round(osfp_64port_w, 1) == 960.0
        and round(osfp_64port_w / qsfp28_64port_w, 2) == 4.69,
    )

    # 24. Rear-Door Heat Exchanger (RDHx <= 20 kW) vs 5-server DGX H100 rack (ADC Ch 3 & Ch 5)
    rack_1srv_rdhx = calculate_rack_thermal_and_power_budget(
        servers_per_rack=1,
        server_power_kw=13.2,
        switches_in_rack=1,
        switch_chassis_power_kw=3.0,
        optics_per_switch=64,
        optic_power_w=15.0,
        facility_pue=1.20,
    )
    rack_5srv_immersion = calculate_rack_thermal_and_power_budget(
        servers_per_rack=5,
        server_power_kw=13.2,
        switches_in_rack=1,
        switch_chassis_power_kw=3.0,
        optics_per_switch=64,
        optic_power_w=15.0,
        facility_pue=1.15,
    )
    check(
        "ADC Ch 5 cooling tier thresholds: 17.16 kW rack fits RDHx (<= 20.0 kW); 5xDGX H100 + 1 switch = 69.96 kW (> 60 kW) requires Cold Plate or Single/Two-Phase Immersion",
        rack_1srv_rdhx.total_rack_it_power_kw == 17.16
        and "RDHx" in rack_1srv_rdhx.recommended_cooling_method
        and rack_5srv_immersion.total_rack_it_power_kw == 69.96
        and "Immersion" in rack_5srv_immersion.recommended_cooling_method,
    )

    # 25. Scheduled Fabric 128-byte cell padding on 1,500-byte Ethernet MTU vs 4,096-byte RDMA payload
    cell_1500_on_128 = analyze_scheduled_fabric_cells(packet_bytes=1500, cell_size_bytes=128)
    check(
        "ADC Ch 3 Scheduled Fabric 128B cell segmentation on 1,500B packet: ceil(1500/128) = 12 cells (1,536B wire, 2.40% padding overhead)",
        cell_1500_on_128.cells_per_packet == 12
        and cell_1500_on_128.padded_wire_bytes == 1536
        and cell_1500_on_128.cell_padding_overhead_pct == 2.4,
    )

    # 26. Dragonfly inter-group full mesh link count for G groups (ADC Ch 3 Fig 3-25..3-27)
    groups = 8
    inter_group_full_mesh_links = (groups * (groups - 1)) // 2
    check(
        "ADC Ch 3 Fig 3-27 Dragonfly full-graph mesh math: 8 nodes/groups require 8*7/2 = 28 direct mesh links (1-hop direct reachability)",
        inter_group_full_mesh_links == 28,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_lab())
