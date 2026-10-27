#!/usr/bin/env python3
"""Chapter 12.23: Fabric validation and capacity planning.

Deterministic reference models and calculators for AI fabric acceptance validation
and capacity planning (stdlib only):
1. Multi-stage cluster acceptance gating (L1 physical/cable/DOM/BER/FEC/lanes ->
   L2 point-to-point RDMA ib_write_bw / ib_write_lat & GPUDirect RDMA ->
   L3 pair-wise / bisection ring & half-bisection ->
   L4 full-scale nccl-tests all_reduce_perf & alltoall_perf ->
   L5 multi-hour burn-in under concurrent traffic & N-1 link drain).
2. Switch, transceiver, and cable Bill of Materials (BOM) calculator for 2-tier
   (3-stage) and 3-tier (5-stage) Clos fabrics with configurable spare percentages,
   including NVIDIA DGX B200 SuperPOD (1-4 SUs, QM9700 64x400G) and DGX GB300
   SuperPOD (2-16 SUs, Q3400-RD 144x800G IB + SN5600D 64x800G Ethernet + SN2201 OOB).
3. Bottleneck cut capacity and oversubscription impact on synchronous AllReduce
   and AllToAll step times under normal and N-1 degraded states (16x800G vs 8x400G
   4.00:1 -> 4.57:1; 16x400G vs 8x400G 2.00:1 -> 4.00:1; 2 GB AllReduce 40 ms -> 80 ms -> 160 ms;
   shared vs separated VL inference p99 latency 1.8 ms -> 14.2 ms -> 3.1 ms).
4. Topograph / LLDP / ibnetdiscover / iblinkinfo cable matrix diff validation
   (detecting missing links, swapped rail ports, wrong destination switch/port,
   width/speed downtraining, and BCM 11 Topograph topology.conf generation).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 1. Constants from V8 Ch 11/12/Labs 01-04, V9 Ch 10/Labs 01-04,
#    superpod-b200-dc, superpod-gb300-ra, and bcm11-admin §7.5
# ---------------------------------------------------------------------------

# Multi-stage acceptance gating thresholds
L1_PRE_FEC_BER_CEILING: float = 1e-5
L1_POST_FEC_BER_CEILING: float = 1e-15
L1_DOM_RX_POWER_MIN_DBM: float = -6.0
L1_DOM_TX_POWER_MIN_DBM: float = -4.0
L1_DOM_TEMP_MAX_C: float = 70.0
L1_MAX_UNCORRECTED_FEC_DELTA: int = 0
L1_MAX_SYMBOL_ERROR_DELTA: int = 0

# V8 Lab 01 / V9 Lab 01-04 reference device & counter numbers
V8_LAB01_MT4129_PART_ID: int = 4129
V8_LAB01_VENDOR_ID_HEX: str = "0x02c9"
V8_LAB01_FW_VER: str = "28.39.2048"
V8_LAB01_NODE_GUID: str = "08c0:eb03:00f1:a2c3"
V8_LAB01_PORT_GUID_HEX: str = "0x08c0eb0300f1a2c3"
V8_LAB01_CAP_MASK_HEX: str = "0x2651e848"
V8_LAB01_MAX_QP: int = 262144
V8_LAB01_MAX_QP_WR: int = 32768
V8_LAB01_MAX_SGE: int = 30
V8_LAB01_BASE_LID: int = 12
V8_LAB01_SM_LID: int = 1
V8_LAB01_RATE_GBPS: int = 400
V8_INDEX_CLUSTER_NODES: int = 128
V8_INDEX_STEP_TIME_VARIATION_PCT: float = 20.0

V9_CH10_PAIRWISE_BW_GBPS: float = 392.11
V9_CH10_COLLECTIVE_RANKS: int = 16
V9_CH10_COLLECTIVE_RX_ECN_PRIO3: int = 288400
V9_CH10_COLLECTIVE_RX_PFC_PRIO3: int = 61200
V9_CH10_IDLE_TAIL_DROPS: int = 0
V9_CH10_SHARED_TAIL_DROPS: int = 38210

V9_LAB01_RX_PACKETS: int = 1024567
V9_LAB01_RX_BYTES: int = 892481382400
V9_LAB02_TX_BYTES: int = 481029120384
V9_LAB01_FEC_CORRECTED_BASELINE: int = 412
V9_LAB01_FEC_UNCORRECTED_BASELINE: int = 0
V9_LAB01_SPEED_MBPS: int = 400000
V9_LAB01_MTU_BYTES: int = 9000

V9_LAB03_IDLE_RX_PRIO3_PKTS: int = 102314
V9_LAB03_IDLE_TX_PRIO3_PKTS: int = 89621
V9_LAB03_CONTENTION_DURATION_S: int = 60
V9_LAB03_CONTENTION_RX_ECN_PRIO3: int = 47829
V9_LAB03_CONTENTION_RX_PFC_PRIO3: int = 412
V9_LAB03_CONTENTION_TX_PFC_PRIO3: int = 14
V9_LAB03_CONTENTION_RX_PRIO3_PKTS: int = 51234892
V9_LAB03_CONTENTION_TX_PRIO3_PKTS: int = 48901234
V9_LAB03_SENDER_A_BW_GBPS: float = 89.2
V9_LAB03_SENDER_B_BW_GBPS: float = 87.1

V9_LAB04_HEALTHY_BW_GBPS: float = 392.0
V9_LAB04_HEALTHY_DURATION_S: float = 2.1
V9_LAB04_BROKEN_BW_GBPS: float = 156.0
V9_LAB04_BROKEN_DURATION_S: float = 8.2
V9_LAB04_BROKEN_RETRY_EXC_ERR: int = 24
V9_LAB04_BROKEN_RX_ECN_PRIO3: int = 142

# V8 Ch 11 / V9 Ch 10 capacity and oversubscription numbers
V9_CH10_RACK_NODES: int = 16
V9_CH10_RAILS_PER_NODE: int = 2
V9_CH10_RAIL_BW_GBPS: int = 400
V9_CH10_NODE_INJECTION_GBPS: int = 800
V9_CH10_DOWNLINK_DEMAND_GBPS: int = 12800
V9_CH10_UPLINKS_NORMAL: int = 8
V9_CH10_UPLINK_CAP_NORMAL_GBPS: int = 3200
V9_CH10_OVERSUB_NORMAL: float = 4.0
V9_CH10_UPLINKS_DEGRADED: int = 7
V9_CH10_UPLINK_CAP_DEGRADED_GBPS: int = 2800
V9_CH10_OVERSUB_DEGRADED: float = round(12800 / 2800, 2)  # 4.57

V8_CH11_RACKS: int = 16
V8_CH11_ENDPOINTS_PER_RACK: int = 16
V8_CH11_TOTAL_GPUS: int = 256
V8_CH11_DOWNLINK_CAP_GBPS: int = 6400
V8_CH11_NONBLOCKING_LEAF_RADIX: int = 32
V8_CH11_CONSTRAINED_LEAF_RADIX: int = 24
V8_CH11_OVERSUB_2TO1_UPLINKS: int = 8
V8_CH11_OVERSUB_2TO1_CAP_GBPS: int = 3200

V8_CH11_INFERENCE_P99_ISOLATED_MS: float = 1.8
V8_CH11_INFERENCE_P99_SHARED_VL_MS: float = 14.2
V8_CH11_INFERENCE_P99_SEPARATED_VL_MS: float = 3.1

# SuperPOD B200 (superpod-b200-dc p. 15, 19, 20, 21)
B200_PSU_TOTAL: int = 6
B200_PSU_REQUIRED: int = 5
B200_PASSIVE_DAC_100G_MAX_M: int = 5
B200_PASSIVE_DAC_400G_MAX_M: int = 3
B200_AOC_MAX_M: int = 30
B200_CABLE_MAX_DISTANCE_FRACTION: float = 0.90  # keep runs under 90% of max distance

SUPERPOD_B200_BOM_TABLE: Dict[int, Dict[str, int]] = {
    1: {"nodes": 31, "gpus": 248, "leaves": 8, "spines": 4, "compute_ufm_cables": 252, "isl_cables": 256},
    2: {"nodes": 63, "gpus": 504, "leaves": 16, "spines": 8, "compute_ufm_cables": 508, "isl_cables": 512},
    3: {"nodes": 95, "gpus": 760, "leaves": 24, "spines": 16, "compute_ufm_cables": 764, "isl_cables": 768},
    4: {"nodes": 127, "gpus": 1016, "leaves": 32, "spines": 16, "compute_ufm_cables": 1020, "isl_cables": 1024},
}

# SuperPOD GB300 (superpod-gb300-ra p. 5, 8-13, 19-23, 31)
GB300_SU_TDP_MW: float = 1.2
GB300_RACKS_PER_SU: int = 8
GB300_GPUS_PER_RACK: int = 72
GB300_TRAYS_PER_RACK: int = 18
GB300_SUPERCHIPS_PER_TRAY: int = 2
GB300_GPUS_PER_TRAY: int = 4
GB300_NVLINK_SWITCH_TRAYS_PER_RACK: int = 9
GB300_NVLINK_CHIPS_PER_SWITCH_TRAY: int = 2
GB300_NVLINK5_LINKS_PER_GPU: int = 18
GB300_NVLINK5_BW_TBPS: float = 1.8
GB300_NVLINK_C2C_BW_GBPS: int = 900
GB300_POWER_SHELVES_PER_RACK: int = 8
GB300_PSUS_PER_SHELF: int = 6
GB300_PSU_KW: float = 5.5
GB300_SHELF_POWER_KW: float = 33.0
GB300_CX8_NICS_PER_TRAY: int = 4
GB300_CX8_BW_GBPS: int = 800
GB300_BF3_PORTS_PER_TRAY: int = 2
GB300_BF3_PORT_BW_GBPS: int = 400
GB300_INBAND_MGMT_BW_GBPS: int = 200
GB300_OOB_SWITCH_PORTS_1G: int = 48
GB300_Q3400_RADIX: int = 144
GB300_SN5600_RADIX: int = 64
GB300_ETH_COMPUTE_LEAF_UPLINKS_400G: int = 24
GB300_ETH_COMPUTE_LEAF_BLOCKING_RATIO: int = 3  # 1:3 blocking ratio
GB300_ETH_STORAGE_LEAF_UPLINKS_400G: int = 72  # non-blocking 72x400G
GB300_ETH_MGMT_LEAF_UPLINKS_400G: int = 24

SUPERPOD_GB300_SCALE_TABLE: Dict[int, Dict[str, int]] = {
    2: {
        "gpus": 1152,
        "ib_leaves_per_su": 8,
        "ib_leaves_total": 16,
        "ib_spines_total": 8,
        "eth_spines": 4,
        "eth_compute_leaves": 8,
        "eth_storage_leaves": 2,
        "max_storage_400g_links": 64,
        "mgmt_leaves": 2,
        "oob_spines": 2,
    },
    4: {
        "gpus": 2304,
        "ib_leaves_per_su": 8,
        "ib_leaves_total": 32,
        "ib_spines_total": 18,
        "eth_spines": 8,
        "eth_compute_leaves": 16,
        "eth_storage_leaves": 2,
        "max_storage_400g_links": 128,
        "mgmt_leaves": 2,
        "oob_spines": 2,
    },
    8: {
        "gpus": 4608,
        "ib_leaves_per_su": 8,
        "ib_leaves_total": 64,
        "ib_spines_total": 36,
        "eth_spines": 12,
        "eth_compute_leaves": 32,
        "eth_storage_leaves": 4,
        "max_storage_400g_links": 256,
        "mgmt_leaves": 2,
        "oob_spines": 2,
    },
    16: {
        "gpus": 9216,
        "ib_leaves_per_su": 8,
        "ib_leaves_total": 128,
        "ib_spines_total": 72,
        "eth_spines": 24,
        "eth_compute_leaves": 64,
        "eth_storage_leaves": 8,
        "max_storage_400g_links": 1024,
        "mgmt_leaves": 2,
        "oob_spines": 2,
    },
}

SUPERPOD_GB300_STORAGE_PERF_GBPS: Dict[str, Dict[str, int]] = {
    "1_su_read": {"standard": 90, "enhanced": 280},
    "1_su_write": {"standard": 45, "enhanced": 140},
    "4_su_read": {"standard": 360, "enhanced": 1120},
    "4_su_write": {"standard": 180, "enhanced": 560},
}

# BCM 11 Topograph constants (bcm11-admin §7.5)
BCM_TOPOGRAPH_PORT: int = 49021
BCM_TOPOGRAPH_FETCH_TIMEOUT_S: int = 20
BCM_TOPOGRAPH_FETCH_ATTEMPTS: int = 12
BCM_TOPOGRAPH_FETCH_WAIT_S: int = 15
BCM_TOPOGRAPH_AGGREGATION_DELAY_S: int = 15
BCM_TOPOGRAPH_PAGE_SIZE: int = 100
BCM_TOPOGRAPH_MEASURABLES: int = 26


# ---------------------------------------------------------------------------
# 2. Multi-stage Cluster Acceptance Gating Model (L1 -> L5)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AcceptanceStageInput:
    # L1 Physical / DOM / BER / FEC / Negotiated lane state
    active_links: int
    expected_links: int
    min_negotiated_rate_gbps: int
    expected_rate_gbps: int
    min_lane_width: int
    expected_lane_width: int
    max_pre_fec_ber: float
    max_post_fec_ber: float
    min_dom_rx_dbm: float
    max_dom_temp_c: float
    uncorrected_fec_delta: int
    symbol_error_delta: int
    # L2 Point-to-point RDMA & GPUDirect RDMA (ib_write_bw / ib_write_lat)
    p2p_host_bw_gbps: float
    p2p_gdr_bw_gbps: float
    p2p_min_required_bw_gbps: float
    p2p_lat_us: float
    p2p_max_lat_us: float
    retry_exc_err_delta: int
    # L3 Pair-wise / bisection ring & half-bisection concurrent RDMA
    bisection_per_pair_bw_gbps: float
    bisection_min_required_bw_gbps: float
    ring_min_pair_bw_gbps: float
    # L4 Full-scale collectives (nccl-tests all_reduce_perf & alltoall_perf)
    allreduce_busbw_gbps: float
    allreduce_min_busbw_gbps: float
    alltoall_busbw_gbps: float
    alltoall_min_busbw_gbps: float
    nccl_wrong_elements: int
    # L5 Multi-hour burn-in under concurrency & N-1 degraded cut
    burnin_hours: float
    min_burnin_hours: float
    link_flaps_during_burnin: int
    tail_drops_during_burnin: int
    step_time_p99_regression_pct: float
    max_step_time_p99_regression_pct: float
    n_minus_1_verified: bool


@dataclass(frozen=True)
class AcceptanceGateReport:
    stage_results: Dict[str, bool]
    first_failed_stage: Optional[str]
    overall_accepted: bool
    reasons: List[str]


def evaluate_acceptance_ladder(inp: AcceptanceStageInput) -> AcceptanceGateReport:
    """Evaluate L1 through L5 acceptance gates strictly in bottom-up order.

    Per V9 Ch 10 Figure 9.10.1 and V8 Ch 12: every stage must pass its own
    evidence check; a passing collective test cannot retroactively excuse a
    skipped or failed physical/IP/QoS/RDMA stage.
    """
    reasons: List[str] = []

    l1_ok = (
        inp.active_links == inp.expected_links
        and inp.min_negotiated_rate_gbps >= inp.expected_rate_gbps
        and inp.min_lane_width >= inp.expected_lane_width
        and inp.max_pre_fec_ber <= L1_PRE_FEC_BER_CEILING
        and inp.max_post_fec_ber <= L1_POST_FEC_BER_CEILING
        and inp.min_dom_rx_dbm >= L1_DOM_RX_POWER_MIN_DBM
        and inp.max_dom_temp_c <= L1_DOM_TEMP_MAX_C
        and inp.uncorrected_fec_delta <= L1_MAX_UNCORRECTED_FEC_DELTA
        and inp.symbol_error_delta <= L1_MAX_SYMBOL_ERROR_DELTA
    )
    if not l1_ok:
        reasons.append("L1 Physical/Cable/DOM/BER gate failed")

    l2_ok = (
        inp.p2p_host_bw_gbps >= inp.p2p_min_required_bw_gbps
        and inp.p2p_gdr_bw_gbps >= inp.p2p_min_required_bw_gbps
        and inp.p2p_lat_us <= inp.p2p_max_lat_us
        and inp.retry_exc_err_delta == 0
    )
    if not l2_ok:
        reasons.append("L2 Point-to-Point RDMA / GPUDirect ib_write_bw gate failed")

    l3_ok = (
        inp.bisection_per_pair_bw_gbps >= inp.bisection_min_required_bw_gbps
        and inp.ring_min_pair_bw_gbps >= inp.p2p_min_required_bw_gbps
    )
    if not l3_ok:
        reasons.append("L3 Pair-wise Ring & Half-Bisection gate failed")

    l4_ok = (
        inp.allreduce_busbw_gbps >= inp.allreduce_min_busbw_gbps
        and inp.alltoall_busbw_gbps >= inp.alltoall_min_busbw_gbps
        and inp.nccl_wrong_elements == 0
    )
    if not l4_ok:
        reasons.append("L4 Full-Scale Collective nccl-tests gate failed")

    l5_ok = (
        inp.burnin_hours >= inp.min_burnin_hours
        and inp.link_flaps_during_burnin == 0
        and inp.tail_drops_during_burnin == 0
        and inp.step_time_p99_regression_pct <= inp.max_step_time_p99_regression_pct
        and inp.n_minus_1_verified
    )
    if not l5_ok:
        reasons.append("L5 Multi-Hour Burn-In & N-1 Resilience gate failed")

    stages = {"L1": l1_ok, "L2": l2_ok, "L3": l3_ok, "L4": l4_ok, "L5": l5_ok}
    first_failed = next((st for st, ok in stages.items() if not ok), None)
    return AcceptanceGateReport(
        stage_results=stages,
        first_failed_stage=first_failed,
        overall_accepted=(first_failed is None),
        reasons=reasons,
    )


# ---------------------------------------------------------------------------
# 3. Switch / Transceiver / Cable BOM Calculator (2-Tier & 3-Tier Fabrics)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class FabricBOM:
    tiers: int
    gpus: int
    nodes: int
    rails_per_node: int
    switch_radix: int
    leaf_switches: int
    spine_switches: int
    superspine_switches: int
    total_switches_active: int
    total_switches_with_spares: int
    host_to_leaf_cables_active: int
    leaf_to_spine_cables_active: int
    spine_to_superspine_cables_active: int
    total_cables_active: int
    total_cables_with_spares: int
    total_transceivers_active: int
    total_transceivers_with_spares: int


def calculate_clos_bom(
    gpus: int,
    gpus_per_node: int = 8,
    switch_radix: int = 64,
    tiers: int = 2,
    leaf_oversubscription: float = 1.0,
    spine_oversubscription: float = 1.0,
    spare_rate: float = 0.05,
    standalone_transceivers_per_cable: int = 2,
) -> FabricBOM:
    """Compute exact switch, cable, and transceiver BOM for 2-tier or 3-tier Clos.

    - In a 2-tier (3-stage) folded Clos:
      Each leaf has `downlinks = int(switch_radix * leaf_oversubscription / (leaf_oversubscription + 1))`
      Wait: for standard 1:1 non-blocking, `downlinks = switch_radix // 2` and `uplinks = switch_radix // 2`.
      More generally, `uplinks = int(round(downlinks / leaf_oversubscription))`.
    - In a 3-tier (5-stage) folded Clos:
      Leaves connect to Spines (within pods/blocks) and Spines connect to Super-Spines.
    """
    if gpus % gpus_per_node != 0:
        raise ValueError("gpus must be divisible by gpus_per_node")
    nodes = gpus // gpus_per_node
    rails = gpus_per_node

    # Leaf downlink/uplink split: downlinks + uplinks <= switch_radix
    # For 1:1 (oversub=1.0) on 64-port switch: 32 down, 32 up.
    # For k:1 oversub where downlinks = switch_radix // 2 (e.g., 32 down, 16 up on 64-port, or 16 down, 8 up on 24-port):
    if math.isclose(leaf_oversubscription, 1.0):
        leaf_down = switch_radix // 2
        leaf_up = switch_radix // 2
    else:
        # Maximize downlinks such that downlinks + downlinks/oversub <= switch_radix
        leaf_down = int(round(switch_radix * leaf_oversubscription / (leaf_oversubscription + 1.0)))
        leaf_up = switch_radix - leaf_down

    leaf_switches = math.ceil(gpus / leaf_down)
    host_to_leaf_cables = gpus
    leaf_to_spine_cables = leaf_switches * leaf_up

    if tiers == 2:
        spine_switches = math.ceil(leaf_to_spine_cables / switch_radix)
        superspine_switches = 0
        spine_to_superspine_cables = 0
    elif tiers == 3:
        # In 3-tier (5-stage) Clos, each spine uses half its ports (or ratio) toward leaves
        spine_down = switch_radix // 2
        spine_up = int(round(spine_down / spine_oversubscription))
        spine_switches = math.ceil(leaf_to_spine_cables / spine_down)
        spine_to_superspine_cables = spine_switches * spine_up
        superspine_switches = math.ceil(spine_to_superspine_cables / switch_radix)
    else:
        raise ValueError("tiers must be 2 or 3")

    total_switches = leaf_switches + spine_switches + superspine_switches
    total_cables = host_to_leaf_cables + leaf_to_spine_cables + spine_to_superspine_cables
    total_transceivers = total_cables * standalone_transceivers_per_cable

    switches_with_spares = math.ceil(total_switches * (1.0 + spare_rate))
    cables_with_spares = math.ceil(total_cables * (1.0 + spare_rate))
    transceivers_with_spares = math.ceil(total_transceivers * (1.0 + spare_rate))

    return FabricBOM(
        tiers=tiers,
        gpus=gpus,
        nodes=nodes,
        rails_per_node=rails,
        switch_radix=switch_radix,
        leaf_switches=leaf_switches,
        spine_switches=spine_switches,
        superspine_switches=superspine_switches,
        total_switches_active=total_switches,
        total_switches_with_spares=switches_with_spares,
        host_to_leaf_cables_active=host_to_leaf_cables,
        leaf_to_spine_cables_active=leaf_to_spine_cables,
        spine_to_superspine_cables_active=spine_to_superspine_cables,
        total_cables_active=total_cables,
        total_cables_with_spares=cables_with_spares,
        total_transceivers_active=total_transceivers,
        total_transceivers_with_spares=transceivers_with_spares,
    )


# ---------------------------------------------------------------------------
# 4. Bottleneck Cut & Oversubscription Impact on Collective Step Time
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CutCapacityAndStepImpact:
    downlink_demand_gbps: float
    uplink_capacity_normal_gbps: float
    uplink_capacity_degraded_gbps: float
    oversub_normal: float
    oversub_degraded: float
    effective_node_bw_normal_gbps: float
    effective_node_bw_degraded_gbps: float
    allreduce_time_uncongested_ms: float
    allreduce_time_normal_ms: float
    allreduce_time_degraded_ms: float
    alltoall_time_normal_ms: float
    alltoall_time_degraded_ms: float


def model_cut_and_collective_impact(
    nodes_per_leaf: int,
    injection_per_node_gbps: float,
    uplinks_normal: int,
    uplinks_degraded: int,
    uplink_rate_gbps: float,
    collective_payload_bytes: int,
    total_ranks: int,
    cross_cut_traffic_fraction: float = 1.0,
) -> CutCapacityAndStepImpact:
    """Calculate normal and N-1 cut oversubscription and collective step times.

    - AllReduce ring volume per rank = 2 * (n - 1) / n * S bytes.
      Note: V8 Ch 6 uses simplified payload-to-wire time `S / BW` (`2 GB` at `50 GB/s` = `40 ms`,
      at `25 GB/s` = `80 ms`, at `12.5 GB/s` = `160 ms`) when `2*(n-1)/n` is absorbed into effective
      bidirectional transfer or for asymptotic `S` transfer. Here we compute the exact transfer time
      for `collective_payload_bytes` across the bottleneck per-node bandwidth.
    """
    downlink_demand = nodes_per_leaf * injection_per_node_gbps * cross_cut_traffic_fraction
    cap_normal = uplinks_normal * uplink_rate_gbps
    cap_degraded = uplinks_degraded * uplink_rate_gbps

    oversub_norm = round(downlink_demand / cap_normal, 2)
    oversub_deg = round(downlink_demand / cap_degraded, 2)

    eff_bw_norm_gbps = min(injection_per_node_gbps, cap_normal / (nodes_per_leaf * cross_cut_traffic_fraction))
    eff_bw_deg_gbps = min(injection_per_node_gbps, cap_degraded / (nodes_per_leaf * cross_cut_traffic_fraction))

    # Convert Gbps to decimal GB/s (1 Byte = 8 bits)
    uncongested_gbs = injection_per_node_gbps / 8.0
    norm_gbs = eff_bw_norm_gbps / 8.0
    deg_gbs = eff_bw_deg_gbps / 8.0

    payload_gb = collective_payload_bytes / 1e9
    ar_uncongested_ms = round((payload_gb / uncongested_gbs) * 1000.0, 2)
    ar_norm_ms = round((payload_gb / norm_gbs) * 1000.0, 2)
    ar_deg_ms = round((payload_gb / deg_gbs) * 1000.0, 2)

    a2a_factor = (total_ranks - 1) / total_ranks
    a2a_norm_ms = round(((payload_gb * a2a_factor) / norm_gbs) * 1000.0, 2)
    a2a_deg_ms = round(((payload_gb * a2a_factor) / deg_gbs) * 1000.0, 2)

    return CutCapacityAndStepImpact(
        downlink_demand_gbps=downlink_demand,
        uplink_capacity_normal_gbps=cap_normal,
        uplink_capacity_degraded_gbps=cap_degraded,
        oversub_normal=oversub_norm,
        oversub_degraded=oversub_deg,
        effective_node_bw_normal_gbps=round(eff_bw_norm_gbps, 2),
        effective_node_bw_degraded_gbps=round(eff_bw_deg_gbps, 2),
        allreduce_time_uncongested_ms=ar_uncongested_ms,
        allreduce_time_normal_ms=ar_norm_ms,
        allreduce_time_degraded_ms=ar_deg_ms,
        alltoall_time_normal_ms=a2a_norm_ms,
        alltoall_time_degraded_ms=a2a_deg_ms,
    )


# ---------------------------------------------------------------------------
# 5. Topograph / LLDP / ibnetdiscover Cable Matrix Diff Validator
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CableLinkSpec:
    src_host: str
    src_port: str
    src_rail: int
    dst_switch: str
    dst_port: str
    speed_gbps: int
    width_lanes: int


@dataclass(frozen=True)
class CableDiffDiscrepancy:
    src_host: str
    src_port: str
    category: str  # "MISSING_LINK", "RAIL_SWITCH_MISMATCH", "PORT_SWAP", "SPEED_OR_WIDTH_DOWNTRAIN"
    expected: str
    observed: str


def validate_cable_matrix_diff(
    expected_links: List[CableLinkSpec],
    discovered_links: List[CableLinkSpec],
) -> List[CableDiffDiscrepancy]:
    """Compare discovered LLDP / ibnetdiscover / Topograph links against the Point-to-Point BOM."""
    disc_map: Dict[Tuple[str, str], CableLinkSpec] = {
        (lnk.src_host, lnk.src_port): lnk for lnk in discovered_links
    }
    discrepancies: List[CableDiffDiscrepancy] = []

    for exp in expected_links:
        key = (exp.src_host, exp.src_port)
        if key not in disc_map:
            discrepancies.append(
                CableDiffDiscrepancy(
                    src_host=exp.src_host,
                    src_port=exp.src_port,
                    category="MISSING_LINK",
                    expected=f"{exp.dst_switch}:{exp.dst_port} ({exp.speed_gbps}G x{exp.width_lanes})",
                    observed="NOT_DISCOVERED",
                )
            )
            continue

        obs = disc_map[key]
        if obs.dst_switch != exp.dst_switch:
            discrepancies.append(
                CableDiffDiscrepancy(
                    src_host=exp.src_host,
                    src_port=exp.src_port,
                    category="RAIL_SWITCH_MISMATCH",
                    expected=f"{exp.dst_switch}:{exp.dst_port} (rail {exp.src_rail})",
                    observed=f"{obs.dst_switch}:{obs.dst_port}",
                )
            )
        elif obs.dst_port != exp.dst_port:
            discrepancies.append(
                CableDiffDiscrepancy(
                    src_host=exp.src_host,
                    src_port=exp.src_port,
                    category="PORT_SWAP",
                    expected=f"{exp.dst_switch}:{exp.dst_port}",
                    observed=f"{obs.dst_switch}:{obs.dst_port}",
                )
            )

        if obs.speed_gbps < exp.speed_gbps or obs.width_lanes < exp.width_lanes:
            discrepancies.append(
                CableDiffDiscrepancy(
                    src_host=exp.src_host,
                    src_port=exp.src_port,
                    category="SPEED_OR_WIDTH_DOWNTRAIN",
                    expected=f"{exp.speed_gbps}G x{exp.width_lanes}",
                    observed=f"{obs.speed_gbps}G x{obs.width_lanes}",
                )
            )

    return discrepancies


def generate_slurm_topology_conf(
    spine_to_leaves: Dict[str, List[str]],
    leaf_to_nodes: Dict[str, List[str]],
) -> List[str]:
    """Generate deterministic Slurm topology/tree lines as produced by BCM 11 Topograph."""
    lines: List[str] = []
    for spine, leaves in sorted(spine_to_leaves.items()):
        leaf_str = ",".join(sorted(leaves))
        lines.append(f"SwitchName={spine} Switches={leaf_str}")
    for leaf, nodes in sorted(leaf_to_nodes.items()):
        node_str = ",".join(sorted(nodes))
        lines.append(f"SwitchName={leaf} Nodes={node_str}")
    return lines
