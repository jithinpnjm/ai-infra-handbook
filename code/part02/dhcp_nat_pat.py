"""Chapter 2.9 model: DHCP lease timer calculation (T1 = 50% renewal, T2 = 87.5%
rebind, expiry), conntrack SNAT/DNAT tuple parser, NAT gateway port-exhaustion
capacity calculation, and hairpin NAT routing diagnosis.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (DHCP, network configuration managers, IP masquerading / NAT, firewalls and
  routers) and Chapter 10 (network services).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapters 5 and 6 (DHCPv4/DHCPv6 interlayer discovery, address translation).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapters 2,
  4, and 6 (conntrack, kube-proxy DNAT/MASQUERADE, Cloud NAT).
"""
from typing import Dict


def compute_dhcp_lease_timers_sec(lease_seconds: int) -> Dict[str, int]:
    """Compute DHCP T1 (50% unicast renew), T2 (87.5% broadcast rebind), and expiry times in seconds."""
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")
    return {
        "lease_sec": lease_seconds,
        "t1_renew_sec": int(lease_seconds * 0.5),
        "t2_rebind_sec": int(lease_seconds * 0.875),
        "expiry_sec": lease_seconds,
    }


def parse_conntrack_nat_entry(line: str) -> Dict[str, object]:
    """Parse a conntrack line into original and expected-reply tuples and classify SNAT vs DNAT."""
    kv = {}
    orig: Dict[str, str] = {}
    reply: Dict[str, str] = {}
    for token in line.strip().split():
        if "=" in token:
            k, v = token.split("=", 1)
            if k not in orig:
                orig[k] = v
            elif k not in reply:
                reply[k] = v
    if not orig or not reply:
        raise ValueError(f"Malformed conntrack line: {line}")
    is_snat = reply.get("dst") != orig.get("src") or reply.get("dport") != orig.get("sport")
    is_dnat = reply.get("src") != orig.get("dst") or reply.get("sport") != orig.get("dport")
    return {
        "orig_src": f"{orig['src']}:{orig['sport']}",
        "orig_dst": f"{orig['dst']}:{orig['dport']}",
        "reply_src": f"{reply['src']}:{reply['sport']}",
        "reply_dst": f"{reply['dst']}:{reply['dport']}",
        "is_snat": is_snat,
        "is_dnat": is_dnat,
    }


def evaluate_nat_port_exhaustion(
    num_public_ips: int,
    ports_per_ip: int,
    concurrent_flows_to_same_dest: int,
) -> Dict[str, object]:
    """Evaluate NAT source-port utilization toward a single destination (IP:port)."""
    if num_public_ips <= 0 or ports_per_ip <= 0 or concurrent_flows_to_same_dest < 0:
        raise ValueError("Invalid NAT capacity parameters")
    total_ports = num_public_ips * ports_per_ip
    utilization_pct = round(100.0 * concurrent_flows_to_same_dest / float(total_ports), 1)
    return {
        "total_ports_per_dest": total_ports,
        "utilization_pct": utilization_pct,
        "exhausted": concurrent_flows_to_same_dest > total_ports,
    }


def check_hairpin_nat_flow(
    client_ip: str,
    server_ip: str,
    same_l2_subnet: bool,
    hairpin_snat_enabled: bool,
) -> Dict[str, object]:
    """Model whether an inside client reaching an inside server via the NAT's public VIP succeeds."""
    if not same_l2_subnet or hairpin_snat_enabled:
        return {"succeeds": True, "reason": "reply_returns_through_nat_and_is_translated"}
    return {
        "succeeds": False,
        "reason": "server_replies_directly_on_l2_with_private_ip_and_client_drops_unexpected_source",
    }
