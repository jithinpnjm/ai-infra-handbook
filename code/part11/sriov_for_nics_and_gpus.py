#!/usr/bin/env python3
"""Chapter 11.22 model: SR-IOV for NICs and GPUs, Zero-Trust Defense & Forensic IR.

Models:
1. SR-IOV PCIe Physical Function (PF) & Virtual Function (VF) allocator for
   ConnectX-7 400G NICs (sriov_totalvfs, sriov_numvfs, SriovNetworkNodePolicy)
   and NVIDIA Ampere/Hopper/Blackwell GPUs (sriov-manage -e ALL, vGPU/MIG VFs).
2. Brendan Gregg, Systems Performance 2nd Ed., Chapter 11 (SP 11):
   - SR-IOV / MR-IOV hardware virtualization (drivers: ixgbe, ena, hv_netvsc, nvme),
   - Elimination of QEMU / dom0 I/O proxy (5 steps in KVM vs 10 in Xen),
   - Host observability blind spot (SR-IOV bypasses host iostat/sar -> require PMCs/DCGM
     or guest-kernel BPF tools like biosnoop),
   - Kubernetes CNI & bandwidth controls (Calico iptables vs Cilium eBPF/Hubble,
     token bucket filter tbf qdisc for ingress-bandwidth / egress-bandwidth, rdma cgroup).
3. Volume 18 Chapter 7 SR-IOV + IOMMU (Intel VT-d / AMD-Vi) DMA security validator.
4. Volume 18 Chapter 12 & Summary:
   - 5-Layer Zero-Trust AI Defense-in-Depth Stack (Supply Chain -> Kubernetes ->
     Network/BlueField DPU -> Hardware/IOMMU -> Data/Confidential Computing),
   - 6-Step Forensic Containment & Scorched-Earth Eradication Playbook (gpu-node-42
     crypto-miner & jupyter-research-1 port 22 scan -> ransomware postmortem).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


FIVE_ZERO_TRUST_AI_LAYERS: List[Dict[str, str]] = [
    {
        "layer": "1. Supply Chain Defense",
        "controls": "Trivy CVE scanning, Cosign image signing, Admission Controller, .safetensors (never untrusted pickle)",
        "threat_mitigated": "Poisoned model weights or Trojan container images entering the cluster",
    },
    {
        "layer": "2. Kubernetes Defense",
        "controls": "Least-privilege RBAC, locked-down gpu-operator namespace, Pod Security Admission (PSA) set to Restricted",
        "threat_mitigated": "Container running as root or escalating privileges to escape into the host kernel",
    },
    {
        "layer": "3. Network Defense",
        "controls": "Default-deny NetworkPolicies + BlueField DPU isolated ARM processor firewall (eliminating Shared Fate)",
        "threat_mitigated": "Lateral movement and port 22 internal network scanning from a compromised pod or host",
    },
    {
        "layer": "4. Hardware Defense",
        "controls": "UEFI Secure Boot, signed GPU/NIC kernel drivers, signed firmware, and motherboard IOMMU (Intel VT-d / AMD-Vi)",
        "threat_mitigated": "Rogue SR-IOV VF or PCIe device executing unauthorized DMA reads against host RAM",
    },
    {
        "layer": "5. Data Defense",
        "controls": "NVIDIA Hopper Confidential Computing paired with CPU TEE (AMD SEV-SNP / Intel TDX), KMS encryption, watermarking",
        "threat_mitigated": "Malicious hypervisor admin or memory dump reading plaintext model weights/prompts in VRAM/RAM",
    },
]


FORENSIC_IR_PLAYBOOK_STEPS: List[Dict[str, str]] = [
    {
        "step": "1",
        "phase": "Cordon",
        "command": "kubectl cordon gpu-node-42",
        "purpose": "Stop Kubernetes from scheduling new pods onto the compromised crime-scene node",
    },
    {
        "step": "2",
        "phase": "Network Quarantine (Isolate, Don't Terminate)",
        "command": "kubectl apply -f quarantine-deny-all-netpol.yaml",
        "purpose": "Drop all ingress/egress except forensic management IP without deleting the pod or clearing RAM/VRAM",
    },
    {
        "step": "3",
        "phase": "Volatile Memory & Forensic Capture",
        "command": "Capture VM/host RAM + GPU VRAM snapshot, K8s API audit logs, image digest, and DCGM power/thermal traces",
        "purpose": "Preserve attacker payloads, active sockets, bash history, and entry CVE before power-down",
    },
    {
        "step": "4",
        "phase": "Root Vulnerability Patch",
        "command": "Patch exploited CVE (e.g. unpatched Jupyter/PyTorch CVE) and admission policy cluster-wide",
        "purpose": "Prevent the attacker from immediately re-exploiting the same entry vector on another pod",
    },
    {
        "step": "5",
        "phase": "Scorched-Earth Hardware Wipe & Firmware Reflash",
        "command": "PXE re-image bare-metal OS + reflash GPU and ConnectX NIC firmware with vendor-signed images",
        "purpose": "Eradicate persistent OS or silicon/NIC/GPU firmware rootkits (never merely 'clean' a breached node)",
    },
    {
        "step": "6",
        "phase": "Credential Rotation & Rejoin",
        "command": "Rotate all K8s Secrets, Registry tokens, and S3 API keys present on gpu-node-42, then uncordon",
        "purpose": "Invalidate any credentials exfiltrated from volatile memory before returning node to service",
    },
]


@dataclass(frozen=True)
class SriovDeviceSpec:
    device_type: str  # "connectx_nic" or "nvidia_gpu"
    model: str
    pf_bdf: str
    sriov_totalvfs: int
    requested_numvfs: int
    iommu_enabled: bool
    firmware_signed_and_verified: bool
    mig_mode_enabled: bool = False
    active_mig_instances: int = 0


def allocate_sriov_virtual_functions(spec: SriovDeviceSpec) -> Dict[str, object]:
    """Models SR-IOV PF -> VF slicing and security validation for NICs and GPUs."""
    if not spec.iommu_enabled:
        return {
            "status": "REJECTED_UNSAFE_NO_IOMMU",
            "allocated_vfs": 0,
            "dma_isolated": False,
            "reason": "SR-IOV without IOMMU (Intel VT-d / AMD-Vi) allows rogue VF driver to DMA-read host RAM",
        }
    if not spec.firmware_signed_and_verified:
        return {
            "status": "REJECTED_UNVERIFIED_FIRMWARE",
            "allocated_vfs": 0,
            "dma_isolated": True,
            "reason": "PF firmware signature not verified; risk of persistent NIC/GPU silicon rootkit",
        }
    if spec.requested_numvfs < 0 or spec.requested_numvfs > spec.sriov_totalvfs:
        return {
            "status": "REJECTED_EXCEEDS_TOTALVFS",
            "allocated_vfs": 0,
            "dma_isolated": True,
            "reason": f"Requested numVfs ({spec.requested_numvfs}) exceeds hardware sriov_totalvfs ({spec.sriov_totalvfs})",
        }

    vf_bdfs = [f"0000:4b:00.{i + 1}" for i in range(spec.requested_numvfs)]
    if spec.device_type == "connectx_nic":
        activation_cmd = f"echo {spec.requested_numvfs} > /sys/class/net/ens1f0np0/device/sriov_numvfs"
        bypass_target = "Bypasses QEMU / dom0 / host TCP stack for line-rate GPUDirect RDMA"
    else:
        activation_cmd = f"/usr/lib/nvidia/sriov-manage -e {spec.pf_bdf}"
        bypass_target = (
            f"Exposes {spec.active_mig_instances} MIG-backed vGPU VFs"
            if spec.mig_mode_enabled
            else f"Exposes {spec.requested_numvfs} time-sliced vGPU VFs"
        )

    return {
        "status": "ACTIVE_SRIOV_VFS",
        "device_type": spec.device_type,
        "pf_bdf": spec.pf_bdf,
        "allocated_vfs": spec.requested_numvfs,
        "sriov_totalvfs": spec.sriov_totalvfs,
        "sample_vf_bdfs": vf_bdfs[:4],
        "dma_isolated": True,
        "host_iostat_visible": False,  # SP 11.2.4: SR-IOV bypasses host OS iostat/sar
        "activation_cmd": activation_cmd,
        "bypass_target": bypass_target,
    }


def evaluate_security_incident_response(action_taken: str) -> Dict[str, object]:
    """Evaluates whether an incident responder preserved or destroyed forensic evidence."""
    if action_taken in ("kubectl_delete_pod", "host_reboot"):
        return {
            "forensic_evidence_preserved": False,
            "root_cve_identified": False,
            "ransomware_reinfection_risk": "HIGH",
            "verdict": "FAIL_EVIDENCE_DESTROYED: Deleting pod or rebooting wipes volatile RAM/VRAM and leaves entry CVE open",
        }
    return {
        "forensic_evidence_preserved": True,
        "root_cve_identified": True,
        "ransomware_reinfection_risk": "LOW",
        "steps_executed": len(FORENSIC_IR_PLAYBOOK_STEPS),
        "verdict": "PASS_FORENSIC_CONTAINMENT: Cordon -> Deny-All NetworkPolicy -> RAM/VRAM Dump -> Patch CVE -> PXE + Firmware Reflash",
    }
