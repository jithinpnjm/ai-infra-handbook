#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.22: Multitenancy and platform services."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from multitenancy_quota_reconciler import (
    compute_tenant_gpu_cost_and_waste,
    evaluate_resource_quota_and_limitrange,
    reconcile_acme_namespace_operator,
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
    # 1. Section 2: LimitRange defaulting/bounds + ResourceQuota enforcement
    lr = {"default_cpu_m": 1000, "default_mem_mi": 4096, "max_cpu_m": 128000, "max_mem_mi": 1048576}
    used = {"requests.cpu_m": 500000, "requests.mem_mi": 3000000, "requests.nvidia.com/gpu": 28, "count/pods": 100}
    hard = {"requests.cpu_m": 512000, "requests.mem_mi": 4194304, "requests.nvidia.com/gpu": 32, "count/pods": 2000}

    ok_pod, new_used, _ = evaluate_resource_quota_and_limitrange(
        pod_containers=[{"name": "trainer", "gpu": 4}],  # inherits 1000m CPU, 4096Mi RAM from LimitRange
        limit_range=lr,
        current_quota_used=used,
        quota_hard=hard,
    )
    bad_pod, _, errs = evaluate_resource_quota_and_limitrange(
        pod_containers=[{"name": "huge", "cpu_m": 256000, "gpu": 8}],  # exceeds max_cpu_m AND gpu quota (28+8=36 > 32)
        limit_range=lr,
        current_quota_used=used,
        quota_hard=hard,
    )
    check(
        "evaluate_resource_quota_and_limitrange injects LimitRange defaults for 4-GPU pod and rejects pod exceeding max CPU and CPU/GPU quota",
        ok_pod is True
        and new_used["requests.nvidia.com/gpu"] == 32
        and bad_pod is False
        and len(errs) == 3,
    )

    # 2. Section 4 & PK Ch. 11 & 16: AcmeNamespace / Team operator level-triggered self-healing
    cache = {
        "Namespace/team-a",
        "Role/team-a/namespace-admin",
        # RoleBinding and ResourceQuota were accidentally deleted!
        "NetworkPolicy/team-a/default-deny-all",
    }
    rec = reconcile_acme_namespace_operator(
        namespace_name="team-a",
        admin_username="alice",
        existing_children_in_cache=cache,
    )
    check(
        "reconcile_acme_namespace_operator detects and recreates the 2 missing child objects (RoleBinding and ResourceQuota)",
        rec["created_children"]
        == [
            "RoleBinding/team-a/namespace-admin-alice",
            "ResourceQuota/team-a/compute-quota",
        ]
        and rec["total_children"] == 5,
    )

    # 3. Section 6: Multi-tenant GPU cost showback and idle waste report
    cost = compute_tenant_gpu_cost_and_waste(
        requested_gpu_hours=1000.0,
        active_utilized_gpu_hours=680.0,
        gpu_hour_rate_usd=4.0,
        shared_platform_overhead_usd=500.0,
    )
    check(
        "compute_tenant_gpu_cost_and_waste bills $4,500 ($4,000 GPU + $500 shared), flags 320 idle GPU-hours ($1,280 waste), and reports 68.0% efficiency",
        cost["total_billed_usd"] == 4500.0
        and cost["idle_gpu_hours"] == 320.0
        and cost["idle_wasted_usd"] == 1280.0
        and cost["utilization_efficiency_pct"] == 68.0,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
