import re
import xml.etree.ElementTree as ET

def generate_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Timeline overview</title>')
    svg.append('  <desc>Sequence diagram illustrating Kubernetes pod lifecycle from creation, admission, scheduling, volume staging, network setup, container runtime execution, running probes, to pod deletion and resource cleanup.</desc>')
    
    # Markers
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
    svg.append('  <text x="800" y="36" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Timeline overview</text>')
    
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
    
    headers = [
        # Row 1 (y = 46..124, h = 78)
        {"id": "U", "row": 1, "cx": 150.0, "lines": [("User /", 0), ("controller", 26)], "icon": "window"},
        {"id": "S", "row": 1, "cx": 475.0, "lines": [("Scheduler", 14)], "icon": "clock"},
        {"id": "R", "row": 1, "cx": 800.0, "lines": [("containerd", 0), ("(CRI)", 26)], "icon": "box"},
        {"id": "V", "row": 1, "cx": 1125.0, "lines": [("CSI node", 0), ("plugin", 26)], "icon": "cylinder"},
        {"id": "X", "row": 1, "cx": 1450.0, "lines": [("runc /", 0), ("kernel", 26)], "icon": "terminal"},
        # Row 2 (y = 130..208, h = 78)
        {"id": "A", "row": 2, "cx": 312.5, "lines": [("API server", 0), ("(+etcd)", 26)], "icon": "lock"},
        {"id": "K", "row": 2, "cx": 637.5, "lines": [("Kubelet", 14)], "icon": "gear"},
        {"id": "C", "row": 2, "cx": 962.5, "lines": [("CNI", 0), ("plugin", 26)], "icon": "network"},
        {"id": "D", "row": 2, "cx": 1287.5, "lines": [("Device", 0), ("plugin", 26)], "icon": "chip"}
    ]
    
    # Render Participant Header Boxes
    for h in headers:
        cx = h["cx"]
        by = 46 if h["row"] == 1 else 130
        bw = 216.0
        bh = 78.0
        bx = cx - bw / 2.0
        
        svg.append(f'  <g id="participant-{h["id"]} status">')
        svg.append(f'    <rect x="{bx:.1f}" y="{by}" width="{bw:.1f}" height="{bh}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
        
        # Simple outline icons (about 56px, green stroke 4, fill none)
        icx = cx - 18
        icy = by + 6
        icon_type = h["icon"]
        if icon_type == "window":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="2" y="2" width="32" height="20" rx="3"/>')
            svg.append('      <line x1="2" y1="8" x2="34" y2="8"/>')
            svg.append('      <circle cx="6" cy="5" r="1.2" fill="#207448"/>')
            svg.append('      <circle cx="11" cy="5" r="1.2" fill="#207448"/>')
            svg.append('    </g>')
        elif icon_type == "clock":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="18" cy="12" r="10"/>')
            svg.append('      <polyline points="18,6 18,12 23,12"/>')
            svg.append('    </g>')
        elif icon_type == "box":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="3" y="2" width="30" height="20" rx="3"/>')
            svg.append('      <line x1="3" y1="8" x2="33" y2="8"/>')
            svg.append('      <line x1="13" y1="8" x2="13" y2="22"/>')
            svg.append('    </g>')
        elif icon_type == "cylinder":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <ellipse cx="18" cy="6" rx="13" ry="4"/>')
            svg.append('      <path d="M 5 6 v 11 c 0 2.5 6 4 13 4 s 13 -1.5 13 -4 v -11"/>')
            svg.append('    </g>')
        elif icon_type == "terminal":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="2" y="2" width="32" height="20" rx="3"/>')
            svg.append('      <polyline points="8,7 13,12 8,17"/>')
            svg.append('      <line x1="16" y1="17" x2="26" y2="17"/>')
            svg.append('    </g>')
        elif icon_type == "lock":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="7" y="9" width="22" height="14" rx="2.5"/>')
            svg.append('      <path d="M 11 9 v -4 c 0 -3.5 3 -5 7 -5 s 7 1.5 7 5 v 4"/>')
            svg.append('    </g>')
        elif icon_type == "gear":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="18" cy="12" r="6"/>')
            svg.append('      <path d="M 18 1 v 3 M 18 20 v 3 M 7 12 h 3 M 26 12 h 3"/>')
            svg.append('    </g>')
        elif icon_type == "network":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <circle cx="18" cy="5" r="3"/>')
            svg.append('      <circle cx="8" cy="19" r="3"/>')
            svg.append('      <circle cx="28" cy="19" r="3"/>')
            svg.append('      <line x1="15" y1="8" x2="10" y2="16"/>')
            svg.append('      <line x1="21" y1="8" x2="26" y2="16"/>')
            svg.append('    </g>')
        elif icon_type == "chip":
            svg.append(f'    <g transform="translate({icx}, {icy})" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
            svg.append('      <rect x="8" y="4" width="20" height="15" rx="2"/>')
            svg.append('      <line x1="12" y1="1" x2="12" y2="4"/>')
            svg.append('      <line x1="18" y1="1" x2="18" y2="4"/>')
            svg.append('      <line x1="24" y1="1" x2="24" y2="4"/>')
            svg.append('      <line x1="12" y1="19" x2="12" y2="22"/>')
            svg.append('      <line x1="18" y1="19" x2="18" y2="22"/>')
            svg.append('      <line x1="24" y1="19" x2="24" y2="22"/>')
            svg.append('    </g>')
            
        # Text inside header (font-size 30 bold)
        lines = h["lines"]
        if len(lines) == 1:
            svg.append(f'    <text x="{cx:.1f}" y="{by + 60}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{lines[0][0]}</text>')
        else:
            svg.append(f'    <text x="{cx:.1f}" y="{by + 48}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
            svg.append(f'      <tspan x="{cx:.1f}" dy="0">{lines[0][0]}</tspan>')
            svg.append(f'      <tspan x="{cx:.1f}" dy="25"> {lines[1][0]}</tspan>')
            svg.append('    </text>')
        svg.append('  </g>')
        
    # Lifelines
    for h in headers:
        cx = h["cx"]
        start_y = 124 if h["row"] == 1 else 208
        svg.append(f'  <line x1="{cx:.1f}" y1="{start_y}" x2="{cx:.1f}" y2="1185" stroke="#b8c9c0" stroke-width="2.5" stroke-dasharray="8 6" />')

    # Step items definition with optimized heights and placement to guarantee 0 collisions
    items = [
        # 1: U -> A
        {'id': 'step-1', 'num': 1, 'src': 'U', 'dst': 'A', 'type': 'msg_r',
         'text': 'create Pod (admission, defaults, SA token, quota)', 'h': 42, 'bx': 180.0},
        # 2: A -->> S
        {'id': 'step-2', 'num': 2, 'src': 'A', 'dst': 'S', 'type': 'dash_r',
         'text': 'watch: Pod with no nodeName', 'h': 42, 'bx': 342.5},
        # 3: S -> A (place box to right of S to avoid overlapping A circle)
        {'id': 'step-3', 'num': 3, 'src': 'S', 'dst': 'A', 'type': 'msg_l_2',
         'lines': ['bind Pod → node', '(spec.nodeName)'], 'h': 50, 'bx': 505.0},
        # 4: A -->> K (place box to right of S circle to avoid overlapping S circle)
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
        # 10: K -> R (place box to right of R circle to avoid overlapping R circle)
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
        {'id': 'note-running', 'num': None, 'src': 'K', 'dst': 'X', 'type': 'note',
         'lines': ['running: probes, log rotation,', 'cgroup accounting, status heartbeats'], 'h': 76, 'bx': 590.0},
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
        itype = it['type']
        h = it['h']
        ay = cur_y + h - 6.0 # Arrow line Y near bottom of band
        
        if itype == 'note':
            # Note over K,X (orange highlight for the single most important item)
            # Starts strictly below Circle 13 bottom (which was at cur_y + 24 in step 13 = cur_y, so by = cur_y + 24 is safe)
            svg.append('  <!-- Note over K,X -->')
            svg.append('  <g id="note-running">')
            bx = it['bx']
            by = cur_y + 22.0 # 22px into this band
            bw = 890.0
            bh = 48.0
            svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="8" fill="#e8f1ea" stroke="#db8129" stroke-width="2.5" />')
            svg.append(f'    <text x="{bx + bw/2.0:.1f}" y="{by + 20.0:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">')
            svg.append(f'      <tspan x="{bx + bw/2.0:.1f}" dy="0">{it["lines"][0]}</tspan>')
            svg.append(f'      <tspan x="{bx + bw/2.0:.1f}" dy="22"> {it["lines"][1]}</tspan>')
            svg.append('    </text>')
            svg.append('  </g>')
            cur_y += h
            continue

        num = it['num']
        src = it['src']
        dst = it['dst']
        cx_src = centers[src]
        cx_dst = centers[dst]
        
        svg.append(f'  <!-- Step {num} -->')
        svg.append(f'  <g id="step-{num}">')
        
        # Number circle (r=24) centered at cx_src, ay
        svg.append(f'    <circle cx="{cx_src:.1f}" cy="{ay:.1f}" r="24" fill="#207448" />')
        svg.append(f'    <text x="{cx_src:.1f}" y="{ay + 8.0:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">{num}</text>')
        
        # Arrow and Card
        if itype in ('msg_r', 'dash_r'):
            x1 = cx_src + 24.0
            x2 = cx_dst
            dash = ' stroke-dasharray="8 6"' if itype == 'dash_r' else ''
            svg.append(f'    <line x1="{x1:.1f}" y1="{ay:.1f}" x2="{x2:.1f}" y2="{ay:.1f}" stroke="#207448" stroke-width="2.5"{dash} marker-end="url(#arrow-green)" />')
            
            t = it['text']
            est_w = len(t) * 0.6 * 24.0
            bw = est_w + 36.0 # >= 18px padding each side
            bh = 28.0
            bx = it.get('bx', cx_src + 30.0)
            by = ay - 32.0 # 4px clearance above arrow line
            svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + 21.0:.1f}" font-family="sans-serif" font-size="24" fill="#303a36">{t}</text>')
            
        elif itype == 'msg_l':
            x1 = cx_src - 24.0
            x2 = cx_dst
            svg.append(f'    <line x1="{x1:.1f}" y1="{ay:.1f}" x2="{x2:.1f}" y2="{ay:.1f}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green-left)" />')
            
            t = it['text']
            est_w = len(t) * 0.6 * 24.0
            bw = est_w + 36.0
            bh = 28.0
            bx = it.get('bx', cx_src - 24.0 - bw - 6.0)
            by = ay - 32.0
            svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + 21.0:.1f}" font-family="sans-serif" font-size="24" fill="#303a36">{t}</text>')
            
        elif itype == 'msg_l_2':
            x1 = cx_src - 24.0
            x2 = cx_dst
            svg.append(f'    <line x1="{x1:.1f}" y1="{ay:.1f}" x2="{x2:.1f}" y2="{ay:.1f}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green-left)" />')
            
            lines = it['lines']
            w1 = len(lines[0]) * 0.6 * 24.0
            w2 = len(lines[1]) * 0.6 * 24.0
            max_w = max(w1, w2)
            bw = max_w + 36.0
            bh = 46.0
            bx = it.get('bx', cx_src - 24.0 - bw - 6.0)
            by = ay - 50.0
            svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + 19.0:.1f}" font-family="sans-serif" font-size="24" fill="#303a36">')
            svg.append(f'      <tspan x="{bx + 18.0:.1f}" dy="0">{lines[0]}</tspan>')
            svg.append(f'      <tspan x="{bx + 18.0:.1f}" dy="22"> {lines[1]}</tspan>')
            svg.append('    </text>')
            
        elif itype == 'self_r_2':
            # Self loop at K
            x1 = cx_src + 24.0
            x_loop = cx_src + 60.0
            svg.append(f'    <path d="M {x1:.1f} {ay - 14.0:.1f} H {x_loop:.1f} V {ay + 10.0:.1f} H {cx_src + 10.0:.1f}" fill="none" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green-left)" />')
            
            lines = it['lines']
            w1 = len(lines[0]) * 0.6 * 24.0
            w2 = len(lines[1]) * 0.6 * 24.0
            max_w = max(w1, w2)
            bw = max_w + 36.0
            bh = 46.0
            bx = it.get('bx', x_loop + 10.0)
            by = ay - 36.0
            svg.append(f'    <rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="6" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
            svg.append(f'    <text x="{bx + 18.0:.1f}" y="{by + 19.0:.1f}" font-family="sans-serif" font-size="24" fill="#303a36">')
            svg.append(f'      <tspan x="{bx + 18.0:.1f}" dy="0">{lines[0]}</tspan>')
            svg.append(f'      <tspan x="{bx + 18.0:.1f}" dy="22"> {lines[1]}</tspan>')
            svg.append('    </text>')

        svg.append('  </g>')
        cur_y += h
        
    svg.append('</svg>')
    return '\n'.join(svg)

content = generate_svg()
with open("perfect_zero_collision.svg", "w") as f:
    f.write(content)
print(f"Generated perfect_zero_collision.svg, total length = {len(content)}")
