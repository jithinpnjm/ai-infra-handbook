import sys

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

# The 20 steps
steps_def = [
    # 1: U -> A
    {"num": 1, "src": "U", "dst": "A", "type": "msg_r",
     "lines": ["create Pod (admission, defaults, SA token, quota)"],
     "card_side": "right"},
    # 2: A -->> S
    {"num": 2, "src": "A", "dst": "S", "type": "dash_r",
     "lines": ["watch: Pod with no nodeName"],
     "card_side": "right"},
    # 3: S -> A
    {"num": 3, "src": "S", "dst": "A", "type": "msg_l",
     "lines": ["bind Pod → node", "(spec.nodeName)"],
     "card_side": "left"},
    # 4: A -->> K
    {"num": 4, "src": "A", "dst": "K", "type": "dash_r",
     "lines": ["watch: Pod bound to my node"],
     "card_side": "right"},
    # 5: K -> K
    {"num": 5, "src": "K", "dst": "K", "type": "self_r",
     "lines": ["admit pod (resources, node-fit,", "kernel params), create pod dirs"],
     "card_side": "right_self"},
    # 6: K -> D
    {"num": 6, "src": "K", "dst": "D", "type": "msg_r",
     "lines": ["Allocate(GPU devices) → env/mounts/CDI names"],
     "card_side": "right", "orange": True},
    # 7: K -> V
    {"num": 7, "src": "K", "dst": "V", "type": "msg_r",
     "lines": ["NodeStageVolume / NodePublishVolume (PVCs)"],
     "card_side": "right"},
    # 8: K -> R
    {"num": 8, "src": "K", "dst": "R", "type": "msg_r",
     "lines": ["RunPodSandbox"],
     "card_side": "right"},
    # 9: R -> C
    {"num": 9, "src": "R", "dst": "C", "type": "msg_r",
     "lines": ["ADD (netns, IP, routes)"],
     "card_side": "right"},
    # 10: K -> R
    {"num": 10, "src": "K", "dst": "R", "type": "msg_r",
     "lines": ["PullImage (per container)"],
     "card_side": "right"},
    # 11: K -> R
    {"num": 11, "src": "K", "dst": "R", "type": "msg_r",
     "lines": ["CreateContainer / StartContainer (init containers first)"],
     "card_side": "right"},
    # 12: R -> X
    {"num": 12, "src": "R", "dst": "X", "type": "msg_r",
     "lines": ["create namespaces, cgroups, mounts, exec"],
     "card_side": "right"},
    # 13: K -> A
    {"num": 13, "src": "K", "dst": "A", "type": "msg_l",
     "lines": ["status updates (PodScheduled,", "Initialized, ContainersReady, Ready)"],
     "card_side": "left"},
    # Note over K,X
    {"num": 0, "src": "K", "dst": "X", "type": "note",
     "lines": ["running: probes, log rotation,", "cgroup accounting, status heartbeats"]},
    # 14: U -> A
    {"num": 14, "src": "U", "dst": "A", "type": "msg_r",
     "lines": ["delete Pod"],
     "card_side": "right"},
    # 15: A -->> K
    {"num": 15, "src": "A", "dst": "K", "type": "dash_r",
     "lines": ["deletionTimestamp set (grace)"],
     "card_side": "right"},
    # 16: K -> X
    {"num": 16, "src": "K", "dst": "X", "type": "msg_r",
     "lines": ["preStop, SIGTERM, wait, SIGKILL"],
     "card_side": "right"},
    # 17: K -> R
    {"num": 17, "src": "K", "dst": "R", "type": "msg_r",
     "lines": ["StopContainer, StopPodSandbox → CNI DEL"],
     "card_side": "right"},
    # 18: K -> V
    {"num": 18, "src": "K", "dst": "V", "type": "msg_r",
     "lines": ["unmount volumes"],
     "card_side": "right"},
    # 19: K -> A
    {"num": 19, "src": "K", "dst": "A", "type": "msg_l",
     "lines": ["remove Pod object (grace 0)"],
     "card_side": "left"}
]

# Calculate dimensions for cards
for s in steps_def:
    max_len = max(len(l) for l in s["lines"])
    est_w = max_len * 24 * 0.6
    s["w"] = est_w + 36.0 # 18px padding on each side
    s["h"] = 28.0 if len(s["lines"]) == 1 else 48.0
    
print("Calculated dimensions.")
