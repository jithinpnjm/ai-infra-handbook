#!/usr/bin/env python3
"""Self-checking lab for Chapter 15.7: NVIDIA NIM and the NIM Operator."""

from __future__ import annotations
import sys
from nvidia_nim_operator import (
    NIMModelProfile,
    select_nim_model_profile,
    compute_nim_gpu_memory_and_replicas,
    evaluate_cold_start_vs_pvc_cache,
    evaluate_multi_lora_memory_savings,
    reconcile_nim_operator_pipeline,
    evaluate_nemo_microservices_metrics,
    evaluate_probes_and_canary_gates,
)


def run_lab() -> int:
    print("=== Chapter 15.7 Lab: NVIDIA NIM and the NIM Operator Verification ===")
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

    manifest_profiles = [
        NIMModelProfile(
            profile_id="tensorrt_llm-h100-fp8-tp1-latency",
            backend="tensorrt_llm",
            gpu_arch="H100",
            precision="fp8",
            tp_size=1,
            min_vram_gb_per_gpu=24.0,
            prebuilt_engine=True,
            lora_supported=False,
            mode="latency",
        ),
        NIMModelProfile(
            profile_id="tensorrt_llm-h100-fp8-tp2-throughput",
            backend="tensorrt_llm",
            gpu_arch="H100",
            precision="fp8",
            tp_size=2,
            min_vram_gb_per_gpu=40.0,
            prebuilt_engine=True,
            lora_supported=False,
            mode="throughput",
        ),
        NIMModelProfile(
            profile_id="tensorrt_llm-a100-bf16-tp1-lora",
            backend="tensorrt_llm",
            gpu_arch="A100",
            precision="bf16",
            tp_size=1,
            min_vram_gb_per_gpu=22.0,
            prebuilt_engine=True,
            lora_supported=True,
            mode="lora",
        ),
        NIMModelProfile(
            profile_id="vllm-generic-bf16-tp1-lora",
            backend="vllm",
            gpu_arch="generic",
            precision="bf16",
            tp_size=1,
            min_vram_gb_per_gpu=20.0,
            prebuilt_engine=False,
            lora_supported=True,
            mode="throughput",
        ),
        NIMModelProfile(
            profile_id="sglang-generic-bf16-tp1",
            backend="sglang",
            gpu_arch="generic",
            precision="bf16",
            tp_size=1,
            min_vram_gb_per_gpu=20.0,
            prebuilt_engine=False,
            lora_supported=False,
            mode="throughput",
        ),
    ]

    # 1. Hardware-Aware Model Profile Manifest Selection (`TensorRT-LLM > vLLM > SGLang`)
    sel_h100_tp2 = select_nim_model_profile(
        manifest_profiles,
        detected_gpu_arch="H100",
        detected_gpu_count=2,
        detected_vram_gb_per_gpu=80.0,
        prefer_mode="throughput",
    )
    check(
        "1. On 2x H100 80GB GPUs (throughput mode), NIM selects pre-built TensorRT-LLM FP8 TP=2 profile",
        sel_h100_tp2["selected_profile"] == "tensorrt_llm-h100-fp8-tp2-throughput"
        and sel_h100_tp2["backend"] == "tensorrt_llm"
        and sel_h100_tp2["prebuilt_engine"] is True,
    )

    sel_h100_tp1_lat = select_nim_model_profile(
        manifest_profiles,
        detected_gpu_arch="H100",
        detected_gpu_count=1,
        detected_vram_gb_per_gpu=80.0,
        prefer_mode="latency",
    )
    check(
        "2. On 1x H100 80GB GPU (latency mode), NIM selects pre-built TensorRT-LLM FP8 TP=1 latency profile",
        sel_h100_tp1_lat["selected_profile"] == "tensorrt_llm-h100-fp8-tp1-latency"
        and sel_h100_tp1_lat["tp_size"] == 1,
    )

    sel_l40s_fallback = select_nim_model_profile(
        manifest_profiles,
        detected_gpu_arch="L40S",
        detected_gpu_count=1,
        detected_vram_gb_per_gpu=48.0,
    )
    check(
        "3. On 1x L40S 48GB GPU without a pre-built L40S TRT-LLM engine, NIM falls back to vLLM before SGLang (TensorRT-LLM > vLLM > SGLang)",
        sel_l40s_fallback["selected_profile"] == "vllm-generic-bf16-tp1-lora"
        and sel_l40s_fallback["backend"] == "vllm"
        and sel_l40s_fallback["selection_reason"] == "vllm_fallback_profile",
    )

    sel_h100_lora = select_nim_model_profile(
        manifest_profiles,
        detected_gpu_arch="H100",
        detected_gpu_count=1,
        detected_vram_gb_per_gpu=80.0,
        require_lora=True,
    )
    check(
        "4. When LoRA is required on H100 and H100 FP8 profiles lack LoRA, NIM selects the LoRA-enabled vLLM profile",
        sel_h100_lora["selected_profile"] == "vllm-generic-bf16-tp1-lora"
        and sel_h100_lora["lora_supported"] is True,
    )

    sel_override_ok = select_nim_model_profile(
        manifest_profiles,
        detected_gpu_arch="A100",
        detected_gpu_count=1,
        detected_vram_gb_per_gpu=40.0,
        explicit_profile_override="tensorrt_llm-a100-bf16-tp1-lora",
    )
    check(
        "5. Explicit NIM_MODEL_PROFILE override ('tensorrt_llm-a100-bf16-tp1-lora') succeeds on 1x A100 40GB",
        sel_override_ok["selected_profile"] == "tensorrt_llm-a100-bf16-tp1-lora"
        and sel_override_ok["selection_reason"] == "explicit_override"
        and sel_override_ok["hardware_compatible"] is True,
    )

    sel_override_bad = select_nim_model_profile(
        manifest_profiles,
        detected_gpu_arch="A100",
        detected_gpu_count=1,
        detected_vram_gb_per_gpu=40.0,
        explicit_profile_override="tensorrt_llm-h100-fp8-tp2-throughput",
    )
    check(
        "6. Explicit NIM_MODEL_PROFILE override for H100 TP=2 on a 1x A100 node is rejected with hardware mismatch",
        sel_override_bad["hardware_compatible"] is False
        and sel_override_bad["selection_reason"] == "override_hardware_mismatch",
    )

    # 2. GPU Memory Sizing & Replica Planning (Volume 14 Lab 01 `llama2-7b` / `8B` on A100 40GB)
    sizing = compute_nim_gpu_memory_and_replicas(
        model_size_gb=14.0,
        framework_overhead_gb=2.0,
        activations_per_req_gb=4.0,
        safety_headroom_gb=2.0,
        gpu_available_gb=40.0,
        target_qps=100.0,
        requests_per_gpu_qps=50.0,
    )
    check(
        "7. V14 Lab 01 sizing: 14 GB weights + 2 GB framework + 4 GB activations + 2 GB safety = 22.0 GB required on 40.0 GB A100 (18.0 GB margin)",
        sizing["total_required_gpu_memory_gb"] == 22.0
        and sizing["free_margin_gb"] == 18.0
        and sizing["fits_on_gpu"] is True,
    )
    check(
        "8. V14 Lab 01 throughput sizing: 100 req/sec target at 50 req/sec per GPU requires 2 replicas (2 GPUs)",
        sizing["replicas_needed"] == 2,
    )

    sizing_70b_1gpu = compute_nim_gpu_memory_and_replicas(
        model_size_gb=140.0,
        framework_overhead_gb=4.0,
        activations_per_req_gb=8.0,
        safety_headroom_gb=4.0,
        gpu_available_gb=80.0,
    )
    check(
        "9. Llama-3-70B in BF16 (140 GB weights, 156 GB total) exceeds a single 80 GB GPU and fails fit check",
        sizing_70b_1gpu["fits_on_gpu"] is False
        and sizing_70b_1gpu["total_required_gpu_memory_gb"] == 156.0,
    )

    # 3. Cold-Start Problem vs Persistent Volume Model Caching (`NIM_CACHE_PATH`, Volume 14 Ch. 4)
    cold = evaluate_cold_start_vs_pvc_cache(
        model_weights_gb=140.0,
        ngc_download_mb_s=116.67,
        nvme_cache_read_gb_s=3.5,
        engine_init_s=5.0,
    )
    check(
        "10. Generic Nginx container (20 MB) starts in 2.0 s, whereas 140 GB Llama-3-70B uncached NGC download takes 1200.0 s (20.08 min)",
        cold["nginx_image_mb"] == 20.0
        and cold["nginx_startup_s"] == 2.0
        and cold["uncached_download_s"] == 1200.0
        and cold["uncached_minutes"] >= 20.0,
    )
    check(
        "11. Mounting a fast NVMe PersistentVolume (NIM_CACHE_PATH=/model_cache at 3.5 GB/s) cuts 140 GB startup to 45.0 s (26.78x faster)",
        cold["cached_read_s"] == 40.0
        and cold["cached_total_s"] == 45.0
        and cold["startup_speedup_x"] == 26.78,
    )

    # 4. Multi-LoRA Dynamic Adapter Serving (`NIM_PEFT_SOURCE`)
    lora = evaluate_multi_lora_memory_savings(
        num_fine_tuned_models=10,
        base_model_weights_gb=16.0,
        runtime_overhead_gb=2.0,
        lora_adapter_size_mb=64.0,
        max_gpu_loras=8,
        max_cpu_loras=32,
    )
    check(
        "12. Serving 10 dedicated 8B fine-tuned NIM pods requires 10 * 18.0 GB = 180.0 GB VRAM across 10 GPUs",
        lora["dedicated_per_pod_gb"] == 18.0
        and lora["dedicated_total_vram_gb"] == 180.0
        and lora["dedicated_gpus_required"] == 10,
    )
    check(
        "13. Multi-LoRA NIM serves 10 domain adapters using 16.0 GB base + 2.0 GB runtime + 0.512 GB GPU LoRA pool (8 * 64 MB) = 18.512 GB (89.72% VRAM reduction)",
        lora["gpu_lora_pool_gb"] == 0.512
        and lora["multi_lora_total_vram_gb"] == 18.512
        and lora["vram_reduction_pct"] == 89.72,
    )

    # 5. Kubernetes NIM Operator (`NIMCache`, `NIMService`, `NIMPipeline`) Reconciliation
    op_bad_token = reconcile_nim_operator_pipeline(ngc_secret_valid=False)
    check(
        "14. Invalid NGC_API_KEY causes NIMCache Job to fail with 401 Unauthorized and holds NIMService in PendingCache (0 replicas)",
        op_bad_token["nim_cache_state"] == "Failed"
        and "401 Unauthorized" in str(op_bad_token["nim_cache_reason"])
        and op_bad_token["nim_service_state"] == "PendingCache"
        and op_bad_token["active_replicas"] == 0,
    )

    op_small_pvc = reconcile_nim_operator_pipeline(ngc_secret_valid=True, pvc_storage_gb=10, required_cache_gb=20)
    check(
        "15. Under-provisioned PVC (10Gi < 20Gi required) fails NIMCache validation before serving pods schedule",
        op_small_pvc["nim_cache_state"] == "Failed"
        and op_small_pvc["active_replicas"] == 0,
    )

    op_scale_out = reconcile_nim_operator_pipeline(
        ngc_secret_valid=True,
        pvc_storage_gb=50,
        required_cache_gb=20,
        min_replicas=2,
        max_replicas=10,
        current_queue_depth=25,
        current_p95_latency_ms=210.0,
    )
    check(
        "16. Valid NIMCache (50Gi RWX PVC) transitions NIMCache, NIMService, and 3-service NIMPipeline to Ready",
        op_scale_out["nim_cache_state"] == "Ready"
        and op_scale_out["nim_service_state"] == "Ready"
        and op_scale_out["nim_pipeline_state"] == "Ready"
        and len(op_scale_out["pipeline_services"]) == 3,
    )
    check(
        "17. Queue depth 25 (> 10) with p95 latency 210.0 ms (> 200.0 ms SLO) triggers HPA SCALE_OUT from 2 to 3 replicas",
        op_scale_out["scaling_decision"] == "SCALE_OUT"
        and op_scale_out["active_replicas"] == 3,
    )

    op_warn = reconcile_nim_operator_pipeline(
        current_queue_depth=15,
        current_p95_latency_ms=175.0,
        min_replicas=3,
    )
    check(
        "18. Queue depth 15 (> 10) with p95 latency 175.0 ms (150-200 ms band) enters WARN_PREPARE_SCALE state",
        op_warn["scaling_decision"] == "WARN_PREPARE_SCALE"
        and op_warn["active_replicas"] == 3,
    )

    op_ok = reconcile_nim_operator_pipeline(
        current_queue_depth=12,
        current_p95_latency_ms=120.0,
        min_replicas=3,
    )
    check(
        "19. Queue depth 12 with p95 latency 120.0 ms (< 150 ms) meets SLO without scaling (SLO_MET_NO_SCALE)",
        op_ok["scaling_decision"] == "SLO_MET_NO_SCALE"
        and op_ok["active_replicas"] == 3,
    )

    # 6. NeMo Microservices (`NemoGuardrails`, `NemoCustomizer`, `NemoEvaluator`, V14 Ch. 5, Ch. 6, Lab 03)
    nemo = evaluate_nemo_microservices_metrics()
    gr = nemo["guardrails"]
    ce = nemo["customizer_evaluator"]
    check(
        "20. V14 Ch. 6 NemoGuardrails latency budget: 45 ms base + 15 ms input + 30 ms intent + 100 ms RAG + 50 ms output + 10 ms audit = 250.0 ms (5.56x)",
        gr["total_guarded_ms"] == 250.0
        and gr["latency_multiplier_x"] == 5.56,
    )
    check(
        "21. V14 Lab 03 NemoEvaluator metrics: test perplexity drops 18.7 -> 15.2 (18.7% reduction), ROUGE-1 0.31 -> 0.35 (+12.9%), BLEU 0.24 -> 0.28 (+16.7%)",
        ce["perplexity_reduction_pct"] == 18.7
        and ce["rouge1_gain_pct"] == 12.9
        and ce["bleu_gain_pct"] == 16.7
        and ce["status"] == "PASSED",
    )

    # 7. Kubernetes Probes & Canary Rollout Circuit Breaker (Volume 14 Ch. 4 & Lab 01)
    probe_ok = evaluate_probes_and_canary_gates(
        model_load_time_s=180.0,
        startup_period_s=10,
        startup_failure_threshold=60,
        liveness_initial_delay_s=60,
        liveness_period_s=30,
        liveness_failure_threshold=3,
        baseline_p95_ms=180.0,
        measured_canary_p95_ms=195.0,
        measured_gpu_util_pct=68.0,
        deterministic_match=True,
    )
    check(
        "22. V14 Ch. 4 startupProbe (60 * 10 s = 600 s max boot window) and livenessProbe (3 * 30 s = 90 s window) protect 180 s model load",
        probe_ok["max_startup_window_s"] == 600
        and probe_ok["liveness_window_s"] == 90
        and probe_ok["startup_survives"] is True,
    )
    check(
        "23. Canary revision at p95=195.0 ms (<= 200 ms gate vs 180 ms baseline, +8.3%), GPU util 68% (> 50%), and deterministic match is promoted",
        probe_ok["canary_passed"] is True
        and probe_ok["canary_action"] == "PROMOTE_TO_PRODUCTION",
    )

    canary_warn = evaluate_probes_and_canary_gates(
        baseline_p95_ms=180.0,
        measured_canary_p95_ms=252.0,
        measured_gpu_util_pct=65.0,
        deterministic_match=True,
    )
    check(
        "24. V14 Ch. 4 canary latency regression (+40%, p95=252.0 ms >= 250 ms warning threshold) pauses canary rollout",
        canary_warn["regression_pct"] == 40.0
        and canary_warn["canary_passed"] is False
        and canary_warn["canary_action"] == "PAUSE_CANARY_WARNING",
    )

    canary_rollback = evaluate_probes_and_canary_gates(
        baseline_p95_ms=180.0,
        measured_canary_p95_ms=305.0,
        measured_gpu_util_pct=65.0,
        deterministic_match=True,
    )
    check(
        "25. Critical canary latency regression (p95=305.0 ms >= 300 ms critical threshold) triggers AUTOMATIC_ROLLBACK (helm rollback)",
        canary_rollback["canary_passed"] is False
        and canary_rollback["canary_action"] == "AUTOMATIC_ROLLBACK",
    )

    print(f"Summary: {passed} passed, {total - passed} failed")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_lab())
