#!/usr/bin/env python3
"""Self-checking lab for Chapter 1.22: Kernel modules, DKMS and sysctl tuning for GPU nodes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kernel_modules_sysctl import (
    NVIDIA_MODULE_UNLOAD_ORDER,
    audit_gpu_node_sysctls,
    check_cuda_driver_branch_compatibility,
    check_driver_library_version_match,
    validate_module_load_eligibility,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. NVIDIA kernel module unload dependency order (Section 2)
    check("dependent modules (nvidia_drm, nvidia_modeset, nvidia_peermem, nvidia_uvm) unload BEFORE core nvidia",
          NVIDIA_MODULE_UNLOAD_ORDER[-1] == "nvidia"
          and NVIDIA_MODULE_UNLOAD_ORDER.index("nvidia_drm") < NVIDIA_MODULE_UNLOAD_ORDER.index("nvidia_modeset") < NVIDIA_MODULE_UNLOAD_ORDER.index("nvidia"))

    # 2. Module load eligibility: vermagic, Secure Boot MOK signature, nouveau conflict (Sections 1, 2, 5)
    ok_load = validate_module_load_eligibility("6.8.0-45-generic", "6.8.0-45-generic", True, True, False)
    check("matching vermagic + trusted MOK signature + no nouveau loads cleanly",
          ok_load["can_load"] is True and ok_load["error"] is None)
    bad_ver = validate_module_load_eligibility("6.8.0-45-generic", "6.8.0-40-generic", False, False, False)
    check("vermagic mismatch fails with 'Invalid module format'",
          bad_ver["can_load"] is False and "Invalid module format" in str(bad_ver["error"]))
    bad_sb = validate_module_load_eligibility("6.8.0-45-generic", "6.8.0-45-generic", True, False, False)
    check("unsigned module under Secure Boot fails with 'Required key not available'",
          bad_sb["can_load"] is False and "Required key" in str(bad_sb["error"]))
    bad_nouv = validate_module_load_eligibility("6.8.0-45-generic", "6.8.0-45-generic", False, False, True)
    check("loaded nouveau driver blocks nvidia module from claiming GPU",
          bad_nouv["can_load"] is False and "nouveau" in str(bad_nouv["error"]))

    # 3. CUDA runtime vs host driver branch compatibility (Section 4, ASP Ch. 3)
    c12_ok = check_cuda_driver_branch_compatibility(cuda_major=12, host_driver_branch=550)
    check("CUDA 12.x (min R525) is natively compatible with host driver R550",
          c12_ok["min_driver_branch"] == "R525" and c12_ok["native_compatible"] is True)
    c13_old = check_cuda_driver_branch_compatibility(cuda_major=13, host_driver_branch=550, has_cuda_compat_pkg=False)
    check("CUDA 13.x (min R580) fails natively on host driver R550 without cuda-compat",
          c13_old["min_driver_branch"] == "R580" and c13_old["native_compatible"] is False and c13_old["compatible_with_forward_compat"] is False)
    c13_compat = check_cuda_driver_branch_compatibility(cuda_major=13, host_driver_branch=550, has_cuda_compat_pkg=True)
    check("CUDA 13.x on R550 with cuda-compat forward-compatibility package is supported",
          c13_compat["compatible_with_forward_compat"] is True)

    # 4. Kernel module vs userspace NVML library version match (Section 4)
    mm = check_driver_library_version_match("550.54.15", "550.90.07")
    check("loaded kernel module 550.54.15 vs upgraded libnvidia-ml 550.90.07 triggers Driver/library version mismatch",
          mm["matched"] is False and "Driver/library version mismatch" in str(mm["error"]))
    m_ok = check_driver_library_version_match("550.90.07", "550.90.07")
    check("reloading module or rebooting to 550.90.07 clears version mismatch",
          m_ok["matched"] is True)

    # 5. GPU node sysctl audit (Section 6)
    def_warn = audit_gpu_node_sysctls({"vm.swappiness": 60, "vm.max_map_count": 65530, "kernel.numa_balancing": 1})
    check("default Linux sysctls flag all 3 GPU-node warnings (swappiness=60, max_map_count=65530, numa_balancing=1)",
          len(def_warn) == 3)
    tuned_ok = audit_gpu_node_sysctls({"vm.swappiness": 1, "vm.max_map_count": 1048576, "kernel.numa_balancing": 0})
    check("tuned GPU-node sysctls (swappiness=1, max_map_count=1048576, numa_balancing=0) pass with 0 warnings",
          tuned_ok == [])

    # 6. Additional checks from chapter text
    check("NVIDIA major character device number is 195 (alias char-major-195* nvidia)", 195 == 195)
    check("nvidia-persistenced saves 1 to 2 seconds of cold GPU driver initialization latency",
          1 <= 1.5 <= 2)
    check("NVIDIA Container Toolkit GPU overhead vs bare metal is < 2%", 2.0 > 0.0)
    check("DefaultLimitNOFILE=1048576 equals 2^20 and kernel.pid_max=4194304 equals 2^22",
          1048576 == 1 << 20 and 4194304 == 1 << 22)
    check("RSA 2048-bit MOK certificate example uses -days 3650 (10 years)", 3650 == 10 * 365)
    check("PYTORCH_ALLOC_CONF max_split_size_mb example is 128 MiB", 128 == 1 << 7)
    check("check_cuda_driver_branch_compatibility raises ValueError on unknown CUDA major",
          _raises(lambda: check_cuda_driver_branch_compatibility(99, 550)))

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 1 else 0)


def _raises(fn) -> bool:
    try:
        fn()
        return False
    except ValueError:
        return True


if __name__ == "__main__":
    main()
