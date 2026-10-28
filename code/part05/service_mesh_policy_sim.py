"""Chapter 5.28 model: Istio `PeerAuthentication` (`PERMISSIVE` vs `STRICT`) +
`AuthorizationPolicy` SPIFFE identity evaluator, `VirtualService`/`DestinationRule`
router with outlier ejection, and Sidecar vs Ambient vs Cilium eBPF mesh
memory-overhead calculator (`KUR` Ch. 15, `PK` Ch. 6 & 10, `NK` Ch. 5 & 6).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 15
  ("Service Meshes"): why add a mesh beyond Services/Ingress, mTLS encryption &
  SPIFFE authentication, traffic shaping/canary/circuit-breaking, introspecting
  a service mesh (`iptables` -> Envoy sidecar -> xDS control plane), and the
  "Do You Really Need a Service Mesh?" decision checklist.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 6 & 10.
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 5 & 6.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def evaluate_mesh_mtls_and_authz(
    *,
    peer_auth_mode: str,
    is_mtls_connection: bool,
    caller_spiffe_principal: str,
    http_method: str,
    http_path: str,
    allow_rules: Sequence[Mapping[str, Any]],
    deny_rules: Sequence[Mapping[str, Any]] = (),
) -> Tuple[bool, str]:
    """Model Section 3 & 6 Istio `PeerAuthentication` (`PERMISSIVE` vs `STRICT`)
    and `AuthorizationPolicy` evaluation order:
    1. If `peer_auth_mode == "STRICT"` and not `is_mtls_connection`, reject
       immediately (`503 UC / TLS handshake error`).
    2. Evaluate `deny_rules` first: if any matches, reject (`403 RBAC: access denied`).
    3. If `allow_rules` is non-empty, caller must match at least one allow rule
       (principal, method, and path prefix), else reject (`403 RBAC: access denied`).
    """
    if peer_auth_mode == "STRICT" and not is_mtls_connection:
        return False, "REJECTED: PeerAuthentication STRICT requires mTLS"

    def rule_matches(rule: Mapping[str, Any]) -> bool:
        principals = rule.get("principals", ())
        if principals and caller_spiffe_principal not in principals:
            return False
        methods = rule.get("methods", ())
        if methods and http_method not in methods:
            return False
        prefixes = rule.get("path_prefixes", ())
        if prefixes and not any(http_path.startswith(p) for p in prefixes):
            return False
        return True

    for d_rule in deny_rules:
        if rule_matches(d_rule):
            return False, "REJECTED: matched explicit DENY AuthorizationPolicy"

    if allow_rules:
        if any(rule_matches(a_rule) for a_rule in allow_rules):
            return True, "ALLOWED: matched ALLOW AuthorizationPolicy"
        return False, "REJECTED: no matching ALLOW AuthorizationPolicy (RBAC: access denied)"

    return True, "ALLOWED: no AuthorizationPolicy restrictions"


def evaluate_outlier_detection_and_routing(
    *,
    headers: Mapping[str, str],
    endpoints: Sequence[Mapping[str, Any]],
    consecutive_5xx_limit: int = 5,
) -> Dict[str, Any]:
    """Model Section 3 `VirtualService` canary header routing + `DestinationRule`
    `outlierDetection` ejecting endpoints with `consecutive_5xx >= consecutive_5xx_limit`.
    """
    target_subset = "v2" if headers.get("x-canary") == "true" else "v1_95_v2_5"
    healthy_eps: List[str] = []
    ejected_eps: List[str] = []
    for ep in endpoints:
        if int(ep.get("consecutive_5xx", 0)) >= consecutive_5xx_limit:
            ejected_eps.append(str(ep["name"]))
        else:
            healthy_eps.append(str(ep["name"]))
    return {
        "selected_route": target_subset,
        "healthy_endpoints": healthy_eps,
        "ejected_endpoints": ejected_eps,
    }


def compute_mesh_fleet_memory_overhead(
    *,
    total_pods: int,
    total_nodes: int,
    waypoints_count: int = 10,
    envoy_sidecar_mib: int = 80,
    linkerd_sidecar_mib: int = 18,
    ztunnel_per_node_mib: int = 40,
    waypoint_mib: int = 100,
) -> Dict[str, int]:
    """Model Section 2 & 7 fleet-wide proxy memory footprint across Sidecar
    (Envoy vs Linkerd) and Ambient (ztunnel per node + shared waypoints).
    """
    return {
        "istio_sidecar_total_mib": total_pods * envoy_sidecar_mib,
        "linkerd_sidecar_total_mib": total_pods * linkerd_sidecar_mib,
        "istio_ambient_total_mib": (total_nodes * ztunnel_per_node_mib) + (waypoints_count * waypoint_mib),
    }
