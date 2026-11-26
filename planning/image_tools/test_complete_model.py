import re

# Let's verify all 16 labels
labels = [
    "From a vLLM metric to an HPA decision",
    "vLLM pod exposes vllm:num_requests_waiting",
    "Prometheus scrapes it",
    "prometheus-adapter rule: seriesQuery vllm:num_requests_waiting with namespace and pod labels; resources overrides map namespace and pod; name as vllm_requests_waiting; metricsQuery sum by group",
    "custom.metrics.k8s.io API",
    "HPA reads it and decides",
    "kafka_consumergroup_lag topic embed",
    "rule name kafka_lag",
    "external.metrics.k8s.io",
    "kubectl get --raw /apis/custom.metrics.k8s.io/v1beta1/namespaces/serving/pods/*/vllm_requests_waiting",
    "kubectl get --raw /apis/external.metrics.k8s.io/v1beta1/namespaces/serving/kafka_lag",
    "kubectl describe hpa vllm -n serving",
    "AbleToScale: can the HPA change the count at all",
    "ScalingActive: can it read the metrics",
    "ScalingLimited: has a minimum or maximum capped the result",
    "if the first command returns nothing, no amount of tuning helps"
]

banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for l in labels:
    words = re.findall(r'\b[a-zA-Z]+\b', l.lower())
    for b in banned:
        assert b not in words, f"Banned word '{b}' found in '{l}'"

print(f"All {len(labels)} labels verified: no banned words.")
