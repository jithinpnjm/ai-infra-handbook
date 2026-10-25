"""Chapter 11.6 — Scheduling GPUs: requests, Topology Manager, CPU and NUMA alignment.

Deterministic models for:
1. NUMA and PCIe / NVLink interconnect bandwidth & latency metrics (`80 ns` local
   vs `139 ns` remote NUMA = `73.75%` / `~75%` penalty; PCIe Gen4 `32 GB/s`, Gen5
   `64 GB/s`, NVLink 4.0 `900 GB/s`, NVLink 5.0 `1800 GB/s`, NVL72 `130 TB/s`).
2. `nvidia-smi topo -m` link classifier (`X`, `NV12`, `NV4`, `PIX`, `PXB`, `PHB`,
   `NODE`, `SYS`).
3. Kubernetes QoS class (`Guaranteed`, `Burstable`, `BestEffort`), CPU Manager
   (`static`), and Topology Manager (`none`, `best-effort`, `restricted`,
   `single-numa-node`) simulator.
4. Dual-socket HGX `TopologyAffinityError` capacity model (`128` cores / `8` GPUs
   across `2` NUMA nodes: `16` cores/Pod leaves `14` free cores on a NUMA node when
   `2` cores are reserved by OS/system daemons, vs `12` cores/Pod fitting all `8` Pods).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


TOPO_LINK_RANK: Dict[str, Tuple[int, str]] = {
    "X": (0, "Self (same physical GPU)"),
    "NV18": (1, "NVLink 5.0 (18 links, 1800 GB/s bidirectional on Blackwell)"),
    "NV12": (2, "NVLink 3.0/4.0 (12 links, 600 GB/s on A100 / 900 GB/s on H100)"),
    "NV4": (3, "NVLink 4-link peer bridge"),
    "PIX": (4, "Same PCIe switch (direct P2P bypass without touching CPU root complex)"),
    "PXB": (5, "Multiple PCIe switches behind the same PCIe host bridge"),
    "PHB": (6, "Same PCIe host bridge (traverses CPU root complex)"),
    "NODE": (7, "Across PCIe host bridges within a single NUMA node"),
    "SYS": (8, "Across inter-socket QPI/UPI/xGMI link between NUMA nodes (slowest)"),
}


def compute_numa_latency_penalty(
    local_ns: float = 80.0, remote_ns: float = 139.0
) -> Dict[str, float]:
    """Compute local vs cross-NUMA memory access latency increase (ASP Ch 3: 80 ns vs 139 ns)."""
    delta_ns = remote_ns - local_ns
    pct_increase = (delta_ns / local_ns) * 100.0
    return {
        "local_ns": local_ns,
        "remote_ns": remote_ns,
        "delta_ns": round(delta_ns, 2),
        "increase_pct_exact": round(pct_increase, 2),
        "increase_pct_approx": float(round(pct_increase / 5.0) * 5),
    }


def classify_pod_qos_and_cpu_pinning(
    cpu_request: Optional[float],
    cpu_limit: Optional[float],
    memory_request_mib: Optional[int],
    memory_limit_mib: Optional[int],
    cpu_manager_policy: str = "static",
) -> Dict[str, object]:
    """Determine Pod QoS class (`Guaranteed`, `Burstable`, `BestEffort`) and exclusive CPU pinning."""
    if (
        cpu_request is None
        and cpu_limit is None
        and memory_request_mib is None
        and memory_limit_mib is None
    ):
        qos = "BestEffort"
    elif (
        cpu_request is not None
        and cpu_limit is not None
        and memory_request_mib is not None
        and memory_limit_mib is not None
        and cpu_request == cpu_limit
        and memory_request_mib == memory_limit_mib
    ):
        qos = "Guaranteed"
    else:
        qos = "Burstable"

    is_integer_cpu = cpu_limit is not None and float(cpu_limit).is_integer() and cpu_limit > 0
    exclusive_cpus = (
        qos == "Guaranteed"
        and is_integer_cpu
        and cpu_manager_policy == "static"
    )
    return {
        "qos_class": qos,
        "is_integer_cpu": bool(is_integer_cpu),
        "exclusive_cpu_pinning": exclusive_cpus,
    }


@dataclass
class NumaSocketState:
    """Resource state of one NUMA node on a multi-socket GPU server."""

    numa_id: int
    free_cpus: int
    free_gpus: int
    free_nics: int


def evaluate_topology_manager_admission(
    policy: str,
    req_cpus: int,
    req_gpus: int,
    req_nics: int,
    sockets: List[NumaSocketState],
) -> Dict[str, object]:
    """Evaluate `none`, `best-effort`, `restricted`, and `single-numa-node` policies."""
    total_free_cpus = sum(s.free_cpus for s in sockets)
    total_free_gpus = sum(s.free_gpus for s in sockets)
    total_free_nics = sum(s.free_nics for s in sockets)

    for s in sockets:
        if (
            s.free_cpus >= req_cpus
            and s.free_gpus >= req_gpus
            and s.free_nics >= req_nics
        ):
            s.free_cpus -= req_cpus
            s.free_gpus -= req_gpus
            s.free_nics -= req_nics
            return {
                "admitted": True,
                "status": "Running",
                "aligned_single_numa": True,
                "selected_numa": s.numa_id,
            }

    # No single NUMA node can satisfy all requested resources simultaneously
    if policy in ("single-numa-node", "restricted"):
        return {
            "admitted": False,
            "status": "TopologyAffinityError",
            "aligned_single_numa": False,
            "selected_numa": None,
        }

    if (
        total_free_cpus < req_cpus
        or total_free_gpus < req_gpus
        or total_free_nics < req_nics
    ):
        return {
            "admitted": False,
            "status": "OutOfResources",
            "aligned_single_numa": False,
            "selected_numa": None,
        }

    # `none` or `best-effort` admits the Pod across multiple NUMA nodes
    return {
        "admitted": True,
        "status": "Running (Cross-NUMA Degraded)",
        "aligned_single_numa": False,
        "selected_numa": None,
    }


def simulate_dual_socket_hgx_pod_packing(
    cores_per_pod: int = 16,
    total_pods: int = 8,
    numa0_initial_cpus: int = 64,
    numa1_initial_cpus: int = 50,  # e.g., 14 cores left after 3 pods or OS daemon reservation
    gpus_per_numa: int = 4,
    policy: str = "single-numa-node",
) -> Dict[str, object]:
    """Simulate the V07 Ch 8 Triton Inference Server scenario on a 128-core, 8-GPU server."""
    sockets = [
        NumaSocketState(numa_id=0, free_cpus=numa0_initial_cpus, free_gpus=gpus_per_numa, free_nics=4),
        NumaSocketState(numa_id=1, free_cpus=numa1_initial_cpus, free_gpus=gpus_per_numa, free_nics=4),
    ]
    admitted_pods = 0
    failed_pods: List[Tuple[int, str]] = []
    for pod_idx in range(1, total_pods + 1):
        res = evaluate_topology_manager_admission(
            policy=policy, req_cpus=cores_per_pod, req_gpus=1, req_nics=0, sockets=sockets
        )
        if res["admitted"]:
            admitted_pods += 1
        else:
            failed_pods.append((pod_idx, str(res["status"])))
    return {
        "cores_per_pod": cores_per_pod,
        "admitted_pods": admitted_pods,
        "failed_pods": failed_pods,
        "remaining_numa0_cpus": sockets[0].free_cpus,
        "remaining_numa1_cpus": sockets[1].free_cpus,
        "remaining_free_gpus": sockets[0].free_gpus + sockets[1].free_gpus,
    }


def parse_failed_scheduling_event(
    total_nodes: int = 12,
    insufficient_gpu_nodes: int = 4,
    untolerated_taint_nodes: int = 6,
    affinity_mismatch_nodes: int = 2,
) -> Dict[str, int]:
    """Validate the V10 Ch 8 `train-worker-2` 12-node FailedScheduling breakdown."""
    if (
        insufficient_gpu_nodes + untolerated_taint_nodes + affinity_mismatch_nodes
        != total_nodes
    ):
        raise ValueError("Clause counts must sum to total_nodes")
    return {
        "total_nodes": total_nodes,
        "capacity_blocked": insufficient_gpu_nodes,
        "taint_blocked": untolerated_taint_nodes,
        "affinity_blocked": affinity_mismatch_nodes,
    }
