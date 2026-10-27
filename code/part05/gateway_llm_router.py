"""Chapter 5.12 model: Gateway API `HTTPRoute` matcher (`Exact` vs `PathPrefix`
precedence, header matching, and cross-namespace `ReferenceGrant` verification),
LLM streaming gateway validator, and KV-cache / queue-aware `InferencePool`
endpoint picker (`KUR` Ch. 8, `PK` Ch. 6, `NK` Ch. 5 & 6).

Sources modeled:
- Brendan Burns, Joe Beda, Kelsey Hightower & Lachlan Evenson, Kubernetes: Up
  and Running, 3rd ed. (kubernetes-up-and-running-3rd-edition, KUR), Chapter 8
  ("HTTP Load Balancing with Ingress"): virtual hosting, `defaultBackend`, path
  routing (`bandicoot.example.com/a/` passed unmodified to upstream unless
  rewritten), `kubernetes.io/tls` Secrets, and multiple Ingress merge hazards.
- Josh Rosso, Rich Lander, Alexander Brand & John Harris, Production Kubernetes
  (production-kubernetes, PK), Chapter 6 ("Service Routing"): Contour `HTTPProxy`
  root inclusion (`includes`) and TCP SNI proxying, dedicated Ingress node pool
  with `hostNetwork: true` + `dnsPolicy: ClusterFirstWithHostNet`.
- James Strong & Vallery Lancey, Networking and Kubernetes (networking-and-
  kubernetes, NK), Chapters 5 & 6 (`Exact` vs `Prefix` path precedence, NGINX
  Ingress, AWS ALB Controller, GKE Container-Native LB with NEGs).
"""
from typing import Any, Dict, List, Mapping, Sequence, Set, Tuple


def evaluate_httproute_and_reference_grant(
    *,
    route_namespace: str,
    request_host: str,
    request_path: str,
    request_headers: Mapping[str, str],
    rules: Sequence[Mapping[str, Any]],
    reference_grants: Set[Tuple[str, str, str]],
) -> Dict[str, Any]:
    """Model Section 2 & 3 Ingress/Gateway API route matching:
    1. `Exact` path match always takes precedence over `PathPrefix` (`NK` Ch. 5).
    2. Longest `PathPrefix` wins among prefix matches, filtered by required headers.
    3. If the selected backend `Service` is in a different namespace than
       `route_namespace`, a `ReferenceGrant` `(from_ns, to_ns, to_service_name)`
       must exist, else status is `ResolvedRefs=False (RefNotPermitted)`.
    """
    best_rule: Mapping[str, Any] | None = None
    best_rank: Tuple[int, int] = (-1, -1)  # (is_exact, path_len)

    for rule in rules:
        if request_host not in rule.get("hostnames", (request_host,)):
            continue
        p_type = str(rule.get("path_type", "PathPrefix"))
        p_val = str(rule.get("path", "/"))
        req_hdrs = rule.get("headers", {})
        if any(request_headers.get(k) != v for k, v in req_hdrs.items()):
            continue

        if p_type == "Exact" and request_path == p_val:
            rank = (1, len(p_val))
        elif p_type == "PathPrefix" and request_path.startswith(p_val):
            rank = (0, len(p_val))
        else:
            continue

        if rank > best_rank:
            best_rank = rank
            best_rule = rule

    if best_rule is None:
        return {"matched": False, "status": 404}

    backend_ns = str(best_rule.get("backend_namespace", route_namespace))
    backend_svc = str(best_rule["backend_service"])
    if backend_ns != route_namespace and (route_namespace, backend_ns, backend_svc) not in reference_grants:
        return {
            "matched": True,
            "resolved_refs": False,
            "status": 500,
            "reason": f"RefNotPermitted: missing ReferenceGrant from {route_namespace!r} to {backend_ns}/{backend_svc}",
        }

    return {
        "matched": True,
        "resolved_refs": True,
        "status": 200,
        "backend_service": f"{backend_ns}/{backend_svc}",
    }


def validate_llm_streaming_gateway_config(cfg: Mapping[str, Any]) -> Tuple[bool, List[str]]:
    """Model Section 6 LLM streaming edge requirements."""
    errors: List[str] = []
    if cfg.get("proxy_buffering") != "off":
        errors.append("proxy_buffering must be 'off' for SSE token streaming")
    if int(cfg.get("proxy_read_timeout_sec", 60)) < 300:
        errors.append("proxy_read_timeout_sec must be >= 300s for long LLM generations")
    if int(cfg.get("proxy_body_size_mb", 1)) < 32:
        errors.append("proxy_body_size_mb must be >= 32m for long prompts / multimodal payloads")
    if int(cfg.get("num_retries_on_post", 0)) > 0:
        errors.append("num_retries_on_post must be 0 to avoid duplicate non-idempotent generation runs")
    return (len(errors) == 0), errors


def pick_llm_inference_endpoint(
    pods: Sequence[Mapping[str, Any]],
    prompt_prefix_hash: str,
) -> str:
    """Model Section 3 & 6 Gateway API Inference Extension endpoint picker:
    Scores candidate model-server pods by:
      +50 bonus if `prompt_prefix_hash` is present in the pod's KV prefix cache
      -2 * `queue_depth`
      -0.5 * `kv_cache_util_pct`
    """
    def score(pod: Mapping[str, Any]) -> float:
        cache_hit = 50.0 if prompt_prefix_hash in pod.get("cached_prefixes", set()) else 0.0
        q_penalty = 2.0 * float(pod.get("queue_depth", 0))
        kv_penalty = 0.5 * float(pod.get("kv_cache_util_pct", 0.0))
        return cache_hit - q_penalty - kv_penalty

    best = max(pods, key=score)
    return str(best["name"])
