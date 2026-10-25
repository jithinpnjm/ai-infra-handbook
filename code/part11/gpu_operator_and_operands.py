"""Chapter 11.4 — GPU Operator architecture and operands.

Deterministic models for:
1. GPU Operator `ClusterPolicy` state machine, `nvidia.com/gpu.deploy.*` node labels,
   and per-node operand init-container gating (`driver-validation`, `toolkit-validation`,
   `cuda-validation`, `plugin-validation`).
2. `ClusterPolicy.status.state: ready` vs per-node DaemonSet readiness accounting
   (`25/25` vs `24/25` with `CrashLoopBackOff` on 1 node).
3. Unpooled vs Canary `ClusterPolicy` blast-radius model (`60` nodes with `35` on an
   unsupported kernel = `58.33%` fleet loss vs `3`-node canary = `5.0%` loss).
4. Driver container rolling upgrade capacity planner (`40` nodes, `8` GPUs/node,
   `6` minutes/node, `28`-GPU headroom SLO: `maxUnavailable: 4` -> `32` GPUs offline vs
   `maxUnavailable: 2` -> `16` GPUs offline).
5. GPU Operator vs NVIDIA Network Operator failure-domain discriminator (`nvidia.com/gpu`
   vs `rdma/rdma_shared_device_a` and `ibv_devinfo` `PORT_ACTIVE`).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


OPERAND_DEPLOY_LABELS: Tuple[str, ...] = (
    "nvidia.com/gpu.deploy.driver",
    "nvidia.com/gpu.deploy.container-toolkit",
    "nvidia.com/gpu.deploy.device-plugin",
    "nvidia.com/gpu.deploy.gpu-feature-discovery",
    "nvidia.com/gpu.deploy.dcgm",
    "nvidia.com/gpu.deploy.dcgm-exporter",
    "nvidia.com/gpu.deploy.node-status-exporter",
    "nvidia.com/gpu.deploy.operator-validator",
)


@dataclass(frozen=True)
class ClusterPolicyConfig:
    """Declarative ownership settings in `ClusterPolicy.spec`."""

    driver_enabled: bool = True
    driver_version: str = "550.90.07"
    use_precompiled: bool = True
    toolkit_enabled: bool = True
    device_plugin_enabled: bool = True
    gfd_enabled: bool = True
    dcgm_exporter_enabled: bool = True
    mig_strategy: str = "single"
    nfd_enabled: bool = True


def compute_node_deploy_labels(
    pci_10de_present: bool, policy: ClusterPolicyConfig
) -> Dict[str, str]:
    """Compute the `nvidia.com/gpu.deploy.*` labels reconciled by the GPU Operator."""
    if not pci_10de_present:
        return {}
    return {
        "nvidia.com/gpu.deploy.driver": "true" if policy.driver_enabled else "false",
        "nvidia.com/gpu.deploy.container-toolkit": (
            "true" if policy.toolkit_enabled else "false"
        ),
        "nvidia.com/gpu.deploy.device-plugin": (
            "true" if policy.device_plugin_enabled else "false"
        ),
        "nvidia.com/gpu.deploy.gpu-feature-discovery": (
            "true" if policy.gfd_enabled else "false"
        ),
        "nvidia.com/gpu.deploy.dcgm": (
            "true" if policy.dcgm_exporter_enabled else "false"
        ),
        "nvidia.com/gpu.deploy.dcgm-exporter": (
            "true" if policy.dcgm_exporter_enabled else "false"
        ),
        "nvidia.com/gpu.deploy.node-status-exporter": "true",
        "nvidia.com/gpu.deploy.operator-validator": "true",
    }


@dataclass(frozen=True)
class NodeOperandGates:
    """Host and init-container gate results on a single GPU worker node."""

    node_name: str
    driver_module_loaded: bool
    nvml_healthy: bool
    toolkit_configured: bool
    cuda_sample_passed: bool
    plugin_registered_and_allocatable: bool


def evaluate_operator_validator_pod(gates: NodeOperandGates) -> Dict[str, object]:
    """Simulate the 4 init containers of `nvidia-operator-validator` on a node."""
    init_statuses: Dict[str, str] = {}

    # 1. driver-validation (runs `chroot /run/nvidia/driver nvidia-smi`)
    if not (gates.driver_module_loaded and gates.nvml_healthy):
        init_statuses["driver-validation"] = "Error"
        return {
            "init_containers": init_statuses,
            "toolkit_pod_state": "Init:0/1",
            "device_plugin_pod_state": "Init:0/1",
            "validator_pod_state": "Init:0/4",
            "validator_log": "Failed to initialize NVML: Driver/library version mismatch",
            "node_accepted": False,
        }
    init_statuses["driver-validation"] = "Completed"

    # 2. toolkit-validation
    if not gates.toolkit_configured:
        init_statuses["toolkit-validation"] = "Error"
        return {
            "init_containers": init_statuses,
            "toolkit_pod_state": "CrashLoopBackOff",
            "device_plugin_pod_state": "Init:0/1",
            "validator_pod_state": "Init:1/4",
            "validator_log": "toolkit-validation failed: runtime not configured",
            "node_accepted": False,
        }
    init_statuses["toolkit-validation"] = "Completed"

    # 3. cuda-validation (spawns Job-style `nvidia-cuda-validator` -> 0/1 Completed)
    if not gates.cuda_sample_passed:
        init_statuses["cuda-validation"] = "Error"
        return {
            "init_containers": init_statuses,
            "toolkit_pod_state": "Running",
            "device_plugin_pod_state": "Running",
            "validator_pod_state": "Init:2/4",
            "validator_log": "CUDA error: no kernel image is available for execution on the device",
            "node_accepted": False,
        }
    init_statuses["cuda-validation"] = "Completed"

    # 4. plugin-validation (spawns `nvidia-device-plugin-validator` -> 0/1 Completed)
    if not gates.plugin_registered_and_allocatable:
        init_statuses["plugin-validation"] = "Error"
        return {
            "init_containers": init_statuses,
            "toolkit_pod_state": "Running",
            "device_plugin_pod_state": "CrashLoopBackOff",
            "validator_pod_state": "Init:3/4",
            "validator_log": "plugin-validation timed out waiting for allocatable GPU",
            "node_accepted": False,
        }
    init_statuses["plugin-validation"] = "Completed"

    return {
        "init_containers": init_statuses,
        "toolkit_pod_state": "Running",
        "device_plugin_pod_state": "Running",
        "validator_pod_state": "Running",
        "validator_log": "all validations are successful",
        "node_accepted": True,
    }


def compare_policy_vs_daemonset_health(
    desired_nodes: int = 25,
    driver_ready: int = 25,
    toolkit_ready: int = 25,
    device_plugin_ready: int = 24,
) -> Dict[str, object]:
    """Model the V10 Ch 6 gap between `ClusterPolicy.status.state: ready` and per-node health."""
    unhealthy_plugin_nodes = desired_nodes - device_plugin_ready
    return {
        "cluster_policy_state": "ready",
        "driver_ready_ratio": f"{driver_ready}/{desired_nodes}",
        "toolkit_ready_ratio": f"{toolkit_ready}/{desired_nodes}",
        "device_plugin_ready_ratio": f"{device_plugin_ready}/{desired_nodes}",
        "unhealthy_nodes_count": unhealthy_plugin_nodes,
        "fleet_fully_healthy": unhealthy_plugin_nodes == 0
        and driver_ready == desired_nodes
        and toolkit_ready == desired_nodes,
    }


def calculate_canary_vs_unpooled_blast_radius(
    total_nodes: int = 60,
    incompatible_kernel_nodes: int = 35,
    canary_pool_nodes: int = 3,
) -> Dict[str, float]:
    """Compute V10 Ch 6 blast radius: unpooled (35/60 = 58.33%) vs 3-node canary (3/60 = 5.0%)."""
    unpooled_pct = (incompatible_kernel_nodes / total_nodes) * 100.0
    canary_pct = (canary_pool_nodes / total_nodes) * 100.0
    untouched_nodes = total_nodes - canary_pool_nodes
    return {
        "unpooled_degraded_pct": round(unpooled_pct, 2),
        "unpooled_degraded_pct_rounded": float(round(unpooled_pct)),
        "canary_degraded_pct": round(canary_pct, 2),
        "canary_untouched_nodes": float(untouched_nodes),
    }


def plan_driver_upgrade_window(
    total_nodes: int = 40,
    gpus_per_node: int = 8,
    minutes_per_node_batch: int = 6,
    max_unavailable_nodes: int = 4,
    required_headroom_gpus: int = 28,
) -> Dict[str, object]:
    """Compute V10 Ch 7 driver DaemonSet rolling upgrade batches, duration, and GPU headroom."""
    batches = math.ceil(total_nodes / max_unavailable_nodes)
    wall_clock_minutes = batches * minutes_per_node_batch
    concurrent_gpus_offline = max_unavailable_nodes * gpus_per_node
    headroom_margin = required_headroom_gpus - concurrent_gpus_offline
    return {
        "batches": batches,
        "wall_clock_minutes": wall_clock_minutes,
        "concurrent_gpus_offline": concurrent_gpus_offline,
        "slo_safe": concurrent_gpus_offline <= required_headroom_gpus,
        "headroom_margin_gpus": headroom_margin,
    }


def classify_gpu_vs_network_operator_fault(
    allocatable_gpu: int,
    cuda_init_ok: bool,
    allocatable_rdma: int,
    ibv_devinfo_port_active: bool,
) -> Dict[str, str]:
    """Route multi-node training or RDMA issues between GPU Operator and Network Operator."""
    if allocatable_gpu <= 0 or not cuda_init_ok:
        return {
            "owner_operator": "GPU Operator",
            "failing_layer": "GPU driver, toolkit, or device plugin",
        }
    if allocatable_rdma <= 0:
        return {
            "owner_operator": "NVIDIA Network Operator",
            "failing_layer": "MOFED driver or RDMA device plugin (rdma/rdma_shared_device_a missing)",
        }
    if not ibv_devinfo_port_active:
        return {
            "owner_operator": "NVIDIA Network Operator",
            "failing_layer": "SR-IOV VF / Multus secondary CNI or physical IB/RoCE link (PORT_DOWN)",
        }
    return {
        "owner_operator": "Healthy",
        "failing_layer": "Both GPU Operator and Network Operator contracts verified",
    }
