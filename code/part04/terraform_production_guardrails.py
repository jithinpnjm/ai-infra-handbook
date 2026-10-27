"""Chapter 4.23 model: Production OPA/Rego guardrail evaluator (blocking prod
node-pool deletion, unversioned checkpoint buckets, and missing `ManagedBy`
tags), Terragrunt `path_relative_to_include()` DRY backend key generator, and
Terratest `SKIP_<stage>` (`RunTestStage`) test-stage runner.

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapters 8, 9, and 10:
  * Chapter 8 ("Production-Grade Terraform Code"): 20-item Production-Grade
    Infrastructure Checklist (Table 8-2), essential vs accidental complexity &
    yak shaving, decomposing monolithic `webserver-cluster` into composable
    `asg-rolling-deploy` + `alb` + `hello-world-app` (`modules/`, `examples/`,
    `test/`), `validation` vs `precondition` (`free_tier_eligible`) vs
    `postcondition` (`length(self.availability_zones) > 1`), `tfenv`
    (`.terraform-version`), and escape hatches (`local-exec`, `remote-exec`,
    `data "external"`).
  * Chapter 9 ("How to Test Terraform Code"): `cloud-nuke`/`aws-nuke`, static
    analysis (`tflint`, `tfsec`, `checkov`, OPA `enforce_tagging.rego`),
    Terratest unit tests (`random.UniqueId()`, `defer terraform.Destroy`,
    `http_helper.HttpGetWithRetry`), dependency injection (`var.mysql_config`),
    and `test_structure.RunTestStage` with `SKIP_<stage>=true`.
  * Chapter 10 ("How to Use Terraform as a Team"): The Golden Rule of Terraform
    ("The main branch of the live repository should be a 1:1 representation of
    what's actually deployed in production"), Terragrunt `remote_state`
    `path_relative_to_include()`, `find_in_parent_folders()`, `dependency`
    blocks, `run-all`, and incremental adoption.
- volume-10/05-terraform-for-infrastructure-as-code.md & volume-10/11.
"""
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple


def evaluate_production_guardrails(
    resource_changes: Sequence[Mapping[str, Any]],
    has_allow_prod_destroy_approval: bool = False,
) -> List[str]:
    """Model Section 5 & TUR Ch. 9 OPA/Rego policy checks on `plan.json`:
    1. Deny deleting a `google_container_node_pool` labeled `tier == 'prod'`
       unless `allow-prod-destroy` approval is granted.
    2. Deny creating/updating a `google_storage_bucket` without `versioning.enabled == True`.
    3. Deny creating/updating any resource missing `ManagedBy == 'Terraform'` label/tag.
    """
    denials: List[str] = []
    for rc in resource_changes:
        addr = str(rc["address"])
        rtype = str(rc["type"])
        change = rc.get("change", {})
        actions = change.get("actions", [])
        before = change.get("before") or {}
        after = change.get("after") or {}

        if rtype == "google_container_node_pool" and "delete" in actions:
            labels = before.get("labels", {})
            if labels.get("tier") == "prod" and not has_allow_prod_destroy_approval:
                denials.append(f"{addr} is a prod node pool: deletion needs the 'allow-prod-destroy' approval")

        if rtype == "google_storage_bucket" and ("create" in actions or "update" in actions):
            if not after.get("versioning_enabled", False):
                denials.append(f"{addr}: versioning must be enabled on buckets")

        if "create" in actions or "update" in actions:
            tags = after.get("labels") or after.get("tags") or {}
            if tags.get("ManagedBy") != "Terraform":
                denials.append(f"{addr}: missing required tag ManagedBy='Terraform'")

    return denials


def render_terragrunt_backend_key(root_dir: str, child_dir: str) -> str:
    """Model TUR Ch. 10 `key = "${path_relative_to_include()}/terraform.tfstate"`."""
    root_clean = root_dir.rstrip("/") + "/"
    if not child_dir.startswith(root_clean):
        raise ValueError(f"{child_dir!r} is not under {root_dir!r}")
    rel = child_dir[len(root_clean) :].strip("/")
    return f"{rel}/terraform.tfstate"


def run_terratest_stages(
    stages: Sequence[Tuple[str, Callable[[], None]]],
    env: Mapping[str, str],
) -> List[str]:
    """Model TUR Ch. 9 `test_structure.RunTestStage(t, stage_name, fn)` skipping
    any stage where `SKIP_<stage_name>` is set in `env`.
    """
    executed: List[str] = []
    for name, fn in stages:
        if env.get(f"SKIP_{name}"):
            executed.append(f"skipped:{name}")
        else:
            fn()
            executed.append(f"ran:{name}")
    return executed
