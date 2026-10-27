"""Chapter 2.1 model: curl -w cumulative timing phase decomposition (DNS, TCP connect,
TLS handshake, server wait/TTFB, body transfer), hop-by-hop L2 MAC vs L3 IP/TTL
header rewrite simulation, and curl exit-code to network layer diagnosis.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (packets, network layers, IP addresses, routes, DNS, TCP ports, ARP/NDP) and
  Chapter 10 (network applications and diagnostic tools).
- James Strong and Vallery Lancey, Networking and Kubernetes (networking-and-kubernetes),
  Chapter 1 ("Networking Introduction": IETF RFC states Proposed Standard vs
  Internet Standard, ISO/IEC 7498-1..4 OSI model vs RFC 1122 TCP/IP model, PDUs,
  Ethernet Preamble/SFD/MAC/EtherType/FCS, and the end-to-end cURL HTTP request
  walkthrough).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions
  (computer-networking-problems-and-solutions), Chapter 1 (packet switching,
  hop-by-hop forwarding, layered models).
"""
from typing import Dict, List


CURL_EXIT_CODE_LAYER_MAP: Dict[int, Dict[str, str]] = {
    6: {"layer": "L7_DNS_resolver", "meaning": "Could not resolve host"},
    7: {"layer": "L3_L4_connect", "meaning": "Failed to connect to host (refused, unreachable, or no route)"},
    22: {"layer": "L7_HTTP_status", "meaning": "HTTP page not retrieved (4xx/5xx with -f)"},
    28: {"layer": "L3_L4_L7_timeout", "meaning": "Operation timed out"},
    35: {"layer": "L6_L7_TLS_handshake", "meaning": "SSL/TLS connect error"},
    60: {"layer": "L6_L7_TLS_PKI", "meaning": "Peer certificate cannot be authenticated with known CA"},
}


def decompose_curl_timings(
    time_namelookup: float,
    time_connect: float,
    time_appconnect: float,
    time_pretransfer: float,
    time_starttransfer: float,
    time_total: float,
) -> Dict[str, float]:
    """Decompose cumulative curl -w timestamps into individual phase durations."""
    if not (0.0 <= time_namelookup <= time_connect <= time_appconnect <= time_pretransfer <= time_starttransfer <= time_total):
        raise ValueError("curl -w cumulative timestamps must be non-decreasing")
    return {
        "dns_s": round(time_namelookup, 4),
        "tcp_connect_s": round(time_connect - time_namelookup, 4),
        "tls_handshake_s": round(time_appconnect - time_connect, 4),
        "server_wait_ttfb_s": round(time_starttransfer - time_pretransfer, 4),
        "body_transfer_s": round(time_total - time_starttransfer, 4),
        "total_s": round(time_total, 4),
    }


def simulate_router_hop_headers(
    src_ip: str,
    dst_ip: str,
    initial_ttl: int,
    hop_mac_pairs: List[Dict[str, str]],
) -> List[Dict[str, object]]:
    """Simulate L2 MAC rewrites and L3 TTL decrements across router hops (without NAT)."""
    if initial_ttl <= 0 or not hop_mac_pairs:
        raise ValueError("initial_ttl > 0 and non-empty hop_mac_pairs required")
    hops: List[Dict[str, object]] = []
    cur_ttl = initial_ttl
    for idx, pair in enumerate(hop_mac_pairs):
        if idx > 0:
            cur_ttl -= 1
        if cur_ttl <= 0:
            raise ValueError("TTL expired in transit (ICMP Time Exceeded)")
        hops.append({
            "hop_index": idx + 1,
            "src_mac": pair["src_mac"],
            "dst_mac": pair["dst_mac"],
            "src_ip": src_ip,
            "dst_ip": dst_ip,
            "ttl": cur_ttl,
        })
    return hops


def diagnose_curl_exit_code(exit_code: int) -> Dict[str, str]:
    """Map a curl exit code (6, 7, 22, 28, 35, 60) to its network layer and meaning."""
    return CURL_EXIT_CODE_LAYER_MAP.get(
        exit_code,
        {"layer": "unknown", "meaning": f"Unmapped exit code {exit_code}"},
    )
