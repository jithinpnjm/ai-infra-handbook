"""Chapter 2.23 model: Netfilter hook traversal simulator (local-in, local-out,
forwarded, loopback), nf_conntrack hash table sizing and memory calculator
(buckets = max // 8, ~350B per entry), and conntrack state machine transition
evaluator (NEW, ESTABLISHED, RELATED, INVALID, UNTRACKED).

Sources modeled:
- James Strong and Vallery Lancey, Networking and Kubernetes (NK), Chapter 2
  ("Linux Networking": netfilter 5 hooks, conntrack states, iptables tables and
  priorities, Martian packets, kube-proxy iptables/IPVS).
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (Linux routers, NAT, firewall strategies).
- Brendan Gregg, Systems Performance, 2nd ed. (systems-performance-2nd-edition),
  Chapter 10.
- nvidia-devops/volume-01/03-linux-networking-masterclass.md (plus volume-01
  01, 02, and 04 masterclasses).
"""
from typing import Dict, List


def trace_netfilter_hooks(flow_type: str) -> List[str]:
    """Return the ordered list of netfilter hooks traversed by a packet for flow_type."""
    paths = {
        "external_to_local": ["prerouting", "input"],
        "local_to_external": ["output", "postrouting"],
        "external_to_external_forwarded": ["prerouting", "forward", "postrouting"],
        "local_to_local_loopback": ["output", "postrouting", "prerouting", "input"],
    }
    if flow_type not in paths:
        raise ValueError(f"Unknown flow_type: {flow_type}")
    return list(paths[flow_type])


def size_conntrack_table(
    nf_conntrack_max: int,
    bucket_ratio: int = 8,
    bytes_per_entry: int = 352,
) -> Dict[str, object]:
    """Compute recommended hashsize (buckets = max // bucket_ratio) and approximate RAM in MiB."""
    if nf_conntrack_max <= 0 or bucket_ratio <= 0 or bytes_per_entry <= 0:
        raise ValueError("Conntrack sizing parameters must be positive")
    buckets = max(1, nf_conntrack_max // bucket_ratio)
    total_bytes = nf_conntrack_max * bytes_per_entry + (buckets * 16)
    ram_mib = round(total_bytes / float(1024 * 1024), 1)
    return {
        "nf_conntrack_max": nf_conntrack_max,
        "recommended_hashsize_buckets": buckets,
        "estimated_ram_mib": ram_mib,
    }


def classify_conntrack_packet_state(
    notrack_matched: bool,
    existing_flow_found: bool,
    seen_reply_direction: bool,
    is_valid_syn_or_first_packet: bool,
    is_helper_or_icmp_error_for_existing: bool = False,
) -> str:
    """Classify a packet's conntrack state (UNTRACKED, RELATED, ESTABLISHED, NEW, INVALID)."""
    if notrack_matched:
        return "UNTRACKED"
    if is_helper_or_icmp_error_for_existing:
        return "RELATED"
    if existing_flow_found:
        return "ESTABLISHED" if seen_reply_direction else "NEW"
    if is_valid_syn_or_first_packet:
        return "NEW"
    return "INVALID"
