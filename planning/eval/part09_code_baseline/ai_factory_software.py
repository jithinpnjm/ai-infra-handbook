#!/usr/bin/env python3
"""Part 9, Chapter 9.12: Software stack and management in an AI factory model.

Models CUDA toolkit-to-driver minor-version compatibility, distributed training
rank/batch/ZeRO-stage memory math, Kubernetes gang-scheduling & runtime checks,
and the Volume 21 Chapter 10 Prometheus/DCGM SLO alert evaluator.

Sources:
- nvidia-devops Volume 21 Chapters 6 and 10
- nvidia-devops-legacy-v10 Chapter 1 (CUDA minor-version compatibility ranges)
- NVIDIA DGX SuperPOD Reference Architecture Featuring DGX GB300 Systems (pp. 13-14, 32-34)
- NVIDIA Base Command Manager 11 Administrator Manual (Sections 3.16, 6.5, 9, 14.5)
"""

from __future__ import annotations

from typing import Dict, List


def verify_cuda_driver_compatibility(
    container_cuda_major: int,
    host_driver_branch: int,
    same_container_and_driver_across_nodes: bool = True,
) -> Dict[str, object]:
    """Check whether a host NVIDIA driver branch supports a container CUDA major version.

    Sources:
    - nvidia-devops Volume 21 Chapter 6 ("1.1 CUDA Version & Driver Alignment")
    - nvidia-devops-legacy-v10 Chapter 1 (line 914: minor-version compatibility ranges:
      CUDA 11.x needs driver >= 450; CUDA 12.x needs driver >= 525; CUDA 13.x needs driver >= 580).
    """
    min_driver_by_major = {
        11: 450,
        12: 525,
        13: 580,
    }
    if container_cuda_major not in min_driver_by_major:
        raise ValueError(f"Unsupported CUDA major version: {container_cuda_major}")

    min_req = min_driver_by_major[container_cuda_major]
    driver_major_family = 13 if host_driver_branch >= 580 else (12 if host_driver_branch >= 525 else (11 if host_driver_branch >= 450 else 0))

    issues: List[str] = []
    if host_driver_branch < min_req:
        issues.append(
            f"host_driver_too_old ({host_driver_branch} < {min_req} required for CUDA {container_cuda_major}.x)"
        )
    elif driver_major_family != container_cuda_major and host_driver_branch < min_req:
        issues.append("cross_major_cuda_driver_mismatch")

    if not same_container_and_driver_across_nodes:
        issues.append("heterogeneous_node_software_stack (all nodes must run identical NGC container and driver branch)")

    return {
        "compatible": len(issues) == 0,
        "minimum_required_driver": min_req,
        "uses_minor_version_compat": driver_major_family == container_cuda_major,
        "issues": issues,
    }


def calculate_zero_stage_memory_per_gpu(
    params_billions: float,
    world_size: int,
    zero_stage: int,
    micro_batch_per_gpu: int = 4,
    grad_accum_steps: int = 8,
) -> Dict[str, float]:
    """Calculate global batch size and per-GPU model-state VRAM under DDP vs ZeRO-1/2/3.

    Sources:
    - nvidia-devops Volume 21 Chapter 4 (16 bytes/param active training state:
      2 B BF16 weights + 2 B BF16 gradients + 12 B FP32 master weights & Adam m/v states).
    - nvidia-devops Volume 21 Chapter 6 ("2.2 DeepSpeed Integration"):
      global_batch_size = train_micro_batch_size_per_gpu * gradient_accumulation_steps * world_size.
      ZeRO Stage 3 shards parameters, gradients, and optimizer states across data-parallel ranks.
    My inference: Combines the 2 B + 2 B + 12 B = 16 B/param breakdown from V21 Ch 4 with
    ZeRO Stage 0 (DDP: 16 B/param), Stage 1 (shards 12 B optimizer across W), Stage 2
    (shards 12 B optimizer + 2 B gradients across W), and Stage 3 (shards all 16 B across W).
    """
    if params_billions <= 0 or world_size <= 0 or micro_batch_per_gpu <= 0 or grad_accum_steps <= 0:
        raise ValueError("All model and batch parameters must be positive.")
    if zero_stage not in (0, 1, 2, 3):
        raise ValueError(f"zero_stage must be 0, 1, 2, or 3; got {zero_stage}")

    weights_gb = params_billions * 2.0
    grads_gb = params_billions * 2.0
    optim_gb = params_billions * 12.0

    if zero_stage == 0:
        per_gpu_gb = weights_gb + grads_gb + optim_gb
    elif zero_stage == 1:
        per_gpu_gb = weights_gb + grads_gb + (optim_gb / world_size)
    elif zero_stage == 2:
        per_gpu_gb = weights_gb + ((grads_gb + optim_gb) / world_size)
    else:
        per_gpu_gb = (weights_gb + grads_gb + optim_gb) / world_size

    global_batch = micro_batch_per_gpu * grad_accum_steps * world_size
    return {
        "zero_stage": zero_stage,
        "world_size": world_size,
        "global_batch_size": global_batch,
        "unsharded_model_state_gb": round(weights_gb + grads_gb + optim_gb, 2),
        "per_gpu_model_state_gb": round(per_gpu_gb, 2),
    }


def audit_distributed_training_runtime(config: Dict[str, object]) -> Dict[str, object]:
    """Audit PyTorch/CUDA/Kubernetes distributed training runtime configuration.

    Sources:
    - nvidia-devops Volume 21 Chapter 6 (Parts 1.2, 2.1, 3.1, 3.2)
    """
    errors: List[str] = []

    if str(config.get("cuda_device_order", "")) != "PCI_BUS_ID":
        errors.append("missing_pci_bus_id_ordering (set CUDA_DEVICE_ORDER=PCI_BUS_ID)")

    if int(config.get("cuda_launch_blocking", 0)) != 0:
        errors.append("cuda_launch_blocking_enabled_in_prod (forces synchronous launches; must be 0)")

    if str(config.get("launcher", "")) == "torch.distributed.launch":
        errors.append("deprecated_launcher (use torchrun instead of deprecated torch.distributed.launch)")

    if bool(config.get("pytorch_to_jax_via_numpy", False)):
        errors.append("host_copy_roundtrip_via_numpy (use DLPack to_dlpack/from_dlpack for zero-copy GPU interop)")

    if str(config.get("orchestrator", "")) == "plain_k8s_indexed_job" and not bool(
        config.get("has_gang_scheduler", False)
    ):
        errors.append(
            "missing_gang_scheduling (plain K8s Job hangs until rendezvous timeout on partial placement; use Kueue/Volcano/PyTorchJob/Run:ai)"
        )

    return {
        "valid_runtime": len(errors) == 0,
        "errors": errors,
    }


def evaluate_ai_factory_slo_alerts(metrics: Dict[str, float]) -> Dict[str, object]:
    """Evaluate the 5 SLO-driven Prometheus alerting rules from Volume 21 Chapter 10.

    Source: nvidia-devops Volume 21 Chapter 10 ("2.1 SLO-Driven Alerts", lines 122-168):
    1. TrainingThroughputLow: training_tps < 0.90 * baseline_tps (for 5m)
    2. GPUTemperatureHigh: max_gpu_temp_c > 80.0 (for 1m)
    3. InferenceLatencyP99High: inference_p99_ttft_ms > 500.0 (for 3m)
    4. GPUFailureDetected: gpu_failure_increase_10m > 0
    5. CostAnomalyDetected: (cluster_power_kw - avg_7d_power_kw) / avg_7d_power_kw > 0.30 (for 10m)
    """
    firing_alerts: List[str] = []

    baseline_tps = float(metrics.get("baseline_training_tps", 60000.0))
    current_tps = float(metrics.get("current_training_tps", baseline_tps))
    if current_tps < 0.90 * baseline_tps:
        firing_alerts.append("TrainingThroughputLow")

    if float(metrics.get("max_gpu_temp_c", 65.0)) > 80.0:
        firing_alerts.append("GPUTemperatureHigh")

    if float(metrics.get("inference_p99_ttft_ms", 200.0)) > 500.0:
        firing_alerts.append("InferenceLatencyP99High")

    if int(metrics.get("gpu_failure_increase_10m", 0)) > 0:
        firing_alerts.append("GPUFailureDetected")

    avg_7d_kw = float(metrics.get("cluster_power_kw_avg_7d", 100.0))
    curr_kw = float(metrics.get("cluster_power_kw", avg_7d_kw))
    if avg_7d_kw > 0 and ((curr_kw - avg_7d_kw) / avg_7d_kw) > 0.30:
        firing_alerts.append("CostAnomalyDetected")

    return {
        "healthy": len(firing_alerts) == 0,
        "firing_alert_count": len(firing_alerts),
        "firing_alerts": firing_alerts,
    }
