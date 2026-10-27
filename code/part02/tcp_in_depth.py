"""Chapter 2.6 model: Bandwidth-Delay Product (BDP = bandwidth * RTT) and
window-limited throughput ceiling (window / RTT), TCP window-scale shift
factor calculation, Jacobson RTO (SRTT + 4 * RTTVAR with 200 ms Linux floor),
and effective send window min(cwnd, rwnd) under loss/recovery.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 2 ("Data Transport": marshaling grammars fixed/TLV/dictionary, error
  detection/correction ARQ vs FEC, multiplexing, addressing, flow control),
  Chapter 3 (DoD/OSI/RINA models, connection-oriented vs connectionless), and
  Chapter 5 (TCP header, sliding window, fast retransmit, SACK, QUIC).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9.
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 10 ("Network": SYN/accept queues, TCP buffers, CUBIC/BBR, Nagle/delayed ACK).
"""
import math
from typing import Dict


def compute_bdp_and_window_scale(
    bandwidth_gbps: float,
    rtt_ms: float,
) -> Dict[str, object]:
    """Compute BDP in bytes and MB (decimal 10^6), plus minimum TCP window-scale shift (0..14)."""
    if bandwidth_gbps <= 0 or rtt_ms <= 0:
        raise ValueError("bandwidth_gbps and rtt_ms must be positive")
    rtt_s = rtt_ms / 1000.0
    bdp_bytes = int(round((bandwidth_gbps * 1e9 / 8.0) * rtt_s))
    bdp_mb = round(bdp_bytes / 1e6, 3)
    if bdp_bytes <= 65535:
        ws_shift = 0
    else:
        ws_shift = min(14, int(math.ceil(math.log2(bdp_bytes / 65535.0))))
    return {
        "bdp_bytes": bdp_bytes,
        "bdp_mb": bdp_mb,
        "min_window_scale_shift": ws_shift,
    }


def compute_window_limited_throughput_mbps(window_bytes: int, rtt_ms: float) -> float:
    """Compute maximum single-stream TCP throughput in Mb/s (10^6 bits/s) given window_bytes and rtt_ms."""
    if window_bytes <= 0 or rtt_ms <= 0:
        raise ValueError("window_bytes and rtt_ms must be positive")
    rtt_s = rtt_ms / 1000.0
    bits_per_sec = (window_bytes * 8.0) / rtt_s
    return round(bits_per_sec / 1e6, 1)


def compute_jacobson_rto_ms(
    srtt_ms: float,
    rttvar_ms: float,
    rto_min_ms: float = 200.0,
    rto_max_ms: float = 120000.0,
) -> float:
    """Compute TCP RTO = clamp(SRTT + 4 * RTTVAR, rto_min_ms, rto_max_ms)."""
    if srtt_ms < 0 or rttvar_ms < 0 or rto_min_ms <= 0:
        raise ValueError("Invalid RTT/RTO parameters")
    raw = srtt_ms + 4.0 * rttvar_ms
    return round(max(rto_min_ms, min(rto_max_ms, raw)), 2)


def simulate_congestion_loss_event(
    cwnd_mss: int,
    rwnd_mss: int,
    algorithm: str,
    loss_type: str,
) -> Dict[str, int]:
    """Model cwnd and ssthresh after 'dup_ack_3' (fast retransmit) or 'rto' for Tahoe, Reno, or CUBIC."""
    if cwnd_mss <= 0 or rwnd_mss <= 0:
        raise ValueError("Windows must be positive")
    if algorithm == "cubic":
        new_ssthresh = max(2, int(cwnd_mss * 0.7))
    elif algorithm in {"reno", "tahoe"}:
        new_ssthresh = max(2, cwnd_mss // 2)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    if loss_type == "rto":
        new_cwnd = 1
    elif loss_type == "dup_ack_3":
        new_cwnd = 1 if algorithm == "tahoe" else new_ssthresh
    else:
        raise ValueError(f"Unknown loss_type: {loss_type}")

    return {
        "new_ssthresh_mss": new_ssthresh,
        "new_cwnd_mss": new_cwnd,
        "effective_flight_mss": min(new_cwnd, rwnd_mss),
    }
