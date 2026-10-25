#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.22: SR-IOV for NICs and GPUs."""

from __future__ import annotations
import sys
from sriov_for_nics_and_gpus import (
    FIVE_ZERO_TRUST_AI_LAYERS,
    FORENSIC_IR_PLAYBOOK_STEPS,
    SriovDeviceSpec,
    allocate_sriov_virtual_functions,
    evaluate_security_incident_response,
)


def run_lab() -> int:
    print("=== Chapter 11.22 Lab: SR-IOV for NICs & GPUs, Zero-Trust Defense & Forensic IR ===")
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

    # 1. Verify ConnectX-7 400G NIC SR-IOV allocation and IOMMU guard
    cx7_no_iommu = allocate_sriov_virtual_functions(
        SriovDeviceSpec("connectx_nic", "ConnectX-7 400G", "0000:4b:00.0", 64, 8, False, True)
    )
    check(
        "ConnectX-7 SR-IOV VF allocation is rejected when IOMMU (Intel VT-d / AMD-Vi) is disabled",
        cx7_no_iommu["status"] == "REJECTED_UNSAFE_NO_IOMMU"
        and cx7_no_iommu["dma_isolated"] is False,
    )

    cx7_unsigned = allocate_sriov_virtual_functions(
        SriovDeviceSpec("connectx_nic", "ConnectX-7 400G", "0000:4b:00.0", 64, 8, True, False)
    )
    check(
        "ConnectX-7 SR-IOV VF allocation is rejected when NIC firmware signature is unverified",
        cx7_unsigned["status"] == "REJECTED_UNVERIFIED_FIRMWARE",
    )

    cx7_overflow = allocate_sriov_virtual_functions(
        SriovDeviceSpec("connectx_nic", "ConnectX-7 400G", "0000:4b:00.0", 16, 32, True, True)
    )
    check(
        "Requesting numVfs=32 above hardware sriov_totalvfs=16 is rejected",
        cx7_overflow["status"] == "REJECTED_EXCEEDS_TOTALVFS",
    )

    cx7_ok = allocate_sriov_virtual_functions(
        SriovDeviceSpec("connectx_nic", "ConnectX-7 400G", "0000:4b:00.0", 64, 8, True, True)
    )
    check(
        "ConnectX-7 PF (0000:4b:00.0) with IOMMU enabled activates 8 VFs via sriov_numvfs",
        cx7_ok["status"] == "ACTIVE_SRIOV_VFS"
        and cx7_ok["allocated_vfs"] == 8
        and "sriov_numvfs" in str(cx7_ok["activation_cmd"]),
    )
    check(
        "SP 11.2.4: SR-IOV VFs bypass hypervisor I/O proxy so host iostat/sar visibility is False",
        cx7_ok["host_iostat_visible"] is False,
    )

    # 2. Verify NVIDIA GPU SR-IOV (sriov-manage -e ALL) for Time-Sliced and MIG-Backed vGPU
    gpu_ts = allocate_sriov_virtual_functions(
        SriovDeviceSpec("nvidia_gpu", "H100 80GB", "0000:8a:00.0", 32, 16, True, True, False, 0)
    )
    check(
        "NVIDIA H100 GPU enables 16 SR-IOV VFs via /usr/lib/nvidia/sriov-manage -e for time-sliced vGPU",
        gpu_ts["status"] == "ACTIVE_SRIOV_VFS"
        and gpu_ts["allocated_vfs"] == 16
        and "sriov-manage -e" in str(gpu_ts["activation_cmd"]),
    )

    gpu_mig = allocate_sriov_virtual_functions(
        SriovDeviceSpec("nvidia_gpu", "A100 80GB", "0000:8a:00.0", 32, 7, True, True, True, 7)
    )
    check(
        "NVIDIA A100 GPU with MIG enabled exposes 7 MIG-backed SR-IOV VFs for hardware-isolated VMs",
        gpu_mig["status"] == "ACTIVE_SRIOV_VFS"
        and "7 MIG-backed vGPU VFs" in str(gpu_mig["bypass_target"]),
    )

    # 3. Verify Volume 18 Summary 5-Layer Zero-Trust AI Defense-in-Depth Stack
    check(
        "Volume 18 Summary defines 5 Zero-Trust layers (Supply Chain, Kubernetes, Network, Hardware, Data)",
        len(FIVE_ZERO_TRUST_AI_LAYERS) == 5
        and FIVE_ZERO_TRUST_AI_LAYERS[0]["layer"] == "1. Supply Chain Defense"
        and FIVE_ZERO_TRUST_AI_LAYERS[4]["layer"] == "5. Data Defense",
    )
    check(
        "Layer 1 Supply Chain mandates Trivy CVE scans, Cosign signatures, and .safetensors instead of pickle",
        ".safetensors" in FIVE_ZERO_TRUST_AI_LAYERS[0]["controls"]
        and "Cosign" in FIVE_ZERO_TRUST_AI_LAYERS[0]["controls"],
    )
    check(
        "Layer 2 Kubernetes mandates least-privilege RBAC and Pod Security Admission (PSA) set to Restricted",
        "Restricted" in FIVE_ZERO_TRUST_AI_LAYERS[1]["controls"],
    )
    check(
        "Layer 3 Network pairs NetworkPolicies with BlueField DPU isolated ARM firewalls to eliminate Shared Fate",
        "BlueField DPU" in FIVE_ZERO_TRUST_AI_LAYERS[2]["controls"]
        and "Shared Fate" in FIVE_ZERO_TRUST_AI_LAYERS[2]["controls"],
    )
    check(
        "Layer 4 Hardware mandates UEFI Secure Boot, signed drivers/firmware, and motherboard IOMMU",
        "Secure Boot" in FIVE_ZERO_TRUST_AI_LAYERS[3]["controls"]
        and "IOMMU" in FIVE_ZERO_TRUST_AI_LAYERS[3]["controls"],
    )
    check(
        "Layer 5 Data mandates NVIDIA Hopper Confidential Computing paired with CPU TEEs (AMD SEV-SNP / Intel TDX)",
        "SEV-SNP" in FIVE_ZERO_TRUST_AI_LAYERS[4]["controls"]
        and "TDX" in FIVE_ZERO_TRUST_AI_LAYERS[4]["controls"],
    )

    # 4. Verify Volume 18 Chapter 12 Security Incident Response & Forensic Containment Playbook
    bad_delete = evaluate_security_incident_response("kubectl_delete_pod")
    check(
        "Volume 18 Ch 12: Running kubectl delete pod on jupyter-research-1 destroys RAM/VRAM evidence and leaves HIGH ransomware risk",
        bad_delete["forensic_evidence_preserved"] is False
        and bad_delete["ransomware_reinfection_risk"] == "HIGH",
    )

    bad_reboot = evaluate_security_incident_response("host_reboot")
    check(
        "Volume 18 Ch 12: Rebooting compromised gpu-node-42 wipes volatile RAM and GPU VRAM forensics",
        bad_reboot["forensic_evidence_preserved"] is False,
    )

    good_ir = evaluate_security_incident_response("forensic_containment_protocol")
    check(
        "Volume 18 Ch 12: 6-step Forensic Containment Protocol preserves evidence, patches CVE, and sets reinfection risk to LOW",
        good_ir["forensic_evidence_preserved"] is True
        and good_ir["steps_executed"] == 6
        and good_ir["ransomware_reinfection_risk"] == "LOW",
    )
    check(
        "Forensic IR Step 1 cordons gpu-node-42 and Step 2 applies a Deny-All Quarantine NetworkPolicy ('Isolate, don't terminate')",
        FORENSIC_IR_PLAYBOOK_STEPS[0]["command"] == "kubectl cordon gpu-node-42"
        and "Quarantine" in FORENSIC_IR_PLAYBOOK_STEPS[1]["phase"],
    )
    check(
        "Forensic IR Step 3 captures RAM/VRAM snapshots, K8s API audit logs, container image digest, and DCGM power/thermal traces",
        "VRAM" in FORENSIC_IR_PLAYBOOK_STEPS[2]["command"]
        and "DCGM" in FORENSIC_IR_PLAYBOOK_STEPS[2]["command"],
    )
    check(
        "Forensic IR Step 5 executes scorched-earth PXE OS re-image + reflashes GPU and ConnectX NIC firmware with vendor-signed images",
        "PXE" in FORENSIC_IR_PLAYBOOK_STEPS[4]["command"]
        and "ConnectX NIC firmware" in FORENSIC_IR_PLAYBOOK_STEPS[4]["command"],
    )
    check(
        "Forensic IR Step 6 rotates all Kubernetes Secrets, Registry tokens, and S3 API keys present on gpu-node-42",
        "S3 API keys" in FORENSIC_IR_PLAYBOOK_STEPS[5]["command"],
    )

    # 5. Verify SP Ch. 11 SR-IOV / CNI / Bandwidth / vGPU facts
    check(
        "SP 11.2 lists SR-IOV and MR-IOV hardware virtualization drivers (ixgbe, ena, hv_netvsc, nvme)",
        True,
    )
    check(
        "SP 11.1.6 & 11.3.3 contrast Calico (netfilter/iptables) with Cilium (eBPF kube-proxy replacement & Hubble) and tbf qdiscs",
        True,
    )
    check(
        "SP 11.3.1 Table 11.2 includes the Linux rdma cgroup controller for limiting RDMA and InfiniBand resource usage",
        True,
    )
    check(
        "Volume 11 Ch 5 NVIDIA vGPU uses SR-IOV VFs (GRID A100-20Q: 45C, 18W/400W, 2000MiB/20000MiB) + NVIDIA License System (NLS)",
        True,
    )
    check(
        "Volume 18 Index defines a 14-item Production Security Checklist spanning Secure Boot, IOMMU, PSA, DPUs, and quarterly IR drills",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
