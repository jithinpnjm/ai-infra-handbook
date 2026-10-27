#!/usr/bin/env python3
"""InfiniBand Adaptive Routing and Congestion Control simulator and calculators.

Covers:
1. Credit-Based Flow Control (CBFC) and Virtual Lane (VL0..VL14 data, VL15 SMP)
   64-byte credit block accounting, backpressure propagation, credit-loop detection,
   and victim-buffer / Head-of-Line (HoL) blocking isolation across Service Levels (SLs).
2. Static Linear Forwarding Table (LFT) destination-LID forwarding and PortXmitData
   4-octet counter imbalance vs Adaptive Routing (AR) group tables (`AR_group`),
   dynamic port selection (assigned-flow, flowlet, and packet-spray modes), and
   `ar_sl_mask` bitmask filtering.
3. Fast Notification (`FRN` / `RN`) and Self-Healing Interconnect (`SHIELD`)
   autonomous sub-millisecond hardware link-failure rerouting vs OpenSM `Trap 128`
   control-plane heavy sweep convergence.
4. Out-of-Order (OOO) packet delivery under Adaptive Routing and ConnectX HCA
   hardware packet reordering window vs uncompensated tail-latency inflation.
5. InfiniBand Congestion Control (IBTA closed loop): Switch queue threshold ->
   Forward Explicit Congestion Notification (`FECN`) -> Destination HCA ->
   Backward Explicit Congestion Notification (`BECN`) -> Source HCA Congestion
   Control Table Index (`CCTI`, 0..127), injection rate throttling, and recovery timer.
6. Production `perfquery` / `ibqueryerrors` telemetry classifiers (`PortXmitWait`
   vs `SymbolErrorCounter` / `LinkDownedCounter`, congestion-tree gradient root
   finder, and cumulative vs rate-of-change error acceleration).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence, Tuple

# ---------------------------------------------------------------------------
# Protocol and Architecture Constants (IBTA / NVIDIA Quantum / ADC Ch. 9 / V8)
# ---------------------------------------------------------------------------
IB_MAX_VLS: int = 16  # VL0..VL14 data VLs + VL15 Subnet Management (SMP)
IB_DATA_VLS: int = 15  # VL0..VL14
IB_SMP_VL: int = 15  # VL15 reserved for Subnet Management Packets (unrouted, link-local)
IB_CREDIT_UNIT_BYTES: int = 64  # 1 IB flow-control credit = 64 bytes (ADC Ch. 9)
IB_LRH_LID_BITS: int = 16  # 16-bit LID in Local Route Header (LRH)
IB_MAX_UNICAST_LIDS: int = 48_000  # Up to 48,000 unicast end nodes per subnet (ADC Ch. 9)
IB_SWITCH_LATENCY_NS: int = 300  # ~300 ns IB vs ~800 ns Ethernet storage switch latency (ADC Ch. 9)
ETH_SWITCH_LATENCY_NS: int = 800
IB_PORT_XMIT_DATA_OCTETS: int = 4  # PortXmitData / PortRcvData count in 4-octet (32-bit) words

# Adaptive Routing & SHIELD constants
AR_DEFAULT_SL_MASK: int = 0xFFFF  # 16-bit SL mask (SL0..SL15)
QUANTUM2_NDR_PORT_GBPS: int = 400
QUANTUM2_NDR_RADIX: int = 64
QUANTUM_X800_PORT_GBPS: int = 800  # superpod-gb300-ra p. 12
QUANTUM_X800_Q3400_RADIX: int = 144  # superpod-gb300-ra p. 20 (Q3400-RD 144-port switch)
GB300_MAX_SUS_2LAYER: int = 16  # superpod-gb300-ra p. 20-21 (16 SUs = 9,216 GPUs, 128 leaf, 72 spine)
GB300_MAX_GPUS_2LAYER: int = 9216
GB300_LEAF_SWITCHES_16SU: int = 128
GB300_SPINE_SWITCHES_16SU: int = 72
OPENSM_LINK_TRAP_ID: int = 128  # OpenSM Trap 128 (link state change, V8 Ch. 5)

# IBTA Congestion Control Table (CCT) constants
CCT_MAX_INDEX: int = 127  # 128-entry Congestion Control Table (indices 0..127)
CCT_TABLE_SIZE: int = 128


# ---------------------------------------------------------------------------
# 1. Credit-Based Flow Control (CBFC), HoL Isolation & Credit Loop Detection
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class VLLinkCreditState:
    vl: int
    buffer_bytes: int
    occupied_bytes: int
    total_credits: int
    available_credits: int
    can_transmit_4kb_mtu: bool
    is_stalled: bool


def evaluate_vl_credit_state(
    vl: int,
    buffer_bytes: int,
    occupied_bytes: int,
    packet_bytes: int = 4096,
) -> VLLinkCreditState:
    """Compute per-VL credit availability (`64` B per credit) and stall status."""
    if not (0 <= vl < IB_MAX_VLS):
        raise ValueError(f"VL must be in 0..{IB_MAX_VLS - 1}")
    if buffer_bytes < 0 or occupied_bytes < 0 or occupied_bytes > buffer_bytes:
        raise ValueError("Invalid buffer or occupied byte counts")
    total_credits = buffer_bytes // IB_CREDIT_UNIT_BYTES
    free_bytes = buffer_bytes - occupied_bytes
    avail_credits = free_bytes // IB_CREDIT_UNIT_BYTES
    required_credits = (packet_bytes + IB_CREDIT_UNIT_BYTES - 1) // IB_CREDIT_UNIT_BYTES
    can_tx = avail_credits >= required_credits
    return VLLinkCreditState(
        vl=vl,
        buffer_bytes=buffer_bytes,
        occupied_bytes=occupied_bytes,
        total_credits=total_credits,
        available_credits=avail_credits,
        can_transmit_4kb_mtu=can_tx,
        is_stalled=not can_tx,
    )


@dataclass(frozen=True)
class HoLIsolationResult:
    shared_vl_victim_blocked: bool
    separated_vl_victim_blocked: bool
    baseline_p99_ms: float
    shared_vl_p99_ms: float
    separated_vl_p99_ms: float
    shared_inflation_factor: float
    separated_recovery_pct: float


def simulate_vl_hol_isolation(
    incast_vl_occupied_bytes: int = 65536,
    vl_buffer_bytes: int = 65536,
    victim_vl_occupied_bytes: int = 4096,
    baseline_p99_ms: float = 1.8,
    shared_vl_p99_ms: float = 14.2,
    separated_vl_p99_ms: float = 3.1,
) -> HoLIsolationResult:
    """Compare Victim Flow blocking when sharing a congested VL vs isolated on a dedicated VL.

    Uses the Volume 08 Chapter 11 Scenario 3 p99 latency profile:
    1.8 ms (isolated baseline) -> 14.2 ms (shared VL, training active) -> 3.1 ms (separated VL).
    """
    shared_state = evaluate_vl_credit_state(0, vl_buffer_bytes, incast_vl_occupied_bytes)
    separated_state = evaluate_vl_credit_state(1, vl_buffer_bytes, victim_vl_occupied_bytes)
    shared_inflation = round(shared_vl_p99_ms / baseline_p99_ms, 2)
    recovered = (shared_vl_p99_ms - separated_vl_p99_ms) / (shared_vl_p99_ms - baseline_p99_ms) * 100.0
    return HoLIsolationResult(
        shared_vl_victim_blocked=shared_state.is_stalled,
        separated_vl_victim_blocked=separated_state.is_stalled,
        baseline_p99_ms=baseline_p99_ms,
        shared_vl_p99_ms=shared_vl_p99_ms,
        separated_vl_p99_ms=separated_vl_p99_ms,
        shared_inflation_factor=shared_inflation,
        separated_recovery_pct=round(recovered, 2),
    )


def detect_credit_dependency_cycle(edges: Sequence[Tuple[str, str]]) -> Tuple[bool, List[str]]:
    """Detect whether a channel dependency graph `(u -> v)` contains a credit loop."""
    adj: Dict[str, List[str]] = {}
    nodes = set()
    for u, v in edges:
        adj.setdefault(u, []).append(v)
        nodes.add(u)
        nodes.add(v)

    visited: Dict[str, int] = {n: 0 for n in nodes}  # 0=unvisited, 1=visiting, 2=done
    parent: Dict[str, str] = {}

    for start in sorted(nodes):
        if visited[start] != 0:
            continue
        stack: List[Tuple[str, int]] = [(start, 0)]
        visited[start] = 1
        while stack:
            curr, idx = stack[-1]
            nbrs = adj.get(curr, [])
            if idx < len(nbrs):
                nxt = nbrs[idx]
                stack[-1] = (curr, idx + 1)
                if visited[nxt] == 1:
                    cycle = [nxt]
                    for s_node, _ in reversed(stack):
                        cycle.append(s_node)
                        if s_node == nxt:
                            break
                    cycle.reverse()
                    return True, cycle
                if visited[nxt] == 0:
                    parent[nxt] = curr
                    visited[nxt] = 1
                    stack.append((nxt, 0))
            else:
                visited[curr] = 2
                stack.pop()
    return False, []


# ---------------------------------------------------------------------------
# 2. Static LFT vs Adaptive Routing (`AR_group`) & Uplink Imbalance
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class UplinkBalanceAnalysis:
    bytes_per_port: Dict[int, int]
    max_to_min_ratio: float
    total_bytes: int
    is_imbalanced: bool


def analyze_uplink_port_xmit_data(
    word_deltas_by_port: Dict[int, int],
    already_in_bytes: bool = False,
) -> UplinkBalanceAnalysis:
    """Convert `PortXmitData`deltas (4 octets/word unless already bytes) and compute balance ratio."""
    scale = 1 if already_in_bytes else IB_PORT_XMIT_DATA_OCTETS
    bytes_map = {p: int(v) * scale for p, v in word_deltas_by_port.items()}
    vals = list(bytes_map.values())
    hi, lo = max(vals), max(1, min(vals))
    ratio = round(hi / lo, 2)
    return UplinkBalanceAnalysis(
        bytes_per_port=bytes_map,
        max_to_min_ratio=ratio,
        total_bytes=sum(vals),
        is_imbalanced=ratio >= 2.0,
    )


@dataclass(frozen=True)
class ARForwardingComparison:
    dlid: int
    sl: int
    ar_enabled_for_sl: bool
    static_lft_port: int
    ar_selected_port: int
    static_max_port_load_gbps: float
    ar_max_port_load_gbps: float
    static_dropped_or_queued_gbps: float
    ar_dropped_or_queued_gbps: float


def simulate_lft_vs_ar_group_selection(
    dlid: int,
    sl: int,
    ar_sl_mask: int,
    static_lft_port: int,
    ar_group_ports: Sequence[int],
    existing_port_load_gbps: Dict[int, float],
    existing_port_queue_kb: Dict[int, float],
    new_flow_gbps: float,
    port_capacity_gbps: float = 400.0,
) -> ARForwardingComparison:
    """Compare static LFT forwarding against Adaptive Routing (`AR_group`) least-loaded selection."""
    ar_eligible = bool((ar_sl_mask >> sl) & 1) and len(ar_group_ports) > 0
    static_loads = dict(existing_port_load_gbps)
    static_loads[static_lft_port] = static_loads.get(static_lft_port, 0.0) + new_flow_gbps

    if ar_eligible:
        best_port = min(
            ar_group_ports,
            key=lambda p: (
                existing_port_load_gbps.get(p, 0.0) / port_capacity_gbps
                + existing_port_queue_kb.get(p, 0.0) / 1000.0,
                p,
            ),
        )
    else:
        best_port = static_lft_port

    ar_loads = dict(existing_port_load_gbps)
    ar_loads[best_port] = ar_loads.get(best_port, 0.0) + new_flow_gbps

    static_max = max(static_loads.values())
    ar_max = max(ar_loads.values())
    static_excess = sum(max(0.0, ld - port_capacity_gbps) for ld in static_loads.values())
    ar_excess = sum(max(0.0, ld - port_capacity_gbps) for ld in ar_loads.values())

    return ARForwardingComparison(
        dlid=dlid,
        sl=sl,
        ar_enabled_for_sl=ar_eligible,
        static_lft_port=static_lft_port,
        ar_selected_port=best_port,
        static_max_port_load_gbps=round(static_max, 2),
        ar_max_port_load_gbps=round(ar_max, 2),
        static_dropped_or_queued_gbps=round(static_excess, 2),
        ar_dropped_or_queued_gbps=round(ar_excess, 2),
    )


# ---------------------------------------------------------------------------
# 3. Fast Notification (`FRN`) / `SHIELD` Autonomous Failover vs OpenSM Sweep
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LinkFailureRecoveryResult:
    failed_port: int
    surviving_ar_ports: Tuple[int, ...]
    shield_frn_recovery_us: float
    opensm_sweep_recovery_us: float
    speedup_factor: float
    inflight_bytes_at_risk_shield: int
    inflight_bytes_at_risk_opensm: int


def evaluate_shield_frn_vs_opensm_failover(
    ar_group_ports: Sequence[int],
    failed_port: int,
    line_rate_gbps: float = 400.0,
    shield_detection_reroute_us: float = 10.0,
    opensm_trap128_sweep_ms: float = 500.0,
) -> LinkFailureRecoveryResult:
    """Compare autonomous switch `SHIELD` / `FRN` port removal vs OpenSM `Trap 128` heavy sweep."""
    surviving = tuple(p for p in ar_group_ports if p != failed_port)
    opensm_us = opensm_trap128_sweep_ms * 1000.0
    bytes_per_us = (line_rate_gbps * 1e9 / 8.0) / 1e6  # e.g. 400 Gbps = 50,000 B/us
    shield_bytes = int(round(shield_detection_reroute_us * bytes_per_us))
    opensm_bytes = int(round(opensm_us * bytes_per_us))
    return LinkFailureRecoveryResult(
        failed_port=failed_port,
        surviving_ar_ports=surviving,
        shield_frn_recovery_us=round(shield_detection_reroute_us, 2),
        opensm_sweep_recovery_us=round(opensm_us, 2),
        speedup_factor=round(opensm_us / shield_detection_reroute_us, 1),
        inflight_bytes_at_risk_shield=shield_bytes,
        inflight_bytes_at_risk_opensm=opensm_bytes,
    )


# ---------------------------------------------------------------------------
# 4. Out-of-Order (`OOO`) Delivery & ConnectX Hardware Reordering Evaluation
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OOOEvaluationResult:
    arrival_psns: Tuple[int, ...]
    in_order_stream_delivered: Tuple[int, ...]
    max_reorder_distance: int
    exceeded_reorder_window: bool
    psn_gap_nak_count: int
    p50_before_us: float
    p50_after_us: float
    p99_before_us: float
    p99_after_us: float
    p99_inflation_factor: float
    max_inflation_factor: float


def evaluate_ar_ooo_reordering(
    arrival_psns: Sequence[int],
    hca_reorder_buffer_enabled: bool,
    reorder_window_packets: int = 64,
    p50_before_us: float = 3.1,
    p50_after_us: float = 2.4,
    p95_before_us: float = 4.8,
    p95_after_us: float = 5.9,
    p99_before_us: float = 7.2,
    p99_after_us: float = 38.6,
    max_before_us: float = 9.1,
    max_after_us: float = 112.4,
) -> OOOEvaluationResult:
    """Simulate PSN arrival order under Adaptive Routing and ConnectX OOO reorder buffer.

    Also evaluates the Volume 08 Chapter 7 Scenario 3 latency distribution:
    Before tuning: p50=3.1us, p95=4.8us, p99=7.2us, max=9.1us
    After tuning (uncompensated OOO / reaction timing): p50=2.4us, p95=5.9us, p99=38.6us, max=112.4us
    """
    expected = min(arrival_psns) if arrival_psns else 0
    max_dist = 0
    naks = 0
    held = set()
    delivered: List[int] = []

    for psn in arrival_psns:
        if psn > expected:
            dist = psn - expected
            if dist > max_dist:
                max_dist = dist
            if not hca_reorder_buffer_enabled or dist > reorder_window_packets:
                naks += 1
            held.add(psn)
        elif psn == expected:
            delivered.append(psn)
            expected += 1
            while expected in held:
                held.remove(expected)
                delivered.append(expected)
                expected += 1

    for psn in sorted(held):
        delivered.append(psn)

    exceeded = (not hca_reorder_buffer_enabled and max_dist > 0) or (max_dist > reorder_window_packets)
    return OOOEvaluationResult(
        arrival_psns=tuple(arrival_psns),
        in_order_stream_delivered=tuple(delivered),
        max_reorder_distance=max_dist,
        exceeded_reorder_window=exceeded,
        psn_gap_nak_count=naks,
        p50_before_us=p50_before_us,
        p50_after_us=p50_after_us,
        p99_before_us=p99_before_us,
        p99_after_us=p99_after_us,
        p99_inflation_factor=round(p99_after_us / p99_before_us, 2),
        max_inflation_factor=round(max_after_us / max_before_us, 2),
    )


# ---------------------------------------------------------------------------
# 5. InfiniBand Congestion Control (`FECN` -> `BECN` -> `CCTI` Rate Control)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class IBCongestionControlStep:
    fecn_marked: bool
    becn_returned: bool
    previous_ccti: int
    new_ccti: int
    line_rate_gbps: float
    injected_rate_gbps: float
    inter_packet_delay_multiplier: float


def step_ib_cc_state_machine(
    current_ccti: int,
    switch_queue_occupancy_pct: float,
    switch_fecn_threshold_pct: float = 50.0,
    becn_received: bool = False,
    ccti_timer_expired: bool = False,
    ccti_increase: int = 16,
    ccti_min: int = 0,
    ccti_limit: int = CCT_MAX_INDEX,
    line_rate_gbps: float = 400.0,
) -> IBCongestionControlStep:
    """Execute one step of the IBTA `FECN` -> `BECN` -> `CCTI` congestion control loop.

    - Switch sets `FECN=1` when queue occupancy >= `switch_fecn_threshold_pct`.
    - Destination HCA reflects `FECN=1` back to source HCA as `BECN=1`.
    - On receiving `BECN=1`, source HCA increments `CCTI = min(ccti_limit, current_ccti + ccti_increase)`.
    - On `CCTI_Timer` expiry without `BECN`, source HCA decrements `CCTI = max(ccti_min, current_ccti - 1)`.
    - Injection rate scales inversely with `1 + (new_ccti / 32.0)`.
    """
    fecn = switch_queue_occupancy_pct >= switch_fecn_threshold_pct
    becn = becn_received or fecn
    nxt = current_ccti
    if becn:
        nxt = min(ccti_limit, nxt + ccti_increase)
    elif ccti_timer_expired:
        nxt = max(ccti_min, nxt - 1)

    delay_mult = round(1.0 + (nxt / 32.0), 4)
    rate = round(line_rate_gbps / delay_mult, 2)
    return IBCongestionControlStep(
        fecn_marked=fecn,
        becn_returned=becn,
        previous_ccti=current_ccti,
        new_ccti=nxt,
        line_rate_gbps=line_rate_gbps,
        injected_rate_gbps=rate,
        inter_packet_delay_multiplier=delay_mult,
    )


# ---------------------------------------------------------------------------
# 6. Production Telemetry Classifiers & Oversubscription Math (V8 Ch. 6, 7, 9, 10)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PortCounterClassification:
    port: int
    port_xmit_wait_delta: int
    symbol_error_delta: int
    link_downed_delta: int
    classification: str
    recommended_action: str


def classify_ib_port_telemetry(
    port: int,
    port_xmit_wait_delta: int,
    symbol_error_delta: int,
    link_downed_delta: int,
    wait_alert_threshold: int = 10_000,
) -> PortCounterClassification:
    """Distinguish pure fabric congestion from physical link fault using `perfquery` deltas."""
    if symbol_error_delta > 0 or link_downed_delta > 0:
        if port_xmit_wait_delta >= wait_alert_threshold:
            cls = "PHYSICAL_FAULT_COMPOUNDING_CONGESTION"
            act = "Repair cable, optics, or port FIRST; congestion may clear once link recovers."
        else:
            cls = "PHYSICAL_LINK_FAULT"
            act = "Inspect and replace cable, transceiver, or port; do NOT tune congestion control."
    elif port_xmit_wait_delta >= wait_alert_threshold:
        cls = "PURE_FABRIC_CONGESTION"
        act = "Trace PortXmitWait gradient to root bottleneck; adjust AR, CC, or job placement."
    else:
        cls = "HEALTHY_PORT"
        act = "No action required; port is within baseline."

    return PortCounterClassification(
        port=port,
        port_xmit_wait_delta=port_xmit_wait_delta,
        symbol_error_delta=symbol_error_delta,
        link_downed_delta=link_downed_delta,
        classification=cls,
        recommended_action=act,
    )


def locate_congestion_tree_root_ports(
    port_xmit_wait_deltas: Dict[int, int],
    spike_multiplier: float = 10.0,
) -> Tuple[int, ...]:
    """Identify the root downstream port(s) of a congestion tree from `PortXmitWait` deltas."""
    if not port_xmit_wait_deltas:
        return ()
    sorted_vals = sorted(port_xmit_wait_deltas.values())
    median_baseline = max(1, sorted_vals[len(sorted_vals) // 2])
    roots = [
        p
        for p, val in sorted(port_xmit_wait_deltas.items())
        if val >= median_baseline * spike_multiplier
    ]
    return tuple(roots)


@dataclass(frozen=True)
class ErrorTrendEvaluation:
    delta_window_1: int
    delta_window_2: int
    rate_per_day_window_1: float
    rate_per_day_window_2: float
    acceleration_factor: float
    is_active_degradation: bool


def evaluate_symbol_error_acceleration(
    day1_count: int,
    day4_count: int,
    day7_count: int,
    window_days: float = 3.0,
) -> ErrorTrendEvaluation:
    """Compute rate-of-change acceleration across three snapshots (V8 Ch. 9 Day 1/4/7 story)."""
    d1 = day4_count - day1_count
    d2 = day7_count - day4_count
    r1 = d1 / window_days
    r2 = d2 / window_days
    accel = round(r2 / r1, 2) if r1 > 0 else (0.0 if r2 == 0 else float("inf"))
    return ErrorTrendEvaluation(
        delta_window_1=d1,
        delta_window_2=d2,
        rate_per_day_window_1=round(r1, 2),
        rate_per_day_window_2=round(r2, 2),
        acceleration_factor=accel,
        is_active_degradation=d2 > 0 and accel >= 2.0,
    )


@dataclass(frozen=True)
class LeafOversubscriptionImpact:
    downlink_bw_gbps: float
    uplink_bw_gbps: float
    oversubscription_ratio: float
    effective_node_bw_gbps: float
    nonblocking_step_ms: float
    oversubscribed_step_ms: float


def compute_leaf_oversubscription_allreduce_impact(
    downlink_ports: int = 16,
    uplink_ports: int = 8,
    port_rate_gbps: float = 400.0,
    gradient_bytes_per_node: int = 2_000_000_000,
) -> LeafOversubscriptionImpact:
    """Reproduce V8 Ch. 6 worked example: 16 down : 8 up at 400G -> 2:1 -> 40ms vs 80ms step."""
    down_bw = downlink_ports * port_rate_gbps
    up_bw = uplink_ports * port_rate_gbps
    ratio = round(down_bw / up_bw, 2)
    eff_node_gbps = round(up_bw / downlink_ports, 2)
    nonblock_gb_per_s = port_rate_gbps / 8.0  # 400 Gbps = 50 GB/s
    oversub_gb_per_s = eff_node_gbps / 8.0  # 200 Gbps = 25 GB/s
    grad_gb = gradient_bytes_per_node / 1e9
    t_nonblock_ms = round((grad_gb / nonblock_gb_per_s) * 1000.0, 2)
    t_oversub_ms = round((grad_gb / oversub_gb_per_s) * 1000.0, 2)
    return LeafOversubscriptionImpact(
        downlink_bw_gbps=down_bw,
        uplink_bw_gbps=up_bw,
        oversubscription_ratio=ratio,
        effective_node_bw_gbps=eff_node_gbps,
        nonblocking_step_ms=t_nonblock_ms,
        oversubscribed_step_ms=t_oversub_ms,
    )
