import re

labels = [
    "Shard Prometheus by function, federate only aggregates",
    "query timeout",
    "One server holds all active series in memory",
    "Shard 1: platform",
    "Shard 2: tenant workloads",
    "Shard 3: GPU and node exporters",
    "Only aggregates and SLI series upward",
    "Never federate raw per-pod series",
    "Cost: fragmented data, a question across shards needs two queries and a join",
    "Shard by function or region first, aggregate with recording rules."
]

print("Total expected labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l}")

