#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.6: Controllers and the reconcile loop: how Kubernetes thinks."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from controller_reconcile_simulator import (
    DeduplicatingWorkQueue,
    reconcile_gpu_node_remediation,
    reconcile_replicaset,
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
    # 1. Section 2: WorkQueue key deduplication, single-worker-per-key, and exponential backoff
    wq = DeduplicatingWorkQueue()
    wq.add("default/web")
    wq.add("default/web")
    wq.add("default/web")
    check("DeduplicatingWorkQueue collapses 3 rapid events for 'default/web' into 1 queue entry", len(wq.queue) == 1)
    k = wq.get()
    # Event arrives while default/web is in processing
    wq.add("default/web")
    check(
        "While 'default/web' is in processing, a new event marks it dirty without queueing a second parallel worker",
        k == "default/web" and len(wq.queue) == 0 and "default/web" in wq.dirty,
    )
    wq.done("default/web")
    d1 = wq.add_rate_limited("default/failing")
    d2 = wq.add_rate_limited("default/failing")
    check("done() re-queues dirty key and add_rate_limited doubles backoff (1.0s -> 2.0s)", wq.queue[0] == "default/web" and d1 == 1.0 and d2 == 2.0)

    # 2. Section 3 & 4 & KUR Ch. 9: ReplicaSet quarantining (orphan on label removal), adoption, and scale-up
    pods = [
        {"name": "web-1", "labels": {"app": "web"}, "owner_uid": "rs-1"},
        {"name": "web-quarantined", "labels": {}, "owner_uid": "rs-1"},  # label removed by operator!
        {"name": "web-standalone", "labels": {"app": "web"}, "owner_uid": None},  # ownerless matching pod -> adopted!
    ]
    res = reconcile_replicaset("web", "rs-1", desired_replicas=3, selector_label=("app", "web"), pods=pods)
    check(
        "reconcile_replicaset orphans unlabeled pod 'web-quarantined', adopts 'web-standalone', and creates 1 pod to reach 3 replicas",
        res["orphaned"] == ["web-quarantined"]
        and res["adopted"] == ["web-standalone"]
        and len(res["created"]) == 1
        and len(res["active_owned"]) == 3,
    )

    # 3. Section 7: Budget-bounded GPU fault remediation controller
    nodes = [
        {"name": "gpu-01", "cordoned": True, "sustained_xid_fault": True},
        {"name": "gpu-02", "cordoned": False, "sustained_xid_fault": True},
        {"name": "gpu-03", "cordoned": False, "sustained_xid_fault": True},
        {"name": "gpu-04", "cordoned": False, "sustained_xid_fault": False},
    ]
    rem = reconcile_gpu_node_remediation(nodes, max_concurrent_cordons=2)
    check(
        "reconcile_gpu_node_remediation cordons gpu-02 (reaching budget=2) and defers gpu-03 to prevent fleet-wide outage",
        rem["newly_cordoned"] == ["gpu-02"] and rem["budget_deferred"] == ["gpu-03"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()