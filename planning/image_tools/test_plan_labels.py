import xml.etree.ElementTree as ET
import re

# Test the 9 labels:
labels = [
    "A CPU limit of 1 and five busy threads",
    "limit 1 CPU = 100 ms of CPU time per 100 ms period regardless of thread count",
    "cpu.stat nr_throttled counts it",
    "Timeline of one 100 ms CFS period",
    "the shared budget of 100 ms of CPU time is used up in the first 20 ms (5 threads times 20 ms)",
    "throttled for the remaining 80 ms even though the node may have idle CPU",
    "the next period starts and the budget refreshes",
    "average looks fine, tail latency grows; requests arriving late in a period wait",
    "default timeoutSeconds 1 on a throttled pod can fail a healthy liveness probe past 1000 ms and restart a healthy container; raise timeoutSeconds to 5 to 10 seconds"
]

print(f"Total labels: {len(labels)}")
for i, l in enumerate(labels, 1):
    print(f"{i}: {l}")
