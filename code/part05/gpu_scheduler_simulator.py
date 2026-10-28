"""Chapter 5.18 model: `NodeResourcesFit` (`LeastAllocated` vs `MostAllocated`
bin-packing) & GPU fragmentation simulator, Kueue `ClusterQueue` cohort
borrowing/lending & gang-admission evaluator, and DRA `matchAttribute`
(`pcieRoot`) device allocator (`KUR`, `volume-03/01..03`).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR).
- nvidia-devops (`volume-03/01-k8s-control-plane-scheduling-masterclass.md`,
  `volume-03/02-k8s-node-storage-masterclass.md`, and
  `volume-03/03-k8s-networking-security-ops-masterclass.md`).
"""
from typing import Any, Dict, List, Mapping, Sequence, Tuple


def simulate_gpu_placement_and_fragmentation(
    node_capacities: Sequence[int],
    pod_gpu_requests: Sequence[int],
    strategy: str = "MostAllocated",
) -> Dict[str, Any]:
    """Simulate placing `pod_gpu_requests` one by one onto nodes with
    `node_capacities` GPUs under `LeastAllocated` (spread) vs `MostAllocated`
    (bin-pack) scoring, and report remaining free GPUs per node and the
    `largest_free_contiguous_block` on a single node.
    """
    used = [0 for _ in node_capacities]
    unschedulable = 0

    for req in pod_gpu_requests:
        candidates: List[Tuple[float, int]] = []
        for idx, cap in enumerate(node_capacities):
            if used[idx] + req <= cap:
                new_used = used[idx] + req
                if strategy == "MostAllocated":
                    score = 100.0 * new_used / cap
                elif strategy == "LeastAllocated":
                    score = 100.0 * (cap - new_used) / cap
                else:
                    raise ValueError(f"unknown strategy {strategy!r}")
                candidates.append((score, -idx))
        if not candidates:
            unschedulable += 1
        else:
            _, neg_idx = max(candidates)
            used[-neg_idx] += req

    free_per_node = [cap - u for cap, u in zip(node_capacities, used)]
    return {
        "free_per_node": free_per_node,
        "largest_free_block": max(free_per_node, default=0),
        "unschedulable_pods": unschedulable,
    }


def evaluate_kueue_cohort_gang_admission(
    *,
    nominal_quota: int,
    borrowing_limit: int,
    current_used: int,
    cohort_lendable_free: int,
    workload_total_gpus: int,
) -> Tuple[bool, str]:
    """Model Section 5 Kueue `ClusterQueue` all-or-nothing gang admission with
    cohort borrowing:
    - A workload requesting `workload_total_gpus` is admitted as a complete unit
      (`suspend: false`) ONLY if:
      1. `current_used + workload_total_gpus <= nominal_quota + borrowing_limit`, AND
      2. Any amount borrowed above `nominal_quota` is <= `cohort_lendable_free`.
    """
    new_total = current_used + workload_total_gpus
    max_allowed = nominal_quota + borrowing_limit
    if new_total > max_allowed:
        return False, f"Workload exceeds nominalQuota ({nominal_quota}) + borrowingLimit ({borrowing_limit})"
    needed_borrow = max(0, new_total - nominal_quota)
    if needed_borrow > cohort_lendable_free:
        return False, f"Workload needs {needed_borrow} borrowed GPUs, but cohort only has {cohort_lendable_free} free"
    return True, f"Admitted (borrowed={needed_borrow} GPUs)"


def allocate_dra_same_pcie_root(
    devices: Sequence[Mapping[str, Any]],
    required_count: int,
    required_product: str = "NVIDIA H100 80GB HBM3",
) -> List[str] | None:
    """Model Section 6 DRA `ResourceClaimTemplate` selecting `required_count`
    GPUs matching `required_product` constrained to the same
    `resource.kubernetes.io/pcieRoot`.
    """
    by_root: Dict[str, List[str]] = {}
    for dev in devices:
        if dev.get("productName") == required_product and dev.get("free", True):
            root = str(dev["pcieRoot"])
            by_root.setdefault(root, []).append(str(dev["name"]))
    for root in sorted(by_root.keys()):
        if len(by_root[root]) >= required_count:
            return by_root[root][:required_count]
    return None
