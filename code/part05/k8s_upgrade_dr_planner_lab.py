#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.20: Upgrades, etcd backup and restore, and disaster recovery."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from k8s_upgrade_dr_planner import (
    evaluate_dr_rpo_rto,
    evaluate_etcd_upgrade_quorum_safety,
    validate_k8s_version_skew,
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
    # 1. Section 1: Kubernetes Version Skew Policy validator
    ok_skew, _ = validate_k8s_version_skew(
        apiserver_versions=["1.31.1", "1.30.4", "1.30.4"],
        controller_manager_version="1.30.4",
        scheduler_version="1.30.4",
        kubelet_versions=["1.30.4", "1.28.9"],
        kubectl_version="1.31.1",
    )
    bad_skew, errs = validate_k8s_version_skew(
        apiserver_versions=["1.32.0", "1.30.4"],  # 2 minors apart!
        controller_manager_version="1.33.0",  # newer than apiserver!
        scheduler_version="1.28.0",  # 2 minors older than min apiserver!
        kubelet_versions=["1.31.0"],  # newer than min apiserver 1.30!
        kubectl_version="1.27.0",  # >1 minor older!
    )
    check(
        "validate_k8s_version_skew accepts rolling 1.30->1.31 HA upgrade state and flags 5 skew violations",
        ok_skew is True and bad_skew is False and len(errs) == 5,
    )

    # 2. Section 5 & PK Ch. 2: Dedicated etcd upgrade strategy safety (subtractive 3->2->3 vs additive/in-place)
    sub = evaluate_etcd_upgrade_quorum_safety(3, "subtractive_remove_first")
    add = evaluate_etcd_upgrade_quorum_safety(3, "additive_learner_first")
    check(
        "PK Ch. 2 etcd upgrade check flags subtractive 3->2->3 (0 fault tolerance at 2 voting members) and approves additive learner",
        sub["safe"] is False
        and sub["active_voting_during_step"] == 2
        and sub["fault_tolerance_during_step"] == 0
        and add["safe"] is True,
    )

    # 3. Section 7: AI training/inference DR RPO and RTO evaluator
    dr = evaluate_dr_rpo_rto(
        checkpoint_interval_min=30.0,
        offsite_sync_lag_min=5.0,
        target_rpo_min=60.0,
        cluster_restore_min=25.0,
        job_reload_min=10.0,
        target_rto_min=60.0,
    )
    check(
        "evaluate_dr_rpo_rto computes achieved_rpo_min=35.0m and achieved_rto_min=35.0m (meeting 60m RPO/RTO targets)",
        dr["achieved_rpo_min"] == 35.0
        and dr["achieved_rto_min"] == 35.0
        and dr["rpo_met"] is True
        and dr["rto_met"] is True,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
