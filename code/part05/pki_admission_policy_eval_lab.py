#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.21: Certificates, identity, admission control and policy."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pki_admission_policy_eval import (
    evaluate_pod_security_standard,
    evaluate_vap_and_gatekeeper_policies,
    match_spire_workload_entry,
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
    # 1. Section 4 & KUR Ch. 19: Pod Security Standards (privileged vs baseline vs restricted)
    hardened_pod = {
        "securityContext": {"runAsNonRoot": True, "seccompProfile": {"type": "RuntimeDefault"}},
        "containers": [
            {
                "name": "trainer",
                "image": "gcr.io/kuar-demo/kuard-amd64:blue",
                "securityContext": {
                    "allowPrivilegeEscalation": False,
                    "capabilities": {"drop": ["ALL"]},
                },
            }
        ],
    }
    bad_pod = {
        "hostNetwork": True,
        "volumes": [{"name": "host-root", "hostPath": {"path": "/"}}],
        "containers": [{"name": "escape", "securityContext": {"privileged": True}}],
    }
    ok_rest, _ = evaluate_pod_security_standard(hardened_pod, profile="restricted")
    ok_base, errs_base = evaluate_pod_security_standard(bad_pod, profile="baseline")
    check(
        "evaluate_pod_security_standard passes hardened Pod under 'restricted' and catches hostNetwork, hostPath, and privileged under 'baseline'",
        ok_rest is True and ok_base is False and len(errs_base) == 3,
    )

    # 2. Section 3 & 5 & KUR Ch. 20: ValidatingAdmissionPolicy GPU limits + Gatekeeper K8sAllowedRepos
    compliant_gpu = {
        "priorityClassName": "training-normal",
        "containers": [
            {
                "name": "trainer",
                "image": "gcr.io/kuar-demo/trainer:v1",
                "resources": {"limits": {"nvidia.com/gpu": 8}},
            }
        ],
    }
    noncompliant_gpu = {
        "containers": [
            {
                "name": "rogue",
                "image": "docker.io/untrusted/miner:latest",
                "resources": {"limits": {"nvidia.com/gpu": 16}},
            }
        ],
    }
    ok_vap, _ = evaluate_vap_and_gatekeeper_policies(compliant_gpu, allowed_repos=["gcr.io/kuar-demo/"])
    bad_vap, vap_errs = evaluate_vap_and_gatekeeper_policies(noncompliant_gpu, allowed_repos=["gcr.io/kuar-demo/"])
    check(
        "evaluate_vap_and_gatekeeper_policies passes compliant 8-GPU Pod and flags untrusted repo, >8 GPUs, and missing priorityClassName",
        ok_vap is True and bad_vap is False and len(vap_errs) == 3,
    )

    # 3. Section 2 & PK Ch. 10: SPIFFE/SPIRE workload attestation selector matching
    spire_entries = [
        {
            "spiffe_id": "spiffe://production-trust-domain/service-a",
            "selectors": [
                "k8s:ns:default",
                "k8s:sa:service-a",
                "k8s:pod-label:app:frontend",
                "k8s:container-image:docker.io/johnharris85/service-a:v0.0.1",
            ],
        }
    ]
    svid = match_spire_workload_entry(
        {
            "k8s:ns:default",
            "k8s:sa:service-a",
            "k8s:pod-label:app:frontend",
            "k8s:container-image:docker.io/johnharris85/service-a:v0.0.1",
            "k8s:node-name:w1",
        },
        spire_entries,
    )
    no_svid = match_spire_workload_entry({"k8s:ns:default", "k8s:sa:other"}, spire_entries)
    check(
        "match_spire_workload_entry issues spiffe://production-trust-domain/service-a when all 4 k8s selectors match and denies mismatched SA",
        svid == "spiffe://production-trust-domain/service-a" and no_svid is None,
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
