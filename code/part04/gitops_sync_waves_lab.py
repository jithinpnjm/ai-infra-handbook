#!/usr/bin/env python3
"""Self-checking lab for Chapter 4.26: GitOps with Argo CD and Flux."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gitops_sync_waves import (
    evaluate_gitops_reconciliation,
    expand_applicationset_matrix,
    plan_argocd_sync_waves,
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
    # 1. Section 2 & 5: GPU platform bootstrap ordering via sync-waves and hooks
    items = [
        {"name": "inference-gateway", "hook": "Sync", "sync_wave": 5},
        {"name": "gpu-operator", "hook": "Sync", "sync_wave": 2},
        {"name": "cert-manager", "hook": "Sync", "sync_wave": 1},
        {"name": "namespaces-and-crds", "hook": "Sync", "sync_wave": 0},
        {"name": "kueue", "hook": "Sync", "sync_wave": 3},
        {"name": "db-migration-job", "hook": "PreSync", "sync_wave": 0},
        {"name": "nccl-smoke-test", "hook": "PostSync", "sync_wave": 0},
    ]
    waves = plan_argocd_sync_waves(items)
    check(
        "plan_argocd_sync_waves orders PreSync -> Wave 0 (CRDs) -> Wave 1 (cert-manager) -> Wave 2 (gpu-operator) -> Wave 3 (kueue) -> Wave 5 -> PostSync",
        waves
        == [
            ["db-migration-job"],
            ["namespaces-and-crds"],
            ["cert-manager"],
            ["gpu-operator"],
            ["kueue"],
            ["inference-gateway"],
            ["nccl-smoke-test"],
        ],
    )

    # 2. Section 2: ApplicationSet matrix generator (prod clusters x addons/*)
    clusters = [
        {"name": "prod-us", "env": "prod", "server": "https://k8s-us.example.com"},
        {"name": "prod-eu", "env": "prod", "server": "https://k8s-eu.example.com"},
        {"name": "dev-us", "env": "dev", "server": "https://k8s-dev.example.com"},
    ]
    apps = expand_applicationset_matrix(clusters, ["addons/gpu-operator", "addons/kueue"], required_env_label="prod")
    check(
        "expand_applicationset_matrix generates 4 Applications (2 prod clusters x 2 addons) and skips dev-us",
        [a["app_name"] for a in apps]
        == ["prod-us-gpu-operator", "prod-us-kueue", "prod-eu-gpu-operator", "prod-eu-kueue"],
    )

    # 3. Section 2 & 7: ignoreDifferences (/spec/replicas) and Prune=false protection on PVCs
    git_desired = {
        "Deployment/vllm": {"image": "vllm:v1", "replicas": 2},
        "ConfigMap/nccl": {"ib": "mlx5_0"},
    }
    live_cluster = {
        "Deployment/vllm": {"image": "vllm:v1", "replicas": 8},  # scaled by HPA; ignored!
        "ConfigMap/nccl": {"ib": "eth0"},  # drifted!
        "Deployment/old-test": {"image": "old"},  # removed from Git -> pruned
        "PersistentVolumeClaim/checkpoints": {"size": "10Ti", "prune_option": "false"},  # Prune=false -> protected!
    }
    rec = evaluate_gitops_reconciliation(
        desired_in_git=git_desired,
        live_in_cluster=live_cluster,
        ignore_replicas_on={"Deployment/vllm"},
        prune_enabled=True,
    )
    check(
        "GitOps reconciler treats HPA-scaled Deployment/vllm as Synced, updates drifted ConfigMap/nccl, prunes old-test, and protects PVC",
        rec["synced"] == ["Deployment/vllm"]
        and rec["updated"] == ["ConfigMap/nccl"]
        and rec["pruned"] == ["Deployment/old-test"]
        and rec["prune_protected"] == ["PersistentVolumeClaim/checkpoints"],
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
