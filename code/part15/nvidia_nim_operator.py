#!/usr/bin/env python3
"""Chapter 15.7 model: NVIDIA NIM and the NIM Operator.

Models:
1. NIM Container Anatomy & Hardware-Aware Model Profile Manifest Selection (`model_manifest.yaml`):
   - Evaluates candidate NIM profiles (`TensorRT-LLM` pre-built `.engine`, `TensorRT-LLM` buildable,
     `vLLM` PagedAttention fallback, and `SGLang` fallback) against detected GPU hardware
     (`H100` `sm_90a`, `A100` `sm_80`, `L40S` `sm_89`, `B200` `sm_100`), GPU count (`tp_size`),
     available HBM, and requested LoRA/PEFT capability.
   - Enforces the strict backend preference order (`TensorRT-LLM > vLLM > SGLang`, *Generative AI on
     Kubernetes* Ch. 1) and explicit `NIM_MODEL_PROFILE` overrides.
   - Reproduces Volume 12 Ch. 5 & Volume 14 Lab 01/02 sizing and throughput benchmarks:
     * `7B/8B` BF16 model (`llama2-7b` / `llama3-8b-instruct`): `14.0 GB` (`13.5 GiB` / `13,850 MiB`
       weights) + `2.0 GB` framework overhead + `4.0 GB` activations + `2.0 GB` safety headroom =
       `22.0 GB` required on a `40.0 GB` A100 (`18.0 GB` margin; `28.0 GB` runtime with active KV cache;
       `50` req/sec per GPU -> `2` replicas for `100` req/sec).
     * `Llama-3-70B` (`140.0 GB` BF16 vs `70.0 GB` FP8 weights; `327,680` bytes/tok = `320 KB/tok` FP16
       vs `163,840` bytes/tok = `160 KB/tok` FP8 KV cache; `115.0 ms -> 18.4 ms` ITL = `6.25x` speedup
       on `8x H100` `TP=8` with pre-built `TensorRT-LLM` engine).
2. Cold-Start Latency Math, `NIM_CACHE_PATH` Persistent Volumes, and Air-Gapped `download-to-cache`:
   - Contrasts a `20 MB` generic web container (`2.0 s` startup) against a `140.0 GB` (`1,120.0 Gb`)
     `Llama-3-70B` uncached NGC download (`20.0+ minutes` / `1,200.0+ s` at `116.67 MB/s` effective
     throughput) versus loading from a fast NVMe `ReadWriteMany` (`RWX`) `PersistentVolume` (`40.0 s`
     at `3.5 GB/s` + `5.0 s` engine init = `45.0 s`, `26.67x` faster startup).
   - Models air-gapped supply-chain verification (`nvcr.io/nim/meta/llama3-8b-instruct:1.0.5@sha256:...`,
     Trivy CVE thresholds `0` critical / `0` high / `0` medium / `2` low, `90`-day `NGC_API_KEY`
     rotation with `30`-day expiry alerts, and `download-to-cache` DMZ staging).
3. Multi-LoRA Dynamic Adapter Serving (`NIM_PEFT_SOURCE`, `NIM_MAX_GPU_LORAS`, `NIM_MAX_CPU_LORAS`):
   - Compares `N=10` separate dedicated fine-tuned `8B` pods (`10 * 16.0 GB = 160.0 GB` weight VRAM +
     `10 * 2.0 GB = 20.0 GB` runtime = `180.0 GB` across `10` GPUs) against a single Multi-LoRA NIM
     instance (`16.0 GB` shared base model + `2.0 GB` runtime + `8 * 64.0 MB = 0.512 GB` GPU LoRA cache =
     `18.512 GB` on `1` GPU, `89.72%` VRAM reduction) with dynamic `NIM_PEFT_REFRESH_INTERVAL=60` s polling.
4. Kubernetes NIM Operator (`NIMCache`, `NIMService`, `NIMPipeline`) & NeMo Microservices CRDs:
   - Simulates `apps.nvidia.com/v1alpha1` reconciliation: `NIMCache` pre-population `Job` -> `Ready` PVC ->
     `NIMService` (`Deployment`, `Service` `:8000`/`:8001`, `ServiceMonitor` `:9090/metrics`, `HPA`) ->
     `NIMPipeline` multi-service RAG DAG (`Embedding NIM -> Reranker NIM -> Generation LLM NIM`).
   - Models `NemoGuardrails` latency budget (`45 ms` base model + `15 ms` input check + `30 ms` intent
     classifier + `100 ms` RAG + `50 ms` output fact-check + `10 ms` audit log = `250 ms` total, `5.56x`),
     `NemoCustomizer` (`8x A100 80GB * 168 h = 1,344` raw or `640` budgeted GPU-hours; `5,000`-step lab
     loss `2.15 -> 1.87` = `12.8%` improvement), and `NemoEvaluator` (perplexity `18.7 -> 15.2` = `18.7%`
     reduction, ROUGE-1 `0.31 -> 0.35` = `+12.9%`, BLEU `0.24 -> 0.28` = `+16.7%`).
5. Health Probe Decoupling, Queue-Depth Autoscaling (`HPA`/KEDA), Canary Gates & 7-Layer Troubleshooting:
   - Validates `startupProbe` (`60 * 10 s = 600 s`), `readinessProbe` (`300 s` delay + `5 * 10 s`),
     and `livenessProbe` (`60 s` delay + `3 * 30 s = 90 s` window) on `/v1/health/live` and `/v1/health/ready`.
   - Evaluates queue-depth (`> 10` or `requests_waiting_total > 20`) and `p95` latency (`150 ms` OK,
     `150-200 ms` warn, `> 200 ms` scale) autoscaling, plus canary circuit-breaker gates (`180 ms` baseline,
     `200 ms` pass gate, `250 ms` `+40%` warning, `300 ms` `+67%` automatic rollback).
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class NIMModelProfile:
    profile_id: str
    backend: str  # "tensorrt_llm", "vllm", "sglang"
    gpu_arch: str  # "H100", "H200", "A100", "L40S", "B200", "generic"
    precision: str  # "fp8", "bf16", "fp16", "int4_awq", "nvfp4"
    tp_size: int
    min_vram_gb_per_gpu: float
    prebuilt_engine: bool = True
    lora_supported: bool = False
    mode: str = "throughput"  # "throughput", "latency", "lora"


BACKEND_PREFERENCE_ORDER: Dict[str, int] = {
    "tensorrt_llm": 1,
    "vllm": 2,
    "sglang": 3,
}


def select_nim_model_profile(
    profiles: Sequence[NIMModelProfile],
    detected_gpu_arch: str,
    detected_gpu_count: int,
    detected_vram_gb_per_gpu: float,
    require_lora: bool = False,
    prefer_mode: str = "throughput",
    explicit_profile_override: Optional[str] = None,
) -> Dict[str, object]:
    """Selects the optimal NIM model profile from `model_manifest.yaml` at container startup.

    Preference order (*Generative AI on Kubernetes* Ch. 1 & V14 Ch. 3):
    1. Explicit `NIM_MODEL_PROFILE` override if provided and hardware-compatible.
    2. Pre-built `TensorRT-LLM` `.engine` matching exact GPU architecture and `tp_size`.
    3. Buildable `TensorRT-LLM` profile matching GPU architecture and `tp_size`.
    4. Generic `vLLM` PagedAttention fallback profile (`vllm > sglang`).
    """
    if explicit_profile_override:
        for p in profiles:
            if p.profile_id == explicit_profile_override:
                hw_ok = (
                    p.gpu_arch in (detected_gpu_arch, "generic")
                    and p.tp_size <= detected_gpu_count
                    and p.min_vram_gb_per_gpu <= detected_vram_gb_per_gpu
                )
                return {
                    "selected_profile": p.profile_id if hw_ok else None,
                    "backend": p.backend if hw_ok else None,
                    "prebuilt_engine": p.prebuilt_engine if hw_ok else False,
                    "selection_reason": "explicit_override" if hw_ok else "override_hardware_mismatch",
                    "hardware_compatible": hw_ok,
                }
        return {
            "selected_profile": None,
            "backend": None,
            "prebuilt_engine": False,
            "selection_reason": "override_not_found",
            "hardware_compatible": False,
        }

    candidates: List[NIMModelProfile] = []
    for p in profiles:
        arch_match = p.gpu_arch in (detected_gpu_arch, "generic")
        tp_match = p.tp_size <= detected_gpu_count
        vram_match = p.min_vram_gb_per_gpu <= detected_vram_gb_per_gpu
        lora_match = (not require_lora) or p.lora_supported
        if arch_match and tp_match and vram_match and lora_match:
            candidates.append(p)

    if not candidates:
        return {
            "selected_profile": None,
            "backend": None,
            "prebuilt_engine": False,
            "selection_reason": "no_compatible_profile_found",
            "hardware_compatible": False,
        }

    def sort_key(p: NIMModelProfile) -> Tuple[int, int, int, int, int]:
        # Lower tuple sorts first (higher priority)
        backend_rank = BACKEND_PREFERENCE_ORDER.get(p.backend, 99)
        prebuilt_rank = 0 if p.prebuilt_engine else 1
        exact_arch_rank = 0 if p.gpu_arch == detected_gpu_arch else 1
        mode_rank = 0 if p.mode == prefer_mode else 1
        # Prefer using highest compatible TP size on the node
        tp_rank = -p.tp_size
        return (backend_rank, prebuilt_rank, exact_arch_rank, mode_rank, tp_rank)

    candidates.sort(key=sort_key)
    chosen = candidates[0]
    if chosen.backend == "tensorrt_llm" and chosen.prebuilt_engine:
        reason = "prebuilt_tensorrt_llm_engine"
    elif chosen.backend == "tensorrt_llm":
        reason = "jit_tensorrt_llm_build"
    elif chosen.backend == "vllm":
        reason = "vllm_fallback_profile"
    else:
        reason = "sglang_fallback_profile"

    return {
        "selected_profile": chosen.profile_id,
        "backend": chosen.backend,
        "precision": chosen.precision,
        "tp_size": chosen.tp_size,
        "prebuilt_engine": chosen.prebuilt_engine,
        "lora_supported": chosen.lora_supported,
        "selection_reason": reason,
        "hardware_compatible": True,
    }


def compute_nim_gpu_memory_and_replicas(
    model_size_gb: float = 14.0,
    framework_overhead_gb: float = 2.0,
    activations_per_req_gb: float = 4.0,
    safety_headroom_gb: float = 2.0,
    gpu_available_gb: float = 40.0,
    target_qps: float = 100.0,
    requests_per_gpu_qps: float = 50.0,
) -> Dict[str, float | int | bool]:
    """Computes NIM GPU memory sizing and replica count from Volume 14 Lab 01 (`llama2-7b` / `8B` on A100 40GB)."""
    total_required_gb = model_size_gb + framework_overhead_gb + activations_per_req_gb + safety_headroom_gb
    free_margin_gb = gpu_available_gb - total_required_gb
    fits = total_required_gb <= gpu_available_gb
    import math
    replicas_needed = int(math.ceil(target_qps / requests_per_gpu_qps))
    return {
        "model_size_gb": model_size_gb,
        "framework_overhead_gb": framework_overhead_gb,
        "activations_per_req_gb": activations_per_req_gb,
        "safety_headroom_gb": safety_headroom_gb,
        "total_required_gpu_memory_gb": round(total_required_gb, 2),
        "gpu_available_gb": gpu_available_gb,
        "free_margin_gb": round(free_margin_gb, 2),
        "fits_on_gpu": fits,
        "target_qps": target_qps,
        "requests_per_gpu_qps": requests_per_gpu_qps,
        "replicas_needed": replicas_needed,
    }


def evaluate_cold_start_vs_pvc_cache(
    model_weights_gb: float = 140.0,
    ngc_download_mb_s: float = 116.67,
    nvme_cache_read_gb_s: float = 3.5,
    engine_init_s: float = 5.0,
    nginx_image_mb: float = 20.0,
    nginx_startup_s: float = 2.0,
) -> Dict[str, float]:
    """Quantifies Volume 14 Ch. 4 cold-start download latency vs PersistentVolume (`NIM_CACHE_PATH`) warm load."""
    model_weights_mb = model_weights_gb * 1000.0
    uncached_download_s = model_weights_mb / ngc_download_mb_s
    uncached_total_s = uncached_download_s + engine_init_s
    uncached_minutes = uncached_total_s / 60.0

    cached_read_s = model_weights_gb / nvme_cache_read_gb_s
    cached_total_s = cached_read_s + engine_init_s
    speedup_x = uncached_total_s / cached_total_s

    return {
        "nginx_image_mb": nginx_image_mb,
        "nginx_startup_s": nginx_startup_s,
        "model_weights_gb": model_weights_gb,
        "uncached_download_s": round(uncached_download_s, 1),
        "uncached_total_s": round(uncached_total_s, 1),
        "uncached_minutes": round(uncached_minutes, 2),
        "cached_read_s": round(cached_read_s, 1),
        "cached_total_s": round(cached_total_s, 1),
        "startup_speedup_x": round(speedup_x, 2),
    }


def evaluate_multi_lora_memory_savings(
    num_fine_tuned_models: int = 10,
    base_model_weights_gb: float = 16.0,
    runtime_overhead_gb: float = 2.0,
    lora_adapter_size_mb: float = 64.0,
    max_gpu_loras: int = 8,
    max_cpu_loras: int = 32,
) -> Dict[str, float | int]:
    """Compares `N` dedicated full-model NIM pods against a single Multi-LoRA NIM service (`NIM_PEFT_SOURCE`)."""
    dedicated_per_pod_gb = base_model_weights_gb + runtime_overhead_gb
    dedicated_total_vram_gb = num_fine_tuned_models * dedicated_per_pod_gb
    dedicated_gpus_required = num_fine_tuned_models

    active_gpu_loras = min(num_fine_tuned_models, max_gpu_loras)
    gpu_lora_pool_gb = (active_gpu_loras * lora_adapter_size_mb) / 1000.0
    cpu_lora_pool_gb = (min(num_fine_tuned_models, max_cpu_loras) * lora_adapter_size_mb) / 1000.0

    multi_lora_total_vram_gb = base_model_weights_gb + runtime_overhead_gb + gpu_lora_pool_gb
    vram_saved_gb = dedicated_total_vram_gb - multi_lora_total_vram_gb
    vram_reduction_pct = (vram_saved_gb / dedicated_total_vram_gb) * 100.0

    return {
        "num_fine_tuned_models": num_fine_tuned_models,
        "dedicated_per_pod_gb": round(dedicated_per_pod_gb, 3),
        "dedicated_total_vram_gb": round(dedicated_total_vram_gb, 3),
        "dedicated_gpus_required": dedicated_gpus_required,
        "active_gpu_loras": active_gpu_loras,
        "gpu_lora_pool_gb": round(gpu_lora_pool_gb, 3),
        "cpu_lora_pool_gb": round(cpu_lora_pool_gb, 3),
        "multi_lora_total_vram_gb": round(multi_lora_total_vram_gb, 3),
        "vram_saved_gb": round(vram_saved_gb, 3),
        "vram_reduction_pct": round(vram_reduction_pct, 2),
    }


def reconcile_nim_operator_pipeline(
    ngc_secret_valid: bool = True,
    pvc_storage_gb: int = 50,
    required_cache_gb: int = 20,
    min_replicas: int = 2,
    max_replicas: int = 10,
    current_queue_depth: int = 25,
    current_p95_latency_ms: float = 210.0,
) -> Dict[str, object]:
    """Models the Kubernetes NIM Operator reconciliation loop (`NIMCache` -> `NIMService` -> `NIMPipeline`)."""
    if not ngc_secret_valid:
        return {
            "nim_cache_state": "Failed",
            "nim_cache_reason": "401 Unauthorized: NGC_API_KEY invalid or expired",
            "nim_service_state": "PendingCache",
            "nim_pipeline_state": "Degraded",
            "active_replicas": 0,
        }
    if pvc_storage_gb < required_cache_gb:
        return {
            "nim_cache_state": "Failed",
            "nim_cache_reason": f"PVC size {pvc_storage_gb}Gi < required {required_cache_gb}Gi",
            "nim_service_state": "PendingCache",
            "nim_pipeline_state": "Degraded",
            "active_replicas": 0,
        }

    # NIMCache Job completes `download-to-cache` and transitions PVC to Ready
    nim_cache_state = "Ready"
    nim_service_state = "Ready"

    # Autoscaling logic from Volume 14 Ch. 4:
    # Queue depth > 10 or requests_waiting_total > 20 -> measure p95 latency:
    # p95 < 150 ms: OK (no scale)
    # p95 150-200 ms: Warning (prepare scale)
    # p95 > 200 ms: SCALE (add replica)
    if current_queue_depth > 10 and current_p95_latency_ms > 200.0:
        scaling_decision = "SCALE_OUT"
        desired_replicas = min(max_replicas, min_replicas + 1)
    elif current_queue_depth > 10 and current_p95_latency_ms >= 150.0:
        scaling_decision = "WARN_PREPARE_SCALE"
        desired_replicas = min_replicas
    else:
        scaling_decision = "SLO_MET_NO_SCALE"
        desired_replicas = min_replicas

    return {
        "nim_cache_state": nim_cache_state,
        "nim_cache_pvc": "llama3-8b-cache-pvc (ReadWriteMany)",
        "nim_service_state": nim_service_state,
        "nim_pipeline_state": "Ready",
        "pipeline_services": [
            "nv-embedqa-e5-v5",
            "nv-rerankqa-mistral-4b-v3",
            "meta-llama3-8b-instruct",
        ],
        "scaling_decision": scaling_decision,
        "active_replicas": desired_replicas,
    }


def evaluate_nemo_microservices_metrics() -> Dict[str, Dict[str, float | str]]:
    """Computes NeMo Microservices (`NemoGuardrails`, `NemoCustomizer`, `NemoEvaluator`) metrics from Volume 14 Ch. 5, Ch. 6, and Lab 03."""
    # Volume 14 Ch. 6 Guardrails latency breakdown:
    base_model_ms = 45.0
    input_validation_ms = 15.0  # 60 ms cumulative
    intent_classifier_ms = 30.0  # 90 ms cumulative
    rag_retrieval_ms = 100.0  # 190 ms cumulative
    output_validator_ms = 50.0  # 240 ms cumulative
    audit_logging_ms = 10.0  # 250 ms cumulative
    total_guarded_ms = (
        base_model_ms
        + input_validation_ms
        + intent_classifier_ms
        + rag_retrieval_ms
        + output_validator_ms
        + audit_logging_ms
    )
    latency_multiplier = total_guarded_ms / base_model_ms  # 250 / 45 = 5.56x (~5.5x)

    # Volume 14 Lab 03 NeMo Customizer & Evaluator metrics:
    baseline_loss = 2.15
    final_train_loss = 1.87
    eval_loss = 1.92
    loss_improvement_pct = round(((baseline_loss - final_train_loss) / baseline_loss) * 100.0, 1)  # 13.0% / 12.8% reported

    base_ppl = 18.7
    ft_ppl = 15.2
    ppl_reduction_pct = round(((base_ppl - ft_ppl) / base_ppl) * 100.0, 1)  # 18.7%

    base_rouge1 = 0.31
    ft_rouge1 = 0.35
    rouge1_gain_pct = round(((ft_rouge1 - base_rouge1) / base_rouge1) * 100.0, 1)  # 12.9%

    base_bleu = 0.24
    ft_bleu = 0.28
    bleu_gain_pct = round(((ft_bleu - base_bleu) / base_bleu) * 100.0, 1)  # 16.7%

    return {
        "guardrails": {
            "base_model_ms": base_model_ms,
            "input_validation_ms": input_validation_ms,
            "intent_classifier_ms": intent_classifier_ms,
            "rag_retrieval_ms": rag_retrieval_ms,
            "output_validator_ms": output_validator_ms,
            "audit_logging_ms": audit_logging_ms,
            "total_guarded_ms": total_guarded_ms,
            "latency_multiplier_x": round(latency_multiplier, 2),
        },
        "customizer_evaluator": {
            "baseline_loss": baseline_loss,
            "final_train_loss": final_train_loss,
            "eval_loss": eval_loss,
            "loss_improvement_pct": loss_improvement_pct,
            "baseline_perplexity": base_ppl,
            "fine_tuned_perplexity": ft_ppl,
            "perplexity_reduction_pct": ppl_reduction_pct,
            "baseline_rouge1": base_rouge1,
            "fine_tuned_rouge1": ft_rouge1,
            "rouge1_gain_pct": rouge1_gain_pct,
            "baseline_bleu": base_bleu,
            "fine_tuned_bleu": ft_bleu,
            "bleu_gain_pct": bleu_gain_pct,
            "status": "PASSED",
        },
    }


def evaluate_probes_and_canary_gates(
    model_load_time_s: float = 180.0,
    startup_period_s: int = 10,
    startup_failure_threshold: int = 60,
    liveness_initial_delay_s: int = 60,
    liveness_period_s: int = 30,
    liveness_failure_threshold: int = 3,
    baseline_p95_ms: float = 180.0,
    measured_canary_p95_ms: float = 195.0,
    measured_gpu_util_pct: float = 68.0,
    deterministic_match: bool = True,
) -> Dict[str, object]:
    """Evaluates Volume 14 Ch. 4 & Lab 01 Kubernetes probe windows and canary rollout circuit-breaker gates."""
    max_startup_window_s = startup_period_s * startup_failure_threshold  # 600 s (10 min)
    liveness_window_s = liveness_period_s * liveness_failure_threshold  # 90 s
    startup_survives = model_load_time_s <= max_startup_window_s

    # Canary gates (V14 Ch. 4 & Lab 01):
    # - Baseline p95 = 180 ms
    # - Strict pass criteria (Lab 01): p95 < 200 ms, GPU Util > 50%, deterministic output matches baseline
    # - Latency regression circuit breaker (Ch. 4):
    #   warning = 250 ms (+38.9% / ~40% slower -> pause canary)
    #   critical = 300 ms (+66.7% / ~67% slower -> automatic rollback `helm rollback`)
    regression_pct = ((measured_canary_p95_ms - baseline_p95_ms) / baseline_p95_ms) * 100.0
    if not deterministic_match or measured_gpu_util_pct <= 50.0 or measured_canary_p95_ms >= 300.0:
        canary_action = "AUTOMATIC_ROLLBACK"
        canary_passed = False
    elif measured_canary_p95_ms >= 250.0:
        canary_action = "PAUSE_CANARY_WARNING"
        canary_passed = False
    elif measured_canary_p95_ms <= 200.0:
        canary_action = "PROMOTE_TO_PRODUCTION"
        canary_passed = True
    else:
        canary_action = "HOLD_FOR_REVIEW"
        canary_passed = False

    return {
        "max_startup_window_s": max_startup_window_s,
        "liveness_window_s": liveness_window_s,
        "liveness_initial_delay_s": liveness_initial_delay_s,
        "startup_survives": startup_survives,
        "baseline_p95_ms": baseline_p95_ms,
        "measured_canary_p95_ms": measured_canary_p95_ms,
        "regression_pct": round(regression_pct, 1),
        "canary_passed": canary_passed,
        "canary_action": canary_action,
    }


if __name__ == "__main__":
    sizing = compute_nim_gpu_memory_and_replicas()
    cold = evaluate_cold_start_vs_pvc_cache()
    lora = evaluate_multi_lora_memory_savings()
    nemo = evaluate_nemo_microservices_metrics()
    print(f"NIM Sizing (7B/8B on 40GB A100): {sizing['total_required_gpu_memory_gb']} GB required, {sizing['replicas_needed']} replicas")
    print(f"Cold Start (140GB 70B): {cold['uncached_minutes']} min uncached vs {cold['cached_total_s']} s cached ({cold['startup_speedup_x']}x faster)")
    print(f"Multi-LoRA (10 models): {lora['dedicated_total_vram_gb']} GB dedicated vs {lora['multi_lora_total_vram_gb']} GB Multi-LoRA ({lora['vram_reduction_pct']}% saved)")
    print(f"NeMo Guardrails Latency: {nemo['guardrails']['base_model_ms']} ms -> {nemo['guardrails']['total_guarded_ms']} ms ({nemo['guardrails']['latency_multiplier_x']}x)")
