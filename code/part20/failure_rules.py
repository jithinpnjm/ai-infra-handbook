# code/part20/failure_rules.py
"""Failure signatures. Thresholds are starting values, not vendor figures.
Tune them against your own baseline before paging anyone."""
from failure_model import Rule

T = dict(waiting=8, kv_full=0.95, kv_high=0.90, slow_load_s=300,
         hol_prompt_ratio=8, accept_low=0.5, tenant_share=0.5, retry_ratio=1.5)

W, RUN, KV = "vllm:num_requests_waiting", "vllm:num_requests_running", "vllm:kv_cache_usage_perc"
PRE, GEN = "vllm:num_preemptions@rate", "vllm:generation_tokens@rate"
TTFT, ITL = "vllm:time_to_first_token_seconds@p99", "vllm:inter_token_latency_seconds@p99"
QT, E2E = "vllm:request_queue_time_seconds@p99", "vllm:e2e_request_latency_seconds@p99"
PP50, PP99 = "vllm:request_prompt_tokens@p50", "vllm:request_prompt_tokens@p99"
PTOK = "vllm:prompt_tokens@rate"
REJ, BAD = "vllm:admission_rejections@rate", "vllm:corrupted_requests@rate"
HITS, QRY = "vllm:prefix_cache_hits@rate", "vllm:prefix_cache_queries@rate"
ACC, DRAFT = "vllm:spec_decode_num_accepted_tokens@rate", "vllm:spec_decode_num_draft_tokens@rate"


def gt(key, n):
    return lambda r: None if r.get(key) is None else r.get(key) >= n


def lt(key, n):
    return lambda r: None if r.get(key) is None else r.get(key) < n


def eq(key, v):
    return lambda r: None if r.get(key) is None else r.get(key) == v


def up(key, factor):
    return lambda r: r.up(key, factor)


def share_up(reason, delta):
    def fn(r):
        a, b = r.finish_share(reason), r.finish_share(reason, baseline=True)
        return None if a is None or b is None else a - b >= delta
    return fn


def busy_no_tokens(r):
    work, gen = (r.get(W) or 0) + (r.get(RUN) or 0), r.get(GEN)
    return None if gen is None else work > 0 and gen == 0


def pool_short(r):
    ready, want = r.get("sig:ready_replicas"), r.get("sig:desired_replicas")
    return None if ready is None or want is None else ready < want


def running_full(r):
    run, cap = r.get(RUN), r.get("sig:max_num_seqs")
    return None if run is None or not cap else run >= 0.9 * cap


def hit_ratio_halved(r):
    now = r.get(HITS), r.get(QRY)
    base = r.baseline.get(HITS), r.baseline.get(QRY)
    if None in now or not now[1] or not all(base) or not base[1]:
        return None
    return (now[0] / now[1]) <= 0.5 * (base[0] / base[1])


def accept_rate_low(r):
    acc, drf = r.get(ACC), r.get(DRAFT)
    return None if acc is None or not drf else acc / drf < T["accept_low"]


def prompt_tail_heavy(r):
    p50, p99 = r.get(PP50), r.get(PP99)
    return None if not p50 or p99 is None else p99 / p50 >= T["hol_prompt_ratio"]


def xid_present(r):
    codes = r.get("sig:xid_codes")
    return None if codes is None else len(codes) > 0


def loads_many(r):
    n, want = r.get("sig:replicas_loading"), r.get("sig:desired_replicas")
    return None if n is None or not want else n >= max(2, 0.5 * want)


RULES = [
    Rule("queue_growth_capacity_saturated",
         "waiting high, running at max_num_seqs, KV usage below 90 percent, tokens still flowing",
         "scale out or shed load at the router; cap admission with --max-num-queued-reqs",
         "autoscale on vllm:num_requests_waiting and queue time, not GPU utilisation",
         ((3, "requests waiting above threshold", gt(W, T["waiting"])),
          (2, "running batch at max_num_seqs", running_full),
          (2, "KV usage below 90 percent", lt(KV, T["kv_high"])),
          (2, "queue time p99 at least 3x baseline", up(QT, 3)),
          (1, "tokens still being generated", gt(GEN, 1e-9)))),
    Rule("kv_cache_exhaustion_preemption",
         "kv_cache_usage_perc near 1 and rate(vllm:num_preemptions_total) above 0",
         "lower max_num_seqs or max_num_batched_tokens, or add replicas",
         "raise gpu_memory_utilization, add tensor parallel, quantise KV cache, resize for context length",
         ((3, "KV usage at or above 95 percent", gt(KV, T["kv_full"])),
          (3, "preemptions are happening", gt(PRE, 1e-9)),
          (1, "inter-token latency p99 at least 2x baseline", up(ITL, 2)),
          (1, "requests waiting", gt(W, 1)),
          (1, "end-to-end p99 at least 2x baseline", up(E2E, 2)))),
    Rule("long_context_head_of_line_blocking",
         "prompt length p99 over p50 is large while ITL p99 rises and KV is not full",
         "route long prompts to a separate pool or lower max_num_batched_tokens",
         "set long_prefill_token_threshold, disaggregate prefill, add context-length quotas",
         ((2, "prompt length tail is heavy", prompt_tail_heavy),
          (2, "inter-token latency p99 at least 2x baseline", up(ITL, 2)),
          (1, "TTFT p99 at least 2x baseline", up(TTFT, 2)),
          (1, "no preemption pressure", lt(PRE, 1e-9)),
          (1, "KV usage below 95 percent", lt(KV, T["kv_full"])))),
    Rule("admission_limit_shedding",
         "rate(vllm:admission_rejections_total) above 0 and clients see HTTP 503",
         "confirm it is deliberate, then scale out or tell clients to back off",
         "size max_num_queued_reqs from capacity and set a retry budget",
         ((4, "admission rejections happening", gt(REJ, 1e-9)),
          (1, "requests waiting", gt(W, 1)))),
    Rule("engine_hang_no_progress",
         "work is queued or running but rate(vllm:generation_tokens_total) is 0",
         "restart the replica after capturing py-spy and logs, drain it from the pool",
         "NCCL timeouts, a hang watchdog, a deep health check that sends one token",
         ((4, "work present but zero tokens generated", busy_no_tokens),
          (2, "NCCL error in log", eq("sig:nccl_error_in_log", True)),
          (1, "/health still returns 200", eq("sig:health_http_status", 200)),
          (1, "Xid events present", xid_present))),
    Rule("gpu_xid_fault",
         "dmesg shows NVRM Xid lines for this GPU; look the code up in the NVIDIA Xid catalog",
         "cordon and drain the node, reset the GPU or reboot, move the replica",
         "automate cordon on fatal Xid codes, keep a spare pool",
         ((4, "Xid codes seen", xid_present),
          (1, "no tokens generated", eq(GEN, 0)),
          (1, "error finish reasons present", gt("vllm:request_success@rate:error", 1e-9)))),
    Rule("oom_at_startup",
         "container exits during load or memory profiling, before the server listens",
         "lower gpu_memory_utilization or max_model_len, check co-tenants on the GPU",
         "size weights plus activations plus CUDA graphs per GPU, pin one replica per GPU",
         ((4, "OOM happened during startup", eq("sig:oom_phase", "startup")),
          (1, "repeated restarts", gt("sig:probe_restarts_1h", 3)))),
    Rule("oom_at_runtime",
         "process dies under load after serving traffic; KV usage was high before the crash",
         "lower max_num_batched_tokens and max_num_seqs, restart, cap prompt length",
         "reserve activation headroom, add prompt-length limits, fix co-tenant sharing",
         ((4, "OOM happened while serving", eq("sig:oom_phase", "runtime")),
          (1, "KV usage was high", gt(KV, T["kv_high"])),
          (1, "prompt token rate above baseline", up(PTOK, 1.5)))),
    Rule("slow_weight_load_cold_start",
         "model load seconds in the startup log far above baseline, replicas not ready",
         "load from local disk or a warm cache, add warm spare replicas",
         "bake or pre-stage weights, stagger startup, set a startup probe window",
         ((3, "weight load slower than threshold", gt("sig:model_load_seconds", T["slow_load_s"])),
          (2, "replicas still loading", gt("sig:replicas_loading", 1)),
          (2, "loading is not pool-wide", lambda r: None if loads_many(r) is None else not loads_many(r)))),
    Rule("thundering_herd_on_restart",
         "many replicas loading weights at once from shared storage; load time inflates",
         "stagger restarts, limit surge, keep serving replicas in the pool",
         "rolling updates with maxUnavailable, local weight cache, jittered retries",
         ((3, "half or more of the pool is loading", loads_many),
          (2, "load time at least 2x baseline", up("sig:model_load_seconds", 2)),
          (1, "ready below desired", pool_short),
          (1, "clients are retrying", gt("sig:attempts_per_unique_request", T["retry_ratio"])))),
    Rule("liveness_probe_kills_busy_worker",
         "container restart reason is a failed liveness probe while the engine was generating",
         "relax liveness timeout and failureThreshold, add startupProbe, move load checks to readiness",
         "liveness checks only local process health; readiness carries load state",
         ((4, "restart caused by liveness probe", eq("sig:restart_reason", "liveness")),
          (2, "engine was busy and making progress", gt(GEN, 1e-9)),
          (1, "no Xid events", eq("sig:xid_codes", [])),
          (1, "no NCCL error", eq("sig:nccl_error_in_log", False)))),
    Rule("silent_pool_shrink",
         "ready replicas below desired with no alert firing; per-replica load rising",
         "restart or replace the missing workers, check service discovery registration",
         "alert on ready versus desired, add readiness-driven re-registration and X+1 spare",
         ((3, "ready replicas below desired", pool_short),
          (2, "no alert is firing", eq("sig:alerts_firing", 0)),
          (1, "recent restarts", gt("sig:probe_restarts_1h", 1)),
          (1, "requests waiting", gt(W, 1)))),
    Rule("retry_amplification",
         "attempts per unique request above 1.5 while errors or rejections are present",
         "cut client retries, add jitter and a retry budget, shed at the edge",
         "retry budget per client, circuit breaker, idempotency keys",
         ((3, "attempts per unique request high", gt("sig:attempts_per_unique_request", T["retry_ratio"])),
          (2, "rejections happening", gt(REJ, 1e-9)),
          (1, "requests waiting", gt(W, 1)),
          (1, "prompt token rate above baseline", up(PTOK, 1.5)))),
    Rule("noisy_tenant",
         "one tenant holds half or more of the prompt tokens while others see queueing",
         "apply that tenant's rate limit or move them to a dedicated pool",
         "per-tenant token quotas and fair-share queueing at the router",
         ((3, "top tenant token share high", gt("sig:top_tenant_token_share", T["tenant_share"])),
          (2, "requests waiting", gt(W, T["waiting"])),
          (1, "TTFT p99 at least 2x baseline", up(TTFT, 2)))),
    Rule("prefix_cache_hit_collapse",
         "hit ratio from vllm:prefix_cache_hits over vllm:prefix_cache_queries fell by half",
         "check router affinity and recent restarts, do not flush caches",
         "cache-aware routing, stable replica identity, larger KV budget",
         ((3, "prefix cache hit ratio halved", hit_ratio_halved),
          (2, "TTFT p99 at least 2x baseline", up(TTFT, 2)),
          (1, "prompt token rate above baseline", up(PTOK, 1.2)))),
    Rule("quality_regression_finish_reason_drift",
         "finished_reason mix moved: more length or repetition, fewer stop; NaN logits count",
         "stop the rollout, roll back the change, compare outputs on a fixed prompt set",
         "canary with output-quality checks and finish_reason alerts",
         ((3, "length share up by 15 points", share_up("length", 0.15)),
          (2, "repetition finishes present", gt("vllm:request_success@rate:repetition", 1e-9)),
          (2, "NaN-logit corrupted requests", gt(BAD, 1e-9)),
          (1, "error finishes present", gt("vllm:request_success@rate:error", 1e-9)))),
    Rule("speculative_decoding_low_acceptance",
         "accepted over draft token rate is low, so drafts cost time and save little",
         "disable speculation or shrink num_speculative_tokens for this traffic",
         "pick a draft that matches the target, tune per workload, alert on acceptance",
         ((3, "acceptance rate below 50 percent", accept_rate_low),
          (2, "inter-token latency p99 at least 1.5x baseline", up(ITL, 1.5)))),
    Rule("quantisation_quality_regression",
         "a precision or KV dtype change shipped and finish_reason mix or eval scores moved",
         "roll back the precision change on the affected pool",
         "gate precision changes behind an eval set and a canary",
         ((3, "precision or KV dtype changed", eq("sig:quantisation_changed", True)),
          (2, "length share up by 15 points", share_up("length", 0.15)),
          (1, "repetition finishes present", gt("vllm:request_success@rate:repetition", 1e-9)))),
    Rule("version_skew_router_engine",
         "router and engine versions differ and errors or output shape changed after a rollout",
         "pin both sides to a compatible pair, roll the newer side back",
         "compatibility matrix in CI, version labels on every hop, staged rollout order",
         ((3, "router and engine versions differ", eq("sig:router_engine_version_skew", True)),
          (2, "error finishes present", gt("vllm:request_success@rate:error", 1e-9)),
          (1, "length share moved", share_up("length", 0.15)))),
]
