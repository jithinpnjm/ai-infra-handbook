import re

labels = [
    "Karpenter versus node groups, and the NodePool rules",
    "menu versus chef",
    "Cluster Autoscaler orders from a fixed menu of node groups, each with one shape",
    "Karpenter watches Pending pods, batches them, computes the best set of instance types that satisfy their constraints, and provisions just in time; bin-packing, spot handling with interruption notices, automatic rotation and drift correction",
    "annotated NodePool gpu-inference",
    "requirements instance-family In g6, g6e, p5",
    "capacity-type On-demand",
    "zones us-east-1a and us-east-1b",
    "taints nvidia.com/gpu=present NoSchedule (keeps ordinary pods off)",
    "nodeClassRef EC2NodeClass gpu",
    "expireAfter 720h",
    "limits nvidia.com/gpu 64 (cap on total GPUs)",
    "disruption consolidationPolicy WhenEmptyOrUnderutilized, consolidateAfter 10m, budgets nodes 10 percent",
    "consolidation can remove a node under a training job: set do-not-disrupt"
]

print("Total labels:", len(labels))
for i, l in enumerate(labels, 1):
    print(f"{i:2d}. {l}")
