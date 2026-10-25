#!/usr/bin/env python3
"""Chapter 11.30 model: Multi-Node GPU Kubernetes Lab on GKE, Nebius, and EKS (K8GS).

Models:
1. Volume 25 Lab 01 Nebius L40S / Cloud GPU VM 4-Layer Provisioning & Verification:
   - Layer 1: Host NVIDIA driver (nvidia-smi),
   - Layer 2: Container GPU passthrough (docker run --gpus all, nvidia-ctk runtime configure),
   - Layer 3: Persistent block volume (/dev/vdX blkid empty check, mkfs.ext4, /data/mlops
     mounted by UUID= in /etc/fstab),
   - Layer 4: UFW firewall (ufw allow OpenSSH before ufw --force enable, verified from a
     brand-new SSH session + post-reboot persistence).
2. Volume 10 Labs 01 & 02 Multi-Node GPU Kubernetes Baseline & GPU Operator Validation:
   - gpu-node-07 (CAPACITY 8 / ALLOCATABLE 8) vs gpu-node-11 (CAPACITY 8 / ALLOCATABLE 0),
   - Host NVIDIA-SMI 550.90.07 / CUDA 12.4 on NVIDIA A100-SXM4-80GB (34C, 62W/400W,
     4MiB/81920MiB, Bus-Id 00000000:1B:00.0, UUID GPU-3a1e9f2b-6c7d-4e91-9a02-1f8b7c0d5e11),
   - containerd io.containerd.runc.v2 (pause:3.9, default_runtime_name = "nvidia"),
   - gpu-node-validation (Pending 1s -> ContainerCreating 3s -> Running 9s -> Completed 11s,
     GPU_NODE_VALIDATED) & GPU Operator (DESIRED 3 / READY 3 / AVAILABLE 3, ALLOCATABLE: 4,
     GPU_OPERATOR_VALIDATED).
3. Packt Kubernetes for Generative AI Solutions (K8GS) Chapters 3, 6 & 8:
   - Ch 3: Cloud K8s 5x growth, 99.95% SLA across 3 AZs, 3 releases/yr (12m community vs
     26m extended support), Terraform >=1.11 (aws >=5.96, helm >=2.17, kubernetes >=2.36,
     vpc 10.0.0.0/16 ~>5.21 23 resources, eks 1.32 ~>20.36 33 resources, addons ~>1.21
     2 nodes & 10 pods, my-llama NLB port 80->5000 /predict),
   - Ch 6: HPA (1..5 replicas, 70% CPU, scaleDown 180s 50%/15s, scaleUp 0s 2 pods/15s,
     ContainerResource 60%), VPA (Off/Auto/Recreate/Initial, 1000m/2Gi..2000m/4Gi),
     KEDA (amazonsqs-scaler 0..10, polling 15s, cooldown 180s, queueLength 10;
     my-llama-deployment-scaler http_requests_total > 10 and DCGM_FI_DEV_GPU_UTIL > 70),
     Karpenter (NodePool eks-gpu-np g6 spot/on-demand WhenEmptyOrUnderutilized + AL2023,
     15890m CPU, 60398040Ki RAM, nvidia.com/gpu: 1, 234 pods),
   - Ch 8: aws-load-balancer-nlb-target-type: ip + /healthz (HTTP 200 OK), Chatbot
     NetworkPolicies (TCP/80 & Qdrant TCP/6333 + CoreDNS), kube-proxy IPVS vs iptables,
     VPC CNI custom networking / IPv6, CoreDNS autoscaling + NodeLocal DNSCache,
     Placement Groups (Cluster, Partition, Spread), and EFA / GPUDirect RDMA.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


NEBIUS_FOUR_VERIFICATION_LAYERS: List[str] = [
    "1. Host NVIDIA driver (nvidia-smi)",
    "2. Container GPU passthrough (docker run --rm --gpus all ... nvidia-smi)",
    "3. Persistent block storage (blkid empty check -> mkfs.ext4 -> UUID= in /etc/fstab -> /data/mlops)",
    "4. Firewall lockdown (ufw allow OpenSSH -> ufw --force enable -> verify from new SSH session + reboot)",
]

VPA_FOUR_OPERATING_MODES: List[str] = [
    "Off",
    "Auto",
    "Recreate",
    "Initial",
]

THREE_PLACEMENT_GROUP_STRATEGIES: List[str] = [
    "Cluster",
    "Partition",
    "Spread",
]


@dataclass(frozen=True)
class NebiusGpuVmState:
    host_nvidia_smi_ok: bool
    docker_daemon_running: bool
    nvidia_ctk_configured_for_docker: bool
    block_device_already_formatted: bool
    fstab_uses_uuid: bool
    ufw_ssh_allowed_before_enable: bool
    verified_from_new_ssh_session: bool
    reboot_persistence_verified: bool


def validate_nebius_gpu_vm_provisioning(state: NebiusGpuVmState) -> Dict[str, object]:
    """Validates Volume 25 Lab 01 4-layer GPU VM provisioning on Nebius L40S / Cloud GPU."""
    if not state.host_nvidia_smi_ok:
        return {
            "ready": False,
            "failed_step": "Step 1: Host Driver",
            "error": "NVIDIA-SMI has failed because it couldn't communicate with the NVIDIA driver",
        }
    if not state.docker_daemon_running:
        return {
            "ready": False,
            "failed_step": "Step 2a: Docker Daemon Down",
            "error": "Cannot connect to the Docker daemon (run: sudo systemctl start docker)",
        }
    if not state.nvidia_ctk_configured_for_docker:
        return {
            "ready": False,
            "failed_step": "Step 2b: Container Toolkit Not Wired",
            "error": 'could not select device driver "" with capabilities: [[gpu]] (run: sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker)',
        }
    if state.block_device_already_formatted:
        return {
            "ready": False,
            "failed_step": "Step 3a: Storage Safety Gate",
            "error": "blkid returned existing filesystem on /dev/vdX; abort mkfs.ext4 to prevent data loss",
        }
    if not state.fstab_uses_uuid:
        return {
            "ready": False,
            "failed_step": "Step 3b: /etc/fstab Mount Persistence",
            "error": "Mount uses raw /dev/vdX instead of UUID=... in /etc/fstab; may fail across reboot",
        }
    if not state.ufw_ssh_allowed_before_enable or not state.verified_from_new_ssh_session:
        return {
            "ready": False,
            "failed_step": "Step 4: Firewall Lockout Guard",
            "error": "Must run 'sudo ufw allow OpenSSH' before 'ufw enable' and verify from a brand-new SSH session",
        }
    return {
        "ready": state.reboot_persistence_verified,
        "failed_step": "None (All 4 Layers + Reboot Verified)",
        "mount_point": "/data/mlops",
    }


def evaluate_keda_and_karpenter_autoscaling(
    http_req_rate_per_sec: float,
    dcgm_gpu_util_pct: float,
    sqs_queue_length: int,
    hpa_enabled: bool,
    vpa_mode: str,
) -> Dict[str, object]:
    """Models K8GS Chapter 6 KEDA ScaledObject triggers, HPA/VPA conflict, and Karpenter."""
    vpa_hpa_conflict = hpa_enabled and (vpa_mode != "Off")
    llama_scale_out = (http_req_rate_per_sec > 10.0) or (dcgm_gpu_util_pct > 70.0)
    sqs_scale_from_zero = sqs_queue_length > 0
    sqs_scale_out_above_threshold = sqs_queue_length > 10

    return {
        "vpa_hpa_conflict": vpa_hpa_conflict,
        "llama_scale_out_triggered": llama_scale_out,
        "sqs_scale_from_zero": sqs_scale_from_zero,
        "sqs_scale_out_above_threshold": sqs_scale_out_above_threshold,
        "karpenter_node_allocatable": {
            "cpu": "15890m",
            "memory": "60398040Ki",
            "nvidia.com/gpu": "1",
            "pods": "234",
        },
        "karpenter_disruption_taint": "karpenter.sh/disrupted:NoSchedule",
    }
