#!/usr/bin/env python3
"""Self-checking lab for Chapter 9.12: Software stack and management in an AI factory."""

from __future__ import annotations

import sys

from ai_factory_software import (
    audit_distributed_training_runtime,
    calculate_zero_stage_memory_per_gpu,
    evaluate_ai_factory_slo_alerts,
    verify_cuda_driver_compatibility,
)


def run_checks() -> int:
    passed = 0
    failed = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label} -- {detail}")

    print("=== Chapter 9.12 Lab: Software Stack & Management in an AI Factory ===")

    # 1. CUDA Toolkit & Host Driver Compatibility checks (V21 Ch 6 & V10 Ch 1)
    c12_ok = verify_cuda_driver_compatibility(12, host_driver_branch=550)
    check(
        "CUDA 12.x container on host driver 550 (>=525) is compatible via minor-version compatibility",
        c12_ok["compatible"] is True and c12_ok["minimum_required_driver"] == 525,
    )

    c13_ok = verify_cuda_driver_compatibility(13, host_driver_branch=580)
    check(
        "CUDA 13.x container on host driver 580 (>=580) is compatible",
        c13_ok["compatible"] is True and c13_ok["minimum_required_driver"] == 580,
    )

    c12_old = verify_cuda_driver_compatibility(12, host_driver_branch=470)
    check(
        "CUDA 12.x container on legacy 470 driver (<525) is rejected (host_driver_too_old)",
        c12_old["compatible"] is False
        and any("host_driver_too_old" in i for i in c12_old["issues"]),
        f"got {c12_old}",
    )

    c_drift = verify_cuda_driver_compatibility(
        12, host_driver_branch=550, same_container_and_driver_across_nodes=False
    )
    check(
        "V21 Ch6: Flags mismatched container image or driver branch across cluster nodes",
        c_drift["compatible"] is False
        and "heterogeneous_node_software_stack (all nodes must run identical NGC container and driver branch)"
        in c_drift["issues"],
    )

    try:
        verify_cuda_driver_compatibility(9, 550)
        check("Rejects unsupported CUDA major version", False)
    except ValueError:
        check("Rejects unsupported CUDA major version", True)

    # 2. DDP vs DeepSpeed ZeRO Stage 1/2/3 Memory & Global Batch checks (V21 Ch 6 Part 2.2)
    z0 = calculate_zero_stage_memory_per_gpu(70.0, world_size=64, zero_stage=0, micro_batch_per_gpu=4, grad_accum_steps=8)
    check(
        "70B unsharded DDP (Stage 0) requires 1,120.0 GB per GPU; global batch (4*8*64) == 2,048",
        z0["unsharded_model_state_gb"] == 1120.0
        and z0["per_gpu_model_state_gb"] == 1120.0
        and z0["global_batch_size"] == 2048,
        f"got {z0}",
    )

    z1 = calculate_zero_stage_memory_per_gpu(70.0, world_size=64, zero_stage=1)
    check(
        "70B ZeRO-1 across 64 GPUs (shards 840 GB optimizer) requires 140 + 140 + 13.125 == 293.12 GB/GPU",
        z1["per_gpu_model_state_gb"] == 293.12,
        f"got {z1}",
    )

    z2 = calculate_zero_stage_memory_per_gpu(70.0, world_size=64, zero_stage=2)
    check(
        "70B ZeRO-2 across 64 GPUs (shards optimizer + grads) requires 140 + (980/64) == 155.31 GB/GPU",
        z2["per_gpu_model_state_gb"] == 155.31,
        f"got {z2}",
    )

    z3 = calculate_zero_stage_memory_per_gpu(70.0, world_size=64, zero_stage=3)
    check(
        "70B ZeRO-3 across 64 GPUs (shards weights + grads + optimizer) requires 1120 / 64 == 17.50 GB/GPU",
        z3["per_gpu_model_state_gb"] == 17.5,
        f"got {z3}",
    )

    try:
        calculate_zero_stage_memory_per_gpu(70.0, world_size=64, zero_stage=4)
        check("Rejects invalid zero_stage = 4", False)
    except ValueError:
        check("Rejects invalid zero_stage = 4", True)

    try:
        calculate_zero_stage_memory_per_gpu(0.0, world_size=64, zero_stage=3)
        check("Rejects non-positive params_billions", False)
    except ValueError:
        check("Rejects non-positive params_billions", True)

    # 3. Distributed Training Runtime & K8s Gang-Scheduling Audit checks (V21 Ch 6)
    good_rt = {
        "cuda_device_order": "PCI_BUS_ID",
        "cuda_launch_blocking": 0,
        "launcher": "torchrun",
        "pytorch_to_jax_via_numpy": False,
        "orchestrator": "kueue_pytorchjob",
        "has_gang_scheduler": True,
    }
    check(
        "Valid torchrun + PCI_BUS_ID + DLPack + gang-scheduled PyTorchJob passes runtime audit",
        audit_distributed_training_runtime(good_rt)["valid_runtime"] is True,
    )

    bad_order = dict(good_rt, cuda_device_order="FASTEST_FIRST")
    check(
        "V21 Ch6 Part 1.2: Flags missing CUDA_DEVICE_ORDER=PCI_BUS_ID",
        any("missing_pci_bus_id_ordering" in e for e in audit_distributed_training_runtime(bad_order)["errors"]),
    )

    bad_block = dict(good_rt, cuda_launch_blocking=1)
    check(
        "V21 Ch6 Part 1.2: Flags CUDA_LAUNCH_BLOCKING=1 in production",
        any("cuda_launch_blocking_enabled_in_prod" in e for e in audit_distributed_training_runtime(bad_block)["errors"]),
    )

    bad_launch = dict(good_rt, launcher="torch.distributed.launch")
    check(
        "V21 Ch6 Part 2.1: Flags deprecated torch.distributed.launch (use torchrun)",
        any("deprecated_launcher" in e for e in audit_distributed_training_runtime(bad_launch)["errors"]),
    )

    bad_dlpack = dict(good_rt, pytorch_to_jax_via_numpy=True)
    check(
        "V21 Ch6 Part 3.1: Flags .numpy() host-copy roundtrip between PyTorch and JAX (use DLPack)",
        any("host_copy_roundtrip_via_numpy" in e for e in audit_distributed_training_runtime(bad_dlpack)["errors"]),
    )

    bad_gang = dict(good_rt, orchestrator="plain_k8s_indexed_job", has_gang_scheduler=False)
    check(
        "V21 Ch6 Part 3.2: Flags plain K8s Indexed Job without gang scheduling",
        any("missing_gang_scheduling" in e for e in audit_distributed_training_runtime(bad_gang)["errors"]),
    )

    # 4. Volume 21 Chapter 10 SLO-Driven Alerting Rules checks
    healthy_metrics = {
        "baseline_training_tps": 60000.0,
        "current_training_tps": 58500.0,
        "max_gpu_temp_c": 71.0,
        "inference_p99_ttft_ms": 240.0,
        "gpu_failure_increase_10m": 0,
        "cluster_power_kw_avg_7d": 110.0,
        "cluster_power_kw": 112.0,
    }
    res_m_ok = evaluate_ai_factory_slo_alerts(healthy_metrics)
    check(
        "Healthy cluster telemetry fires 0 SLO alerts",
        res_m_ok["healthy"] is True and res_m_ok["firing_alert_count"] == 0,
    )

    m_low_tps = dict(healthy_metrics, current_training_tps=51000.0)  # < 0.9 * 60000 (54000)
    check(
        "V21 Ch10: Training throughput < 90% of baseline (51,000 < 54,000 tok/s) fires TrainingThroughputLow",
        "TrainingThroughputLow" in evaluate_ai_factory_slo_alerts(m_low_tps)["firing_alerts"],
    )

    m_hot = dict(healthy_metrics, max_gpu_temp_c=84.0)
    check(
        "V21 Ch10: GPU temperature > 80C fires GPUTemperatureHigh",
        "GPUTemperatureHigh" in evaluate_ai_factory_slo_alerts(m_hot)["firing_alerts"],
    )

    m_ttft = dict(healthy_metrics, inference_p99_ttft_ms=620.0)
    check(
        "V21 Ch10: Inference P99 TTFT > 500 ms fires InferenceLatencyP99High",
        "InferenceLatencyP99High" in evaluate_ai_factory_slo_alerts(m_ttft)["firing_alerts"],
    )

    m_fail = dict(healthy_metrics, gpu_failure_increase_10m=1)
    check(
        "V21 Ch10: GPU failure / Xid increase > 0 in 10m fires GPUFailureDetected",
        "GPUFailureDetected" in evaluate_ai_factory_slo_alerts(m_fail)["firing_alerts"],
    )

    m_cost = dict(healthy_metrics, cluster_power_kw=150.0)  # (150 - 110)/110 = 36.4% > 30%
    check(
        "V21 Ch10: Cluster power > 30% above 7-day average fires CostAnomalyDetected",
        "CostAnomalyDetected" in evaluate_ai_factory_slo_alerts(m_cost)["firing_alerts"],
    )

    m_multi = {
        "baseline_training_tps": 60000.0,
        "current_training_tps": 40000.0,
        "max_gpu_temp_c": 88.0,
        "inference_p99_ttft_ms": 750.0,
        "gpu_failure_increase_10m": 2,
        "cluster_power_kw_avg_7d": 100.0,
        "cluster_power_kw": 140.0,
    }
    check(
        "Simultaneous degradation across all 5 SLO metrics fires all 5 alerts",
        evaluate_ai_factory_slo_alerts(m_multi)["firing_alert_count"] == 5,
    )

    c11_ok = verify_cuda_driver_compatibility(11, host_driver_branch=470)
    check(
        "CUDA 11.x container on host driver 470 (>=450) is compatible",
        c11_ok["compatible"] is True and c11_ok["minimum_required_driver"] == 450,
    )

    gang_indexed = dict(good_rt, orchestrator="plain_k8s_indexed_job", has_gang_scheduler=True)
    check(
        "K8s Indexed Job paired with Kueue/Volcano gang scheduler passes runtime audit",
        audit_distributed_training_runtime(gang_indexed)["valid_runtime"] is True,
    )

    print(f"\nSummary: {passed} passed, {failed} failed (total {passed + failed})")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_checks())
