#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.25: Terraform with Kubernetes and Helm providers, and OpenTofu."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from terraform_k8s_helm_opentofu import (
    check_cluster_and_ownership_safety,
    evaluate_crd_manifest_plan,
    generate_team_tenancy_objects,
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
    # 1. Section 4: kubernetes_manifest vs kubectl_manifest CRD plan-time schema check
    ok_k8s_missing, _ = evaluate_crd_manifest_plan(
        resource_provider_type="kubernetes_manifest",
        crd_already_in_apiserver=False,
    )
    ok_k8s_present, _ = evaluate_crd_manifest_plan(
        resource_provider_type="kubernetes_manifest",
        crd_already_in_apiserver=True,
    )
    ok_kubectl_missing, _ = evaluate_crd_manifest_plan(
        resource_provider_type="kubectl_manifest",
        crd_already_in_apiserver=False,
    )
    check(
        "kubernetes_manifest fails at plan time when CRD is not yet installed, whereas layered apply or kubectl_manifest succeeds",
        ok_k8s_missing is False and ok_k8s_present is True and ok_kubectl_missing is True,
    )

    # 2. Section 5: Multi-tenant Kubernetes Namespace + GPU ResourceQuota + RoleBinding + NetworkPolicy generator
    teams = {
        "llm": {
            "gpu_quota": 16,
            "cpu_quota": "128",
            "mem_quota": "1Ti",
            "namespaces": ["train", "infer"],
            "admin_groups": ["llm-leads@example.com"],
        }
    }
    tenancy = generate_team_tenancy_objects(teams)
    check(
        "generate_team_tenancy_objects creates 'llm-train' and 'llm-infer' with requests.nvidia.com/gpu='16', baseline PSA, and default-deny",
        set(tenancy.keys()) == {"llm-train", "llm-infer"}
        and tenancy["llm-train"]["resource_quota_hard"]["requests.nvidia.com/gpu"] == "16"
        and tenancy["llm-train"]["namespace_labels"]["pod-security.kubernetes.io/enforce"] == "baseline"
        and tenancy["llm-train"]["default_deny_ingress"] is True,
    )

    # 3. Section 1, 6, 7: Wrong-cluster guard and Terraform vs Argo CD dual-ownership detector
    errs = check_cluster_and_ownership_safety(
        configured_host="",
        actual_kube_system_uid="uid-staging",
        expected_kube_system_uid="uid-prod",
        terraform_managed_objects={"Namespace/llm-train", "Application/root"},
        argocd_managed_objects={"Namespace/llm-train", "Deployment/vllm"},
    )
    clean = check_cluster_and_ownership_safety(
        configured_host="https://34.1.2.3",
        actual_kube_system_uid="uid-prod",
        expected_kube_system_uid="uid-prod",
        terraform_managed_objects={"Application/root"},
        argocd_managed_objects={"Namespace/llm-train", "Deployment/vllm"},
    )
    check(
        "check_cluster_and_ownership_safety catches empty host, kube-system UID mismatch, and Terraform+Argo CD dual ownership",
        len(errs) == 3 and clean == [],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
