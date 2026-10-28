"""Chapter 5.33 model: GPU Operator `gpuStateLabels` workload-config label
mapper & `isDaemonSetReady` (`RollingUpdate` vs `OnDelete`) evaluator,
`/run/nvidia/validations` vs `network.nvidia.com/operator.mofed.wait` per-node
dependency gate simulator, and Network Operator `state_skel.go` stale-object
cleanup detector.

Sources modeled:
- `NVIDIA/gpu-operator` (commit `0fbefd5`): `controllers/clusterpolicy_controller.go`,
  `controllers/state_manager.go` (`gpuStateLabels`), `controllers/object_controls.go`
  (`DaemonSet`, `isDaemonSetReady`, `isDaemonsetSpecChanged`), `cmd/nvidia-validator/main.go`.
- `Mellanox/network-operator` (commit `041bd87`): `controllers/nicclusterpolicy_controller.go`,
  `controllers/mofed_wait_labels.go`, `pkg/state/manager.go`, `pkg/state/state_skel.go`.
- Philippe Martin / Stefan Schimanski & Michael Hausenblas, Kubernetes
  Programming with Go / Programming Kubernetes (kubernetes-programming-with-go-
  programming-kubernetes-clients-and-operators-using-go-and-the-kuberne, KPG).
"""
from typing import Any, Dict, List, Mapping, Sequence, Set


WORKLOAD_CONFIG_LABELS: Dict[str, Dict[str, str]] = {
    "container": {
        "nvidia.com/gpu.deploy.driver": "true",
        "nvidia.com/gpu.deploy.container-toolkit": "true",
        "nvidia.com/gpu.deploy.device-plugin": "true",
        "nvidia.com/gpu.deploy.dcgm": "true",
        "nvidia.com/gpu.deploy.dcgm-exporter": "true",
        "nvidia.com/gpu.deploy.gpu-feature-discovery": "true",
        "nvidia.com/gpu.deploy.operator-validator": "true",
    },
    "vm-passthrough": {
        "nvidia.com/gpu.deploy.sandbox-validator": "true",
        "nvidia.com/gpu.deploy.vfio-manager": "true",
        "nvidia.com/gpu.deploy.sandbox-device-plugin": "true",
    },
    "vm-vgpu": {
        "nvidia.com/gpu.deploy.vgpu-host-driver": "true",
        "nvidia.com/gpu.deploy.vgpu-device-manager": "true",
        "nvidia.com/gpu.deploy.sandbox-validator": "true",
        "nvidia.com/gpu.deploy.sandbox-device-plugin": "true",
    },
}


def compute_gpu_node_deploy_labels(node_labels: Mapping[str, str]) -> Dict[str, str]:
    """Model Section 5 `NodeLabelingReconciler` & `gpuStateLabels` in `state_manager.go`."""
    if node_labels.get("feature.node.kubernetes.io/pci-10de.present") != "true":
        return {}
    if node_labels.get("nvidia.com/gpu.deploy.operands") == "false":
        return {"nvidia.com/gpu.present": "true", "nvidia.com/gpu.deploy.operands": "false"}

    wl_config = node_labels.get("nvidia.com/gpu.workload.config", "container")
    result = {"nvidia.com/gpu.present": "true"}
    result.update(WORKLOAD_CONFIG_LABELS.get(wl_config, WORKLOAD_CONFIG_LABELS["container"]))
    return result


def is_daemonset_ready(
    *,
    generation: int,
    observed_generation: int,
    desired_scheduled: int,
    number_unavailable: int,
    updated_scheduled: int,
    update_strategy: str = "RollingUpdate",
    current_revision_hash: str = "rev-2",
    pods_on_daemonset: Sequence[Mapping[str, Any]] = (),
) -> bool:
    """Model Section 4 `isDaemonSetReady` in `controllers/object_controls.go`."""
    if observed_generation < generation:
        return False
    if desired_scheduled == 0:
        return True
    if number_unavailable > 0:
        return False

    if update_strategy == "RollingUpdate":
        return updated_scheduled == desired_scheduled

    if update_strategy == "OnDelete":
        if len(pods_on_daemonset) != desired_scheduled:
            return False
        for pod in pods_on_daemonset:
            if pod.get("controller-revision-hash") != current_revision_hash:
                return False
            if not pod.get("all_containers_ready", False):
                return False
        return True

    raise ValueError(f"unknown update_strategy {update_strategy!r}")


def evaluate_node_operand_gating_and_stale_objects(
    *,
    validation_files_present: Set[str],
    mofed_pod_ready: bool,
    previously_rendered_objects: Set[str],
    currently_rendered_objects: Set[str],
) -> Dict[str, Any]:
    """Model Section 5, 9, & 10:
    - GPU Operator `/run/nvidia/validations` init-container gating.
    - Network Operator `network.nvidia.com/operator.mofed.wait` label (`"false"`
      when OFED is ready, `"true"` while waiting).
    - Network Operator `state_skel.go` stale-object cleanup (`previously - currently`).
    """
    toolkit_init_unblocked = "driver-ready" in validation_files_present
    device_plugin_init_unblocked = (
        "driver-ready" in validation_files_present and "toolkit-ready" in validation_files_present
    )
    mofed_wait_label = "false" if mofed_pod_ready else "true"
    stale_to_delete = sorted(previously_rendered_objects - currently_rendered_objects)

    return {
        "toolkit_init_unblocked": toolkit_init_unblocked,
        "device_plugin_init_unblocked": device_plugin_init_unblocked,
        "mofed_wait_label": mofed_wait_label,
        "rdma_dp_can_schedule": (mofed_wait_label == "false"),
        "stale_objects_to_delete": stale_to_delete,
    }
