"""Chapter 5.35 model: Kueue `MultiKueue` dispatcher (`AllAtOnce` vs
`Incremental` 3-cluster rounds & kubeconfig path-prefix validator), Argo CD
`ApplicationSet` label-selector & ring rollout planner, and Fleet CIDR overlap &
`KUR` Ch. 21 replicated-silo minimum-replica overhead calculator.

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 21
  ("Multicluster Application Deployments": before you begin—"fixing foundational
  problems is 10 times harder when you have 10 clusters", GeoDNS TTL caching &
  uneven ISP resolution drawbacks vs Anycast Cloud Load Balancing, TCP vs HTTP
  path-based load balancing, Replicated Silo pattern minimum-3-replica overhead
  in small regions, Sharded / Regional data vs Active-Active / Read-Replica
  eventual vs strong consistency `Cloud Spanner`).
- Kubernetes SIGs Kueue (`MultiKueue`, commit `1ec0d28`): `MultiKueueCluster`,
  `MultiKueueConfig`, `AllAtOnce` vs `Incremental` dispatcher (batches of 3 every
  5 minutes in `spec.clusters` order), and `/etc/multikueue/kubeconfigs/` path
  validation.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 2 ("Deployment Models").
- NVIDIA Base Command Manager 11 Containerization Manual (bcm11-containerization,
  Chapter 8: "Kubernetes Cluster API").
"""
import ipaddress
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def simulate_multikueue_dispatch(
    *,
    ordered_worker_clusters: Sequence[Mapping[str, Any]],
    job_gpu_demand: int,
    dispatcher_mode: str = "Incremental",
    incremental_batch_size: int = 3,
) -> Dict[str, Any]:
    """Model Section 5 Kueue `MultiKueue` job dispatch:
    - `AllAtOnce`: nominates ALL worker clusters in round 1; first in order with
      `free_gpus >= job_gpu_demand` admits the Workload, and remote Workloads on
      other nominated clusters are deleted.
    - `Incremental` (Kueue v0.13+/v0.19+): nominates clusters in rounds of
      `incremental_batch_size` (default 3) in the exact order of
      `MultiKueueConfig.spec.clusters` (e.g. on-prem -> reserved cloud -> spot
      overflow), advancing to the next 5-minute round only if no cluster in the
      current batch has `free_gpus >= job_gpu_demand`.
    """
    if dispatcher_mode == "AllAtOnce":
        nominated = [str(c["name"]) for c in ordered_worker_clusters]
        admitted = next(
            (str(c["name"]) for c in ordered_worker_clusters if int(c["free_gpus"]) >= job_gpu_demand),
            None,
        )
        return {
            "rounds_taken": 1,
            "nominated_clusters_in_winning_round": nominated,
            "admitted_cluster": admitted,
            "remote_workloads_cleaned_up": [n for n in nominated if n != admitted],
        }

    if dispatcher_mode == "Incremental":
        rounds = 0
        for start in range(0, len(ordered_worker_clusters), incremental_batch_size):
            rounds += 1
            batch = ordered_worker_clusters[start : start + incremental_batch_size]
            nominated = [str(c["name"]) for c in batch]
            for c in batch:
                if int(c["free_gpus"]) >= job_gpu_demand:
                    admitted = str(c["name"])
                    return {
                        "rounds_taken": rounds,
                        "elapsed_wait_minutes": (rounds - 1) * 5,
                        "nominated_clusters_in_winning_round": nominated,
                        "admitted_cluster": admitted,
                        "remote_workloads_cleaned_up": [n for n in nominated if n != admitted],
                    }
        return {
            "rounds_taken": rounds,
            "elapsed_wait_minutes": rounds * 5,
            "nominated_clusters_in_winning_round": [],
            "admitted_cluster": None,
            "remote_workloads_cleaned_up": [],
        }

    raise ValueError(f"unknown dispatcher_mode {dispatcher_mode!r}")


def plan_applicationset_ring_rollout(
    clusters: Sequence[Mapping[str, str]],
    required_labels: Mapping[str, str],
) -> List[Tuple[str, List[str]]]:
    """Model Section 4 & 9 Argo CD `ApplicationSet` label matching and ring-ordered
    progressive rollout (`canary` -> `staging` -> `prod-ring-1` -> `prod-ring-2`).
    """
    ring_order = ("canary", "staging", "prod-ring-1", "prod-ring-2")
    by_ring: Dict[str, List[str]] = {r: [] for r in ring_order}

    for cl in clusters:
        if all(cl.get(k) == v for k, v in required_labels.items()):
            r = cl.get("ring", "prod-ring-2")
            by_ring.setdefault(r, []).append(cl["name"])

    return [(r, sorted(by_ring[r])) for r in ring_order if by_ring.get(r)]


def audit_fleet_cidrs_and_silo_overhead(
    cluster_pod_cidrs: Mapping[str, str],
    *,
    num_regions: int = 8,
    min_ha_replicas_per_region: int = 3,
    global_demand_replicas: int = 10,
) -> Dict[str, Any]:
    """Model Section 6 non-overlapping Fleet Pod CIDR check and KUR Ch. 21
    Replicated-Silo minimum-replica overhead in low-traffic regions.
    """
    overlaps: List[str] = []
    parsed: List[Tuple[str, ipaddress.IPv4Network]] = [
        (name, ipaddress.IPv4Network(cidr)) for name, cidr in sorted(cluster_pod_cidrs.items())
    ]
    for i in range(len(parsed)):
        for j in range(i + 1, len(parsed)):
            n1, net1 = parsed[i]
            n2, net2 = parsed[j]
            if net1.overlaps(net2):
                overlaps.append(f"{n1} ({net1}) overlaps {n2} ({net2})")

    silo_total_replicas = max(global_demand_replicas, num_regions * min_ha_replicas_per_region)
    overprovisioned_replicas = silo_total_replicas - global_demand_replicas

    return {
        "cidr_overlaps": overlaps,
        "cidrs_valid_for_clustermesh": (len(overlaps) == 0),
        "silo_total_replicas": silo_total_replicas,
        "silo_overprovisioned_replicas": overprovisioned_replicas,
    }
