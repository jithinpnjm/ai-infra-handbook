"""Chapter 2.3 model: MAC address EUI-48 decoding (OUI, I/G unicast vs multicast
bit, U/L globally unique vs locally administered bit), Ethernet switch FDB MAC
learning and forwarding/flooding/filtering simulation, IPv6 EUI-64 link-local
and solicited-node multicast address generation, and serialization delay math.

Sources modeled:
- Russ White and Ethan Banks, Computer Networking Problems and Solutions
  (computer-networking-problems-and-solutions), Chapter 4 ("Lower Layer Transports":
  Ethernet CSMA/CD, MAC I/G & U/L bits, frame format, 802.11 CSMA/CA), Chapter 6
  ("Interlayer Discovery": ARP, gratuitous ARP, proxy ARP, IPv6 NDP RS/RA/NS/NA,
  EUI-64, DAD, SLAAC), and Chapter 7 ("Packet Switching": 4 internal switching
  steps, VOQs and iSLIP, store-and-forward vs cut-through).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (Ethernet, ARP, NDP, wireless).
"""
from typing import Dict, List


def decode_mac_address(mac_str: str) -> Dict[str, object]:
    """Decode a 48-bit MAC address ('52:54:00:12:34:56') into OUI, I/G bit, and U/L bit."""
    octets = [int(x, 16) for x in mac_str.strip().split(":")]
    if len(octets) != 6:
        raise ValueError(f"Invalid MAC address: {mac_str}")
    first = octets[0]
    is_Broadcast = all(b == 0xFF for b in octets)
    ig_multicast = bool(first & 0x01)
    ul_locally_administered = bool(first & 0x02)
    oui = ":".join(f"{b:02x}" for b in octets[:3])
    return {
        "oui": oui,
        "is_broadcast": is_Broadcast,
        "is_multicast": ig_multicast,
        "is_unicast": not ig_multicast,
        "locally_administered": ul_locally_administered,
    }


def simulate_switch_frame_action(
    fdb_mac_to_port: Dict[str, int],
    all_ports: List[int],
    ingress_port: int,
    src_mac: str,
    dst_mac: str,
) -> Dict[str, object]:
    """Simulate L2 switch learning of src_mac on ingress_port and forwarding/flooding/filtering of dst_mac."""
    if ingress_port not in all_ports:
        raise ValueError(f"Ingress port {ingress_port} not in switch ports")
    # 1. Learn source MAC
    fdb_mac_to_port[src_mac.lower()] = ingress_port
    dst = dst_mac.lower()
    dst_info = decode_mac_address(dst)

    # 2. Broadcast or multicast -> flood to all ports except ingress
    if dst_info["is_broadcast"] or dst_info["is_multicast"]:
        egress = [p for p in all_ports if p != ingress_port]
        return {"action": "flood_broadcast_or_multicast", "egress_ports": egress}

    # 3. Known unicast
    if dst in fdb_mac_to_port:
        target_port = fdb_mac_to_port[dst]
        if target_port == ingress_port:
            return {"action": "filter_same_port", "egress_ports": []}
        return {"action": "forward_unicast", "egress_ports": [target_port]}

    # 4. Unknown unicast -> flood
    egress = [p for p in all_ports if p != ingress_port]
    return {"action": "flood_unknown_unicast", "egress_ports": egress}


def mac_to_ipv6_eui64_link_local(mac_str: str) -> Dict[str, str]:
    """Convert a 48-bit MAC ('01:23:45:67:89:ab') to modified EUI-64 link-local IPv6 and solicited-node multicast."""
    octets = [int(x, 16) for x in mac_str.strip().split(":")]
    if len(octets) != 6:
        raise ValueError(f"Invalid MAC address: {mac_str}")
    # Flip U/L bit (bit 1 of first octet, 0x02) and insert ff:fe in the middle
    b0 = octets[0] ^ 0x02
    eui = [b0, octets[1], octets[2], 0xFF, 0xFE, octets[3], octets[4], octets[5]]
    g1 = (eui[0] << 8) | eui[1]
    g2 = (eui[2] << 8) | eui[3]
    g3 = (eui[4] << 8) | eui[5]
    g4 = (eui[6] << 8) | eui[7]
    link_local = f"fe80::{g1:x}:{g2:x}:{g3:x}:{g4:x}"
    sol_node_ip = f"ff02::1:ff{eui[5]:02x}:{g4:x}"
    sol_node_mac = f"33:33:ff:{eui[5]:02x}:{eui[6]:02x}:{eui[7]:02x}"
    return {
        "link_local_ipv6": link_local,
        "solicited_node_multicast_ipv6": sol_node_ip,
        "solicited_node_multicast_mac": sol_node_mac,
    }


def compute_serialization_delay_ns(frame_bytes: int, link_rate_gbps: float) -> float:
    """Compute serialization delay in nanoseconds: (frame_bytes * 8) / link_rate_gbps."""
    if frame_bytes <= 0 or link_rate_gbps <= 0:
        raise ValueError("frame_bytes and link_rate_gbps must be positive")
    return round((frame_bytes * 8.0) / link_rate_gbps, 1)
