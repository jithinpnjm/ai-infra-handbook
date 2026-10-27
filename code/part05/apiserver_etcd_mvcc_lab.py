#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.5: The API server and etcd: how a request becomes cluster state."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from apiserver_etcd_mvcc import (
    EtcdMVCCSimulator,
    compute_apf_concurrency_limit,
    evaluate_ssa_field_ownership,
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
    # 1. Section 3 & 7: etcd MVCC revisions, 409 Conflict on stale RV, compaction, and 410 Gone vs BOOKMARK
    store = EtcdMVCCSimulator()
    rv1 = store.put("/registry/configmaps/default/cfg", {"data": "v1"})
    rv2 = store.put("/registry/configmaps/default/cfg", {"data": "v2"}, expected_rv=rv1)
    got_409 = False
    try:
        store.put("/registry/configmaps/default/cfg", {"data": "stale"}, expected_rv=rv1)
    except RuntimeError as exc:
        got_409 = "409 Conflict" in str(exc)

    store.compact(rv2)
    gone_events = store.watch_from("/registry/configmaps/default/cfg", start_rv=rv1)
    bookmark_events = store.watch_from("/registry/configmaps/default/cfg", start_rv=rv2, allow_bookmarks=True)
    check(
        "EtcdMVCCSimulator increments revisions, rejects stale update with 409 Conflict, returns 410 Gone below compacted revision, and emits BOOKMARK at head",
        rv1 == 2
        and rv2 == 3
        and got_409 is True
        and "410 Gone" in gone_events[0][1]
        and bookmark_events == [(3, "BOOKMARK")],
    )

    # 2. Section 4: Server-Side Apply (managedFields) field-ownership conflict and --force-conflicts
    ok_conflict, _, conflicts = evaluate_ssa_field_ownership(
        current_owners={"/spec/replicas": "kube-controller-manager-hpa", "/spec/image": "argocd"},
        applying_manager="argocd",
        applied_fields={"/spec/replicas": 2, "/spec/image": "vllm:v2"},
        force_conflicts=False,
    )
    ok_forced, owners_forced, _ = evaluate_ssa_field_ownership(
        current_owners={"/spec/replicas": "kube-controller-manager-hpa"},
        applying_manager="argocd",
        applied_fields={"/spec/replicas": 2},
        force_conflicts=True,
    )
    check(
        "evaluate_ssa_field_ownership detects 409 conflict when argocd touches HPA-owned /spec/replicas without force_conflicts",
        ok_conflict is False
        and len(conflicts) == 1
        and ok_forced is True
        and owners_forced["/spec/replicas"] == "argocd",
    )

    # 3. Section 6: API Priority and Fairness concurrency allocation
    alloc = compute_apf_concurrency_limit(
        server_total_concurrency=600,
        level_shares={"system": 30, "node-high": 40, "batch-controllers": 30, "global-default": 20},
    )
    check(
        "compute_apf_concurrency_limit allocates 150 concurrent requests to batch-controllers (30/120 of 600)",
        alloc == {"system": 150, "node-high": 200, "batch-controllers": 150, "global-default": 100},
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
