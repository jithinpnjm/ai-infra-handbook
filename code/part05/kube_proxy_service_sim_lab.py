#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.10: Services, endpoints and kube-proxy: the life of a Service."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kube_proxy_service_sim import (
    build_endpointslices,
    compute_iptables_sep_probabilities,
    simulate_external_traffic_policy,
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
    # 1. Section 3 & NK Ch. 4: iptables 1/(N-i) sequential probabilities for 4 backends
    rules = compute_iptables_sep_probabilities(["10.0.0.1", "10.0.0.2", "10.0.0.3", "10.0.0.4"])
    cond_probs = [r["conditional_probability"] for r in rules]
    eff_shares = [r["effective_share"] for r in rules]
    check(
        "compute_iptables_sep_probabilities generates [0.25, 0.33333, 0.5, 1.0] yielding equal 0.25 share per backend",
        cond_probs == [0.25, 0.33333, 0.5, 1.0] and eff_shares == [0.25, 0.25, 0.25, 0.25],
    )

    # 2. Section 2: EndpointSlice 100-endpoint sharding and terminating fallback
    pods_250 = [{"ip": f"10.244.1.{i}", "ready": True, "serving": True, "terminating": False} for i in range(250)]
    sharded = build_endpointslices(pods_250, max_per_slice=100)
    term_pods = [{"ip": "10.244.1.99", "ready": False, "serving": True, "terminating": True}]
    fallback = build_endpointslices(term_pods, max_per_slice=100)
    check(
        "build_endpointslices shards 250 pods into 3 slices (100, 100, 50) and falls back to serving+terminating pod when 0 ready",
        sharded["slice_count"] == 3
        and [len(s) for s in sharded["slices"]] == [100, 100, 50]
        and fallback["used_terminating_fallback"] is True
        and fallback["slices"] == [["10.244.1.99"]],
    )

    # 3. Section 4: externalTrafficPolicy Cluster vs Local
    eps_map = {"node-1": ["10.244.1.10"], "node-2": []}
    res_cluster = simulate_external_traffic_policy(
        policy="Cluster",
        client_ip="203.0.113.5",
        ingress_node="node-2",
        node_ip="10.0.0.22",
        endpoints_by_node=eps_map,
    )
    res_local_ok = simulate_external_traffic_policy(
        policy="Local",
        client_ip="203.0.113.5",
        ingress_node="node-1",
        node_ip="10.0.0.21",
        endpoints_by_node=eps_map,
    )
    res_local_empty = simulate_external_traffic_policy(
        policy="Local",
        client_ip="203.0.113.5",
        ingress_node="node-2",
        node_ip="10.0.0.22",
        endpoints_by_node=eps_map,
    )
    check(
        "externalTrafficPolicy Cluster SNATs to node_ip, whereas Local preserves client_ip on node-1 and fails health check on empty node-2",
        res_cluster["source_ip_seen_by_pod"] == "10.0.0.22"
        and res_local_ok["source_ip_seen_by_pod"] == "203.0.113.5"
        and res_local_empty["routed"] is False
        and res_local_empty["health_check_node_port_pass"] is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
