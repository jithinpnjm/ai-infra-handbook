#!/usr/bin/env python3
"""Chapter 10.9 model: The NVIDIA Software Stack: Driver, CUDA Toolkit, Container Toolkit, Compatibility.

Encodes the verifiable CUDA software stack layers, kernel modules, device node
major/minor numbers, driver backward/minor-version/forward compatibility rules,
PTX vs SASS/CUBIN fatbinary load-time resolution, JIT cold-start and host RAM
storms, and container CDI / runtime audit checks from:
- AI Systems Performance Engineering (ASP) Chapter 3 ("NVIDIA Software Stack"):
  GPU driver, CUDA Toolkit & Runtime (nvcc, cudart, cuBLAS, cuDNN, NCCL, CUTLASS),
  Python CUDA libraries (CUDA Python, cuTile, cuPyNumeric, CuPy, NVIDIA Warp,
  OpenAI Triton), PyTorch compiler stack (TorchDynamo, AOT Autograd, TorchInductor),
  and PTX vs CUBIN/SASS fatbinary forward/backward compatibility.
- nvidia-devops Volume 03 Chapter 02, Chapter 11 & Lab 01:
  7-step CUDA validation ladder (PCI 10de -> nvidia-smi -> /dev/nvidia* ->
  libcuda.so / libcudart.so -> nvcc -> context -> kernel returning 42),
  Runtime API (libcudart.so) vs Driver API (libcuda.so), lazy context init,
  nvcc -gencode arch=compute_XX,code=sm_XX / compute_XX, cuobjdump, PTX JIT
  cold start (2,340.6 ms request 1 vs 12.8 ms request 2 = 182.86x ~ 190x slower),
  and T4 (sm_75) -> L40S (sm_89) 10-pod * 5 GB = 50 GB host RAM JIT storm.
- nvidia-devops Legacy Volume 04 Chapter 02 (02-gpu-software-operator-masterclass.md):
  Kernel-Mode Driver modules (nvidia.ko, nvidia-uvm.ko, nvidia-modeset.ko,
  nvidia-peermem.ko), character devices (/dev/nvidia0 major 195 minor 0,
  /dev/nvidiactl major 195 minor 255, /dev/nvidia-modeset major 195 minor 254,
  /dev/nvidia-uvm), 4 Container Toolkit generations (nvidia-docker ->
  nvidia-docker2 -> OCI pre-start hook -> CDI 0.5.0 /var/run/cdi/nvidia.yaml),
  CUDA Forward Compatibility (/usr/local/cuda/compat in LD_LIBRARY_PATH),
  NVRM API mismatch (client 535.104.05 vs kernel module 525.105.17), and
  container PID namespace visibility in nvidia-smi.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence


class SoftwareStackError(ValueError):
    """Raised when invalid software stack or binary parameters are provided."""


@dataclass(frozen=True)
class KernelModuleSpec:
    module_name: str
    ko_filename: str
    device_nodes: tuple[str, ...]
    primary_role: str
    failure_if_missing: str


KERNEL_MODULES: Dict[str, KernelModuleSpec] = {
    "nvidia": KernelModuleSpec(
        module_name="nvidia",
        ko_filename="nvidia.ko",
        device_nodes=("/dev/nvidia0", "/dev/nvidiactl"),
        primary_role="Core kernel-mode driver (KMD): PCIe initialization, context/memory management, command submission, interrupt & Xid handling (major 195).",
        failure_if_missing="nvidia-smi and all CUDA calls fail immediately (NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver).",
    ),
    "nvidia_uvm": KernelModuleSpec(
        module_name="nvidia_uvm",
        ko_filename="nvidia-uvm.ko",
        device_nodes=("/dev/nvidia-uvm", "/dev/nvidia-uvm-tools"),
        primary_role="Unified Virtual Memory (UVM) page-fault handler and demand-paging migration between CPU and GPU.",
        failure_if_missing="Ordinary cudaMalloc works, but cudaMallocManaged / Unified Memory and modern AI frameworks requiring UVM fail to initialize.",
    ),
    "nvidia_modeset": KernelModuleSpec(
        module_name="nvidia_modeset",
        ko_filename="nvidia-modeset.ko",
        device_nodes=("/dev/nvidia-modeset",),
        primary_role="Display mode-setting engine (major 195, minor 254); loaded as a dependency of nvidia_drm on headless nodes.",
        failure_if_missing="Display/DRM consumers fail; headless compute unaffected unless module dependency chain is broken.",
    ),
    "nvidia_peermem": KernelModuleSpec(
        module_name="nvidia_peermem",
        ko_filename="nvidia-peermem.ko",
        device_nodes=(),
        primary_role="Registers GPU HBM physical pages with the InfiniBand/RoCE RDMA subsystem (mlx5) for zero-copy GPUDirect RDMA.",
        failure_if_missing="Intra-node NVLink still works, but inter-node GPUDirect RDMA silently falls back to staging through host CPU RAM.",
    ),
}

# Minimum host driver branch for native minor-version compatibility (also used in Ch 9.12)
CUDA_MAJOR_MIN_DRIVER: Dict[int, int] = {
    11: 450,
    12: 525,
    13: 580,
}

GPU_COMPUTE_CAPABILITIES: Dict[str, str] = {
    "V100": "sm_70",
    "T4": "sm_75",
    "A100": "sm_80",
    "A10": "sm_86",
    "L4": "sm_89",
    "L40S": "sm_89",
    "H100": "sm_90",
    "H200": "sm_90",
    "B200": "sm_100",
}


def evaluate_driver_cuda_compatibility(
    host_kmd_version: str,
    host_umd_version: str,
    container_cuda_major: int,
    container_cuda_minor: int,
    forward_compat_mounted: bool = False,
    forward_compat_driver_major: int = 535,
) -> Dict[str, object]:
    """Evaluate host Kernel-Mode Driver (KMD), User-Mode Driver (UMD), and container CUDA compatibility.

    Rules from V3 Ch 2, V3 Lab 01, and VL4 Ch 2 (§2.2, §6 Scenario B, §8):
    1. KMD (`nvidia.ko`) and host UMD (`libcuda.so`) must match exact version string;
       if they differ (e.g. client 535.104.05 vs kernel module 525.105.17), NVML/CUDA fails
       with `NVRM: API mismatch`.
    2. Driver backward compatibility: a newer host driver (e.g. 535 or 550) natively runs
       containers built with older CUDA toolkits (e.g. CUDA 11.4) without rebuilding.
    3. Minor-version compatibility: within a CUDA major family (e.g. CUDA 12.x), any host driver
       at or above `CUDA_MAJOR_MIN_DRIVER[major]` (525 for CUDA 12.x) natively supports newer
       CUDA 12.y runtimes (`libcudart.so.12`).
    4. CUDA Forward Compatibility (`/usr/local/cuda/compat` prepended to `LD_LIBRARY_PATH`):
       allows a newer CUDA toolkit container to run on an older enterprise host driver branch
       by supplying a newer user-mode `libcuda.so` inside the container, provided the compat
       package supports the host KMD branch.
    """
    if container_cuda_major not in CUDA_MAJOR_MIN_DRIVER or container_cuda_minor < 0:
        raise SoftwareStackError(f"Unsupported CUDA version: {container_cuda_major}.{container_cuda_minor}")

    try:
        kmd_major = int(host_kmd_version.split(".")[0])
    except (ValueError, IndexError) as exc:
        raise SoftwareStackError(f"Invalid host_kmd_version: {host_kmd_version}") from exc

    if host_kmd_version.strip() != host_umd_version.strip():
        return {
            "compatible": False,
            "mode": "KMD_UMD_API_MISMATCH",
            "reason": (
                f"NVRM: API mismatch: the client has the version {host_umd_version}, "
                f"but this kernel module has the version {host_kmd_version}. Reboot or reload nvidia.ko."
            ),
        }

    min_driver = CUDA_MAJOR_MIN_DRIVER[container_cuda_major]
    if kmd_major >= min_driver:
        mode = "BACKWARD_OR_MINOR_COMPATIBLE"
        return {
            "compatible": True,
            "mode": mode,
            "reason": (
                f"Host driver {host_kmd_version} (>= {min_driver}) natively supports "
                f"CUDA {container_cuda_major}.{container_cuda_minor} container via backward/minor-version compatibility."
            ),
        }

    if forward_compat_mounted and forward_compat_driver_major >= min_driver:
        return {
            "compatible": True,
            "mode": "CUDA_FORWARD_COMPATIBILITY",
            "reason": (
                f"Host driver {host_kmd_version} (< {min_driver}) is bridged by /usr/local/cuda/compat "
                f"(user-mode libcuda.so.{forward_compat_driver_major}) on LD_LIBRARY_PATH."
            ),
        }

    return {
        "compatible": False,
        "mode": "HOST_DRIVER_TOO_OLD",
        "reason": (
            f"Host driver {host_kmd_version} is older than minimum branch {min_driver} for "
            f"CUDA {container_cuda_major}.{container_cuda_minor} and /usr/local/cuda/compat is not active."
        ),
    }


def resolve_fatbinary_execution_path(
    target_gpu_sm: str,
    embedded_sass_targets: Sequence[str],
    embedded_ptx_targets: Sequence[str],
    jit_cache_enabled: bool = True,
    first_load_jit_ms: float = 2340.6,
    steady_state_kernel_ms: float = 12.8,
    concurrent_pods_on_node: int = 1,
    jit_ram_gb_per_pod: float = 5.0,
) -> Dict[str, object]:
    """Simulate fatbinary module load resolution per V3 Ch 11 and ASP Ch 3 (pp. 58-60).

    Three load-time outcomes (V3 Ch 11 Fig 3.11.1):
    1. Exact SASS (`CUBIN`) match (e.g. `sm_90` on H100): loads native machine code directly with 0 JIT delay.
    2. No exact SASS match, but compatible `compute_XX` PTX present (where `XX <= target_XX`):
       driver JIT-compiles PTX to target SASS on first load (`2,340.6 ms` vs `12.8 ms` steady state = `182.86x`
       slower in V3 Ch 11; or `15 min` startup and `10 pods * 5 GB = 50 GB` host RAM in V3 Ch 11 Customer Scenario).
    3. Neither matching SASS nor compatible PTX present: fails at first kernel launch with
       `cudaErrorNoKernelImageForDevice` (`CUDA error: no kernel image is available for execution on the device`).
    """
    if not target_gpu_sm.startswith("sm_") or not target_gpu_sm[3:].isdigit():
        raise SoftwareStackError(f"Invalid target_gpu_sm '{target_gpu_sm}' (expected 'sm_XX')")
    if first_load_jit_ms <= 0 or steady_state_kernel_ms <= 0 or concurrent_pods_on_node <= 0:
        raise SoftwareStackError("Timing and pod count parameters must be positive")

    target_ver = int(target_gpu_sm[3:])
    sass_set = {s.strip() for s in embedded_sass_targets}

    if target_gpu_sm in sass_set:
        return {
            "target_gpu_sm": target_gpu_sm,
            "path": "NATIVE_SASS_FAST_PATH",
            "can_execute": True,
            "requires_jit": False,
            "first_request_ms": round(steady_state_kernel_ms, 2),
            "steady_state_ms": round(steady_state_kernel_ms, 2),
            "cold_start_slowdown_x": 1.0,
            "total_jit_host_ram_gb": 0.0,
            "error": None,
        }

    compat_ptx: List[int] = []
    for p in embedded_ptx_targets:
        clean = p.strip()
        if clean.startswith("compute_") and clean[8:].isdigit():
            ptx_ver = int(clean[8:])
            if ptx_ver <= target_ver:
                compat_ptx.append(ptx_ver)

    if compat_ptx:
        slowdown = first_load_jit_ms / steady_state_kernel_ms
        total_ram = concurrent_pods_on_node * jit_ram_gb_per_pod
        return {
            "target_gpu_sm": target_gpu_sm,
            "path": "PTX_JIT_FALLBACK_PATH",
            "matched_ptx": f"compute_{max(compat_ptx)}",
            "can_execute": True,
            "requires_jit": True,
            "jit_cache_persisted": jit_cache_enabled,
            "first_request_ms": round(first_load_jit_ms, 2),
            "steady_state_ms": round(steady_state_kernel_ms, 2),
            "cold_start_slowdown_x": round(slowdown, 2),
            "total_jit_host_ram_gb": round(total_ram, 2),
            "error": None,
        }

    return {
        "target_gpu_sm": target_gpu_sm,
        "path": "NO_KERNEL_IMAGE_FAILURE",
        "can_execute": False,
        "requires_jit": False,
        "first_request_ms": None,
        "steady_state_ms": None,
        "cold_start_slowdown_x": None,
        "total_jit_host_ram_gb": 0.0,
        "error": "cudaErrorNoKernelImageForDevice: CUDA error: no kernel image is available for execution on the device",
    }


def diagnose_cuda_stack_boundary(
    pci_10de_present: bool = True,
    nvidia_smi_succeeds: bool = True,
    host_kmd_matches_umd: bool = True,
    dev_nvidia_nodes_present: bool = True,
    dev_nvidia_uvm_present: bool = True,
    libcuda_resolves: bool = True,
    libcudart_resolves: bool = True,
    nvidia_visible_devices: str = "all",
    cuda_visible_devices: str = "0",
    binary_has_compatible_code: bool = True,
    validation_kernel_result: int = 42,
) -> Dict[str, object]:
    """Walk the 7-layer CUDA fault-isolation ladder from V3 Ch 2 Fig 3.2.1, V3 Lab 01 Fig 3.L1.1, and VL4 Ch 2."""
    if not pci_10de_present:
        return {
            "healthy": False,
            "failing_layer": "1_PCI_ENUMERATION",
            "diagnosis": "GPU missing from `lspci -Dnn | grep -i 10de`; hardware seating, power whip, or BIOS PCIe boundary issue below the driver.",
        }
    if not nvidia_smi_succeeds or not host_kmd_matches_umd:
        return {
            "healthy": False,
            "failing_layer": "2_KERNEL_DRIVER_KMD",
            "diagnosis": "Kernel driver `nvidia.ko` not loaded or `NVRM: API mismatch` between `libcuda.so` and `nvidia.ko`; check `lsmod | grep nvidia` and `dmesg | grep NVRM`.",
        }
    if not dev_nvidia_nodes_present:
        return {
            "healthy": False,
            "failing_layer": "3_DEVICE_NODES_CDI",
            "diagnosis": "Host `nvidia-smi` works, but `/dev/nvidia0` or `/dev/nvidiactl` is missing in container; Container Toolkit / CDI (`/var/run/cdi/nvidia.yaml`) failed to inject device nodes.",
        }
    if not dev_nvidia_uvm_present:
        return {
            "healthy": False,
            "failing_layer": "3B_UVM_DEVICE_NODE",
            "diagnosis": "`/dev/nvidia-uvm` is missing (`nvidia-uvm.ko` not loaded or not injected); Unified Memory (`cudaMallocManaged`) and modern frameworks will fail.",
        }
    if nvidia_visible_devices.strip().lower() in {"none", "void", ""}:
        return {
            "healthy": False,
            "failing_layer": "4_ENV_VISIBILITY_FILTER",
            "diagnosis": f"Environment variable `NVIDIA_VISIBLE_DEVICES={nvidia_visible_devices}` silently disables container GPU injection.",
        }
    if cuda_visible_devices.strip() == "" or cuda_visible_devices.strip() == "-1":
        return {
            "healthy": False,
            "failing_layer": "4_ENV_VISIBILITY_FILTER",
            "diagnosis": f"`CUDA_VISIBLE_DEVICES='{cuda_visible_devices}'` hides all GPUs from the CUDA runtime (`cudaGetDeviceCount() == 0`).",
        }
    if not libcuda_resolves:
        return {
            "healthy": False,
            "failing_layer": "5_USER_MODE_DRIVER_LIBCUDA",
            "diagnosis": "`libcuda.so.1` missing from `ldconfig -p`; host user-mode driver library was not mounted into container by NVIDIA Container Toolkit / CDI.",
        }
    if not libcudart_resolves:
        return {
            "healthy": False,
            "failing_layer": "6_CUDA_RUNTIME_LIBCUDART",
            "diagnosis": "`libcudart.so` missing from `ldconfig -p` / `LD_LIBRARY_PATH`; incomplete CUDA Toolkit runtime installation inside image.",
        }
    if not binary_has_compatible_code or validation_kernel_result != 42:
        return {
            "healthy": False,
            "failing_layer": "7_DEVICE_CODE_EXECUTION",
            "diagnosis": "`import torch` and `cudaGetDeviceCount()` succeed, but first kernel launch fails (`cudaErrorNoKernelImageForDevice`) or returns wrong value; inspect binary with `cuobjdump --list-elf` / `--list-ptx`.",
        }
    return {
        "healthy": True,
        "failing_layer": "NONE",
        "diagnosis": "All 7 layers of the CUDA execution ladder verified (PCI 10de -> nvidia.ko -> /dev/nvidia* -> libcuda.so -> libcudart.so -> context -> kernel result == 42).",
    }


def bcm_container_stack_owners(
    gpu_operator_selected: bool,
    operator_toolkit_enabled: bool = True,
    operator_driver_enabled: bool = False,
    os_image_is_dgx_os: bool = False,
    cdi_available: bool = True,
    adv_configuration_flag: bool = False,
) -> dict:
    """Who installs the container toolkit and the driver on a BCM 11 Kubernetes cluster.

    Source: bcm11-containerization sections 2.7, 4.2 and 6.7 (the cm-kubernetes-setup wizard):
    - With the GPU Operator selected the wizard skips the two NVIDIA package screens, installs the BCM NVIDIA
      packages (cuda-dcgm) and does NOT install the cm-nvidia-container-toolkit package.
      `--adv-configuration-bcm-nvidia-packages` shows both screens anyway.
    - Operator toolkit.enabled (default on): the operator manages the toolkit and hooks it in through CDI plugins;
      with an older operator, or CDI disabled, containerd runtime-class drop-ins are used instead.
    - Operator toolkit.enabled off: BCM provides the toolkit as a system package and containerd runtime-class drop-ins.
    - Operator driver.enabled (default off): off = driver must already be on the host; on = operator driver container.
      On DGX OS images the driver is always provisioned by the host.
    """
    if gpu_operator_selected:
        shows_screens = bool(adv_configuration_flag)
        toolkit_owner = "gpu_operator" if operator_toolkit_enabled else "bcm_package_cm-nvidia-container-toolkit"
        bcm_toolkit_pkg_installed_by_wizard = (not operator_toolkit_enabled) and shows_screens
    else:
        shows_screens = True
        toolkit_owner = "bcm_package_cm-nvidia-container-toolkit"
        bcm_toolkit_pkg_installed_by_wizard = None  # depends on the administrator's answer on the screen
    if os_image_is_dgx_os:
        driver_owner = "host_provisioned_by_bcm"
    else:
        driver_owner = "operator_driver_container" if (gpu_operator_selected and operator_driver_enabled) else "host_provisioned_by_bcm"
    if toolkit_owner == "gpu_operator" and cdi_available:
        injection = "CDI"
    else:
        injection = "containerd_runtime_class_dropins"
    return {
        "shows_nvidia_package_screens": shows_screens,
        "toolkit_owner": toolkit_owner,
        "driver_owner": driver_owner,
        "device_injection": injection,
        "bcm_toolkit_package_installed_by_wizard": bcm_toolkit_pkg_installed_by_wizard,
    }
