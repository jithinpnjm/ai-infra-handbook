#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.3: Kubernetes architecture overview: components and what talks to what."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from k8s_architecture_flow import (
    compute_etcd_raft_quorum,
    compute_node_allocatable,
    validate_k8s_communication_edges,
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
    # 1. Section 3 & 4: Hub-and-spoke communication rules (only kube-apiserver talks to etcd)
    valid_flow = [
        ("kubectl", "kube-apiserver"),
        ("kube-apiserver", "etcd"),
        ("kube-controller-manager", "kube-apiserver"),
        ("kube-scheduler", "kube-apiserver"),
        ("kubelet", "kube-apiserver"),
        ("kubelet", "containerd"),
    ]
    invalid_flow = [
        ("kubelet", "etcd"),
        ("kube-scheduler", "kubelet"),
    ]
    check(
        "validate_k8s_communication_edges accepts hub-and-spoke Pod creation flow and rejects kubelet->etcd and scheduler->kubelet",
        validate_k8s_communication_edges(valid_flow) == []
        and len(validate_k8s_communication_edges(invalid_flow)) == 2,
    )

    # 2. Section 2 & 8: etcd Raft quorum calculator (3-node vs 4-node vs 5-node)
    q3 = compute_etcd_raft_quorum(3)
    q4 = compute_etcd_raft_quorum(4)
    q5 = compute_etcd_raft_quorum(5)
    check(
        "compute_etcd_raft_quorum shows 3-node (quorum=2, tol=1), 4-node (quorum=3, tol=1 — worse HA than 3), and 5-node (quorum=3, tol=2)",
        q3 == {"total_members": 3, "quorum": 2, "max_tolerated_failures": 1}
        and q4 == {"total_members": 4, "quorum": 3, "max_tolerated_failures": 1}
        and q5 == {"total_members": 5, "quorum": 3, "max_tolerated_failures": 2},
    )

    # 3. KUR Ch. 3 & Section 6: Node Capacity vs Allocatable calculation
    alloc = compute_node_allocatable(
        capacity={"cpu_m": 64000, "memory_mi": 512000, "nvidia.com/gpu": 8},
        kube_reserved={"cpu_m": 1000, "memory_mi": 4096},
        system_reserved={"cpu_m": 1000, "memory_mi": 4096},
        eviction_threshold={"memory_mi": 100},
    )
    check(
        "compute_node_allocatable subtracts kube/system/eviction reserves from CPU/RAM while keeping 8 GPUs allocatable",
        alloc == {"cpu_m": 62000, "memory_mi": 503708, "nvidia.com/gpu": 8},
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
