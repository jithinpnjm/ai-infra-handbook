import re
import sys
import xml.etree.ElementTree as ET
import pathlib

def build_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Timeline overview</title>')
    svg.append('  <desc>Sequence diagram illustrating Kubernetes pod lifecycle from creation, admission, scheduling, volume staging, network setup, container runtime execution, running probes, to pod deletion and resource cleanup.</desc>')
    
    # Marker definitions
    svg.append('  <defs>')
    # Green arrow right (18px)
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    # Green arrow left (18px)
    svg.append('    <marker id="arrow-green-left" viewBox="0 0 18 18" refX="2" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 16 3 L 2 9 L 16 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title (48px bold)
    svg.append('  <text x="800" y="44" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Timeline overview</text>')
    
    # 9 Participants centers
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
    
    # Participant Header Cards (height 90, width 220)
    # Row 1: y = 56 to 146
    # Row 2: y = 158 to 248
    headers = [
        # Row 1
        {"id": "U", "row": 1, "cx": 150.0, "lines": [("User /", 0), ("controller", 30)], "icon": "window"},
        {"id": "S", "row": 1, "cx": 475.0, "lines": [("Scheduler", 14)], "icon": "clock"},
        {"id": "R", "row": 1, "cx": 800.0, "lines": [("containerd", 0), ("(CRI)", 30)], "icon": "box"},
        {"id": "V", "row": 1, "cx": 1125.0, "lines": [("CSI node", 0), ("plugin", 30)], "icon": "cylinder"},
        {"id": "X", "row": 1, "cx": 1450.0, "lines": [("runc /", 0), ("kernel", 30)], "icon": "terminal"},
        # Row 2
        {"id": "A", "row": 2, "cx": 312.5, "lines": [("API server", 0), ("(+etcd)", 30)], "icon": "lock"},
        {"id": "K", "row": 2, "cx": 637.5, "lines": [("Kubelet", 14)], "icon": "gear"},
        {"id": "C", "row": 2, "cx": 962.5, "lines": [("CNI", 0), ("plugin", 30)], "icon": "network"},
        {"id": "D", "row": 2, "cx": 1287.5, "lines": [("Device", 0), ("plugin", 30)], "icon": "chip"}
    ]
    
    # Render Participant Headers
    for h in headers:
        cx = h["cx"]
        by = 56 if h["row"] == 1 else 158
        bx = cx - 110.0
        bw = 220.0
        bh = 90.0
        
        svg.append(f'  <g id="participant-{h["id"]} status">')
        svg.append(f'    <rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
        
        # Simple outline icons (about 56px, green stroke 4, fill none)
        icx = cx - 22
        icy = by + 6
        if h["icon"] == "window":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="2" y="2" width="40" height="28" rx="4"/>')
            svg.append('      <line x1="2" y1="10" x2="42" y2="10"/>')
            svg.append('      <circle cx="8" cy="6" r="1.5" fill="#207448"/>')
            svg.append('      <circle cx="14" cy="6" r="1.5" fill="#207448"/>')
            svg.append('    </g>')
        elif h["icon"] == "clock":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="22" cy="16" r="14"/>')
            svg.append('      <polyline points="22,8 22,16 28,16"/>')
            svg.append('    </g>')
        elif h["icon"] == "box":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="4" y="4" width="36" height="24" rx="3"/>')
            svg.append('      <line x1="4" y1="12" x2="40" y2="12"/>')
            svg.append('      <line x1="16" y1="12" x2="16" y2="28"/>')
            svg.append('    </g>')
        elif h["icon"] == "cylinder":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <ellipse cx="22" cy="8" rx="16" ry="5"/>')
            svg.append('      <path d="M 6 8 v 14 c 0 3 7 5 16 5 s 16 -2 16 -5 v -14"/>')
            svg.append('      <path d="M 6 15 c 0 3 7 5 16 5 s 16 -2 16 -5"/>')
            svg.append('    </g>')
        elif h["icon"] == "terminal":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="2" y="2" width="40" height="28" rx="4"/>')
            svg.append('      <polyline points="10,10 16,16 10,22"/>')
            svg.append('      <line x1="20" y1="22" x2="32" y2="22"/>')
            svg.append('    </g>')
        elif h["icon"] == "lock":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="8" y="12" width="28" height="18" rx="3"/>')
            svg.append('      <path d="M 14 12 v -5 c 0 -4.5 3.5 -6 8 -6 s 8 1.5 8 6 v 5"/>')
            svg.append('    </g>')
        elif h["icon"] == "gear":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="22" cy="16" r="8"/>')
            svg.append('      <path d="M 22 2 v 4 M 22 26 v 4 M 8 16 h 4 M 32 16 h 4"/>')
            svg.append('    </g>')
        elif h["icon"] == "network":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="22" cy="8" r="4"/>')
            svg.append('      <circle cx="10" cy="24" r="4"/>')
            svg.append('      <circle cx="34" cy="24" r="4"/>')
            svg.append('      <line x1="19" y1="11" x2="13" y2="21"/>')
            svg.append('      <line x1="25" y1="11" x2="31" y2="21"/>')
            svg.append('    </g>')
        elif h["icon"] == "chip":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="10" y="6" width="24" height="20" rx="3"/>')
            svg.append('      <line x1="15" y1="2" x2="15" y2="6"/>')
            svg.append('      <line x1="22" y1="2" x2="22" y2="6"/>')
            svg.append('      <line x1="29" y1="2" x2="29" y2="6"/>')
            svg.append('      <line x1="15" y1="26" x2="15" y2="30"/>')
            svg.append('      <line x1="22" y1="26" x2="22" y2="30"/>')
            svg.append('      <line x1="29" y1="26" x2="29" y2="30"/>')
            svg.append('    </g>')

        # Text inside header (font-size 30 bold)
        lines = h["lines"]
        if len(lines) == 1:
            svg.append(f'    <text x="{cx:.1f}" y="{by + 68}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{lines[0][0]}</text>')
        else:
            svg.append(f'    <text x="{cx:.1f}" y="{by + 58}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
            svg.append(f'      <tspan x="{cx:.1f}" dy="0">{lines[0][0]}</tspan>')
            svg.append(f'      <tspan x="{cx:.1f}" dy="26"> {lines[1][0]}</tspan>')
            svg.append('    </text>')
        svg.append('  </g>')

    # 9 Lifelines
    for h in headers:
        cx = h["cx"]
        start_y = 146 if h["row"] == 1 else 248
        svg.append(f'  <line x1="{cx:.1f}" y1="{start_y}" x2="{cx:.1f}" y2="1175" stroke="#b8c9c0" stroke-width="2.5" stroke-dasharray="8 6" />')

    # Steps definition (19 message steps + 1 note)
    steps = [
        # 1: U -> A
        {"num": 1, "src": "U", "dst": "A", "type": "msg_r",
         "text": "create Pod (admission, defaults, SA token, quota)",
         "card_x": 180.0, "by": 246},
        
        # 2: A -->> S
        {"num": 2, "src": "A", "dst": "S", "type": "dash_r",
         "text": "watch: Pod with no nodeName",
         "card_x": 342.5, "by": 288},
        
        # 3: S -> A
        {"num": 3, "src": "S", "dst": "A", "type": "msg_l",
         "text": "bind Pod → node (spec.nodeName)",
         "card_x": 50.0, "by": 330},
        
        # 4: A -->> K
        {"num": 4, "src": "A", "dst": "K", "type": "dash_r",
         "text": "watch: Pod bound to my node",
         "card_x": 342.5, "by": 372},
        
        # 5: K -> K
        {"num": 5, "src": "K", "dst": "K", "type": "self_r",
         "text": "admit pod (resources, node-fit, kernel params), create pod dirs",
         "card_x": 580.0, "by": 414},
        
        # 6: K -> D
        {"num": 6, "src": "K", "dst": "D", "type": "msg_r",
         "text": "Allocate(GPU devices) → env/mounts/CDI names",
         "card_x": 667.5, "by": 463},
        
        # 7: K -> V
        {"num": 7, "src": "K", "dst": "V", "type": "msg_r",
         "text": "NodeStageVolume / NodePublishVolume (PVCs)",
         "card_x": 667.5, "by": 512},
        
        # 8: K -> R
        {"num": 8, "src": "K", "dst": "R", "type": "msg_r",
         "text": "RunPodSandbox",
         "card_x": 667.5, "by": 561},
        
        # 9: R -> C
        {"num": 9, "src": "R", "dst": "C", "type": "msg_r",
         "text": "ADD (netns, IP, routes)",
         "card_x": 830.0, "by": 603},
        
        # 10: K -> R
        {"num": 10, "src": "K", "dst": "R", "type": "msg_r",
         "text": "PullImage (per container)",
         "card_x": 667.5, "by": 645},
        
        # 11: K -> R
        {"num": 11, "src": "K", "dst": "R", "type": "msg_r",
         "text": "CreateContainer / StartContainer (init containers first)",
         "card_x": 667.5, "by": 694},
        
        # 12: R -> X
        {"num": 12, "src": "R", "dst": "X", "type": "msg_r",
         "text": "create namespaces, cgroups, mounts, exec",
         "card_x": 830.0, "by": 736},
        
        # 13: K -> A
        {"num": 13, "src": "K", "dst": "A", "type": "msg_l",
         "text": "status updates (PodScheduled, Initialized, ContainersReady, Ready)",
         "card_x": 50.0, "by": 778},
        
        # Note over K,X (running phase - highlighted with orange)
        {"type": "note", "src": "K", "dst": "X",
         "text": "running: probes, log rotation, cgroup accounting, status heartbeats",
         "card_x": 520.0, "by": 828},
        
        # 14: U -> A
        {"num": 14, "src": "U", "dst": "A", "type": "msg_r",
         "text": "delete Pod",
         "card_x": 180.0, "by": 874},
        
        # 15: A -->> K
        {"num": 15, "src": "A", "dst": "K", "type": "dash_r",
         "text": "deletionTimestamp set (grace)",
         "card_x": 342.5, "by": 916},
        
        # 16: K -> X
        {"num": 16, "src": "K", "dst": "X", "type": "msg_r",
         "text": "preStop, SIGTERM, wait, SIGKILL",
         "card_x": 667.5, "by": 958},
        
        # 17: K -> R
        {"num": 17, "src": "K", "dst": "R", "type": "msg_r",
         "text": "StopContainer, StopPodSandbox → CNI DEL",
         "card_x": 667.5, "by": 1007},
        
        # 18: K -> V
        {"num": 18, "src": "K", "dst": "V", "type": "msg_r",
         "text": "unmount volumes",
         "card_x": 667.5, "by": 1056},
        
        # 19: K -> A
        {"num": 19, "src": "K", "dst": "A", "type": "msg_l",
         "text": "remove Pod object (grace 0)",
         "card_x": 180.0, "by": 1105}
    ]

    for s in steps:
        stype = s["type"]
        t = s["text"]
        est_w = len(t) * 0.6 * 24
        bw = est_w + 36.0 # ensures 18px padding on each side
        bh = 32.0
        bx = s["card_x"]
        by = s["by"]
        tx = bx + 18.0
        ty = by + 24.0
        
        if stype == "note":
            # Note over K,X: running phase (orange highlight for the single most important item)
            svg.append('  <!-- Note over K,X -->')
            svg.append('  <g id="note-running">')
            svg.append(f'    <rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh + 6}" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
            svg.append(f'    <text x="{tx:.1f}" y="{ty + 3}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">{t}</text>')
            svg.append('  </g>')
            continue
            
        num = s["num"]
        src = s["src"]
        dst = s["dst"]
        c_cx = centers[src]
        c_cy = by + 16.0 # vertically aligned with card
        ay = by + 16.0 # arrow Y
        
        svg.append(f'  <!-- Step {num} -->')
        svg.append(f'  <g id="step-{num}">')
        
        # Number circle (r=24)
        svg.append(f'    <circle cx="{c_cx:.1f}" cy="{c_cy:.1f}" r="24" fill="#207448" />')
        svg.append(f'    <text x="{c_cx:.1f}" y="{c_cy + 8:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{num}</text>')
        
        # Arrow
        if stype == "msg_r":
            x1 = c_cx + 24
            x2 = centers[dst]
            svg.append(f'    <line x1="{x1:.1f}" y1="{ay:.1f}" x2="{x2:.1f}" y2="{ay:.1f}" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green)" />')
        elif stype == "dash_r":
            x1 = c_cx + 24
            x2 = centers[dst]
            svg.append(f'    <line x1="{x1:.1f}" y1="{ay:.1f}" x2="{x2:.1f}" y2="{ay:.1f}" stroke="#207448" stroke-width="3" stroke-dasharray="8 6" marker-end="url(#arrow-green)" />')
        elif stype == "msg_l":
            x1 = c_cx - 24
            x2 = centers[dst]
            svg.append(f'    <line x1="{x1:.1f}" y1="{ay:.1f}" x2="{x2:.1f}" y2="{ay:.1f}" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-left)" />')
        elif stype == "self_r":
            x1 = c_cx + 24
            x_loop = c_cx + 60
            svg.append(f'    <path d="M {x1:.1f} {ay - 12:.1f} H {x_loop:.1f} V {ay + 12:.1f} H {c_cx + 10:.1f}" fill="none" stroke="#207448" stroke-width="3" marker-end="url(#arrow-green-left)" />')
            
        # Label card (drawn AFTER arrow so arrow does not cross text)
        svg.append(f'    <rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh}" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2" />')
        svg.append(f'    <text x="{tx:.1f}" y="{ty}" font-family="sans-serif" font-size="24" fill="#303a36">{t}</text>')
        svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

content = build_svg()
with open("test_timeline.svg", "w") as f:
    f.write(content)

print("Saved test_timeline.svg")
