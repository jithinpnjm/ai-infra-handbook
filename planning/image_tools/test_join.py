import re

labels_data = [
    {
        "expected": "Scheduled, then rejected: scheduler and kubelet disagree",
        "lines": [
            "Scheduled, then rejected:",
            "scheduler and kubelet disagree"
        ],
        "fs": 48
    },
    {
        "expected": "kube-scheduler: sees requests, labels, allocatable; not NUMA alignment",
        "lines": [
            "kube-scheduler:",
            "sees requests, labels,",
            "allocatable; not",
            "NUMA alignment"
        ],
        "fs": 26
    },
    {
        "expected": "places a pod on a node (bind)",
        "lines": [
            "places a pod on a node",
            "(bind)"
        ],
        "fs": 26
    },
    {
        "expected": "kubelet Topology Manager: at admission tries to align CPU, memory and devices on one NUMA node",
        "lines": [
            "kubelet Topology Manager:",
            "at admission tries to align",
            "CPU, memory and devices",
            "on one NUMA node"
        ],
        "fs": 25
    },
    {
        "expected": "rejects with TopologyAffinityError because no aligned set exists",
        "lines": [
            "rejects with",
            "TopologyAffinityError",
            "because no aligned set exists"
        ],
        "fs": 25
    },
    {
        "expected": "Pod ends failed after binding",
        "lines": [
            "Pod ends failed after binding"
        ],
        "fs": 28
    },
    {
        "expected": "NodeResourceTopology (NFD) so the scheduler sees NUMA zones",
        "lines": [
            "NodeResourceTopology (NFD)",
            "so the scheduler",
            "sees NUMA zones"
        ],
        "fs": 25
    },
    {
        "expected": "align kubelet policy with NUMA-aware scheduling",
        "lines": [
            "align kubelet policy with",
            "NUMA-aware scheduling"
        ],
        "fs": 25
    },
    {
        "expected": "DRA with attributes",
        "lines": [
            "DRA with attributes"
        ],
        "fs": 26
    },
    {
        "expected": "label nodes topology.example.com/block, /rack, /leaf, /nvlink-domain or use cloud topology.kubernetes.io labels",
        "lines": [
            "label nodes",
            "topology.example.com/block,",
            "/rack, /leaf, /nvlink-domain",
            "or use cloud",
            "topology.kubernetes.io labels"
        ],
        "fs": 24
    },
    {
        "expected": "a job spread over wrong racks loses bandwidth on every all-reduce and nothing in the logs shows an error",
        "lines": [
            "a job spread over wrong racks",
            "loses bandwidth on every",
            "all-reduce and nothing in",
            "the logs shows an error"
        ],
        "fs": 24
    },
    {
        "expected": "NVL72 domain is a rack-scale unit: schedule whole-domain jobs onto one domain",
        "lines": [
            "NVL72 domain is a",
            "rack-scale unit:",
            "schedule whole-domain",
            "jobs onto one domain"
        ],
        "fs": 25
    }
]

print("Checking joined text matches:")
all_ok = True
for item in labels_data:
    joined = " ".join(item["lines"])
    ok = (joined == item["expected"])
    if not ok:
        all_ok = False
        print(f"MISMATCH:\n  expected: '{item['expected']}'\n  got:      '{joined}'")
    else:
        print(f"OK: '{joined}'")

print("All matched:", all_ok)
