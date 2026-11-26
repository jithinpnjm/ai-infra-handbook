import xml.etree.ElementTree as ET
import re
import pathlib

# Row data definition
rows_data = [
    {
        "id": "row-1",
        "h": 150,
        "c1": ["LLM online inference", "(vLLM, Triton, TGI)"],
        "c2": [
            "HPA or KEDA on queue depth,",
            "concurrency, KV-cache;",
            "min 1 to 2; slow scale-down"
        ],
        "c3": [
            "fixed reserved GPU pool plus burst",
            "autoscaled pool, overprovision",
            "pause pods, pre-pulled images;",
            "replica start 2 to 15 min"
        ],
        "orange": True,
        "icon": "chip"
    },
    {
        "id": "row-2",
        "h": 100,
        "c1": ["Embedding and", "reranker services"],
        "c2": [
            "HPA on CPU or GPU",
            "concurrency, smaller replicas"
        ],
        "c3": ["autoscaled L4 or L40S pool"],
        "orange": False,
        "icon": "layers"
    },
    {
        "id": "row-3",
        "h": 100,
        "c1": ["Batch inference"],
        "c2": [
            "KEDA on queue backlog,",
            "Jobs with parallelism"
        ],
        "c3": [
            "cluster autoscaler or Karpenter on",
            "Pending, spot allowed; scale to zero"
        ],
        "orange": False,
        "icon": "stack"
    },
    {
        "id": "row-4",
        "h": 124,
        "c1": ["Training"],
        "c2": [
            "not HPA-based, fixed job size,",
            "elastic training can scale",
            "workers within min and max"
        ],
        "c3": [
            "admit with Kueue, provision nodes",
            "atomically; scale events trigger",
            "rendezvous restarts"
        ],
        "orange": False,
        "icon": "cluster"
    },
    {
        "id": "row-5",
        "h": 100,
        "c1": ["Data processing", "(Spark, Ray)"],
        "c2": [
            "operator-driven dynamic",
            "allocation"
        ],
        "c3": [
            "Ray autoscaler talks to Kubernetes",
            "through KubeRay"
        ],
        "orange": False,
        "icon": "gear"
    },
    {
        "id": "row-6",
        "h": 100,
        "c1": ["Interactive notebooks"],
        "c2": ["none per user"],
        "c3": [
            "pool scaling plus idle culling,",
            "quotas cap spend"
        ],
        "orange": False,
        "icon": "window"
    },
    {
        "id": "row-7",
        "h": 90,
        "c1": ["Gateways and ingress"],
        "c2": ["HPA on CPU, RPS or connections"],
        "c3": ["keep at least 3 for HA"],
        "orange": False,
        "icon": "shield"
    }
]

# Total height calculation:
# Canvas: 1600 x 1130
H_CANVAS = 1130

# Layout coordinates:
# Header: y=92, h=54
# Gaps: 12 px between rows
# Rule strip at bottom: h=84

