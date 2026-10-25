"""Chapter 11.3 — Node Feature Discovery and GPU Feature Discovery.

Deterministic models for:
1. NFD PCI / CPU / Kernel feature label generation (`feature.node.kubernetes.io/*`)
   and PCI class/vendor decoding (`0302` 3D controller, `0300` VGA, `10de` NVIDIA,
   `1002` AMD, `8086` Intel, `1d0f` AWS).
2. GFD NVML label synthesis (`nvidia.com/gpu.*`, `nvidia.com/mig.*`, `nvidia.com/cuda.*`)
   across exclusive, time-sliced (`-SHARED`), and MIG (`single` vs `mixed`) modes.
3. Three-tier label taxonomy governance (Discovered Fact, Lifecycle Assertion,
   Service Class) and SKU-coupling vs Service-Class fleet refresh impact (`80` nodes:
   `30` A100-80GB, `30` H100-80GB-HBM3, `20` A100-40GB).
4. Discovery drift & stale-label detector (`nfd-worker` timestamp vs maintenance
   timestamp, pool label asymmetry, and scheduler predicate evaluation).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


PCI_VENDOR_NAMES: Dict[str, str] = {
    "10de": "NVIDIA",
    "1002": "AMD",
    "8086": "Intel",
    "1d0f": "AWS",
}

PCI_CLASS_NAMES: Dict[str, str] = {
    "0302": "3D controller (GPU)",
    "0300": "VGA compatible controller",
}


@dataclass(frozen=True)
class HostHardwareProbe:
    """Raw host hardware & OS facts probed by NFD worker."""

    pci_devices: Tuple[Tuple[str, str], ...]  # (class_code, vendor_id)
    avx512f: bool = True
    cpu_multithreading: bool = True
    cpu_family: str = "6"
    cpu_model_id: str = "85"
    cpu_vendor: str = "Intel"
    selinux_enabled: bool = True
    kernel_full: str = "5.14.0-427.62.1.el9_4.x86_64"


def generate_nfd_labels(probe: HostHardwareProbe) -> Dict[str, str]:
    """Generate `feature.node.kubernetes.io/*` labels from a host probe."""
    labels: Dict[str, str] = {}
    for pci_class, vendor_id in probe.pci_devices:
        labels[f"feature.node.kubernetes.io/pci-{pci_class}_{vendor_id}.present"] = "true"
        if vendor_id == "10de":
            labels["feature.node.kubernetes.io/pci-10de.present"] = "true"
    if probe.avx512f:
        labels["feature.node.kubernetes.io/cpu-cpuid.AVX512F"] = "true"
    labels["feature.node.kubernetes.io/cpu-hardware_multithreading"] = (
        "true" if probe.cpu_multithreading else "false"
    )
    labels["feature.node.kubernetes.io/cpu-model.family"] = probe.cpu_family
    labels["feature.node.kubernetes.io/cpu-model.id"] = probe.cpu_model_id
    labels["feature.node.kubernetes.io/cpu-model.vendor_id"] = probe.cpu_vendor
    labels["feature.node.kubernetes.io/kernel-selinux.enabled"] = (
        "true" if probe.selinux_enabled else "false"
    )
    labels["feature.node.kubernetes.io/kernel-version.full"] = probe.kernel_full
    return labels


@dataclass(frozen=True)
class GpuNvmlProbe:
    """NVML GPU facts read by GPU Feature Discovery (GFD)."""

    physical_gpu_count: int
    product_name: str
    memory_mib: int
    family: str
    driver_version: str
    cuda_runtime_version: str
    compute_major: int
    compute_minor: int
    machine_type: str = "dgx-a100"
    mig_capable: bool = True
    mig_strategy: Optional[str] = None  # None, "single", "mixed"
    single_mig_profile: Optional[str] = None  # e.g., "1g.5gb"
    single_mig_slices_per_gpu: int = 7
    single_mig_slice_memory_mib: int = 5120
    mixed_mig_counts: Dict[str, int] = field(default_factory=dict)
    time_slicing_replicas: int = 1


def generate_gfd_labels(probe: GpuNvmlProbe) -> Dict[str, str]:
    """Synthesize GFD node labels (`nvidia.com/*`) according to Table 3-1 rules."""
    product = probe.product_name
    count = probe.physical_gpu_count
    memory = probe.memory_mib

    if probe.mig_strategy == "single" and probe.single_mig_profile:
        product = f"{product}-MIG-{probe.single_mig_profile}"
        count = probe.physical_gpu_count * probe.single_mig_slices_per_gpu
        memory = probe.single_mig_slice_memory_mib

    if probe.time_slicing_replicas > 1:
        product = f"{product}-SHARED"
        count = count * probe.time_slicing_replicas

    labels: Dict[str, str] = {
        "nvidia.com/gpu.present": "true",
        "nvidia.com/gpu.count": str(count),
        "nvidia.com/gpu.product": product,
        "nvidia.com/gpu.memory": str(memory),
        "nvidia.com/gpu.family": probe.family,
        "nvidia.com/cuda.driver-version.full": probe.driver_version,
        "nvidia.com/cuda.runtime.version.full": probe.cuda_runtime_version,
        "nvidia.com/mig.capable": "true" if probe.mig_capable else "false",
        "nvidia.com/gpu.replicas": str(probe.time_slicing_replicas),
        "nvidia.com/gpu.machine": probe.machine_type,
        "nvidia.com/gpu.compute.major": str(probe.compute_major),
        "nvidia.com/gpu.compute.minor": str(probe.compute_minor),
    }
    if probe.mig_strategy:
        labels["nvidia.com/mig.strategy"] = probe.mig_strategy
    if probe.mig_strategy == "mixed":
        for profile, prof_count in probe.mixed_mig_counts.items():
            labels[f"nvidia.com/mig-{profile}.count"] = str(prof_count)
    return labels


def classify_label_tier(label_key: str) -> Dict[str, str]:
    """Classify a node label into Discovered Fact, Lifecycle Assertion, or Service Class."""
    if label_key.startswith("feature.node.kubernetes.io/") or label_key.startswith(
        "nvidia.com/"
    ):
        return {
            "kind": "discovered_fact",
            "authoritative_writer": "discovery_component (NFD / GFD)",
            "consumer": "platform_automation_and_diagnostics",
        }
    if label_key in ("gpu-validation", "platform.nvidia.com/validation-state"):
        return {
            "kind": "lifecycle_assertion",
            "authoritative_writer": "controlled_platform_controller",
            "consumer": "admission_and_operations",
        }
    if label_key.startswith("gpu.platform.example/class") or label_key == "hardware-type":
        return {
            "kind": "service_class",
            "authoritative_writer": "platform_engineering",
            "consumer": "workload_manifests",
        }
    return {
        "kind": "unclassified",
        "authoritative_writer": "unknown",
        "consumer": "unknown",
    }


def evaluate_fleet_refresh_blast_radius(
    a100_80gb_nodes: int = 30,
    h100_80gb_nodes: int = 30,
    a100_40gb_retired_nodes: int = 20,
    workload_manifests_count: int = 45,
) -> Dict[str, int]:
    """Compare SKU-coupled affinity vs service-class affinity during a fleet refresh."""
    total_nodes = a100_80gb_nodes + h100_80gb_nodes + a100_40gb_retired_nodes
    return {
        "total_fleet_nodes": total_nodes,
        "retired_nodes": a100_40gb_retired_nodes,
        "sku_coupled_manifests_broken": workload_manifests_count,
        "service_class_manifests_broken": 0,
        "service_class_controller_configs_updated": 1,
    }


def evaluate_node_affinity_candidate(
    node_labels: Dict[str, str],
    node_taints: Dict[str, str],
    pod_tolerations: List[str],
    required_min_memory_mib: int = 40000,
    preferred_families: Tuple[str, ...] = ("hopper",),
    preferred_weight: int = 1,
) -> Tuple[bool, int, str]:
    """Evaluate Example 3-4 (`Gt 40000` MiB required + `In [hopper]` preferred weight 1) and taints."""
    for taint_key in node_taints:
        if taint_key not in pod_tolerations:
            return False, 0, f"Rejected: untolerated taint {taint_key}"
    mem_str = node_labels.get("nvidia.com/gpu.memory")
    if mem_str is None or int(mem_str) <= required_min_memory_mib:
        return (
            False,
            0,
            f"Rejected: nvidia.com/gpu.memory ({mem_str}) is not Gt {required_min_memory_mib}",
        )
    score = 0
    if node_labels.get("nvidia.com/gpu.family") in preferred_families:
        score += preferred_weight
    return True, score, "Eligible"


def detect_discovery_drift(
    last_probe_hhmmss: str,
    last_maintenance_hhmmss: str,
    pool_node_labels: Dict[str, Dict[str, str]],
    required_pool_keys: Tuple[str, ...] = (
        "nvidia.com/mig.capable",
        "nvidia.com/mig.strategy",
    ),
) -> Dict[str, object]:
    """Detect timestamp drift (`08:40:11` vs `09:15:00`) and missing pool keys (`gpu-node-13`)."""
    probe_stale = last_probe_hhmmss < last_maintenance_hhmmss
    asymmetric_nodes: List[str] = []
    for node_name, labels in pool_node_labels.items():
        for req_key in required_pool_keys:
            if req_key not in labels:
                asymmetric_nodes.append(node_name)
                break
    return {
        "probe_stale": probe_stale,
        "asymmetric_nodes": asymmetric_nodes,
        "safe_for_admission": (not probe_stale) and (len(asymmetric_nodes) == 0),
    }
