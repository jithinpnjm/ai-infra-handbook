#!/usr/bin/env python3
"""Chapter 11.1 model: Why Kubernetes needs a GPU platform layer.

Models every architectural boundary, two-path triage gate (`Bound?` vs `CudaInit?`),
32-GPU pool fragmentation calculation, whole-GPU memory waste (`Llama-3.2-1B` `1.8 GB`
on `24 GB` `L4` = `92.5%` / `~92%` unused vs `10` time-sliced replicas), combinatorial
qualification matrix (`3 * 2 * 4 = 24`, `* 2 = 48` vs `2 * 4 = 8` profile pairs),
and 5-gate node acceptance verifier from:
  - `nvidia-devops` Volume 10 (`index.md`, `chapter-01`, `chapter-02`):
    * Two-path agreement (`Bound?` control/allocation path vs `CudaInit?` runtime/execution path)
    * 32-GPU pool fragmentation (`16` training + `8` dist-inference + `8` general;
      `24/32 = 75.0%` cluster idle while general pool hits `4/8 -> 0/8` free)
    * Qualification matrix (`3` kernels * `2` drivers * `4` image families = `24` runs,
      * `2` K8s versions = `48` runs -> collapsed to `2` node profiles * `4` image families = `8`)
    * 5-gate node acceptance checklist & layer-by-layer fault triage (`gpu-node-11` missing
      `nvidia.com/gpu` key + `CrashLoopBackOff` 14 restarts vs `gpu-node-22` `Ready` with
      empty `lsmod` and Secure Boot `error -1` vs `gpu-node-30` `Allocatable: 4` with
      `CreateContainerError` `/dev/nvidia0` vs `CUDA_CHECK_OK` + `no kernel image`)
  - *Generative AI on Kubernetes* (`GAK` Ch 3), *Kubernetes for Generative AI Solutions*
    (`K8GS` Ch 2 & Ch 10), *Scalable Kubernetes Infrastructure for AI Platforms* (`SKI` Ch 1 & 2),
    and *AI Systems Performance Engineering* (`ASP` Ch 3):
    * OpenAI `7,500` nodes, `71%` Fortune 100, `90%+` by 2027, `< 2%` container overhead (MLPerf v5.0)
    * PCI vendor `10de`, class `0302` (`feature.node.kubernetes.io/pci-0302_10de.present=true`)
    * `Llama-3.2-1B` (`1.8 GB`) on `L4` (`24 GB`, `g6.2xlarge`) = `92.5%` (`~92%`) unused memory;
      `70B` model = `280 GB` FP32 (`4 B`/param) vs `35 GB` 4-bit (`0.5 B`/param);
      `40 GB == 37.25 GiB`, `80 GB == 74.5 GiB`
    * AWS Trainium `Trn1` (`up to 50%` lower cost) & `Trn2` (`4x` Trn1 perf, `30%-40%` price-perf
      vs `P5e`/`P5en`, `100,000+` HF models).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple


OPENAI_K8S_MAX_NODES_EXAMPLE: int = 7500
FORTUNE_100_K8S_ADOPTION_PCT: int = 71
GARTNER_2027_CONTAINER_PCT: int = 90
CONTAINER_MAX_OVERHEAD_PCT: float = 2.0
NVIDIA_PCI_VENDOR_ID: str = "10de"
GPU_3D_CONTROLLER_PCI_CLASS: str = "0302"


@dataclass(frozen=True)
class TwoPathTriageResult:
    """Two-path GPU platform incident triage (`Bound?` vs `CudaInit?`, V10 Index & Ch 1)."""

    pod_bound: bool
    capacity_key_present: bool
    allocatable_gpus: int
    lsmod_nvidia_loaded: bool
    minimal_cuda_check_ok: bool
    framework_cuda_init_ok: bool
    failing_path: str
    failing_layer: str
    diagnosis: str


def triage_gpu_platform_incident(
    pod_bound: bool,
    capacity_key_present: bool = True,
    allocatable_gpus: int = 1,
    lsmod_nvidia_loaded: bool = True,
    minimal_cuda_check_ok: bool = True,
    framework_cuda_init_ok: bool = True,
) -> TwoPathTriageResult:
    """Route a Kubernetes GPU incident across the Control/Allocation path and Runtime/Execution path
    (V10 Ch 1 Figure 10.1.1 & V10 Ch 2 Figure 10.2.1).
    """
    if allocatable_gpus < 0:
        raise ValueError("allocatable_gpus must be non-negative")

    if not lsmod_nvidia_loaded:
        return TwoPathTriageResult(
            pod_bound=pod_bound,
            capacity_key_present=capacity_key_present,
            allocatable_gpus=allocatable_gpus,
            lsmod_nvidia_loaded=False,
            minimal_cuda_check_ok=False,
            framework_cuda_init_ok=False,
            failing_path="HOST_DRIVER_PATH",
            failing_layer="Layer 2: Host Kernel Driver (nvidia.ko)",
            diagnosis="Node is Ready at K8s layer, but nvidia.ko failed to load (check dmesg for Secure Boot / DKMS error -1)",
        )

    if not capacity_key_present:
        return TwoPathTriageResult(
            pod_bound=False,
            capacity_key_present=False,
            allocatable_gpus=0,
            lsmod_nvidia_loaded=True,
            minimal_cuda_check_ok=minimal_cuda_check_ok,
            framework_cuda_init_ok=framework_cuda_init_ok,
            failing_path="CONTROL_ADVERTISEMENT_PATH",
            failing_layer="Layer 4: Device Plugin Registration",
            diagnosis="nvidia.com/gpu key absent from status.capacity; device plugin never registered with kubelet gRPC socket",
        )

    if not pod_bound:
        return TwoPathTriageResult(
            pod_bound=False,
            capacity_key_present=True,
            allocatable_gpus=allocatable_gpus,
            lsmod_nvidia_loaded=True,
            minimal_cuda_check_ok=minimal_cuda_check_ok,
            framework_cuda_init_ok=framework_cuda_init_ok,
            failing_path="CONTROL_SCHEDULING_PATH",
            failing_layer="Layer 5: Scheduling Policy / Pool Capacity",
            diagnosis="Pod is Pending: compare request against pool allocatable capacity, taints, and nodeAffinity",
        )

    if not minimal_cuda_check_ok:
        return TwoPathTriageResult(
            pod_bound=True,
            capacity_key_present=True,
            allocatable_gpus=allocatable_gpus,
            lsmod_nvidia_loaded=True,
            minimal_cuda_check_ok=False,
            framework_cuda_init_ok=False,
            failing_path="RUNTIME_EXECUTION_PATH",
            failing_layer="Layer 3: Container Runtime / NVIDIA Container Toolkit / CDI",
            diagnosis="Pod bound (allocation succeeded), but container creation or minimal CUDA check failed (mount / CDI / toolkit error)",
        )

    if not framework_cuda_init_ok:
        return TwoPathTriageResult(
            pod_bound=True,
            capacity_key_present=True,
            allocatable_gpus=allocatable_gpus,
            lsmod_nvidia_loaded=True,
            minimal_cuda_check_ok=True,
            framework_cuda_init_ok=False,
            failing_path="WORKLOAD_IMAGE_PATH",
            failing_layer="Layer 6: Workload Container Image / CUDA sm_ Compatibility",
            diagnosis="Minimal CUDA_CHECK_OK passed on node; failure is inside the application framework image (e.g. missing sm_ kernel image)",
        )

    return TwoPathTriageResult(
        pod_bound=True,
        capacity_key_present=True,
        allocatable_gpus=allocatable_gpus,
        lsmod_nvidia_loaded=True,
        minimal_cuda_check_ok=True,
        framework_cuda_init_ok=True,
        failing_path="NONE",
        failing_layer="All 6 Layers Healthy",
        diagnosis="Both Control/Allocation path and Runtime/Execution path succeeded",
    )


@dataclass(frozen=True)
class PoolFragmentationReport:
    """32-GPU multi-pool taint fragmentation model (V10 Ch 1)."""

    total_cluster_gpus: int
    training_pool_gpus: int
    dist_inference_pool_gpus: int
    general_pool_gpus: int
    general_pool_used_before: int
    new_general_job_gpus: int
    general_pool_free_after: int
    cluster_used_after: int
    cluster_idle_after: int
    cluster_idle_pct: float
    cluster_utilization_pct: float
    next_unconstrained_job_schedulable: bool


def evaluate_pool_fragmentation(
    training_pool_gpus: int = 16,
    dist_inference_pool_gpus: int = 8,
    general_pool_gpus: int = 8,
    general_pool_used_before: int = 4,
    new_general_job_gpus: int = 4,
) -> PoolFragmentationReport:
    """Reproduce the V10 Ch 1 32-GPU pool fragmentation calculation (`24/32 = 75%` idle while general pool hits `0/8` free)."""
    if any(x <= 0 for x in (training_pool_gpus, dist_inference_pool_gpus, general_pool_gpus)):
        raise ValueError("Pool sizes must be positive")
    if general_pool_used_before < 0 or new_general_job_gpus < 0:
        raise ValueError("Used and requested GPUs must be non-negative")
    if general_pool_used_before + new_general_job_gpus > general_pool_gpus:
        raise ValueError("General pool allocation exceeds general pool capacity")

    tot = training_pool_gpus + dist_inference_pool_gpus + general_pool_gpus
    used_after = general_pool_used_before + new_general_job_gpus
    free_general_after = general_pool_gpus - used_after
    idle_cluster = tot - used_after
    idle_pct = round(idle_cluster / tot * 100.0, 1)
    util_pct = round(used_after / tot * 100.0, 1)

    return PoolFragmentationReport(
        total_cluster_gpus=tot,
        training_pool_gpus=training_pool_gpus,
        dist_inference_pool_gpus=dist_inference_pool_gpus,
        general_pool_gpus=general_pool_gpus,
        general_pool_used_before=general_pool_used_before,
        new_general_job_gpus=new_general_job_gpus,
        general_pool_free_after=free_general_after,
        cluster_used_after=used_after,
        cluster_idle_after=idle_cluster,
        cluster_idle_pct=idle_pct,
        cluster_utilization_pct=util_pct,
        next_unconstrained_job_schedulable=(free_general_after > 0),
    )


@dataclass(frozen=True)
class QualificationMatrixModel:
    """Combinatorial vs profile-based qualification matrix calculator (V10 Ch 2)."""

    kernels: int
    driver_branches: int
    image_families: int
    k8s_versions: int
    three_layer_combinations: int
    four_layer_combinations: int
    approved_node_profiles: int
    profile_based_combinations: int
    reduction_factor: float


def compute_qualification_matrix(
    kernels: int = 3,
    driver_branches: int = 2,
    image_families: int = 4,
    k8s_versions: int = 2,
    approved_node_profiles: int = 2,
) -> QualificationMatrixModel:
    """Compute `3 * 2 * 4 = 24`, `* 2 = 48` vs `2 profiles * 4 image families = 8` (V10 Ch 2)."""
    if any(x <= 0 for x in (kernels, driver_branches, image_families, k8s_versions, approved_node_profiles)):
        raise ValueError("All matrix counts must be positive")

    c3 = kernels * driver_branches * image_families
    c4 = c3 * k8s_versions
    prof = approved_node_profiles * image_families
    return QualificationMatrixModel(
        kernels=kernels,
        driver_branches=driver_branches,
        image_families=image_families,
        k8s_versions=k8s_versions,
        three_layer_combinations=c3,
        four_layer_combinations=c4,
        approved_node_profiles=approved_node_profiles,
        profile_based_combinations=prof,
        reduction_factor=round(c4 / prof, 2),
    )


@dataclass(frozen=True)
class ModelMemoryAndSharingPlan:
    """Model memory footprint (`70B` FP32 vs 4-bit, `Llama-3.2-1B` on `24 GB` L4) & GB->GiB conversion (GAK Ch 3 & K8GS Ch 10)."""

    gpu_vram_gb: float
    model_vram_gb: float
    single_pod_unused_vram_gb: float
    single_pod_unused_vram_pct: float
    time_slicing_replicas: int
    deployed_pods: int
    shared_used_vram_gb: float
    fits_in_vram: bool
    fp32_70b_gb: float
    int4_70b_gb: float
    gb_40_in_gib: float
    gb_80_in_gib: float


def evaluate_model_memory_and_sharing(
    gpu_vram_gb: float = 24.0,
    model_vram_gb: float = 1.8,
    time_slicing_replicas: int = 10,
    deployed_pods: int = 5,
    params_billions: float = 70.0,
) -> ModelMemoryAndSharingPlan:
    """Reproduce `K8GS Ch 10` (`1.8 GB` Llama-3.2-1B on `24 GB` L4 = `92.5%` / `~92%` unused; `10` replicas)
    and `GAK Ch 3` (`70B` = `280 GB` FP32 vs `35 GB` 4-bit; `40 GB == 37.25 GiB`, `80 GB == 74.5 GiB`).
    """
    if gpu_vram_gb <= 0 or model_vram_gb <= 0 or time_slicing_replicas <= 0 or deployed_pods <= 0:
        raise ValueError("VRAM and replica counts must be positive")

    unused_gb = round(gpu_vram_gb - model_vram_gb, 2)
    unused_pct = round(unused_gb / gpu_vram_gb * 100.0, 1)
    shared_gb = round(deployed_pods * model_vram_gb, 2)
    fp32_gb = round(params_billions * 4.0, 1)
    int4_gb = round(params_billions * 0.5, 1)
    gib_40 = round(40 * (10 ** 9) / (1024 ** 3), 2)
    gib_80 = round(80 * (10 ** 9) / (1024 ** 3), 1)

    return ModelMemoryAndSharingPlan(
        gpu_vram_gb=gpu_vram_gb,
        model_vram_gb=model_vram_gb,
        single_pod_unused_vram_gb=unused_gb,
        single_pod_unused_vram_pct=unused_pct,
        time_slicing_replicas=time_slicing_replicas,
        deployed_pods=deployed_pods,
        shared_used_vram_gb=shared_gb,
        fits_in_vram=(shared_gb <= gpu_vram_gb),
        fp32_70b_gb=fp32_gb,
        int4_70b_gb=int4_gb,
        gb_40_in_gib=gib_40,
        gb_80_in_gib=gib_80,
    )
