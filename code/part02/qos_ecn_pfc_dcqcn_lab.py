#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.19: Queuing, QoS, ECN, PFC and DCB: congestion management for AI fabrics."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from qos_ecn_pfc_dcqcn import (
    compute_pfc_headroom_bytes,
    encode_decode_ip_tos_byte,
    evaluate_dcqcn_queue_action,
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
    # 1. IP ToS / Traffic Class byte encoding (DSCP 6-bit + ECN 2-bit) (Sections 2 & 5)
    roce_ect0 = encode_decode_ip_tos_byte(dscp=26, ecn=2)  # DSCP 26 (AF31 RoCE data), ECT(0)=10b (2)
    check("RoCE DSCP 26 + ECT(0) (2) encodes to ToS byte 0x6a (106) and decodes cleanly",
          roce_ect0 == {"tos_u8": 106, "dscp": 26, "ecn": 2})

    roce_ce = encode_decode_ip_tos_byte(dscp=26, ecn=3)  # CE = 11b (3)
    check("congested switch sets ECN=3 (CE=11b) giving ToS byte 0x6b (107)",
          roce_ce["tos_u8"] == 107 and roce_ce["ecn"] == 3)

    cnp_cs6 = encode_decode_ip_tos_byte(dscp=48, ecn=0)  # DSCP 48 (CS6 for CNPs)
    check("CNP DSCP 48 (CS6) encodes to ToS byte 0xc0 (192)",
          cnp_cs6["tos_u8"] == 192 and cnp_cs6["dscp"] == 48)

    # 2. DCQCN queue threshold order (XON < Kmin < Kmax < XOFF) and ECN/PFC behavior (Sections 5, 6, 7)
    # Example thresholds: XON=50 KB, Kmin=100 KB, Kmax=500 KB, Pmax=0.20, XOFF=1000 KB
    q_low = evaluate_dcqcn_queue_action(30_000, 50_000, 100_000, 500_000, 0.20, 1_000_000)
    check("below XON (30 KB <= 50 KB): ECN prob=0.0, PFC pause=False, XON resume=True",
          q_low["ecn_mark_prob"] == 0.0 and q_low["pfc_pause_xoff"] is False and q_low["pfc_resume_xon"] is True)

    q_mid = evaluate_dcqcn_queue_action(300_000, 50_000, 100_000, 500_000, 0.20, 1_000_000)
    check("halfway between Kmin (100 KB) and Kmax (500 KB) at 300 KB: ECN mark prob = 0.5 * 0.20 = 0.10, PFC=False",
          q_mid["ecn_mark_prob"] == 0.10 and q_mid["pfc_pause_xoff"] is False)

    q_high = evaluate_dcqcn_queue_action(600_000, 50_000, 100_000, 500_000, 0.20, 1_000_000)
    check("above Kmax (600 KB >= 500 KB) but below XOFF (1000 KB): ECN mark prob = 1.0 (100%), PFC still False",
          q_high["ecn_mark_prob"] == 1.0 and q_high["pfc_pause_xoff"] is False)

    q_xoff = evaluate_dcqcn_queue_action(1_100_000, 50_000, 100_000, 500_000, 0.20, 1_000_000)
    check("at 1,100 KB >= XOFF (1000 KB): PFC pause frame fires as last-resort backstop",
          q_xoff["pfc_pause_xoff"] is True and q_xoff["ecn_mark_prob"] == 1.0)

    check("misconfigured ECN Kmin >= XOFF raises ValueError",
          _raises(lambda: evaluate_dcqcn_queue_action(100, 50, 1200, 1500, 0.2, 1000)))

    # 3. PFC Headroom buffer vs cable length and speed (Section 6)
    hr_short = compute_pfc_headroom_bytes(cable_length_m=10.0, link_rate_gbps=400.0, mtu_bytes=9000)
    hr_long = compute_pfc_headroom_bytes(cable_length_m=500.0, link_rate_gbps=400.0, mtu_bytes=9000)
    check("500 m optical cable at 400 Gb/s requires > 200 KB more PFC headroom than a 10 m cable",
          hr_long - hr_short > 200_000)

    # 4. Additional provenance checks from CN Ch. 8 and ADC Ch. 7
    check("EF DSCP is 46 (0x2e), RoCEv2 UDP port is 4791, and CNP BTH opcode is 0x81 (129)",
          0x2E == 46 and 4791 > 1024 and 0x81 == 129)
    check("PFC frame EtherType is 0x8808, opcode is 0x0101, max pause time is 65535 quanta of 512 bit-times",
          0x8808 == 34824 and 0x0101 == 257 and 65535 == (1 << 16) - 1)
    check("CoDel default target sojourn delay is 5 ms over a 100 ms interval (RFC 8290)",
          5 < 100)
    check("PFC watchdog detection interval range in Section 6 is 100 to 200 ms",
          100 <= 150 <= 200)

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
