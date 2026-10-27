"""Chapter 5.10 model: `kube-proxy` `iptables` sequential `--probability`
(`1 / (N - i)`) rule generator (`NK` Ch. 4 & `PK` Ch. 6), `EndpointSlice`
sharding & terminating-endpoint fallback evaluator, and `externalTrafficPolicy`
(`Cluster` vs `Local`) packet path & source-IP simulator.

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 7
  ("Service Discovery"): `kubectl expose`, `ClusterIP`/`NodePort`/`LoadBalancer`,
  Endpoints readiness watching, internal LoadBalancer annotations, selector-less
  Services.
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 4 & 5: sequential `iptables` `--mode random
  --probability` rules (`0.25`, `0.33333`, `0.50` for 4 backends), IPVS 6 load
  balancing modes (`rr`, `lc`, `dh`, `sh`, `sed`, `nq`), MetalLB `controller` +
  `speaker`.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 6 ("Service Routing"): `kube-ipvs0`
  dummy interface, conntrack 5-tuple mapping, Service environment variable
  ordering vs DNS.
"""
from typing import Any, Dict, List, Mapping, Sequence


def compute_iptables_sep_probabilities(endpoints: Sequence[str]) -> List[Dict[str, object]]:
    """Model Section 3 & NK Ch. 4 `KUBE-SVC-*` sequential `--mode random
    --probability` rules over N endpoints:
    Rule `i` (0-indexed out of N) matches with probability `p_i = 1 / (N - i)`
    so that each endpoint receives an exact unconditional `1 / N` share of new
    connections.
    """
    n = len(endpoints)
    rules: List[Dict[str, object]] = []
    remaining_share = 1.0
    for i, ep in enumerate(endpoints):
        cond_prob = 1.0 / (n - i)
        effective_share = remaining_share * cond_prob
        remaining_share *= (1.0 - cond_prob)
        rules.append(
            {
                "endpoint": ep,
                "conditional_probability": round(cond_prob, 5),
                "effective_share": round(effective_share, 5),
            }
        )
    return rules


def build_endpointslices(
    pods: Sequence[Mapping[str, Any]],
    max_per_slice: int = 100,
) -> Dict[str, Any]:
    """Model Section 2 EndpointSlice sharding (up to `max_per_slice` endpoints
    per slice) and terminating-endpoint fallback:
    - Normal state: route to `ready and serving` endpoints.
    - All-terminating fallback: if 0 `ready` endpoints exist, route to
      `serving and terminating` endpoints rather than dropping traffic.
    """
    ready_eps = [str(p["ip"]) for p in pods if p.get("ready", False) and p.get("serving", True)]
    term_serving_eps = [
        str(p["ip"])
        for p in pods
        if not p.get("ready", False) and p.get("serving", False) and p.get("terminating", False)
    ]
    active_targets = ready_eps if ready_eps else term_serving_eps
    slices: List[List[str]] = [
        active_targets[i : i + max_per_slice]
        for i in range(0, len(active_targets), max_per_slice)
    ]
    return {
        "slice_count": len(slices),
        "slices": slices,
        "used_terminating_fallback": (len(ready_eps) == 0 and len(term_serving_eps) > 0),
    }


def simulate_external_traffic_policy(
    *,
    policy: str,
    client_ip: str,
    ingress_node: str,
    node_ip: str,
    endpoints_by_node: Mapping[str, Sequence[str]],
) -> Dict[str, Any]:
    """Model Section 4 `externalTrafficPolicy: Cluster` vs `Local`."""
    local_eps = list(endpoints_by_node.get(ingress_node, ()))
    all_eps = [ep for eps in endpoints_by_node.values() for ep in eps]

    if policy == "Cluster":
        if not all_eps:
            return {"routed": False, "reason": "no endpoints in cluster"}
        return {
            "routed": True,
            "candidate_endpoints": all_eps,
            "source_ip_seen_by_pod": node_ip,  # SNAT masqueraded!
            "extra_node_hop_possible": True,
            "health_check_node_port_pass": True,
        }
    if policy == "Local":
        if not local_eps:
            return {
                "routed": False,
                "reason": "no local endpoint on ingress_node (healthCheckNodePort returns 503)",
                "health_check_node_port_pass": False,
            }
        return {
            "routed": True,
            "candidate_endpoints": local_eps,
            "source_ip_seen_by_pod": client_ip,  # Preserved!
            "extra_node_hop_possible": False,
            "health_check_node_port_pass": True,
        }
    raise ValueError(f"unknown externalTrafficPolicy {policy!r}")
