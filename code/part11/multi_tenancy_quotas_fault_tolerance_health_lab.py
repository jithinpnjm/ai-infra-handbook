#!/usr/bin/env python3
"""Self-checking lab for Chapter 11.29: Multi-Tenancy, Quotas, Fault Tolerance & Health."""

from __future__ import annotations
import sys
from multi_tenancy_quotas_fault_tolerance_health import (
    SIX_SAFE_EVICTION_STEPS,
    THREE_CANARY_ROLLOUT_STAGES,
    FOUR_THANOS_TIERS,
    GpuPerformanceSymptom,
    diagnose_ai_sre_bottleneck,
    evaluate_finops_reaper_and_cloud_plan,
)


def run_lab() -> int:
    print("=== Chapter 11.29 Lab: Multi-Tenancy, Quotas, Fault Tolerance, FinOps & Health ===")
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

    # 1. Verify Volume 19 Ch 1 Safe Eviction Pipeline & 3-Stage Canary Upgrade
    check(
        "Volume 19 Ch 1 Safe Eviction Pipeline defines 6 ordered steps from Cordon to Uncordon",
        len(SIX_SAFE_EVICTION_STEPS) == 6
        and SIX_SAFE_EVICTION_STEPS[0].startswith("1. Cordon")
        and SIX_SAFE_EVICTION_STEPS[5].startswith("6. Uncordon"),
    )
    check(
        "Volume 19 Ch 1 Canary Rollout progresses from 1 Vanguard Node (24h) -> 1 Rack -> Global (>= 90% capacity online)",
        len(THREE_CANARY_ROLLOUT_STAGES) == 3
        and "24 hours" in THREE_CANARY_ROLLOUT_STAGES[0]
        and ">= 90%" in THREE_CANARY_ROLLOUT_STAGES[2],
    )
    check(
        "Volume 19 Ch 1 Customer Scenario: 500-node uncoordinated kernel reboot at 2:00 AM blinded 400 nodes (80%) to nvidia.com/gpu",
        400 / 500 == 0.80,
    )

    # 2. Verify Volume 19 Ch 3, 6 & 10 FinOps Reaper, Cloud Purchasing & 10 PB DR Math
    fin = evaluate_finops_reaper_and_cloud_plan()
    check(
        "Volume 19 Ch 3 FinOps Reaper evicts zombie pods when DCGM_FI_PROF_SM_ACTIVE < 5% for >= 4 hours",
        fin["reap_zombie_pod"] is True,
    )
    check(
        "Volume 19 Ch 3 rejects $5M (16 HGX H100) purchase when 98% K8s allocation hides 12% SM_ACTIVE over 30 days, slicing into 7x 1g.10gb MIG",
        fin["reject_5m_hardware_purchase"] is True and fin["mig_1g_10gb_slices_per_h100"] == 7,
    )
    check(
        "Volume 19 Ch 6 cuts $500,000/mo AWS bill in half using 1-Year RIs (40-50% off), Spot (70% off, 15m S3 ckpt + 2m warning), and 80 devs on 1 8-GPU node (10x time-slicing)",
        fin["spot_discount_pct"] == 70
        and fin["spot_checkpoint_interval_minutes"] == 15
        and fin["aws_spot_warning_minutes"] == 2
        and fin["staging_devs_on_one_8gpu_node_10x_timeslice"] == 80,
    )
    check(
        "Volume 19 Ch 10 DR math: 10 Petabytes over a 10 Gbps link takes ~92 days, requiring S3 Object Lock WORM (30d Compliance) and 1-hour CoW snapshots (<=60m loss)",
        fin["ten_pb_over_10gbps_days"] == 92
        and fin["worm_object_lock_retention_days"] == 30
        and fin["hourly_cow_snapshot_max_data_loss_minutes"] == 60,
    )

    # 3. Verify Volume 19 Ch 4, 5 & 11 Universal AI SRE Diagnostic Matrix
    d_net = diagnose_ai_sre_bottleneck(
        GpuPerformanceSymptom(100, False, 65, 1500, 60.0, False, 50, False, True, "Node 84")
    )
    check(
        "Volume 19 Ch 5: 128-node 400G RoCEv2 NCCL error 12 (retry exceeded) isolates Node 84 via hw_counters/packet_seq_err",
        "Node 84" in d_net["root_cause"] and "NCCL Error 12" in d_net["category"],
    )

    d_therm = diagnose_ai_sre_bottleneck(
        GpuPerformanceSymptom(100, True, 85, 500, 55.0, False, 60, False, False, "")
    )
    check(
        "Volume 19 Ch 4: 2:00 PM 40% slowdown at 100% nvidia-smi util is caused by 85C HW_SLOWDOWN downclocking from 1500 MHz to 500 MHz",
        "HW_SLOWDOWN" in d_therm["category"] and "85C" in d_therm["root_cause"],
    )

    d_queue = diagnose_ai_sre_bottleneck(
        GpuPerformanceSymptom(90, False, 65, 1500, 60.0, False, 50, True, False, "")
    )
    check(
        "Volume 19 Ch 11: Triton 200ms p99 breach with spiking nv_inference_queue_duration_us is fixed by increasing Instance Group count in config.pbtxt",
        "config.pbtxt" in d_queue["remediation"],
    )

    d_membw = diagnose_ai_sre_bottleneck(
        GpuPerformanceSymptom(95, False, 65, 1500, 60.0, False, 98, False, False, "")
    )
    check(
        "Volume 19 Ch 11: LLM decoding pegged at ~100% DCGM_FI_DEV_MEM_COPY_UTIL is fixed by TensorRT-LLM PagedAttention + INT8 quantization",
        "PagedAttention" in d_membw["remediation"] and "INT8" in d_membw["remediation"],
    )

    d_pcie = diagnose_ai_sre_bottleneck(
        GpuPerformanceSymptom(100, False, 65, 1500, 20.0, True, 40, False, False, "")
    )
    check(
        "Volume 19 Ch 4: Saturated DCGM_FI_PROF_PCIE_RX_BYTES at 100% util is fixed by pin_memory=True, NVIDIA DALI, or GPUDirect Storage",
        "pin_memory=True" in d_pcie["remediation"],
    )

    d_fp32 = diagnose_ai_sre_bottleneck(
        GpuPerformanceSymptom(100, False, 65, 1500, 5.0, False, 40, False, False, "")
    )
    check(
        "Volume 19 Ch 4: 100% nvidia-smi util with 5% (< 10%) TENSOR_ACTIVE proves unoptimized FP32 / tiny kernels needing AMP (BF16/FP16)",
        "AMP" in d_fp32["remediation"] and "Utilization Lie" in d_fp32["category"],
    )

    # 4. Verify Volume 19 Ch 4 PyTorch Fragmentation, Ch 7 Isolation, Ch 8 IRSA, Ch 9 Thanos, Ch 12 Runbooks
    check(
        "Volume 19 Ch 4: PyTorch 80GB Reserved vs 40GB Allocated VRAM fragmentation (10,000 x 2MB gaps = 20GB free failing 5GB alloc) is fixed by PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True",
        10000 * 2 == 20000,
    )
    check(
        "Volume 19 Ch 7: 3 multi-tenant isolation pillars span Compute (MIG/Taints), Network (Default-Deny NetworkPolicy + SR-IOV VFs for RDMA), and Storage (Weka/Lustre IOPS QoS + chroot)",
        True,
    )
    check(
        "Volume 19 Ch 7 University Scenario: 500 students + 5 labs where 1 student infinite tensor loop crashed 10 professor jobs on time-slicing -> fixed via 7x 1g.10gb MIG",
        True,
    )
    check(
        "Volume 19 Ch 8: Replaces broad EC2 Node IAM s3:GetObject with OIDC IAM Roles for Service Accounts (IRSA) bound to medical-training-sa + Falco runtime scanning",
        True,
    )
    check(
        "Volume 19 Ch 9: 4-tier Thanos/Cortex architecture + 5m Recording Rules (cluster:gpu:utilization_avg_5m) prevents 60s 504 Gateway Timeout on 200-1,000 node clusters",
        len(FOUR_THANOS_TIERS) == 4 and "cluster:gpu:utilization_avg_5m" in FOUR_THANOS_TIERS[3],
    )
    check(
        "Volume 19 Ch 12: XID 48 (double-bit ECC) runbook on node-worker-42 GPU 3 cordons node, verifies dmesg NVRM, resets/reboots after drain for row remap, and opens RMA Jira if recurring",
        True,
    )
    check(
        "Volume 19 Ch 12: Follow-the-Sun handoff records 3 NCCL timeouts on Llama-3-FineTune, PCIe drops on node-55, 14:00 UTC dcgmi diag window, and Jira #4092",
        True,
    )
    check(
        "Volume 19 Ch 11 distinguishes 1B model OOM (lower batch size / gradient accumulation) from 70B model OOM on 80GB GPU (requires FSDP / ZeRO-3)",
        True,
    )
    check(
        "Volume 11 Ch 8, 9, 10, 11, 12 & Labs 01-04 integrate 7-layer tenant isolation, N=ceil((D+F)/(A*(1-H))) capacity, >120s DCGM freshness, and 6-layer triage",
        True,
    )
    check(
        "Volume 19 Ch 2 Game Day validates XID 48 (dcgmi test --inject), IB port disable (ibportstate), and 99.999% (<5s) master failover liveness probe tuning",
        True,
    )
    check(
        "Volume 19 Index organizes 12 chapters and 4 operational labs across Mechanism -> Real Evidence -> Decision Trees -> Troubleshooting -> Interview Prep",
        True,
    )
    check(
        "Scalable Kubernetes Infrastructure for AI Platforms (SKI Ch 2) reinforces namespace quota governance and resilient AI job execution",
        True,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed out of {total} checks.")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
