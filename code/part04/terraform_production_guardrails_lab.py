#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.23: Production-grade Terraform: structure, testing and team workflows."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_production_guardrails import (
    evaluate_production_guardrails,
    render_terragrunt_backend_key,
    run_terratest_stages,
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
    # 1. Section 5 & TUR Ch. 9: OPA/Rego production guardrails (prod node pool delete, bucket versioning, ManagedBy tag)
    bad_changes = [
        {
            "address": "google_container_node_pool.h100",
            "type": "google_container_node_pool",
            "change": {"actions": ["delete"], "before": {"labels": {"tier": "prod"}}},
        },
        {
            "address": "google_storage_bucket.ckpt",
            "type": "google_storage_bucket",
            "change": {"actions": ["create"], "after": {"versioning_enabled": False, "labels": {}}},
        },
    ]
    denials = evaluate_production_guardrails(bad_changes, has_allow_prod_destroy_approval=False)
    good_changes = [
        {
            "address": "google_storage_bucket.ckpt",
            "type": "google_storage_bucket",
            "change": {
                "actions": ["create"],
                "after": {"versioning_enabled": True, "labels": {"ManagedBy": "Terraform"}},
            },
        }
    ]
    check(
        "evaluate_production_guardrails blocks prod node-pool deletion, unversioned bucket, and missing ManagedBy tag, and passes compliant plan",
        len(denials) == 3 and evaluate_production_guardrails(good_changes) == [],
    )

    # 2. TUR Ch. 10: Terragrunt path_relative_to_include() DRY backend key generation
    key = render_terragrunt_backend_key(
        "/repo/live",
        "/repo/live/prod/us-central1/gpu-pools",
    )
    check(
        "render_terragrunt_backend_key computes 'prod/us-central1/gpu-pools/terraform.tfstate'",
        key == "prod/us-central1/gpu-pools/terraform.tfstate",
    )

    # 3. TUR Ch. 9: Terratest test_structure.RunTestStage with SKIP_<stage>=true
    stages = [
        ("deploy_db", lambda: None),
        ("deploy_app", lambda: None),
        ("validate_app", lambda: None),
        ("teardown_app", lambda: None),
        ("teardown_db", lambda: None),
    ]
    dev_loop = run_terratest_stages(stages, {"SKIP_deploy_db": "true", "SKIP_teardown_db": "true", "SKIP_teardown_app": "true"})
    check(
        "run_terratest_stages skips deploy_db/teardown_db/teardown_app during fast local iteration and runs deploy_app + validate_app",
        dev_loop
        == [
            "skipped:deploy_db",
            "ran:deploy_app",
            "ran:validate_app",
            "skipped:teardown_app",
            "skipped:teardown_db",
        ],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
