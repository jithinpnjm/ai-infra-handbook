"""Chapter 5.3 model: Kubernetes watch-driven control loop & hub-and-spoke
communication validator (`apiserver` as the sole `etcd` client), Raft quorum
calculator (`floor(N/2) + 1`), and Node `Capacity` vs `Allocatable` resource
calculator (`KUR` Ch. 1 & 3, `volume-03` Ch. 01–03).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapters 1 & 3:
  * Chapter 1 ("Introduction"): Borg/Omega heritage (2014 open-source release),
    five core benefits (Velocity via immutable declarative state & self-healing,
    Scaling software & teams via decoupled microservices/autoscaling, Abstracting
    infrastructure for hybrid/multi-cloud portability, Efficiency via bin-packing
    batch + serving workloads, and Cloud Native Ecosystem via CNCF).
  * Chapter 3 ("Deploying a Kubernetes Cluster"): `kubectl version` (±1 version
    skew policy), `kubectl get nodes`, `kubectl describe nodes` (`Capacity` vs
    `Allocatable` = `Capacity - kube-reserved - system-reserved - eviction-threshold`,
    node `Conditions` `Ready`/`MemoryPressure`/`DiskPressure`/`PIDPressure`),
    and `kube-system` components (`coredns`/`kube-dns`, `kube-proxy` DaemonSet).
- nvidia-devops (`volume-03/01-kubernetes-architecture-deep-dive.md`,
  `volume-03/02-etcd-the-brain-of-kubernetes.md`, and
  `volume-03/03-api-server-and-admission-control.md`).
"""
from typing import Dict, List, Mapping, Sequence, Tuple

ALLOWED_DIRECT_EDGES: set[Tuple[str, str]] = {
    ("kubectl", "kube-apiserver"),
    ("kube-apiserver", "etcd"),
    ("kube-scheduler", "kube-apiserver"),
    ("kube-controller-manager", "kube-apiserver"),
    ("cloud-controller-manager", "kube-apiserver"),
    ("kubelet", "kube-apiserver"),
    ("kube-proxy", "kube-apiserver"),
    ("kube-apiserver", "kubelet"),  # logs/exec/port-forward
    ("kubelet", "containerd"),
    ("containerd", "cni"),
    ("device-plugin", "kubelet"),
}


def validate_k8s_communication_edges(edges: Sequence[Tuple[str, str]]) -> List[str]:
    """Verify Section 3 & 4 hub-and-spoke rule: ONLY `kube-apiserver` talks to
    `etcd`, and controllers/scheduler/kubelet communicate exclusively via
    `kube-apiserver` watches and writes (never controller->kubelet or kubelet->etcd).
    """
    violations: List[str] = []
    for src, dst in edges:
        if dst == "etcd" and src != "kube-apiserver":
            violations.append(f"illegal direct etcd access: {src} -> etcd (only kube-apiserver talks to etcd)")
        elif (src, dst) not in ALLOWED_DIRECT_EDGES:
            violations.append(f"disallowed direct edge: {src} -> {dst} (must coordinate via kube-apiserver)")
    return violations


def compute_etcd_raft_quorum(total_members: int) -> Dict[str, int]:
    """Model Section 2 & 8 etcd Raft quorum (`floor(N/2) + 1`) and fault tolerance."""
    if total_members < 1:
        raise ValueError("total_members must be >= 1")
    quorum = (total_members // 2) + 1
    max_failures = total_members - quorum
    return {
        "total_members": total_members,
        "quorum": quorum,
        "max_tolerated_failures": max_failures,
    }


def compute_node_allocatable(
    capacity: Mapping[str, int],
    kube_reserved: Mapping[str, int],
    system_reserved: Mapping[str, int],
    eviction_threshold: Mapping[str, int],
) -> Dict[str, int]:
    """Model KUR Ch. 3 & Section 6 Node `Allocatable` formula:
      Allocatable = Capacity - kube-reserved - system-reserved - eviction-threshold
    Note: GPUs (`nvidia.com/gpu`) have 0 daemon reservation so Allocatable == Capacity
    (when the NVIDIA device plugin is healthy).
    """
    alloc: Dict[str, int] = {}
    for res, cap_val in capacity.items():
        deducted = (
            int(kube_reserved.get(res, 0))
            + int(system_reserved.get(res, 0))
            + int(eviction_threshold.get(res, 0))
        )
        alloc[res] = max(0, int(cap_val) - deducted)
    return alloc
