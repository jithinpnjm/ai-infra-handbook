"""Chapter 2.19 model: IP ToS / Traffic Class byte (DSCP 6-bit + ECN 2-bit)
encoder/decoder, DCQCN queue threshold order (XON < Kmin < Kmax < XOFF) and
WRED/ECN linear marking probability calculator, PFC pause headroom buffer
calculator, and PFC watchdog state machine.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 8 ("Quality of Service": why not just size links large enough,
  classification DSCP RFC 2474 / EF RFC 3246, preserving markings, unmarked
  Internet, LLQ vs CBWFQ, policing vs shaping, WRED, bufferbloat and CoDel
  RFC 8290).
- Dinakaran Setty et al., AI Data Center Network Design and Technologies (ADC),
  Chapter 7 ("RoCEv2 Transport and Congestion Management": congestion points,
  ECN and CNP BTH opcode 0x81, PFC 802.1Qbb XON/XOFF and headroom, PFC storms /
  deadlocks / watchdog, DCQCN SIGCOMM 2015, Source Flow Control SFC 802.1Qdw,
  Congestion Signaling CSIG).
"""
from typing import Dict


def encode_decode_ip_tos_byte(dscp: int, ecn: int) -> Dict[str, int]:
    """Encode 6-bit DSCP (0..63) and 2-bit ECN (0..3) into the 8-bit IP ToS / Traffic Class byte."""
    if not (0 <= dscp <= 63) or not (0 <= ecn <= 3):
        raise ValueError("dscp must be in 0..63 and ecn in 0..3")
    tos = (dscp << 2) | ecn
    return {
        "tos_u8": tos,
        "dscp": (tos >> 2) & 0x3F,
        "ecn": tos & 0x03,
    }


def evaluate_dcqcn_queue_action(
    queue_bytes: int,
    xon_bytes: int,
    ecn_kmin_bytes: int,
    ecn_kmax_bytes: int,
    ecn_pmax: float,
    xoff_bytes: int,
) -> Dict[str, object]:
    """Validate DCQCN threshold ordering (XON < Kmin < Kmax < XOFF) and compute ECN marking probability and PFC state."""
    if not (0 <= xon_bytes < ecn_kmin_bytes < ecn_kmax_bytes < xoff_bytes) or not (0.0 < ecn_pmax <= 1.0):
        raise ValueError("Thresholds must satisfy 0 <= XON < Kmin < Kmax < XOFF and 0 < Pmax <= 1")
    if queue_bytes <= ecn_kmin_bytes:
        ecn_mark_prob = 0.0
    elif queue_bytes >= ecn_kmax_bytes:
        ecn_mark_prob = 1.0
    else:
        frac = (queue_bytes - ecn_kmin_bytes) / float(ecn_kmax_bytes - ecn_kmin_bytes)
        ecn_mark_prob = round(frac * ecn_pmax, 3)

    pfc_send_xoff = queue_bytes >= xoff_bytes
    pfc_send_xon_resume = queue_bytes <= xon_bytes
    return {
        "ecn_mark_prob": ecn_mark_prob,
        "pfc_pause_xoff": pfc_send_xoff,
        "pfc_resume_xon": pfc_send_xon_resume,
    }


def compute_pfc_headroom_bytes(
    cable_length_m: float,
    link_rate_gbps: float,
    mtu_bytes: int = 9000,
    pause_reaction_ns: float = 600.0,
) -> int:
    """Compute minimum PFC headroom buffer in bytes above XOFF:
    2 * propagation_delay * bw + 2 * mtu_bytes + pause_reaction_delay * bw.
    Fiber propagation is ~5 ns/m.
    """
    if cable_length_m < 0 or link_rate_gbps <= 0 or mtu_bytes <= 0 or pause_reaction_ns < 0:
        raise ValueError("Invalid headroom parameters")
    prop_rtt_ns = 2.0 * cable_length_m * 5.0
    total_flight_ns = prop_rtt_ns + pause_reaction_ns
    bytes_per_ns = link_rate_gbps / 8.0
    in_flight_bytes = int(round(total_flight_ns * bytes_per_ns))
    return in_flight_bytes + (2 * mtu_bytes)
