#!/usr/bin/env python3
"""Chapter 12.4 model: PFC, ECN and DCQCN in depth.

Models the IEEE 802.1Qbb Priority Flow Control (PFC) frame format and quanta timing,
cable + transceiver + ASIC pipeline flight-time headroom buffer sizing (XOFF / XON),
Weighted Random Early Detection (WRED) ECN marking probability between K_min and K_max,
Data Center Quantized Congestion Notification (DCQCN) Reaction Point (RP), Congestion
Point (CP), and Notification Point (NP) closed-loop rate control, threshold ordering
validation (XON < K_min < K_max < XOFF), PFC Watchdog 3-stage state machine (detection,
drop/forward mitigation, restoration), Source Flow Control (SFC, IEEE 802.1Qdw),
Congestion Signaling (CSIG, draft-ravi-ippm-csig-01), and the production incident
evidence scenarios from:
  - *AI Data Center Network Design and Technologies* (`ai-data-center-network-design-and-technologies`),
    Chapter 7 ("7. RoCEv2 Transport and Congestion Management"):
    * Congestion Points (Figures 7-1..7-6): local leaf link, leaf-to-spine, spine-to-leaf,
      leaf-to-server, spine-to-super-spine, and super-spine-to-spine incast
    * ECN (Table 7-1, Figures 7-7..7-9): IP DSCP (6 bits) + ECN (2 bits: ECT and CE),
      00 (not ECN-capable, drop), 01 / 10 (ECT(1) / ECT(0)), 11 (CE), RoCEv2 UDP port 4791,
      CNP frame with ECN 01 and IB BTH opcode 129 (0x81 = 10000001)
    * PFC (IEEE 802.1Qbb, Figures 7-10..7-15): EtherType 0x8808, opcode 0x0101,
      destination MAC 01:80:C2:00:00:01 (64-byte frame on wire, e.g. source 10:0e:7e:b7:a7:1b,
      class enable vector 0x0008 for Priority 3), 16-bit pause time 0..65535 quanta
      (512 bit-times per quantum; 0 = XON un-pause), XOFF and XON thresholds, PFC Watchdog
      3 stages (Detection, Mitigation via Drop or Forward, Restoration)
    * DCQCN (Figures 7-16..7-17): threshold ordering XON < ECN < XOFF, 5-step hop-by-hop
      PFC propagation from egress pause to ingress XOFF breach
    * Source Flow Control (SFC, IEEE 802.1Qdw, Figure 7-18) and Congestion Signaling
      (CSIG, draft-ravi-ippm-csig-01, Figures 7-19..7-21)
  - `nvidia-devops` Volume 09:
    * `chapter-04-priority-flow-control.md` (`mlnx_qos -i swp12`: receive buffer 262,144 B,
      Priority 3 buffer 65,536 B, XOFF 49,152 B [75%], XON 32,768 B [50%], headroom 16,384 B [25%],
      hysteresis 16,384 B [25%]; Scenario 1 pause tree `swp7` `tx_pfc_prio3=0`,
      `rx_ecn_marked_prio3=2200` vs `swp3` `rx_pfc_prio3=41823`, `tx_pfc_prio3=41810`,
      `rx_ecn_marked_prio3=190`, `queue3_occupancy=98%`; Scenario 2 `prio0` + `prio3` PFC enabled)
    * `chapter-05-ecn-and-dcqcn.md` (`swp9` `rx_ecn_marked_prio3` 84,200 -> 84,512 [delta 312],
      `np_cnp_handled=298`, `np_ecn_marked_roce_packets=305`, `rp_byte_reset=1`; Scenario 1
      `rx_ecn_marked_prio3=412880`, `rx_pfc_prio3=93100`, `np_cnp_handled=409500`,
      `rp_current_rate=98 Gbps` on 100 Gbps link; Scenario 2 oscillation `t=0..4s`:
      `100 -> 12 -> 95 -> 11 -> 96 Gbps` with `np_cnp_handled` `40 -> 380 -> 2 -> 410 -> 3`)
    * `labs/lab-01-inventory-an-ai-ethernet-path.md`, `labs/lab-02-validate-roce-addressing-and-mtu.md`,
      `labs/lab-03-observe-pfc-and-ecn-under-load.md` (60s contention: `rx_ecn_marked_prio3=47829`,
      `rx_pfc_prio3=412`, `tx_pfc_prio3=14`, `rx_prio3_packets` 102,314 -> 51,234,892,
      `tx_prio3_packets` 89,621 -> 48,901,234, Sender A `89.2 Gbps` + Sender B `87.1 Gbps` = `176.3 Gbps`
      on 400 Gbps uplink), and `labs/lab-04-troubleshoot-a-roce-path.md` (`392 Gbps` healthy on
      `mlx5_0` in `2.1 s` vs `156 Gbps` degraded on `mlx5_1` in `8.2 s` with `24` `RETRY_EXC_ERR`
      and `rx_ecn_marked_prio3=142`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


# --- IEEE 802.1Qbb PFC and RoCEv2 / ECN protocol constants (ADC Ch 7 & Handbook 2.19) ---
PFC_ETHERTYPE: int = 0x8808
PFC_OPCODE: int = 0x0101
PFC_DEST_MAC: str = "01:80:C2:00:00:01"
PFC_EXAMPLE_SRC_MAC: str = "10:0e:7e:b7:a7:1b"
PFC_CLASS3_ENABLE_VECTOR: int = 0x0008  # Bit 3 enabled (1 << 3 = 8)
PFC_FRAME_WIRE_BYTES: int = 64
PFC_TIME_FIELD_OCTETS: int = 16  # 8 classes * 2 octets per class
PFC_MAX_QUANTA: int = 65535
PFC_BITS_PER_QUANTUM: int = 512
ROCEV2_UDP_PORT: int = 4791
CNP_BTH_OPCODE: int = 129  # 0x81 (binary 10000001)
IP_TOS_BITS: int = 8
DSCP_BITS: int = 6
ECN_BITS: int = 2
ROCE_DEFAULT_DSCP: int = 26
CNP_DEFAULT_DSCP: int = 48
EF_DSCP: int = 46  # tos 0xb8 >> 2 == 46 (V9 Ch 6)

# ECN 2-bit codepoints (Table 7-1 in ADC Ch 7)
ECN_NOT_ECT: str = "00"
ECN_ECT1: str = "01"
ECN_ECT0: str = "10"
ECN_CE: str = "11"


@dataclass(frozen=True)
class PfcPauseDuration:
    """IEEE 802.1Qbb PFC pause frame timing for a given line rate and quanta value."""

    quanta: int
    line_rate_gbps: float
    total_bit_times: int
    pause_duration_ns: float
    pause_duration_us: float
    is_unpause_xon: bool


def compute_pfc_pause_duration(quanta: int = PFC_MAX_QUANTA, line_rate_gbps: float = 400.0) -> PfcPauseDuration:
    """Compute PFC pause duration from quanta (`quanta * 512 / line_rate`, IEEE 802.1Qbb / ADC Ch 7).

    In IEEE 802.1Qbb, 1 quantum = 512 bit-times. At line rate R (in Gbps = bits/ns):
      duration_ns = (quanta * 512) / line_rate_gbps
      duration_us = duration_ns / 1000.0
    A quanta value of 0 is an explicit XON (un-pause) frame.
    """
    if not (0 <= quanta <= PFC_MAX_QUANTA):
        raise ValueError(f"quanta must be in 0..{PFC_MAX_QUANTA}, got {quanta}")
    if line_rate_gbps <= 0:
        raise ValueError("line_rate_gbps must be positive")

    total_bits = quanta * PFC_BITS_PER_QUANTUM
    duration_ns = round(total_bits / line_rate_gbps, 4)
    duration_us = round(duration_ns / 1000.0, 4)
    return PfcPauseDuration(
        quanta=quanta,
        line_rate_gbps=line_rate_gbps,
        total_bit_times=total_bits,
        pause_duration_ns=duration_ns,
        pause_duration_us=duration_us,
        is_unpause_xon=(quanta == 0),
    )


@dataclass(frozen=True)
class PfcBufferProfile:
    """Port and priority buffer profile (`mlnx_qos` & cable flight-time headroom model, V9 Ch 4 & ADC Ch 7)."""

    port_receive_buffer_bytes: int
    priority_buffer_bytes: int
    xoff_bytes: int
    xon_bytes: int
    headroom_bytes: int
    hysteresis_bytes: int
    xoff_pct: float
    xon_pct: float
    headroom_pct: float
    hysteresis_pct: float
    required_flight_headroom_bytes: int
    headroom_sufficient: bool


def calculate_flight_headroom_bytes(
    line_rate_gbps: float,
    cable_length_m: float,
    ns_per_meter: float = 5.0,
    transceiver_asic_delay_ns: float = 600.0,
    mtu_bytes: int = 9000,
    in_flight_mtu_packets: int = 2,
) -> int:
    """Compute minimum lossless headroom buffer to absorb in-flight bytes after XOFF triggers.

    Following Chapter 2.19 §6 and V9 Ch 4 ("Headroom and Threshold Design"):
      1. Round-trip propagation delay = 2 * cable_length_m * ns_per_meter
      2. Total reaction time (ns) = round_trip_cable_ns + transceiver_asic_delay_ns
      3. In-flight wire bytes during reaction window = (reaction_time_ns * line_rate_gbps) / 8
      4. Serialization allowance = in_flight_mtu_packets * mtu_bytes (e.g. 2 * MTU + PFC frame)
    """
    if line_rate_gbps <= 0 or cable_length_m < 0 or mtu_bytes <= 0:
        raise ValueError("Invalid link parameters for headroom calculation")

    rtt_cable_ns = 2.0 * cable_length_m * ns_per_meter
    total_delay_ns = rtt_cable_ns + transceiver_asic_delay_ns
    wire_bytes = (total_delay_ns * line_rate_gbps) / 8.0
    serialization_bytes = in_flight_mtu_packets * mtu_bytes + PFC_FRAME_WIRE_BYTES
    return int(round(wire_bytes + serialization_bytes))


def evaluate_pfc_buffer_profile(
    port_receive_buffer_bytes: int = 262_144,
    priority_buffer_bytes: int = 65_536,
    xoff_bytes: int = 49_152,
    xon_bytes: int = 32_768,
    required_flight_headroom_bytes: int = 16_384,
) -> PfcBufferProfile:
    """Evaluate a priority buffer profile (reproducing `mlnx_qos -i swp12` in V9 Ch 4)."""
    if not (0 < xon_bytes < xoff_bytes < priority_buffer_bytes <= port_receive_buffer_bytes):
        raise ValueError("Must satisfy 0 < XON < XOFF < priority_buffer <= port_receive_buffer")

    headroom = priority_buffer_bytes - xoff_bytes
    hysteresis = xoff_bytes - xon_bytes
    xoff_pct = round(xoff_bytes / priority_buffer_bytes * 100.0, 2)
    xon_pct = round(xon_bytes / priority_buffer_bytes * 100.0, 2)
    headroom_pct = round(headroom / priority_buffer_bytes * 100.0, 2)
    hysteresis_pct = round(hysteresis / priority_buffer_bytes * 100.0, 2)

    return PfcBufferProfile(
        port_receive_buffer_bytes=port_receive_buffer_bytes,
        priority_buffer_bytes=priority_buffer_bytes,
        xoff_bytes=xoff_bytes,
        xon_bytes=xon_bytes,
        headroom_bytes=headroom,
        hysteresis_bytes=hysteresis,
        xoff_pct=xoff_pct,
        xon_pct=xon_pct,
        headroom_pct=headroom_pct,
        hysteresis_pct=hysteresis_pct,
        required_flight_headroom_bytes=required_flight_headroom_bytes,
        headroom_sufficient=(headroom >= required_flight_headroom_bytes),
    )


def compute_wred_ecn_mark_probability(
    queue_bytes: float,
    k_min_bytes: float = 150_000.0,
    k_max_bytes: float = 1_500_000.0,
    p_max: float = 1.0,
) -> Tuple[float, str]:
    """Compute WRED ECN marking probability and zone (ADC Ch 7, V9 Ch 5 & V6 Ch 1).

    Zones (from V9 Ch 5 Figure "Tuning the ECN and PFC Thresholds"):
      - queue_bytes < k_min_bytes: 0.0 ("GREEN_ZONE_FREE_FLOW")
      - k_min_bytes <= queue_bytes < k_max_bytes:
          p = p_max * (queue_bytes - k_min_bytes) / (k_max_bytes - k_min_bytes)
          ("YELLOW_ZONE_PROBABILISTIC_ECN")
      - queue_bytes >= k_max_bytes: 1.0 ("RED_ZONE_100PCT_ECN_MARKING")
    """
    if not (0 < k_min_bytes < k_max_bytes) or not (0.0 < p_max <= 1.0):
        raise ValueError("Invalid WRED ECN threshold parameters")
    if queue_bytes < k_min_bytes:
        return 0.0, "GREEN_ZONE_FREE_FLOW"
    if queue_bytes >= k_max_bytes:
        return 1.0, "RED_ZONE_100PCT_ECN_MARKING"
    prob = p_max * (queue_bytes - k_min_bytes) / (k_max_bytes - k_min_bytes)
    return round(prob, 4), "YELLOW_ZONE_PROBABILISTIC_ECN"


@dataclass(frozen=True)
class ThresholdOrderingValidation:
    """Validation result for DCQCN queue threshold ordering (`XON < K_min < K_max < XOFF`)."""

    xon_bytes: int
    k_min_bytes: int
    k_max_bytes: int
    xoff_bytes: int
    buffer_limit_bytes: int
    is_valid: bool
    violation_reason: str


def validate_dcqcn_threshold_ordering(
    xon_bytes: int,
    k_min_bytes: int,
    k_max_bytes: int,
    xoff_bytes: int,
    buffer_limit_bytes: int,
) -> ThresholdOrderingValidation:
    """Validate DCQCN threshold ordering (`XON < ECN < XOFF` and `K_min < K_max < XOFF`, ADC Ch 7 & V9 Ch 5)."""
    if xon_bytes <= 0:
        return ThresholdOrderingValidation(xon_bytes, k_min_bytes, k_max_bytes, xoff_bytes, buffer_limit_bytes, False, "XON_MUST_BE_POSITIVE")
    if xon_bytes >= xoff_bytes:
        return ThresholdOrderingValidation(xon_bytes, k_min_bytes, k_max_bytes, xoff_bytes, buffer_limit_bytes, False, "XON_GE_XOFF_NO_HYSTERESIS")
    if k_min_bytes >= k_max_bytes:
        return ThresholdOrderingValidation(xon_bytes, k_min_bytes, k_max_bytes, xoff_bytes, buffer_limit_bytes, False, "KMIN_GE_KMAX")
    if k_max_bytes >= xoff_bytes:
        return ThresholdOrderingValidation(xon_bytes, k_min_bytes, k_max_bytes, xoff_bytes, buffer_limit_bytes, False, "ECN_KMAX_GE_PFC_XOFF_PFC_FIRES_BEFORE_FULL_ECN")
    if xoff_bytes >= buffer_limit_bytes:
        return ThresholdOrderingValidation(xon_bytes, k_min_bytes, k_max_bytes, xoff_bytes, buffer_limit_bytes, False, "XOFF_AT_BUFFER_MAX_NO_HEADROOM")
    return ThresholdOrderingValidation(xon_bytes, k_min_bytes, k_max_bytes, xoff_bytes, buffer_limit_bytes, True, "VALID_DCQCN_ORDERING")


@dataclass(frozen=True)
class DcqcnRpState:
    """DCQCN Reaction Point (RP) state at the sender NIC."""

    current_rate_gbps: float
    target_rate_gbps: float
    alpha: float
    stage: str


def dcqcn_rp_rate_cut(
    current_rate_gbps: float,
    alpha: float,
    g: float = 0.0625,
) -> DcqcnRpState:
    """Apply DCQCN Reaction Point (RP) rate cut upon receiving a CNP (SIGCOMM 2015 / V9 Ch 5).

    On CNP arrival:
      R_t = R_c                           (save current rate as target rate for recovery)
      R_c = R_c * (1 - alpha / 2)         (multiplicative rate cut, at most 50% when alpha=1.0)
      alpha = (1 - g) * alpha + g * 1.0   (EWMA congestion estimate update toward 1.0)
    """
    if current_rate_gbps <= 0 or not (0.0 <= alpha <= 1.0) or not (0.0 < g <= 1.0):
        raise ValueError("Invalid DCQCN RP parameters")
    target_rate = round(current_rate_gbps, 4)
    new_rate = round(current_rate_gbps * (1.0 - alpha / 2.0), 4)
    new_alpha = round((1.0 - g) * alpha + g * 1.0, 6)
    return DcqcnRpState(
        current_rate_gbps=new_rate,
        target_rate_gbps=target_rate,
        alpha=new_alpha,
        stage="RATE_CUT_ON_CNP",
    )


def dcqcn_rp_recover_step(
    current_rate_gbps: float,
    target_rate_gbps: float,
    alpha: float,
    line_rate_gbps: float = 400.0,
    r_ai_gbps: float = 4.0,
    r_hai_gbps: float = 40.0,
    step_index: int = 1,
    fast_recovery_threshold_f: int = 5,
    g: float = 0.0625,
) -> DcqcnRpState:
    """Apply one DCQCN timer/byte-counter recovery step when no CNPs arrive.

    Stages:
      1. Fast Recovery (step_index <= F):
           R_c = (R_c + R_t) / 2
      2. Additive Increase (step_index > F, single counter exceeded):
           R_t = min(line_rate, R_t + R_AI)
           R_c = (R_c + R_t) / 2
      3. Hyper-Additive Increase (both timer and byte counter exceeded > F):
           i = step_index - F
           R_t = min(line_rate, R_t + i * R_HAI)
           R_c = (R_c + R_t) / 2
    Alpha decays via EWMA: alpha = (1 - g) * alpha.
    """
    new_alpha = round((1.0 - g) * alpha, 6)
    if step_index <= fast_recovery_threshold_f:
        new_target = target_rate_gbps
        stage = "FAST_RECOVERY"
    elif step_index <= fast_recovery_threshold_f + 2:
        new_target = min(line_rate_gbps, target_rate_gbps + r_ai_gbps)
        stage = "ADDITIVE_INCREASE"
    else:
        i = step_index - (fast_recovery_threshold_f + 2)
        new_target = min(line_rate_gbps, target_rate_gbps + i * r_hai_gbps)
        stage = "HYPER_ADDITIVE_INCREASE"

    new_current = min(line_rate_gbps, round((current_rate_gbps + new_target) / 2.0, 4))
    return DcqcnRpState(
        current_rate_gbps=new_current,
        target_rate_gbps=round(new_target, 4),
        alpha=new_alpha,
        stage=stage,
    )


@dataclass(frozen=True)
class PfcWatchdogDecision:
    """PFC Watchdog 3-stage state machine result (Detection, Mitigation, Restoration, ADC Ch 7)."""

    state: str
    mitigation_mode: str
    discard_existing_queue_packets: bool
    discard_new_queue_packets: bool
    discard_incoming_pause_frames: bool
    forward_packets_ignoring_pfc: bool
    lossless_restored: bool


def evaluate_pfc_watchdog(
    paused_duration_ms: float,
    detection_threshold_ms: float = 100.0,
    mitigation_mode: str = "drop",
    quiet_duration_ms: float = 0.0,
    restoration_threshold_ms: float = 200.0,
) -> PfcWatchdogDecision:
    """Evaluate the 3-stage PFC Watchdog (ADC Ch 7 Figure 7-15 & Handbook 2.19 §6).

    1. Detection: If a port/queue remains in a PFC storm for >= detection_threshold_ms,
       mark the port as being in a PFC storm.
    2. Mitigation:
       - "drop" (most common): (a) discard all packets already in the output queue,
         (b) discard any new packets meant for the output queue, and (c) discard new
         packets/pause frames from the same priority group so the pause frame does not
         propagate upstream (e.g. Spine1 does not pause LeafA).
       - "forward": ignore received PFC frames and forward all packets already in or
         entering the queue.
    3. Restoration: When received PFC pause frames stay below the threshold for
       >= restoration_threshold_ms, un-pause traffic and resume lossless Ethernet.
    """
    if mitigation_mode not in ("drop", "forward"):
        raise ValueError("mitigation_mode must be 'drop' or 'forward'")

    if paused_duration_ms < detection_threshold_ms:
        return PfcWatchdogDecision(
            state="NORMAL_LOSSLESS",
            mitigation_mode=mitigation_mode,
            discard_existing_queue_packets=False,
            discard_new_queue_packets=False,
            discard_incoming_pause_frames=False,
            forward_packets_ignoring_pfc=False,
            lossless_restored=True,
        )

    if quiet_duration_ms >= restoration_threshold_ms:
        return PfcWatchdogDecision(
            state="RESTORATION_COMPLETE",
            mitigation_mode=mitigation_mode,
            discard_existing_queue_packets=False,
            discard_new_queue_packets=False,
            discard_incoming_pause_frames=False,
            forward_packets_ignoring_pfc=False,
            lossless_restored=True,
        )

    if mitigation_mode == "drop":
        return PfcWatchdogDecision(
            state="MITIGATION_ACTIVE_DROP",
            mitigation_mode="drop",
            discard_existing_queue_packets=True,
            discard_new_queue_packets=True,
            discard_incoming_pause_frames=True,
            forward_packets_ignoring_pfc=False,
            lossless_restored=False,
        )
    return PfcWatchdogDecision(
        state="MITIGATION_ACTIVE_FORWARD",
        mitigation_mode="forward",
        discard_existing_queue_packets=False,
        discard_new_queue_packets=False,
        discard_incoming_pause_frames=True,
        forward_packets_ignoring_pfc=True,
        lossless_restored=False,
    )


def trace_pause_tree_origin(port_counters: List[Dict[str, int | str]]) -> str:
    """Identify the origin vs relay hop in a PFC pause tree (V9 Ch 4 Scenario 1 & Interview Q2).

    - A switch port where `rx_pfc > 0` and `tx_pfc > 0` (e.g. `swp3`: `rx_pfc_prio3=41823`,
      `tx_pfc_prio3=41810`, `queue3_occupancy=98%`) is a relay hop caught in the middle of a
      pause chain.
    - Walking in the `rx_pfc` direction until finding the downstream hop where `rx_pfc > 0`
      and `tx_pfc == 0` (or the congested receiver-facing egress generating the initial pause)
      identifies the root of the pause tree.
    """
    for entry in port_counters:
        rx_pfc = int(entry.get("rx_pfc", 0))
        tx_pfc = int(entry.get("tx_pfc", 0))
        if rx_pfc > 0 and tx_pfc == 0:
            return str(entry["port"])
    for entry in port_counters:
        if int(entry.get("rx_ecn_marked", 0)) > 1000 and int(entry.get("tx_pfc", 0)) == 0:
            return str(entry["port"])
    return "UNKNOWN_ORIGIN"


def diagnose_dcqcn_telemetry(
    switch_ecn_marks_delta: int,
    switch_pfc_rx_delta: int,
    np_cnp_handled_delta: int,
    rp_current_rate_gbps: float,
    line_rate_gbps: float = 100.0,
    rate_samples_gbps: List[float] | None = None,
) -> str:
    """Diagnose ECN/DCQCN operational state from switch and NIC counters (V9 Ch 5 Scenarios 1-4)."""
    if rate_samples_gbps and len(rate_samples_gbps) >= 4:
        swings = [abs(rate_samples_gbps[i] - rate_samples_gbps[i - 1]) for i in range(1, len(rate_samples_gbps))]
        if max(swings) >= 0.70 * line_rate_gbps and min(rate_samples_gbps) <= 0.20 * line_rate_gbps:
            return "SCENARIO_2_SYNCHRONIZED_RATE_OSCILLATION"

    if switch_ecn_marks_delta > 0 and np_cnp_handled_delta == 0:
        return "SCENARIO_3_BROKEN_FEEDBACK_LOOP_NO_SENDER_RESPONSE"

    if (
        switch_ecn_marks_delta > 10_000
        and switch_pfc_rx_delta > 10_000
        and np_cnp_handled_delta >= 0.90 * switch_ecn_marks_delta
        and rp_current_rate_gbps >= 0.95 * line_rate_gbps
    ):
        return "SCENARIO_1_WEAK_RP_RESPONSE_OR_HARD_CAPACITY_BOTTLENECK"

    if (
        switch_ecn_marks_delta > 0
        and abs(switch_ecn_marks_delta - np_cnp_handled_delta) <= max(50, int(0.15 * switch_ecn_marks_delta))
        and switch_pfc_rx_delta < 1000
    ):
        return "HEALTHY_CLOSED_LOOP_CONTAINED"

    return "UNCLASSIFIED_STATE"
