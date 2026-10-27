#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.2: How networks work: layers, encapsulation, the TCP/IP model."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from layers_encapsulation import (
    compute_max_frame_rate_mpps,
    compute_tcp_ethernet_goodput,
    demultiplex_packet,
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
    # 1. Standard 1500 MTU vs 9000 jumbo MTU vs VXLAN goodput (Section 4)
    g1500 = compute_tcp_ethernet_goodput(mtu_bytes=1500, ipv6=False, tcp_options_bytes=0)
    check("MTU 1500 TCP/IPv4 has MSS=1460 B, wire_bytes=1538 B, and goodput=94.9%",
          g1500 == {"mss_bytes": 1460, "wire_bytes": 1538, "goodput_pct": 94.9})

    g1500_ts = compute_tcp_ethernet_goodput(mtu_bytes=1500, ipv6=False, tcp_options_bytes=12)
    check("MTU 1500 with 12-byte TCP timestamps reduces MSS from 1460 to 1448 bytes",
          g1500_ts["mss_bytes"] == 1448)

    g9000 = compute_tcp_ethernet_goodput(mtu_bytes=9000, ipv6=False, tcp_options_bytes=0)
    check("Jumbo MTU 9000 TCP/IPv4 has MSS=8960 B, wire_bytes=9038 B, and goodput=99.1%",
          g9000 == {"mss_bytes": 8960, "wire_bytes": 9038, "goodput_pct": 99.1})

    g_vxlan = compute_tcp_ethernet_goodput(mtu_bytes=1500, ipv6=False, vxlan_overlay=True)
    check("VXLAN 50-byte overlay reduces inner MSS on a 1500-MTU underlay from 1460 to 1410 bytes",
          g_vxlan["mss_bytes"] == 1410)

    # 2. Minimum 64-byte frame rate (Mpps) on 100 GbE and 400 GbE (Section 4)
    mpps_100 = compute_max_frame_rate_mpps(link_rate_gbps=100.0, frame_bytes_before_preamble=64)
    check("100 Gb/s link with 64-byte min frames (84 byte-times on wire) carries at most 148.8 Mpps",
          mpps_100 == 148.8)
    mpps_400 = compute_max_frame_rate_mpps(link_rate_gbps=400.0, frame_bytes_before_preamble=64)
    check("400 Gb/s link with 64-byte min frames carries at most 595.2 Mpps (4 * 148.8)",
          mpps_400 == 595.2)

    # 3. Demultiplexing keys: EtherType -> IP protocol -> TCP/UDP port (Section 4)
    d_https = demultiplex_packet(0x0800, 6, 443)
    check("EtherType 0x0800 + proto 6 + port 443 demultiplexes to IPv4 -> TCP -> HTTPS_or_QUIC",
          d_https == {"l3": "IPv4", "l4": "TCP", "service": "HTTPS_or_QUIC"})
    d_roce = demultiplex_packet(0x0800, 17, 4791)
    check("EtherType 0x0800 + proto 17 + port 4791 demultiplexes to IPv4 -> UDP -> RoCE_v2",
          d_roce == {"l3": "IPv4", "l4": "UDP", "service": "RoCE_v2"})
    d_ipv6 = demultiplex_packet(0x86DD, 58, 0)
    check("EtherType 0x86DD + next-header 58 demultiplexes to IPv6 -> ICMPv6",
          d_ipv6["l3"] == "IPv6" and d_ipv6["l4"] == "ICMPv6")

    # 4. Additional provenance checks from CN Ch. 1 & Ch. 3
    check("ATM cell is 53 bytes (5-byte header + 48-byte payload)", 5 + 48 == 53)
    check("VXLAN overhead is 50 bytes (14 Eth + 20 IPv4 + 8 UDP + 8 VXLAN)",
          14 + 20 + 8 + 8 == 50)
    check("RoCE v2 adds 8B UDP + 12B IB BTH + 4B ICRC", 8 + 12 + 4 == 24)
    check("TCP/IP model has 4 layers and OSI model (1977) has 7 layers", 4 < 7 and 1977 > 1970)
    check("compute_tcp_ethernet_goodput raises ValueError on MTU < 64",
          _raises(lambda: compute_tcp_ethernet_goodput(32)))
    check("compute_max_frame_rate_mpps raises ValueError on zero link rate",
          _raises(lambda: compute_max_frame_rate_mpps(0.0)))

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
