#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.29: Extending Kubernetes: CRDs and operators."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from crd_schema_conversion_sim import (
    convert_crd_via_hub_and_migrate_storage,
    evaluate_crd_schema_and_cel,
    reconcile_cr_with_finalizer_and_status,
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
    # 1. Section 2: Structural schema pruning, defaulting, and CEL cross-field & immutability rules
    ok_create, doc1, _ = evaluate_crd_schema_and_cel(
        {
            "targetPool": "h100-pool",
            "xid": {"codes": [48, 79]},  # defaults action='Cordon', windowSeconds=600
            "undeclaredField": "silently-pruned",
        }
    )
    bad_update, _, errs = evaluate_crd_schema_and_cel(
        {
            "targetPool": "mutated-pool",  # violates self == oldSelf!
            "xid": {"codes": [79], "action": "CordonAndDrain"},  # missing maxUnavailableNodes!
        },
        old_spec=doc1,
    )
    check(
        "evaluate_crd_schema_and_cel prunes undeclaredField, defaults action/windowSeconds, and catches CEL CordonAndDrain & immutability violations",
        ok_create is True
        and "undeclaredField" not in doc1
        and doc1["xid"]["action"] == "Cordon"
        and doc1["xid"]["windowSeconds"] == 600
        and bad_update is False
        and len(errs) == 2,
    )

    # 2. Section 2: Hub-and-spoke version conversion and storedVersions migration
    etcd_objs = [
        {"apiVersion": "platform.example.com/v1alpha1", "name": "p1", "xidCodes": [48, 79]},
        {"apiVersion": "platform.example.com/v1beta1", "name": "p2", "xid": {"codes": [63]}},
    ]
    mig = convert_crd_via_hub_and_migrate_storage(etcd_objs, new_storage_version="v1beta1")
    check(
        "convert_crd_via_hub_and_migrate_storage converts v1alpha1 xidCodes to v1beta1 xid.codes and narrows storedVersions to ['v1beta1']",
        mig["stored_versions"] == ["v1beta1"]
        and mig["migrated_objects"][0]["xid"] == {"codes": [48, 79]},
    )

    # 3. Section 2 & 3: Finalizer lifecycle and /status subresource observedGeneration
    cr: dict = {"metadata": {"name": "default", "generation": 3}}
    r1 = reconcile_cr_with_finalizer_and_status(cr)
    has_fin_after_create = "platform.example.com/cleanup" in cr["metadata"]["finalizers"]
    # Mark for deletion
    cr["metadata"]["deletionTimestamp"] = "2026-10-28T12:00:00Z"
    r2 = reconcile_cr_with_finalizer_and_status(cr)
    check(
        "reconcile_cr_with_finalizer_and_status adds finalizer, sets status.observedGeneration=3 without bumping generation, and removes finalizer on deletionTimestamp",
        has_fin_after_create is True
        and r1["generation"] == "3"
        and r1["observedGeneration"] == "3"
        and r2["can_delete_from_etcd"] == "True"
        and cr["metadata"]["finalizers"] == [],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
