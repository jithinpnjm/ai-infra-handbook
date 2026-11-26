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
    {"num": 1, "src": "U", "dst": "A", "type": "msg_r",
     "text": "create Pod (admission, defaults, SA token, quota)",
     "card_x": 180.0},
    
    # 2: A -->> S
    {"num": 2, "src": "A", "dst": "S", "type": "dash_r",
     "text": "watch: Pod with no nodeName",
     "card_x": 342.5},
    
    # 3: S -> A
    {"num": 3, "src": "S", "dst": "A", "type": "msg_l",
     "text": "bind Pod → node (spec.nodeName)",
     "card_x": 50.0},
    
    # 4: A -->> K
    {"num": 4, "src": "A", "dst": "K", "type": "dash_r",
     "text": "watch: Pod bound to my node",
     "card_x": 342.5},
    
    # 5: K -> K
    {"num": 5, "src": "K", "dst": "K", "type": "self_r",
     "text": "admit pod (resources, node-fit, kernel params), create pod dirs",
     "card_x": 580.0},
    
    # 6: K -> D
    {"num": 6, "src": "K", "dst": "D", "type": "msg_r",
     "text": "Allocate(GPU devices) → env/mounts/CDI names",
     "card_x": 667.5},
    
    # 7: K -> V
    {"num": 7, "src": "K", "dst": "V", "type": "msg_r",
     "text": "NodeStageVolume / NodePublishVolume (PVCs)",
     "card_x": 667.5},
    
    # 8: K -> R
    {"num": 8, "src": "K", "dst": "R", "type": "msg_r",
     "text": "RunPodSandbox",
     "card_x": 667.5},
    
    # 9: R -> C
    {"num": 9, "src": "R", "dst": "C", "type": "msg_r",
     "text": "ADD (netns, IP, routes)",
     "card_x": 830.0},
    
    # 10: K -> R
    {"num": 10, "src": "K", "dst": "R", "type": "msg_r",
     "text": "PullImage (per container)",
     "card_x": 667.5},
    
    # 11: K -> R
    {"num": 11, "src": "K", "dst": "R", "type": "msg_r",
     "text": "CreateContainer / StartContainer (init containers first)",
     "card_x": 667.5},
    
    # 12: R -> X
    {"num": 12, "src": "R", "dst": "X", "type": "msg_r",
     "text": "create namespaces, cgroups, mounts, exec",
     "card_x": 830.0},
    
    # 13: K -> A
    {"num": 13, "src": "K", "dst": "A", "type": "msg_l",
     "text": "status updates (PodScheduled, Initialized, ContainersReady, Ready)",
     "card_x": 50.0},
    
    # Note over K,X
    {"type": "note", "src": "K", "dst": "X",
     "text": "running: probes, log rotation, cgroup accounting, status heartbeats",
     "card_x": 520.0},
    
    # 14: U -> A
    {"num": 14, "src": "U", "dst": "A", "type": "msg_r",
     "text": "delete Pod",
     "card_x": 180.0},
    
    # 15: A -->> K
    {"num": 15, "src": "A", "dst": "K", "type": "dash_r",
     "text": "deletionTimestamp set (grace)",
     "card_x": 342.5},
    
    # 16: K -> X
    {"num": 16, "src": "K", "dst": "X", "type": "msg_r",
     "text": "preStop, SIGTERM, wait, SIGKILL",
     "card_x": 667.5},
    
    # 17: K -> R
    {"num": 17, "src": "K", "dst": "R", "type": "msg_r",
     "text": "StopContainer, StopPodSandbox → CNI DEL",
     "card_x": 667.5},
    
    # 18: K -> V
    {"num": 18, "src": "K", "dst": "V", "type": "msg_r",
     "text": "unmount volumes",
     "card_x": 667.5},
    
    # 19: K -> A
    {"num": 19, "src": "K", "dst": "A", "type": "msg_l",
     "text": "remove Pod object (grace 0)",
     "card_x": 180.0}
]

for item in items:
    t = item["text"]
    est_w = len(t) * 0.6 * 24
    bw = est_w + 36 # at least 18px pad on each side
    item["bw"] = bw
    right_x = item["card_x"] + bw
    pad = (bw - est_w) / 2
    label = item.get("num", "note")
    print(f"[{str(label):>4}] x=[{item['card_x']:6.1f}, {right_x:6.1f}] bw={bw:5.1f} pad={pad:4.1f} | '{t[:35]}...'")
    assert item["card_x"] >= 40.0, f"Left margin {item['card_x']} < 40!"
    assert right_x <= 1560.0, f"Right margin {right_x} > 1560!"
    assert pad >= 16.0, f"Pad {pad} < 16!"

print("\nALL 20 CARDS FIT WITHIN MARGINS AND HAVE PAD >= 16px! (PASS)")
