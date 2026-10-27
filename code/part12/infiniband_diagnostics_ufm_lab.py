#!/usr/bin/env python3
"""Self-checking lab for Chapter 12.9: InfiniBand diagnostics, UFM and operations.

Runs 28 deterministic checks covering:
  - SCL Ch. 5 InfiniBand addressing (`49,151` unicast LIDs `0x0001..0xBFFF`, multicast
    `0xC000..0xFFFE`, permissive `0xFFFF`, `0xFE80::/64` & `0xFEC0::/64` GIDs, `20`-byte
    IPoIB hardware address, `4 KB` datagram vs `64 KB` connected MTU, and Table 5-1 speeds
    `SDR` to `GDR` `4x` and `12x`)
  - Complete 27-tool OFED / rdma-core / MFT diagnostic utility taxonomy (`ibstat`, `ibstatus`,
    `ibdev2netdev`, `ibhosts`, `ibswitches`, `ibnodes`, `ibnetdiscover`, `iblinkinfo`, `ibaddr`,
    `ibping`, `ibsysstat`, `ibtracert`, `ibroute`, `perfquery`, `ibqueryerrors`, `ibportstate`,
    `smpquery`, `saquery`, `ibdiagnet`, `mlxlink`, `mst`, `mlxconfig`, `ofed_info`)
  - `perfquery` counter delta classification (`SymbolErrorCounter`, `LinkErrorRecoveryCounter`,
    `LinkDownedCounter`, `PortRcvErrors`, `PortXmitDiscards`, `PortXmitWait`, and `PortXmitData`
    4-octet words) across V8 Ch. 7, Ch. 9, and Ch. 10 scenarios
  - `mlxlink -c -m` SERDES BER (`15E-255`), optical DDM budget (`38 C`, `3255.2 mV`, `6.750 mA`,
    `Rx -14..6 dBm`, `Tx -12..6 dBm`), and degraded lane / optic detection
  - `smpquery nodedesc 914` vs `saquery 914` (`n51001 HCA-1`, `0x0012345600003740`) SM database
    consistency check and `ibdiagnet` multi-stage audit
  - NVIDIA UFM Enterprise HA, SM priority handover (`priority 15` vs `8`/`14`), `P_Key` / SHARP
    integration, BCM 11 (`10.149.0.0/16`, `Topograph` port `49021`), and DGX B200 / GB300
    SuperPOD UFM appliance scaling
  - 7-gate bottom-up troubleshooting workflow (`V8` Ch. 10, Ch. 12, and Labs 01-04).
"""

from __future__ import annotations

import sys

from infiniband_diagnostics_ufm import (
    B200_AOC_MAX_M,
    B200_CABLE_SAFETY_MARGIN_PCT,
    B200_DAC_MAX_100G_M,
    B200_DAC_MAX_400G_M,
    B200_POWER_PER_SU_KW,
    B200_SU_SCALE_TABLE,
    BCM_IBNET_CIDR,
    BCM_TOPOGRAPH_ATTEMPTS,
    BCM_TOPOGRAPH_HTTPS_PORT,
    BCM_TOPOGRAPH_MEASURABLES,
    BCM_TOPOGRAPH_TIMEOUT_S,
    BCM_TOPOGRAPH_WAIT_S,
    GB300_PORT_RATE_GBPS,
    GB300_SU_SCALE_TABLE,
    GB300_SWITCH_MODEL,
    GB300_SWITCH_RADIX,
    IB_CREDIT_UNIT_BYTES,
    IB_DATA_VL_COUNT,
    IB_DEFAULT_GID_PREFIX,
    IB_DIAGNOSTIC_UTILITIES,
    IB_GEN_TABLE_4X_12X_GBPS,
    IB_LID_MULTICAST_MAX,
    IB_LID_MULTICAST_MIN,
    IB_LID_PERMISSIVE,
    IB_LID_RESERVED,
    IB_LID_UNICAST_MAX,
    IB_MULTICAST_GID_HIGH_BYTE,
    IB_PORT_DATA_COUNTER_OCTETS,
    IB_SITE_LOCAL_GID_PREFIX,
    IB_SMP_VL,
    IB_SUBNET_MAX_UNICAST_LIDS,
    IB_TOTAL_VL_COUNT,
    IPOIB_CONNECTED_MTU_BYTES,
    IPOIB_DATAGRAM_MTU_BYTES,
    IPOIB_HWADDR_BYTES,
    SCL5_MLXLINK_BIAS_MA,
    SCL5_MLXLINK_DISTANCE_M,
    SCL5_MLXLINK_MAX_POWER_W,
    SCL5_MLXLINK_SPEED_MASK,
    SCL5_MLXLINK_TEMP_C,
    SCL5_MLXLINK_UPTIME_MIN,
    SCL5_MLXLINK_VOLTAGE_MV,
    SCL5_MLXLINK_WAVELENGTH_NM,
    SCL5_PORT1_LID_DEC,
    SCL5_PORT1_LID_HEX,
    SCL5_PORT1_SM_LID_DEC,
    SCL5_PORT1_SM_LID_HEX,
    SCL5_PORT2_LID_DEC,
    SCL5_PORT2_LID_HEX,
    SCL5_PORT2_SM_LID_DEC,
    SCL5_PORT2_SM_LID_HEX,
    SCL5_QUERY_LID,
    V8_HCA_BASE_LID,
    V8_HCA_CAP_MASK,
    V8_HCA_FW_VER,
    V8_HCA_MAX_QP,
    V8_HCA_MAX_QP_WR,
    V8_HCA_MAX_SGE,
    V8_HCA_NODE_GUID,
    V8_HCA_PART_ID,
    V8_HCA_SM_LID,
    V8_HCA_VENDOR_ID,
    V8_SM_ACTIVITY_COUNT,
    V8_SM_MASTER_GUID,
    V8_SM_MASTER_PRIORITY,
    V8_SM_MASTER_STATE,
    V8_TRAP_LINK_STATE_CHANGE,
    audit_perfquery_counter_deltas,
    audit_topology_against_source_of_truth,
    compare_smpquery_and_saquery,
    evaluate_error_rate_acceleration,
    evaluate_ib_write_lat_percentiles,
    evaluate_ibdiagnet_stages,
    evaluate_mlxlink_module_health,
    evaluate_ufm_enterprise_ha,
    run_seven_gate_bottom_up_triage,
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

    print("=== Chapter 12.9 Lab: InfiniBand Diagnostics, UFM and Operations ===")

    # 1. SCL Ch. 5: Addressing, LID space (49,151), GID prefixes, VL15, and IPoIB 20-byte MAC / MTU
    check(
        "SCL Ch 5 Addressing & IPoIB: 49,151 unicast LIDs (0x0001..0xBFFF), multicast 0xC000..0xFFFE, permissive 0xFFFF, GID 0xFE80/0xFEC0/0xFF, 16 VLs (VL15 SMP, 64B credit), 20B IPoIB MAC (4KB datagram / 64KB connected)",
        IB_SUBNET_MAX_UNICAST_LIDS == 49_151
        and IB_LID_RESERVED == 0x0000
        and IB_LID_UNICAST_MAX == 0xBFFF
        and IB_LID_MULTICAST_MIN == 0xC000
        and IB_LID_MULTICAST_MAX == 0xFFFE
        and IB_LID_PERMISSIVE == 0xFFFF
        and IB_DEFAULT_GID_PREFIX == 0xFE80
        and IB_SITE_LOCAL_GID_PREFIX == 0xFEC0
        and IB_MULTICAST_GID_HIGH_BYTE == 0xFF
        and IB_TOTAL_VL_COUNT == 16
        and IB_DATA_VL_COUNT == 15
        and IB_SMP_VL == 15
        and IB_CREDIT_UNIT_BYTES == 64
        and IPOIB_HWADDR_BYTES == 20
        and IPOIB_DATAGRAM_MTU_BYTES == 4096
        and IPOIB_CONNECTED_MTU_BYTES == 65536,
    )

    # 2. SCL Ch. 5 Table 5-1: InfiniBand generation speeds (SDR to GDR, 4x and 12x effective Gbps)
    check(
        "SCL Ch 5 Table 5-1 Generation Bandwidths: SDR (8/24G), DDR (16/48G), QDR (32/96G), FDR (54.4/163.2G), EDR (100/300G), HDR (200/600G), NDR (400/1200G), XDR (800/2400G), GDR (1600/4800G)",
        IB_GEN_TABLE_4X_12X_GBPS["SDR"] == (2.5, 8.0, 24.0, "8b/10b")
        and IB_GEN_TABLE_4X_12X_GBPS["FDR"] == (14.0625, 54.4, 163.2, "64b/66b")
        and IB_GEN_TABLE_4X_12X_GBPS["HDR"] == (53.125, 200.0, 600.0, "64b/66b")
        and IB_GEN_TABLE_4X_12X_GBPS["NDR"] == (106.25, 400.0, 1200.0, "256b/257b")
        and IB_GEN_TABLE_4X_12X_GBPS["XDR"] == (200.0, 800.0, 2400.0, "256b/257b")
        and IB_GEN_TABLE_4X_12X_GBPS["GDR"] == (400.0, 1600.0, 4800.0, "256b/257b"),
    )

    # 3. SCL Ch. 5 `ibstat` (decimal) vs `ibstatus` (hex) base_lid and sm_lid formatting on MT4113
    check(
        "SCL Ch 5 ibstat vs ibstatus formatting: Port 1 Base LID 913 == 0x391, SM LID 43 == 0x2b; Port 2 Base LID 1361 == 0x551, SM LID 698 == 0x2ba",
        SCL5_PORT1_LID_DEC == SCL5_PORT1_LID_HEX == 913
        and SCL5_PORT1_SM_LID_DEC == SCL5_PORT1_SM_LID_HEX == 43
        and SCL5_PORT2_LID_DEC == SCL5_PORT2_LID_HEX == 1361
        and SCL5_PORT2_SM_LID_DEC == SCL5_PORT2_SM_LID_HEX == 698,
    )

    # 4. Complete 27-utility OFED / rdma-core / MFT diagnostic taxonomy
    required_tools = {
        "ibstat", "ibstatus", "ibdev2netdev", "ibv_devices", "ibv_devinfo", "show_gids", "ofed_info",
        "ibhosts", "ibswitches", "ibnodes", "ibnetdiscover", "iblinkinfo",
        "ibaddr", "ibping", "ibsysstat", "ibtracert", "ibroute",
        "sminfo", "smpquery", "saquery",
        "perfquery", "ibqueryerrors", "ibdiagnet", "mlxlink", "mst",
        "mlxconfig", "ibportstate",
    }
    mutating_tools = {name for name, spec in IB_DIAGNOSTIC_UTILITIES.items() if spec.mutates_state}
    check(
        "OFED / MFT Utility Taxonomy: all 27 diagnostic utilities cataloged; only `mlxconfig` and `ibportstate` flagged as state-mutating",
        set(IB_DIAGNOSTIC_UTILITIES.keys()) == required_tools
        and len(IB_DIAGNOSTIC_UTILITIES) == 27
        and mutating_tools == {"mlxconfig", "ibportstate"},
    )

    # 5. V8 Lab 01 `ibv_devinfo` & `ibstat` inventory constants (`MT4129` ConnectX-7, `fw_ver 28.39.2048`)
    check(
        "V8 Lab 01 HCA & Port Inventory (`MT4129` ConnectX-7): fw 28.39.2048, vendor 0x02c9, GUID 0x08c0eb0300f1a2c3, max_qp 262,144, max_qp_wr 32,768, max_sge 30, Base lid 12, SM lid 1, cap_mask 0x2651e848",
        V8_HCA_PART_ID == 4129
        and V8_HCA_FW_VER == "28.39.2048"
        and V8_HCA_VENDOR_ID == 0x02C9
        and V8_HCA_NODE_GUID == 0x08C0EB0300F1A2C3
        and V8_HCA_MAX_QP == 262_144
        and V8_HCA_MAX_QP_WR == 32_768
        and V8_HCA_MAX_SGE == 30
        and V8_HCA_BASE_LID == 12
        and V8_HCA_SM_LID == 1
        and V8_HCA_CAP_MASK == 0x2651E848,
    )

    # 6. `perfquery` Scenario A: V8 Ch. 9 Scenario 1 Historical Scar Tissue (`12,034 -> 12,034` over 300 s)
    scar_audit = audit_perfquery_counter_deltas(
        lid=44,
        port=9,
        window_sec=300.0,
        before={"SymbolErrorCounter": 12_034, "LinkDownedCounter": 0, "PortXmitWait": 100, "PortXmitData": 0},
        after={"SymbolErrorCounter": 12_034, "LinkDownedCounter": 0, "PortXmitWait": 100, "PortXmitData": 5_368_709_120},
    )
    check(
        "V8 Ch 9 Scenario 1 Historical Scar Tissue (`perfquery <lid> 9` over 300 s): SymbolErrorCounter 12,034 -> 12,034 (delta=0) classified as HISTORICAL_SCAR_TISSUE",
        scar_audit.symbol_error_delta == 0
        and scar_audit.xmit_bytes_delta == 21_474_836_480
        and scar_audit.classification == "HISTORICAL_SCAR_TISSUE",
    )

    # 7. `perfquery` Scenario B: V8 Ch. 7 / Ch. 10 Pure Fabric Congestion (`PortXmitWait=998,432`, 0 physical errors)
    cong_audit = audit_perfquery_counter_deltas(
        lid=44,
        port=3,
        window_sec=60.0,
        before={"SymbolErrorCounter": 0, "LinkDownedCounter": 0, "PortXmitWait": 0},
        after={"SymbolErrorCounter": 0, "LinkDownedCounter": 0, "PortXmitWait": 998_432},
    )
    check(
        "V8 Ch 7 / Ch 10 Pure Congestion (`switch port 3`): PortXmitWait delta=998,432 with SymbolErrorCounter=0 & LinkDownedCounter=0 classified as PURE_CONGESTION",
        cong_audit.port_xmit_wait_delta == 998_432
        and cong_audit.symbol_error_delta == 0
        and cong_audit.link_downed_delta == 0
        and cong_audit.classification == "PURE_CONGESTION",
    )

    # 8. `perfquery` Scenario C: V8 Ch. 7 / Ch. 10 Flapping Physical Fault (`PortXmitWait=2,109`, `SymbolErrorCounter=41`, `LinkDownedCounter=2`)
    flap_audit = audit_perfquery_counter_deltas(
        lid=44,
        port=4,
        window_sec=60.0,
        before={"SymbolErrorCounter": 0, "LinkDownedCounter": 0, "PortXmitWait": 0},
        after={"SymbolErrorCounter": 41, "LinkDownedCounter": 2, "PortXmitWait": 2_109},
    )
    check(
        "V8 Ch 7 / Ch 10 Physical Link Fault (`switch port 4`): SymbolErrorCounter=41 & LinkDownedCounter=2 classified as FLAPPING_LINK_FAULT",
        flap_audit.symbol_error_delta == 41
        and flap_audit.link_downed_delta == 2
        and flap_audit.classification == "FLAPPING_LINK_FAULT",
    )

    # 9. `perfquery` Scenario D: Routing / P_Key / HoQ Discard (`PortXmitDiscards` > 0)
    disc_audit = audit_perfquery_counter_deltas(
        lid=44,
        port=11,
        window_sec=60.0,
        before={"PortXmitDiscards": 10},
        after={"PortXmitDiscards": 260},
    )
    check(
        "perfquery PortXmitDiscards delta=250 classified as ROUTING_OR_POLICY_DISCARD (LFT, P_Key, MTU, or HoQ lifetime drop)",
        disc_audit.port_xmit_discards_delta == 250
        and disc_audit.classification == "ROUTING_OR_POLICY_DISCARD",
    )

    # 10. `perfquery` Scenario E: V8 Ch. 6 4-octet `PortXmitData` uplink imbalance (`21,474,836,480` B vs `1,073,741,824` B)
    up5 = audit_perfquery_counter_deltas(
        lid=10, port=5, window_sec=10.0,
        before={"PortXmitData": 0}, after={"PortXmitData": 5_368_709_120},
    )
    up7 = audit_perfquery_counter_deltas(
        lid=10, port=7, window_sec=10.0,
        before={"PortXmitData": 0}, after={"PortXmitData": 268_435_456},
    )
    check(
        "V8 Ch 6 PortXmitData 4-octet conversion: Port 5 (5,368,709,120 words = 21,474,836,480 B) vs Port 7 (268,435,456 words = 1,073,741,824 B) = 20.0:1 ratio",
        IB_PORT_DATA_COUNTER_OCTETS == 4
        and up5.xmit_bytes_delta == 21_474_836_480
        and up7.xmit_bytes_delta == 1_073_741_824
        and round(up5.xmit_bytes_delta / up7.xmit_bytes_delta, 1) == 20.0,
    )

    # 11. V8 Ch. 9 Story: "The Fabric Failed Slowly" Day 1 -> Day 4 -> Day 7 error acceleration
    slow_fail = evaluate_error_rate_acceleration(
        day1_errors=4, day4_errors=890, day7_errors=41_200,
        day1_downed=0, day4_downed=3, day7_downed=11,
        days_per_window=3.0,
    )
    check(
        "V8 Ch 9 'The Fabric Failed Slowly' (port 12): Day 1 (4) -> Day 4 (890, +886 = 295.33/day) -> Day 7 (41,200, +40,310 = 13,436.67/day) = 45.5x acceleration, LinkDowned 0->3->11",
        slow_fail.day1_to_day4_delta == 886
        and slow_fail.day4_to_day7_delta == 40_310
        and slow_fail.rate_period1_per_day == 295.33
        and slow_fail.rate_period2_per_day == 13436.67
        and slow_fail.acceleration_factor == 45.5
        and slow_fail.link_downed_delta_total == 11
        and slow_fail.alert_triggered is True,
    )

    # 12. SCL Ch. 5 `mlxlink -d mlx5_1 -c -m` healthy EDR 4x 850nm VCSEL module audit
    mlx_healthy = evaluate_mlxlink_module_health(
        state="Active",
        physical_state="LinkUp",
        speed="IB-EDR",
        width_lanes=4,
        expected_lanes=4,
        raw_ber=15e-255,
        effective_ber=15e-255,
        lane_errors=(0, 0, 0, 0),
        temperature_c=SCL5_MLXLINK_TEMP_C,
        voltage_mv=SCL5_MLXLINK_VOLTAGE_MV,
        bias_ma_per_lane=(6.750, 6.750, 6.750, 6.750),
        rx_power_dbm_per_lane=(0.0, 0.0, 0.0, 0.0),
        tx_power_dbm_per_lane=(0.0, 0.0, 0.0, 0.0),
    )
    check(
        "SCL Ch 5 mlxlink -d mlx5_1 -c -m healthy baseline: IB-EDR 4x, mask 0x3f, 12824.8 min, BER 15E-255, 850nm VCSEL 10m 2.5W, 38C [-10..80], 3255.2mV [3100..3500], 6.750mA [5.492..8.5], Rx/Tx 0 dBm -> HEALTHY",
        SCL5_MLXLINK_SPEED_MASK == 0x0000003F
        and SCL5_MLXLINK_UPTIME_MIN == 12824.8
        and SCL5_MLXLINK_WAVELENGTH_NM == 850
        and SCL5_MLXLINK_DISTANCE_M == 10
        and SCL5_MLXLINK_MAX_POWER_W == 2.5
        and SCL5_MLXLINK_BIAS_MA == 6.750
        and mlx_healthy.overall_status == "HEALTHY"
        and mlx_healthy.ber_healthy is True,
    )

    # 13. `mlxlink` degraded optical power (`Rx Power = -16.8 dBm` on lane 2 below `-14..6 dBm` budget)
    mlx_bad_optic = evaluate_mlxlink_module_health(
        state="Active",
        physical_state="LinkUp",
        speed="IB-NDR",
        width_lanes=4,
        expected_lanes=4,
        raw_ber=2e-5,
        effective_ber=1e-13,
        lane_errors=(0, 0, 18420, 0),
        temperature_c=52.0,
        voltage_mv=3280.0,
        bias_ma_per_lane=(7.1, 7.1, 7.2, 7.1),
        rx_power_dbm_per_lane=(-1.2, -1.4, -16.8, -1.3),
        tx_power_dbm_per_lane=(0.5, 0.5, 0.4, 0.5),
    )
    check(
        "mlxlink degraded lane 2 Rx optical power (-16.8 dBm < -14.0 dBm floor): rx_power_in_spec=False -> OPTICAL_POWER_OUT_OF_SPEC",
        mlx_bad_optic.rx_power_in_spec is False
        and mlx_bad_optic.overall_status == "OPTICAL_POWER_OUT_OF_SPEC",
    )

    # 14. `mlxlink` / `iblinkinfo` lane width downshift (`1x` negotiated vs `4x` expected -> V8 Ch. 10 Story)
    mlx_width_drop = evaluate_mlxlink_module_health(
        state="Active",
        physical_state="LinkUp",
        speed="IB-NDR",
        width_lanes=1,
        expected_lanes=4,
        raw_ber=1e-15,
        effective_ber=1e-15,
        lane_errors=(0, 0, 0, 0),
        temperature_c=44.0,
        voltage_mv=3300.0,
        bias_ma_per_lane=(6.8, 6.8, 6.8, 6.8),
        rx_power_dbm_per_lane=(-1.0, -1.0, -1.0, -1.0),
        tx_power_dbm_per_lane=(0.2, 0.2, 0.2, 0.2),
    )
    check(
        "V8 Ch 10 Story width degradation: Active port negotiated at 1x instead of 4x classified as LANE_WIDTH_DEGRADED",
        mlx_width_drop.overall_status == "LANE_WIDTH_DEGRADED",
    )

    # 15. SCL Ch. 5 `smpquery nodedesc 914` vs `saquery 914` consistency (`n51001 HCA-1`, `0x0012345600003740`)
    smp_sa_ok = compare_smpquery_and_saquery(
        lid=SCL5_QUERY_LID,
        smp_node_desc="n51001 HCA-1",
        smp_port_guid=0x0012345600003740,
        sa_node_desc="n51001 HCA-1",
        sa_port_guid=0x0012345600003740,
    )
    smp_sa_stale = compare_smpquery_and_saquery(
        lid=SCL5_QUERY_LID,
        smp_node_desc="n51001 HCA-1",
        smp_port_guid=0x0012345600003740,
        sa_node_desc="n50999 HCA-1",
        sa_port_guid=0x0012345600009999,
    )
    smp_sa_down = compare_smpquery_and_saquery(
        lid=SCL5_QUERY_LID,
        smp_node_desc="n51001 HCA-1",
        smp_port_guid=0x0012345600003740,
        sa_node_desc=None,
        sa_port_guid=None,
    )
    check(
        "SCL Ch 5 smpquery vs saquery on LID 914 (`n51001 HCA-1`, GUID 0x0012345600003740): detects consistent SA, stale SA record, and unreachable SM",
        SCL5_QUERY_LID == 914
        and smp_sa_ok.is_consistent is True
        and smp_sa_stale.diagnosis == "SM_SA_DATABASE_STALE_NEEDS_RESWEEP"
        and smp_sa_down.diagnosis == "SA_QUERY_FAILED_SM_UNREACHABLE_OR_WEDGED",
    )

    # 16. `ibdiagnet` multi-stage fabric audit summary (healthy vs failing PM/BER stage)
    ibd_clean = evaluate_ibdiagnet_stages(
        [
            ("Discovery", 0, 0),
            ("Duplicated GUIDs", 0, 0),
            ("Links Check", 0, 0),
            ("Subnet Manager", 0, 0),
            ("Port Counters", 1, 0),
            ("BER Test", 0, 0),
            ("Routing / LFT", 0, 0),
            ("SHARP Aggregation", 0, 0),
        ]
    )
    ibd_fail = evaluate_ibdiagnet_stages(
        [
            ("Discovery", 0, 0),
            ("Duplicated GUIDs", 0, 0),
            ("Links Check", 1, 2),
            ("Subnet Manager", 0, 0),
            ("Port Counters", 3, 4),
            ("BER Test", 0, 1),
        ]
    )
    check(
        "ibdiagnet multi-stage parser: clean 8-stage run passes (0 errors), degraded run pinpoints first failing stage ('Links Check') and tallies 7 errors",
        ibd_clean.fabric_healthy is True
        and ibd_clean.total_stages == 8
        and ibd_fail.fabric_healthy is False
        and ibd_fail.first_failing_stage == "Links Check"
        and ibd_fail.errors_count == 7,
    )

    # 17. V8 Ch. 10 Incident 10: Post-maintenance topology drift (`iblinkinfo` vs source of truth)
    expected_topo = {
        "n01:mlx5_0:p1": ("leaf01:p1", 400, 4),
        "n01:mlx5_1:p1": ("leaf02:p1", 400, 4),
        "n02:mlx5_0:p1": ("leaf01:p2", 400, 4),
        "n02:mlx5_1:p1": ("leaf02:p2", 400, 4),
    }
    drifted_topo = {
        "n01:mlx5_0:p1": ("leaf02:p1", 400, 4),  # swapped rail cable
        "n01:mlx5_1:p1": ("leaf01:p1", 400, 4),  # swapped rail cable
        "n02:mlx5_0:p1": ("leaf01:p2", 400, 1),  # degraded 1x width
        # n02:mlx5_1:p1 missing
    }
    drift_res = audit_topology_against_source_of_truth(expected_topo, drifted_topo)
    check(
        "Post-maintenance topology drift audit: detects 1 missing link, 2 swapped rail cables, and 1 width-downgraded (1x@400G) link",
        drift_res.matches_design is False
        and len(drift_res.missing_links) == 1
        and len(drift_res.swapped_cables) == 2
        and len(drift_res.width_downgraded_links) == 1,
    )

    # 18. UFM Enterprise HA & SM election (`sminfo` `0x0002c903004a1b20` priority 15 state 3 `SMINFO_MASTER`)
    ufm_ha_ok = evaluate_ufm_enterprise_ha(
        candidates=[
            ("ufm-appliance-01", V8_SM_MASTER_GUID, V8_SM_MASTER_PRIORITY, "sha256:9f86d08"),
            ("ufm-appliance-02", 0x08C0EB0300F1A2C3, 8, "sha256:9f86d08"),
        ],
        drbd_synced=True,
        virtual_ip_active=True,
        sharp_am_enabled=True,
        ufm_telemetry_running=True,
    )
    ufm_ha_drift = evaluate_ufm_enterprise_ha(
        candidates=[
            ("ufm-appliance-01", 0x08C0EB0300F1A2C3, 14, "sha256:9f86d08"),
            ("ufm-appliance-02", V8_SM_MASTER_GUID, 14, "sha256:different"),
        ],
        drbd_synced=True,
        virtual_ip_active=True,
        sharp_am_enabled=True,
        ufm_telemetry_running=True,
    )
    check(
        "UFM Enterprise HA & sminfo election: priority 15 master (GUID 0x0002c903004a1b20, activity 184,223, state 3, Trap 128) is HA ready; tie-breaker selects lowest GUID and flags config drift",
        V8_SM_ACTIVITY_COUNT == 184_223
        and V8_SM_MASTER_STATE == 3
        and V8_TRAP_LINK_STATE_CHANGE == 128
        and ufm_ha_ok.ha_ready is True
        and ufm_ha_ok.master_node == "ufm-appliance-01"
        and ufm_ha_drift.master_node == "ufm-appliance-02"
        and ufm_ha_drift.ha_ready is False
        and ufm_ha_drift.failure_reason == "OPENSM_OR_PKEY_CONFIG_DRIFT_ACROSS_HA_NODES",
    )

    # 19. DGX B200 SuperPOD UFM Appliance & Cabling rules (`superpod-b200-dc`: `458 kW`/SU, `31, 63, 95, 127` nodes, `248..1,016` GPUs)
    check(
        "superpod-b200-dc UFM Appliance & Cabling: 458 kW/SU, 1 UFM appliance displaces 1 node (31, 63, 95, 127 nodes; 248, 504, 760, 1,016 GPUs; 1,020 node + 1,024 ISL cables at 4 SUs; DAC <=5m/3m, AOC <=30m, 90% margin)",
        B200_POWER_PER_SU_KW == 458
        and B200_SU_SCALE_TABLE[1]["nodes"] == 31
        and B200_SU_SCALE_TABLE[1]["gpus"] == 248
        and B200_SU_SCALE_TABLE[2]["nodes"] == 63
        and B200_SU_SCALE_TABLE[3]["nodes"] == 95
        and B200_SU_SCALE_TABLE[4]["nodes"] == 127
        and B200_SU_SCALE_TABLE[4]["gpus"] == 1016
        and B200_SU_SCALE_TABLE[4]["node_cables"] == 1020
        and B200_SU_SCALE_TABLE[4]["isl_cables"] == 1024
        and B200_DAC_MAX_100G_M == 5
        and B200_DAC_MAX_400G_M == 3
        and B200_AOC_MAX_M == 30
        and B200_CABLE_SAFETY_MARGIN_PCT == 90,
    )

    # 20. DGX GB300 SuperPOD Quantum-X800 (`superpod-gb300-ra`: `144`-port `Q3400-RD` at `800G`, `2..16` SUs / `1,152..9,216` GPUs)
    check(
        "superpod-gb300-ra Quantum-X800 scaling: 144-port Q3400-RD at 800 Gbps scales across 2, 4, 8, 16 SUs (1,152, 2,304, 4,608, 9,216 GPUs; 16..128 leaves; 8..72 spines)",
        GB300_SWITCH_MODEL == "Q3400-RD"
        and GB300_PORT_RATE_GBPS == 800
        and GB300_SWITCH_RADIX == 144
        and GB300_SU_SCALE_TABLE[2] == {"gpus": 1152, "leaf_switches": 16, "spine_switches": 8}
        and GB300_SU_SCALE_TABLE[16] == {"gpus": 9216, "leaf_switches": 128, "spine_switches": 72},
    )

    # 21. BCM 11 (`bcm11-admin` §3.6.3 & §7.5): `ibnet` `10.149.0.0/16` & `Topograph` HTTPS port `49021` (`26` measurables)
    check(
        "BCM 11 (§3.6.3 & §7.5): ibnet 10.149.0.0/16, Topograph HTTPS port 49021, timeout 20s, 12 attempts, 15s wait, 26 Prometheus measurables",
        BCM_IBNET_CIDR == "10.149.0.0/16"
        and BCM_TOPOGRAPH_HTTPS_PORT == 49021
        and BCM_TOPOGRAPH_TIMEOUT_S == 20
        and BCM_TOPOGRAPH_ATTEMPTS == 12
        and BCM_TOPOGRAPH_WAIT_S == 15
        and BCM_TOPOGRAPH_MEASURABLES == 26,
    )

    # 22. V8 Ch. 10 Step 6 `ib_write_lat` percentile tail regression (`1.58 vs 1.55 us` typical, `2.90 vs 1.71 us` p99, `5.77 vs 1.98 us` p99.9)
    lat_audit = evaluate_ib_write_lat_percentiles(
        msg_bytes=2,
        iterations=1000,
        typical_us=1.58,
        baseline_typical_us=1.55,
        p99_us=2.90,
        baseline_p99_us=1.71,
        p999_us=5.77,
        baseline_p999_us=1.98,
    )
    check(
        "V8 Ch 10 Step 6 ib_write_lat percentile audit (2B, 1000 iters): typical 1.58 vs 1.55 us (1.02x, looks healthy), but p99 is 2.90 vs 1.71 us (1.70x) and p99.9 is 5.77 vs 1.98 us (2.91x -> tail_is_degraded)",
        lat_audit.typical_ratio == 1.02
        and lat_audit.p99_ratio == 1.70
        and lat_audit.p999_ratio == 2.91
        and lat_audit.average_looks_healthy is True
        and lat_audit.tail_is_degraded is True,
    )

    # 23. 7-Gate Bottom-Up Triage Gate 2: Physical fault (`V8` Ch. 10 Story — NCCL timeout caused by degraded width/cable)
    g2 = run_seven_gate_bottom_up_triage(
        inventory_matches_bom=True,
        phys_link_up=True,
        rate_and_width_match_design=False,
        physical_errors_stable=False,
        sm_master_healthy_and_port_active=True,
        route_and_pkey_valid=True,
        host_rdma_bw_and_tail_healthy=False,
        gpudirect_and_numa_local=False,
    )
    check(
        "7-Gate Triage Gate 2 (V8 Ch 10 Story): stops at GATE_2_PHYSICAL when width/errors fail, even if higher layers also report timeouts",
        g2.first_failing_gate == "GATE_2_PHYSICAL" and g2.stop_layer_number == 2,
    )

    # 24. 7-Gate Bottom-Up Triage Gate 3: Control plane fault (`LinkUp` + `Initializing` + `Base lid: 0`)
    g3 = run_seven_gate_bottom_up_triage(
        inventory_matches_bom=True,
        phys_link_up=True,
        rate_and_width_match_design=True,
        physical_errors_stable=True,
        sm_master_healthy_and_port_active=False,
        route_and_pkey_valid=False,
        host_rdma_bw_and_tail_healthy=False,
        gpudirect_and_numa_local=False,
    )
    check(
        "7-Gate Triage Gate 3 (V8 Ch 10 Incident 2): stops at GATE_3_SM_CONTROL when port is LinkUp but stuck in Initializing (Base lid: 0)",
        g3.first_failing_gate == "GATE_3_SM_CONTROL" and g3.stop_layer_number == 3,
    )

    # 25. 7-Gate Bottom-Up Triage Gate 4: Routing / P_Key mismatch (`0x8021` vs `0x8035`)
    g4 = run_seven_gate_bottom_up_triage(
        inventory_matches_bom=True,
        phys_link_up=True,
        rate_and_width_match_design=True,
        physical_errors_stable=True,
        sm_master_healthy_and_port_active=True,
        route_and_pkey_valid=False,
        host_rdma_bw_and_tail_healthy=False,
        gpudirect_and_numa_local=False,
    )
    check(
        "7-Gate Triage Gate 4 (V8 Ch 10 Incident 5): stops at GATE_4_ROUTING_PKEY when P_Key or LFT route is invalid",
        g4.first_failing_gate == "GATE_4_ROUTING_PKEY" and g4.stop_layer_number == 4,
    )

    # 26. 7-Gate Bottom-Up Triage Gate 5: Host-memory RDMA transport / congestion failure
    g5 = run_seven_gate_bottom_up_triage(
        inventory_matches_bom=True,
        phys_link_up=True,
        rate_and_width_match_design=True,
        physical_errors_stable=True,
        sm_master_healthy_and_port_active=True,
        route_and_pkey_valid=True,
        host_rdma_bw_and_tail_healthy=False,
        gpudirect_and_numa_local=True,
    )
    check(
        "7-Gate Triage Gate 5 (V8 Ch 10 Step 6): stops at GATE_5_HOST_RDMA when host-memory ib_write_bw/lat fails below GPUDirect",
        g5.first_failing_gate == "GATE_5_HOST_RDMA" and g5.stop_layer_number == 5,
    )

    # 27. 7-Gate Bottom-Up Triage Gate 6: GPUDirect / NUMA locality fault (`V8` Lab 04 — `NUMA node 1` vs `NUMA node 0`)
    g6 = run_seven_gate_bottom_up_triage(
        inventory_matches_bom=True,
        phys_link_up=True,
        rate_and_width_match_design=True,
        physical_errors_stable=True,
        sm_master_healthy_and_port_active=True,
        route_and_pkey_valid=True,
        host_rdma_bw_and_tail_healthy=True,
        gpudirect_and_numa_local=False,
    )
    check(
        "7-Gate Triage Gate 6 (V8 Lab 04 & Ch 10 Incident 6): stops at GATE_6_GPUDIRECT_NUMA when host RDMA passes but GPU/NUMA locality is remote",
        g6.first_failing_gate == "GATE_6_GPUDIRECT_NUMA" and g6.stop_layer_number == 6,
    )

    # 28. 7-Gate Bottom-Up Triage Gate 7: Application / collective layer (all 6 fabric/host gates clean)
    g7 = run_seven_gate_bottom_up_triage(
        inventory_matches_bom=True,
        phys_link_up=True,
        rate_and_width_match_design=True,
        physical_errors_stable=True,
        sm_master_healthy_and_port_active=True,
        route_and_pkey_valid=True,
        host_rdma_bw_and_tail_healthy=True,
        gpudirect_and_numa_local=True,
    )
    check(
        "7-Gate Triage Gate 7 (V8 Ch 10 Step 7): reaches GATE_7_APPLICATION only after Gates 1-6 match baseline",
        g7.first_failing_gate == "GATE_7_APPLICATION" and g7.stop_layer_number == 7,
    )

    print(f"\nSummary: {passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
