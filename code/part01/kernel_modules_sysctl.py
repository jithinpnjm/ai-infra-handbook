"""Chapter 1.22 model: Kernel module vermagic and Secure Boot signature check,
NVIDIA kernel module unload dependency ordering, CUDA runtime vs host driver
branch compatibility (R525 for CUDA 12.x, R580 for CUDA 13.x), and GPU node
sysctl validation.

Sources modeled:
- Brian Ward, How Linux Works, 3rd ed. (how-linux-works-3rd-edition), Chapter 5
  (kernel parameters and UEFI Secure Boot).
- Chris Fregly, AI Systems Performance Engineering (ai-systems-performance-engineering),
  Chapter 3 ("OS, Docker, and Kubernetes Tuning for GPU-Based Environments":
  CUDA 12.x R525 / CUDA 13.x R580 driver branches, PTX/CUBIN fatbin, persistence
  mode 1-2s latency saved, clock locking, PYTORCH_ALLOC_CONF, <2% container overhead).
- nvidia-devops/volume-10/03-os-provisioning-and-linux-security-hardening.md
  (DKMS vs precompiled kABI/golden-image reasoning, MOK signing, GPU node sysctls).
"""
from typing import Dict, List


NVIDIA_MODULE_UNLOAD_ORDER: List[str] = [
    "nvidia_drm",
    "nvidia_modeset",
    "nvidia_peermem",
    "nvidia_uvm",
    "nvidia",
]

CUDA_MIN_DRIVER_BRANCH: Dict[int, int] = {
    11: 450,
    12: 525,
    13: 580,
}


def validate_module_load_eligibility(
    running_kernel_release: str,
    module_vermagic_release: str,
    secure_boot_enabled: bool,
    module_signed_by_trusted_key: bool,
    nouveau_loaded: bool = False,
) -> Dict[str, object]:
    """Determine whether modprobe nvidia succeeds or which exact kernel error occurs."""
    if running_kernel_release != module_vermagic_release:
        return {"can_load": False, "error": "Invalid module format (vermagic mismatch)"}
    if secure_boot_enabled and not module_signed_by_trusted_key:
        return {"can_load": False, "error": "Key was rejected by service / Required key not available (Secure Boot lockdown)"}
    if nouveau_loaded:
        return {"can_load": False, "error": "Device claimed by nouveau (blacklist nouveau and rebuild initramfs)"}
    return {"can_load": True, "error": None}


def check_cuda_driver_branch_compatibility(
    cuda_major: int,
    host_driver_branch: int,
    has_cuda_compat_pkg: bool = False,
) -> Dict[str, object]:
    """Check whether host_driver_branch (e.g. 525, 550, 580) supports cuda_major (11, 12, 13)."""
    if cuda_major not in CUDA_MIN_DRIVER_BRANCH:
        raise ValueError(f"Unsupported CUDA major version: {cuda_major}")
    min_branch = CUDA_MIN_DRIVER_BRANCH[cuda_major]
    native_ok = host_driver_branch >= min_branch
    compatible = native_ok or has_cuda_compat_pkg
    return {
        "cuda_major": cuda_major,
        "min_driver_branch": f"R{min_branch}",
        "host_driver_branch": f"R{host_driver_branch}",
        "native_compatible": native_ok,
        "compatible_with_forward_compat": compatible,
    }


def check_driver_library_version_match(loaded_kernel_mod_ver: str, userspace_nvml_ver: str) -> Dict[str, object]:
    """Detect the 'Failed to initialize NVML: Driver/library version mismatch' condition after an upgrade."""
    matched = loaded_kernel_mod_ver.strip() == userspace_nvml_ver.strip()
    return {
        "matched": matched,
        "error": None if matched else "Failed to initialize NVML: Driver/library version mismatch",
    }


def audit_gpu_node_sysctls(sysctls: Dict[str, int]) -> List[str]:
    """Audit key GPU-node sysctl parameters and return warnings for misconfigured defaults."""
    warnings: List[str] = []
    if sysctls.get("vm.swappiness", 60) > 10:
        warnings.append("vm.swappiness_too_high_for_gpu_node")
    if sysctls.get("vm.max_map_count", 65530) < 262144:
        warnings.append("vm.max_map_count_too_low_for_mmap_dataloaders")
    if sysctls.get("kernel.numa_balancing", 1) != 0:
        warnings.append("kernel.numa_balancing_enabled_causes_migration_jitter")
    return warnings
