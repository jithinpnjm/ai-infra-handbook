"""Chapter 4.22 model: State secret-exposure auditor (comparing plaintext-in-state
patterns vs `manage_master_user_password`, `ephemeral`, and write-only `*_wo`
arguments), GitHub Actions OIDC `AssumeRoleWithWebIdentity` trust-policy
evaluator (`TUR` Ch. 6), and multi-provider `configuration_aliases` validator
(`TUR` Ch. 7).

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapters 6 & 7:
  * Chapter 6 ("Managing Secrets with Terraform"): 3 secret types (personal,
    customer, infrastructure), file-based (`aws_kms_secrets`, `sops`) vs
    centralized (`Vault`, `AWS Secrets Manager`, `Google Secret Manager`) stores,
    provider auth via `aws-vault`, EC2 IAM Instance Profiles (`169.254.169.254`),
    and GitHub Actions OIDC (`aws_iam_openid_connect_provider`,
    `sts:AssumeRoleWithWebIdentity` conditioned on `repo:<ORG>/<REPO>:ref:refs/heads/main`),
    and why `TF_VAR_*`, `aws_kms_secrets`, and `aws_secretsmanager_secret_version`
    still persist secrets in `terraform.tfstate` when passed to normal resource
    attributes.
  * Chapter 7 ("Working with Multiple Providers"): Provider RPC subprocess model,
    multi-region aliases (`aws.region_1`, `aws.region_2`, regional `data "aws_ami"`,
    RDS MySQL primary + cross-region read replica `replicate_source_db`),
    multi-account `assume_role` + `configuration_aliases = [aws.parent, aws.child]`,
    and combining `aws` (EKS) + `kubernetes` providers.
- volume-10/05-terraform-for-infrastructure-as-code.md & volume-10/11.
"""
from typing import Dict, List, Mapping, Sequence, Set, Tuple


def classify_secret_state_exposure(pattern: str) -> Dict[str, bool]:
    """Model Section 1 & 2 secret handling patterns and whether the secret
    plaintext is written into `terraform.tfstate` and `tfplan`:
    - 'workload_identity_iam': no secret exists -> not in state, not in CLI
    - 'manage_master_user_password': cloud service stores in Secrets Manager -> not in state
    - 'ephemeral_or_write_only': ephemeral resource + `password_wo` -> not in state
    - 'sensitive_var_or_data_source': `sensitive = true` / `data.aws_secretsmanager_secret_version`
      passed to standard `password` attribute -> redacted in CLI, but PLAINTEXT IN STATE!
    - 'random_password_resource': `random_password` -> redacted in CLI, PLAINTEXT IN STATE!
    """
    table = {
        "workload_identity_iam": {"in_state": False, "in_cli_output": False},
        "manage_master_user_password": {"in_state": False, "in_cli_output": False},
        "ephemeral_or_write_only": {"in_state": False, "in_cli_output": False},
        "sensitive_var_or_data_source": {"in_state": True, "in_cli_output": False},
        "random_password_resource": {"in_state": True, "in_cli_output": False},
        "unmarked_variable": {"in_state": True, "in_cli_output": True},
    }
    if pattern not in table:
        raise ValueError(f"unknown pattern {pattern!r}")
    return table[pattern]


def verify_github_oidc_assume_role(
    token_aud: str,
    token_sub: str,
    allowed_org_repo: str,
    allowed_branch: str = "main",
) -> bool:
    """Model TUR Ch. 6 `aws_iam_openid_connect_provider` + `AssumeRoleWithWebIdentity`
    trust policy condition:
      `token.actions.githubusercontent.com:aud == "sts.amazonaws.com"` and
      `token.actions.githubusercontent.com:sub == "repo:<ORG>/<REPO>:ref:refs/heads/<BRANCH>"`.
    """
    expected_sub = f"repo:{allowed_org_repo}:ref:refs/heads/{allowed_branch}"
    return token_aud == "sts.amazonaws.com" and token_sub == expected_sub


def validate_child_module_provider_wiring(
    *,
    child_has_provider_block: bool,
    required_configuration_aliases: Sequence[str],
    caller_providers_map: Mapping[str, str],
    root_defined_providers: Set[str],
) -> Tuple[bool, List[str]]:
    """Model Section 4 & TUR Ch. 7 rules for multi-provider modules:
    1. Child modules must NOT contain `provider "..." {}` blocks.
    2. Every alias declared in `configuration_aliases` must be passed by the
       caller in `providers = { ... }`.
    3. Every provider passed by the caller must exist in the root module.
    """
    errors: List[str] = []
    if child_has_provider_block:
        errors.append("child module must not declare a provider configuration block")
    for req_alias in required_configuration_aliases:
        if req_alias not in caller_providers_map:
            errors.append(f"missing required configuration_alias {req_alias!r} in module providers map")
    for mod_slot, root_prov in caller_providers_map.items():
        if root_prov not in root_defined_providers:
            errors.append(f"caller passed unknown root provider {root_prov!r} for slot {mod_slot!r}")
    return (len(errors) == 0), errors
