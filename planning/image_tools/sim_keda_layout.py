import re
import xml.etree.ElementTree as ET

# Define the expected labels
expected_labels = [
    "KEDA: the switch and the dimmer",
    "Stage A",
    "zero to one: the switch, handled by KEDA operator (a plain HPA cannot scale to zero because the formula multiplies by zero)",
    "Stage B",
    "one to N: the dimmer, handled by the HPA that KEDA creates, fed by KEDA metrics adapter on the External Metrics API",
    "ScaledObject batch-embed",
    "minReplicaCount 0",
    "maxReplicaCount 50",
    "pollingInterval 15",
    "cooldownPeriod 300 (quiet time before one to zero)",
    "scaleDown stabilizationWindowSeconds 600",
    "kafka lagThreshold 200",
    "prometheus query sum vllm:num_requests_waiting threshold 5",
    "cron 0 8 to 0 20 Monday to Friday desiredReplicas 4 (pre-warm business hours)",
    "the largest desired count across active triggers wins, so cron acts as a floor in business hours",
    "ScaledJob transcribe-job",
    "one short Job per queued message, aws-sqs-queue queueLength 1, maxReplicaCount 20, strategy accurate",
    "ScaledObject",
    "keeps a long-running Deployment and changes its size",
    "scale-to-zero on a GPU service costs a cold start; fine for a nightly batch job, painful for a person typing in chat"
]

print(f"Total expected labels: {len(expected_labels)}")
