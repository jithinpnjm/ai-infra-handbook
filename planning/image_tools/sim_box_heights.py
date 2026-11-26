import re

def text_lines(text, max_w, is_mono=False):
    # compute wrapped lines given max_w
    fs = 24
    char_w = fs * (0.62 if is_mono else 0.6)
    max_chars = int(max_w / char_w)
    words = text.split()
    lines = []
    cur = []
    for w in words:
        if cur and len(" ".join(cur + [w])) > max_chars:
            lines.append(" ".join(cur))
            cur = [w]
        else:
            cur.append(w)
    if cur:
        lines.append(" ".join(cur))
    return lines

# Let's inspect each node's text and optimal wrapping
nodes = {
    'vllm': 'vLLM pod exposes vllm:num_requests_waiting',
    'prom': 'Prometheus scrapes it',
    'rule_custom': 'prometheus-adapter rule: seriesQuery vllm:num_requests_waiting with namespace and pod labels; resources overrides map namespace and pod; name as vllm_requests_waiting; metricsQuery sum by group',
    'api_custom': 'custom.metrics.k8s.io API',
    'hpa': 'HPA reads it and decides',
    'kafka': 'kafka_consumergroup_lag topic embed',
    'rule_ext': 'rule name kafka_lag',
    'api_ext': 'external.metrics.k8s.io',
    'cmd_custom': 'kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/serving/pods/*/vllm_requests_waiting',
    'cmd_ext': 'kubectl get --raw /apis/external.metrics.k8s.io/v1beta1/namespaces/serving/kafka_lag',
    'cmd_hpa': 'kubectl describe hpa vllm -n serving',
    'cond_able': 'AbleToScale: can the HPA change the count at all',
    'cond_active': 'ScalingActive: can it read the metrics',
    'cond_limited': 'ScalingLimited: has a minimum or maximum capped the result',
    'note': 'if the first command returns nothing, no amount of tuning helps'
}

print("Node texts and lengths:")
for k, v in nodes.items():
    print(f"  {k:12s}: {len(v):3d} chars")
