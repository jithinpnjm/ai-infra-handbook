import re
import json

# Expected labels
source_title = "Cluster autoscaler: pending pods, node groups and the settings that matter"
source_labels = [
    "Cluster autoscaler: pending pods, node groups and the settings that matter",
    "HPA asks for more replicas",
    "pods sit Pending: no node has a free GPU",
    "cluster autoscaler notices pending pods that a node group could fit",
    "asks the cloud for a node; provisioning clock starts",
    "node registers, image pull, weight load, ready",
    "replica count rose at once while serving count stayed flat; that gap is what to explain",
    "expander chooses which node group to grow: random, most-pods, least-waste, price, priority (rank GPU types)",
    "--max-node-provision-time default 15 minutes: if a node has not registered by then the autoscaler stops counting it, which is why you keep warm capacity",
    "scale-down: node considered when pod CPU and memory requests sum below 50 percent of allocatable; must stay unneeded 10 minutes; held 10 minutes after a scale-up; evicts through the eviction API for up to 2 minutes; accelerator flag scale-down-gpu-utilization-threshold default 0.5",
    "autoscaling min and max node count flags; page gives no defaults or timings; keep a CPU node group of at least two nodes (or autoscaling) so CoreDNS and networking add-ons run there; known issue with GPU Operator and Network Operator creating extra nodes, not reproduced"
]

print("Loaded labels successfully.")
