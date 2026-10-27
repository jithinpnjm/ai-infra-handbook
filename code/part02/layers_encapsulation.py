"""Chapter 2.2 model: Ethernet/IP/TCP encapsulation overhead and on-wire goodput
efficiency (standard 1500 MTU vs 9000 jumbo MTU vs VXLAN 50-byte overlay),
maximum packet rate (Mpps) on 100/400 Gb/s links for minimum 64-byte frames, and
L2 -> L3 -> L4 demultiplexing key resolution.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions
  (computer-networking-problems-and-solutions), Chapter 1 ("Fundamental Concepts":
  circuit vs packet switching, ATM 53-byte cells, loop-free path algorithms,
  QoS, hourglass/wasp waist, State/Optimization/Surface SOS triangle) and
  Chapter 3 ("Modeling Network Transport": 4 jobs of a protocol, DoD/TCP-IP vs
  OSI vs RINA models, connection-oriented vs connectionless).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9.
"""
from typing import Dict


ETHERTYPE_MAP: Dict[int, str] = {
    0x0800: "IPv4",
    0x86DD: "IPv6",
    0x0806: "ARP",
    0x8100: "802.1Q_VLAN",
    0x8915: "RoCE_v1",
}

IP_PROTOCOL_MAP: Dict[int, str] = {
    1: "ICMP",
    6: "TCP",
    17: "UDP",
    47: "GRE",
    50: "ESP",
    58: "ICMPv6",
    89: "OSPF",
}


def compute_tcp_ethernet_goodput(
    mtu_bytes: int = 1500,
    ipv6: bool = False,
    tcp_options_bytes: int = 0,
    vlan_tags: int = 0,
    vxlan_overlay: bool = False,
) -> Dict[str, float]:
    """Compute MSS, total byte-times on the wire (incl. 14B Eth + 4B FCS + 8B preamble + 12B IFG), and goodput %."""
    if mtu_bytes < 64 or tcp_options_bytes < 0 or vlan_tags < 0:
        raise ValueError("Invalid MTU or header parameters")
    ip_hdr = 40 if ipv6 else 20
    tcp_hdr = 20 + tcp_options_bytes
    vxlan_hdr = 50 if vxlan_overlay else 0
    mss = mtu_bytes - ip_hdr - tcp_hdr - vxlan_hdr
    if mss <= 0:
        raise ValueError("Headers exceed MTU")
    eth_l1_l2_overhead = 14 + (4 * vlan_tags) + 4 + 8 + 12  # 38 bytes without VLAN
    wire_bytes = mtu_bytes + eth_l1_l2_overhead
    goodput_pct = round(100.0 * mss / float(wire_bytes), 1)
    return {
        "mss_bytes": mss,
        "wire_bytes": wire_bytes,
        "goodput_pct": goodput_pct,
    }


def compute_max_frame_rate_mpps(link_rate_gbps: float, frame_bytes_before_preamble: int = 64) -> float:
    """Compute maximum million packets per second (Mpps) given 8B preamble/SFD + 12B IFG (20B L1 overhead)."""
    if link_rate_gbps <= 0 or frame_bytes_before_preamble < 64:
        raise ValueError("link_rate_gbps > 0 and frame_bytes_before_preamble >= 64 required")
    wire_bytes = frame_bytes_before_preamble + 20  # 64 + 20 = 84 bytes = 672 bits
    pps = (link_rate_gbps * 1e9) / float(wire_bytes * 8)
    return round(pps / 1e6, 1)


def demultiplex_packet(ethertype: int, ip_proto: int, dst_port: int) -> Dict[str, str]:
    """Resolve L2 EtherType -> L3 protocol -> L4 transport and well-known service."""
    l3 = ETHERTYPE_MAP.get(ethertype, "UNKNOWN_L3")
    l4 = IP_PROTOCOL_MAP.get(ip_proto, "UNKNOWN_L4")
    port_services = {22: "SSH", 53: "DNS", 80: "HTTP", 443: "HTTPS_or_QUIC", 4791: "RoCE_v2"}
    app = port_services.get(dst_port, f"port_{dst_port}")
    return {"l3": l3, "l4": l4, "service": app}
