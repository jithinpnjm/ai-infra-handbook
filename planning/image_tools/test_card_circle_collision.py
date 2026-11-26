import re

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

items = [
    # 1: U -> A
    {"step": 1, "src": "U", "dst": "A", "text": "create Pod (admission, defaults, SA token, quota)", "type": "line_r"},
    # 2: A -> S
    {"step": 2, "src": "A", "dst": "S", "text": "watch: Pod with no nodeName", "type": "dash_r"},
    # 3: S -> A
    {"step": 3, "src": "S", "dst": "A", "text": "bind Pod → node (spec.nodeName)", "type": "line_l"},
    # 4: A -> K
    {"step": 4, "src": "A", "dst": "K", "text": "watch: Pod bound to my node", "type": "dash_r"},
    # 5: K -> K
    {"step": 5, "src": "K", "dst": "K", "text": "admit pod (resources, node-fit, kernel params), create pod dirs", "type": "self_r"},
    # 6: K -> D
    {"step": 6, "src": "K", "dst": "D", "text": "Allocate(GPU devices) → env/mounts/CDI names", "type": "line_r"},
    # 7: K -> V
    {"step": 7, "src": "K", "dst": "V", "text": "NodeStageVolume / NodePublishVolume (PVCs)", "type": "line_r"},
    # 8: K -> R
    {"step": 8, "src": "K", "dst": "R", "text": "RunPodSandbox", "type": "line_r"},
    # 9: R -> C
    {"step": 9, "src": "R", "dst": "C", "text": "ADD (netns, IP, routes)", "type": "line_r"},
    # 10: K -> R
    {"step": 10, "src": "K", "dst": "R", "text": "PullImage (per container)", "type": "line_r"},
    # 11: K -> R
    {"step": 11, "src": "K", "dst": "R", "text": "CreateContainer / StartContainer (init containers first)", "type": "line_r"},
    # 12: R -> X
    {"step": 12, "src": "R", "dst": "X", "text": "create namespaces, cgroups, mounts, exec", "type": "line_r"},
    # 13: K -> A
    {"step": 13, "src": "K", "dst": "A", "text": "status updates (PodScheduled, Initialized, ContainersReady, Ready)", "type": "line_l"},
    # Note over K,X
    {"step": "note", "src": "K", "dst": "X", "text": "running: probes, log rotation, cgroup accounting, status heartbeats", "type": "note"},
    # 14: U -> A
    {"step": 14, "src": "U", "dst": "A", "text": "delete Pod", "type": "line_r"},
    # 15: A -> K
    {"step": 15, "src": "A", "dst": "K", "text": "deletionTimestamp set (grace)", "type": "dash_r"},
    # 16: K -> X
    {"step": 16, "src": "K", "dst": "X", "text": "preStop, SIGTERM, wait, SIGKILL", "type": "line_r"},
    # 17: K -> R
    {"step": 17, "src": "K", "dst": "R", "text": "StopContainer, StopPodSandbox → CNI DEL", "type": "line_r"},
    # 18: K -> V
    {"step": 18, "src": "K", "dst": "V", "text": "unmount volumes", "type": "line_r"},
    # 19: K -> A
    {"step": 19, "src": "K", "dst": "A", "text": "remove Pod object (grace 0)", "type": "line_l"}
]

cur_y = 265.0
prev_src = None
for item in items:
    s = item["src"]
    if prev_src == "K" and s == "K":
        cur_y += 49.0
    else:
        if prev_src is not None:
            cur_y += 42.0
    item["y"] = cur_y
    prev_src = s
    
    # Calculate card x, y, w, h
    t = item["text"]
    w = len(t) * 0.6 * 24 + 32 # with 16px pad each side
    item["w"] = w
    item["h"] = 32
    item["cy"] = cur_y
    item["card_y"] = cur_y - 34
    
    # Where does card sit?
    # Rightward arrows: card starts at centers[src] + 28
    # Leftward arrows: card ends at centers[src] - 28, or sits between
    if item["type"] in ("line_r", "dash_r", "self_r"):
        item["card_x"] = centers[item["src"]] + 28
    elif item["type"] == "line_l":
        # Leftward arrow: src > dst
        # If card fits between dst and src:
        # e.g. Step 3: S(475) -> A(312.5). text len=31, w=478.4 px.
        # It can start at centers[dst] - 150 or similar, or centers[src] - w - 28
        item["card_x"] = centers[item["src"]] - 28 - w
        if item["card_x"] < 40:
            item["card_x"] = 40
    elif item["type"] == "note":
        item["card_x"] = centers["K"] - 30
        item["w"] = centers["X"] - centers["K"] + 60
        item["h"] = 36
        item["card_y"] = cur_y - 18

print("Layout computation complete.")
