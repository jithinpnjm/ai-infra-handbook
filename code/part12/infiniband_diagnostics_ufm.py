#!/usr/bin/env python3
"""Deterministic InfiniBand diagnostics, UFM Enterprise operations, and telemetry models for Chapter 12.9.

Covers:
  - Complete OFED / rdma-core / MFT diagnostic utility taxonomy (`ibstat`, `ibstatus`,
    `ibdev2netdev`, `ibhosts`, `ibswitches`, `ibnodes`, `ibnetdiscover`, `iblinkinfo`,
    `ibaddr`, `ibping`, `ibsysstat`, `ibtracert`, `ibroute`, `perfquery`, `ibqueryerrors`,
    `ibportstate`, `smpquery`, `saquery`, `ibdiagnet`, `mlxlink`, `mst`, `mlxconfig`, `ofed_info`)
  - `perfquery` counter classification and rate-of-change delta triage (`SymbolErrorCounter`,
    `LinkErrorRecoveryCounter`, `LinkDownedCounter`, `PortRcvErrors`, `PortXmitDiscards`,
    `PortXmitWait`, and `PortXmitData` / `PortRcvData` 4-octet words)
  - `mlxlink` physical BER (`Raw Physical BER`, `Effective Physical BER`), per-lane error counts,
    optical transceiver DDM budget (`Temperature [C]`, `Voltage [mV]`, `Bias Current [mA]`,
    `Rx Power Current [dBm]`, `Tx Power Current [dBm]`), and speed bitmask decoding
  - `ibdiagnet` multi-stage fabric audit parser and expected-vs-discovered cable topology validator
  - `ibportstate` safe port isolation (`disable` / `enable` / `reset`) and `smpquery` vs `saquery`
    Subnet Manager database synchronization audit (`LID 914` on `n51001 HCA-1`)
  - NVIDIA Unified Fabric Manager (`UFM` Enterprise, UFM Telemetry, UFM Cyber-AI) High Availability,
    SM priority handover (`priority 15` master vs `priority 8`/`14` standby), `P_Key` partition API,
    SHARP Aggregation Manager (`AM`), and DGX B200 / GB300 SuperPOD UFM appliance scaling
  - 7-gate bottom-up InfiniBand incident triage and `ib_write_lat` / `ib_write_bw` baseline verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# Protocol, Hardware, and UFM Operational Constants
# ---------------------------------------------------------------------------

# SCL Ch. 5: InfiniBand addressing & subnet limits
IB_SUBNET_MAX_UNICAST_LIDS: int = 49_151  # 2^15 + 2^14 - 1 (0x0001..0xBFFF)
IB_LID_RESERVED: int = 0x0000
IB_LID_UNICAST_MAX: int = 0xBFFF
IB_LID_MULTICAST_MIN: int = 0xC000
IB_LID_MULTICAST_MAX: int = 0xFFFE
IB_LID_PERMISSIVE: int = 0xFFFF
IB_DEFAULT_GID_PREFIX: int = 0xFE80
IB_SITE_LOCAL_GID_PREFIX: int = 0xFEC0
IB_MULTICAST_GID_HIGH_BYTE: int = 0xFF
IB_SMP_VL: int = 15
IB_DATA_VL_COUNT: int = 15
IB_TOTAL_VL_COUNT: int = 16
IB_CREDIT_UNIT_BYTES: int = 64
IB_PORT_DATA_COUNTER_OCTETS: int = 4  # PortXmitData / PortRcvData count 4-byte (32-bit) words
IPOIB_HWADDR_BYTES: int = 20  # 1B flags + 3B QPN + 16B GID (vs 6B Ethernet MAC)
IPOIB_DATAGRAM_MTU_BYTES: int = 4096
IPOIB_CONNECTED_MTU_BYTES: int = 65536

# SCL Ch. 5: Table 5-1 InfiniBand generation speeds (4x and 12x effective Gbps)
IB_GEN_TABLE_4X_12X_GBPS: Dict[str, Tuple[float, float, float, str]] = {
    # gen: (raw_lane_gbps, eff_4x_gbps, eff_12x_gbps, coding)
    "SDR": (2.5, 8.0, 24.0, "8b/10b"),
    "DDR": (5.0, 16.0, 48.0, "8b/10b"),
    "QDR": (10.0, 32.0, 96.0, "8b/10b"),
    "FDR": (14.0625, 54.4, 163.2, "64b/66b"),
    "EDR": (25.78125, 100.0, 300.0, "64b/66b"),
    "HDR": (53.125, 200.0, 600.0, "64b/66b"),
    "NDR": (106.25, 400.0, 1200.0, "256b/257b"),
    "XDR": (200.0, 800.0, 2400.0, "256b/257b"),
    "GDR": (400.0, 1600.0, 4800.0, "256b/257b"),
}

# SCL Ch. 5 `ibstat` / `ibstatus` / `mlxlink` / `smpquery` / `saquery` reference constants
SCL5_MT4113_FW: str = "10.12.1100"
SCL5_PORT1_LID_DEC: int = 913
SCL5_PORT1_LID_HEX: int = 0x391
SCL5_PORT1_SM_LID_DEC: int = 43
SCL5_PORT1_SM_LID_HEX: int = 0x2B
SCL5_PORT2_LID_DEC: int = 1361
SCL5_PORT2_LID_HEX: int = 0x551
SCL5_PORT2_SM_LID_DEC: int = 698
SCL5_PORT2_SM_LID_HEX: int = 0x2BA
SCL5_QUERY_LID: int = 914
SCL5_MLXLINK_SPEED_MASK: int = 0x0000003F  # EDR,FDR,FDR10,QDR,DDR,SDR
SCL5_MLXLINK_UPTIME_MIN: float = 12824.8
SCL5_MLXLINK_WAVELENGTH_NM: int = 850
SCL5_MLXLINK_DISTANCE_M: int = 10
SCL5_MLXLINK_MAX_POWER_W: float = 2.5
SCL5_MLXLINK_TEMP_C: float = 38.0
SCL5_MLXLINK_TEMP_RANGE_C: Tuple[float, float] = (-10.0, 80.0)
SCL5_MLXLINK_VOLTAGE_MV: float = 3255.2
SCL5_MLXLINK_VOLTAGE_RANGE_MV: Tuple[float, float] = (3100.0, 3500.0)
SCL5_MLXLINK_BIAS_MA: float = 6.750
SCL5_MLXLINK_BIAS_RANGE_MA: Tuple[float, float] = (5.492, 8.5)
SCL5_MLXLINK_RX_DBM_RANGE: Tuple[float, float] = (-14.0, 6.0)
SCL5_MLXLINK_TX_DBM_RANGE: Tuple[float, float] = (-12.0, 6.0)

# V8 Lab 01 & Ch. 5/7/9/10 constants
V8_HCA_PART_ID: int = 4129  # MT4129 ConnectX-7
V8_HCA_FW_VER: str = "28.39.2048"
V8_HCA_VENDOR_ID: int = 0x02C9
V8_HCA_NODE_GUID: int = 0x08C0EB0300F1A2C3
V8_HCA_MAX_QP: int = 262_144
V8_HCA_MAX_QP_WR: int = 32_768
V8_HCA_MAX_SGE: int = 30
V8_HCA_BASE_LID: int = 12
V8_HCA_SM_LID: int = 1
V8_HCA_CAP_MASK: int = 0x2651E848
V8_SM_MASTER_GUID: int = 0x0002C903004A1B20
V8_SM_ACTIVITY_COUNT: int = 184_223
V8_SM_MASTER_PRIORITY: int = 15
V8_SM_MASTER_STATE: int = 3  # SMINFO_MASTER
V8_TRAP_LINK_STATE_CHANGE: int = 128

# DGX B200 (`superpod-b200-dc`) & DGX GB300 (`superpod-gb300-ra`) UFM & fabric scaling
B200_POWER_PER_SU_KW: int = 458
B200_UFM_APPLIANCES_DISPLACED_NODES: int = 1  # 32 -> 31 compute nodes in SU1 when UFM appliance installed
B200_SU_SCALE_TABLE: Dict[int, Dict[str, int]] = {
    1: {"nodes": 31, "gpus": 248, "leaf_switches": 8, "spine_switches": 4, "node_cables": 252, "isl_cables": 256},
    2: {"nodes": 63, "gpus": 504, "leaf_switches": 16, "spine_switches": 8, "node_cables": 508, "isl_cables": 512},
    3: {"nodes": 95, "gpus": 760, "leaf_switches": 24, "spine_switches": 12, "node_cables": 764, "isl_cables": 768},
    4: {"nodes": 127, "gpus": 1016, "leaf_switches": 32, "spine_switches": 16, "node_cables": 1020, "isl_cables": 1024},
}
B200_DAC_MAX_100G_M: int = 5
B200_DAC_MAX_400G_M: int = 3
B200_AOC_MAX_M: int = 30
B200_CABLE_SAFETY_MARGIN_PCT: int = 90

GB300_SWITCH_MODEL: str = "Q3400-RD"
GB300_PORT_RATE_GBPS: int = 800
GB300_SWITCH_RADIX: int = 144
GB300_SU_SCALE_TABLE: Dict[int, Dict[str, int]] = {
    2: {"gpus": 1152, "leaf_switches": 16, "spine_switches": 8},
    4: {"gpus": 2304, "leaf_switches": 32, "spine_switches": 18},
    8: {"gpus": 4608, "leaf_switches": 64, "spine_switches": 36},
    16: {"gpus": 9216, "leaf_switches": 128, "spine_switches": 72},
}

# BCM 11 (`bcm11-admin` §3.6.3 & §7.5) constants
BCM_IBNET_CIDR: str = "10.149.0.0/16"
BCM_TOPOGRAPH_HTTPS_PORT: int = 49021
BCM_TOPOGRAPH_TIMEOUT_S: int = 20
BCM_TOPOGRAPH_ATTEMPTS: int = 12
BCM_TOPOGRAPH_WAIT_S: int = 15
BCM_TOPOGRAPH_MEASURABLES: int = 26


# ---------------------------------------------------------------------------
# 1. OFED / rdma-core / MFT Utility Taxonomy (`SCL` Ch. 5 + `V8` Labs 01-04)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class IBUtilitySpec:
    name: str
    plane: str  # "local_host", "subnet_discovery", "path_routing", "counters_phy", "control_ufm"
    mutates_state: bool
    primary_purpose: str


IB_DIAGNOSTIC_UTILITIES: Dict[str, IBUtilitySpec] = {
    "ibstat": IBUtilitySpec("ibstat", "local_host", False, "Show local HCA device/port state, physical state, decimal Base LID, SM LID, rate, and GUIDs"),
    "ibstatus": IBUtilitySpec("ibstatus", "local_host", False, "Shell script wrapper showing local port state, default GID, hex Base LID/SM LID, and rate with width/mode"),
    "ibdev2netdev": IBUtilitySpec("ibdev2netdev", "local_host", False, "Map RDMA HCA devices/ports (mlx5_0) to Linux network interfaces (ib0, eth0)"),
    "ibv_devices": IBUtilitySpec("ibv_devices", "local_host", False, "List local RDMA verbs devices visible to userspace"),
    "ibv_devinfo": IBUtilitySpec("ibv_devinfo", "local_host", False, "Inspect HCA firmware, vendor/part ID, max_qp, max_qp_wr, max_sge, active_mtu, and port states"),
    "show_gids": IBUtilitySpec("show_gids", "local_host", False, "Display per-port GID table indices, IPv4-mapped GIDs, and RoCE/IB versions"),
    "ofed_info": IBUtilitySpec("ofed_info", "local_host", False, "Report installed MLNX_OFED / DOCA-OFED version and package components"),
    "ibhosts": IBUtilitySpec("ibhosts", "subnet_discovery", False, "List all Channel Adapter (host) nodes discovered in the InfiniBand subnet"),
    "ibswitches": IBUtilitySpec("ibswitches", "subnet_discovery", False, "List all InfiniBand switch nodes discovered in the subnet with GUIDs and LIDs"),
    "ibnodes": IBUtilitySpec("ibnodes", "subnet_discovery", False, "List all InfiniBand nodes (both hosts and switches) in the subnet"),
    "ibnetdiscover": IBUtilitySpec("ibnetdiscover", "subnet_discovery", False, "Perform full subnet topology crawl of switches, HCAs, routers, and port-to-port links"),
    "iblinkinfo": IBUtilitySpec("iblinkinfo", "subnet_discovery", False, "Report link status, negotiated speed, lane width (4x/1x), and peer port for every switch port"),
    "ibaddr": IBUtilitySpec("ibaddr", "path_routing", False, "Resolve GID and LID Range (Base LID..Max LID) for a local or specified InfiniBand port"),
    "ibping": IBUtilitySpec("ibping", "path_routing", False, "Verify IB mad-layer reachability between client and server (`ibping -S` on target, `ibping <lid>`)"),
    "ibsysstat": IBUtilitySpec("ibsysstat", "path_routing", False, "Query basic remote host system status (hostname, CPU, memory) over InfiniBand MADs"),
    "ibtracert": IBUtilitySpec("ibtracert", "path_routing", False, "Trace the exact switch-by-switch unicast or multicast hop path between two LIDs/GIDs"),
    "ibroute": IBUtilitySpec("ibroute", "path_routing", False, "Dump a switch's Linear Forwarding Table (LFT) or Multicast Forwarding Table (MFT)"),
    "sminfo": IBUtilitySpec("sminfo", "control_ufm", False, "Query Subnet Manager master LID, GUID, activity count, priority (0..15), and state (0..3)"),
    "smpquery": IBUtilitySpec("smpquery", "control_ufm", False, "Send direct VL15 Subnet Management Packets (SMP) to a target node (`nodedesc`, `portinfo`, `pkeys`)"),
    "saquery": IBUtilitySpec("saquery", "control_ufm", False, "Query the Subnet Manager's Subnet Administration (SA) database (`NodeRecord`, `PathRecord`)"),
    "perfquery": IBUtilitySpec("perfquery", "counters_phy", False, "Read PMA hardware error, wait, and data counters from any LID/port (`-x` extended, `-R` resets)"),
    "ibqueryerrors": IBUtilitySpec("ibqueryerrors", "counters_phy", False, "Sweep switches across the subnet and print ports with non-zero error/wait counters"),
    "ibdiagnet": IBUtilitySpec("ibdiagnet", "counters_phy", False, "Comprehensive fabric-wide diagnostic suite checking dup GUIDs, SM, links, BER, LFT loops, and SHARP"),
    "mlxlink": IBUtilitySpec("mlxlink", "counters_phy", False, "Read low-level SERDES BER (`-c`), optical transceiver DDM (`-m`), and JSON (`--json`) on NVIDIA/Mellanox ports"),
    "mst": IBUtilitySpec("mst", "counters_phy", False, "Mellanox Software Tools service managing `/dev/mst/*` PCI configuration devices (`mst start`, `mst status`)"),
    "mlxconfig": IBUtilitySpec("mlxconfig", "control_ufm", True, "Query or modify non-volatile HCA firmware configuration (`LINK_TYPE_P1`, `SRIOV_EN`, `NUM_OF_VFS`)"),
    "ibportstate": IBUtilitySpec("ibportstate", "control_ufm", True, "Query or modify logical/physical port state (`disable`, `enable`, `reset`) or link speed/width"),
}


# ---------------------------------------------------------------------------
# 2. `perfquery` Counter Classification & Delta Triage
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PerfQueryCounterAudit:
    lid: int
    port: int
    window_sec: float
    symbol_error_delta: int
    link_recovery_delta: int
    link_downed_delta: int
    port_rcv_errors_delta: int
    port_xmit_discards_delta: int
    port_xmit_wait_delta: int
    xmit_bytes_delta: int
    rcv_bytes_delta: int
    achieved_tx_gbps: float
    classification: str  # "HEALTHY", "HISTORICAL_SCAR_TISSUE", "PURE_CONGESTION", "PHYSICAL_DEGRADATION", "FLAPPING_LINK_FAULT", "ROUTING_OR_POLICY_DISCARD"
    recommended_action: str


def audit_perfquery_counter_deltas(
    lid: int,
    port: int,
    window_sec: float,
    before: Dict[str, int],
    after: Dict[str, int],
) -> PerfQueryCounterAudit:
    """Compute counter deltas between two read-only `perfquery` snapshots and classify root cause.

    Note: `PortXmitData` and `PortRcvData` increment in 4-octet (32-bit) words per IBTA spec.
    """
    if window_sec <= 0:
        raise ValueError("window_sec must be positive")

    sym_d = after.get("SymbolErrorCounter", 0) - before.get("SymbolErrorCounter", 0)
    rec_d = after.get("LinkErrorRecoveryCounter", 0) - before.get("LinkErrorRecoveryCounter", 0)
    down_d = after.get("LinkDownedCounter", 0) - before.get("LinkDownedCounter", 0)
    rcv_err_d = after.get("PortRcvErrors", 0) - before.get("PortRcvErrors", 0)
    disc_d = after.get("PortXmitDiscards", 0) - before.get("PortXmitDiscards", 0)
    wait_d = after.get("PortXmitWait", 0) - before.get("PortXmitWait", 0)

    xmit_words_d = after.get("PortXmitData", 0) - before.get("PortXmitData", 0)
    rcv_words_d = after.get("PortRcvData", 0) - before.get("PortRcvData", 0)
    xmit_bytes = xmit_words_d * IB_PORT_DATA_COUNTER_OCTETS
    rcv_bytes = rcv_words_d * IB_PORT_DATA_COUNTER_OCTETS
    tx_gbps = round((xmit_bytes * 8.0) / (window_sec * 1e9), 2)

    if down_d > 0:
        classification = "FLAPPING_LINK_FAULT"
        action = "Isolate port with `ibportstate <lid> <port> disable`, inspect `mlxlink -c -m`, and replace cable/optic."
    elif sym_d > 0 or rec_d > 0 or rcv_err_d > 0:
        classification = "PHYSICAL_DEGRADATION"
        action = "Inspect `mlxlink -c -m` pre-FEC BER and Rx/Tx dBm; clean or replace degraded transceiver/fiber before link drops."
    elif disc_d > 0:
        classification = "ROUTING_OR_POLICY_DISCARD"
        action = "Check switch LFT (`ibroute`), P_Key table (`smpquery pkeys`), MTU, or HOQ lifetime drop policy."
    elif wait_d >= 10_000:
        classification = "PURE_CONGESTION"
        action = "Physical link is clean; trace downstream CBFC congestion tree (`PortXmitWait` gradient), verify AR/CC, or adjust placement."
    elif (
        after.get("SymbolErrorCounter", 0) > 0
        or after.get("LinkDownedCounter", 0) > 0
        or after.get("PortRcvErrors", 0) > 0
    ) and sym_d == 0 and down_d == 0 and rcv_err_d == 0:
        classification = "HISTORICAL_SCAR_TISSUE"
        action = "Delta is 0 over active traffic window; record historical count and do NOT replace hardware."
    else:
        classification = "HEALTHY"
        action = "Port counters are clean and within operational baseline."

    return PerfQueryCounterAudit(
        lid=lid,
        port=port,
        window_sec=window_sec,
        symbol_error_delta=sym_d,
        link_recovery_delta=rec_d,
        link_downed_delta=down_d,
        port_rcv_errors_delta=rcv_err_d,
        port_xmit_discards_delta=disc_d,
        port_xmit_wait_delta=wait_d,
        xmit_bytes_delta=xmit_bytes,
        rcv_bytes_delta=rcv_bytes,
        achieved_tx_gbps=tx_gbps,
        classification=classification,
        recommended_action=action,
    )


@dataclass(frozen=True)
class MultiDayErrorAccelerationAudit:
    day1_to_day4_delta: int
    day4_to_day7_delta: int
    rate_period1_per_day: float
    rate_period2_per_day: float
    acceleration_factor: float
    link_downed_delta_total: int
    alert_triggered: bool


def evaluate_error_rate_acceleration(
    day1_errors: int,
    day4_errors: int,
    day7_errors: int,
    day1_downed: int,
    day4_downed: int,
    day7_downed: int,
    days_per_window: float = 3.0,
) -> MultiDayErrorAccelerationAudit:
    """Evaluate V8 Ch. 9 'The Fabric Failed Slowly' multi-day counter acceleration."""
    d14 = day4_errors - day1_errors
    d47 = day7_errors - day4_errors
    r1 = round(d14 / days_per_window, 2)
    r2 = round(d47 / days_per_window, 2)
    accel = round((d47 / days_per_window) / (d14 / days_per_window), 1) if d14 > 0 else 0.0
    down_tot = day7_downed - day1_downed
    return MultiDayErrorAccelerationAudit(
        day1_to_day4_delta=d14,
        day4_to_day7_delta=d47,
        rate_period1_per_day=r1,
        rate_period2_per_day=r2,
        acceleration_factor=accel,
        link_downed_delta_total=down_tot,
        alert_triggered=(accel >= 5.0 or down_tot > 0),
    )


# ---------------------------------------------------------------------------
# 3. `mlxlink` Transceiver DDM & BER Optical Budget Evaluator (`SCL` Ch. 5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MlxLinkOpticalAudit:
    state: str
    physical_state: str
    speed: str
    width_lanes: int
    raw_ber: float
    effective_ber: float
    lane_errors: Tuple[int, ...]
    temperature_c: float
    voltage_mv: float
    bias_ma_per_lane: Tuple[float, ...]
    rx_power_dbm_per_lane: Tuple[float, ...]
    tx_power_dbm_per_lane: Tuple[float, ...]
    temp_in_spec: bool
    voltage_in_spec: bool
    bias_in_spec: bool
    rx_power_in_spec: bool
    tx_power_in_spec: bool
    ber_healthy: bool
    overall_status: str  # "HEALTHY", "LANE_WIDTH_DEGRADED", "OPTICAL_POWER_OUT_OF_SPEC", "HIGH_PRE_FEC_BER", "THERMAL_OR_VOLTAGE_FAULT"


def evaluate_mlxlink_module_health(
    state: str,
    physical_state: str,
    speed: str,
    width_lanes: int,
    expected_lanes: int,
    raw_ber: float,
    effective_ber: float,
    lane_errors: Sequence[int],
    temperature_c: float,
    voltage_mv: float,
    bias_ma_per_lane: Sequence[float],
    rx_power_dbm_per_lane: Sequence[float],
    tx_power_dbm_per_lane: Sequence[float],
    temp_range_c: Tuple[float, float] = SCL5_MLXLINK_TEMP_RANGE_C,
    voltage_range_mv: Tuple[float, float] = SCL5_MLXLINK_VOLTAGE_RANGE_MV,
    bias_range_ma: Tuple[float, float] = SCL5_MLXLINK_BIAS_RANGE_MA,
    rx_dbm_range: Tuple[float, float] = SCL5_MLXLINK_RX_DBM_RANGE,
    tx_dbm_range: Tuple[float, float] = SCL5_MLXLINK_TX_DBM_RANGE,
    max_raw_ber_threshold: float = 1e-6,
    max_eff_ber_threshold: float = 1e-12,
) -> MlxLinkOpticalAudit:
    """Evaluate `mlxlink -d <dev> -c -m` physical BER and optical DDM telemetry."""
    temp_ok = temp_range_c[0] <= temperature_c <= temp_range_c[1]
    volt_ok = voltage_range_mv[0] <= voltage_mv <= voltage_range_mv[1]
    bias_ok = all(bias_range_ma[0] <= b <= bias_range_ma[1] for b in bias_ma_per_lane)
    rx_ok = all(rx_dbm_range[0] <= p <= rx_dbm_range[1] for p in rx_power_dbm_per_lane)
    tx_ok = all(tx_dbm_range[0] <= p <= tx_dbm_range[1] for p in tx_power_dbm_per_lane)
    ber_ok = (raw_ber <= max_raw_ber_threshold) and (effective_ber <= max_eff_ber_threshold)

    if width_lanes < expected_lanes:
        status = "LANE_WIDTH_DEGRADED"
    elif not (rx_ok and tx_ok and bias_ok):
        status = "OPTICAL_POWER_OUT_OF_SPEC"
    elif not ber_ok:
        status = "HIGH_PRE_FEC_BER"
    elif not (temp_ok and volt_ok):
        status = "THERMAL_OR_VOLTAGE_FAULT"
    else:
        status = "HEALTHY"

    return MlxLinkOpticalAudit(
        state=state,
        physical_state=physical_state,
        speed=speed,
        width_lanes=width_lanes,
        raw_ber=raw_ber,
        effective_ber=effective_ber,
        lane_errors=tuple(lane_errors),
        temperature_c=temperature_c,
        voltage_mv=voltage_mv,
        bias_ma_per_lane=tuple(bias_ma_per_lane),
        rx_power_dbm_per_lane=tuple(rx_power_dbm_per_lane),
        tx_power_dbm_per_lane=tuple(tx_power_dbm_per_lane),
        temp_in_spec=temp_ok,
        voltage_in_spec=volt_ok,
        bias_in_spec=bias_ok,
        rx_power_in_spec=rx_ok,
        tx_power_in_spec=tx_ok,
        ber_healthy=ber_ok,
        overall_status=status,
    )


# ---------------------------------------------------------------------------
# 4. `smpquery` vs `saquery` Control-Plane Consistency & `ibportstate` Rules
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class SmpVsSaConsistencyAudit:
    lid: int
    smp_node_desc: str
    sa_node_desc: str | None
    smp_port_guid: int
    sa_port_guid: int | None
    is_consistent: bool
    diagnosis: str


def compare_smpquery_and_saquery(
    lid: int,
    smp_node_desc: str,
    smp_port_guid: int,
    sa_node_desc: str | None,
    sa_port_guid: int | None,
) -> SmpVsSaConsistencyAudit:
    """Compare live hardware `smpquery` (VL15 SMP) against SM cached `saquery` (`SCL` Ch. 5)."""
    if sa_node_desc is None or sa_port_guid is None:
        return SmpVsSaConsistencyAudit(
            lid=lid,
            smp_node_desc=smp_node_desc,
            sa_node_desc=sa_node_desc,
            smp_port_guid=smp_port_guid,
            sa_port_guid=sa_port_guid,
            is_consistent=False,
            diagnosis="SA_QUERY_FAILED_SM_UNREACHABLE_OR_WEDGED",
        )
    if smp_node_desc != sa_node_desc or smp_port_guid != sa_port_guid:
        return SmpVsSaConsistencyAudit(
            lid=lid,
            smp_node_desc=smp_node_desc,
            sa_node_desc=sa_node_desc,
            smp_port_guid=smp_port_guid,
            sa_port_guid=sa_port_guid,
            is_consistent=False,
            diagnosis="SM_SA_DATABASE_STALE_NEEDS_RESWEEP",
        )
    return SmpVsSaConsistencyAudit(
        lid=lid,
        smp_node_desc=smp_node_desc,
        sa_node_desc=sa_node_desc,
        smp_port_guid=smp_port_guid,
        sa_port_guid=sa_port_guid,
        is_consistent=True,
        diagnosis="CONSISTENT_NODE_AND_SA_RECORD",
    )


@dataclass(frozen=True)
class IbdiagnetStageSummary:
    total_stages: int
    failed_stages: Tuple[str, ...]
    warnings_count: int
    errors_count: int
    fabric_healthy: bool
    first_failing_stage: str | None


def evaluate_ibdiagnet_stages(
    stage_results: Sequence[Tuple[str, int, int]],
) -> IbdiagnetStageSummary:
    """Summarize an `ibdiagnet` multi-stage run (`(stage_name, warnings, errors)`)."""
    failed: List[str] = []
    tot_w = 0
    tot_e = 0
    for stage, w, e in stage_results:
        tot_w += w
        tot_e += e
        if e > 0:
            failed.append(stage)
    return IbdiagnetStageSummary(
        total_stages=len(stage_results),
        failed_stages=tuple(failed),
        warnings_count=tot_w,
        errors_count=tot_e,
        fabric_healthy=(tot_e == 0),
        first_failing_stage=failed[0] if failed else None,
    )


@dataclass(frozen=True)
class TopologyDriftAudit:
    expected_links: int
    discovered_links: int
    missing_links: Tuple[str, ...]
    swapped_cables: Tuple[str, ...]
    width_downgraded_links: Tuple[str, ...]
    matches_design: bool


def audit_topology_against_source_of_truth(
    expected: Dict[str, Tuple[str, int, int]],
    discovered: Dict[str, Tuple[str, int, int]],
) -> TopologyDriftAudit:
    """Compare discovered `iblinkinfo`/`ibnetdiscover` links `{src_port: (peer_port, speed_gbps, width_x)}` against source of truth."""
    missing: List[str] = []
    swapped: List[str] = []
    degraded: List[str] = []

    for src_port, (exp_peer, exp_speed, exp_width) in expected.items():
        if src_port not in discovered:
            missing.append(src_port)
            continue
        disc_peer, disc_speed, disc_width = discovered[src_port]
        if disc_peer != exp_peer:
            swapped.append(f"{src_port}: expected {exp_peer}, found {disc_peer}")
        if disc_speed < exp_speed or disc_width < exp_width:
            degraded.append(
                f"{src_port}: expected {exp_width}x@{exp_speed}G, found {disc_width}x@{disc_speed}G"
            )

    return TopologyDriftAudit(
        expected_links=len(expected),
        discovered_links=len(discovered),
        missing_links=tuple(missing),
        swapped_cables=tuple(swapped),
        width_downgraded_links=tuple(degraded),
        matches_design=(not missing and not swapped and not degraded),
    )


# ---------------------------------------------------------------------------
# 5. UFM Enterprise HA, SM Handover, and P_Key / SHARP Operations
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UFMHighAvailabilityAudit:
    master_node: str
    master_guid: int
    master_priority: int
    standby_nodes: Tuple[str, ...]
    drbd_Or_shared_state_synced: bool
    virtual_ip_active: bool
    config_checksum_match: bool
    sharp_am_enabled: bool
    ufm_telemetry_running: bool
    ha_ready: bool
    failure_reason: str | None


def evaluate_ufm_enterprise_ha(
    candidates: Sequence[Tuple[str, int, int, str]],  # (node_name, port_guid, priority, config_hash)
    drbd_synced: bool,
    virtual_ip_active: bool,
    sharp_am_enabled: bool,
    ufm_telemetry_running: bool,
) -> UFMHighAvailabilityAudit:
    """Evaluate UFM Enterprise HA appliance cluster state and OpenSM election (`priority 0..15`, lowest GUID tie-breaker)."""
    if len(candidates) < 2:
        raise ValueError("UFM HA requires at least 2 candidate nodes")

    # Sort by highest priority first, then lowest GUID tie-breaker
    ordered = sorted(candidates, key=lambda item: (-item[2], item[1]))
    master_name, master_guid, master_prio, master_hash = ordered[0]
    standbys = tuple(item[0] for item in ordered[1:])
    hashes_match = all(item[3] == master_hash for item in candidates)

    reason: str | None = None
    if not drbd_synced:
        reason = "DRBD_STATE_OUT_OF_SYNC"
    elif not virtual_ip_active:
        reason = "VIRTUAL_IP_INACTIVE"
    elif not hashes_match:
        reason = "OPENSM_OR_PKEY_CONFIG_DRIFT_ACROSS_HA_NODES"
    elif not ufm_telemetry_running:
        reason = "UFM_TELEMETRY_COLLECTOR_DOWN"

    return UFMHighAvailabilityAudit(
        master_node=master_name,
        master_guid=master_guid,
        master_priority=master_prio,
        standby_nodes=standbys,
        drbd_Or_shared_state_synced=drbd_synced,
        virtual_ip_active=virtual_ip_active,
        config_checksum_match=hashes_match,
        sharp_am_enabled=sharp_am_enabled,
        ufm_telemetry_running=ufm_telemetry_running,
        ha_ready=(reason is None),
        failure_reason=reason,
    )


# ---------------------------------------------------------------------------
# 6. 7-Gate Bottom-Up Troubleshooting & Latency Percentile Validator (`V8` Ch. 10 & Labs 01-04)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class LatencyPercentileAudit:
    msg_bytes: int
    iterations: int
    typical_us: float
    baseline_typical_us: float
    p99_us: float
    baseline_p99_us: float
    p999_us: float
    baseline_p999_us: float
    typical_ratio: float
    p99_ratio: float
    p999_ratio: float
    average_looks_healthy: bool
    tail_is_degraded: bool


def evaluate_ib_write_lat_percentiles(
    msg_bytes: int,
    iterations: int,
    typical_us: float,
    baseline_typical_us: float,
    p99_us: float,
    baseline_p99_us: float,
    p999_us: float,
    baseline_p999_us: float,
) -> LatencyPercentileAudit:
    """Evaluate V8 Ch. 10 Step 6 `ib_write_lat` percentile tail regression vs typical average."""
    typ_r = round(typical_us / baseline_typical_us, 2)
    p99_r = round(p99_us / baseline_p99_us, 2)
    p999_r = round(p999_us / baseline_p999_us, 2)
    avg_ok = typ_r <= 1.05
    tail_bad = (p99_r >= 1.50) or (p999_r >= 2.00)
    return LatencyPercentileAudit(
        msg_bytes=msg_bytes,
        iterations=iterations,
        typical_us=typical_us,
        baseline_typical_us=baseline_typical_us,
        p99_us=p99_us,
        baseline_p99_us=baseline_p99_us,
        p999_us=p999_us,
        baseline_p999_us=baseline_p999_us,
        typical_ratio=typ_r,
        p99_ratio=p99_r,
        p999_ratio=p999_r,
        average_looks_healthy=avg_ok,
        tail_is_degraded=tail_bad,
    )


@dataclass(frozen=True)
class LayeredTriageDecision:
    first_failing_gate: str  # "GATE_1_INVENTORY", "GATE_2_PHYSICAL", "GATE_3_SM_CONTROL", "GATE_4_ROUTING_PKEY", "GATE_5_HOST_RDMA", "GATE_6_GPUDIRECT_NUMA", "GATE_7_APPLICATION"
    stop_layer_number: int
    diagnosis: str
    remediation: str


def run_seven_gate_bottom_up_triage(
    inventory_matches_bom: bool,
    phys_link_up: bool,
    rate_and_width_match_design: bool,
    physical_errors_stable: bool,
    sm_master_healthy_and_port_active: bool,
    route_and_pkey_valid: bool,
    host_rdma_bw_and_tail_healthy: bool,
    gpudirect_and_numa_local: bool,
) -> LayeredTriageDecision:
    """Execute the V8 Ch. 10 / Ch. 12 / Lab 04 7-gate bottom-up troubleshooting sequence."""
    if not inventory_matches_bom:
        return LayeredTriageDecision(
            first_failing_gate="GATE_1_INVENTORY",
            stop_layer_number=1,
            diagnosis="Discovered GUID/cable/switch inventory deviates from source of truth.",
            remediation="Reconcile `ibnetdiscover` / `iblinkinfo` against rack wiring plan before testing.",
        )
    if not (phys_link_up and rate_and_width_match_design and physical_errors_stable):
        return LayeredTriageDecision(
            first_failing_gate="GATE_2_PHYSICAL",
            stop_layer_number=2,
            diagnosis="Physical link down, width/speed downshifted (e.g. 1x vs 4x), or symbol/recovery errors climbing.",
            remediation="STOP: Inspect `ibstat`, `iblinkinfo`, `mlxlink -c -m`, and `perfquery`; replace cable/optic.",
        )
    if not sm_master_healthy_and_port_active:
        return LayeredTriageDecision(
            first_failing_gate="GATE_3_SM_CONTROL",
            stop_layer_number=3,
            diagnosis="Port is `LinkUp` but stuck in `Initializing` (`Base lid: 0`) or `sminfo` shows no/wedged Master SM.",
            remediation="STOP: Check `sminfo`, UFM/OpenSM logs, `smpquery` vs `saquery`, and VL15 reachability.",
        )
    if not route_and_pkey_valid:
        return LayeredTriageDecision(
            first_failing_gate="GATE_4_ROUTING_PKEY",
            stop_layer_number=4,
            diagnosis="Missing LFT route (`ibroute`), rail imbalance, or incompatible `P_Key` membership (`smpquery pkeys`).",
            remediation="STOP: Repair OpenSM/UFM `partitions.conf` or routing engine policy before debugging QPs.",
        )
    if not host_rdma_bw_and_tail_healthy:
        return LayeredTriageDecision(
            first_failing_gate="GATE_5_HOST_RDMA",
            stop_layer_number=5,
            diagnosis="Host-memory `ib_write_bw` or `ib_write_lat` (p99/p99.9) fails or falls below baseline.",
            remediation="STOP: Fault is in RDMA transport or fabric congestion (`PortXmitWait`), below GPUDirect and NCCL.",
        )
    if not gpudirect_and_numa_local:
        return LayeredTriageDecision(
            first_failing_gate="GATE_6_GPUDIRECT_NUMA",
            stop_layer_number=6,
            diagnosis="Host RDMA is healthy, but GPU-memory RDMA degrades due to cross-NUMA binding (`NUMA 1` vs `NUMA 0`) or missing `nvidia-peermem`.",
            remediation="STOP: Fix `numactl --cpunodebind/--membind`, GPU-to-HCA affinity (`nvidia-smi topo -m`), or GPUDirect DMA-BUF.",
        )
    return LayeredTriageDecision(
        first_failing_gate="GATE_7_APPLICATION",
        stop_layer_number=7,
        diagnosis="Gates 1-6 match baseline; fault is in collective algorithm, rank straggler, or application layer.",
        remediation="Inspect NCCL logs (`NCCL_DEBUG=INFO`), collective scale behavior, and per-rank compute/storage timelines.",
    )
