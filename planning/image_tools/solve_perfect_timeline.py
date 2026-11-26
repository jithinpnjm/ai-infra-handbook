import xml.etree.ElementTree as ET
import re

# Let's test a complete layout solver
H = 1200
W = 1600

centers = {
    "U": 150.0,
    "A": 312.5,
    "S": 475.0,
    "K": 637.5,
    "R": 800.0,
    "C": 962.5,
    "V": 1125.0,
    "D": 1287.5,
    "X": 1450.0
}

# Check participants layout
headers = [
    # Row 1 (y=48 to 126, height=78)
    {"id": "U", "row": 1, "cx": 150.0, "lines": ["User /", "controller"], "icon": "window"},
    {"id": "S", "row": 1, "cx": 475.0, "lines": ["Scheduler"], "icon": "clock"},
    {"id": "R", "row": 1, "cx": 800.0, "lines": ["containerd", "(CRI)"], "icon": "box"},
    {"id": "V", "row": 1, "cx": 1125.0, "lines": ["CSI node", "plugin"], "icon": "cylinder"},
    {"id": "X", "row": 1, "cx": 1450.0, "lines": ["runc /", "kernel"], "icon": "terminal"},
    # Row 2 (y=134 to 212, height=78)
    {"id": "A", "row": 2, "cx": 312.5, "lines": ["API server", "(+etcd)"], "icon": "lock"},
    {"id": "K", "row": 2, "cx": 637.5, "lines": ["Kubelet"], "icon": "gear"},
    {"id": "C", "row": 2, "cx": 962.5, "lines": ["CNI", "plugin"], "icon": "network"},
    {"id": "D", "row": 2, "cx": 1287.5, "lines": ["Device", "plugin"], "icon": "chip"}
]

print("Participant headers defined.")
