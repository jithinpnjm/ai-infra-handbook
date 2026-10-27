"""Chapter 2.4 model: IPv4 CIDR subnet calculator (network, broadcast, first/last
usable host, usable count including RFC 3021 /31 and /32, wildcard mask), VLSM
largest-first aligned allocator, prefix summarization (collapse_addresses), and
Kubernetes Pod CIDR sizing.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (IPv4/IPv6 addresses, subnets and CIDR masks, RFC 1918 private ranges, Netplan
  and NetworkManager).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions
  (computer-networking-problems-and-solutions), Chapter 4, Chapter 5 (IPv4/IPv6
  headers, fragmentation and PMTUD, route aggregation), and Chapter 6 (EUI-64).
"""
import ipaddress
import math
from typing import Dict, List


def analyze_ipv4_cidr(cidr_str: str) -> Dict[str, object]:
    """Compute network, broadcast, usable host range, usable count, netmask, and wildcard mask."""
    iface = ipaddress.IPv4Interface(cidr_str)
    net = iface.network
    plen = net.prefixlen
    total = net.num_addresses
    if plen == 32:
        usable = 1
        first_host = str(net.network_address)
        last_host = str(net.network_address)
    elif plen == 31:
        usable = 2
        first_host = str(net.network_address)
        last_host = str(net.broadcast_address)
    else:
        usable = total - 2
        first_host = str(net.network_address + 1)
        last_host = str(net.broadcast_address - 1)
    return {
        "network": str(net.network_address),
        "prefixlen": plen,
        "netmask": str(net.netmask),
        "wildcard": str(net.hostmask),
        "broadcast": str(net.broadcast_address),
        "first_usable": first_host,
        "last_usable": last_host,
        "usable_hosts": usable,
    }


def allocate_vlsm_subnets(parent_cidr: str, required_hosts_list: List[int]) -> List[str]:
    """Allocate VLSM subnets from parent_cidr sorted largest-first and aligned on block boundaries."""
    parent = ipaddress.IPv4Network(parent_cidr, strict=True)
    # Sort requirements largest first
    sorted_reqs = sorted(required_hosts_list, reverse=True)
    available: List[ipaddress.IPv4Network] = [parent]
    allocated: List[str] = []

    for req in sorted_reqs:
        if req <= 0:
            raise ValueError("Required host count must be positive")
        if req == 2:
            # Use /31 for 2-host point-to-point links if requested as 2, or /30 if standard
            needed_addrs = 2
            target_plen = 31
        else:
            needed_addrs = req + 2
            host_bits = int(math.ceil(math.log2(needed_addrs)))
            target_plen = 32 - host_bits

        chosen_idx = -1
        for i, block in enumerate(available):
            if block.prefixlen <= target_plen:
                chosen_idx = i
                break
        if chosen_idx == -1:
            raise ValueError(f"Insufficient contiguous space in {parent_cidr} for {req} hosts")

        block = available.pop(chosen_idx)
        while block.prefixlen < target_plen:
            left, right = list(block.subnets(prefixlen_diff=1))
            available.insert(chosen_idx, right)
            block = left
        allocated.append(str(block))

    return allocated


def summarize_ipv4_prefixes(prefixes: List[str]) -> List[str]:
    """Collapse a list of IPv4 prefixes into the minimal set of exact summary prefixes."""
    nets = [ipaddress.IPv4Network(p, strict=True) for p in prefixes]
    return [str(n) for n in ipaddress.collapse_addresses(nets)]


def size_kubernetes_pod_cidr(max_nodes: int, node_pod_prefixlen: int = 24) -> Dict[str, object]:
    """Compute required cluster Pod CIDR prefix length given max_nodes and per-node pod prefix (/24 = 256 IPs)."""
    if max_nodes <= 0 or not (16 <= node_pod_prefixlen <= 28):
        raise ValueError("Invalid node count or per-node prefix length")
    ips_per_node = 1 << (32 - node_pod_prefixlen)
    total_ips_needed = max_nodes * ips_per_node
    node_bits = int(math.ceil(math.log2(max_nodes))) if max_nodes > 1 else 0
    cluster_plen = node_pod_prefixlen - node_bits
    return {
        "ips_per_node": ips_per_node,
        "min_total_ips": total_ips_needed,
        "recommended_cluster_prefixlen": cluster_plen,
        "cluster_block_ips": 1 << (32 - cluster_plen),
    }
