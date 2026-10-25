#!/usr/bin/env python3
"""Self-checking lab for Chapter 10.9: The NVIDIA software stack: driver, CUDA toolkit, container toolkit, compatibility."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nvidia_software_stack import (
    bcm_container_stack_owners,
    CUDA_MAJOR_MIN_DRIVER,
    GPU_COMPUTE_CAPABILITIES,
    KERNEL_MODULES,
    SoftwareStackError,
    diagnose_cuda_stack_boundary,
    evaluate_driver_cuda_compatibility,
    resolve_fatbinary_execution_path,
)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        msg = f"  [FAIL] {name}"
        if detail:
            msg += f" -> {detail}"
        print(msg)


def main() -> int:
    print("=== Chapter 10.9 Lab: The NVIDIA Software Stack (Driver, CUDA, Container Toolkit & Compatibility) ===")

    # 1. Kernel-Mode Driver (KMD) Modules & Character Devices (VL4 Ch 2 §2.1 & V3 Lab 01 Step 5)
    check(
        "VL4 Ch2 §2.1: Kernel-Mode Driver defines nvidia.ko, nvidia-uvm.ko, nvidia-modeset.ko, and nvidia-peermem.ko",
        set(KERNEL_MODULES.keys()) == {"nvidia", "nvidia_uvm", "nvidia_modeset", "nvidia_peermem"},
    )
    check(
        "V3 Lab 01 Step 5: nvidia.ko exposes /dev/nvidia0 and /dev/nvidiactl (major 195), and nvidia-uvm.ko exposes /dev/nvidia-uvm",
        "/dev/nvidia0" in KERNEL_MODULES["nvidia"].device_nodes
        and "/dev/nvidiactl" in KERNEL_MODULES["nvidia"].device_nodes
        and "/dev/nvidia-uvm" in KERNEL_MODULES["nvidia_uvm"].device_nodes,
    )

    # 2. Compute Capabilities Across GPU Generations (V3 Ch 11)
    check(
        "V3 Ch11: Compute capabilities map T4=sm_75, A100=sm_80, A10=sm_86, L4/L40S=sm_89, H100/H200=sm_90",
        GPU_COMPUTE_CAPABILITIES["T4"] == "sm_75"
        and GPU_COMPUTE_CAPABILITIES["A100"] == "sm_80"
        and GPU_COMPUTE_CAPABILITIES["A10"] == "sm_86"
        and GPU_COMPUTE_CAPABILITIES["L40S"] == "sm_89"
        and GPU_COMPUTE_CAPABILITIES["H100"] == "sm_90",
    )

    # 3. Driver Backward, Minor-Version, and Forward Compatibility (V3 Ch 2 Customer Scenario & VL4 Ch 2 §6/§8)
    back_ok = evaluate_driver_cuda_compatibility(
        host_kmd_version="535.154.05",
        host_umd_version="535.154.05",
        container_cuda_major=11,
        container_cuda_minor=4,
    )
    check(
        "V3 Ch2 Customer Scenario: Host driver 535.154.05 natively runs legacy CUDA 11.4 container via driver backward compatibility",
        back_ok["compatible"] is True and back_ok["mode"] == "BACKWARD_OR_MINOR_COMPATIBLE",
    )

    minor_ok = evaluate_driver_cuda_compatibility(
        host_kmd_version="550.90.07",
        host_umd_version="550.90.07",
        container_cuda_major=12,
        container_cuda_minor=4,
    )
    check(
        "V3 Lab 01: Host driver 550.90.07 (>= 525) natively supports CUDA 12.4 container",
        minor_ok["compatible"] is True and CUDA_MAJOR_MIN_DRIVER[12] == 525,
    )

    api_mismatch = evaluate_driver_cuda_compatibility(
        host_kmd_version="525.105.17",
        host_umd_version="535.104.05",
        container_cuda_major=12,
        container_cuda_minor=2,
    )
    check(
        "VL4 Ch2 §6 Scenario B: Detects NVRM API mismatch (client 535.104.05 vs kernel module 525.105.17)",
        api_mismatch["compatible"] is False
        and api_mismatch["mode"] == "KMD_UMD_API_MISMATCH"
        and "535.104.05" in api_mismatch["reason"]
        and "525.105.17" in api_mismatch["reason"],
    )

    too_old = evaluate_driver_cuda_compatibility(
        host_kmd_version="450",
        host_umd_version="450",
        container_cuda_major=12,
        container_cuda_minor=2,
        forward_compat_mounted=False,
    )
    check(
        "V3 Ch2 Customer Scenario: CUDA 12.2 container on legacy 450 host driver without forward-compat fails",
        too_old["compatible"] is False and too_old["mode"] == "HOST_DRIVER_TOO_OLD",
    )

    fwd_compat = evaluate_driver_cuda_compatibility(
        host_kmd_version="450",
        host_umd_version="450",
        container_cuda_major=12,
        container_cuda_minor=2,
        forward_compat_mounted=True,
        forward_compat_driver_major=535,
    )
    check(
        "VL4 Ch2 §8: /usr/local/cuda/compat (libcuda.so.535.104.05 on LD_LIBRARY_PATH) enables CUDA Forward Compatibility",
        fwd_compat["compatible"] is True and fwd_compat["mode"] == "CUDA_FORWARD_COMPATIBILITY",
    )

    # 4. Fatbinary SASS vs PTX Load-Time Resolution & JIT Storms (V3 Ch 11 & ASP Ch 3 pp. 58-60)
    sass_fast = resolve_fatbinary_execution_path(
        target_gpu_sm="sm_90",
        embedded_sass_targets=("sm_80", "sm_90"),
        embedded_ptx_targets=("compute_90",),
    )
    check(
        "V3 Ch11 Fig 3.11.1: Exact sm_90 SASS match loads on H100 via NATIVE_SASS_FAST_PATH with 0 JIT overhead (12.8 ms)",
        sass_fast["path"] == "NATIVE_SASS_FAST_PATH"
        and sass_fast["requires_jit"] is False
        and sass_fast["first_request_ms"] == 12.8,
    )

    ptx_jit = resolve_fatbinary_execution_path(
        target_gpu_sm="sm_90",
        embedded_sass_targets=("sm_80",),
        embedded_ptx_targets=("compute_80",),
        first_load_jit_ms=2340.6,
        steady_state_kernel_ms=12.8,
    )
    check(
        "V3 Ch11 §Production Troubleshooting: PTX-only load takes 2,340.6 ms on request 1 vs 12.8 ms steady state (182.86x ~ 190x slower)",
        ptx_jit["path"] == "PTX_JIT_FALLBACK_PATH"
        and ptx_jit["requires_jit"] is True
        and ptx_jit["first_request_ms"] == 2340.6
        and ptx_jit["steady_state_ms"] == 12.8
        and ptx_jit["cold_start_slowdown_x"] == 182.86,
    )

    l40s_storm = resolve_fatbinary_execution_path(
        target_gpu_sm="sm_89",
        embedded_sass_targets=("sm_75",),
        embedded_ptx_targets=("compute_75",),
        concurrent_pods_on_node=10,
        jit_ram_gb_per_pod=5.0,
    )
    check(
        "V3 Ch11 Customer Scenario: 10 pods on L40S (sm_89) with only T4 SASS (sm_75) + PTX consume 10 * 5 GB == 50.0 GB host RAM in JIT storm",
        l40s_storm["path"] == "PTX_JIT_FALLBACK_PATH"
        and l40s_storm["matched_ptx"] == "compute_75"
        and l40s_storm["total_jit_host_ram_gb"] == 50.0,
    )

    no_img = resolve_fatbinary_execution_path(
        target_gpu_sm="sm_90",
        embedded_sass_targets=("sm_80", "sm_86"),
        embedded_ptx_targets=(),
    )
    check(
        "V3 Ch11 Story: Binary with only sm_80/sm_86 SASS and no PTX fails on H100 (sm_90) with cudaErrorNoKernelImageForDevice",
        no_img["path"] == "NO_KERNEL_IMAGE_FAILURE"
        and no_img["can_execute"] is False
        and "no kernel image is available" in no_img["error"],
    )

    # 5. 7-Layer CUDA Fault-Isolation Ladder (V3 Ch 2 Fig 3.2.1 & V3 Lab 01 Fig 3.L1.1)
    ok_ladder = diagnose_cuda_stack_boundary()
    check(
        "V3 Lab 01: Complete 7-layer CUDA validation chain (kernel result == 42) passes",
        ok_ladder["healthy"] is True and ok_ladder["failing_layer"] == "NONE",
    )

    f_pci = diagnose_cuda_stack_boundary(pci_10de_present=False)
    check(
        "V3 Lab 01 Step 1: Missing PCI vendor 10de isolates fault to 1_PCI_ENUMERATION below the driver",
        f_pci["healthy"] is False and f_pci["failing_layer"] == "1_PCI_ENUMERATION",
    )

    f_kmd = diagnose_cuda_stack_boundary(nvidia_smi_succeeds=False)
    check(
        "V3 Lab 01 Step 2: Failed nvidia-smi with PCI present isolates fault to 2_KERNEL_DRIVER_KMD",
        f_kmd["healthy"] is False and f_kmd["failing_layer"] == "2_KERNEL_DRIVER_KMD",
    )

    f_dev = diagnose_cuda_stack_boundary(dev_nvidia_nodes_present=False)
    check(
        "V3 Ch2 §Production Troubleshooting: Missing /dev/nvidia* in container with working host nvidia-smi isolates to 3_DEVICE_NODES_CDI",
        f_dev["healthy"] is False and f_dev["failing_layer"] == "3_DEVICE_NODES_CDI",
    )

    f_uvm = diagnose_cuda_stack_boundary(dev_nvidia_uvm_present=False)
    check(
        "V3 Lab 01 Step 5 & VL4 Ch2 §2.1: Missing /dev/nvidia-uvm isolates fault to 3B_UVM_DEVICE_NODE",
        f_uvm["healthy"] is False and f_uvm["failing_layer"] == "3B_UVM_DEVICE_NODE",
    )

    f_env_nv = diagnose_cuda_stack_boundary(nvidia_visible_devices="none")
    check(
        "V3 Ch2 Row 3: NVIDIA_VISIBLE_DEVICES=none silently disables container GPU injection (4_ENV_VISIBILITY_FILTER)",
        f_env_nv["healthy"] is False and f_env_nv["failing_layer"] == "4_ENV_VISIBILITY_FILTER",
    )

    f_env_cuda = diagnose_cuda_stack_boundary(cuda_visible_devices="")
    check(
        "V3 Lab 01 Step 13: CUDA_VISIBLE_DEVICES='' forces cudaGetDeviceCount() == 0 (4_ENV_VISIBILITY_FILTER)",
        f_env_cuda["healthy"] is False and f_env_cuda["failing_layer"] == "4_ENV_VISIBILITY_FILTER",
    )

    f_libcuda = diagnose_cuda_stack_boundary(libcuda_resolves=False)
    check(
        "V3 Ch2 & Lab 01 Step 7: Missing libcuda.so.1 in ldconfig -p isolates fault to 5_USER_MODE_DRIVER_LIBCUDA",
        f_libcuda["healthy"] is False and f_libcuda["failing_layer"] == "5_USER_MODE_DRIVER_LIBCUDA",
    )

    f_libcudart = diagnose_cuda_stack_boundary(libcudart_resolves=False)
    check(
        "V3 Lab 01 Step 7: Missing libcudart.so isolates fault to 6_CUDA_RUNTIME_LIBCUDART",
        f_libcudart["healthy"] is False and f_libcudart["failing_layer"] == "6_CUDA_RUNTIME_LIBCUDART",
    )

    f_kern = diagnose_cuda_stack_boundary(binary_has_compatible_code=False)
    check(
        "V3 Ch2 & Ch11: Lazy init where import succeeds but first kernel fails isolates to 7_DEVICE_CODE_EXECUTION",
        f_kern["healthy"] is False and f_kern["failing_layer"] == "7_DEVICE_CODE_EXECUTION",
    )

    # 6. Input Validation Checks
    try:
        evaluate_driver_cuda_compatibility("550.90.07", "550.90.07", 9, 0)
        check("Rejects unsupported CUDA major version", False)
    except SoftwareStackError:
        check("Rejects unsupported CUDA major version", True)

    try:
        evaluate_driver_cuda_compatibility("bad_ver", "550.90.07", 12, 4)
        check("Rejects malformed host driver version string", False)
    except SoftwareStackError:
        check("Rejects malformed host driver version string", True)

    try:
        resolve_fatbinary_execution_path("invalid_arch", ("sm_80",), ("compute_80",))
        check("Rejects invalid target_gpu_sm format", False)
    except SoftwareStackError:
        check("Rejects invalid target_gpu_sm format", True)

    # BCM container stack ownership (bcm11-containerization, added after review)
    a = bcm_container_stack_owners(gpu_operator_selected=True)
    check("bcm11-containerization 4.2: with the GPU Operator selected, the wizard skips both NVIDIA package screens and the operator owns the toolkit via CDI",
          a["shows_nvidia_package_screens"] is False and a["toolkit_owner"] == "gpu_operator" and a["device_injection"] == "CDI"
          and a["bcm_toolkit_package_installed_by_wizard"] is False)
    b = bcm_container_stack_owners(gpu_operator_selected=True, adv_configuration_flag=True)
    check("bcm11-containerization 4.2: --adv-configuration-bcm-nvidia-packages shows the screens even with the operator", b["shows_nvidia_package_screens"] is True)
    c = bcm_container_stack_owners(gpu_operator_selected=True, operator_toolkit_enabled=False)
    check("bcm11-containerization 6.7.1: toolkit.enabled off means the BCM package owns the toolkit and containerd runtime-class drop-ins are used",
          c["toolkit_owner"] == "bcm_package_cm-nvidia-container-toolkit" and c["device_injection"] == "containerd_runtime_class_dropins")
    d = bcm_container_stack_owners(gpu_operator_selected=True, cdi_available=False)
    check("bcm11-containerization 6.7.1: older operator or CDI disabled falls back to runtime-class drop-ins", d["device_injection"] == "containerd_runtime_class_dropins")
    e = bcm_container_stack_owners(gpu_operator_selected=True, operator_driver_enabled=True)
    f = bcm_container_stack_owners(gpu_operator_selected=True, operator_driver_enabled=True, os_image_is_dgx_os=True)
    check("bcm11-containerization 6.7: driver.enabled gives an operator driver container, but on DGX OS the driver is always host-provisioned",
          e["driver_owner"] == "operator_driver_container" and f["driver_owner"] == "host_provisioned_by_bcm")

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
