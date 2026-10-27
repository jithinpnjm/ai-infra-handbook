#!/usr/bin/env python3
"""Deterministic models and runtime calculators for Chapter 15.15:
Autoscaling inference: HPA, KEDA and scale-to-zero.

Covers:
1. Why CPU, memory, and `DCGM_FI_DEV_GPU_UTIL` fail as LLM autoscaling signals under
   continuous batching and static PagedAttention VRAM pre-allocation (`VL5` Ch. 3;
   `GAK` Ch. 4, 5; `LLP` Ch. 6; `V12` Ch. 1, 8).
2. Custom Prometheus scaling signals: `vllm:num_requests_waiting`,
   `vllm:gpu_cache_usage_perc` (`0-80%` Safe, `80-90%` Warning, `> 90%` Emergency),
   `TTFT` / `ITL` (`TPOT`) histogram quantiles, Triton ensemble bottleneck queue delay
   (`nv_inference_queue_duration_us / nv_inference_request_success > 500000` us),
   and `llm-d` Workload Variant Autoscaler (`WVA`) (`VL5` Ch. 3; `GAK` Ch. 4, 5; `V12` Ch. 8, 10).
3. Kubernetes HPA v2 control-loop equation
   `desiredReplicas = ceil[currentReplicas * (currentMetricValue / desiredMetricValue)]`,
   `10%` deadband tolerance, stabilization windows (`0 s` scaleUp vs `180 s` / `300 s` / `600 s`
   scaleDown), asymmetric `Percent` and `Pods` policies (`selectPolicy: Max` / `Min`),
   VPA (`Auto` vs `Off` / `Goldilocks`) conflict analysis, and `8`-GPU rolling update
   `maxSurge: 1, maxUnavailable: 3` math (`LLP` Ch. 6; `K8GS` Ch. 6, 7; `VL5` Ch. 3).
4. KEDA `ScaledObject` architecture (`keda-operator` `0 <-> 1` activation vs
   `keda-operator-metrics-apiserver` `1 <-> N` HPA loop), `PodMetric` (OpenTelemetry) vs
   `External` (Prometheus) triggers, scale-from-zero division-by-zero protection,
   KEDA HTTP Add-on interceptor, and KServe `Knative` (`KPA` `60 s` stable vs `6 s` panic
   window at `200%` threshold + `queue-proxy` `containerConcurrency`) vs `Standard` mode
   (`GAK` Ch. 1, 4, 5; `K8GS` Ch. 6; `LLP` Ch. 6; `VL5` Ch. 3).
5. End-to-end cold-start anatomy:
   `T_cold = T_node_provision + T_image_pull + T_init + T_weight_load + T_cuda_graph_warmup`
   across Cluster Autoscaler vs Karpenter (`33.66 ms` solver, `~117 s` node ready),
   `imagePullPolicy: IfNotPresent` (`~5 GB` image), remote S3/HF vs shared NFS PVC vs
   local NVMe vs KServe `modelcar` (`/proc/$$/root/models`, `< 10 MB` RAM) / K8s `1.31`/`1.35`
   OCI image volume mounts vs `Run:ai Model Streamer` (`16` threads) vs NVIDIA GPUDirect
   Storage (`GDS` / `cuFile`) (`GAK` Ch. 2, 4; `VL5` Ch. 3; `HLS` Ch. 5; `K8GS` Ch. 6).
6. Production failure modes and FinOps cost engineering:
   - Scenario 1: Queue-depth thrashing on `Llama-3-8B` (`threshold=5`, `50`-req burst,
     `60 s` cold start, `2 -> 10 -> 2` oscillation) vs `avg_over_time[1m]` / `threshold=100`
     / `time_in_queue > 2.0 s` (`VL5` Ch. 3).
   - Scenario 2: Readiness probe cascading `503` outage during `4 -> 12` HPA scale-out over
     shared NFS (`1.2 s` stall vs `1.0 s` timeout) fixed by `600 s` `startupProbe`, `5 s`
     `/health` `readinessProbe`, and `/ping` `livenessProbe` (`V12` Ch. 11).
   - Scenario 3: Multi-turn KV prefix cache miss storm across `10` round-robin pods vs
     Gateway API Inference Extension (`InferencePool` + Envoy `ext_proc` Endpoint Picker
     port `9002`) / `Chat-Session-ID` sticky routing (`VL5` Ch. 3; `GAK` Ch. 4; `V12` Ch. 9).
   - FinOps `Cost per 1M Tokens = (Node_Cost_Per_Hour / 3600) / Throughput * 1,000,000`
     and quantization KV capacity expansion (`Qwen3-14B` BF16 `72,064` tokens vs AWQ 4-bit
     `191,056` tokens, `2.70x` throughput and cost reduction) (`VL5` Ch. 3; `HLS` Ch. 5, 9; `V12` Ch. 10).
"""

from __future__ import annotations
import math
from typing import Dict, List, Sequence, Tuple


# ---------------------------------------------------------------------------
# 1. Why CPU, Memory, and GPU SM Utilization Fail as LLM Autoscaling Signals
# ---------------------------------------------------------------------------

def evaluate_vllm_memory_and_signal_fidelity(
    active_requests: int,
    total_gpu_memory_gib: float = 79.14,
    gpu_memory_utilization: float = 0.90,
    model_weights_gib: float = 14.99,
    non_torch_gib: float = 0.12,
    activation_peak_gib: float = 1.19,
    max_kv_tokens: int = 128000,
    avg_tokens_per_request: int = 2048,
    max_batch_capacity: int = 64,
) -> Dict[str, float | int | str | bool]:
    """Compare legacy resource metrics (CPU, VRAM, `DCGM_FI_DEV_GPU_UTIL`) against
    LLM-native metrics (`vllm:num_requests_waiting`, `vllm:gpu_cache_usage_perc`).

    Numbers grounded in `GAK` Ch. 4 Example 4-3 (`79.14 GiB * 0.90 = 71.22 GiB`,
    `14.99 GiB` weights, `0.12 GiB` non-torch, `1.19 GiB` activation peak,
    `54.93 GiB` KV cache) and `VL5` Ch. 3 / `V12` Ch. 1, 8.
    """
    if active_requests < 0:
        raise ValueError("active_requests must be non-negative")

    usable_vram_gib = round(total_gpu_memory_gib * gpu_memory_utilization, 2)
    kv_cache_reserved_gib = round(
        usable_vram_gib - model_weights_gib - non_torch_gib - activation_peak_gib, 2
    )
    # Static pre-allocation means OS/container VRAM usage is fixed at 90.0% regardless of load
    allocated_vram_pct = round(gpu_memory_utilization * 100.0, 1)

    running_requests = min(active_requests, max_batch_capacity)
    waiting_requests = max(0, active_requests - max_batch_capacity)

    # Under continuous batching, even 1 active decode stream keeps the GPU kernel loop active ~99-100% of time
    dcgm_gpu_util_pct = 0.0 if running_requests == 0 else (98.0 if running_requests == 1 else 100.0)
    # True SM occupancy scales with batch size up to the Roofline ridge point
    dcgm_sm_active_pct = round(min(95.0, (running_requests / max_batch_capacity) * 90.0), 1)
    host_cpu_util_pct = round(min(45.0, 5.0 + running_requests * 0.35), 1)

    active_kv_tokens = running_requests * avg_tokens_per_request
    kv_cache_usage_ratio = min(1.0, round(active_kv_tokens / max_kv_tokens, 4))
    kv_cache_usage_pct = round(kv_cache_usage_ratio * 100.0, 2)

    if kv_cache_usage_pct < 80.0:
        kv_zone = "Safe"
    elif kv_cache_usage_pct <= 90.0:
        kv_zone = "Warning"
    else:
        kv_zone = "Emergency"

    return {
        "active_requests": active_requests,
        "running_requests": running_requests,
        "waiting_requests": waiting_requests,
        "usable_vram_gib": usable_vram_gib,
        "kv_cache_reserved_gib": kv_cache_reserved_gib,
        "allocated_vram_pct": allocated_vram_pct,
        "host_cpu_util_pct": host_cpu_util_pct,
        "dcgm_gpu_util_pct": dcgm_gpu_util_pct,
        "dcgm_sm_active_pct": dcgm_sm_active_pct,
        "kv_cache_usage_ratio": kv_cache_usage_ratio,
        "kv_cache_usage_pct": kv_cache_usage_pct,
        "kv_zone": kv_zone,
        "legacy_metrics_blind": (running_requests >= 1 and dcgm_gpu_util_pct >= 98.0),
    }


def compute_8b_vram_sizing(
    batch_size: int = 1,
    params_billions: float = 8.0,
    bytes_per_param: float = 2.0,
    infra_gb: float = 1.0,
    base_activation_gb: float = 0.9,
    base_output_gb: float = 0.4,
    per_extra_req_kv_and_act_gb: float = 1.2,
) -> Dict[str, float | int]:
    """Model VRAM growth from `GAK` Ch. 4 sidebar ('How to Calculate Model Memory Requirements'):
    An 8B float16 model at 2048 context needs 16 GB weights + 1 GB infra + 0.9 GB activations
    + 0.4 GB output = 17.3 GB at batch=1, and pushes over 28 GB (28.1 GB) at batch=10.
    """
    weights_gb = round(params_billions * bytes_per_param, 2)
    extra_batches = max(0, batch_size - 1)
    total_vram_gb = round(
        weights_gb + base_activation_gb + base_output_gb + extra_batches * per_extra_req_kv_and_act_gb,
        2,
    )
    total_with_infra_gb = round(total_vram_gb + infra_gb, 2)
    return {
        "batch_size": batch_size,
        "weights_gb": weights_gb,
        "infra_gb": infra_gb,
        "base_activation_gb": base_activation_gb,
        "base_output_gb": base_output_gb,
        "total_vram_gb": total_vram_gb,
        "total_with_infra_gb": total_with_infra_gb,
    }


# ---------------------------------------------------------------------------
# 2. Custom Prometheus Metrics: Queue Depth, KV Usage, TTFT/ITL & Triton Queue
# ---------------------------------------------------------------------------

def evaluate_custom_llm_scaling_triggers(
    total_requests_waiting: int,
    active_replicas: int,
    kv_cache_usage_per_pod: Sequence[float],
    p95_ttft_seconds: float,
    p95_itl_seconds: float,
    waiting_per_pod_threshold: float = 20.0,
    kv_usage_threshold: float = 0.80,
    ttft_slo_seconds: float = 0.200,
    itl_slo_seconds: float = 0.025,
    triton_queue_duration_us: float = 0.0,
    triton_request_success: int = 1,
    triton_threshold_us: float = 500000.0,
) -> Dict[str, object]:
    """Evaluate multi-signal PromQL triggers for vLLM and NVIDIA Triton (`VL5` Ch. 3, `V12` Ch. 10, `GAK` Ch. 4, 5)."""
    if active_replicas <= 0:
        avg_waiting_per_replica = float("inf") if total_requests_waiting > 0 else 0.0
    else:
        avg_waiting_per_replica = round(total_requests_waiting / active_replicas, 2)

    max_kv_usage = round(max(kv_cache_usage_per_pod) if kv_cache_usage_per_pod else 0.0, 4)
    avg_kv_usage = round(
        sum(kv_cache_usage_per_pod) / len(kv_cache_usage_per_pod) if kv_cache_usage_per_pod else 0.0,
        4,
    )

    triton_avg_queue_us = (
        round(triton_queue_duration_us / triton_request_success, 2)
        if triton_request_success > 0
        else 0.0
    )

    queue_trigger = avg_waiting_per_replica > waiting_per_pod_threshold
    kv_trigger = max_kv_usage >= kv_usage_threshold
    ttft_trigger = p95_ttft_seconds > ttft_slo_seconds
    itl_trigger = p95_itl_seconds > itl_slo_seconds
    triton_trigger = triton_avg_queue_us > triton_threshold_us

    return {
        "avg_waiting_per_replica": avg_waiting_per_replica,
        "max_kv_usage": max_kv_usage,
        "avg_kv_usage": avg_kv_usage,
        "p95_ttft_seconds": p95_ttft_seconds,
        "p95_itl_seconds": p95_itl_seconds,
        "triton_avg_queue_us": triton_avg_queue_us,
        "queue_trigger_fired": queue_trigger,
        "kv_trigger_fired": kv_trigger,
        "ttft_trigger_fired": ttft_trigger,
        "itl_trigger_fired": itl_trigger,
        "triton_trigger_fired": triton_trigger,
        "scale_up_required": any([queue_trigger, kv_trigger, ttft_trigger, itl_trigger, triton_trigger]),
    }


# ---------------------------------------------------------------------------
# 3. Kubernetes HPA v2 Formula, Stabilization Windows & Policy Simulator
# ---------------------------------------------------------------------------

def compute_hpa_desired_replicas(
    current_replicas: int,
    current_metric_value: float,
    desired_metric_value: float,
    min_replicas: int = 1,
    max_replicas: int = 10,
    tolerance: float = 0.10,
    scale_up_percent_cap: float | None = None,
    scale_up_pods_cap: int | None = None,
    scale_up_select_policy: str = "Max",
    scale_down_percent_cap: float | None = None,
    scale_down_pods_cap: int | None = None,
    scale_down_select_policy: str = "Min",
) -> Dict[str, int | float | bool | str]:
    """Compute Kubernetes HPA v2 target replica count with deadband tolerance and behavior policies.

    Formula (`LLP` Ch. 6, `K8GS` Ch. 6, `VL5` Ch. 3):
        desiredReplicas = ceil[currentReplicas * (currentMetricValue / desiredMetricValue)]
    """
    if desired_metric_value <= 0:
        raise ValueError("desired_metric_value must be positive")
    if current_replicas <= 0:
        raise ValueError("HPA requires current_replicas >= 1 (use KEDA for 0 -> 1)")

    ratio = current_metric_value / desired_metric_value
    within_tolerance = abs(ratio - 1.0) <= tolerance

    if within_tolerance:
        raw_desired = current_replicas
    else:
        raw_desired = math.ceil(current_replicas * ratio)

    policy_capped = raw_desired
    if raw_desired > current_replicas:
        candidates: List[int] = []
        if scale_up_percent_cap is not None:
            candidates.append(current_replicas + math.ceil(current_replicas * (scale_up_percent_cap / 100.0)))
        if scale_up_pods_cap is not None:
            candidates.append(current_replicas + scale_up_pods_cap)
        if candidates:
            policy_capped = max(candidates) if scale_up_select_policy == "Max" else min(candidates)
            policy_capped = min(raw_desired, policy_capped)
    elif raw_desired < current_replicas:
        candidates = []
        if scale_down_percent_cap is not None:
            max_drop = math.floor(current_replicas * (scale_down_percent_cap / 100.0))
            candidates.append(current_replicas - max_drop)
        if scale_down_pods_cap is not None:
            candidates.append(current_replicas - scale_down_pods_cap)
        if candidates:
            # Min policy means smallest change (i.e. highest remaining replica floor)
            policy_capped = max(candidates) if scale_down_select_policy == "Min" else min(candidates)
            policy_capped = max(raw_desired, policy_capped)

    clamped = max(min_replicas, min(max_replicas, policy_capped))
    return {
        "current_replicas": current_replicas,
        "metric_ratio": round(ratio, 4),
        "within_tolerance": within_tolerance,
        "raw_desired_replicas": raw_desired,
        "policy_capped_replicas": policy_capped,
        "final_desired_replicas": clamped,
    }


def evaluate_rolling_update_gpu_budget(
    replicas: int = 5,
    gpus_per_pod: int = 8,
    max_surge_pods: int = 1,
    max_unavailable_pods: int = 3,
    spare_cluster_gpus: int = 0,
) -> Dict[str, int | bool]:
    """Evaluate `LLP` Ch. 6 Listing 6.9 rolling update GPU budget for 8-GPU LLM pods."""
    steady_state_gpus = replicas * gpus_per_pod
    surge_gpus_needed = max_surge_pods * gpus_per_pod
    can_surge_without_terminating = spare_cluster_gpus >= surge_gpus_needed
    min_available_pods = replicas - max_unavailable_pods
    freed_gpus_from_unavailable = max_unavailable_pods * gpus_per_pod
    rollout_progresses = (spare_cluster_gpus + freed_gpus_from_unavailable) >= gpus_per_pod
    return {
        "replicas": replicas,
        "gpus_per_pod": gpus_per_pod,
        "steady_state_gpus": steady_state_gpus,
        "surge_gpus_needed": surge_gpus_needed,
        "min_available_pods": min_available_pods,
        "freed_gpus_from_unavailable": freed_gpus_from_unavailable,
        "can_surge_without_terminating": can_surge_without_terminating,
        "rollout_progresses": rollout_progresses,
    }


# ---------------------------------------------------------------------------
# 4. KEDA Scale-to-Zero & Knative KPA Stable vs Panic Window Controller
# ---------------------------------------------------------------------------

def simulate_keda_and_knative_autoscaling(
    pending_requests: int,
    current_replicas: int,
    seconds_since_last_active: int,
    keda_threshold: float = 20.0,
    keda_activation_threshold: float = 0.0,
    cooldown_period_s: int = 300,
    min_replicas: int = 0,
    max_replicas: int = 10,
    knative_stable_concurrency: float = 0.0,
    knative_panic_concurrency: float = 0.0,
    knative_target_concurrency: float = 10.0,
    knative_panic_threshold_pct: float = 200.0,
) -> Dict[str, object]:
    """Model KEDA `0 <-> 1` activation + `1 <-> N` HPA scaling alongside Knative KPA
    (`60 s` stable window vs `6 s` panic window at `200%` burst threshold).
    """
    # KEDA state machine
    if current_replicas == 0:
        if pending_requests > keda_activation_threshold:
            # KEDA operator wakes deployment 0 -> 1, then HPA computes desired replicas
            keda_replicas = min(max_replicas, max(1, math.ceil(pending_requests / keda_threshold)))
            keda_state = "ActivatedFromZero"
        else:
            keda_replicas = 0
            keda_state = "ScaledToZero"
    else:
        if pending_requests == 0 and min_replicas == 0 and seconds_since_last_active >= cooldown_period_s:
            keda_replicas = 0
            keda_state = "CooldownExpiredScaleToZero"
        elif pending_requests == 0 and seconds_since_last_active < cooldown_period_s:
            keda_replicas = current_replicas
            keda_state = "InCooldownHold"
        else:
            per_pod_metric = pending_requests / current_replicas
            raw = math.ceil(current_replicas * (per_pod_metric / keda_threshold))
            keda_replicas = max(max(1, min_replicas), min(max_replicas, raw))
            keda_state = "ActiveHpaScaling"

    # Knative KPA state machine (stable 60s vs panic 6s window)
    panic_ratio = (knative_panic_concurrency / knative_target_concurrency) * 100.0 if knative_target_concurrency > 0 else 0.0
    in_panic_mode = panic_ratio >= knative_panic_threshold_pct
    effective_concurrency = knative_panic_concurrency if in_panic_mode else knative_stable_concurrency
    kpa_desired_replicas = (
        math.ceil(effective_concurrency / knative_target_concurrency)
        if effective_concurrency > 0
        else 0
    )

    return {
        "keda_state": keda_state,
        "keda_desired_replicas": keda_replicas,
        "kpa_in_panic_mode": in_panic_mode,
        "kpa_panic_ratio_pct": round(panic_ratio, 1),
        "kpa_desired_replicas": kpa_desired_replicas,
    }


# ---------------------------------------------------------------------------
# 5. Cold-Start Anatomy: Image Pull, Node Provisioning & Weight Streaming
# ---------------------------------------------------------------------------

def compute_cold_start_anatomy(
    model_weights_gb: float = 140.0,
    node_provision_s: float = 0.0,
    image_size_gb: float = 5.0,
    image_cached: bool = True,
    image_pull_bw_gb_s: float = 0.25,
    runtime_init_s: float = 1.0,
    weight_load_gb_s: float = 11.2,
    cuda_graph_warmup_s: float = 8.0,
) -> Dict[str, float]:
    """Decompose LLM pod cold-start latency into its five physical stages (`GAK` Ch. 4, `VL5` Ch. 3, `HLS` Ch. 5):
        T_cold = T_node_provision + T_image_pull + T_init + T_weight_load + T_cuda_graph_warmup
    """
    t_image = 0.0 if image_cached else round(image_size_gb / image_pull_bw_gb_s, 2)
    t_weights = round(model_weights_gb / weight_load_gb_s, 2)
    t_total = round(node_provision_s + t_image + runtime_init_s + t_weights + cuda_graph_warmup_s, 2)
    return {
        "node_provision_s": round(node_provision_s, 2),
        "image_pull_s": t_image,
        "runtime_init_s": round(runtime_init_s, 2),
        "weight_load_s": t_weights,
        "cuda_graph_warmup_s": round(cuda_graph_warmup_s, 2),
        "total_cold_start_s": t_total,
    }


def compare_weight_loading_strategies(
    model_weights_gb: float = 140.0,
) -> Dict[str, Dict[str, float]]:
    """Compare cold-start weight loading across storage & streaming tiers for `Llama-3-70B` (`140 GB` FP16):
    1. Uncached node + `imagePullPolicy: Always` (`5 GB` @ `0.25 GB/s` = `20 s`) + remote S3/HF download (`0.5 GB/s` = `280 s`) + Karpenter node boot (`117 s`).
    2. Warm node + shared NFS PVC (`1.25 GB/s` = `112 s`).
    3. Warm node + local NVMe single-thread `safetensors` (`7.0 GB/s` = `20.0 s`).
    4. Warm node + `Run:ai Model Streamer` (`--load-format runai_streamer --model-loader-extra-config '{"concurrency":16}'` @ `11.2 GB/s` = `12.5 s`).
    5. Warm node + NVIDIA GPUDirect Storage (`GDS` `cuFile` DMA over PCIe Gen5 @ `28.0 GB/s` = `5.0 s`).
    """
    return {
        "remote_s3_cold_node": compute_cold_start_anatomy(
            model_weights_gb=model_weights_gb,
            node_provision_s=117.0,
            image_cached=False,
            image_pull_bw_gb_s=0.25,
            runtime_init_s=1.0,
            weight_load_gb_s=0.5,
            cuda_graph_warmup_s=8.0,
        ),
        "shared_nfs_warm_node": compute_cold_start_anatomy(
            model_weights_gb=model_weights_gb,
            node_provision_s=0.0,
            image_cached=True,
            runtime_init_s=1.0,
            weight_load_gb_s=1.25,
            cuda_graph_warmup_s=8.0,
        ),
        "local_nvme_standard": compute_cold_start_anatomy(
            model_weights_gb=model_weights_gb,
            node_provision_s=0.0,
            image_cached=True,
            runtime_init_s=1.0,
            weight_load_gb_s=7.0,
            cuda_graph_warmup_s=8.0,
        ),
        "runai_model_streamer_16t": compute_cold_start_anatomy(
            model_weights_gb=model_weights_gb,
            node_provision_s=0.0,
            image_cached=True,
            runtime_init_s=1.0,
            weight_load_gb_s=11.2,
            cuda_graph_warmup_s=8.0,
        ),
        "gpudirect_storage_gds": compute_cold_start_anatomy(
            model_weights_gb=model_weights_gb,
            node_provision_s=0.0,
            image_cached=True,
            runtime_init_s=1.0,
            weight_load_gb_s=28.0,
            cuda_graph_warmup_s=8.0,
        ),
    }


# ---------------------------------------------------------------------------
# 6. Production Failure Modes & Cost-per-Million-Tokens FinOps
# ---------------------------------------------------------------------------

def diagnose_queue_thrashing_and_probe_cascade(
    initial_replicas: int = 2,
    burst_requests: int = 50,
    naive_queue_threshold: int = 5,
    tuned_queue_threshold: int = 100,
    service_rate_req_per_s_per_pod: float = 15.0,
    pod_cold_start_s: float = 60.0,
    cooldown_s: int = 300,
    hpa_scale_from: int = 4,
    hpa_scale_to: int = 12,
    nfs_bandwidth_gb_s: float = 1.25,
    probe_timeout_naive_s: float = 1.0,
    probe_timeout_tuned_s: float = 5.0,
    nfs_contended_response_s: float = 1.2,
) -> Dict[str, object]:
    """Simulate:
    1. `VL5` Ch. 3 Scenario 1: Queue-depth thrashing on `Llama-3-8B` (`2 -> 10 -> 2` replicas)
       when `threshold = 5` and a `50`-request burst clears in `1.67 s` (`< 60 s` cold start).
    2. `V12` Ch. 11 Scenario 1: Readiness probe cascading `503` outage when `8` new pods
       saturate shared NFS, pushing healthy pods' `/v1/models` response time to `1.2 s > 1.0 s`.
    """
    # Scenario 1: Queue-depth thrashing
    naive_desired = math.ceil(initial_replicas * ((burst_requests / initial_replicas) / naive_queue_threshold))
    burst_drain_time_s = round(burst_requests / (initial_replicas * service_rate_req_per_s_per_pod), 2)
    thrashing_occurs = (naive_desired > initial_replicas) and (burst_drain_time_s < pod_cold_start_s)

    tuned_desired = max(
        initial_replicas,
        math.ceil(initial_replicas * ((burst_requests / initial_replicas) / tuned_queue_threshold)),
    )

    # Scenario 2: Readiness probe cascade during NFS weight pull storm
    new_pods = hpa_scale_to - hpa_scale_from
    per_pod_nfs_mb_s = round((nfs_bandwidth_gb_s * 1000.0) / new_pods, 2)
    naive_probe_fails = nfs_contended_response_s > probe_timeout_naive_s
    naive_healthy_endpoints = 0 if naive_probe_fails else hpa_scale_from
    tuned_probe_passes = nfs_contended_response_s <= probe_timeout_tuned_s
    tuned_healthy_endpoints = hpa_scale_from if tuned_probe_passes else 0

    return {
        "naive_scaled_replicas": naive_desired,
        "burst_drain_time_s": burst_drain_time_s,
        "pod_cold_start_s": pod_cold_start_s,
        "wasted_gpu_pod_seconds": (naive_desired - initial_replicas) * cooldown_s,
        "thrashing_occurs": thrashing_occurs,
        "tuned_scaled_replicas": tuned_desired,
        "new_scaling_pods": new_pods,
        "per_pod_nfs_mb_s": per_pod_nfs_mb_s,
        "naive_healthy_endpoints": naive_healthy_endpoints,
        "naive_http_503_pct": 100.0 if naive_healthy_endpoints == 0 else 0.0,
        "tuned_healthy_endpoints": tuned_healthy_endpoints,
        "startup_probe_budget_s": 60 * 10,  # failureThreshold 60 * periodSeconds 10 = 600s
    }


def compute_token_cost_and_quantization_roi(
    node_cost_per_hour_usd: float = 49.60,
    throughput_tok_per_s: float = 2658.76,
    early_scale_batch1_tok_per_s: float = 24.0,
    l40s_hourly_usd: float = 2.25,
    qwen_bf16_tok_s: float = 474.38,
    qwen_bf16_kv_tokens: int = 72064,
    qwen_awq_tok_s: float = 1280.0,
    qwen_awq_kv_tokens: int = 191056,
) -> Dict[str, float]:
    """Compute `VL5` Ch. 3 FinOps metric:
        Cost per 1M Tokens = (Node Cost per Hour / 3600) / Throughput * 1,000,000
    and `HLS` Ch. 9 quantization capacity/throughput ROI (`Qwen3-14B` BF16 vs AWQ 4-bit).
    """
    cost_per_1m_optimal_usd = round((node_cost_per_hour_usd / 3600.0) / throughput_tok_per_s * 1_000_000.0, 2)
    cost_per_1m_batch1_usd = round((node_cost_per_hour_usd / 3600.0) / early_scale_batch1_tok_per_s * 1_000_000.0, 2)
    premature_scaling_penalty_x = round(cost_per_1m_batch1_usd / cost_per_1m_optimal_usd, 2)

    qwen_bf16_cost_1m = round((l40s_hourly_usd / 3600.0) / qwen_bf16_tok_s * 1_000_000.0, 2)
    qwen_awq_cost_1m = round((l40s_hourly_usd / 3600.0) / qwen_awq_tok_s * 1_000_000.0, 2)
    kv_expansion_x = round(qwen_awq_kv_tokens / qwen_bf16_kv_tokens, 2)
    throughput_gain_x = round(qwen_awq_tok_s / qwen_bf16_tok_s, 2)

    return {
        "node_cost_per_hour_usd": node_cost_per_hour_usd,
        "cost_per_1m_optimal_usd": cost_per_1m_optimal_usd,
        "cost_per_1m_batch1_usd": cost_per_1m_batch1_usd,
        "premature_scaling_penalty_x": premature_scaling_penalty_x,
        "qwen_bf16_cost_1m_usd": qwen_bf16_cost_1m,
        "qwen_awq_cost_1m_usd": qwen_awq_cost_1m,
        "kv_expansion_x": kv_expansion_x,
        "throughput_gain_x": throughput_gain_x,
    }


if __name__ == "__main__":
    print("Chapter 15.15 Autoscaling Inference Model Loaded Successfully.")
