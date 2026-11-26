import xml.etree.ElementTree as ET
import re

# Test layout and text length
labels = [
    ("Title", "Scheduled, then rejected: scheduler and kubelet disagree", 48, True),
    ("Actor 1", "kube-scheduler: sees requests, labels, allocatable; not NUMA alignment", 28, True),
    ("Message 1", "places a pod on a node (bind)", 26, True),
    ("Actor 2", "kubelet Topology Manager: at admission tries to align CPU, memory and devices on one NUMA node", 28, True),
    ("Message 2", "rejects with TopologyAffinityError because no aligned set exists", 26, True),
    ("Outcome", "Pod ends failed after binding", 28, True),
    ("Fix 1", "NodeResourceTopology (NFD) so the scheduler sees NUMA zones", 25, False),
    ("Fix 2", "align kubelet policy with NUMA-aware scheduling", 25, False),
    ("Fix 3", "DRA with attributes", 26, False),
    ("Related 1", "label nodes topology.example.com/block, /rack, /leaf, /nvlink-domain or use cloud topology.kubernetes.io labels", 24, False),
    ("Related 2", "a job spread over wrong racks loses bandwidth on every all-reduce and nothing in the logs shows an error", 24, False),
    ("Related 3", "NVL72 domain is a rack-scale unit: schedule whole-domain jobs onto one domain", 24, False)
]

print(f"Total labels: {len(labels)}")
for name, text, fs, is_bold in labels:
    w = len(text) * fs * 0.6
    print(f"{name:12s} ({fs}px): len={len(text):3d}, est_width={w:6.1f} | '{text}'")
