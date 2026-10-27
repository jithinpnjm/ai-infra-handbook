"""Chapter 4.26 model: Argo CD `sync-wave` & hook (`PreSync`/`Sync`/`PostSync`)
execution planner, `ApplicationSet` `clusters x git directories` matrix
generator, and GitOps drift/prune reconciler (`ignoreDifferences` on
`/spec/replicas` and `Prune=false` protection on stateful PVCs).

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 11 ("Building Platform Services"):
  * Extending Kubernetes to eliminate toil: CRDs + Controllers = Operators
    (Brandon Phillips, CoreOS, Nov 2016).
  * App-Specific Operators vs Platform/Tenancy Operators (`AcmeNamespace`
    `tenancy.acme.com/v1alpha1` reconciling child `Namespace`, `Role`, and
    `RoleBinding` with `ownerReferences` via `ctrl.SetControllerReference` and
    tracking `status.phase`: `CreationInProgress` -> `Created`).
  * Operator toolchains: Kubebuilder (`controller-runtime`), Operator SDK
    (Go, Ansible, Helm), and Metacontroller.
- volume-10/11-cicd-for-infrastructure-and-cluster-configuration.md & volume-10/17.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def plan_argocd_sync_waves(resources: Sequence[Mapping[str, Any]]) -> List[List[str]]:
    """Model Section 2 & 5 Argo CD sync ordering:
    1. Phase order: `PreSync` hooks -> `Sync` resources -> `PostSync` hooks.
    2. Within each phase, resources are grouped by integer `sync_wave`
       (default `0`, sorted lowest to highest: `-1`, `0`, `1`, `2`, ..., `5`).
    3. Within the same phase and wave, resources are ordered deterministically by name.
    """
    phase_rank = {"PreSync": 0, "Sync": 1, "PostSync": 2}
    buckets: Dict[Tuple[int, int], List[str]] = {}
    for res in resources:
        phase = str(res.get("hook", "Sync"))
        wave = int(res.get("sync_wave", 0))
        key = (phase_rank[phase], wave)
        buckets.setdefault(key, []).append(str(res["name"]))
    return [sorted(names) for _, names in sorted(buckets.items())]


def expand_applicationset_matrix(
    clusters: Sequence[Mapping[str, str]],
    git_dirs: Sequence[str],
    required_env_label: str = "prod",
) -> List[Dict[str, str]]:
    """Model Section 2 `ApplicationSet` matrix generator (`clusters` selector
    crossed with `git` directories `addons/*`).
    """
    apps: List[Dict[str, str]] = []
    for cl in clusters:
        if cl.get("env") != required_env_label:
            continue
        for path in git_dirs:
            basename = path.rstrip("/").rsplit("/", 1)[-1]
            apps.append(
                {
                    "app_name": f"{cl['name']}-{basename}",
                    "server": cl["server"],
                    "path": path,
                    "namespace": basename,
                }
            )
    return apps


def evaluate_gitops_reconciliation(
    *,
    desired_in_git: Mapping[str, Dict[str, Any]],
    live_in_cluster: Mapping[str, Dict[str, Any]],
    ignore_replicas_on: set[str],
    prune_enabled: bool = True,
) -> Dict[str, List[str]]:
    """Model Section 2 & 7 GitOps diff, `ignoreDifferences` (`/spec/replicas`
    managed by HPA), and `prune` with `Prune=false` protection on stateful PVCs.
    """
    synced: List[str] = []
    out_of_sync_updated: List[str] = []
    pruned: List[str] = []
    prune_protected: List[str] = []

    for obj_id, git_spec in sorted(desired_in_git.items()):
        if obj_id not in live_in_cluster:
            out_of_sync_updated.append(obj_id)
            continue
        live_spec = dict(live_in_cluster[obj_id])
        git_cmp = dict(git_spec)
        if obj_id in ignore_replicas_on:
            live_spec.pop("replicas", None)
            git_cmp.pop("replicas", None)
        if live_spec == git_cmp:
            synced.append(obj_id)
        else:
            out_of_sync_updated.append(obj_id)

    for obj_id, live_spec in sorted(live_in_cluster.items()):
        if obj_id not in desired_in_git and prune_enabled:
            if live_spec.get("prune_option") == "false":
                prune_protected.append(obj_id)
            else:
                pruned.append(obj_id)

    return {
        "synced": synced,
        "updated": out_of_sync_updated,
        "pruned": pruned,
        "prune_protected": prune_protected,
    }
