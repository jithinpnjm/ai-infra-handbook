"""Chapter 5.11 model: Kubernetes `/etc/resolv.conf` `ndots` search-list query
expander (`NK` Ch. 5 & `PK` Ch. 6), Headless Service (`publishNotReadyAddresses`)
DNS record generator (`KUR` Ch. 7), and CoreDNS `loop` detector (`127.0.0.53`).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 7
  ("Service Discovery").
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 4 & 5 (`CoreDNS` plugins Table 4-5, `dnsPolicy`,
  `host -v -t a github.com` search expansion across `default.svc.cluster.local`,
  `svc.cluster.local`, `cluster.local`).
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 6 ("Service Routing": `ndots` external
  lookup amplification and `Cluster Proportional Autoscaler`).
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def expand_dns_search_queries(
    query_name: str,
    namespace: str = "default",
    cluster_domain: str = "cluster.local",
    ndots: int = 5,
    extra_searches: Sequence[str] = (),
    dual_stack_a_and_aaaa: bool = True,
) -> List[str]:
    """Model Section 2 & NK Ch. 5 `/etc/resolv.conf` search expansion:
    - If `query_name` ends with a trailing dot (`.`), it is already an absolute
      FQDN -> 1 query (or 2 with A + AAAA), zero search expansion.
    - Otherwise, count dots in `query_name`:
      * If `dot_count < ndots`, try `<query_name>.<search>` for each search
        domain in `[f"{namespace}.svc.{cluster_domain}", f"svc.{cluster_domain}",
        cluster_domain, *extra_searches]` BEFORE trying `<query_name>.`!
      * If `dot_count >= ndots`, try `<query_name>.` first.
    """
    if query_name.endswith("."):
        candidates = [query_name]
    else:
        searches = [
            f"{namespace}.svc.{cluster_domain}",
            f"svc.{cluster_domain}",
            cluster_domain,
            *extra_searches,
        ]
        dot_count = query_name.count(".")
        if dot_count < ndots:
            candidates = [f"{query_name}.{s}." for s in searches] + [f"{query_name}."]
        else:
            candidates = [f"{query_name}."]

    if not dual_stack_a_and_aaaa:
        return candidates
    expanded: List[str] = []
    for c in candidates:
        expanded.append(f"A {c}")
        expanded.append(f"AAAA {c}")
    return expanded


def resolve_headless_service_records(
    service_name: str,
    namespace: str,
    pods: Sequence[Mapping[str, Any]],
    publish_not_ready_addresses: bool = False,
    cluster_domain: str = "cluster.local",
) -> Dict[str, List[str]]:
    """Model Section 1 & 5 Headless Service + StatefulSet per-pod DNS records."""
    fqdn = f"{service_name}.{namespace}.svc.{cluster_domain}."
    records: Dict[str, List[str]] = {fqdn: []}
    for pod in pods:
        if pod.get("ready", False) or publish_not_ready_addresses:
            ip = str(pod["ip"])
            pod_name = str(pod["name"])
            records[fqdn].append(ip)
            records[f"{pod_name}.{fqdn}"] = [ip]
    return records


def detect_coredns_forwarding_loop(upstream_nameservers: Sequence[str]) -> Tuple[bool, str]:
    """Model Section 3 & 7 CoreDNS `loop` plugin detecting self-forwarding
    when node `/etc/resolv.conf` points to `127.0.0.53` (`systemd-resolved`)
    or `127.0.0.1`.
    """
    loopback_set = {"127.0.0.1", "127.0.0.53", "::1"}
    bad = [ns for ns in upstream_nameservers if ns in loopback_set]
    if bad:
        return True, f"Loop detected in forward plugin: upstream {bad} points back to local loopback"
    return False, "upstreams valid"
