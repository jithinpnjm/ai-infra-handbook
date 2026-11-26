import xml.etree.ElementTree as ET

# Centers of the 9 participants
centers = {
    'U': 150.0,
    'A': 312.5,
    'S': 475.0,
    'K': 637.5,
    'R': 800.0,
    'C': 962.5,
    'V': 1125.0,
    'D': 1287.5,
    'X': 1450.0
}

# Let's define the exact items with Y coordinates
# Headers end at y = 208.
# Let Step 1 start at cur_y = 216.

items = [
    # 1: U -> A
    {'id': 'step-1', 'num': 1, 'src': 'U', 'dst': 'A', 'type': 'msg_r',
     'text': 'create Pod (admission, defaults, SA token, quota)', 'h': 42, 'bx': 180.0},
    # 2: A -->> S
    {'id': 'step-2', 'num': 2, 'src': 'A', 'dst': 'S', 'type': 'dash_r',
     'text': 'watch: Pod with no nodeName', 'h': 42, 'bx': 342.5},
    # 3: S -> A (place box to right of S)
    {'id': 'step-3', 'num': 3, 'src': 'S', 'dst': 'A', 'type': 'msg_l_2',
     'lines': ['bind Pod → node', '(spec.nodeName)'], 'h': 50, 'bx': 505.0},
    # 4: A -->> K (place box to right of S)
    {'id': 'step-4', 'num': 4, 'src': 'A', 'dst': 'K', 'type': 'dash_r',
     'text': 'watch: Pod bound to my node', 'h': 42, 'bx': 505.0},
    # 5: K -> K
    {'id': 'step-5', 'num': 5, 'src': 'K', 'dst': 'K', 'type': 'self_r_2',
     'lines': ['admit pod (resources, node-fit,', 'kernel params), create pod dirs'], 'h': 52, 'bx': 707.5},
    # 6: K -> D
    {'id': 'step-6', 'num': 6, 'src': 'K', 'dst': 'D', 'type': 'msg_r',
     'text': 'Allocate(GPU devices) → env/mounts/CDI names', 'h': 44, 'bx': 667.5},
    # 7: K -> V
    {'id': 'step-7', 'num': 7, 'src': 'K', 'dst': 'V', 'type': 'msg_r',
     'text': 'NodeStageVolume / NodePublishVolume (PVCs)', 'h': 44, 'bx': 667.5},
    # 8: K -> R
    {'id': 'step-8', 'num': 8, 'src': 'K', 'dst': 'R', 'type': 'msg_r',
     'text': 'RunPodSandbox', 'h': 42, 'bx': 667.5},
    # 9: R -> C
    {'id': 'step-9', 'num': 9, 'src': 'R', 'dst': 'C', 'type': 'msg_r',
     'text': 'ADD (netns, IP, routes)', 'h': 42, 'bx': 830.0},
    # 10: K -> R (place box to right of R)
    {'id': 'step-10', 'num': 10, 'src': 'K', 'dst': 'R', 'type': 'msg_r',
     'text': 'PullImage (per container)', 'h': 44, 'bx': 830.0},
    # 11: K -> R
    {'id': 'step-11', 'num': 11, 'src': 'K', 'dst': 'R', 'type': 'msg_r',
     'text': 'CreateContainer / StartContainer (init containers first)', 'h': 42, 'bx': 667.5},
    # 12: R -> X
    {'id': 'step-12', 'num': 12, 'src': 'R', 'dst': 'X', 'type': 'msg_r',
     'text': 'create namespaces, cgroups, mounts, exec', 'h': 42, 'bx': 830.0},
    # 13: K -> A
    {'id': 'step-13', 'num': 13, 'src': 'K', 'dst': 'A', 'type': 'msg_l_2',
     'lines': ['status updates (PodScheduled,', 'Initialized, ContainersReady, Ready)'], 'h': 54, 'bx': 50.0},
    # Note over K,X (running phase - highlighted with orange)
    # Give enough gap so Note is below Circle 13
    {'id': 'note-running', 'num': None, 'src': 'K', 'dst': 'X', 'type': 'note',
     'lines': ['running: probes, log rotation,', 'cgroup accounting, status heartbeats'], 'h': 72, 'bx': 590.0},
    # 14: U -> A
    {'id': 'step-14', 'num': 14, 'src': 'U', 'dst': 'A', 'type': 'msg_r',
     'text': 'delete Pod', 'h': 42, 'bx': 180.0},
    # 15: A -->> K
    {'id': 'step-15', 'num': 15, 'src': 'A', 'dst': 'K', 'type': 'dash_r',
     'text': 'deletionTimestamp set (grace)', 'h': 44, 'bx': 342.5},
    # 16: K -> X
    {'id': 'step-16', 'num': 16, 'src': 'K', 'dst': 'X', 'type': 'msg_r',
     'text': 'preStop, SIGTERM, wait, SIGKILL', 'h': 44, 'bx': 667.5},
    # 17: K -> R
    {'id': 'step-17', 'num': 17, 'src': 'K', 'dst': 'R', 'type': 'msg_r',
     'text': 'StopContainer, StopPodSandbox → CNI DEL', 'h': 44, 'bx': 667.5},
    # 18: K -> V
    {'id': 'step-18', 'num': 18, 'src': 'K', 'dst': 'V', 'type': 'msg_r',
     'text': 'unmount volumes', 'h': 44, 'bx': 667.5},
    # 19: K -> A
    {'id': 'step-19', 'num': 19, 'src': 'K', 'dst': 'A', 'type': 'msg_l',
     'text': 'remove Pod object (grace 0)', 'h': 42, 'bx': 180.0}
]

cur_y = 216
for it in items:
    h = it['h']
    ay = cur_y + h - 6.0
    if it['type'] == 'note':
        by = cur_y + 18.0 # places Note 18px below cur_y
        print(f"Note: cur_y={cur_y}, by={by}, bottom={by+48}")
    else:
        print(f"{it['id']}: cur_y={cur_y}, ay={ay}, circle bottom={ay+24}")
    cur_y += h

print(f"Final cur_y = {cur_y}")
