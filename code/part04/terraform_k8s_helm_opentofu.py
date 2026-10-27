"""Chapter 4.25 model: `kubernetes_manifest` vs `kubectl_manifest` CRD plan-time
schema checker, multi-tenant Kubernetes `Namespace`/`ResourceQuota`/`RoleBinding`/
`NetworkPolicy` generator, and wrong-cluster / dual-controller ownership guard.

Sources modeled:
- Yevgeniy Brikman, Terraform: Up and Running, 3rd ed. (terraform-up-and-running-
  3rd-edition, TUR), Chapter 7 ("Working with Multiple Providers").
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 11 ("Building Platform Services").
- volume-10/05-terraform-for-infrastructure-as-code.md & volume-10/11.
"""
from typing import Any, Dict, List, Mapping, Set, Tuple


def evaluate_crd_manifest_plan(
    *,
    resource_provider_type: str,
    crd_already_in_apiserver: bool,
) -> Tuple[bool, str]:
    """Model Section 4 CRD plan-time schema lookup:
    - `kubernetes_manifest` queries the Kubernetes API server's OpenAPI schema
      DURING `terraform plan`; if the CRD (`ServiceMonitor`, `ClusterPolicy`,
      `ClusterQueue`) is being installed in the same apply, `plan` fails!
    - `kubectl_manifest` (`alekc/kubectl`) or a 2-stack layered apply succeeds.
    """
    if resource_provider_type == "kubernetes_manifest":
        if not crd_already_in_apiserver:
            return False, "Error: failed toitzel OpenAPI schema during plan: CRD not yet installed on API server"
        return True, "planned with server-side apply schema validation"
    if resource_provider_type == "kubectl_manifest":
        return True, "planned as raw YAML (schema validated at apply time after depends_on)"
    raise ValueError(f"unknown provider resource type {resource_provider_type!r}")


def generate_team_tenancy_objects(teams: Mapping[str, Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Model Section 5 per-(team, namespace) tenancy objects:
    Namespace (`pod-security.kubernetes.io/enforce = baseline`), GPU/CPU/Mem
    `ResourceQuota`, `RoleBinding` to `edit`, and `default-deny-ingress`
    `NetworkPolicy`.
    """
    out: Dict[str, Dict[str, Any]] = {}
    for team, cfg in sorted(teams.items()):
        for ns_short in cfg.get("namespaces", ()):
            ns_name = f"{team}-{ns_short}"
            out[ns_name] = {
                "namespace_labels": {
                    "team": team,
                    "pod-security.kubernetes.io/enforce": "baseline",
                },
                "resource_quota_hard": {
                    "requests.nvidia.com/gpu": str(cfg["gpu_quota"]),
                    "requests.cpu": str(cfg["cpu_quota"]),
                    "requests.memory": str(cfg["mem_quota"]),
                    "persistentvolumeclaims": "50",
                },
                "role_binding_groups": list(cfg.get("admin_groups", ())),
                "default_deny_ingress": True,
            }
    return out


def check_cluster_and_ownership_safety(
    *,
    configured_host: str,
    actual_kube_system_uid: str,
    expected_kube_system_uid: str,
    terraform_managed_objects: Set[str],
    argocd_managed_objects: Set[str],
) -> List[str]:
    """Model Section 1, 6, 7 safety rules:
    1. Reject empty `host` (which silently falls back to local `~/.kube/config`).
    2. Reject `kube-system` UID mismatch (wrong cluster guard).
    3. Reject dual ownership between Terraform and Argo CD (`selfHeal` fight).
    """
    errors: List[str] = []
    if not configured_host:
        errors.append("provider kubernetes host is empty (would fall back to local kubeconfig)")
    if actual_kube_system_uid != expected_kube_system_uid:
        errors.append(f"wrong cluster: kube-system uid {actual_kube_system_uid!r} != {expected_kube_system_uid!r}")
    overlap = sorted(terraform_managed_objects & argocd_managed_objects)
    if overlap:
        errors.append(f"dual-ownership conflict between Terraform and Argo CD on {overlap}")
    return errors
