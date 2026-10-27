#!/usr/bin/env python3
"""Self-checking lab for Chapter 5.12: Ingress, load balancers and the Gateway API."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gateway_llm_router import (
    evaluate_httproute_and_reference_grant,
    pick_llm_inference_endpoint,
    validate_llm_streaming_gateway_config,
)

passed = 0
failed = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global passed, failed
    if cond:
        passed += 1
        print(f"PASS: {name}")
    else:
        failed += 1
        print(f"FAIL: {name}" + (f" ({detail})" if detail else ""))


def main() -> None:
    # 1. Section 2 & 3 & NK Ch. 5: Exact vs PathPrefix precedence, header match, and ReferenceGrant check
    rules = [
        {"path_type": "PathPrefix", "path": "/v1", "headers": {"x-model": "llama-70b"}, "backend_namespace": "serving", "backend_service": "vllm-70b"},
        {"path_type": "Exact", "path": "/v1/health", "headers": {}, "backend_namespace": "ops", "backend_service": "health-svc"},
    ]
    # Header match in same namespace
    r_chat = evaluate_httproute_and_reference_grant(
        route_namespace="serving",
        request_host="chat.ai.example.com",
        request_path="/v1/chat/completions",
        request_headers={"x-model": "llama-70b"},
        rules=rules,
        reference_grants=set(),
    )
    # Cross-namespace Exact match WITHOUT ReferenceGrant -> blocked!
    r_blocked = evaluate_httproute_and_reference_grant(
        route_namespace="serving",
        request_host="chat.ai.example.com",
        request_path="/v1/health",
        request_headers={"x-model": "llama-70b"},
        rules=rules,
        reference_grants=set(),
    )
    # Cross-namespace Exact match WITH ReferenceGrant -> allowed!
    r_allowed = evaluate_httproute_and_reference_grant(
        route_namespace="serving",
        request_host="chat.ai.example.com",
        request_path="/v1/health",
        request_headers={"x-model": "llama-70b"},
        rules=rules,
        reference_grants={("serving", "ops", "health-svc")},
    )
    check(
        "HTTPRoute enforces Exact > PathPrefix precedence, matches x-model header, and requires ReferenceGrant for cross-namespace backend",
        r_chat["backend_service"] == "serving/vllm-70b"
        and r_blocked["resolved_refs"] is False
        and r_allowed["resolved_refs"] is True
        and r_allowed["backend_service"] == "ops/health-svc",
    )

    # 2. Section 6: LLM streaming gateway config validator
    ok_llm, _ = validate_llm_streaming_gateway_config(
        {"proxy_buffering": "off", "proxy_read_timeout_sec": 600, "proxy_body_size_mb": 64, "num_retries_on_post": 0}
    )
    bad_llm, errs = validate_llm_streaming_gateway_config(
        {"proxy_buffering": "on", "proxy_read_timeout_sec": 60, "proxy_body_size_mb": 1, "num_retries_on_post": 3}
    )
    check(
        "validate_llm_streaming_gateway_config accepts streaming-tuned edge and catches 60s timeout, buffering=on, 1m body, and POST retries",
        ok_llm is True and bad_llm is False and len(errs) == 4,
    )

    # 3. Section 3 & 6: KV-cache & queue-aware InferencePool endpoint picker
    pods = [
        {"name": "vllm-0", "queue_depth": 15, "kv_cache_util_pct": 90.0, "cached_prefixes": {"sys-prompt-a"}},
        {"name": "vllm-1", "queue_depth": 2, "kv_cache_util_pct": 30.0, "cached_prefixes": {"sys-prompt-a"}},
        {"name": "vllm-2", "queue_depth": 1, "kv_cache_util_pct": 25.0, "cached_prefixes": set()},
    ]
    chosen = pick_llm_inference_endpoint(pods, prompt_prefix_hash="sys-prompt-a")
    check(
        "pick_llm_inference_endpoint selects vllm-1 (warm prefix cache + low queue depth) over overloaded vllm-0 and cold vllm-2",
        chosen == "vllm-1",
    )

    print(f"Summary: {passed} passed, {failed} failed (total {passed + failed})")
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
