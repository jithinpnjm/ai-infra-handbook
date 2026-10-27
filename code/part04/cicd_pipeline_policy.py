"""Chapter 4.2 model: Infrastructure CI/CD pipeline policy evaluation (OPA/Rego
equivalent on Terraform plan JSON), OIDC claim-to-role federation guard,
staged canary + batch rollout simulator with `serial` and `max_fail_percentage`,
and `terraform plan -detailed-exitcode` drift classification.

Sources modeled:
- Christian Adell, Scott Lowe, Matt Oswalt & Jason Edelman, Network
  Programmability and Automation, 2nd ed. (network-programmability-and-automation-
  2nd-edition, NPA), Chapter 13 ("Continuous Integration"):
  * Removing humans from the direct control path ("Change Management Theater" /
    CAB meetings vs automated CI/CD pipeline), release engineers, and cookie-
    cutter vs snowflake network designs.
  * Continuous Integration vs Continuous Delivery vs Continuous Deployment, and
    Test-Driven Development (TDD).
  * 5-part network CI pipeline (Peer review on GitHub/GitLab/Gerrit/Bitbucket,
    Build automation with `validate_yaml.py` & `tox -epep8/-epy38/-ecover`,
    Deployment validation across Operational state/Basic connectivity/End-to-end
    performance with NAPALM, Batfish, Forward Networks, NetBeez, ThousandEyes,
    Test/dev/staging virtual topologies with Vagrant/Containerlab/Terraform, and
    Deployment strategies: Deploy in place, Rolling, Canary, Blue/Green with
    Junos XML `<bgp operation="replace">` ensuring WISB == WIRI).
- Bas Meijer, Lorin Hochstein & René Moser, Ansible: Up and Running, 3rd ed.
  (ansible-up-and-running-3rd-edition, AUR), Chapter 22 ("CI/CD and Ansible"):
  * Martin Fowler's 2006 CI definition & 4-VM CI/CD stack (Sonatype Nexus3 artifact
    proxy, Gitea + MySQL, SonarQube + PostgreSQL, and Jenkins).
  * Jenkins Configuration as Code (`casc` `/var/lib/jenkins/casc_configs/jenkins.yaml`,
    `-Dcasc.jenkins.config=...`), Job DSL seed job (`jobs.groovy.j2` +
    `jenkins-cli.jar reload-jcasc-configuration`), Declarative `Jenkinsfile`
    running Molecule stages (`syntax`, `lint`, `converge`, `verify`, `idempotence`),
    and `ansiblePlaybook` vs `ansibleTower` (`jobTemplate: '1234'`) plugins.
- volume-10/11-cicd-for-infrastructure-and-cluster-configuration.md.
"""
from typing import Dict, List, Sequence, Set, Tuple


RESTRICTED_GPU_TYPES: Set[str] = {"p5.48xlarge", "p4d.24xlarge"}


def evaluate_terraform_plan_policies(plan_json: Dict[str, object]) -> List[str]:
    """Model Section 7 OPA/Rego policy rules over `terraform show -json tfplan`:
    1. Deny creating > 16 restricted GPU instances unless Override-Capacity tag is present.
    2. Deny deleting any resource tagged `Mission-Critical == "true"`.
    """
    denials: List[str] = []
    resource_changes: Sequence[Dict[str, object]] = plan_json.get("resource_changes", [])  # type: ignore[assignment]

    created_restricted = [
        rc
        for rc in resource_changes
        if rc.get("type") == "aws_instance"
        and "create" in rc.get("change", {}).get("actions", [])  # type: ignore[attr-defined]
        and rc.get("change", {}).get("after", {}).get("instance_type") in RESTRICTED_GPU_TYPES  # type: ignore[attr-defined]
    ]

    has_override_tag = bool(plan_json.get("override_capacity_tag", False))
    if len(created_restricted) > 16 and not has_override_tag:
        denials.append(
            f"plan creates {len(created_restricted)} restricted GPU instances; add the Override-Capacity tag after approval"
        )

    for rc in resource_changes:
        change = rc.get("change", {})  # type: ignore[assignment]
        actions = change.get("actions", [])  # type: ignore[attr-defined]
        before_tags = (change.get("before") or {}).get("tags", {})  # type: ignore[attr-defined]
        if "delete" in actions and before_tags.get("Mission-Critical") == "true":
            denials.append(f"{rc['address']} is tagged Mission-Critical and cannot be deleted by pipeline")

    return denials


def authorize_oidc_token_claims(
    claims: Dict[str, str],
    requested_role: str,
    expected_repo: str = "org/infra",
) -> Tuple[bool, str]:
    """Model Section 5 OIDC federation trust policy separating `plan` (read-only)
    from `apply` (write, restricted to `refs/heads/main` and `environment=prod|staging`).
    """
    if claims.get("repository") != expected_repo:
        return False, "denied: untrusted repository or fork"
    if requested_role == "tf-plan-readonly":
        return True, "allowed: read-only plan role"
    if requested_role == "tf-apply-write":
        if claims.get("ref") == "refs/heads/main" and claims.get("environment") in {"staging", "prod"}:
            return True, "allowed: write apply role on protected main branch and environment"
        return False, "denied: apply role requires refs/heads/main and protected environment"
    return False, f"denied: unknown role {requested_role!r}"


def simulate_staged_fleet_rollout(
    nodes: Sequence[str],
    failing_nodes: Set[str],
    canary_count: int = 2,
    serial_batch_size: int = 5,
    max_fail_percentage: float = 10.0,
) -> Dict[str, object]:
    """Model Section 9 canary + batched fleet rollout with `serial` and
    `max_fail_percentage` stop-the-line halting.
    """
    upgraded: List[str] = []
    failed: List[str] = []

    canary = list(nodes[:canary_count])
    for n in canary:
        if n in failing_nodes:
            failed.append(n)
            return {
                "halted_at": "canary",
                "upgraded": upgraded,
                "failed": failed,
            }
        upgraded.append(n)

    remaining = list(nodes[canary_count:])
    for idx in range(0, len(remaining), serial_batch_size):
        batch = remaining[idx : idx + serial_batch_size]
        batch_failures = 0
        for n in batch:
            if n in failing_nodes:
                failed.append(n)
                batch_failures += 1
            else:
                upgraded.append(n)
        fail_pct = (batch_failures / len(batch)) * 100.0 if batch else 0.0
        if fail_pct > max_fail_percentage:
            return {
                "halted_at": f"batch_{idx // serial_batch_size + 1}",
                "upgraded": upgraded,
                "failed": failed,
            }

    return {
        "halted_at": "completed",
        "upgraded": upgraded,
        "failed": failed,
    }


def classify_terraform_detailed_exitcode(exit_code: int, resource_stateful: bool) -> str:
    """Model Section 11 `terraform plan -detailed-exitcode`:
    - 0: clean (no drift)
    - 1: error
    - 2: drift detected (alert-only if stateful, auto-reconcile if stateless)
    """
    if exit_code == 0:
        return "clean"
    if exit_code == 1:
        return "error"
    if exit_code == 2:
        return "drift_alert_only" if resource_stateful else "drift_auto_heal"
    raise ValueError(f"unexpected exit code {exit_code}")
