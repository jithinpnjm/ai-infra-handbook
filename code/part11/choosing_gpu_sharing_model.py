#!/usr/bin/env python3
"""Chapter 11.26 model: Choosing a GPU Sharing Model, Capacity Planning & Chargeback.

Models:
1. Volume 11 Chapter 6 4-Branch Decision Tree + CUDA MPS selector (Dedicated GPU,
   MIG profile pool, NVIDIA vGPU, Time-Slicing, and CUDA MPS).
2. Volume 11 Chapter 6 Active Sharing Mechanism Diagnostic Classifier
   (mig.mode.current / mig -lgi, nvidia-smi vgpu, nvidia-smi --query-processes,
   and node status.allocatable).
3. Volume 11 Chapter 9 5-Layer Capacity Hierarchy (Physical -> Configured ->
   Allocatable -> Service -> Sellable), 5 Named Reserves (Node-failure, Maintenance,
   Rollout, Demand-variance, Fragmentation), Conservative Node Sizing Equation
   N = ceil((D + F) / (A * (1 - H))), and Allocation-Based Chargeback Rate Card.
4. Volume 11 Chapter 6 Allocation Efficiency vs Delivered Efficiency & 4-Service Catalog.
"""

from __future__ import annotations
from dataclasses import dataclass
import math
from typing import Dict, List


FIVE_CAPACITY_LAYERS: List[str] = [
    "Physical inventory",
    "Configured inventory",
    "Allocatable inventory",
    "Service capacity",
    "Sellable capacity",
]

FIVE_NAMED_RESERVES: List[str] = [
    "Node-failure reserve",
    "Maintenance reserve",
    "Rollout reserve",
    "Demand-variance reserve",
    "Fragmentation reserve",
]

FOUR_WORKSHOP_OWNERS: List[str] = [
    "Application owner",
    "Platform owner",
    "Security owner",
    "Service/Finance owner",
]

FOUR_CATALOG_SERVICES: List[Dict[str, str]] = [
    {
        "service": "Interactive sandbox",
        "mechanism": "time-sliced",
        "admission_posture": "bounded quota and queue",
        "failure_behavior": "slowdown or recall is acceptable",
        "billable_unit": "Access-hour or queue class",
    },
    {
        "service": "Protected inference",
        "mechanism": "MIG profile",
        "admission_posture": "qualification and protected reserve",
        "failure_behavior": "controlled failover or queueing",
        "billable_unit": "Allocated profile-hour",
    },
    {
        "service": "Large job",
        "mechanism": "dedicated GPU",
        "admission_posture": "capacity reservation / coordinated start",
        "failure_behavior": "checkpoint-aware maintenance",
        "billable_unit": "Reserved GPU-hour",
    },
    {
        "service": "Regulated VM",
        "mechanism": "vGPU",
        "admission_posture": "VM and identity controls",
        "failure_behavior": "host/guest lifecycle procedure",
        "billable_unit": "Assigned vGPU/VM-hour",
    },
]


@dataclass(frozen=True)
class WorkloadSharingRequirements:
    vm_tenant_boundary_required: bool
    hardware_partition_qos_required: bool
    best_effort_concurrency_acceptable: bool
    cooperative_single_tenant_spatial_mps: bool = False


def select_gpu_sharing_model(req: WorkloadSharingRequirements) -> Dict[str, str]:
    """Implements Volume 11 Chapter 6 Figure 11.6.1 decision tree + Volume 04 Ch 3 MPS."""
    if req.vm_tenant_boundary_required:
        return {
            "selected_model": "vGPU",
            "primary_boundary": "Virtual device assigned to a guest VM",
            "billable_unit": "Assigned vGPU/VM-hour",
        }
    if req.hardware_partition_qos_required:
        return {
            "selected_model": "MIG",
            "primary_boundary": "Supported hardware GPU instance (GI/CI)",
            "billable_unit": "Allocated profile-hour",
        }
    if req.best_effort_concurrency_acceptable:
        if req.cooperative_single_tenant_spatial_mps:
            return {
                "selected_model": "CUDA MPS",
                "primary_boundary": "Shared single CUDA context in EXCLUSIVE_PROCESS mode",
                "billable_unit": "Access-hour (cooperative microservice pool)",
            }
        return {
            "selected_model": "Time-slicing",
            "primary_boundary": "Software-advertised logical replica / process access",
            "billable_unit": "Access-hour or queue class",
        }
    return {
        "selected_model": "Dedicated GPU",
        "primary_boundary": "Whole physical GPU device",
        "billable_unit": "Reserved GPU-hour",
    }


def compute_required_nodes_vol11_ch9(
    demand_allocations_d: int,
    fragmentation_loss_f: int,
    usable_allocations_per_node_a: int,
    headroom_fraction_h: float,
) -> Dict[str, object]:
    """Computes N = ceil((D + F) / (A * (1 - H))) from Volume 11 Chapter 9."""
    if usable_allocations_per_node_a <= 0 or not (0.0 <= headroom_fraction_h < 1.0):
        raise ValueError("Invalid A or H in capacity formula")
    effective_allocations_per_node = usable_allocations_per_node_a * (1.0 - headroom_fraction_h)
    required_nodes_n = math.ceil((demand_allocations_d + fragmentation_loss_f) / effective_allocations_per_node)
    total_physical_allocations = required_nodes_n * usable_allocations_per_node_a
    sellable_allocations = int(math.floor(total_physical_allocations * (1.0 - headroom_fraction_h))) - fragmentation_loss_f

    return {
        "demand_d": demand_allocations_d,
        "fragmentation_f": fragmentation_loss_f,
        "allocations_per_node_a": usable_allocations_per_node_a,
        "headroom_fraction_h": headroom_fraction_h,
        "effective_allocations_per_node": round(effective_allocations_per_node, 2),
        "required_nodes_n": required_nodes_n,
        "total_configured_allocations": total_physical_allocations,
        "sellable_allocations": sellable_allocations,
    }


def detect_active_sharing_mechanism(
    mig_mode_enabled: bool,
    vgpu_instances_present: bool,
    node_allocatable_per_physical_gpu: int,
    concurrent_host_pids_on_gpu0: int,
) -> str:
    """Identifies the active sharing mechanism from host & K8s observations (Vol 11 Ch 6)."""
    if vgpu_instances_present:
        return "vGPU"
    if mig_mode_enabled:
        return "MIG"
    if node_allocatable_per_physical_gpu > 1 or concurrent_host_pids_on_gpu0 > 1:
        return "Time-slicing"
    return "Dedicated GPU"
