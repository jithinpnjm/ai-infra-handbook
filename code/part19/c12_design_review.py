"""Design review checklist for an inference platform design (chapter 19.12).
A design is a plain dict. review() returns the findings, each tied to a section of the chapter.
The checks are my reasoning from chapters 19.12, 20.18 to 20.22, not an external standard.
Standard library only."""

REQUIRED_METRICS = {"ttft", "tpot", "queue_depth", "kv_cache_usage", "error_rate_by_model", "finish_reason"}


def review(d):
    f = []

    def bad(section, msg):
        f.append((section, msg))

    slo = d.get("slo", {})
    if not all(k in slo for k in ("availability", "ttft_p99_s", "tpot_p95_s")):
        bad("1", "SLOs must state availability, TTFT p99 and TPOT p95 per model")
    if not d.get("assumptions"):
        bad("1", "sizing assumptions are not written down")
    if d.get("engine") not in ("vllm", "tensorrt-llm", "sglang", "llama.cpp"):
        bad("3", "engine not chosen from a named option")
    if not d.get("engine_pinned_version"):
        bad("3", "engine image must be pinned by version or digest, never latest")
    tiers = d.get("tiers", {})
    for name, t in tiers.items():
        if t.get("tier") == "hot" and t.get("min_replicas", 0) < 2:
            bad("4", f"{name}: hot model with fewer than two replicas")
        if t.get("tier") == "cold" and not t.get("cache_slots"):
            bad("4", f"{name}: cold model with no cache slots or eviction rule")
    if d.get("spare_gpus", 0) < d.get("largest_replica_gpus", 1):
        bad("4", "spare GPUs are smaller than the largest replica, so one node loss cannot be absorbed")
    if not d.get("priority_classes"):
        bad("4", "no priority classes: batch cannot yield to interactive")
    gw = d.get("gateway", {})
    if not gw.get("auth"):
        bad("5", "gateway has no authentication")
    if not gw.get("token_quota_per_team"):
        bad("5", "no per-team token quota, so one team can take the pool")
    if not gw.get("retry_budget"):
        bad("5", "retries have no budget")
    sc = d.get("autoscaling", {})
    if sc.get("signal") in ("cpu", "gpu_util"):
        bad("6", "autoscaling on CPU or GPU utilisation")
    if sc.get("scale_down_window_s", 0) < 3 * d.get("cold_start_s", 150):
        bad("6", "scale-down window under three cold starts")
    cn = d.get("canary", {})
    for g in ("error_rate", "ttft", "finish_reason", "quality_eval", "neighbour_ttft"):
        if g not in cn.get("gates", []):
            bad("7", f"canary has no {g} gate")
    if not cn.get("rollback_automatic"):
        bad("7", "rollback is not automatic")
    sec = d.get("security", {})
    if not sec.get("network_policy_default_deny"):
        bad("9", "no default-deny network policy for the engine namespace")
    if sec.get("model_baked_in_image"):
        bad("9", "model weights baked into the image")
    if sec.get("secrets_in_env_literals"):
        bad("9", "secrets written as literals")
    missing = REQUIRED_METRICS - set(d.get("metrics", []))
    if missing:
        bad("10", "missing metrics: " + ", ".join(sorted(missing)))
    if d.get("termination_grace_s", 0) < d.get("max_request_s", 60):
        bad("10", "termination grace shorter than the longest request, so streams are cut on scale-down")
    return f


GOOD = {
    "slo": {"availability": 0.999, "ttft_p99_s": 2.0, "tpot_p95_s": 0.05},
    "assumptions": ["12 to 30 QPS peak", "H100 80 GB", "BF16"],
    "engine": "vllm", "engine_pinned_version": True,
    "tiers": {"assistant": {"tier": "hot", "min_replicas": 2},
              "contracts-8b": {"tier": "cold", "cache_slots": 1}},
    "spare_gpus": 8, "largest_replica_gpus": 4,
    "priority_classes": ["llm-interactive", "llm-batch"],
    "gateway": {"auth": "jwt", "token_quota_per_team": True, "retry_budget": 0.1},
    "autoscaling": {"signal": "inflight", "scale_down_window_s": 900}, "cold_start_s": 150,
    "canary": {"gates": ["error_rate", "ttft", "finish_reason", "quality_eval", "neighbour_ttft"],
               "rollback_automatic": True},
    "security": {"network_policy_default_deny": True},
    "metrics": sorted(REQUIRED_METRICS),
    "termination_grace_s": 180, "max_request_s": 120,
}

BAD = {
    "slo": {"availability": 0.999},
    "engine": "custom", "tiers": {"assistant": {"tier": "hot", "min_replicas": 1}},
    "spare_gpus": 0, "largest_replica_gpus": 4,
    "gateway": {}, "autoscaling": {"signal": "gpu_util", "scale_down_window_s": 60},
    "canary": {"gates": ["error_rate"]},
    "security": {"model_baked_in_image": True},
    "metrics": ["ttft"], "termination_grace_s": 30, "max_request_s": 120,
}

if __name__ == "__main__":
    for name, d in (("good", GOOD), ("bad", BAD)):
        r = review(d)
        print(name, len(r), "findings")
        for s, m in r:
            print(f"  section {s}: {m}")
