"""Autoscaling policy as code for the shared inference pool (chapter 19.12).

One function turns a workload and its measured replica ceiling into a KEDA ScaledObject.
A second function rejects policies that break the rules from chapters 20.20 and 19.12.
Timings are assumptions: replace them with your own measured cold start.
Standard library only (plus PyYAML for the dump helper).
"""
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.join(_HERE, "..", "part20")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import c12_size_inference_pool as pool  # noqa: E402
import c20_autoscale_sim as sim  # noqa: E402

PROM = "http://prometheus.monitoring.svc:9090"
INFLIGHT_FRACTION = 0.7   # target in-flight per replica, as a fraction of the design batch
KV_TARGET = 0.8           # average KV-cache usage that asks for one more replica
# Assumed cold-start parts, seconds. A replica on a node that is already free skips node and image.
COLD = {"node_provision_s": 240, "image_pull_s": 90, "weight_load_s": 120, "warmup_s": 30}


def inflight_target(w):
    """In-flight requests per replica. By Little's law the ceiling is the design batch."""
    return max(1, round(INFLIGHT_FRACTION * w.batch))


def cold_start(has_node=True):
    return sim.cold_start_s(COLD, has_node)


def headroom_replicas(w, ramp_qps_per_min, has_node=True):
    """Replicas to hold spare so growth during one cold start is covered. From 20.20."""
    cap = pool.replica_capacity(w)
    return sim.lead_time_headroom(ramp_qps_per_min, cold_start(has_node), cap["rate_qps"])


def scale_down_window_s(has_node=True):
    """My reasoning: wait at least three cold starts before removing a replica, so one flap is cheap."""
    return max(900, 3 * cold_start(has_node))


def max_replicas(w, pool_gpus_for_model):
    return max(w.min_replicas, pool_gpus_for_model // w.tp)


def scaled_object(w, max_r, namespace="llm"):
    """KEDA ScaledObject for one model. Hot and warm models scale on in-flight requests and KV cache.
    The batch model scales on a queue metric from our own gateway, because vLLM metrics do not exist at zero pods."""
    sel = f'namespace="{namespace}",pod=~"vllm-{w.name}-.*"'
    if w.tier == "batch":
        triggers = [{
            "type": "prometheus", "name": "queue", "metricType": "AverageValue",
            "metadata": {
                "serverAddress": PROM,
                "query": f'sum(gateway_queue_depth{{model="{w.name}"}})',
                "threshold": str(inflight_target(w)),
                "activationThreshold": "1",
                "ignoreNullValues": "true",
            }}]
        down = {"stabilizationWindowSeconds": 300, "selectPolicy": "Min",
                "policies": [{"type": "Percent", "value": 100, "periodSeconds": 60}]}
        fallback = None
    else:
        triggers = [
            {"type": "prometheus", "name": "inflight", "metricType": "AverageValue",
             "metadata": {"serverAddress": PROM,
                          "query": f"sum(vllm:num_requests_running{{{sel}}}) + sum(vllm:num_requests_waiting{{{sel}}})",
                          "threshold": str(inflight_target(w)), "ignoreNullValues": "false"}},
            {"type": "prometheus", "name": "kv_cache", "metricType": "Value",
             "metadata": {"serverAddress": PROM,
                          "query": f"avg(vllm:kv_cache_usage_perc{{{sel}}})",
                          "threshold": str(KV_TARGET), "ignoreNullValues": "false"}},
        ]
        down = {"stabilizationWindowSeconds": scale_down_window_s(),
                "selectPolicy": "Min", "policies": [{"type": "Pods", "value": 1, "periodSeconds": 180}]}
        fallback = {"failureThreshold": 3, "replicas": max(w.min_replicas, 2), "behavior": "currentReplicas"}
    spec = {
        "scaleTargetRef": {"name": f"vllm-{w.name}"},
        "pollingInterval": 15,
        "minReplicaCount": w.min_replicas,
        "maxReplicaCount": max_r,
        "advanced": {"horizontalPodAutoscalerConfig": {"behavior": {
            "scaleUp": {"stabilizationWindowSeconds": 0,
                        "policies": [{"type": "Percent", "value": 100, "periodSeconds": 60}]},
            "scaleDown": down}}},
        "triggers": triggers,
    }
    if fallback:
        spec["fallback"] = fallback
    if w.tier == "batch":
        spec["cooldownPeriod"] = 300
    return {"apiVersion": "keda.sh/v1alpha1", "kind": "ScaledObject",
            "metadata": {"name": f"vllm-{w.name}", "namespace": namespace}, "spec": spec}


def check_policy(obj, w, pool_gpus):
    """Return a list of problems. An empty list means the policy passes the chapter's rules."""
    s, bad = obj["spec"], []
    trig = s.get("triggers", [])
    if w.tier in ("hot", "warm") and s.get("minReplicaCount", 0) < max(1, w.min_replicas):
        bad.append("hot or warm model must keep its minimum replicas, never scale to zero")
    if w.tier == "hot" and s.get("minReplicaCount", 0) < 2:
        bad.append("hot model needs at least two replicas so one failure is not an outage")
    if not trig:
        bad.append("no triggers")
    for t in trig:
        q = t["metadata"].get("query", "")
        if t["type"] in ("cpu", "memory") or "DCGM_FI_DEV_GPU_UTIL" in q:
            bad.append("CPU or GPU utilisation is not a valid signal for an LLM engine")
    if s.get("maxReplicaCount", 0) * w.tp > pool_gpus:
        bad.append("maxReplicaCount needs more GPUs than the pool gives this model")
    down = s["advanced"]["horizontalPodAutoscalerConfig"]["behavior"]["scaleDown"]
    if w.tier != "batch" and down["stabilizationWindowSeconds"] < 3 * cold_start():
        bad.append("scale-down window is shorter than three cold starts, so the pool will flap")
    if w.tier != "batch" and "fallback" not in s:
        bad.append("no fallback: a broken metrics query would freeze scaling at the wrong size")
    if s.get("minReplicaCount", 0) > s.get("maxReplicaCount", 0):
        bad.append("min above max")
    return bad


def all_policies(pool_gpus_by_model=None):
    """Policies for the three scaled workloads, with the GPUs each may grow to."""
    gpus = pool_gpus_by_model or {"assistant": 8, "docsum": 8, "analyst": 16}
    return {w.name: scaled_object(w, max_replicas(w, gpus[w.name])) for w in pool.WORKLOADS}


def dump(obj):
    import yaml
    return yaml.safe_dump(obj, sort_keys=False, width=1000)


if __name__ == "__main__":
    for name, o in all_policies().items():
        print("---", name)
        print(dump(o))
    print("cold start with a free node:", cold_start(True), "s; without:", cold_start(False), "s")
