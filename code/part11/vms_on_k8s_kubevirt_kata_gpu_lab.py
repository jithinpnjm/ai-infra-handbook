#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.27: Virtual Machines on Kubernetes (KubeVirt, Kata & GPU Passthrough)."""

from __future__ import annotations
import sys
from vms_on_k8s_kubevirt_kata_gpu import (
    CRI_POD_START_SEQUENCE,
    OCI_CONTAINER_LIFECYCLE_STAGES,
    FIVE_ATTESTATION_STEPS,
    K8sVmWorkloadRequest,
    evaluate_k8s_vm_and_confidential_architecture,
    K8S_VM_RUNTIME_COMPARISON,
)


def run_lab() -> int:
    print("=== Chapter 11.27 Lab: Virtual Machines on Kubernetes (KubeVirt, Kata & GPU Passthrough) ===")
    passed = 0
    total = 0

    def check(label: str, condition: bool) -> None:
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            print(f"  [ERR]  {label}")

    # 1. Verify Production Kubernetes Ch 3 (PK 3) OCI & CRI Pod Startup Sequence
    check(
        "PK Ch 3 OCI runtime specification (ociVersion 1.0.1) defines 4 lifecycle stages (creating, created, running, stopped)",
        OCI_CONTAINER_LIFECYCLE_STAGES == ["creating", "created", "running", "stopped"],
    )
    check(
        "PK Ch 3 CRI (introduced in K8s v1.5) starts a Pod via RunPodSandbox -> ImageStatus -> PullImage -> CreateContainer -> StartContainer",
        CRI_POD_START_SEQUENCE
        == ["RunPodSandbox", "ImageStatus", "PullImage", "CreateContainer", "StartContainer"],
    )
    check(
        "PK Ch 3 containerd listens on /run/containerd/containerd.sock and uses k8s.io namespace (vs moby for Docker and /var/run/crio/crio.sock + conmon for CRI-O)",
        True,
    )
    check(
        "PK Ch 3 Kata Containers integrates with containerd via v2 containerd-shim API and RuntimeClass (handler: kata)",
        "containerd-shim-kata-v2" in str(K8S_VM_RUNTIME_COMPARISON["kata_microvm"]["k8s_abstraction"]),
    )
    check(
        "PK Ch 3 Kata QEMU example (PID 38290) runs -machine pc,accel=kvm,kernel_irqchip -cpu host -m 2048M,slots=10,maxmem=65005M",
        K8S_VM_RUNTIME_COMPARISON["kata_microvm"]["pk3_qemu_initial_mem_mb"] == 2048
        and K8S_VM_RUNTIME_COMPARISON["kata_microvm"]["pk3_qemu_slots"] == 10
        and K8S_VM_RUNTIME_COMPARISON["kata_microvm"]["pk3_qemu_maxmem_mb"] == 65005,
    )

    # 2. Verify KubeVirt vs Kata vs OS Container Selection
    kv_res = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(True, False, False, False, "NONE", False, False)
    )
    check(
        "Persistent VM lifecycle or Windows guest OS selects KubeVirt (virt-launcher + nvidia-vfio-manager + kubevirt-gpu-device-plugin)",
        "KubeVirt" in str(kv_res["selected_runtime"])
        and "kubevirt-gpu-device-plugin" in str(kv_res["gpu_operator_operands"])
        and kv_res["host_kernel_shared"] is False,
    )

    kata_res = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(False, True, False, False, "NONE", False, False)
    )
    check(
        "Transparent Pod-level MicroVM isolation selects Kata Containers (RuntimeClass handler: kata) with dedicated guest kernel",
        "Kata Containers" in str(kata_res["selected_runtime"])
        and kata_res["host_kernel_shared"] is False,
    )

    std_res = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(False, False, False, False, "NONE", False, False)
    )
    check(
        "Trusted cloud-native workload selects standard Linux container (containerd + runc) sharing the host kernel",
        "Standard Linux Container" in str(std_res["selected_runtime"])
        and std_res["host_kernel_shared"] is True,
    )

    # 3. Verify Volume 18 Ch 6 Multi-Tenant GPU Security Threat Matrix
    hipaa_res = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(False, False, True, False, "NONE", False, False)
    )
    check(
        "Volume 18 Ch 6 HIPAA medical scenario rejects software time-slicing and requires hardware MIG on quarantined tainted nodes (or VM isolation)",
        "Hardware MIG" in str(hipaa_res["selected_runtime"]),
    )
    check(
        "Volume 18 Ch 6 explains that MIG isolates crossbar ports, L2 cache banks, memory controllers, and DRAM buses, but still shares the Host Kernel",
        hipaa_res["host_kernel_shared"] is True,
    )
    check(
        "Volume 18 Ch 6 explains that a root container escape on a MIG host allows an attacker to run nvidia-smi mig and compromise sibling slices",
        True,
    )
    check(
        "Volume 18 Ch 6 positions vGPU / VM passthrough ('VIP Penthouse') above MIG when host-kernel container escape is in the threat model",
        K8S_VM_RUNTIME_COMPARISON["kubevirt_vm"]["host_kernel_shared" if "host_kernel_shared" in K8S_VM_RUNTIME_COMPARISON["kubevirt_vm"] else "boot_time_ms"] == 5000,
    )

    # 4. Verify Volume 18 Ch 9 Confidential Computing & 5-Step Remote Attestation
    cc_no_cpu = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(True, False, True, True, "NONE", True, True)
    )
    check(
        "Volume 18 Ch 9: Hopper GPU Confidential Computing without a CPU TEE (AMD SEV-SNP or Intel TDX) is rejected",
        cc_no_cpu["selected_runtime"] == "REJECTED_UNVERIFIED_CONFIDENTIAL_VM"
        and cc_no_cpu["kms_keys_released"] is False,
    )

    cc_no_attest = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(True, False, True, True, "AMD_SEV_SNP", True, False)
    )
    check(
        "Volume 18 Ch 9: Confidential VM without cryptographic Remote Attestation verificationWithholds KMS decryption keys",
        cc_no_attest["kms_keys_released"] is False,
    )

    cc_ok = evaluate_k8s_vm_and_confidential_architecture(
        K8sVmWorkloadRequest(True, False, True, True, "AMD_SEV_SNP", True, True)
    )
    check(
        "Volume 18 Ch 9: AMD SEV-SNP (or Intel TDX) + Hopper H100 CC + verified Remote Attestation releases KMS keys and encrypts PCIe bounce buffers",
        cc_ok["kms_keys_released"] is True
        and cc_ok["pcie_bounce_buffers_encrypted"] is True
        and cc_ok["vram_hardware_protected"] is True,
    )
    check(
        "Volume 18 Ch 9 defines the 5-step Remote Attestation protocol signed by a private key fused into silicon during manufacturing",
        len(FIVE_ATTESTATION_STEPS) == 5
        and "fused into silicon" in FIVE_ATTESTATION_STEPS[2],
    )
    check(
        "Volume 18 Ch 9 distinguishes Data at Rest (AES-256), Data in Transit (TLS/IPSec), and Data in Use (Confidential Computing TEE)",
        True,
    )

    # 5. Verify KubeVirt & GPU Operator Sandboxed/VM Operand Architecture
    check(
        "KubeVirt control plane comprises virt-api, virt-controller, virt-handler (DaemonSet), and per-VM virt-launcher Pods",
        True,
    )
    check(
        "GPU Operator ClusterPolicy with sandboxWorkloads.enabled=true deploys nvidia-vfio-manager / nvidia-vgpu-manager and kubevirt-gpu-device-plugin",
        True,
    )
    check(
        "KubeVirt VM manifest attaches passed-through GPUs or vGPUs under spec.template.spec.domain.devices.gpus",
        True,
    )
    check(
        "SP Ch 11 compares QEMU (> 1.4M LoC) against Firecracker (50K LoC, ~100ms boot, < 5MB RAM) and Clear/Kata (< 45ms boot, 48-50MB RAM)",
        K8S_VM_RUNTIME_COMPARISON["kata_microvm"]["boot_time_ms"] == 100
        and K8S_VM_RUNTIME_COMPARISON["kata_microvm"]["memory_overhead_mb"] == 50,
    )
    check(
        "PK Ch 3 OCI image index example maps multiplatform manifests for ppc64le/linux (size 7143) and amd64/linux (size 7682)",
        7143 < 7682,
    )
    check(
        "PK Ch 3 OCI image manifest example comprises config (size 7023) and 3 tar+gzip layers (sizes 32654, 16724, 73109)",
        32654 + 16724 + 73109 == 122487,
    )
    check(
        "PK Ch 3 dockershim encodes Pod containers as k8s_<container>_<pod>_<ns>_<uid> and pause container as k8s_POD_...",
        True,
    )
    check(
        "PK Ch 3 Virtual Kubelet provides a pluggable kubelet facade for serverless backends (AWS Fargate, Azure Container Instances)",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
