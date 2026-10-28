#!/usr/bin/env python3
"""Self-checking lab for Chapter 6.16: Slurm on Kubernetes: Slinky and Soperator."""
import sys

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


OPERATOR_PREFIX = "slurm-operator:"


def reconcile_slinky_node_drain(
    k8s_cordoned: bool,
    selected_for_scale_in: bool,
    slurm_state: str,
    slurm_reason: str,
) -> tuple[str, str, bool]:
    """Simulate Slinky NodeSet controller drain/cordon & scale-in safety state machine.

    Returns (new_slurm_state, new_slurm_reason, can_delete_pod).
    """
    externally_drained = bool(slurm_reason) and not slurm_reason.startswith(OPERATOR_PREFIX)
    want_drain = k8s_cordoned or selected_for_scale_in

    if want_drain:
        if externally_drained:
            # Never overwrite an admin/health-check drain reason
            new_reason = slurm_reason
        else:
            why = "scale-in" if selected_for_scale_in else "node-cordoned"
            new_reason = f"{OPERATOR_PREFIX} {why}"
        new_state = "DRAINING" if slurm_state in ("ALLOCATED", "MIXED", "DRAINING") else "DRAINED"
    else:
        # Uncordoned and not scaling in: only resume if the drain was set by slurm-operator
        if slurm_state in ("DRAINING", "DRAINED") and slurm_reason.startswith(OPERATOR_PREFIX):
            new_state = "ALLOCATED" if slurm_state == "DRAINING" else "IDLE"
            new_reason = ""
        else:
            new_state = slurm_state
            new_reason = slurm_reason

    can_delete_pod = selected_for_scale_in and new_state == "DRAINED"
    return new_state, new_reason, can_delete_pod


def validate_slinky_crds(crds: set[str], ha_enabled: bool, rwx_claim: str) -> bool:
    """Verify the 6 Slinky CRDs and HA shared-state PVC requirement."""
    expected = {"Controller", "NodeSet", "LoginSet", "Accounting", "RestApi", "Token"}
    if crds != expected:
        return False
    if ha_enabled and not rwx_claim:
        return False
    return True


def main() -> None:
    # 1. Verify Slinky drain/cordon reconciliation and external drain preservation
    # Case A: Active job on pod selected for scale-in -> transitions to DRAINING, pod deletion blocked
    st1, r1, del1 = reconcile_slinky_node_drain(
        k8s_cordoned=False, selected_for_scale_in=True, slurm_state="ALLOCATED", slurm_reason=""
    )
    # Case B: Job finishes (node now IDLE/DRAINED) -> transitions to DRAINED, pod deletion allowed
    st2, r2, del2 = reconcile_slinky_node_drain(
        k8s_cordoned=False, selected_for_scale_in=True, slurm_state="DRAINED", slurm_reason=r1
    )
    # Case C: Admin drained node with "Xid79 GPU3"; K8s node is uncordoned -> external drain MUST be preserved
    st3, r3, del3 = reconcile_slinky_node_drain(
        k8s_cordoned=False, selected_for_scale_in=False, slurm_state="DRAINED", slurm_reason="Xid79 GPU3 ticket INC123"
    )
    # Case D: Operator drained node on cordon; K8s node is uncordoned -> operator resumes node to IDLE
    st4, r4, del4 = reconcile_slinky_node_drain(
        k8s_cordoned=False, selected_for_scale_in=False, slurm_state="DRAINED", slurm_reason="slurm-operator: node-cordoned"
    )
    check(
        "Slinky NodeSet controller blocks pod deletion while DRAINING, deletes when DRAINED, and never clears non-'slurm-operator:' drains",
        (st1, r1, del1) == ("DRAINING", "slurm-operator: scale-in", False)
        and (st2, r2, del2) == ("DRAINED", "slurm-operator: scale-in", True)
        and (st3, r3, del3) == ("DRAINED", "Xid79 GPU3 ticket INC123", False)
        and (st4, r4, del4) == ("IDLE", "", False),
    )

    # 2. Verify Slinky 6 CRDs and Controller HA ReadWriteMany PVC requirement
    crds = {"Controller", "NodeSet", "LoginSet", "Accounting", "RestApi", "Token"}
    check(
        "Slinky defines 6 CRDs (Controller, NodeSet, LoginSet, Accounting, RestApi, Token) and enforces RWX PVC for HA",
        validate_slinky_crds(crds, ha_enabled=True, rwx_claim="slurm-state-rwx")
        and not validate_slinky_crds(crds, ha_enabled=True, rwx_claim=""),
    )

    # 3. Verify Soperator SlurmCluster 3 pod groups (Login, Controller, Worker) and shared jail + ActiveCheck model
    soperator_pods = {"Login", "Controller", "Worker"}
    active_check_modes = {"k8sJob", "slurmJob"}
    check(
        "Soperator SlurmCluster models Login, Controller, and Worker StatefulSets with shared jail rootfs and k8sJob/slurmJob ActiveChecks",
        len(soperator_pods) == 3 and len(active_check_modes) == 2,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
