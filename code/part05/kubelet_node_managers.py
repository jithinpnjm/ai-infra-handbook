"""Chapter 5.9 model: Kubelet CPU Manager (`static` + `full-pcpus-only`),
Topology Manager (`none` / `best-effort` / `restricted` / `single-numa-node`)
NUMA hint bitwise evaluator, and Node-Pressure Eviction victim selector.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 3 ("Container Runtime").
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 5.
- nvidia-devops (`volume-03/02-k8s-node-storage-masterclass.md`).
"""
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


def evaluate_cpu_manager_static(
    *,
    qos_class: str,
    cpu_request_m: int,
    full_pcpus_only: bool = True,
    threads_per_core: int = 2,
) -> Tuple[str, str]:
    """Model Section 4 CPU Manager `static` policy:
    - Only `Guaranteed` pods requesting an integer number of CPUs
      (`cpu_request_m % 1000 == 0` and `cpu_request_m >= 1000`) qualify for
      exclusive pinned cores.
    - When `full-pcpus-only: "true"` is enabled on an SMT/HyperThreading host
      (`threads_per_core == 2`), the integer CPU count must also be a multiple
      of `threads_per_core`.
    """
    if qos_class != "Guaranteed":
        return "shared_pool", "Pod QoS is not Guaranteed"
    if cpu_request_m < 1000 or (cpu_request_m % 1000) != 0:
        return "shared_pool", "CPU request is fractional (not an integer core count)"
    cores = cpu_request_m // 1000
    if full_pcpus_only and (cores % threads_per_core) != 0:
        return "rejected_smt", f"full-pcpus-only requires a multiple of {threads_per_core} vCPUs, got {cores}"
    return "exclusive_pinned", f"allocated {cores} exclusive vCPUs"


def evaluate_topology_manager(
    policy: str,
    provider_numa_masks: Sequence[Set[int]],
) -> Tuple[bool, Set[int], str]:
    """Model Section 4 Topology Manager NUMA hint intersection across CPU,
    Memory, and Device managers:
    - Each provider supplies the set of NUMA node IDs (`{0}`, `{0, 1}`) that can
      satisfy its resource request with minimal cross-NUMA traffic.
    - `intersection` = common NUMA node(s) across all providers.
    """
    if policy == "none":
        return True, set(), "admitted (policy=none)"
    if not provider_numa_masks:
        return True, {0}, "admitted (no providers)"

    common = set(provider_numa_masks[0])
    for mask in provider_numa_masks[1:]:
        common &= set(mask)

    single_numa_possible = len(common) >= 1 and all(len(m) == 1 for m in provider_numa_masks)
    if policy == "single-numa-node":
        if len(common) >= 1 and single_numa_possible:
            return True, common, "admitted on single NUMA node"
        return False, set(), "TopologyAffinityError: cannot align all resources on a single NUMA node"
    if policy == "restricted":
        if len(common) >= 1:
            return True, common, "admitted with preferred NUMA alignment"
        return False, set(), "TopologyAffinityError: preferred NUMA affinity cannot be satisfied"
    if policy == "best-effort":
        return True, common, "admitted (best-effort)"
    raise ValueError(f"unknown topologyManagerPolicy {policy!r}")


def rank_memory_eviction_victims(pods: Sequence[Mapping[str, Any]]) -> List[str]:
    """Model Section 6 kubelet node-pressure memory eviction ranking:
    1. Pods whose `usage_mi > request_mi` (`BestEffort` has `request_mi = 0`, so
       it is always over request) are evicted before pods within their request.
    2. Within each tier, lower `priority` is evicted first.
    3. Tie-breaker: larger `(usage_mi - request_mi)` excess is evicted first.
    """
    def sort_key(p: Mapping[str, Any]) -> Tuple[int, int, int]:
        req = int(p.get("request_mi", 0))
        use = int(p.get("usage_mi", 0))
        prio = int(p.get("priority", 0))
        over_req_tier = 0 if use > req else 1
        excess = use - req
        return (over_req_tier, prio, -excess)

    return [str(p["name"]) for p in sorted(pods, key=sort_key)]
