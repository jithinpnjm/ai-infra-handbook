#!/usr/bin/env python3
"""Chapter 11.29 model: Multi-Tenancy, Quotas, Fault Tolerance, FinOps & Health on GPU Clusters.

Models:
1. Volume 19 Chapter 1 Safe Eviction Pipeline (6 steps) & 3-Stage Canary Upgrade
   (1 Vanguard node 24h -> 1 Rack -> Global RollingUpdate >= 90% capacity online,
   contrasted with the 500-node big-bang reboot that blinded 400 nodes / 80%).
2. Volume 19 Chapters 3 & 6 + Volume 11 Chapter 9 FinOps Reaper & 3-Tier Cloud Purchasing:
   - FinOps Reaper terminates zombie pods when DCGM_FI_PROF_SM_ACTIVE < 5% for >= 4 hours,
   - Rejects $5M (16 HGX H100) purchase when 98% K8s allocation hides 12% SM_ACTIVE over 30 days,
   - Cuts $500,000/month AWS GPU bill in half via 1-Year Reserved Instances (40-50% off),
     Spot instances (70% off with 15-min async S3 checkpoints + 2-min AWS Node Termination
     Handler), and 10:1 staging time-slicing (80 devs on 1 8-GPU node).
3. Volume 19 Chapters 4, 5, 11 & Volume 11 Chapters 10-11 Universal Diagnostic Matrix:
   - 100% nvidia-smi utilization lie decoder (CLOCK_THROTTLE_REASONS 85C HW_SLOWDOWN
     1500->500 MHz at 2:00 PM causing 40% slowdown; TENSOR_ACTIVE < 10% FP32 vs > 50%;
     PCIE_RX_BYTES; MEM_COPY_UTIL; nv_inference_queue_duration_us; PYTORCH_CUDA_ALLOC_CONF),
   - 3-Layer AI Network Triage (Node 84 NCCL error 12 via hw_counters/packet_seq_err,
     perfquery SymbolErrorCounter, PFC rx_prio_pause storms, OpenSM flapping ports).
4. Volume 19 Chapters 7, 8, 9, 10, 12 Multi-Tenancy (Compute MIG/Taints, Network Policy/SR-IOV,
   Storage QoS/chroot), IRSA Workload Identity (medical-training-sa), Thanos 4-tier observability
   + 5m Recording Rules, Disaster Recovery (10 PB over 10 Gbps = ~92 days, S3 Object Lock WORM
   30 days Compliance mode, 1-hour CoW storage snapshots), and XID 48 Zero-Touch Runbook.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


SIX_SAFE_EVICTION_STEPS: List[str] = [
    "1. Cordon (kubectl cordon node-42)",
    "2. Drain (kubectl drain node-42 --ignore-daemonsets --delete-emptydir-data + checkpoint)",
    "3. Verify Idle (nvidia-smi shows 0 running processes)",
    "4. Execute Upgrade (Helm driver update or OS kernel reboot)",
    "5. Validation (Automated DCGM diagnostic burn-in test)",
    "6. Uncordon (Return node to active scheduling pool)",
]

THREE_CANARY_ROLLOUT_STAGES: List[str] = [
    "1. Vanguard Node (1 isolated node soaked for 24 hours under low-priority batch load)",
    "2. Rack-Level Rollout (1 full leaf-switch InfiniBand fault domain)",
    "3. Global Rollout (Kubernetes RollingUpdates keeping >= 90% cluster capacity online)",
]

FOUR_THANOS_TIERS: List[str] = [
    "1. Scraping Tier (Lightweight node/rack Prometheus Agents / OTel Collectors)",
    "2. Aggregation Tier (Horizontally scalable Thanos Receive / Cortex / VictoriaMetrics)",
    "3. Storage Tier (Compressed blocks in S3 Object Storage for long-term retention)",
    "4. Query Tier (Thanos Querier + 5-minute Prometheus Recording Rules e.g. cluster:gpu:utilization_avg_5m)",
]


@dataclass(frozen=True)
class GpuPerformanceSymptom:
    nvidia_smi_util_pct: int
    clock_throttle_hw_slowdown: bool
    gpu_temp_c: int
    sm_clock_mhz: int
    tensor_active_pct: float
    pcie_rx_saturated: bool
    mem_copy_util_pct: int
    triton_queue_duration_spiking: bool
    nccl_error_12_retry_exceeded: bool
    packet_seq_err_node: str


def diagnose_ai_sre_bottleneck(sym: GpuPerformanceSymptom) -> Dict[str, str]:
    """Implements the Volume 19 Chapters 4, 5, and 11 Universal Diagnostic Matrix."""
    if sym.nccl_error_12_retry_exceeded:
        return {
            "category": "Layer 1/2 RDMA Fabric Degradation (NCCL Error 12)",
            "root_cause": (
                f"Silent RDMA packet drops / sequence errors (packet_seq_err, local_ack_timeout_err) "
                f"on {sym.packet_seq_err_node} optical transceiver poisoning the AllReduce ring"
            ),
            "remediation": f"Cordon {sym.packet_seq_err_node} and replace degraded optical transceiver/fiber",
        }
    if sym.clock_throttle_hw_slowdown or sym.gpu_temp_c >= 85:
        return {
            "category": "Hardware Thermal / Power Throttling (HW_SLOWDOWN)",
            "root_cause": (
                f"GPU hit {sym.gpu_temp_c}C (>= 85C) and downclocked to {sym.sm_clock_mhz} MHz "
                f"while nvidia-smi still reports {sym.nvidia_smi_util_pct}% utilization"
            ),
            "remediation": "Escalate to Data Center Facilities (HVAC / server fan failure) and monitor DCGM_FI_DEV_CLOCK_THROTTLE_REASONS",
        }
    if sym.triton_queue_duration_spiking:
        return {
            "category": "Inference Server Software Queue Saturation",
            "root_cause": "nv_inference_queue_duration_us is spiking: requests wait in Triton software queue for an execution thread",
            "remediation": "Increase Instance Group count in Triton config.pbtxt to allow more concurrent execution streams",
        }
    if sym.nvidia_smi_util_pct >= 80 and sym.mem_copy_util_pct >= 95:
        return {
            "category": "GPU Memory Bandwidth Bound (Roofline Low Arithmetic Intensity)",
            "root_cause": "DCGM_FI_DEV_MEM_COPY_UTIL is pegged near 100% during LLM token decoding (TPOT)",
            "remediation": "Deploy TensorRT-LLM with PagedAttention, kernel fusion / FlashAttention, and INT8/FP8 quantization",
        }
    if sym.nvidia_smi_util_pct == 100 and sym.pcie_rx_saturated:
        return {
            "category": "Host-to-Device PCIe Data Transfer Bottleneck",
            "root_cause": "DCGM_FI_PROF_PCIE_RX_BYTES is saturated copying unpinned batches across PCIe",
            "remediation": "Enable pin_memory=True, increase num_workers / NVIDIA DALI, or use GPUDirect Storage (GDS)",
        }
    if sym.nvidia_smi_util_pct == 100 and sym.tensor_active_pct < 10.0:
        return {
            "category": "Software Precision / Tiny-Kernel Spin (The Utilization Lie)",
            "root_cause": (
                f"nvidia-smi shows 100%, but DCGM_FI_PROF_PIPE_TENSOR_ACTIVE is {sym.tensor_active_pct}% (< 10%): "
                f"running unoptimized FP32 math or tiny un-fused kernels"
            ),
            "remediation": "Enable Automatic Mixed Precision (AMP / BF16 / FP16), larger batch sizes, and operator fusion",
        }
    return {
        "category": "Healthy Compute Execution",
        "root_cause": "Tensor cores active (> 50%), clocks unthrottled, and fabric counters clean",
        "remediation": "No remediation required",
    }


def evaluate_finops_reaper_and_cloud_plan(
    k8s_allocated_pct: float = 98.0,
    dcgm_sm_active_30d_avg_pct: float = 12.0,
    pod_sm_active_pct: float = 0.0,
    pod_idle_hours: float = 4.0,
    dataset_size_pb: float = 10.0,
    backup_link_gbps: float = 10.0,
) -> Dict[str, object]:
    """Models Volume 19 Chapters 3, 6 & 10 FinOps Reaper, cloud savings, and 10 PB transfer time."""
    reap_zombie_pod = (pod_sm_active_pct < 5.0) and (pod_idle_hours >= 4.0)
    reject_5m_hardware_purchase = (k8s_allocated_pct >= 90.0) and (dcgm_sm_active_30d_avg_pct < 20.0)

    # 10 PB = 10 * 10^15 bytes = 80 * 10^15 bits; at 10 * 10^9 bits/s = 8,000,000 seconds / 86,400 s/day ≈ 92.59 days (~92 days)
    transfer_seconds = (dataset_size_pb * 8_000_000.0) / backup_link_gbps
    transfer_days = int(transfer_seconds // 86400)

    return {
        "reap_zombie_pod": reap_zombie_pod,
        "reject_5m_hardware_purchase": reject_5m_hardware_purchase,
        "mig_1g_10gb_slices_per_h100": 7,
        "staging_devs_on_one_8gpu_node_10x_timeslice": 8 * 10,
        "ri_1yr_discount_pct_range": (40, 60),
        "spot_discount_pct": 70,
        "spot_checkpoint_interval_minutes": 15,
        "aws_spot_warning_minutes": 2,
        "ten_pb_over_10gbps_days": transfer_days,
        "worm_object_lock_retention_days": 30,
        "hourly_cow_snapshot_max_data_loss_minutes": 60,
    }
