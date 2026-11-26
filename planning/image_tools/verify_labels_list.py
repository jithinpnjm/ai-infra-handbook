import re
import xml.etree.ElementTree as ET

# List of the exact 13 source labels
expected_labels = [
    "Busy is not the same as useful",
    "Dashboard utilisation 95 percent",
    "requests finished on time",
    "requests finished too late to help anyone",
    "retries",
    "preempted requests whose cache was thrown away",
    "Goodput",
    "goodput QPS = QPS x fraction of requests within the objective",
    "cost per good token = cost per token / fraction within the objective",
    "if 5 percent of requests miss the objective, goodput is 95 percent of throughput and the cost of a good token rises by about 5 percent",
    "0.4 second p90 time to first token and 0.04 second p90 time per output token",
    "report goodput not throughput when comparing configurations, and name the latency objectives applied; do not push for full use if the latency objective is broken",
    "fraction of paid GPU time spent at the planned load, not the nvidia-smi figure"
]

print(f"Total expected labels: {len(expected_labels)}")
for i, l in enumerate(expected_labels, 1):
    print(f"{i:2d}. '{l}'")
