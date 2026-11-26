import re

H = 1200
centers = {
    "U": 148.0,
    "A": 311.0,
    "S": 474.0,
    "K": 637.0,
    "R": 800.0,
    "C": 963.0,
    "V": 1126.0,
    "D": 1289.0,
    "X": 1452.0
}

# The solved coordinates:
cy = {
    1: 264.0,
    2: 296.0,
    3: 328.0,
    4: 418.0,
    5: 450.0,
    6: 511.0,
    7: 559.0,
    8: 607.0,
    9: 639.0,
    10: 699.0,
    11: 747.0,
    12: 779.0,
    13: 811.0,
    14: 927.0,
    15: 959.0,
    16: 991.0,
    17: 1039.0,
    18: 1087.0,
    19: 1135.0
}

svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
svg.append('  <title>Timeline overview</title>')
svg.append('  <desc>Sequence diagram illustrating the end-to-end lifecycle of a Kubernetes Pod from user submission through scheduling, kubelet admission, GPU device plugin allocation, CSI volume mounting, containerd CRI sandbox and CNI networking, runc kernel container creation, steady-state running probes, and graceful termination.</desc>')
svg.append('  <defs>')
svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
svg.append('    </marker>')
svg.append('    <marker id="arrow-green-left" viewBox="0 0 18 18" refX="2" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 16 3 L 2 9 L 16 15 Z" fill="#207448" />')
svg.append('    </marker>')
svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
svg.append('    </marker>')
svg.append('  </defs>')
svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
svg.append('  <text x="800" y="42" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Timeline overview</text>')

# 9 Participants in two staggered tiers to allow generous box width (216px) and 30px bold font
# Tier 1: U, S, R, V, X at y=54..134
# Tier 2: A, K, C, D at y=142..222
headers = [
    # Row 1
    {"id": "U", "row": 1, "cx": 148.0, "lines": [("User / ", 0), ("controller", 25)], "icon": "window"},
    {"id": "S", "row": 1, "cx": 474.0, "lines": [("Scheduler", 14)], "icon": "clock"},
    {"id": "R", "row": 1, "cx": 800.0, "lines": [("containerd ", 0), ("(CRI)", 25)], "icon": "box"},
    {"id": "V", "row": 1, "cx": 1126.0, "lines": [("CSI node ", 0), ("plugin", 25)], "icon": "cylinder"},
    {"id": "X", "row": 1, "cx": 1452.0, "lines": [("runc / ", 0), ("kernel", 25)], "icon": "terminal"},
    # Row 2
    {"id": "A", "row": 2, "cx": 311.0, "lines": [("API server ", 0), ("(+etcd)", 25)], "icon": "lock"},
    {"id": "K", "row": 2, "cx": 637.0, "lines": [("Kubelet", 14)], "icon": "gear"},
    {"id": "C", "row": 2, "cx": 963.0, "lines": [("CNI ", 0), ("plugin", 25)], "icon": "network"},
    {"id": "D", "row": 2, "cx": 1289.0, "lines": [("Device ", 0), ("plugin", 25)], "icon": "chip"}
]

for h in headers:
    cx = h["cx"]
    by = 54 if h["row"] == 1 else 142
    bx = cx - 108.0
    bw = 216.0
    bh = 80.0
    gid = f"participant-{h['id']}"
    
    svg.append(f'  <g id="{gid}">')
    svg.append(f'    <rect x="{bx:.0f}" y="{by}" width="{bw:.0f}" height="{bh}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    
    # Icon
    icx = cx - 17.0
    icy = by + 6.0
    svg.append(f'    <g transform="translate({icx:.0f}, {icy:.0f})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    if h["icon"] == "window":
        svg.append('      <rect x="2" y="1" width="30" height="17" rx="3" />')
        svg.append('      <line x1="17" y1="18" x2="17" y2="23" />')
        svg.append('      <line x1="10" y1="23" x2="24" y2="23" />')
        svg.append('      <polyline points="7,6 12,9.5 7,13" />')
    elif h["icon"] == "clock":
        svg.append('      <circle cx="17" cy="12" r="10" />')
        svg.append('      <polyline points="17,6 17,12 21,14" />')
    elif h["icon"] == "box":
        svg.append('      <rect x="3" y="3" width="28" height="18" rx="2" />')
        svg.append('      <line x1="12" y1="3" x2="12" y2="21" />')
        svg.append('      <line x1="22" y1="3" x2="22" y2="21" />')
    elif h["icon"] == "cylinder":
        svg.append('      <ellipse cx="17" cy="6" rx="14" ry="4" />')
        svg.append('      <path d="M 3 6 v 12 c 0 2.2 6.3 4 14 4 s 14 -1.8 14 -4 v -12" />')
        svg.append('      <path d="M 3 12 c 0 2.2 6.3 4 14 4 s 14 -1.8 14 -4" />')
    elif h["icon"] == "terminal":
        svg.append('      <rect x="5" y="4" width="24" height="16" rx="2" />')
        svg.append('      <line x1="10" y1="0" x2="10" y2="4" /><line x1="17" y1="0" x2="17" y2="4" /><line x1="24" y1="0" x2="24" y2="4" />')
        svg.append('      <line x1="10" y1="20" x2="10" y2="24" /><line x1="17" y1="20" x2="17" y2="24" /><line x1="24" y1="20" x2="24" y2="24" />')
    elif h["icon"] == "lock":
        svg.append('      <path d="M 17 2 L 6 6 v 6 c 0 6 5 10 11 11 c 6 -1 11 -5 11 -11 v -6 Z" />')
    elif h["icon"] == "gear":
        svg.append('      <circle cx="17" cy="12" r="6" />')
        svg.append('      <path d="M 17 2 v 3 M 17 19 v 3 M 7 12 h 3 M 24 12 h 3 M 10 5 l 2 2 M 22 17 l 2 2 M 10 19 l 2 -2 M 22 7 l 2 -2" />')
    elif h["icon"] == "network":
        svg.append('      <circle cx="7" cy="12" r="4" /><circle cx="27" cy="12" r="4" />')
        svg.append('      <line x1="11" y1="12" x2="23" y2="12" />')
    elif h["icon"] == "chip":
        svg.append('      <rect x="4" y="3" width="26" height="18" rx="2" />')
        svg.append('      <circle cx="12" cy="12" r="3" /><circle cx="22" cy="12" r="3" />')
    svg.append('    </g>')
    
    # Text
    lines = h["lines"]
    if len(lines) == 1:
        svg.append(f'    <text x="{cx:.0f}" y="{by + 60}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{lines[0][0]}</text>')
    else:
        svg.append(f'    <text x="{cx:.0f}" y="{by + 50}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36"><tspan x="{cx:.0f}" dy="0">{lines[0][0]}</tspan><tspan x="{cx:.0f}" dy="25">{lines[1][0]}</tspan></text>')
    svg.append('  </g>')

# 9 Lifelines
for h in headers:
    cx = h["cx"]
    sy = 134 if h["row"] == 1 else 222
    svg.append(f'  <line x1="{cx:.0f}" y1="{sy}" x2="{cx:.0f}" y2="1155" stroke="#b8c9c0" stroke-width="2.5" stroke-dasharray="8 6" />')

# Steps data
steps_data = [
    # 1: U -> A
    {"num": 1, "src": "U", "dst": "A", "type": "msg_r",
     "text": "create Pod (admission, defaults, SA token, quota)", "rx": 182.0, "rw": 741.0, "rh": 28.0, "pos": "above"},
    
    # 2: A -->> S
    {"num": 2, "src": "A", "dst": "S", "type": "dash_r",
     "text": "watch: Pod with no nodeName", "rx": 345.0, "rw": 424.0, "rh": 28.0, "pos": "above"},
    
    # 3: S -> A (leftward)
    {"num": 3, "src": "S", "dst": "A", "type": "msg_l",
     "text": "bind Pod → node (spec.nodeName)", "rx": 184.0, "rw": 256.0, "rh": 50.0, "pos": "below",
     "lines": [("bind Pod → node ", 0), ("(spec.nodeName)", 24)], "tx": 312.0},
    
    # 4: A -->> K
    {"num": 4, "src": "A", "dst": "K", "type": "dash_r",
     "text": "watch: Pod bound to my node", "rx": 345.0, "rw": 424.0, "rh": 28.0, "pos": "above"},
    
    # 5: K -> K (self loop)
    {"num": 5, "src": "K", "dst": "K", "type": "self_r",
     "text": "admit pod (resources, node-fit, kernel params), create pod dirs", "rx": 705.0, "rw": 486.0, "rh": 50.0, "pos": "self",
     "lines": [("admit pod (resources, node-fit, ", 0), ("kernel params), create pod dirs", 24)], "tx": 948.0},
    
    # 6: K -> D (ORANGE HIGHLIGHT!)
    {"num": 6, "src": "K", "dst": "D", "type": "msg_r",
     "text": "Allocate(GPU devices) → env/mounts/CDI names", "rx": 671.0, "rw": 669.0, "rh": 28.0, "pos": "above", "orange": True},
    
    # 7: K -> V
    {"num": 7, "src": "K", "dst": "V", "type": "msg_r",
     "text": "NodeStageVolume / NodePublishVolume (PVCs)", "rx": 671.0, "rw": 640.0, "rh": 28.0, "pos": "above"},
    
    # 8: K -> R
    {"num": 8, "src": "K", "dst": "R", "type": "msg_r",
     "text": "RunPodSandbox", "rx": 671.0, "rw": 223.0, "rh": 28.0, "pos": "above"},
    
    # 9: R -> C
    {"num": 9, "src": "R", "dst": "C", "type": "msg_r",
     "text": "ADD (netns, IP, routes)", "rx": 834.0, "rw": 367.0, "rh": 28.0, "pos": "above"},
    
    # 10: K -> R
    {"num": 10, "src": "K", "dst": "R", "type": "msg_r",
     "text": "PullImage (per container)", "rx": 671.0, "rw": 396.0, "rh": 28.0, "pos": "above"},
    
    # 11: K -> R
    {"num": 11, "src": "K", "dst": "R", "type": "msg_r",
     "text": "CreateContainer / StartContainer (init containers first)", "rx": 671.0, "rw": 842.0, "rh": 28.0, "pos": "above"},
    
    # 12: R -> X
    {"num": 12, "src": "R", "dst": "X", "type": "msg_r",
     "text": "create namespaces, cgroups, mounts, exec", "rx": 834.0, "rw": 612.0, "rh": 28.0, "pos": "above"},
    
    # 13: K -> A (leftward)
    {"num": 13, "src": "K", "dst": "A", "type": "msg_l",
     "text": "status updates (PodScheduled, Initialized, ContainersReady, Ready)", "rx": 47.0, "rw": 556.0, "rh": 50.0, "pos": "above",
     "lines": [("status updates (PodScheduled, ", 0), ("Initialized, ContainersReady, Ready)", 24)], "tx": 325.0},
    
    # Note over K,X: running phase
    {"type": "note",
     "text": "running: probes, log rotation, cgroup accounting, status heartbeats", "rx": 607.0, "rw": 875.0, "rh": 56.0,
     "lines": [("running: probes, log rotation, ", 0), ("cgroup accounting, status heartbeats", 25)], "tx": 1044.5},
    
    # 14: U -> A
    {"num": 14, "src": "U", "dst": "A", "type": "msg_r",
     "text": "delete Pod", "rx": 182.0, "rw": 180.0, "rh": 28.0, "pos": "above"},
    
    # 15: A -->> K
    {"num": 15, "src": "A", "dst": "K", "type": "dash_r",
     "text": "deletionTimestamp set (grace)", "rx": 345.0, "rw": 453.0, "rh": 28.0, "pos": "above"},
    
    # 16: K -> X
    {"num": 16, "src": "K", "dst": "X", "type": "msg_r",
     "text": "preStop, SIGTERM, wait, SIGKILL", "rx": 671.0, "rw": 482.0, "rh": 28.0, "pos": "above"},
    
    # 17: K -> R
    {"num": 17, "src": "K", "dst": "R", "type": "msg_r",
     "text": "StopContainer, StopPodSandbox → CNI DEL", "rx": 671.0, "rw": 597.0, "rh": 28.0, "pos": "above"},
    
    # 18: K -> V
    {"num": 18, "src": "K", "dst": "V", "type": "msg_r",
     "text": "unmount volumes", "rx": 671.0, "rw": 252.0, "rh": 28.0, "pos": "above"},
    
    # 19: K -> A (leftward)
    {"num": 19, "src": "K", "dst": "A", "type": "msg_l",
     "text": "remove Pod object (grace 0)", "rx": 179.0, "rw": 424.0, "rh": 28.0, "pos": "above"}
]

for s in steps_data:
    stype = s.get("type")
    t = s["text"]
    rx = s["rx"]
    rw = s["rw"]
    rh = s["rh"]
    
    if stype == "note":
        y_note = cy[13] + 28.0
        svg.append('  <!-- Note over K,X -->')
        svg.append('  <g id="note-running">')
        svg.append(f'    <rect x="{rx:.0f}" y="{y_note:.0f}" width="{rw:.0f}" height="{rh:.0f}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" stroke-dasharray="6 4" />')
        lines = s["lines"]
        tx = s["tx"]
        svg.append(f'    <text x="{tx:.1f}" y="{y_note + 22.0:.0f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36"><tspan x="{tx:.1f}" dy="0">{lines[0][0]}</tspan><tspan x="{tx:.1f}" dy="{lines[1][1]}">{lines[1][0]}</tspan></text>')
        svg.append('  </g>')
        continue
        
    num = s["num"]
    ay = cy[num]
    pos = s["pos"]
    if pos == "above":
        ry = ay - rh - 4.0
    elif pos == "below":
        ry = ay + 4.0
    elif pos == "self":
        ry = ay - 25.0
        
    src = s["src"]
    dst = s["dst"]
    c_cx = centers[src]
    c_cy = ay
    is_orange = s.get("orange", False)
    
    svg.append(f'  <!-- Step {num} -->')
    svg.append(f'  <g id="step-{num}">')
    
    # Circle (r=24)
    circle_color = "#db8129" if is_orange else "#207448"
    svg.append(f'    <circle cx="{c_cx:.0f}" cy="{c_cy:.0f}" r="24" fill="{circle_color}" />')
    svg.append(f'    <text x="{c_cx:.0f}" y="{c_cy + 8:.0f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{num}</text>')
    
    # Arrow
    arrow_color = "#db8129" if is_orange else "#207448"
    marker_name = "arrow-orange" if is_orange else "arrow-green"
    
    if stype == "msg_r":
        x1 = c_cx + 24.0
        x2 = centers[dst]
        svg.append(f'    <line x1="{x1:.0f}" y1="{ay:.0f}" x2="{x2:.0f}" y2="{ay:.0f}" stroke="{arrow_color}" stroke-width="3" marker-end="url(#{marker_name})" />')
    elif stype == "dash_r":
        x1 = c_cx + 24.0
        x2 = centers[dst]
        svg.append(f'    <line x1="{x1:.0f}" y1="{ay:.0f}" x2="{x2:.0f}" y2="{ay:.0f}" stroke="{arrow_color}" stroke-width="3" stroke-dasharray="8 6" marker-end="url(#{marker_name})" />')
    elif stype == "msg_l":
        x1 = c_cx - 24.0
        x2 = centers[dst]
        marker_left = "arrow-green-left"
        svg.append(f'    <line x1="{x1:.0f}" y1="{ay:.0f}" x2="{x2:.0f}" y2="{ay:.0f}" stroke="{arrow_color}" stroke-width="3" marker-end="url(#{marker_left})" />')
    elif stype == "self_r":
        x1 = c_cx + 24.0
        x_loop = c_cx + 54.0
        marker_left = "arrow-green-left"
        svg.append(f'    <path d="M {x1:.0f} {ay - 12:.0f} H {x_loop:.0f} V {ay + 12:.0f} H {c_cx + 10:.0f}" fill="none" stroke="{arrow_color}" stroke-width="3" marker-end="url(#{marker_left})" />')
        
    # Card rect
    rect_stroke = "#db8129" if is_orange else "#207448"
    rect_stroke_w = "2" if is_orange else "1.5"
    svg.append(f'    <rect x="{rx:.0f}" y="{ry:.0f}" width="{rw:.0f}" height="{rh:.0f}" rx="6" fill="#ffffff" stroke="{rect_stroke}" stroke-width="{rect_stroke_w}" />')
    
    # Card text
    if "lines" in s:
        lines = s["lines"]
        tx = s["tx"]
        svg.append(f'    <text x="{tx:.1f}" y="{ry + 20.0:.0f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36"><tspan x="{tx:.1f}" dy="0">{lines[0][0]}</tspan><tspan x="{tx:.1f}" dy="{lines[1][1]}">{lines[1][0]}</tspan></text>')
    else:
        text_weight = ' font-weight="bold"' if is_orange else ''
        svg.append(f'    <text x="{rx + 14.0:.0f}" y="{ry + 22.0:.0f}" font-family="sans-serif" font-size="24"{text_weight} fill="#303a36">{t}</text>')
        
    svg.append('  </g>')

svg.append('</svg>')

final_svg = "\n".join(svg)
with open("test_timeline.svg", "w") as f:
    f.write(final_svg)

print("Saved test_timeline.svg successfully!")
