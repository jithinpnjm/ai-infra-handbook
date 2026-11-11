#!/usr/bin/env python3
"""Production LLM serving stack and reliability models for Chapter 15.16.

Covers:
1. 9-stage inference request path latency, Gateway API Inference Extension (EPP),
   multi-model/multi-engine routing (`ModelRouter`), and Ray Serve LRU multiplexing.
2. Dual Token Bucket rate limiting (RPM and TPM), semantic caching, Anthropic/RAG
   prefix caching savings, prompt compression, and NeMo Guardrails latency budget.
3. Canary rollouts (`CanaryDeployment`), A/B consistent hashing, shadow traffic,
   SSE streaming token chunking, TCP_NODELAY, and graceful connection draining.
4. Kubernetes 3-probe (`startupProbe`, `readinessProbe`, `livenessProbe`) validation,
   probe-induced cascading outage simulation, and XID 62 zombie pod blackhole math.
5. Circuit breaker state machine (`CLOSED` / `OPEN` / `HALF_OPEN`), fallback model
   cascades, recompute-only preemption (`--swap-space 0` on vLLM before v0.18) vs PCIe thrashing, and Spot + On-Demand pool economics.
6. OpenTelemetry 6-span trace waterfall decomposition, CPU vs GPU bottleneck triage,
   Prometheus SLO error budgets, and RAG retrieval (`MRR`, `MAP`, `F1`) + NPS metrics.
"""

from __future__ import annotations
import hashlib
import math
from typing import Any


# ---------------------------------------------------------------------------
# 1. Request Path, Model/Engine Routing, EPP Scoring & Ray Serve Multiplexing
# ---------------------------------------------------------------------------

def decompose_nine_stage_request_path(
    ingress_tls_ms: float = 5.0,
    admission_queue_ms: float = 12.0,
    cpu_tokenize_ms: float = 8.0,
    scheduler_alloc_ms: float = 0.8,
    pcie_h2d_ms: float = 0.4,
    gpu_prefill_ms: float = 180.0,
    gpu_decode_itl_ms: float = 20.0,
    output_tokens: int = 50,
    gpu_sampler_per_tok_ms: float = 0.3,
    pcie_d2h_detok_per_tok_ms: float = 0.5,
    sse_flush_per_tok_ms: float = 1.2,
    use_pinned_host_memory: bool = True,
) -> dict[str, Any]:
    """Decompose the 9-stage inference request lifecycle (V12 Ch. 2, HLS Ch. 4)."""
    pcie_bw_gbps = 60.0 if use_pinned_host_memory else 12.0
    ttft_ms = (
        ingress_tls_ms
        + admission_queue_ms
        + cpu_tokenize_ms
        + scheduler_alloc_ms
        + pcie_h2d_ms
        + gpu_prefill_ms
        + gpu_sampler_per_tok_ms
        + pcie_d2h_detok_per_tok_ms
        + sse_flush_per_tok_ms
    )
    effective_itl_ms = (
        gpu_decode_itl_ms
        + gpu_sampler_per_tok_ms
        + pcie_d2h_detok_per_tok_ms
        + sse_flush_per_tok_ms
    )
    decode_tail_ms = max(0, output_tokens - 1) * effective_itl_ms
    e2e_ms = ttft_ms + decode_tail_ms
    non_gpu_ttft_ms = ttft_ms - (gpu_prefill_ms + gpu_sampler_per_tok_ms)
    non_gpu_ttft_share_pct = round(100.0 * non_gpu_ttft_ms / ttft_ms, 2)
    return {
        "ttft_ms": round(ttft_ms, 2),
        "effective_itl_ms": round(effective_itl_ms, 2),
        "e2e_latency_ms": round(e2e_ms, 2),
        "non_gpu_ttft_ms": round(non_gpu_ttft_ms, 2),
        "non_gpu_ttft_share_pct": non_gpu_ttft_share_pct,
        "pcie_transfer_bw_gbps": pcie_bw_gbps,
        "pinned_vs_pageable_speedup_x": round(60.0 / 12.0, 2),
    }


class ModelRouter:
    """Multi-model and multi-engine API Gateway router (DAI Ch. 9)."""

    def __init__(
        self,
        model_endpoints: dict[str, str],
        engine_routes: dict[tuple[str, str | None], str] | None = None,
        healthy_backends: set[str] | None = None,
    ) -> None:
        self.model_endpoints = dict(model_endpoints)
        self.engine_routes = dict(engine_routes or {})
        self.healthy_backends = (
            set(healthy_backends)
            if healthy_backends is not None
            else set(model_endpoints.values()) | set(self.engine_routes.values())
        )

    def list_models(self) -> list[str]:
        return sorted(self.model_endpoints.keys())

    def route_request(self, request: dict[str, Any], endpoint_path: str = "/v1/chat/completions") -> dict[str, Any]:
        if endpoint_path not in ("/v1/chat/completions", "/v1/completions"):
            return {"status_code": 400, "error": f"Unsupported path {endpoint_path}"}
        model = request.get("model")
        engine = request.get("inference_server")
        if (model, engine) in self.engine_routes:
            target = self.engine_routes[(model, engine)]
        elif (model, None) in self.engine_routes and engine is None:
            target = self.engine_routes[(model, None)]
        elif model in self.model_endpoints:
            target = self.model_endpoints[model]
        else:
            return {"status_code": 404, "error": f"Model '{model}' not found"}

        if target not in self.healthy_backends and self.healthy_backends:
            return {"status_code": 503, "error": f"Backend '{target}' unhealthy"}
        return {
            "status_code": 200,
            "model": model,
            "inference_server": engine or "vllm",
            "target_service": target,
            "endpoint_path": endpoint_path,
        }


def score_epp_endpoints(
    candidates: list[dict[str, Any]],
    required_lora: str | None = None,
    kv_saturation_limit: float = 0.95,
    queue_saturation_limit: int = 50,
) -> dict[str, Any]:
    """Gateway API Inference Extension Endpoint Picker (EPP) scoring (GAK Ch. 4, DAI Ch. 9).

    Lower composite score is better:
      score = 2.0 * waiting_reqs + 100.0 * kv_usage - 30.0 * prefix_hit_ratio - 15.0 * lora_loaded
    """
    scored: list[dict[str, Any]] = []
    for pod in candidates:
        if pod["kv_usage"] >= kv_saturation_limit or pod["waiting_reqs"] >= queue_saturation_limit:
            continue
        lora_loaded = required_lora in pod.get("loras", set()) if required_lora else False
        score = (
            2.0 * pod["waiting_reqs"]
            + 100.0 * pod["kv_usage"]
            - 30.0 * pod.get("prefix_hit_ratio", 0.0)
            - (15.0 if lora_loaded else 0.0)
        )
        scored.append(
            {
                "pod_id": pod["pod_id"],
                "score": round(score, 2),
                "lora_loaded": lora_loaded,
                "prefix_hit_ratio": pod.get("prefix_hit_ratio", 0.0),
            }
        )
    scored.sort(key=lambda x: x["score"])
    return {
        "selected_pod": scored[0]["pod_id"] if scored else None,
        "ranked_candidates": scored,
        "fail_close_rejected": len(scored) == 0,
    }


def simulate_ray_serve_multiplexed_lru(
    request_model_ids: list[str],
    max_num_models_per_replica: int = 2,
) -> dict[str, Any]:
    """Simulate Ray Serve `@serve.multiplexed(max_num_models_per_replica=2)` LRU cache (HLS Ch. 4)."""
    cache: list[str] = []
    hits = 0
    cold_loads = 0
    evictions: list[str] = []
    for model_id in request_model_ids:
        if model_id in cache:
            hits += 1
            cache.remove(model_id)
            cache.append(model_id)
        else:
            cold_loads += 1
            if len(cache) >= max_num_models_per_replica:
                evicted = cache.pop(0)
                evictions.append(evicted)
            cache.append(model_id)
    return {
        "final_cached_models": list(cache),
        "cache_hits": hits,
        "cold_loads": cold_loads,
        "evictions": evictions,
        "hit_rate_pct": round(100.0 * hits / max(1, len(request_model_ids)), 2),
    }


# ---------------------------------------------------------------------------
# 2. Dual Token Bucket Rate Limiter (RPM/TPM), Prefix Caching & Guardrails
# ---------------------------------------------------------------------------

class DualTokenBucketRateLimiter:
    """Per-tenant RPM + TPM Token Bucket rate limiter (DAI Ch. 9, GAK Ch. 4, HLS Ch. 4)."""

    def __init__(
        self,
        requests_per_minute: int = 60,
        request_burst: int = 10,
        tokens_per_minute: int = 60000,
        token_burst: int = 15000,
        stale_ttl_seconds: float = 3600.0,
    ) -> None:
        self.rpm = requests_per_minute
        self.req_rate_per_sec = requests_per_minute / 60.0
        self.req_burst = float(request_burst)
        self.tpm = tokens_per_minute
        self.tok_rate_per_sec = tokens_per_minute / 60.0
        self.tok_burst = float(token_burst)
        self.stale_ttl_seconds = stale_ttl_seconds
        self.clients: dict[str, dict[str, float]] = {}

    def _get_or_update(self, client_id: str, now_sec: float) -> dict[str, float]:
        if client_id not in self.clients:
            self.clients[client_id] = {
                "req_tokens": self.req_burst,
                "llm_tokens": self.tok_burst,
                "last_ts": now_sec,
            }
            return self.clients[client_id]
        state = self.clients[client_id]
        elapsed = max(0.0, now_sec - state["last_ts"])
        state["req_tokens"] = min(self.req_burst, state["req_tokens"] + elapsed * self.req_rate_per_sec)
        state["llm_tokens"] = min(self.tok_burst, state["llm_tokens"] + elapsed * self.tok_rate_per_sec)
        state["last_ts"] = now_sec
        return state

    def check_rate_limit(self, client_id: str, requested_tokens: int, now_sec: float) -> dict[str, Any]:
        state = self._get_or_update(client_id, now_sec)
        if state["req_tokens"] < 1.0 or state["llm_tokens"] < float(requested_tokens):
            req_deficit = max(0.0, 1.0 - state["req_tokens"])
            tok_deficit = max(0.0, float(requested_tokens) - state["llm_tokens"])
            wait_sec = max(
                req_deficit / max(1e-9, self.req_rate_per_sec),
                tok_deficit / max(1e-9, self.tok_rate_per_sec),
            )
            return {
                "allowed": False,
                "status_code": 429,
                "remaining_requests": int(math.floor(state["req_tokens"])),
                "remaining_tokens": int(math.floor(state["llm_tokens"])),
                "reset_seconds": round(wait_sec, 2),
                "headers": {
                    "X-RateLimit-Remaining": str(int(math.floor(state["req_tokens"]))),
                    "X-RateLimit-Remaining-Tokens": str(int(math.floor(state["llm_tokens"]))),
                    "X-RateLimit-Reset": f"{wait_sec:.2f}",
                },
            }
        state["req_tokens"] -= 1.0
        state["llm_tokens"] -= float(requested_tokens)
        return {
            "allowed": True,
            "status_code": 200,
            "remaining_requests": int(math.floor(state["req_tokens"])),
            "remaining_tokens": int(math.floor(state["llm_tokens"])),
            "reset_seconds": 0.0,
            "headers": {
                "X-RateLimit-Remaining": str(int(math.floor(state["req_tokens"]))),
                "X-RateLimit-Remaining-Tokens": str(int(math.floor(state["llm_tokens"]))),
                "X-RateLimit-Reset": "0.00",
            },
        }

    def cleanup_stale_clients(self, now_sec: float) -> int:
        stale = [
            cid for cid, st in self.clients.items() if (now_sec - st["last_ts"]) > self.stale_ttl_seconds
        ]
        for cid in stale:
            del self.clients[cid]
        return len(stale)


def evaluate_prefix_and_prompt_compression(
    max_context_tokens: int = 32768,
    current_conversation_tokens: int = 26000,
    summarize_trigger_ratio: float = 0.75,
    oldest_fraction_to_summarize: float = 0.25,
    summary_compression_ratio: float = 0.20,
    system_prompt_tokens: int = 200,
    config_token_replacement: int = 10,
) -> dict[str, Any]:
    """Evaluate prompt compression & Anthropic/RAG prefix caching benchmarks (ASP Ch. 16, AIE Ch. 9)."""
    trigger_tokens = int(max_context_tokens * summarize_trigger_ratio)
    triggered = current_conversation_tokens > trigger_tokens
    if triggered:
        oldest_tokens = int(current_conversation_tokens * oldest_fraction_to_summarize)
        compressed_oldest = int(oldest_tokens * summary_compression_ratio)
        new_conversation_tokens = current_conversation_tokens - oldest_tokens + compressed_oldest
    else:
        new_conversation_tokens = current_conversation_tokens

    orig_quadratic = current_conversation_tokens * (current_conversation_tokens + 1) // 2
    new_quadratic = new_conversation_tokens * (new_conversation_tokens + 1) // 2
    attention_work_reduction_pct = round(100.0 * (1.0 - new_quadratic / orig_quadratic), 2)

    anthropic_table_9_3 = {
        "book_100k": {"ttft_no_cache_s": 11.5, "ttft_cached_s": 2.4, "latency_reduction_pct": 79, "cost_reduction_pct": 90},
        "many_shot_10k": {"ttft_no_cache_s": 1.6, "ttft_cached_s": 1.1, "latency_reduction_pct": 31, "cost_reduction_pct": 86},
        "multi_turn_10": {"ttft_no_cache_s": 10.0, "ttft_cached_s": 2.5, "latency_reduction_pct": 75, "cost_reduction_pct": 53},
    }
    return {
        "summarize_trigger_tokens": trigger_tokens,
        "compression_triggered": triggered,
        "original_tokens": current_conversation_tokens,
        "compressed_tokens": new_conversation_tokens,
        "attention_work_reduction_pct": attention_work_reduction_pct,
        "config_token_compression_x": round(system_prompt_tokens / config_token_replacement, 1),
        "daily_saved_tokens_1k_sys_1m_calls": 1_000 * 1_000_000,
        "anthropic_benchmarks": anthropic_table_9_3,
    }


def evaluate_nemo_guardrails_budget(
    base_model_ms: float = 45.0,
    input_pii_length_ms: float = 15.0,
    intent_classifier_ms: float = 30.0,
    rag_retrieval_ms: float = 100.0,
    output_fact_check_ms: float = 50.0,
    audit_log_ms: float = 10.0,
    max_input_length: int = 2048,
    min_confidence: float = 0.85,
    audit_retention_days: int = 2555,
) -> dict[str, Any]:
    """Compute NeMo Guardrails 5-stage latency budget and policy governance (V14 Ch. 6, GAK Ch. 5)."""
    cumulative = [
        base_model_ms,
        base_model_ms + input_pii_length_ms,
        base_model_ms + input_pii_length_ms + intent_classifier_ms,
        base_model_ms + input_pii_length_ms + intent_classifier_ms + rag_retrieval_ms,
        base_model_ms + input_pii_length_ms + intent_classifier_ms + rag_retrieval_ms + output_fact_check_ms,
        base_model_ms + input_pii_length_ms + intent_classifier_ms + rag_retrieval_ms + output_fact_check_ms + audit_log_ms,
    ]
    total_ms = cumulative[-1]
    overhead_ms = total_ms - base_model_ms
    slowdown_x = round(total_ms / base_model_ms, 2)
    return {
        "base_model_ms": base_model_ms,
        "total_guarded_ms": total_ms,
        "guardrail_overhead_ms": overhead_ms,
        "slowdown_factor_x": slowdown_x,
        "cumulative_stages_ms": cumulative,
        "max_input_length_tokens": max_input_length,
        "min_confidence_to_respond": min_confidence,
        "audit_retention_days": audit_retention_days,
        "five_rail_types": ("input", "dialog", "retrieval", "execution", "output"),
    }


# ---------------------------------------------------------------------------
# 3. Canary Rollouts, Consistent-Hash A/B Testing & SSE Streaming Drain
# ---------------------------------------------------------------------------

class CanaryDeploymentController:
    """Canary deployment controller with progressive shifting & auto-rollback (DAI Ch. 9, V14 Ch. 4)."""

    STEPS = (0.0, 10.0, 25.0, 50.0, 75.0, 100.0)

    def __init__(self, stable_endpoint: str, canary_endpoint: str, initial_pct: float = 10.0) -> None:
        self.stable_endpoint = stable_endpoint
        self.canary_endpoint = canary_endpoint
        self._canary_pct = float(initial_pct)
        self.stats: dict[str, dict[str, Any]] = {
            "stable": {"total": 0, "errors": 0, "latencies": []},
            "canary": {"total": 0, "errors": 0, "latencies": []},
        }

    @property
    def canary_percentage(self) -> float:
        return self._canary_pct

    def set_canary_percentage(self, pct: float) -> None:
        self._canary_pct = max(0.0, min(100.0, float(pct)))

    def record_result(self, is_canary: bool, success: bool, latency_ms: float) -> None:
        bucket = self.stats["canary" if is_canary else "stable"]
        bucket["total"] += 1
        if not success:
            bucket["errors"] += 1
        bucket["latencies"].append(float(latency_ms))

    def evaluate_gate(
        self,
        abs_error_threshold: float = 0.05,
        rel_error_multiplier: float = 2.0,
        promote_error_ratio: float = 1.10,
        promote_latency_ratio: float = 1.20,
        baseline_p95_ms: float = 180.0,
        warn_p95_ms: float = 250.0,
        critical_rollback_p95_ms: float = 300.0,
    ) -> dict[str, Any]:
        st = self.stats["stable"]
        ca = self.stats["canary"]
        st_err = st["errors"] / max(1, st["total"])
        ca_err = ca["errors"] / max(1, ca["total"])
        st_lat = sum(st["latencies"]) / max(1, len(st["latencies"]))
        ca_lat = sum(ca["latencies"]) / max(1, len(ca["latencies"]))
        ca_sorted = sorted(ca["latencies"])
        ca_p95 = ca_sorted[int(0.95 * (len(ca_sorted) - 1))] if ca_sorted else 0.0

        rollback_by_abs_err = ca["total"] >= 10 and (ca_err - st_err) > abs_error_threshold
        rollback_by_rel_err = ca["total"] >= 10 and st_err > 0 and ca_err > (rel_error_multiplier * st_err)
        rollback_by_p95 = ca_p95 >= critical_rollback_p95_ms
        should_rollback = rollback_by_abs_err or rollback_by_rel_err or rollback_by_p95

        can_promote = (
            not should_rollback
            and ca["total"] >= 20
            and ca_err <= max(0.01, st_err * promote_error_ratio)
            and (st_lat == 0 or ca_lat <= st_lat * promote_latency_ratio)
            and ca_p95 < warn_p95_ms
        )
        return {
            "stable_error_rate": round(st_err, 4),
            "canary_error_rate": round(ca_err, 4),
            "stable_mean_latency_ms": round(st_lat, 2),
            "canary_mean_latency_ms": round(ca_lat, 2),
            "canary_p95_latency_ms": round(ca_p95, 2),
            "baseline_p95_ms": baseline_p95_ms,
            "should_rollback": should_rollback,
            "can_promote": can_promote,
            "warning_circuit_breaker": warn_p95_ms <= ca_p95 < critical_rollback_p95_ms,
        }

    def promote_step(self) -> float:
        for step in self.STEPS:
            if step > self._canary_pct:
                self._canary_pct = step
                return self._canary_pct
        self._canary_pct = 100.0
        return self._canary_pct


def assign_ab_variant(test_name: str, user_id: str, variants: dict[str, float]) -> str:
    """Deterministic consistent-hashing variant assignment for A/B testing (DAI Ch. 9)."""
    digest = hashlib.sha256(f"{test_name}:{user_id}".encode("utf-8")).hexdigest()
    bucket = (int(digest[:8], 16) % 10000) / 10000.0
    cumulative = 0.0
    last_variant = next(iter(variants))
    for variant, weight in variants.items():
        cumulative += weight
        last_variant = variant
        if bucket < cumulative:
            return variant
    return last_variant


def evaluate_sse_streaming_and_drain(
    total_output_tokens: int = 100,
    generation_rate_tok_per_s: float = 20.0,
    tokens_per_sse_flush: int = 5,
    active_streams_at_sigterm: int = 24,
    remaining_tokens_per_stream: int = 60,
    prestop_sleep_s: int = 15,
    termination_grace_period_s: int = 120,
) -> dict[str, Any]:
    """Evaluate SSE streaming UX and Kubernetes graceful drain timing (ASP Ch. 16, V12 Ch. 3 & 11)."""
    full_generation_s = total_output_tokens / generation_rate_tok_per_s
    first_chunk_arrival_s = tokens_per_sse_flush / generation_rate_tok_per_s
    stream_drain_time_s = remaining_tokens_per_stream / generation_rate_tok_per_s
    total_shutdown_required_s = prestop_sleep_s + stream_drain_time_s
    zero_dropped_streams = total_shutdown_required_s <= termination_grace_period_s
    return {
        "full_generation_s": round(full_generation_s, 2),
        "first_sse_chunk_s": round(first_chunk_arrival_s, 2),
        "perceived_Wait_reduction_x": round(full_generation_s / first_chunk_arrival_s, 1),
        "human_reading_tok_per_s_range": (4, 13),
        "nagle_delayed_ack_worst_ms": 200,
        "client_flow_control_buffer_tokens": (50, 100),
        "debounce_window_ms": (2, 5),
        "max_output_token_limit": 4096,
        "generation_timeout_s": 30,
        "uncoordinated_unload_drop_pct": 15.0,
        "active_streams_at_sigterm": active_streams_at_sigterm,
        "total_shutdown_required_s": round(total_shutdown_required_s, 2),
        "termination_grace_period_s": termination_grace_period_s,
        "zero_dropped_streams": zero_dropped_streams,
    }


# ---------------------------------------------------------------------------
# 4. Kubernetes Health Probes, Probe-Induced Cascade & XID 62 Zombie Blackhole
# ---------------------------------------------------------------------------

def validate_k8s_llm_probes_and_failures(
    model_load_seconds: float = 240.0,
    startup_initial_delay_s: int = 30,
    startup_period_s: int = 10,
    startup_failure_threshold: int = 60,
    readiness_timeout_s: int = 5,
    nfs_io_stall_latency_s: float = 1.2,
    bad_readiness_timeout_s: int = 1,
    tp_world_size: int = 8,
    faulted_gpu_index: int = 3,
    total_cluster_replicas: int = 8,
    faulted_replicas: int = 1,
) -> dict[str, Any]:
    """Validate K8s Startup/Readiness/Liveness probes and V12 Ch. 11 failure scenarios."""
    startup_budget_s = startup_initial_delay_s + startup_period_s * startup_failure_threshold
    startup_survives_load = startup_budget_s >= model_load_seconds

    bad_probe_cascades = nfs_io_stall_latency_s > bad_readiness_timeout_s
    good_probe_survives = nfs_io_stall_latency_s <= readiness_timeout_s

    blackhole_timeout_pct = round(100.0 * faulted_replicas / total_cluster_replicas, 2)
    gpu_util_vector = [100 if i == faulted_gpu_index else 0 for i in range(tp_world_size)]
    return {
        "startup_budget_s": startup_budget_s,
        "startup_window_only_s": startup_period_s * startup_failure_threshold,
        "startup_survives_load": startup_survives_load,
        "bad_probe_1s_cascades_100pct_503": bad_probe_cascades,
        "good_probe_5s_survives_nfs_spike": good_probe_survives,
        "xid_62_faulted_gpu": faulted_gpu_index,
        "xid_62_tp_gpu_util_pct": gpu_util_vector,
        "xid_62_cluster_timeout_pct": blackhole_timeout_pct,
        "npd_remediation_xids": (48, 62, 79, 92),
    }


# ---------------------------------------------------------------------------
# 5. Circuit Breaker State Machine, Fallback Cascades & Swap Thrashing
# ---------------------------------------------------------------------------

def evaluate_circuit_breaker_and_fallbacks(
    kv_cache_usage_perc: float,
    num_requests_waiting: int,
    sustained_seconds: float,
    current_state: str = "CLOSED",
    open_kv_threshold: float = 0.95,
    open_queue_threshold: int = 50,
    open_sustained_s: float = 5.0,
    reset_kv_threshold: float = 0.80,
) -> dict[str, Any]:
    """Evaluate admission control, circuit breaker transitions & fallback cascade (V12 Ch. 1, 8, 11)."""
    if kv_cache_usage_perc < 0.80 and num_requests_waiting < 20:
        zone = "SAFE"
    elif kv_cache_usage_perc <= 0.90 and num_requests_waiting <= open_queue_threshold:
        zone = "WARNING"
    else:
        zone = "EMERGENCY"

    next_state = current_state
    if current_state == "CLOSED":
        if (
            kv_cache_usage_perc > open_kv_threshold or num_requests_waiting > open_queue_threshold
        ) and sustained_seconds >= open_sustained_s:
            next_state = "OPEN"
    elif current_state == "OPEN":
        if kv_cache_usage_perc < reset_kv_threshold and num_requests_waiting < 20:
            next_state = "CLOSED"

    action = "route_primary_70b" if next_state == "CLOSED" else "shed_429_or_fallback_8b_cloud"

    # V12 Ch. 8 PCIe swap thrashing math: 20 ms/tok -> 850 ms/tok (42.5x / +4,150% ~ 4,000% degradation)
    swap_itl_normal_ms = 20.0
    swap_itl_thrashing_ms = 850.0
    swap_degradation_pct = round(100.0 * (swap_itl_thrashing_ms - swap_itl_normal_ms) / swap_itl_normal_ms, 1)

    # DAI Ch. 9 Spot + On-Demand cost optimization (50% Spot at 70% discount + 50% On-Demand)
    blended_spot_savings_pct = 0.50 * 70.0
    return {
        "operating_zone": zone,
        "previous_state": current_state,
        "next_state": next_state,
        "routing_action": action,
        "swap_space_recommended_gb": 0,
        "swap_thrashing_itl_ms": (swap_itl_normal_ms, swap_itl_thrashing_ms),
        "swap_degradation_pct": swap_degradation_pct,
        "blended_50pct_spot_savings_pct": blended_spot_savings_pct,
    }


# ---------------------------------------------------------------------------
# 6. OpenTelemetry Tracing, CPU vs GPU Triage, SLO Budgets & RAG/LLMOps Metrics
# ---------------------------------------------------------------------------

def analyze_otel_trace_and_slo_budgets() -> dict[str, Any]:
    """Analyze OTel trace waterfalls (V12 Ch. 1 & Lab 04), SLO budgets (LLP Ch. 2), and RAG MAP/F1 (LLP Ch. 7)."""
    # V12 Ch. 1 Scenario 2: 4,820 ms streaming stall decomposed via OpenTelemetry spans
    waterfall_spans_ms = {
        "tokenize_input": 4.0,
        "admission_queue_wait": 12.0,
        "ttft_prefill_ingest": 180.0,
        "decode_tokens_1_to_10": 240.0,
        "decode_stall_prefill_starvation": 3850.0,
        "decode_tokens_11_to_50": 534.0,
    }
    total_trace_ms = sum(waterfall_spans_ms.values())
    chunked_prefill_after = {"mean_ttft_ms": 210.4, "p99_itl_ms": 22.8, "before_p99_itl_ms": 4500.0}

    # V12 Lab 04: 200 requests at C=8 (ThreadPool GIL vs ProcessPoolExecutor)
    lab04_unfixed = {"rps": 13.47, "total_p99_ms": 1410.20, "cpu_prep_p99_ms": 1395.80, "triton_infer_p99_ms": 18.10}
    lab04_fixed = {"rps": 104.17, "total_p99_ms": 44.80, "cpu_prep_p99_ms": 31.00, "triton_infer_p99_ms": 13.50}

    # 30-day (43,200 minutes) SLO error budget math: 43.20 minutes (99.9%), 21.60 minutes (99.95%),
    # 4.32 minutes / 259.2 seconds (99.99%), and 0.432 minutes / 25.92 seconds (99.999%)
    minutes_30d = 30 * 24 * 60
    error_budgets_min = {
        "99.9%": round(minutes_30d * (1.0 - 0.999), 2),
        "99.95%": round(minutes_30d * (1.0 - 0.9995), 2),
        "99.99%": round(minutes_30d * (1.0 - 0.9999), 2),
        "99.999%": round(minutes_30d * (1.0 - 0.99999), 3),
        "99.99%_sec": 259.2,
    }

    # LLP Ch. 7 RAG Mean Average Precision (MAP) & F1 Relevance worked example
    ap_q1_pct = round((100.0 + 100.0 + 0.0) / 3.0)
    ap_q2_pct = round((100.0 + 0.0 + 67.0) / 3.0)
    map_pct = int(math.floor((ap_q1_pct + ap_q2_pct) / 2.0))
    f1_balanced = round(2 * 60.0 * 60.0 / (60.0 + 60.0), 1)
    f1_unbalanced = round(2 * 90.0 * 30.0 / (90.0 + 30.0), 1)

    return {
        "otel_six_spans": (
            "gateway.receive",
            "gateway.route",
            "tokenizer.encode",
            "model.inference",
            "tokenizer.decode",
            "gateway.respond",
        ),
        "waterfall_total_ms": total_trace_ms,
        "waterfall_stall_ms": waterfall_spans_ms["decode_stall_prefill_starvation"],
        "chunked_prefill_remediation": chunked_prefill_after,
        "lab04_throughput_gain_x": round(lab04_fixed["rps"] / lab04_unfixed["rps"], 2),
        "lab04_p99_reduction_x": round(lab04_unfixed["total_p99_ms"] / lab04_fixed["total_p99_ms"], 2),
        "error_budgets_30d_min": error_budgets_min,
        "rag_ap_q1_pct": ap_q1_pct,
        "rag_ap_q2_pct": ap_q2_pct,
        "rag_map_pct": map_pct,
        "rag_f1_balanced_vs_unbalanced": (f1_balanced, f1_unbalanced),
    }
