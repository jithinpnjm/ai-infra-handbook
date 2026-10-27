"""Chapter 2.7 model: Overlay and tunnel inner MTU and TCP MSS calculator
(VXLAN, Geneve, GRE, IPIP, WireGuard IPv4/IPv6, MPLS), ping -M do payload size
calculator for IPv4 (-28) and IPv6 (-48), and mtr per-hop packet loss vs
control-plane ICMP rate-limiting classifier.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (ICMP, ping, traceroute, IPv4/IPv6 fragmentation and MTU).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapter 5 (UDP, IPv4 fragmentation vs IPv6 source fragmentation, PMTUD, ICMP).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 10 (ping, traceroute, path MTU, UDP buffer error counters).
"""
from typing import Dict, List


TUNNEL_OVERHEAD_BYTES: Dict[str, int] = {
    "none": 0,
    "mpls_1label": 4,
    "ipip": 20,
    "gre": 24,
    "vxlan": 50,
    "geneve_base": 50,
    "wireguard_ipv4": 60,
    "wireguard_ipv6": 80,
}


def compute_overlay_mtu_and_mss(
    underlay_mtu: int,
    encapsulation: str = "vxlan",
    inner_ipv6: bool = False,
) -> Dict[str, int]:
    """Compute maximum inner MTU and inner TCP MSS given underlay_mtu and encapsulation type."""
    if underlay_mtu < 576:
        raise ValueError("underlay_mtu must be >= 576")
    if encapsulation not in TUNNEL_OVERHEAD_BYTES:
        raise ValueError(f"Unknown encapsulation: {encapsulation}")
    overhead = TUNNEL_OVERHEAD_BYTES[encapsulation]
    inner_mtu = underlay_mtu - overhead
    inner_ip_tcp_hdr = 60 if inner_ipv6 else 40
    inner_mss = inner_mtu - inner_ip_tcp_hdr
    return {
        "underlay_mtu": underlay_mtu,
        "overhead_bytes": overhead,
        "inner_mtu": inner_mtu,
        "inner_tcp_mss": inner_mss,
    }


def compute_max_ping_df_payload(path_mtu: int, ipv6: bool = False) -> int:
    """Compute maximum 'ping -M do -s <payload>' size that fits in path_mtu without fragmentation."""
    if path_mtu < 68:
        raise ValueError("path_mtu must be >= 68")
    ip_plus_icmp_hdr = 48 if ipv6 else 28
    return path_mtu - ip_plus_icmp_hdr


def classify_mtr_hop_loss(hop_loss_pcts: List[float]) -> Dict[str, object]:
    """Distinguish router control-plane ICMP rate limiting from genuine forwarding packet loss.
    Genuine loss starts at hop K and persists all the way to the final destination hop.
    """
    if not hop_loss_pcts or any(not (0.0 <= x <= 100.0) for x in hop_loss_pcts):
        raise ValueError("Invalid hop_loss_pcts list")
    dest_loss = hop_loss_pcts[-1]
    any_intermediate_loss = any(x > 0.0 for x in hop_loss_pcts[:-1])
    if dest_loss == 0.0 and any_intermediate_loss:
        return {
            "verdict": "icmp_control_plane_rate_limiting_only",
            "first_real_loss_hop": None,
            "destination_loss_pct": 0.0,
        }
    if dest_loss > 0.0:
        # Find earliest hop from which all subsequent hops up to destination have loss > 0
        start_idx = len(hop_loss_pcts) - 1
        while start_idx > 0 and hop_loss_pcts[start_idx - 1] > 0.0:
            start_idx -= 1
        return {
            "verdict": "genuine_forwarding_loss",
            "first_real_loss_hop": start_idx + 1,  # 1-based hop number
            "destination_loss_pct": dest_loss,
        }
    return {
        "verdict": "clean_path_zero_loss",
        "first_real_loss_hop": None,
        "destination_loss_pct": 0.0,
    }
