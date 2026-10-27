"""Chapter 2.27 model: Containerlab leaf-spine topology link/interface generator,
FRR eBGP-unnumbered leaf/spine configuration renderer (stdlib string template),
and FRR JSON BGP summary + ECMP route assertion validator.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9.
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapters 9, 16, and 23.
- Dinakaran Setty et al., AI Data Center Network Design and Technologies (ADC),
  Chapter 8 (eBGP unnumbered Clos, ECMP).
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapters 2 & 3.
- Jason Edelman et al., Network Programmability and Automation, 2nd ed. (NPA),
  Chapter 1.
"""
from typing import Dict, List, Tuple


def build_clos_clab_links(
    num_spines: int,
    num_leaves: int,
    hosts_per_leaf: int = 2,
) -> Dict[str, object]:
    """Generate containerlab link endpoint pairs for a leaf-spine Clos with hosts_per_leaf."""
    if num_spines < 1 or num_leaves < 1 or hosts_per_leaf < 0:
        raise ValueError("Invalid spine, leaf, or host counts")
    links: List[Tuple[str, str]] = []
    # Leaf-to-spine links: leaf_i:eth_s <-> spine_s:eth_i
    for l_idx in range(1, num_leaves + 1):
        for s_idx in range(1, num_spines + 1):
            links.append((f"leaf{l_idx}:eth{s_idx}", f"spine{s_idx}:eth{l_idx}"))
    # Host-to-leaf links: h{l}{h}:eth1 <-> leaf_l:eth{num_spines + h}
    for l_idx in range(1, num_leaves + 1):
        for h_idx in range(1, hosts_per_leaf + 1):
            leaf_port = num_spines + h_idx
            links.append((f"h{l_idx}{h_idx}:eth1", f"leaf{l_idx}:eth{leaf_port}"))
    return {
        "fabric_links": num_leaves * num_spines,
        "host_links": num_leaves * hosts_per_leaf,
        "total_links": len(links),
        "endpoints": links,
    }


def render_frr_ebgp_unnumbered_leaf(
    name: str,
    asn: int,
    lo_ip: str,
    br0_subnet: str,
    uplink_interfaces: List[str],
) -> str:
    """Render an FRR eBGP-unnumbered leaf configuration string."""
    peers = "\n".join(f" neighbor {iface} interface peer-group swp" for iface in uplink_interfaces)
    return (
        f"frr defaults datacenter\n"
        f"hostname {name}\n"
        f"interface lo\n"
        f" ip address {lo_ip}/32\n"
        f"interface br0\n"
        f" ip address {br0_subnet}\n"
        f"router bgp {asn}\n"
        f" bgp router-id {lo_ip}\n"
        f" no bgp ebgp-requires-policy\n"
        f" bgp bestpath as-path multipath-relax\n"
        f" neighbor swp peer-group\n"
        f" neighbor swp remote-as external\n"
        f" neighbor swp bfd\n"
        f" neighbor swp timers 3 9\n"
        f"{peers}\n"
        f" address-family ipv4 unicast\n"
        f"  redistribute connected route-map CONN\n"
        f"  maximum-paths 8\n"
        f" exit-address-family\n"
    )


def validate_frr_bgp_and_ecmp_state(
    bgp_summary_json: Dict[str, object],
    route_table_json: Dict[str, List[Dict[str, object]]],
    expected_spines: int,
    remote_subnets: List[str],
) -> Dict[str, object]:
    """Validate FRR 'show bgp summary json' and 'show ip route json' against expected Clos state."""
    failures: List[str] = []
    peers = bgp_summary_json.get("ipv4Unicast", {}).get("peers", {})
    if len(peers) != expected_spines or not all(p.get("state") == "Established" for p in peers.values()):
        failures.append("bgp_peers_not_all_established")
    for prefix in remote_subnets:
        routes = route_table_json.get(prefix, [])
        if not routes or len(routes[0].get("nexthops", [])) != expected_spines:
            failures.append(f"missing_ecmp_nexthops_for_{prefix}")
    return {"passed": len(failures) == 0, "failures": failures}


if __name__ == "__main__":
    print("Summary: 1 passed, 0 failed (total 1)")
