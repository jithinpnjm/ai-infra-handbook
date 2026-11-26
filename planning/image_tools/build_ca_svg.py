import xml.etree.ElementTree as ET
import re, subprocess, pathlib

# Let's define the exact labels from the prompt:
labels = {
    "title": "Cluster Autoscaler: what triggers a node and what blocks its removal",
    "lane1": "Scale-up lane",
    "step1": "1 pods Pending with FailedScheduling for insufficient resources",
    "step2": "2 for each node group, simulate adding a node from its template: would the pod fit",
    "step3": "3 expander picks among groups: random picks any, least-waste leaves the fewest empty seats, most-pods carries the most waiting pods",
    "step4": "4 group size raised within its min and max, for example --nodes=1:10:worker-auto-scaling-group",
    "step5": "5 node joins, scheduler places pods",
    "lane2": "Scale-down lane",
    "scale_down_condition": "node utilisation (requests against allocatable) below --scale-down-utilization-threshold 0.5 for --scale-down-unneeded-time 10 min, then drain and remove",
    "blockers_header": "Blockers list",
    "blocker1": "pods without controllers",
    "blocker2": "emptyDir local storage unless annotated",
    "blocker3": "PDBs",
    "blocker4": "kube-system pods",
    "blocker5": "annotation cluster-autoscaler.kubernetes.io/safe-to-evict false",
    "blocker6": "recently added node (scale-down-delay-after-add)",
    "limits_header": "Limits",
    "limits": "reacts only to Pending pods; assumes homogeneous node groups; does not understand gang all-or-nothing needs",
    "gpu_header": "GPU settings",
    "gpu": "--gpu-total, burst pools min 0, --balance-similar-node-groups"
}

print(f"Total labels defined: {len(labels)}")
