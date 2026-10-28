"""Chapter 5.22 model: `LimitRange` default injector + `ResourceQuota`
admission evaluator, `PK` Ch. 11 & 16 `AcmeNamespace`/`Team` operator
level-triggered reconciler (querying actual child existence vs trusting
`status.phase`), and multi-tenant GPU cost & idle-waste calculator.

Sources modeled:
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapters 11, 12, and 16:
  * Chapter 11 ("Building Platform Services"): Operator history (Brandon
    Phillips, CoreOS, Nov 2016), `WebApp` (`workloads.apps.acme.com/v1alpha1`)
    and `AcmeNamespace` (`AcmeNamespaceSpec` `namespaceName`, `adminUsername`,
    `AcmeNamespaceStatus` `statusCreated`/`statusInProgress`, why trusting
    `status.phase` alone fails on controller crash or manual child deletion,
    `ownerReferences` on cluster-scoped vs namespaced resources, Kubebuilder vs
    Operator SDK vs Metacontroller).
  * Chapter 12 ("Multitenancy"): Soft vs hard multitenancy ("family sharing a
    house" vs "hotel"), Namespace per application vs Namespace per team, RBAC,
    `default-deny-all` NetworkPolicy, CPU CFS quota throttling (`20ms` of `100ms`
    period), QoS classes, and Fluent Bit tag-based log routing (`kube.var.log.containers.*_alice-ns_*`).
  * Chapter 16 ("Platform Abstractions"): `Team` CRD operator (`examples.namespace-operator.io/v1`)
    and the 4-stage spectrum of abstraction (`kubectl`/`kubectx`/`kubens`/`Octant`/`Lens` ->
    `Helm` + `Kustomize` / `K8s Initializer` -> custom workload CRDs `PinterestService` ->
    full PaaS `Cloud Foundry`/`Backstage`/`Waypoint`).
"""
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


def evaluate_resource_quota_and_limitrange(
    *,
    pod_containers: Sequence[Mapping[str, Any]],
    limit_range: Mapping[str, int],
    current_quota_used: Mapping[str, int],
    quota_hard: Mapping[str, int],
) -> Tuple[bool, Dict[str, int], List[str]]:
    """Model Section 2 LimitRange defaulting/bounds + ResourceQuota enforcement:
    - Injects `default_cpu_m` and `default_mem_mi` if omitted on a container.
    - Checks container against `max_cpu_m` and `max_mem_mi`.
    - Sums Pod requests (`cpu_m`, `mem_mi`, `gpu`, `pods=1`) and checks against
      `quota_hard` (`requests.cpu_m`, `requests.mem_mi`, `requests.nvidia.com/gpu`,
      `count/pods`).
    """
    errors: List[str] = []
    pod_cpu = 0
    pod_mem = 0
    pod_gpu = 0

    for ctr in pod_containers:
        c_name = str(ctr.get("name", "app"))
        cpu = int(ctr.get("cpu_m", limit_range["default_cpu_m"]))
        mem = int(ctr.get("mem_mi", limit_range["default_mem_mi"]))
        gpu = int(ctr.get("gpu", 0))

        if cpu > int(limit_range["max_cpu_m"]):
            errors.append(f"LimitRange violation on {c_name!r}: cpu {cpu}m > max {limit_range['max_cpu_m']}m")
        if mem > int(limit_range["max_mem_mi"]):
            errors.append(f"LimitRange violation on {c_name!r}: mem {mem}Mi > max {limit_range['max_mem_mi']}Mi")

        pod_cpu += cpu
        pod_mem += mem
        pod_gpu += gpu

    new_usage = {
        "requests.cpu_m": int(current_quota_used.get("requests.cpu_m", 0)) + pod_cpu,
        "requests.mem_mi": int(current_quota_used.get("requests.mem_mi", 0)) + pod_mem,
        "requests.nvidia.com/gpu": int(current_quota_used.get("requests.nvidia.com/gpu", 0)) + pod_gpu,
        "count/pods": int(current_quota_used.get("count/pods", 0)) + 1,
    }
    for k, val in new_usage.items():
        if k in quota_hard and val > int(quota_hard[k]):
            errors.append(f"exceeded quota on {k}: requested total {val} > hard limit {quota_hard[k]}")

    return (len(errors) == 0), new_usage, errors


def reconcile_acme_namespace_operator(
    *,
    namespace_name: str,
    admin_username: str,
    existing_children_in_cache: Set[str],
) -> Dict[str, Any]:
    """Model PK Ch. 11 & 16 `AcmeNamespace` / `Team` operator level-triggered
    reconcile:
    Rather than trusting `status.phase == 'Created'` (which misses deleted child
    RoleBindings or controller crashes during `CreationInProgress`), inspect
    `existing_children_in_cache` for all required child objects and create any
    missing children.
    """
    required_children = [
        f"Namespace/{namespace_name}",
        f"Role/{namespace_name}/namespace-admin",
        f"RoleBinding/{namespace_name}/namespace-admin-{admin_username}",
        f"ResourceQuota/{namespace_name}/compute-quota",
        f"NetworkPolicy/{namespace_name}/default-deny-all",
    ]
    created: List[str] = []
    for child in required_children:
        if child not in existing_children_in_cache:
            existing_children_in_cache.add(child)
            created.append(child)
    return {
        "created_children": created,
        "status_phase": "Created",
        "total_children": len(existing_children_in_cache),
    }


def compute_tenant_gpu_cost_and_waste(
    *,
    requested_gpu_hours: float,
    active_utilized_gpu_hours: float,
    gpu_hour_rate_usd: float,
    shared_platform_overhead_usd: float = 0.0,
) -> Dict[str, float]:
    """Model Section 6 multi-tenant GPU chargeback/showback and idle waste."""
    compute_cost = requested_gpu_hours * gpu_hour_rate_usd
    total_billed = round(compute_cost + shared_platform_overhead_usd, 2)
    idle_gpu_hours = max(0.0, requested_gpu_hours - active_utilized_gpu_hours)
    idle_wasted_usd = round(idle_gpu_hours * gpu_hour_rate_usd, 2)
    efficiency_pct = round(100.0 * active_utilized_gpu_hours / max(1e-9, requested_gpu_hours), 1)
    return {
        "total_billed_usd": total_billed,
        "idle_gpu_hours": round(idle_gpu_hours, 2),
        "idle_wasted_usd": idle_wasted_usd,
        "utilization_efficiency_pct": efficiency_pct,
    }
