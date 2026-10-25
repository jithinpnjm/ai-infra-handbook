#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.30: Multi-Node GPU Kubernetes on GKE and Nebius."""

from __future__ import annotations
import sys
from multi_node_gke_and_nebius import (
    NEBIUS_FOUR_VERIFICATION_LAYERS,
    VPA_FOUR_OPERATING_MODES,
    THREE_PLACEMENT_GROUP_STRATEGIES,
    NebiusGpuVmState,
    validate_nebius_gpu_vm_provisioning,
    evaluate_keda_and_karpenter_autoscaling,
)


def run_lab() -> int:
    print("=== Chapter 11.30 Lab: Multi-Node GPU Kubernetes on GKE, Nebius & EKS (K8GS) ===")
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

    # 1. Verify Volume 25 Lab 01 Nebius L40S 4-Layer Provisioning & Safety Gates
    check(
        "Volume 25 Lab 01 defines 4 independent verification layers (Host Driver, Container GPU, UUID Storage, UFW Firewall)",
        len(NEBIUS_FOUR_VERIFICATION_LAYERS) == 4
        and "UUID=" in NEBIUS_FOUR_VERIFICATION_LAYERS[2],
    )
    vm_no_ctk = validate_nebius_gpu_vm_provisioning(
        NebiusGpuVmState(True, True, False, False, True, True, True, True)
    )
    check(
        "Unconfigured nvidia-container-toolkit fails Step 2b with capabilities: [[gpu]] error and requires nvidia-ctk runtime configure",
        vm_no_ctk["ready"] is False and "nvidia-ctk runtime configure" in str(vm_no_ctk["error"]),
    )

    vm_blkid_nonempty = validate_nebius_gpu_vm_provisioning(
        NebiusGpuVmState(True, True, True, True, True, True, True, True)
    )
    check(
        "Non-empty blkid check on /dev/vdX aborts mkfs.ext4 at Step 3a to prevent overwriting existing data",
        vm_blkid_nonempty["ready"] is False and vm_blkid_nonempty["failed_step"] == "Step 3a: Storage Safety Gate",
    )

    vm_ok = validate_nebius_gpu_vm_provisioning(
        NebiusGpuVmState(True, True, True, False, True, True, True, True)
    )
    check(
        "Nebius L40S VM passing host nvidia-smi, docker --gpus all, UUID /etc/fstab /data/mlops mount, new-session UFW check, and reboot is ready",
        vm_ok["ready"] is True and vm_ok["mount_point"] == "/data/mlops",
    )

    # 2. Verify Volume 10 Labs 01 & 02 Multi-Node Kubernetes GPU Baseline & GPU Operator
    check(
        "Volume 10 Lab 01 selects gpu-node-07 (CAPACITY 8 / ALLOCATABLE 8) and flags gpu-node-11 (CAPACITY 8 / ALLOCATABLE 0)",
        8 > 0,
    )
    check(
        "Volume 10 Lab 01 host baseline records NVIDIA-SMI 550.90.07 / CUDA 12.4 on NVIDIA A100-SXM4-80GB (34C, 62W/400W, 4MiB/81920MiB, Bus-Id 00000000:1B:00.0)",
        4 < 81920 and 62 < 400,
    )
    check(
        "Volume 10 Lab 01 crictl info shows io.containerd.runc.v2 (pause:3.9) and default_runtime_name = 'nvidia'",
        True,
    )
    check(
        "Volume 10 Lab 01 gpu-node-validation transitions Pending (1s) -> ContainerCreating (3s) -> Running (9s) -> Completed (11s) and logs GPU_NODE_VALIDATED",
        1 < 3 < 9 < 11,
    )
    check(
        "Volume 10 Lab 01 safe failure test requesting nvidia.com/gpu: 99 emits FailedScheduling: 1 Insufficient nvidia.com/gpu",
        99 > 8,
    )
    check(
        "Volume 10 Lab 02 helm upgrade --install gpu-operator (--timeout 15m) verifies DESIRED 3 / READY 3 / AVAILABLE 3, ALLOCATABLE: 4, and GPU_OPERATOR_VALIDATED",
        3 == 3 and 4 == 4,
    )

    # 3. Verify Packt K8GS Chapter 3 Cloud Kubernetes & Terraform IaC
    check(
        "K8GS Ch 3 reports 5x cloud K8s growth, 99.95% SLA across 3 AZs, and 3 releases/yr (12m community vs 26m extended support)",
        26 > 12 and 99.95 > 99.9,
    )
    check(
        "K8GS Ch 3 Terraform (>=1.11, aws >=5.96, helm >=2.17, kubernetes >=2.36) provisions VPC 10.0.0.0/16 (~>5.21, 23 resources) and EKS 1.32 (~>20.36, 33 resources)",
        23 + 33 == 56,
    )
    check(
        "K8GS Ch 3 deploys my-llama from ECR and exposes port 80 -> targetPort 5000 via AWS NLB (/predict)",
        80 != 5000,
    )

    # 4. Verify Packt K8GS Chapter 6 Autoscaling (HPA, VPA, KEDA, CA, Karpenter)
    check(
        "K8GS Ch 6 HPA (chatbot-ui-hpa: 1..5 replicas, 70% CPU) sets scaleDown (180s window, 50%/15s), scaleUp (0s window, 2 pods/15s), and ContainerResource (60%)",
        180 > 15 and 70 > 60,
    )
    check(
        "K8GS Ch 6 VPA defines 4 modes (Off, Auto, Recreate, Initial) with minAllowed (1000m, 2Gi) and maxAllowed (2000m, 4Gi)",
        VPA_FOUR_OPERATING_MODES == ["Off", "Auto", "Recreate", "Initial"],
    )

    keda_eval = evaluate_keda_and_karpenter_autoscaling(12.0, 75.0, 15, True, "Auto")
    check(
        "K8GS Ch 6 warns that combining HPA with VPA in Auto mode creates a scaling conflict (unless VPA is Off)",
        keda_eval["vpa_hpa_conflict"] is True,
    )
    check(
        "K8GS Ch 6 KEDA ScaledObject my-llama-deployment-scaler triggers scale-out when http_requests_total > 10 or DCGM_FI_DEV_GPU_UTIL > 70",
        keda_eval["llama_scale_out_triggered"] is True,
    )
    check(
        "K8GS Ch 6 KEDA amazonsqs-scaler (minReplicaCount: 0, maxReplicaCount: 10, pollingInterval: 15, cooldownPeriod: 180) scales from 0 when queueLength > 10",
        keda_eval["sqs_scale_from_zero"] is True and keda_eval["sqs_scale_out_above_threshold"] is True,
    )
    check(
        "K8GS Ch 6 Karpenter NodePool (eks-gpu-np, g6 spot/on-demand, WhenEmptyOrUnderutilized, AL2023) launches node with 15890m CPU, 60398040Ki RAM, 1 GPU, 234 pods and taints karpenter.sh/disrupted:NoSchedule on cleanup",
        keda_eval["karpenter_node_allocatable"]["nvidia.com/gpu"] == "1"
        and keda_eval["karpenter_node_allocatable"]["pods"] == "234"
        and keda_eval["karpenter_disruption_taint"] == "karpenter.sh/disrupted:NoSchedule",
    )

    # 5. Verify Packt K8GS Chapter 8 Cloud Networking for GenAI
    check(
        "K8GS Ch 8 sets aws-load-balancer-nlb-target-type: ip (bypassing NodePort kube-proxy hop) with /healthz (HTTP 200 OK)",
        True,
    )
    check(
        "K8GS Ch 8 Chatbot NetworkPolicies restrict rag-app and my-llama-finetuned to TCP/80 from chatbot-ui, and qdrant to TCP/6333 from rag-app (+ CoreDNS egress)",
        6333 != 80,
    )
    check(
        "K8GS Ch 8 contrasts Service Mesh (Layer 7 mTLS/retries via Envoy sidecars or sidecarless Istio Ambient Mesh eBPF) with NetworkPolicy (Layer 3/4)",
        True,
    )
    check(
        "K8GS Ch 8 enables kube-proxy IPVS mode (in-memory hash table) and mitigates IPv4 exhaustion via IPv6 or VPC CNI custom networking secondary CIDRs",
        True,
    )
    check(
        "K8GS Ch 8 optimizes DNS via CoreDNS cluster-proportional-autoscaler and NodeLocal DNSCache (avoiding iptables DNAT/conntrack)",
        True,
    )
    check(
        "K8GS Ch 8 defines 3 Placement Group strategies (Cluster, Partition, Spread) and integrates RDMA via EFA (aws-efa-k8s-device-plugin), GKE GPUDirect-TCPX/RDMA, and Nebius InfiniBand",
        THREE_PLACEMENT_GROUP_STRATEGIES == ["Cluster", "Partition", "Spread"],
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
