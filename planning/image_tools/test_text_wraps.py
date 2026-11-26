import re

labels = {
    0: "Cluster autoscaler: pending pods, node groups and the settings that matter",
    1: "HPA asks for more replicas",
    2: "pods sit Pending: no node has a free GPU",
    3: "cluster autoscaler notices pending pods that a node group could fit",
    4: "asks the cloud for a node; provisioning clock starts",
    5: "node registers, image pull, weight load, ready",
    6: "replica count rose at once while serving count stayed flat; that gap is what to explain",
    7: "expander chooses which node group to grow: random, most-pods, least-waste, price, priority (rank GPU types)",
    8: "--max-node-provision-time default 15 minutes: if a node has not registered by then the autoscaler stops counting it, which is why you keep warm capacity",
    9: "scale-down: node considered when pod CPU and memory requests sum below 50 percent of allocatable; must stay unneeded 10 minutes; held 10 minutes after a scale-up; evicts through the eviction API for up to 2 minutes; accelerator flag scale-down-gpu-utilization-threshold default 0.5",
    10: "autoscaling min and max node count flags; page gives no defaults or timings; keep a CPU node group of at least two nodes (or autoscaling) so CoreDNS and networking add-ons run there; known issue with GPU Operator and Network Operator creating extra nodes, not reproduced"
}

# Left column: x = 50, w = 550. Inside box, icon is on left (56px) or text is beside icon?
# If icon is on left (w=56), e.g. x=70, text starts at x=150.
# Available text width = 550 - (150 - 50) - 20 = 430px.
# Or if text is centered or left-aligned with icon on left:
# Let's test left box width = 540.
