"""Chapter 5.19 model: Day-2 GPU node lifecycle state machine (`Validating`
bootstrap taint gate + PDB-aware `kubectl drain`), GPU fleet capacity & idle-
waste analyzer, and `etcd` topology advisor (`PK` Ch. 1–2 & `KUR` Ch. 3).

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 1 & 2 ("Path to Production" and
  "Deployment Models"):
  * Managed vs Prebuilt Installer vs Roll Your Own, Dev/Testing (<1wk TTL)/
    Staging/Production cluster tiers, Few Large vs Many Small clusters.
  * Colocated vs dedicated etcd thresholds (`<= 50` colocated, `> 50` consider
    dedicated, `> 200` dedicated etcd required; no load balancer between
    kube-apiserver and etcd).
  * Characteristic-based vs role-based node pools (`M5` `1CPU:4GiB`, `R5`
    `1CPU:8GiB`, `C5` `1CPU:2GiB`).
  * Self-contained (pivoted) Cluster API topology for Cluster Autoscaler.
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 3.
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def evaluate_node_validation_and_drain(
    *,
    validation_checks: Mapping[str, bool],
    pods_on_node: Sequence[Mapping[str, Any]],
    ignore_daemonsets: bool = True,
    delete_emptydir_data: bool = True,
) -> Dict[str, Any]:
    """Model Section 3 node validation gate (`node.example.com/validating=true:NoSchedule`)
    and `kubectl drain` eviction checks (DaemonSets, `emptyDir`, unmanaged pods,
    and `PodDisruptionBudget` `disruptions_allowed`).
    """
    validation_passed = all(validation_checks.values())
    failed_checks = [k for k, ok in sorted(validation_checks.items()) if not ok]

    drain_blockers: List[str] = []
    evicted_pods: List[str] = []
    for pod in pods_on_node:
        name = str(pod["name"])
        if pod.get("is_daemonset", False):
            if not ignore_daemonsets:
                drain_blockers.append(f"{name}: DaemonSet pod requires --ignore-daemonsets")
            continue
        if not pod.get("has_controller", True):
            drain_blockers.append(f"{name}: unmanaged bare pod requires --force")
            continue
        if pod.get("has_emptydir", False) and not delete_emptydir_data:
            drain_blockers.append(f"{name}: pod with emptyDir requires --delete-emptydir-data")
            continue
        if int(pod.get("pdb_disruptions_allowed", 1)) <= 0:
            drain_blockers.append(f"{name}: eviction blocked by PodDisruptionBudget (disruptionsAllowed=0)")
            continue
        evicted_pods.append(name)

    return {
        "validation_passed": validation_passed,
        "remove_validating_taint": validation_passed,
        "failed_checks": failed_checks,
        "drain_succeeded": (len(drain_blockers) == 0),
        "evicted_pods": evicted_pods,
        "drain_blockers": drain_blockers,
    }


def analyze_gpu_fleet_and_etcd_sizing(
    worker_node_count: int,
    nodes: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    """Model Section 2 & 4 PK Ch. 2 etcd sizing threshold (`<=50` colocated,
    `51..200` consider dedicated, `>200` dedicated required) and GPU fleet
    allocation vs utilization efficiency.
    """
    if worker_node_count > 200:
        etcd_rec = "dedicated_required"
    elif worker_node_count > 50:
        etcd_rec = "consider_dedicated"
    else:
        etcd_rec = "colocated_ok"

    total_allocatable = sum(int(n["allocatable_gpus"]) for n in nodes)
    total_requested = sum(int(n["requested_gpus"]) for n in nodes)
    total_active_busy = sum(float(n["busy_gpus"]) for n in nodes)
    idle_allocated = sum(
        int(n["requested_gpus"]) for n in nodes if int(n["requested_gpus"]) > 0 and float(n["busy_gpus"]) == 0.0
    )
    largest_free_block = max((int(n["allocatable_gpus"]) - int(n["requested_gpus"]) for n in nodes), default=0)

    return {
        "etcd_recommendation": etcd_rec,
        "allocation_ratio": round(total_requested / max(1, total_allocatable), 3),
        "utilization_ratio": round(total_active_busy / max(1, total_allocatable), 3),
        "idle_allocated_gpus": idle_allocated,
        "largest_free_block": largest_free_block,
    }
