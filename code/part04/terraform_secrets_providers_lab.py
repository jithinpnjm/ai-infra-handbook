#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.22: Terraform secrets and multiple providers."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_secrets_providers import (
    classify_secret_state_exposure,
    validate_child_module_provider_wiring,
    verify_github_oidc_assume_role,
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
    # 1. Section 1 & 2: State secret-exposure classification
    check(
        "sensitive vars and random_password still persist in state, whereas manage_master_user_password and ephemeral/write-only do not",
        classify_secret_state_exposure("sensitive_var_or_data_source")["in_state"] is True
        and classify_secret_state_exposure("random_password_resource")["in_state"] is True
        and classify_secret_state_exposure("manage_master_user_password")["in_state"] is False
        and classify_secret_state_exposure("ephemeral_or_write_only")["in_state"] is False,
    )

    # 2. Section 3 & TUR Ch. 6: GitHub Actions OIDC AssumeRoleWithWebIdentity condition check
    check(
        "verify_github_oidc_assume_role allows repo:acme/infra:ref:refs/heads/main and rejects feature branches or wrong audience",
        verify_github_oidc_assume_role("sts.amazonaws.com", "repo:acme/infra:ref:refs/heads/main", "acme/infra") is True
        and verify_github_oidc_assume_role("sts.amazonaws.com", "repo:acme/infra:ref:refs/heads/feat", "acme/infra") is False
        and verify_github_oidc_assume_role("wrong-aud", "repo:acme/infra:ref:refs/heads/main", "acme/infra") is False,
    )

    # 3. Section 4 & TUR Ch. 7: Multi-provider configuration_aliases wiring validation
    ok_wiring, _ = validate_child_module_provider_wiring(
        child_has_provider_block=False,
        required_configuration_aliases=["aws.parent", "aws.child"],
        caller_providers_map={"aws.parent": "aws.mgmt", "aws.child": "aws.prod"},
        root_defined_providers={"aws.mgmt", "aws.prod"},
    )
    bad_wiring, errs = validate_child_module_provider_wiring(
        child_has_provider_block=True,
        required_configuration_aliases=["aws.parent", "aws.child"],
        caller_providers_map={"aws.parent": "aws.mgmt"},
        root_defined_providers={"aws.mgmt"},
    )
    check(
        "validate_child_module_provider_wiring accepts valid alias mapping and flags internal provider blocks & missing aliases",
        ok_wiring is True and bad_wiring is False and len(errs) == 2,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
