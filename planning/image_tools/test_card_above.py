import re
import xml.etree.ElementTree as ET

def generate():
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
    
    # Participant Header Cards (height 76, width 220)
    # Row 1: y = 60 to 136
    # Row 2: y = 144 to 220
    headers = [
        # Row 1
        {"id": "U", "row": 1, "cx": 150.0, "lines": [("User /", 0), ("controller", 26)], "icon": "window"},
        {"id": "S", "row": 1, "cx": 475.0, "lines": [("Scheduler", 14)], "icon": "clock"},
        {"id": "R", "row": 1, "cx": 800.0, "lines": [("containerd", 0), ("(CRI)", 26)], "icon": "box"},
        {"id": "V", "row": 1, "cx": 1125.0, "lines": [("CSI node", 0), ("plugin", 26)], "icon": "cylinder"},
        {"id": "X", "row": 1, "cx": 1450.0, "lines": [("runc /", 0), ("kernel", 26)], "icon": "terminal"},
        # Row 2
        {"id": "A", "row": 2, "cx": 312.5, "lines": [("API server", 0), ("(+etcd)", 26)], "icon": "lock"},
        {"id": "K", "row": 2, "cx": 637.5, "lines": [("Kubelet", 14)], "icon": "gear"},
        {"id": "C", "row": 2, "cx": 962.5, "lines": [("CNI", 0), ("plugin", 26)], "icon": "network"},
        {"id": "D", "row": 2, "cx": 1287.5, "lines": [("Device", 0), ("plugin", 26)], "icon": "chip"}
    ]
    
    for h in headers:
        cx = h["cx"]
        by = 60 if h["row"] == 1 else 144
        bx = cx - 110.0
        bw = 220.0
        bh = 76.0
        
        svg.append(f'  <g id="participant-{h["id"]} status">')
        svg.append(f'    <rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
        
        # Simple outline icons (about 56px, green stroke 4, fill none)
        icx = cx - 20
        icy = by + 6
        if h["icon"] == "window":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="2" y="2" width="36" height="22" rx="3"/>')
            svg.append('      <line x1="2" y1="8" x2="38" y2="8"/>')
            svg.append('    </g>')
        elif h["icon"] == "clock":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="20" cy="13" r="11"/>')
            svg.append('      <polyline points="20,7 20,13 25,13"/>')
            svg.append('    </g>')
        elif h["icon"] == "box":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="4" y="2" width="32" height="22" rx="3"/>')
            svg.append('      <line x1="4" y1="9" x2="36" y2="9"/>')
            svg.append('      <line x1="14" y1="9" x2="14" y2="24"/>')
            svg.append('    </g>')
        elif h["icon"] == "cylinder":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <ellipse cx="20" cy="6" rx="14" ry="4.5"/>')
            svg.append('      <path d="M 6 6 v 12 c 0 2.5 6 4.5 14 4.5 s 14 -2 14 -4.5 v -12"/>')
            svg.append('    </g>')
        elif h["icon"] == "terminal":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="2" y="2" width="36" height="22" rx="3"/>')
            svg.append('      <polyline points="9,8 14,13 9,18"/>')
            svg.append('      <line x1="17" y1="18" x2="27" y2="18"/>')
            svg.append('    </g>')
        elif h["icon"] == "lock":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="7" y="10" width="26" height="15" rx="3"/>')
            svg.append('      <path d="M 12 10 v -4 c 0 -3.5 3.5 -5 8 -5 s 8 1.5 8 5 v 4"/>')
            svg.append('    </g>')
        elif h["icon"] == "gear":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="20" cy="13" r="7"/>')
            svg.append('      <path d="M 20 2 v 4 M 20 20 v 4 M 9 13 h 4 M 27 13 h 4"/>')
            svg.append('    </g>')
        elif h["icon"] == "network":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="20" cy="6" r="3.5"/>')
            svg.append('      <circle cx="9" cy="19" r="3.5"/>')
            svg.append('      <circle cx="31" cy="19" r="3.5"/>')
            svg.append('      <line x1="17" y1="9" x2="12" y2="16"/>')
            svg.append('      <line x1="23" y1="9" x2="28" y2="16"/>')
            svg.append('    </g>')
        elif h["icon"] == "chip":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="9" y="5" width="22" height="17" rx="2.5"/>')
            svg.append('      <line x1="14" y1="1" x2="14" y2="5"/>')
            svg.append('      <line x1="20" y1="1" x2="20" y2="5"/>')
            svg.append('      <line x1="26" y1="1" x2="26" y2="5"/>')
            svg.append('      <line x1="14" y1="22" x2="14" y2="26"/>')
            svg.append('      <line x1="20" y1="22" x2="20" y2="26"/>')
            svg.append('      <line x1="26" y1="22" x2="26" y2="26"/>')
            svg.append('    </g>')

        # Text inside header (font-size 30 bold)
        lines = h["lines"]
        if len(lines) == 1:
            svg.append(f'    <text x="{cx:.1f}" y="{by + 60}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{lines[0][0]}</text>')
        else:
            svg.append(f'    <text x="{cx:.1f}" y="{by + 48}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
            svg.append(f'      <tspan x="{cx:.1f}" dy="0">{lines[0][0]}</tspan>')
            svg.append(f'      <tspan x="{cx:.1f}" dy="24"> {lines[1][0]}</tspan>')
            svg.append('    </text>')
        svg.append('  </g>')

    # 9 Lifelines
    for h in headers:
        cx = h["cx"]
        start_y = 136 if h["row"] == 1 else 220
        svg.append(f'  <line x1="{cx:.1f}" y1="{start_y}" x2="{cx:.1f}" y2="1175" stroke="#b8c9c0" stroke-width="2.5" stroke-dasharray="8 6" />')

    # Steps definition (19 message steps + 1 note)
    # Each step has:
    # ay = arrow Y level
    # card sitting ABOVE arrow line: by = ay - 32, bh = 28 (bottom of card is ay - 4)
    # circle centered at (c_cx, cy = ay): r = 24
    steps_data = [
        # 1: U -> A
        {"num": 1, "src": "U", "dst": "A", "type": "msg_r",
         "text": "create Pod (admission, defaults, SA token, quota)", "card_x": 180.0},
        
        # 2: A -->> S
        {"num": 2, "src": "A", "dst": "S", "type": "dash_r",
         "text": "watch: Pod with no nodeName", "card_x": 342.5},
        
        # 3: S -> A (leftward)
        {"num": 3, "src": "S", "dst": "A", "type": "msg_l",
         "text": "bind Pod → node (spec.nodeName)", "card_x": 178.0, "bw": 268.0,
         "lines": [("bind Pod → node", 18), (" (spec.nodeName)", 38)], "bh": 44},
        
        # 4: A -->> K
        {"num": 4, "src": "A", "dst": "K", "type": "dash_r",
         "text": "watch: Pod bound to my node", "card_x": 342.5},
        
        # 5: K -> K (self-loop)
        {"num": 5, "src": "K", "dst": "K", "type": "self_r",
         "text": "admit pod (resources, node-fit, kernel params), create pod dirs",
         "card_x": 720.0, "bw": 710.0,
         "lines": [("admit pod (resources, node-fit, kernel params),", 18), (" create pod dirs", 38)], "bh": 44},
        
        # 6: K -> D
        {"num": 6, "src": "K", "dst": "D", "type": "msg_r",
         "text": "Allocate(GPU devices) → env/mounts/CDI names", "card_x": 667.5},
        
        # 7: K -> V
        {"num": 7, "src": "K", "dst": "V", "type": "msg_r",
         "text": "NodeStageVolume / NodePublishVolume (PVCs)", "card_x": 667.5},
        
        # 8: K -> R
        {"num": 8, "src": "K", "dst": "R", "type": "msg_r",
         "text": "RunPodSandbox", "card_x": 667.5},
        
        # 9: R -> C
        {"num": 9, "src": "R", "dst": "C", "type": "msg_r",
         "text": "ADD (netns, IP, routes)", "card_x": 830.0},
        
        # 10: K -> R
        {"num": 10, "src": "K", "dst": "R", "type": "msg_r",
         "text": "PullImage (per container)", "card_x": 667.5},
        
        # 11: K -> R
        {"num": 11, "src": "K", "dst": "R", "type": "msg_r",
         "text": "CreateContainer / StartContainer (init containers first)", "card_x": 667.5},
        
        # 12: R -> X
        {"num": 12, "src": "R", "dst": "X", "type": "msg_r",
         "text": "create namespaces, cgroups, mounts, exec", "card_x": 830.0},
        
        # 13: K -> A (leftward, 3 lines)
        {"num": 13, "src": "K", "dst": "A", "type": "msg_l",
         "text": "status updates (PodScheduled, Initialized, ContainersReady, Ready)",
         "card_x": 178.0, "bw": 430.0,
         "lines": [("status updates", 18), (" (PodScheduled, Initialized,", 38), (" ContainersReady, Ready)", 58)], "bh": 64},
        
        # Note over K,X (running phase - highlighted with orange)
        {"type": "note", "src": "K", "dst": "X",
         "text": "running: probes, log rotation, cgroup accounting, status heartbeats",
         "card_x": 520.0, "bh": 36},
        
        # 14: U -> A
        {"num": 14, "src": "U", "dst": "A", "type": "msg_r",
         "text": "delete Pod", "card_x": 180.0},
        
        # 15: A -->> K
        {"num": 15, "src": "A", "dst": "K", "type": "dash_r",
         "text": "deletionTimestamp set (grace)", "card_x": 342.5},
        
        # 16: K -> X
        {"num": 16, "src": "K", "dst": "X", "type": "msg_r",
         "text": "preStop, SIGTERM, wait, SIGKILL", "card_x": 667.5},
        
        # 17: K -> R
        {"num": 17, "src": "K", "dst": "R", "type": "msg_r",
         "text": "StopContainer, StopPodSandbox → CNI DEL", "card_x": 667.5},
        
        # 18: K -> V
        {"num": 18, "src": "K", "dst": "V", "type": "msg_r",
         "text": "unmount volumes", "card_x": 667.5},
        
        # 19: K -> A (leftward)
        {"num": 19, "src": "K", "dst": "A", "type": "msg_l",
         "text": "remove Pod object (grace 0)", "card_x": 180.0}
    ]

    # Compute vertical coordinates
    # Step 1 arrow at ay = 264.
    cur_ay = 264.0
    prev_src = None
    for s in steps_data:
        src = s["src"]
        num = s.get("num")
        bh = s.get("bh", 28.0)
        
        if prev_src == "K" and src == "K" and num != "note":
            cur_ay += 49.0
        else:
            if prev_src is not None:
                cur_ay += max(42.0, bh + 12.0)
                
        s["ay"] = cur_ay
        s["cy"] = cur_ay
        # Card sits 4px above arrow line:
        s["by"] = cur_ay - bh - 4.0
        prev_src = src

    for s in steps_data:
        stype = s["type"]
        t = s["text"]
        bx = s["card_x"]
        by = s["by"]
        bh = s.get("bh", 28.0)
        ay = s["ay"]
        
        if "bw" in s:
            bw = s["bw"]
        else:
            est_w = len(t) * 0.6 * 24
            bw = est_w + 36.0
            
        if stype == "note":
            # Note over K,X: running phase (orange highlight for the single most important item)
            svg.append('  <!-- Note over K,X -->')
            svg.append('  <g id="note-running">')
            svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + 26.0:.1f}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">{t}</text>')
            svg.append('  </g>')
            continue
            
        num = s["num"]
        src = s["src"]
        dst = s["dst"]
        c_cx = centers[src]
        c_cy = s["cy"]
        
        svg.append(f'  <!-- Step {num} -->')
        svg.append(f'  <g id="step-{num}">')
        
        # Number circle (r=24)
        svg.append(f'    <circle cx="{c_cx:.1f}" cy="{c_cy:.1f}" r="24" fill="#207448" />')
        svg.append(f'    <text x="{c_cx:.1f}" y="{c_cy + 8:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{num}</text>')
        
        # Arrow line (runs horizontally at ay, 4px below card)
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
            
        # Label card (sits completely ABOVE the arrow line)
        svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="#ffffff" stroke="#207448" stroke-width="2" />')
        
        # Text inside card
        if "lines" in s:
            lines = s["lines"]
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + lines[0][1]:.1f}" font-family="sans-serif" font-size="24" fill="#303a36">')
            for idx, (ltxt, dy_val) in enumerate(lines):
                if idx == 0:
                    svg.append(f'      <tspan x="{bx + 18.0:.1f}" dy="0">{ltxt}</tspan>')
                else:
                    svg.append(f'      <tspan x="{bx + 18.0:.1f}" dy="{dy_val - lines[idx-1][1]}">{ltxt}</tspan>')
            svg.append('    </text>')
        else:
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + 21.0:.1f}" font-family="sans-serif" font-size="24" fill="#303a36">{t}</text>')
            
        svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

content = generate()
with open("test_timeline.svg", "w") as f:
    f.write(content)

print("Saved test_timeline.svg with card ABOVE arrow line!")
