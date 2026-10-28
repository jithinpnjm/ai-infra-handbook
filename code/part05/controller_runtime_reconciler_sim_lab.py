#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.31: Operators in Go: controller-runtime and kubebuilder."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from controller_runtime_reconciler_sim import (
    convert_myresource_spoke_to_hub_and_back,
    evaluate_watch_predicates,
    set_status_condition_and_check_noop,
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
    # 1. Section 5 & KPG Ch. 10: GenerationChangedPredicate & Node heartbeat predicate
    cr_v1 = {"metadata": {"generation": 2}, "status": {"ready": False}}
    cr_status_only = {"metadata": {"generation": 2}, "status": {"ready": True}}
    cr_spec_edit = {"metadata": {"generation": 3}, "status": {"ready": True}}

    node_hb1 = {
        "metadata": {"labels": {"gpu": "h100"}},
        "spec": {"unschedulable": False},
        "status": {"conditions": [{"type": "Ready", "status": "True", "reason": "KubeletReady", "lastHeartbeatTime": "10:00:00"}]},
    }
    node_hb2 = {
        "metadata": {"labels": {"gpu": "h100"}},
        "spec": {"unschedulable": False},
        "status": {"conditions": [{"type": "Ready", "status": "True", "reason": "KubeletReady", "lastHeartbeatTime": "10:00:10"}]},
    }
    node_xid = {
        "metadata": {"labels": {"gpu": "h100"}},
        "spec": {"unschedulable": False},
        "status": {"conditions": [{"type": "GPUXIDError", "status": "True", "reason": "XID79", "lastHeartbeatTime": "10:00:20"}]},
    }
    check(
        "evaluate_watch_predicates skips status-only CR updates & Node heartbeats, and enqueues on spec generation bump or XID condition",
        evaluate_watch_predicates(cr_v1, cr_status_only, is_primary_cr=True) is False
        and evaluate_watch_predicates(cr_v1, cr_spec_edit, is_primary_cr=True) is True
        and evaluate_watch_predicates(node_hb1, node_hb2, is_primary_cr=False) is False
        and evaluate_watch_predicates(node_hb2, node_xid, is_primary_cr=False) is True,
    )

    # 2. Section 4 & KPG Ch. 11: meta.SetStatusCondition lastTransitionTime preservation & no-op skip
    conds0 = [{"type": "Ready", "status": "True", "reason": "Healthy", "message": "ok", "lastTransitionTime": "2026-10-28T00:00:00Z"}]
    # Same status/reason/message at a later time -> should_patch is False, lastTransitionTime preserved!
    should_patch_noop, conds1 = set_status_condition_and_check_noop(
        conds0,
        {"type": "Ready", "status": "True", "reason": "Healthy", "message": "ok"},
        now_iso="2026-10-28T01:00:00Z",
    )
    # Flip status to False -> should_patch is True, lastTransitionTime updated!
    should_patch_flip, conds2 = set_status_condition_and_check_noop(
        conds1,
        {"type": "Ready", "status": "False", "reason": "BudgetExhausted", "message": "blocked"},
        now_iso="2026-10-28T02:00:00Z",
    )
    check(
        "set_status_condition_and_check_noop skips no-op status write (preserving lastTransitionTime) and patches when status flips",
        should_patch_noop is False
        and conds1[0]["lastTransitionTime"] == "2026-10-28T00:00:00Z"
        and should_patch_flip is True
        and conds2[0]["lastTransitionTime"] == "2026-10-28T02:00:00Z",
    )

    # 3. KPG Ch. 13: Kubebuilder Hub (v1alpha1 memory) <-> Spoke (v1beta1 memoryRequest) round-trip conversion
    spoke = {
        "apiVersion": "mygroup.myid.dev/v1beta1",
        "kind": "MyResource",
        "metadata": {"name": "sample"},
        "spec": {"image": "nginx", "memoryRequest": "512Mi"},
        "status": {"state": "Ready"},
    }
    hub, roundtrip = convert_myresource_spoke_to_hub_and_back(spoke)
    check(
        "KPG Ch. 13 ConvertTo/ConvertFrom round-trips v1beta1.spec.memoryRequest <-> v1alpha1.spec.memory losslessly",
        hub["spec"]["memory"] == "512Mi" and roundtrip == spoke,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
