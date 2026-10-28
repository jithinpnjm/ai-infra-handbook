#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.28: Service mesh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from service_mesh_policy_sim import (
    compute_mesh_fleet_memory_overhead,
    evaluate_mesh_mtls_and_authz,
    evaluate_outlier_detection_and_routing,
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
    # 1. Section 3 & 6: PeerAuthentication STRICT + AuthorizationPolicy SPIFFE principal check
    allow_rules = [
        {
            "principals": ["cluster.local/ns/edge/sa/router"],
            "methods": ["POST"],
            "path_prefixes": ["/v1/"],
        }
    ]
    ok_router, _ = evaluate_mesh_mtls_and_authz(
        peer_auth_mode="STRICT",
        is_mtls_connection=True,
        caller_spiffe_principal="cluster.local/ns/edge/sa/router",
        http_method="POST",
        http_path="/v1/chat/completions",
        allow_rules=allow_rules,
    )
    fail_plaintext, _ = evaluate_mesh_mtls_and_authz(
        peer_auth_mode="STRICT",
        is_mtls_connection=False,
        caller_spiffe_principal="cluster.local/ns/edge/sa/router",
        http_method="POST",
        http_path="/v1/chat/completions",
        allow_rules=allow_rules,
    )
    fail_wrong_sa, _ = evaluate_mesh_mtls_and_authz(
        peer_auth_mode="STRICT",
        is_mtls_connection=True,
        caller_spiffe_principal="cluster.local/ns/team-b/sa/notebook",
        http_method="POST",
        http_path="/v1/chat/completions",
        allow_rules=allow_rules,
    )
    check(
        "evaluate_mesh_mtls_and_authz admits mTLS call from edge/router on POST /v1/* and rejects plaintext or unauthorized notebook SA",
        ok_router is True and fail_plaintext is False and fail_wrong_sa is False,
    )

    # 2. Section 3: VirtualService x-canary header routing & DestinationRule outlierDetection
    eps = [
        {"name": "vllm-0", "consecutive_5xx": 0},
        {"name": "vllm-1", "consecutive_5xx": 6},  # >= 5 -> ejected!
        {"name": "vllm-2", "consecutive_5xx": 1},
    ]
    rt = evaluate_outlier_detection_and_routing(
        headers={"x-canary": "true"},
        endpoints=eps,
        consecutive_5xx_limit=5,
    )
    check(
        "evaluate_outlier_detection_and_routing routes x-canary=true to v2 and ejects vllm-1 (6 consecutive 5xx errors)",
        rt["selected_route"] == "v2"
        and rt["ejected_endpoints"] == ["vllm-1"]
        and rt["healthy_endpoints"] == ["vllm-0", "vllm-2"],
    )

    # 3. Section 2 & 7: Fleet memory overhead at 5,000 pods across 200 nodes (Sidecar vs Ambient)
    mem = compute_mesh_fleet_memory_overhead(total_pods=5000, total_nodes=200, waypoints_count=10)
    check(
        "At 5,000 pods / 200 nodes, Envoy sidecars consume 400,000 MiB (~390 GiB) vs 9,000 MiB (~8.8 GiB) in Istio Ambient mode",
        mem["istio_sidecar_total_mib"] == 400_000
        and mem["linkerd_sidecar_total_mib"] == 90_000
        and mem["istio_ambient_total_mib"] == 9_000,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
