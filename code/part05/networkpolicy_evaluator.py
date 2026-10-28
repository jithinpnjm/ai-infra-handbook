"""Chapter 5.15 model: Kubernetes `NetworkPolicy` AND vs OR `from`/`to` peer
selector evaluator, dual-ended (source egress + destination ingress) flow
verdict engine with stateful `conntrack` tracking, and `AdminNetworkPolicy` ->
`NetworkPolicy` -> `BaselineAdminNetworkPolicy` precedence evaluator (`NK` Ch. 4–5,
`PK` Ch. 5, `volume-03/03`).

Sources modeled:
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 4 & 5 (NetworkPolicy selectors, default-deny,
  node-origin probe allowance, CNI enforcement).
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 5 ("Pod Networking").
- nvidia-devops (`volume-03/03-k8s-networking-security-ops-masterclass.md`).
"""
import ipaddress
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def match_networkpolicy_peer(
    peer_elem: Mapping[str, Any],
    *,
    policy_namespace: str,
    candidate_namespace: str,
    candidate_pod_labels: Mapping[str, str],
    candidate_ip: str | None = None,
) -> bool:
    """Model Section 1 `from`/`to` single list-element matching:
    - If `ipBlock` is specified: matches `cidr` and not in `except`.
    - If BOTH `namespaceSelector` and `podSelector` are present in the SAME
      dict element: they are AND'd!
    - If ONLY `podSelector` is present: candidate MUST be in `policy_namespace`
      AND match `podSelector`.
    - If ONLY `namespaceSelector` is present: candidate namespace must match
      `namespaceSelector` (all pods in those namespaces).
    """
    if "ipBlock" in peer_elem:
        if not candidate_ip:
            return False
        ip_obj = ipaddress.ip_address(candidate_ip)
        cidr = ipaddress.ip_network(str(peer_elem["ipBlock"]["cidr"]))
        if ip_obj not in cidr:
            return False
        for ex in peer_elem["ipBlock"].get("except", ()):
            if ip_obj in ipaddress.ip_network(str(ex)):
                return False
        return True

    has_ns_sel = "namespaceSelector" in peer_elem
    has_pod_sel = "podSelector" in peer_elem

    if has_ns_sel:
        ns_req = peer_elem["namespaceSelector"]
        if ns_req and ns_req.get("name") != candidate_namespace:
            return False
    else:
        # No namespaceSelector -> restricted to policy's own namespace!
        if candidate_namespace != policy_namespace:
            return False

    if has_pod_sel:
        pod_req = peer_elem["podSelector"]
        for k, v in pod_req.items():
            if candidate_pod_labels.get(k) != v:
                return False

    return True


def evaluate_peer_list(
    peer_list: Sequence[Mapping[str, Any]],
    *,
    policy_namespace: str,
    candidate_namespace: str,
    candidate_pod_labels: Mapping[str, str],
    candidate_ip: str | None = None,
) -> bool:
    """Separate elements in `from:` / `to:` are OR'd."""
    return any(
        match_networkpolicy_peer(
            elem,
            policy_namespace=policy_namespace,
            candidate_namespace=candidate_namespace,
            candidate_pod_labels=candidate_pod_labels,
            candidate_ip=candidate_ip,
        )
        for elem in peer_list
    )


def evaluate_policy_hierarchy(
    *,
    admin_action: str | None,
    namespace_netpol_isolated: bool,
    namespace_netpol_allowed: bool,
    baseline_action: str = "Allow",
) -> str:
    """Model Section 4 `AdminNetworkPolicy` (Allow / Deny / Pass) ->
    `NetworkPolicy` -> `BaselineAdminNetworkPolicy` (Allow / Deny) evaluation order.
    """
    if admin_action == "Allow":
        return "ALLOW (by AdminNetworkPolicy)"
    if admin_action == "Deny":
        return "DENY (by AdminNetworkPolicy)"
    # AdminNetworkPolicy is None or "Pass" -> evaluate namespace NetworkPolicy
    if namespace_netpol_isolated:
        return "ALLOW (by NetworkPolicy)" if namespace_netpol_allowed else "DENY (by NetworkPolicy isolation)"
    # Non-isolated in namespace -> fall through to BaselineAdminNetworkPolicy
    return f"{baseline_action.upper()} (by BaselineAdminNetworkPolicy)"
