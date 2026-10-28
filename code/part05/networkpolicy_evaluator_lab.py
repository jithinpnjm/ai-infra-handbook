#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.15: NetworkPolicy and the kernel: netfilter, conntrack and eBPF."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from networkpolicy_evaluator import (
    evaluate_peer_list,
    evaluate_policy_hierarchy,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 1: Single-element AND vs two-element OR YAML indentation trap!
    # Correct AND: ONE list item containing BOTH namespaceSelector and podSelector
    and_peers = [
        {"namespaceSelector": {"name": "edge"}, "podSelector": {"app": "gateway"}},
    ]
    # Broken OR (accidental extra dash `-` before podSelector!): TWO list items
    or_peers = [
        {"namespaceSelector": {"name": "edge"}},
        {"podSelector": {"app": "gateway"}},  # only in policy_namespace ("serving")!
    ]
    # Test a random non-gateway pod ("attacker") inside namespace "edge"
    and_allows_attacker_in_edge = evaluate_peer_list(
        and_peers,
        policy_namespace="serving",
        candidate_namespace="edge",
        candidate_pod_labels={"app": "attacker"},
    )
    or_allows_attacker_in_edge = evaluate_peer_list(
        or_peers,
        policy_namespace="serving",
        candidate_namespace="edge",
        candidate_pod_labels={"app": "attacker"},
    )
    check(
        "Single-element AND blocks non-gateway pod in 'edge' namespace, whereas accidental two-element OR allows ALL pods in 'edge'",
        and_allows_attacker_in_edge is False and or_allows_attacker_in_edge is True,
    )

    # 2. Section 1: ipBlock CIDR with except subnet exclusion
    ip_peers = [{"ipBlock": {"cidr": "10.20.0.0/16", "except": ["10.20.5.0/24"]}}]
    ok_ip = evaluate_peer_list(
        ip_peers,
        policy_namespace="serving",
        candidate_namespace="ext",
        candidate_pod_labels={},
        candidate_ip="10.20.1.50",
    )
    blocked_except = evaluate_peer_list(
        ip_peers,
        policy_namespace="serving",
        candidate_namespace="ext",
        candidate_pod_labels={},
        candidate_ip="10.20.5.50",
    )
    check(
        "ipBlock 10.20.0.0/16 except 10.20.5.0/24 allows 10.20.1.50 and blocks 10.20.5.50",
        ok_ip is True and blocked_except is False,
    )

    # 3. Section 4: AdminNetworkPolicy -> NetworkPolicy -> BaselineAdminNetworkPolicy precedence
    v_admin_deny = evaluate_policy_hierarchy(
        admin_action="Deny",
        namespace_netpol_isolated=True,
        namespace_netpol_allowed=True,
        baseline_action="Allow",
    )
    v_pass_to_netpol = evaluate_policy_hierarchy(
        admin_action="Pass",
        namespace_netpol_isolated=True,
        namespace_netpol_allowed=True,
        baseline_action="Deny",
    )
    v_non_isolated_baseline = evaluate_policy_hierarchy(
        admin_action=None,
        namespace_netpol_isolated=False,
        namespace_netpol_allowed=False,
        baseline_action="Deny",
    )
    check(
        "AdminNetworkPolicy Deny overrides namespace Allow, Pass delegates to NetworkPolicy, and non-isolated falls through to BaselineAdminNetworkPolicy",
        v_admin_deny == "DENY (by AdminNetworkPolicy)"
        and v_pass_to_netpol == "ALLOW (by NetworkPolicy)"
        and v_non_isolated_baseline == "DENY (by BaselineAdminNetworkPolicy)",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
