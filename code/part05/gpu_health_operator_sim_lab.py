#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.32: Project A: GPU node health operator."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gpu_health_operator_sim import (
    ANNOTATION_OWNER,
    compute_budget,
    is_pod_evictable,
    judge_node,
    plan_remediation,
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
    # 1. Judge 6 cases: False >=2m (unhealthy), False <2m (pending + wait_for), True >=5m (healthy),
    #    True <5m (recovering), absent and Unknown (neither healthy nor unhealthy)
    pol = {"name": "h100-pool", "conditionType": "GPUHealthy", "unhealthyForSec": 120.0, "healthyForSec": 300.0}
    v_unhealthy = judge_node(pol, {"name": "n1", "conditions": [{"type": "GPUHealthy", "status": "False", "lastTransitionSec": 0.0}]}, now_sec=150.0)
    v_pending = judge_node(pol, {"name": "n2", "conditions": [{"type": "GPUHealthy", "status": "False", "lastTransitionSec": 100.0}]}, now_sec=150.0)
    v_healthy = judge_node(pol, {"name": "n3", "conditions": [{"type": "GPUHealthy", "status": "True", "lastTransitionSec": 0.0}]}, now_sec=350.0)
    v_absent = judge_node(pol, {"name": "n4", "conditions": []}, now_sec=150.0)
    v_unknown = judge_node(pol, {"name": "n5", "conditions": [{"type": "GPUHealthy", "status": "Unknown", "lastTransitionSec": 0.0}]}, now_sec=500.0)
    check(
        "judge_node classifies stabilized False (unhealthy), recent False (pending, wait=70s), stabilized True (healthy), and absent or Unknown (neither)",
        v_unhealthy.unhealthy is True
        and (v_pending.pending is True and v_pending.wait_for_sec == 70.0)
        and v_healthy.healthy is True
        and (v_absent.healthy is False and v_absent.unhealthy is False and v_absent.pending is False)
        and (v_unknown.unhealthy is False and v_unknown.healthy is False),
    )

    # 2. Budget & Plan: 1 human-cordoned node + 3 unhealthy nodes under budget=2 -> 1 acted on ('n1'), 2 blocked ('n2', 'n3')
    b_val = compute_budget("20%", matched=10)
    b_invalid = compute_budget("-5", matched=10)
    verdicts = [
        judge_node(pol, {"name": "n0-human-maint", "unschedulable": True, "conditions": []}, now_sec=200.0),
        judge_node(pol, {"name": "n3", "conditions": [{"type": "GPUHealthy", "status": "False", "lastTransitionSec": 0.0}]}, now_sec=200.0),
        judge_node(pol, {"name": "n1", "conditions": [{"type": "GPUHealthy", "status": "False", "lastTransitionSec": 0.0}]}, now_sec=200.0),
        judge_node(pol, {"name": "n2", "conditions": [{"type": "GPUHealthy", "status": "False", "lastTransitionSec": 0.0}]}, now_sec=200.0),
    ]
    act, blocked = plan_remediation(verdicts, budget=b_val)
    check(
        "compute_budget('20%', 10)=2 (invalid->0) and plan_remediation counts human cordon against budget, acting on ['n1'] and blocking ['n2', 'n3']",
        b_val == 2 and b_invalid == 0 and act == ["n1"] and blocked == ["n2", "n3"],
    )

    # 3. evictable() skips Succeeded/Failed, mirror pods, and DaemonSet pods while evicting normal workload pods
    ok_work = is_pod_evictable({"phase": "Running", "ownerReferences": [{"kind": "ReplicaSet", "controller": True}]})
    skip_ds = is_pod_evictable({"phase": "Running", "ownerReferences": [{"kind": "DaemonSet", "controller": True}]})
    skip_mirror = is_pod_evictable({"phase": "Running", "annotations": {"kubernetes.io/config.mirror": "hash"}})
    skip_done = is_pod_evictable({"phase": "Succeeded"})
    check(
        "is_pod_evictable admits Running ReplicaSet pod and skips DaemonSet, mirror, and Succeeded pods",
        ok_work is True and skip_ds is False and skip_mirror is False and skip_done is False,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
