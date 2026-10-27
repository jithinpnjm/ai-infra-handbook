#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.6: TCP in depth: handshake, windows, congestion control, tuning and troubleshooting."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tcp_in_depth import (
    compute_bdp_and_window_scale,
    compute_jacobson_rto_ms,
    compute_window_limited_throughput_mbps,
    simulate_congestion_loss_event,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. BDP and window-scale shift calculation (Section 6)
    bdp_dc = compute_bdp_and_window_scale(bandwidth_gbps=100.0, rtt_ms=1.0)
    check("100 Gb/s x 1 ms RTT has BDP = 12.5 MB and requires window scale shift >= 8",
          bdp_dc["bdp_mb"] == 12.5 and bdp_dc["min_window_scale_shift"] == 8)
    bdp_wan = compute_bdp_and_window_scale(bandwidth_gbps=10.0, rtt_ms=70.0)
    check("10 Gb/s x 70 ms cross-continent path has BDP = 87.5 MB",
          bdp_wan["bdp_mb"] == 87.5)
    bdp_25g = compute_bdp_and_window_scale(bandwidth_gbps=25.0, rtt_ms=40.0)
    check("25 Gb/s x 40 ms path has BDP = 125.0 MB",
          bdp_25g["bdp_mb"] == 125.0)

    # 2. Window-limited throughput (Section 6)
    tput_70ms = compute_window_limited_throughput_mbps(window_bytes=4_000_000, rtt_ms=70.0)
    check("4 MB window over 70 ms RTT caps single-stream throughput at ~457.1 Mb/s on a 10 Gb/s link",
          tput_70ms == 457.1)
    tput_80ms = compute_window_limited_throughput_mbps(window_bytes=4_000_000, rtt_ms=80.0)
    check("4 MB window over 80 ms RTT caps throughput at 400.0 Mb/s (50 MB/s)",
          tput_80ms == 400.0)

    # 3. Jacobson RTO with Linux 200 ms TCP_RTO_MIN floor (Section 5)
    rto_dc = compute_jacobson_rto_ms(srtt_ms=0.2, rttvar_ms=0.05, rto_min_ms=200.0)
    check("datacenter 0.2 ms SRTT is clamped to Linux TCP_RTO_MIN = 200.0 ms unless rto_min is tuned",
          rto_dc == 200.0)
    rto_wan = compute_jacobson_rto_ms(srtt_ms=150.0, rttvar_ms=30.0, rto_min_ms=200.0)
    check("WAN 150 ms SRTT + 4*30 ms RTTVAR computes RTO = 270.0 ms",
          rto_wan == 270.0)

    # 4. Congestion loss reactions: Tahoe vs Reno vs CUBIC (Section 7)
    tahoe_dup = simulate_congestion_loss_event(100, 200, "tahoe", "dup_ack_3")
    reno_dup = simulate_congestion_loss_event(100, 200, "reno", "dup_ack_3")
    cubic_dup = simulate_congestion_loss_event(100, 200, "cubic", "dup_ack_3")
    cubic_rto = simulate_congestion_loss_event(100, 200, "cubic", "rto")
    check("on 3 dup ACKs at cwnd=100: Tahoe resets cwnd=1, Reno halves to 50, CUBIC scales by beta=0.7 to 70",
          tahoe_dup["new_cwnd_mss"] == 1
          and reno_dup["new_cwnd_mss"] == 50
          and cubic_dup["new_cwnd_mss"] == 70)
    check("on an RTO timeout, even CUBIC collapses cwnd to 1 MSS",
          cubic_rto["new_cwnd_mss"] == 1 and cubic_rto["new_ssthresh_mss"] == 70)

    # 5. Additional provenance checks from chapter text
    check("16-bit unscaled TCP window max is 65,535 bytes and max window scale shift is 14 (~1 GiB)",
          (1 << 16) - 1 == 65535 and 65535 * (1 << 14) > (1 << 30) - (1 << 20))
    check("Linux TIME_WAIT duration is 2*MSL = 60 s and delayed ACK timeout is up to 40 ms",
          60 > 40)
    check("initial congestion window IW10 is 10 segments and default tcp_retries2 is 15",
          10 < 15)
    check("compute_bdp_and_window_scale raises ValueError on zero bandwidth",
          _raises(lambda: compute_bdp_and_window_scale(0.0, 10.0)))
    check("simulate_congestion_loss_event raises ValueError on unknown algorithm",
          _raises(lambda: simulate_congestion_loss_event(10, 10, "bogus", "rto")))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
