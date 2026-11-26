import math

labels = {
    "U": "Teams",
    "Q": "Queue and fair share",
    "P": "Topology-aware placer",
    "N": "Nodes in fabric blocks",
    "H": "Node health feed",
    "C": "Checkpoint store",
}

for k, v in labels.items():
    print(f"{k}: '{v}' (len={len(v)}, w30={len(v)*18}px, w32={len(v)*32*0.6:.1f}px)")
