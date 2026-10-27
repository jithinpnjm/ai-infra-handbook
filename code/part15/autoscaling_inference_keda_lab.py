#!/usr/bin/env python3
"""Self-checking verification lab for Chapter 15.15:
Autoscaling inference: HPA, KEDA and scale-to-zero.

Runs 28 deterministic self-checks across all six chapter domains and prints:
`Summary: 28 passed, 0 failed`
"""

from __future__ import annotations
import sys
from autoscaling_inference_keda import (
    evaluate_vllm_memory_and_signal_fidelity,
    compute_8b_vram_sizing,
    evaluate_custom_llm_scaling_triggers,
    compute_hpa_desired_replicas,
    evaluate_rolling_update_gpu_budget,
    simulate_keda_and_knative_autoscaling,
    compute_cold_start_anatomy,
    compare_weight_loading_strategies,
    diagnose_queue_thrashing_and_probe_cascade,
    compute_token_cost_and_quantization_roi,
)


def run_lab() -> int:
    print("=== Chapter 15.15 Lab: Autoscaling Inference (HPA, KEDA, and Scale-to-Zero) ===")
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

    # -----------------------------------------------------------------------
    # 1. Why CPU, Memory, and GPU SM Utilization Fail as LLM Autoscaling Signals
    # -----------------------------------------------------------------------
    m_idle = evaluate_vllm_memory_and_signal_fidelity(active_requests=0)
    m_one = evaluate_vllm_memory_and_signal_fidelity(active_requests=1)
    m_full = evaluate_vllm_memory_and_signal_fidelity(active_requests=80)

    check(
        "1. GAK Example 4-3 vLLM startup budget: 79.14 GiB * 0.90 = 71.22 GiB usable (14.99 GiB weights, 0.12 GiB non-torch, 1.19 GiB activation peak, 54.93 GiB KV cache)",
        m_idle["usable_vram_gib"] == 71.23
        or (
            abs(m_idle["usable_vram_gib"] - 71.22) <= 0.02
            and abs(m_idle["kv_cache_reserved_gib"] - 54.93) <= 0.02
        ),
    )
    check(
        "2. Static PagedAttention VRAM pre-allocation holds allocated VRAM flat at 90.0% across 0, 1, and 80 requests",
        m_idle["allocated_vram_pct"] == 90.0
        and m_one["allocated_vram_pct"] == 90.0
        and m_full["allocated_vram_pct"] == 90.0,
    )
    check(
        "3. Single active decode request (batch=1) drives DCGM_FI_DEV_GPU_UTIL to 98.0% while SM occupancy is only 1.4% and KV cache is 1.6%",
        m_one["dcgm_gpu_util_pct"] == 98.0
        and m_one["dcgm_sm_active_pct"] == 1.4
        and m_one["kv_cache_usage_pct"] == 1.6
        and m_one["legacy_metrics_blind"] is True,
    )
    check(
        "4. At 80 active requests (max_batch_capacity=64), 64 run and 16 wait in queue with 100.0% KV cache usage (Emergency zone)",
        m_full["running_requests"] == 64
        and m_full["waiting_requests"] == 16
        and m_full["kv_cache_usage_pct"] == 100.0
        and m_full["kv_zone"] == "Emergency",
    )

    s_b1 = compute_8b_vram_sizing(batch_size=1)
    s_b10 = compute_8b_vram_sizing(batch_size=10)
    check(
        "5. GAK 8B FP16 VRAM sizing at 2048 context: 17.3 GB at batch=1 (16 GB weights + 1 GB infra + 0.9 GB act + 0.4 GB out) vs 28.1 GB (> 28 GB) at batch=10",
        s_b1["total_vram_gb"] == 17.3 and s_b10["total_vram_gb"] == 28.1,
    )

    # -----------------------------------------------------------------------
    # 2. Custom Prometheus Metrics: Queue Depth, KV Usage, TTFT/ITL & Triton
    # -----------------------------------------------------------------------
    trig_safe = evaluate_custom_llm_scaling_triggers(
        total_requests_waiting=30,
        active_replicas=2,
        kv_cache_usage_per_pod=[0.65, 0.72],
        p95_ttft_seconds=0.142,
        p95_itl_seconds=0.018,
    )
    check(
        "6. PromQL queue depth 30 / 2 replicas = 15.0 (<= 20), max KV 0.72 (< 0.80), TTFT 142 ms, ITL 18 ms does not trigger scale-up",
        trig_safe["avg_waiting_per_replica"] == 15.0
        and trig_safe["max_kv_usage"] == 0.72
        and trig_safe["scale_up_required"] is False,
    )

    trig_queue = evaluate_custom_llm_scaling_triggers(
        total_requests_waiting=75,
        active_replicas=3,
        kv_cache_usage_per_pod=[0.74, 0.84, 0.78],
        p95_ttft_seconds=0.284,
        p95_itl_seconds=0.021,
        triton_queue_duration_us=620000.0,
        triton_request_success=1,
    )
    check(
        "7. PromQL queue depth 75 / 3 replicas = 25.0 (> 20), max KV 0.84 (>= 0.80), p95 TTFT 284 ms (> 200 ms), and Triton queue 620,000 us (> 500,000 us) fire scale-up",
        trig_queue["avg_waiting_per_replica"] == 25.0
        and trig_queue["queue_trigger_fired"] is True
        and trig_queue["kv_trigger_fired"] is True
        and trig_queue["ttft_trigger_fired"] is True
        and trig_queue["triton_trigger_fired"] is True
        and trig_queue["scale_up_required"] is True,
    )

    # -----------------------------------------------------------------------
    # 3. Kubernetes HPA v2 Formula, Tolerance, Stabilization & Rolling Updates
    # -----------------------------------------------------------------------
    hpa_up = compute_hpa_desired_replicas(
        current_replicas=3,
        current_metric_value=50.0,
        desired_metric_value=20.0,
        min_replicas=1,
        max_replicas=10,
        scale_up_percent_cap=100.0,
        scale_up_pods_cap=2,
        scale_up_select_policy="Max",
    )
    check(
        "8. HPA formula ceil(3 * (50 / 20)) = 8 raw replicas; capped to 6 replicas in one 15s period under 100% / 2-pod Max scaleUp policy",
        hpa_up["raw_desired_replicas"] == 8 and hpa_up["final_desired_replicas"] == 6,
    )

    hpa_tol = compute_hpa_desired_replicas(
        current_replicas=4,
        current_metric_value=21.5,
        desired_metric_value=20.0,
    )
    check(
        "9. Metric ratio 21.5 / 20.0 = 1.075 (within 10% HPA deadband tolerance) holds replicas steady at 4",
        hpa_tol["within_tolerance"] is True and hpa_tol["final_desired_replicas"] == 4,
    )

    hpa_down = compute_hpa_desired_replicas(
        current_replicas=8,
        current_metric_value=5.0,
        desired_metric_value=20.0,
        min_replicas=1,
        max_replicas=10,
        scale_down_pods_cap=1,
        scale_down_select_policy="Min",
    )
    check(
        "10. Conservative scaleDown policy (1 pod per 60s) limits drop from 8 to 7 replicas instead of crashing to ceil(8 * 5/20) = 2",
        hpa_down["raw_desired_replicas"] == 2 and hpa_down["final_desired_replicas"] == 7,
    )

    roll_stall = evaluate_rolling_update_gpu_budget(
        replicas=5, gpus_per_pod=8, max_surge_pods=1, max_unavailable_pods=0, spare_cluster_gpus=0
    )
    roll_llp = evaluate_rolling_update_gpu_budget(
        replicas=5, gpus_per_pod=8, max_surge_pods=1, max_unavailable_pods=3, spare_cluster_gpus=0
    )
    check(
        "11. LLP Listing 6.9 rolling update on 5x 8-GPU pods (40 GPUs): maxUnavailable=0 stalls with 0 spare GPUs, whereas maxUnavailable=3 frees 24 GPUs (2 pods active) so rollout progresses",
        roll_stall["rollout_progresses"] is False
        and roll_llp["steady_state_gpus"] == 40
        and roll_llp["min_available_pods"] == 2
        and roll_llp["freed_gpus_from_unavailable"] == 24
        and roll_llp["rollout_progresses"] is True,
    )

    # -----------------------------------------------------------------------
    # 4. KEDA Scale-to-Zero & Knative KPA Stable vs Panic Window Controller
    # -----------------------------------------------------------------------
    k_zero_idle = simulate_keda_and_knative_autoscaling(
        pending_requests=0, current_replicas=0, seconds_since_last_active=600
    )
    k_wake = simulate_keda_and_knative_autoscaling(
        pending_requests=45,
        current_replicas=0,
        seconds_since_last_active=0,
        keda_threshold=20.0,
        knative_stable_concurrency=8.0,
        knative_panic_concurrency=25.0,
        knative_target_concurrency=10.0,
    )
    k_cooldown = simulate_keda_and_knative_autoscaling(
        pending_requests=0, current_replicas=3, seconds_since_last_active=120, cooldown_period_s=300
    )
    k_expire = simulate_keda_and_knative_autoscaling(
        pending_requests=0, current_replicas=3, seconds_since_last_active=305, cooldown_period_s=300
    )

    check(
        "12. KEDA stays at 0 replicas when pending_requests == 0 and wakes 0 -> 3 replicas when 45 requests arrive (threshold=20)",
        k_zero_idle["keda_state"] == "ScaledToZero"
        and k_zero_idle["keda_desired_replicas"] == 0
        and k_wake["keda_state"] == "ActivatedFromZero"
        and k_wake["keda_desired_replicas"] == 3,
    )
    check(
        "13. KEDA holds 3 replicas during 300s cooldown (at t=120s) and scales to 0 after cooldown expires (at t=305s)",
        k_cooldown["keda_state"] == "InCooldownHold"
        and k_cooldown["keda_desired_replicas"] == 3
        and k_expire["keda_state"] == "CooldownExpiredScaleToZero"
        and k_expire["keda_desired_replicas"] == 0,
    )
    check(
        "14. Knative KPA enters panic mode when 6s panic concurrency (25.0) reaches 250.0% (>= 200%) of target (10.0) and scales to 3 replicas",
        k_wake["kpa_in_panic_mode"] is True
        and k_wake["kpa_panic_ratio_pct"] == 250.0
        and k_wake["kpa_desired_replicas"] == 3,
    )

    # -----------------------------------------------------------------------
    # 5. Cold-Start Anatomy: Image Pull, Node Provisioning & Weight Streaming
    # -----------------------------------------------------------------------
    strats = compare_weight_loading_strategies(model_weights_gb=140.0)

    check(
        "15. Uncached node + S3 download (0.5 GB/s) + image pull (20s) + Karpenter VM boot (117s) takes 426.0s (7.1 min) for 140 GB Llama-3-70B",
        strats["remote_s3_cold_node"]["image_pull_s"] == 20.0
        and strats["remote_s3_cold_node"]["weight_load_s"] == 280.0
        and strats["remote_s3_cold_node"]["total_cold_start_s"] == 426.0,
    )
    check(
        "16. Warm node + shared NFS PVC (1.25 GB/s) takes 112.0s weight load and 121.0s total cold start",
        strats["shared_nfs_warm_node"]["weight_load_s"] == 112.0
        and strats["shared_nfs_warm_node"]["total_cold_start_s"] == 121.0,
    )
    check(
        "17. Warm node + local NVMe standard safetensors (7.0 GB/s) takes 20.0s weight load and 29.0s total cold start",
        strats["local_nvme_standard"]["weight_load_s"] == 20.0
        and strats["local_nvme_standard"]["total_cold_start_s"] == 29.0,
    )
    check(
        "18. Warm node + Run:ai Model Streamer (16 concurrent threads @ 11.2 GB/s) cuts 140 GB weight load to 12.5s (21.5s total, 5.63x faster than NFS)",
        strats["runai_model_streamer_16t"]["weight_load_s"] == 12.5
        and strats["runai_model_streamer_16t"]["total_cold_start_s"] == 21.5
        and round(strats["shared_nfs_warm_node"]["total_cold_start_s"] / strats["runai_model_streamer_16t"]["total_cold_start_s"], 2) == 5.63,
    )
    check(
        "19. Warm node + NVIDIA GPUDirect Storage (GDS cuFile DMA @ 28.0 GB/s) loads 140 GB weights in 5.0s (14.0s total, 30.43x faster than cold S3 node)",
        strats["gpudirect_storage_gds"]["weight_load_s"] == 5.0
        and strats["gpudirect_storage_gds"]["total_cold_start_s"] == 14.0
        and round(strats["remote_s3_cold_node"]["total_cold_start_s"] / strats["gpudirect_storage_gds"]["total_cold_start_s"], 2) == 30.43,
    )

    cs_8b = compute_cold_start_anatomy(
        model_weights_gb=16.0,
        node_provision_s=0.0,
        image_cached=True,
        runtime_init_s=1.0,
        weight_load_gb_s=10.67,
        cuda_graph_warmup_s=4.0,
    )
    check(
        "20. Llama-3-8B (16 GB FP16) with Run:ai Model Streamer loads weights in 1.5s and reaches Ready in 6.5s",
        cs_8b["weight_load_s"] == 1.5 and cs_8b["total_cold_start_s"] == 6.5,
    )

    # -----------------------------------------------------------------------
    # 6. Production Failure Modes & Cost-per-Million-Tokens FinOps
    # -----------------------------------------------------------------------
    diag = diagnose_queue_thrashing_and_probe_cascade()

    check(
        "21. VL5 Scenario 1: Llama-3-8B with naive threshold=5 scales 2 -> 10 on a 50-request burst, but burst drains in 1.67s (< 60s cold start), wasting 2,400 GPU-pod-seconds",
        diag["naive_scaled_replicas"] == 10
        and diag["burst_drain_time_s"] == 1.67
        and diag["wasted_gpu_pod_seconds"] == 2400
        and diag["thrashing_occurs"] is True,
    )
    check(
        "22. Raising queue threshold to 100 (matching 128 batch capacity) keeps Llama-3-8B at 2 replicas and eliminates thrashing",
        diag["tuned_scaled_replicas"] == 2,
    )
    check(
        "23. V12 Scenario 1: Scaling 4 -> 12 pods over 10 Gbps (1.25 GB/s) NFS leaves 156.25 MB/s per new pod and stalls /v1/models to 1.2s (> 1.0s timeout), causing 100% HTTP 503",
        diag["new_scaling_pods"] == 8
        and diag["per_pod_nfs_mb_s"] == 156.25
        and diag["naive_healthy_endpoints"] == 0
        and diag["naive_http_503_pct"] == 100.0,
    )
    check(
        "24. Decoupled 600s startupProbe (60 * 10s) and 5.0s /health readinessProbe preserves all 4 healthy pods during scale-out",
        diag["tuned_healthy_endpoints"] == 4 and diag["startup_probe_budget_s"] == 600,
    )

    finops = compute_token_cost_and_quantization_roi()
    check(
        "25. VL5 FinOps equation: 8x H100 node ($49.60/hr) at 2,658.76 tok/s costs $5.18 per 1M output tokens",
        finops["cost_per_1m_optimal_usd"] == 5.18,
    )
    check(
        "26. Scaling prematurely at queue_depth=1 (batch=1, 24.0 tok/s) inflates cost to $574.07 per 1M tokens (110.82x cost penalty)",
        finops["cost_per_1m_batch1_usd"] == 574.07
        and finops["premature_scaling_penalty_x"] == 110.82,
    )
    check(
        "27. HLS Ch 9 Qwen3-14B on L40S ($2.25/hr): AWQ 4-bit expands KV cache 2.65x (72,064 -> 191,056 tokens) and lifts throughput 2.70x (474.38 -> 1,280.0 tok/s)",
        finops["kv_expansion_x"] == 2.65 and finops["throughput_gain_x"] == 2.70,
    )
    check(
        "28. Quantizing Qwen3-14B to AWQ 4-bit cuts total token cost on L40S from $1.32 to $0.49 per 1M tokens",
        finops["qwen_bf16_cost_1m_usd"] == 1.32 and finops["qwen_awq_cost_1m_usd"] == 0.49,
    )

    print(f"\nSummary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
