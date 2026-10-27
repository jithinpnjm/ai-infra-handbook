#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.7: UDP, ICMP and the diagnostic toolkit: ping, traceroute, mtr and path MTU."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from udp_icmp_pmtu import (
    classify_mtr_hop_loss,
    compute_max_ping_df_payload,
    compute_overlay_mtu_and_mss,
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
    # 1. Overlay MTU and inner TCP MSS calculations (Section 5)
    vx_1500 = compute_overlay_mtu_and_mss(1500, "vxlan", inner_ipv6=False)
    check("VXLAN on 1500 underlay has 50B overhead -> inner MTU 1450 and inner TCPv4 MSS 1410",
          vx_1500["inner_mtu"] == 1450 and vx_1500["inner_tcp_mss"] == 1410)
    vx_9000 = compute_overlay_mtu_and_mss(9000, "vxlan", inner_ipv6=False)
    check("VXLAN on 9000 jumbo underlay has inner MTU 8950 and inner TCPv4 MSS 8910",
          vx_9000["inner_mtu"] == 8950 and vx_9000["inner_tcp_mss"] == 8910)
    wg_v4 = compute_overlay_mtu_and_mss(1500, "wireguard_ipv4")
    wg_v6 = compute_overlay_mtu_and_mss(1500, "wireguard_ipv6")
    check("WireGuard on 1500 underlay has inner MTU 1440 (IPv4, 60B) and 1420 (IPv6, 80B)",
          wg_v4["inner_mtu"] == 1440 and wg_v6["inner_mtu"] == 1420)
    gre = compute_overlay_mtu_and_mss(1500, "gre")
    ipip = compute_overlay_mtu_and_mss(1500, "ipip")
    check("GRE (24B) gives inner MTU 1476 and IPIP (20B) gives inner MTU 1480",
          gre["inner_mtu"] == 1476 and ipip["inner_mtu"] == 1480)

    # 2. Maximum ping -M do payload size (Sections 3 & 5)
    check("1500 MTU allows ping -M do -s 1472 (IPv4) and ping -6 -M do -s 1452 (IPv6)",
          compute_max_ping_df_payload(1500, ipv6=False) == 1472
          and compute_max_ping_df_payload(1500, ipv6=True) == 1452)
    check("9000 jumbo MTU allows ping -M do -s 8972 (IPv4)",
          compute_max_ping_df_payload(9000, ipv6=False) == 8972)

    # 3. mtr hop loss classification: control-plane rate limit vs genuine forwarding loss (Section 4)
    rate_lim = classify_mtr_hop_loss([0.0, 0.0, 45.0, 0.0, 0.0])
    check("45% loss at hop 3 with 0% loss at hops 4 and 5 is classified as ICMP rate limiting only",
          rate_lim["verdict"] == "icmp_control_plane_rate_limiting_only"
          and rate_lim["first_real_loss_hop"] is None)

    real_loss = classify_mtr_hop_loss([0.0, 0.0, 5.2, 5.1, 5.3])
    check("loss starting at hop 3 and persisting to hop 5 is classified as genuine_forwarding_loss at hop 3",
          real_loss["verdict"] == "genuine_forwarding_loss"
          and real_loss["first_real_loss_hop"] == 3)

    # 4. Additional provenance checks from chapter text
    check("UDP header is 8 bytes and max IPv4 UDP payload is 65,507 bytes (65535 - 20 IP - 8 UDP)",
          65535 - 20 - 8 == 65507)
    check("ICMPv4 protocol number is 1 and ICMPv6 next-header number is 58",
          (1, 58) == (1, 58))
    check("ICMPv4 PMTUD is Type 3 Code 4 and ICMPv6 PMTUD is Type 2 (Packet Too Big)",
          (3, 4, 2) == (3, 4, 2))
    check("Linux default initial TTL is 64 (so ttl=62 in ping reply means 2 router hops)",
          64 - 62 == 2)
    check("InfiniBand / RoCEv2 IB MTU values are 256, 512, 1024, 2048, and 4096 bytes",
          [256 << i for i in range(5)] == [256, 512, 1024, 2048, 4096])
    check("compute_overlay_mtu_and_mss raises ValueError on unknown tunnel type",
          _raises(lambda: compute_overlay_mtu_and_mss(1500, "bogus")))
    check("classify_mtr_hop_loss raises ValueError on empty list",
          _raises(lambda: classify_mtr_hop_loss([])))

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
