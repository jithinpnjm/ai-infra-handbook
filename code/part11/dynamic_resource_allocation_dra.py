"""Chapter 11.12 — Dynamic Resource Allocation (DRA).

Deterministic models for:
1. Dynamic Resource Allocation (`resource.k8s.io/v1`, stable in Kubernetes `1.34`)
   structured-parameter matcher:
   - `ResourceSlice` advertisement (`gpu.nvidia.com`, memory GiB/GB, `migMode`,
     PCIe root / NUMA node).
   - `DeviceClass` (`gpu.nvidia.com` / `gpu.nvidia.com/a100`) and
     `ResourceClaimTemplate` (`allocationMode: ExactCount`, `count`, `minMemory`,
     `migMode: "disabled"`).
2. Optimistic Concurrency Control (`ResourceVersion`: `"154329"` -> `"154330"`,
   `200 OK` vs `409 Conflict` on concurrent controller updates).
3. Kubelet Sync Loop, PLEG health (`3m0s` threshold), and QoS `oom_score_adj`
   (`kubelet: -999`, `Guaranteed: -997`, `BestEffort: 1000`, `OOMKilled`
   `exitCode: 137 = 128 + 9`).
4. CSI vs DRA lifecycle comparison (`ControllerPublishVolume` ->
   `NodeStageVolume` -> `NodePublishVolume` vs `ResourceSlice` -> `ResourceClaim`
   allocation -> `NodePrepareResources`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DraGpuDevice:
    """Single GPU advertised inside a node's `ResourceSlice` (`resource.k8s.io/v1`)."""

    device_name: str
    product: str
    memory_gb_decimal: int
    memory_gib_binary: float
    mig_mode: str  # "enabled" or "disabled"
    numa_node: int


@dataclass(frozen=True)
class DraResourceSlice:
    """Node-level `ResourceSlice` published by a DRA kubelet plugin."""

    node_name: str
    driver_name: str  # e.g., "gpu.nvidia.com"
    devices: Tuple[DraGpuDevice, ...]


@dataclass(frozen=True)
class DraClaimRequest:
    """Structured-parameter request inside a `ResourceClaim` / `ResourceClaimTemplate`."""

    claim_name: str
    device_class_name: str  # e.g., "gpu.nvidia.com" or "gpu.nvidia.com/a100"
    allocation_mode: str = "ExactCount"
    count: int = 1
    min_memory_gb: int = 40
    required_mig_mode: str = "disabled"
    require_same_numa: bool = False


def match_dra_resource_claim(
    claim: DraClaimRequest, slices: List[DraResourceSlice]
) -> Dict[str, object]:
    """Evaluate a DRA ResourceClaim against published ResourceSlices during scheduling."""
    for rslice in slices:
        matching_devs = [
            d
            for d in rslice.devices
            if d.memory_gb_decimal >= claim.min_memory_gb
            and d.mig_mode == claim.required_mig_mode
        ]
        if not claim.require_same_numa:
            if len(matching_devs) >= claim.count:
                chosen = [d.device_name for d in matching_devs[: claim.count]]
                return {
                    "allocated": True,
                    "selected_node": rslice.node_name,
                    "allocated_devices": chosen,
                    "reason": "Structured parameters matched ResourceSlice",
                }
        else:
            # Group by NUMA node on this host
            by_numa: Dict[int, List[str]] = {}
            for d in matching_devs:
                by_numa.setdefault(d.numa_node, []).append(d.device_name)
            for numa_id, dev_names in sorted(by_numa.items()):
                if len(dev_names) >= claim.count:
                    return {
                        "allocated": True,
                        "selected_node": rslice.node_name,
                        "allocated_devices": dev_names[: claim.count],
                        "numa_node": numa_id,
                        "reason": f"Allocated {claim.count} devices aligned on NUMA {numa_id}",
                    }
    return {
        "allocated": False,
        "selected_node": None,
        "allocated_devices": [],
        "reason": "Unallocated ResourceClaim: no node ResourceSlice satisfied CEL/parameter constraints",
    }


def simulate_resource_version_occ(
    initial_rv: int = 154329,
    controller_a_rv: int = 154329,
    controller_b_rv: int = 154329,
) -> Dict[str, object]:
    """Simulate Volume 03 Section 3.2 Optimistic Concurrency Control (`154329` -> `154330`, `409 Conflict`)."""
    current_rv = initial_rv
    if controller_a_rv == current_rv:
        current_rv += 1
        a_status = 200
    else:
        a_status = 409

    if controller_b_rv == current_rv:
        current_rv += 1
        b_status = 200
    else:
        b_status = 409

    return {
        "initial_rv": str(initial_rv),
        "controller_a_http_status": a_status,
        "etcd_rv_after_a": str(current_rv),
        "controller_b_http_status": b_status,
        "controller_b_must_retry": b_status == 409,
    }


def evaluate_pleg_and_qos_oom(
    pleg_last_seen_seconds: int = 185,
    pleg_threshold_seconds: int = 180,
    qos_class: str = "Guaranteed",
) -> Dict[str, object]:
    """Evaluate Volume 03 Ch 2 PLEG health (`3m5s` > `3m0s` = `180s`) and QoS `oom_score_adj`."""
    oom_map = {
        "kubelet": -999,
        "Guaranteed": -997,
        "Burstable": 500,
        "BestEffort": 1000,
    }
    pleg_healthy = pleg_last_seen_seconds <= pleg_threshold_seconds
    return {
        "pleg_healthy": pleg_healthy,
        "node_condition": "Ready" if pleg_healthy else "NotReady (PLEG is not healthy)",
        "oom_score_adj": oom_map[qos_class],
        "sigkill_exit_code": 128 + 9,  # 137
    }
