"""Chapter 2.5 model: Linux FIB longest-prefix-match (LPM) and metric tie-breaking,
policy-based routing (ip rule priority -> routing table lookup) for multi-NIC
AI servers, reverse-path filtering (rp_filter effective value = max(all, iface)
and mode 0/1/2 check), and ECMP multipath hash policy (L3 vs L4).

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 9
  (routes and the kernel routing table, ip route show, default gateway, LPM,
  IPv6 routes, Linux as a router net.ipv4.ip_forward=1, NAT, Netplan/nmcli).
- James Strong and Vallery Lancey, Networking and Kubernetes (networking-and-kubernetes),
  Chapter 2 ("Linux Networking": kernel parameters, routing tables 255 local /
  254 main / 253 default, netfilter, conntrack, IPVS).
- Russ White and Ethan Banks, Computer Networking Problems and Solutions (CN),
  Chapters 6 and 7 (default gateway determination, FIB lookup, ECMP hashing).
"""
import ipaddress
from typing import Dict, List, Optional


STANDARD_ROUTE_TABLES: Dict[int, str] = {
    255: "local",
    254: "main",
    253: "default",
}


def select_best_route_lpm(
    dst_ip: str,
    routes: List[Dict[str, object]],
) -> Optional[Dict[str, object]]:
    """Select the winning route using Longest Prefix Match (LPM), breaking ties by lowest metric."""
    target = ipaddress.IPv4Address(dst_ip)
    matches: List[Dict[str, object]] = []
    for r in routes:
        net = ipaddress.IPv4Network(str(r["prefix"]), strict=False)
        if target in net:
            matches.append({
                "prefix": str(net),
                "prefixlen": net.prefixlen,
                "metric": int(r.get("metric", 0)),
                "dev": str(r["dev"]),
                "via": r.get("via"),
                "src": r.get("src"),
            })
    if not matches:
        return None
    # Sort by (-prefixlen, +metric)
    matches.sort(key=lambda m: (-int(m["prefixlen"]), int(m["metric"])))
    return matches[0]


def evaluate_policy_routing(
    src_ip: str,
    dst_ip: str,
    rules: List[Dict[str, object]],
    tables: Dict[str, List[Dict[str, object]]],
) -> Optional[Dict[str, object]]:
    """Walk ip rules in ascending priority order and look up dst_ip in the first matching table."""
    src_addr = ipaddress.IPv4Address(src_ip)
    sorted_rules = sorted(rules, key=lambda r: int(r["priority"]))
    for rule in sorted_rules:
        from_prefix = str(rule.get("from", "0.0.0.0/0"))
        if src_addr in ipaddress.IPv4Network(from_prefix, strict=False):
            tbl_name = str(rule["table"])
            route = select_best_route_lpm(dst_ip, tables.get(tbl_name, []))
            if route is not None:
                out = dict(route)
                out["table"] = tbl_name
                out["rule_priority"] = int(rule["priority"])
                return out
    return None


def evaluate_rp_filter(
    rp_filter_all: int,
    rp_filter_iface: int,
    arrival_dev: str,
    reverse_route_best_dev: Optional[str],
    reverse_route_any_dev: bool,
) -> Dict[str, object]:
    """Compute effective rp_filter = max(all, iface) and whether packet is accepted or dropped (IPStatsInAddrErrors)."""
    if rp_filter_all not in {0, 1, 2} or rp_filter_iface not in {0, 1, 2}:
        raise ValueError("rp_filter values must be 0, 1, or 2")
    effective = max(rp_filter_all, rp_filter_iface)
    if effective == 0:
        accepted = True
    elif effective == 1:
        accepted = reverse_route_best_dev == arrival_dev
    else:  # effective == 2 (loose mode)
        accepted = reverse_route_any_dev
    return {
        "effective_rp_filter": effective,
        "accepted": accepted,
        "drop_counter": None if accepted else "IPStatsInAddrErrors",
    }
