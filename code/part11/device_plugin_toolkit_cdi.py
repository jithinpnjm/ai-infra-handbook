"""Chapter 11.2 — Device plugin, container toolkit, CDI and runtime classes.

Deterministic models for:
1. Kubelet Device Plugin gRPC state machine (Register, ListAndWatch, Allocate)
   and Capacity vs Allocatable vs Allocated accounting.
2. Container Device Interface (CDI) specification generation (`cdiVersion: 0.5.0`,
   `kind: nvidia.com/gpu`) and containerd `config.toml` runtime handler resolution.
3. Fleet placement probability when bare `nvidia.com/gpu` requests are scheduled
   without hardware-class node affinity (`15 / 40 = 37.5%` mismatch risk).
4. Dependency-ordered missing-allocatable-GPU and runtime-injection triage engine.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DeviceNodeSpec:
    """Linux character device node entry inside a CDI specification."""

    path: str
    dev_type: str
    major: int
    minor: int


@dataclass(frozen=True)
class MountSpec:
    """Bind mount entry inside a CDI specification."""

    host_path: str
    container_path: str
    options: Tuple[str, ...] = ("ro", "nosuid", "nodev", "bind")


@dataclass(frozen=True)
class CdiDeviceEntry:
    """Single GPU entry inside a CDI specification (`nvidia.com/gpu`)."""

    name: str
    uuid: str
    device_nodes: Tuple[DeviceNodeSpec, ...]
    mounts: Tuple[MountSpec, ...]


@dataclass(frozen=True)
class CdiSpec:
    """Container Device Interface (CDI) specification model."""

    cdi_version: str
    kind: str
    devices: Tuple[CdiDeviceEntry, ...]


def generate_cdi_spec(
    gpu_uuids: List[str],
    uvm_major: int = 238,
    driver_lib_path: str = "/usr/lib/x86_64-linux-gnu/libcuda.so.1",
    smi_path: str = "/usr/bin/nvidia-smi",
) -> CdiSpec:
    """Generate a CDI 0.5.0 specification for discovered NVIDIA GPUs."""
    entries: List[CdiDeviceEntry] = []
    common_nodes = (
        DeviceNodeSpec(path="/dev/nvidiactl", dev_type="c", major=195, minor=255),
        DeviceNodeSpec(path="/dev/nvidia-uvm", dev_type="c", major=uvm_major, minor=0),
    )
    common_mounts = (
        MountSpec(host_path=driver_lib_path, container_path=driver_lib_path),
        MountSpec(host_path=smi_path, container_path=smi_path),
    )
    for idx, uuid in enumerate(gpu_uuids):
        gpu_node = DeviceNodeSpec(
            path=f"/dev/nvidia{idx}", dev_type="c", major=195, minor=idx
        )
        entries.append(
            CdiDeviceEntry(
                name=str(idx),
                uuid=uuid,
                device_nodes=(gpu_node,) + common_nodes,
                mounts=common_mounts,
            )
        )
    return CdiSpec(
        cdi_version="0.5.0",
        kind="nvidia.com/gpu",
        devices=tuple(entries),
    )


@dataclass
class KubeletDevicePluginState:
    """Models the kubelet <-> device-plugin gRPC contract on a single GPU node."""

    node_name: str
    resource_name: str = "nvidia.com/gpu"
    socket_path: str = "/var/lib/kubelet/device-plugins/nvidia-gpu.sock"
    registered: bool = False
    stream_open: bool = False
    device_health: Dict[str, str] = field(default_factory=dict)
    historical_capacity: Optional[int] = None
    allocated_devices: List[str] = field(default_factory=list)

    def register(self, device_uuids: List[str]) -> bool:
        """Simulate gRPC Register() + opening ListAndWatch()."""
        self.registered = True
        self.stream_open = True
        self.device_health = {uuid: "Healthy" for uuid in device_uuids}
        self.historical_capacity = len(device_uuids)
        return True

    def mark_unhealthy(self, uuid: str) -> None:
        """Update health state over ListAndWatch()."""
        if uuid in self.device_health:
            self.device_health[uuid] = "Unhealthy"

    def drop_stream(self) -> None:
        """Simulate plugin crash or lost gRPC connection after prior registration."""
        self.stream_open = False
        self.registered = False

    def node_status(self) -> Dict[str, Optional[int]]:
        """Return Capacity, Allocatable, Allocated, and Schedulable Free counts."""
        if self.historical_capacity is None:
            return {
                "capacity": None,
                "allocatable": None,
                "allocated": 0,
                "free_schedulable": 0,
            }
        if not self.registered or not self.stream_open:
            return {
                "capacity": self.historical_capacity,
                "allocatable": None,
                "allocated": len(self.allocated_devices),
                "free_schedulable": 0,
            }
        healthy_count = sum(
            1 for state in self.device_health.values() if state == "Healthy"
        )
        free_count = max(0, healthy_count - len(self.allocated_devices))
        return {
            "capacity": self.historical_capacity,
            "allocatable": healthy_count,
            "allocated": len(self.allocated_devices),
            "free_schedulable": free_count,
        }

    def allocate(
        self, count: int, strategy: str = "cdi-annotations"
    ) -> Dict[str, object]:
        """Simulate Kubelet Allocate() call to the device plugin for a bound Pod."""
        if not self.registered or not self.stream_open:
            raise RuntimeError("Device plugin stream is not active")
        healthy_free = [
            uuid
            for uuid, health in self.device_health.items()
            if health == "Healthy" and uuid not in self.allocated_devices
        ]
        if len(healthy_free) < count:
            raise ValueError(
                f"Insufficient healthy GPUs: requested {count}, available {len(healthy_free)}"
            )
        chosen = healthy_free[:count]
        self.allocated_devices.extend(chosen)
        uuid_to_idx = {
            uuid: idx for idx, uuid in enumerate(self.device_health.keys())
        }
        indices = [uuid_to_idx[u] for u in chosen]
        if strategy == "cdi-annotations":
            return {
                "allocated_uuids": chosen,
                "cdi_devices": [f"nvidia.com/gpu={i}" for i in indices],
                "device_paths": [f"/dev/nvidia{i}" for i in indices],
            }
        return {
            "allocated_uuids": chosen,
            "env": {"NVIDIA_VISIBLE_DEVICES": ",".join(chosen)},
            "device_paths": [f"/dev/nvidia{i}" for i in indices],
        }


def validate_extended_resource_spec(
    requests: Optional[Dict[str, int]],
    limits: Optional[Dict[str, int]],
    resource_name: str = "nvidia.com/gpu",
) -> Tuple[bool, str]:
    """Validate Kubernetes Pod extended-resource rules for `nvidia.com/gpu`."""
    req_val = (requests or {}).get(resource_name)
    lim_val = (limits or {}).get(resource_name)
    if lim_val is None:
        if req_val is not None:
            return (
                False,
                "Invalid: specifying requests without limits is not allowed for extended resources",
            )
        return False, "No GPU extended resource requested"
    if lim_val <= 0:
        return False, "Invalid: GPU limit must be a positive integer"
    if req_val is not None and req_val != lim_val:
        return (
            False,
            f"Invalid: requests ({req_val}) must equal limits ({lim_val}) for extended resources",
        )
    return True, f"Valid extended resource spec: {resource_name}={lim_val}"


def compute_underspecified_placement_risk(
    total_nodes: int = 40,
    qualified_nvlink_nodes: int = 25,
    older_pcie_nodes: int = 15,
    has_required_affinity: bool = False,
) -> Dict[str, float]:
    """Compute the probability of landing on an older PCIe pool without node affinity."""
    if total_nodes != qualified_nvlink_nodes + older_pcie_nodes:
        raise ValueError("Node counts must sum to total_nodes")
    if has_required_affinity:
        eligible = qualified_nvlink_nodes
        wrong_pool_prob = 0.0
    else:
        eligible = total_nodes
        wrong_pool_prob = (older_pcie_nodes / total_nodes) * 100.0
    return {
        "eligible_nodes": float(eligible),
        "wrong_pool_probability_pct": round(wrong_pool_prob, 2),
        "qualified_pool_probability_pct": round(100.0 - wrong_pool_prob, 2),
    }


@dataclass(frozen=True)
class MissingGpuTriageCase:
    """Input evidence for dependency-ordered missing-GPU or failed-injection triage."""

    name: str
    lspci_visible: bool
    host_nvidia_smi_ok: bool
    plugin_pod_running_and_enumerated: bool
    kubelet_registered: bool
    allocatable_gpus: int
    container_devices_populated: bool
    container_nvidia_smi_ok: bool


def triage_gpu_node_or_pod(case: MissingGpuTriageCase) -> Dict[str, str]:
    """Return the lowest failing boundary and next action in strict dependency order."""
    if not case.lspci_visible:
        return {
            "failing_boundary": "hardware_pci_passthrough",
            "next_action": "Stop and escalate to hardware/cloud provider (PCI device absent)",
        }
    if not case.host_nvidia_smi_ok:
        return {
            "failing_boundary": "driver_kernel_boundary",
            "next_action": "Inspect journalctl -k for NVRM/Xid/RmInitAdapter; do not touch device plugin yet",
        }
    if not case.plugin_pod_running_and_enumerated:
        return {
            "failing_boundary": "device_plugin_boundary",
            "next_action": "Inspect DaemonSet selector, Pod events, and NVML init in device-plugin logs",
        }
    if not case.kubelet_registered or case.allocatable_gpus <= 0:
        return {
            "failing_boundary": "kubelet_registration_boundary",
            "next_action": "Inspect journalctl -u kubelet for registration dial timeout on /var/lib/kubelet/device-plugins/",
        }
    if not case.container_devices_populated:
        return {
            "failing_boundary": "runtime_injection_boundary",
            "next_action": "Inspect containerd config.toml, RuntimeClass handler, and /var/run/cdi spec",
        }
    if not case.container_nvidia_smi_ok:
        return {
            "failing_boundary": "driver_to_image_compatibility",
            "next_action": "Compare minimal validation image vs workload CUDA user-space / LD_LIBRARY_PATH",
        }
    return {
        "failing_boundary": "healthy_or_scheduling_policy",
        "next_action": "Node and runtime path healthy; if Pod is Pending, inspect taints, affinity, and quotas",
    }
