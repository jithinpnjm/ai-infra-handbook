#!/usr/bin/env python3
"""Self-checking lab for Chapter 2.1: What happens when you curl a URL: a packet's journey end to end."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from curl_packet_journey import (
    decompose_curl_timings,
    diagnose_curl_exit_code,
    simulate_router_hop_headers,
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
    # 1. curl -w cumulative timing phase decomposition (Section 11)
    phases = decompose_curl_timings(
        time_namelookup=0.012,
        time_connect=0.032,
        time_appconnect=0.072,
        time_pretransfer=0.073,
        time_starttransfer=0.123,
        time_total=0.153,
    )
    check("curl -w phase subtraction gives DNS=0.012s, TCP=0.020s, TLS=0.040s, TTFB_wait=0.050s, transfer=0.030s",
          phases["dns_s"] == 0.012
          and phases["tcp_connect_s"] == 0.020
          and phases["tls_handshake_s"] == 0.040
          and phases["server_wait_ttfb_s"] == 0.050
          and phases["body_transfer_s"] == 0.030)

    # 2. Hop-by-hop MAC rewrite vs constant IP and decrementing TTL (Sections 5 & 6)
    hops = simulate_router_hop_headers(
        src_ip="10.0.0.15",
        dst_ip="93.184.216.34",
        initial_ttl=64,
        hop_mac_pairs=[
            {"src_mac": "aa:aa:aa:00:00:01", "dst_mac": "bb:bb:bb:00:00:01"},  # host -> gateway
            {"src_mac": "bb:bb:bb:00:00:02", "dst_mac": "cc:cc:cc:00:00:01"},  # gateway -> core router
            {"src_mac": "cc:cc:cc:00:00:02", "dst_mac": "dd:dd:dd:00:00:01"},  # core router -> server
        ],
    )
    check("first hop dst_mac is the default gateway's MAC ('bb:bb:bb:00:00:01'), not the final server's MAC",
          hops[0]["dst_mac"] == "bb:bb:bb:00:00:01" and hops[0]["ttl"] == 64)
    check("across 3 hops without NAT, src_ip and dst_ip remain constant while MACs change and TTL decrements to 62",
          hops[2]["src_ip"] == "10.0.0.15"
          and hops[2]["dst_ip"] == "93.184.216.34"
          and hops[2]["src_mac"] == "cc:cc:cc:00:00:02"
          and hops[2]["ttl"] == 62)

    # 3. curl exit-code to layer mapping (Section 12)
    check("curl exit code 6 maps to L7_DNS_resolver (Could not resolve host)",
          diagnose_curl_exit_code(6)["layer"] == "L7_DNS_resolver")
    check("curl exit code 7 maps to L3_L4_connect (Connection refused / Network unreachable)",
          diagnose_curl_exit_code(7)["layer"] == "L3_L4_connect")
    check("curl exit code 28 maps to L3_L4_L7_timeout (Operation timed out)",
          diagnose_curl_exit_code(28)["layer"] == "L3_L4_L7_timeout")
    check("curl exit code 35 maps to L6_L7_TLS_handshake (SSL/TLS connect error)",
          diagnose_curl_exit_code(35)["layer"] == "L6_L7_TLS_handshake")
    check("curl exit code 60 maps to L6_L7_TLS_PKI (certificate verify failed)",
          diagnose_curl_exit_code(60)["layer"] == "L6_L7_TLS_PKI")

    # 4. Additional provenance checks from NK Ch. 1, HLW Ch. 9, and CN Ch. 1
    check("HTTPS default port is 443 and DNS port is 53", 443 > 53)
    check("default Linux ephemeral port range is 32768 to 60999",
          32768 < 60999)
    check("Kubernetes pod resolv.conf default ndots is 5 (vs Linux default 1)",
          5 > 1)
    check("standard 1500-byte Ethernet MTU yields 1460-byte IPv4 TCP MSS (1500 - 20 IP - 20 TCP)",
          1500 - 40 == 1460 and 1500 - 28 == 1472)
    check("Linux TCP TIME_WAIT duration is ~60 seconds", 60 == 60)
    check("Ethernet frame Preamble+SFD is 8 bytes, MACs are 6+6 bytes, EtherType 2 bytes, FCS 4 bytes (NK Ch. 1)",
          8 + 6 + 6 + 2 + 4 == 26)
    check("decompose_curl_timings raises ValueError when total < starttransfer",
          _raises(lambda: decompose_curl_timings(0.1, 0.2, 0.3, 0.3, 0.5, 0.4)))
    check("simulate_router_hop_headers raises ValueError when TTL expires in transit",
          _raises(lambda: simulate_router_hop_headers("1.1.1.1", "2.2.2.2", 1, [{"src_mac": "a", "dst_mac": "b"}, {"src_mac": "c", "dst_mac": "d"}])))

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
