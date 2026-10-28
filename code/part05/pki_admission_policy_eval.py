"""Chapter 5.21 model: Pod Security Standards (`privileged` / `baseline` /
`restricted`) evaluator (`KUR` Ch. 19), `ValidatingAdmissionPolicy` + OPA
Gatekeeper `K8sAllowedRepos` & `data.inventory` evaluator (`KUR` Ch. 20 & `PK`
Ch. 8), and SPIFFE/SPIRE workload attestation selector matcher (`PK` Ch. 10).

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 8 ("Admission Control") & 10 ("Identity"):
  * Chapter 8: Built-in `NamespaceLifecycle` vs custom `controller-runtime`
    mutating webhook (`Handle(ctx, req)`, `PatchResponseFromRaw`, `+kubebuilder:webhook`),
    OPA Gatekeeper `Config` `data.inventory` sync, `ConstraintTemplate` &
    `Constraint` (`limit-namespace-ingress`).
  * Chapter 10: X.509 CSR flow, OIDC, `kube2iam`/`kiam` `spec.nodeName` flaw vs
    `IRSA` (`sts:AssumeRoleWithWebIdentity`), and `SPIFFE`/`SPIRE` node/workload
    attestation (`spire-server entry create`).
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters
  19 ("Securing Applications in Kubernetes") & 20 ("Policy and Governance"):
  * Chapter 19: `securityContext`, `amicontained`, `AppArmor`, `seccompProfile`,
    Pod Security Standards (`privileged`, `baseline`, `restricted`) dry-run
    namespace labeling, `RuntimeClass` (`firecracker`), `automountServiceAccountToken`,
    and `kube-bench` CIS benchmarks.
  * Chapter 20: Gatekeeper `K8sAllowedRepos`, `enforcementAction: dryrun`,
    `Assign` (`mutations.gatekeeper.sh/v1alpha1`), and `K8sUniqueIngressHost`.
- nvidia-devops (`volume-03/03-k8s-networking-security-ops-masterclass.md`).
"""
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


def evaluate_pod_security_standard(
    pod_spec: Mapping[str, Any],
    profile: str = "restricted",
) -> Tuple[bool, List[str]]:
    """Model Section 4 & KUR Ch. 19 Pod Security Standards (`privileged`,
    `baseline`, `restricted`).
    """
    if profile == "privileged":
        return True, []

    violations: List[str] = []
    # Baseline checks
    for host_ns in ("hostNetwork", "hostPID", "hostIPC"):
        if pod_spec.get(host_ns, False):
            violations.append(f"baseline forbids {host_ns}=True")
    for vol in pod_spec.get("volumes", ()):
        if "hostPath" in vol:
            violations.append(f"baseline forbids hostPath volume {vol.get('name')!r}")
    for ctr in pod_spec.get("containers", ()):
        sc = ctr.get("securityContext", {})
        if sc.get("privileged", False):
            violations.append(f"baseline forbids privileged=True on container {ctr['name']!r}")

    if profile == "baseline":
        return (len(violations) == 0), violations

    if profile == "restricted":
        pod_sc = pod_spec.get("securityContext", {})
        for ctr in pod_spec.get("containers", ()):
            sc = ctr.get("securityContext", {})
            run_as_non_root = sc.get("runAsNonRoot", pod_sc.get("runAsNonRoot", False))
            if not run_as_non_root:
                violations.append(f"restricted requires runAsNonRoot=True on {ctr['name']!r}")
            if sc.get("allowPrivilegeEscalation", True) is not False:
                violations.append(f"restricted requires allowPrivilegeEscalation=False on {ctr['name']!r}")
            drops = set(sc.get("capabilities", {}).get("drop", ()))
            if "ALL" not in drops:
                violations.append(f"restricted requires capabilities.drop=['ALL'] on {ctr['name']!r}")
            seccomp = sc.get("seccompProfile", pod_sc.get("seccompProfile", {})).get("type")
            if seccomp not in {"RuntimeDefault", "Localhost"}:
                violations.append(f"restricted requires seccompProfile RuntimeDefault/Localhost on {ctr['name']!r}")
        return (len(violations) == 0), violations

    raise ValueError(f"unknown Pod Security profile {profile!r}")


def evaluate_vap_and_gatekeeper_policies(
    pod_spec: Mapping[str, Any],
    allowed_repos: Sequence[str],
    max_gpus_per_pod: int = 8,
) -> Tuple[bool, List[str]]:
    """Model Section 3 & 5 ValidatingAdmissionPolicy (`gpu-request-limits`) and
    KUR Ch. 20 Gatekeeper `K8sAllowedRepos`.
    """
    violations: List[str] = []
    total_gpus = 0
    for ctr in pod_spec.get("containers", ()):
        img = str(ctr.get("image", ""))
        if not any(img.startswith(repo) for repo in allowed_repos):
            violations.append(
                f"container <{ctr['name']}> has an invalid image repo <{img}>, allowed repos are {list(allowed_repos)}"
            )
        gpus = int(ctr.get("resources", {}).get("limits", {}).get("nvidia.com/gpu", 0))
        total_gpus += gpus

    if total_gpus > max_gpus_per_pod:
        violations.append(f"A single pod may request at most {max_gpus_per_pod} GPUs (got {total_gpus}).")
    if total_gpus > 0 and not pod_spec.get("priorityClassName"):
        violations.append("GPU pods must set a priorityClassName.")

    return (len(violations) == 0), violations


def match_spire_workload_entry(
    workload_selectors: Set[str],
    entries: Sequence[Mapping[str, Any]],
) -> str | None:
    """Model Section 2 & PK Ch. 10 `spire-agent` Workload API attestation."""
    for entry in entries:
        required = set(entry.get("selectors", ()))
        if required.issubset(workload_selectors):
            return str(entry["spiffe_id"])
    return None
