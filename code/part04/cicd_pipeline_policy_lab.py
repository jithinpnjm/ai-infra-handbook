#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.2: CI/CD pipelines: concepts and design."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cicd_pipeline_policy import (
    authorize_oidc_token_claims,
    classify_terraform_detailed_exitcode,
    evaluate_terraform_plan_policies,
    simulate_staged_fleet_rollout,
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
    # 1. Section 7 OPA/Rego policy checks on Terraform plan JSON
    bad_plan = {
        "resource_changes": [
            *[
                {
                    "address": f"aws_instance.gpu[{i}]",
                    "type": "aws_instance",
                    "change": {"actions": ["create"], "after": {"instance_type": "p5.48xlarge"}},
                }
                for i in range(18)
            ],
            {
                "address": "aws_s3_bucket.checkpoints",
                "type": "aws_s3_bucket",
                "change": {"actions": ["delete"], "before": {"tags": {"Mission-Critical": "true"}}},
            },
        ],
        "override_capacity_tag": False,
    }
    denials = evaluate_terraform_plan_policies(bad_plan)
    override_plan = dict(bad_plan, resource_changes=bad_plan["resource_changes"][:18], override_capacity_tag=True)
    check(
        "Policy gate blocks >16 restricted p5.48xlarge instances and Mission-Critical deletion, and honors Override-Capacity",
        len(denials) == 2
        and "plan creates 18 restricted GPU instances" in denials[0]
        and "aws_s3_bucket.checkpoints is tagged Mission-Critical" in denials[1]
        and evaluate_terraform_plan_policies(override_plan) == [],
    )

    # 2. Section 5 OIDC claim-to-role federation guard (plan vs apply)
    pr_claims = {"repository": "org/infra", "ref": "refs/pull/42/merge", "environment": ""}
    main_claims = {"repository": "org/infra", "ref": "refs/heads/main", "environment": "prod"}
    fork_claims = {"repository": "attacker/infra", "ref": "refs/heads/main", "environment": "prod"}
    ok_plan, _ = authorize_oidc_token_claims(pr_claims, "tf-plan-readonly")
    deny_pr_apply, _ = authorize_oidc_token_claims(pr_claims, "tf-apply-write")
    ok_main_apply, _ = authorize_oidc_token_claims(main_claims, "tf-apply-write")
    deny_fork, _ = authorize_oidc_token_claims(fork_claims, "tf-plan-readonly")
    check(
        "OIDC guard grants PR read-only plan role, denies PR write apply role, grants main+prod apply role, and blocks forks",
        ok_plan is True and deny_pr_apply is False and ok_main_apply is True and deny_fork is False,
    )

    # 3. Section 9 Staged fleet rollout (canary halt vs batch max_fail_percentage halt vs full completion)
    fleet = [f"gpu{i:02d}" for i in range(1, 21)]
    r_canary_fail = simulate_staged_fleet_rollout(fleet, failing_nodes={"gpu02"}, canary_count=2, serial_batch_size=5, max_fail_percentage=10.0)
    r_batch2_fail = simulate_staged_fleet_rollout(fleet, failing_nodes={"gpu09"}, canary_count=2, serial_batch_size=5, max_fail_percentage=10.0)
    r_ok = simulate_staged_fleet_rollout(fleet, failing_nodes=set(), canary_count=2, serial_batch_size=5, max_fail_percentage=10.0)
    check(
        "Fleet rollout halts immediately on canary failure, halts at batch_2 when 1/5 (20% > 10%) fails, and completes 20/20 when healthy",
        r_canary_fail["halted_at"] == "canary"
        and len(r_canary_fail["upgraded"]) == 1
        and r_batch2_fail["halted_at"] == "batch_2"
        and r_ok["halted_at"] == "completed"
        and len(r_ok["upgraded"]) == 20,
    )

    # 4. Section 11 Drift detection (-detailed-exitcode 0, 1, 2)
    check(
        "terraform plan -detailed-exitcode maps 0->clean, 1->error, and 2->drift_alert_only (stateful) vs drift_auto_heal (stateless)",
        classify_terraform_detailed_exitcode(0, True) == "clean"
        and classify_terraform_detailed_exitcode(1, True) == "error"
        and classify_terraform_detailed_exitcode(2, True) == "drift_alert_only"
        and classify_terraform_detailed_exitcode(2, False) == "drift_auto_heal",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
