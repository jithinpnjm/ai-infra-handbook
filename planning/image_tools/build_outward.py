import xml.etree.ElementTree as ET
import re

def build_svg():
    # Palette
    BG = "#f5f8f5"
    TEXT = "#303a36"
    MAIN_GREEN = "#207448"
    LIGHT_GREEN = "#e8f1ea"
    ORANGE = "#db8129"
    WHITE = "#ffffff"

    # Dimensions
    W = 1600
    H = 1200

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Debug from the object outward, cheapest question first</title>')
    svg.append('  <desc>Visual ladder of nine debugging steps in Kubernetes, from pod status and events through node, kubelet, container runtime, and network.</desc>')
    
    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{BG}" />')

    # Title
    svg.append(f'  <text x="800" y="78" font-family="sans-serif" font-size="48" font-weight="bold" fill="{TEXT}" text-anchor="middle">Debug from the object outward, cheapest question first</text>')

    # Steps definition
    # Each: (num, title, chips, is_orange, y, h)
    steps_data = [
        (1, "STATUS column of the pod", ["kubectl get pod"], False, 130, 64),
        (2, "Events table at the bottom", ["kubectl describe pod"], True, 235, 64),
        (3, "Namespace events, sorted by time", ["kubectl get events"], False, 340, 64),
        (4, "Logs of the running container and the earlier one", ["kubectl logs", "kubectl logs --previous"], False, 445, 90),
        (5, "Exec into the container, only if the pod looks fine", ["kubectl exec"], False, 576, 64),
        (6, "Node: Conditions, Taints and Lease", ["kubectl describe node"], False, 681, 64),
        (7, "Kubelet journal", ["journalctl -xeu kubelet"], False, 786, 64),
        (8, "Container runtime", ["crictl"], False, 891, 64),
        (9, "Network plugin, then DNS", [], False, 996, 64),
    ]

    # Brackets on the left
    # Bracket 1 spans steps 1 to 4: y1 = 130, y2 = 535
    def make_bracket(x_tick, x_line, x_cusp, y1, y2):
        ym = (y1 + y2) / 2
        r = 12
        return f"M {x_tick},{y1} Q {x_line},{y1} {x_line},{y1+r} L {x_line},{ym-r} Q {x_line},{ym} {x_cusp},{ym} Q {x_line},{ym} {x_line},{ym+r} L {x_line},{y2-r} Q {x_line},{y2} {x_tick},{y2}"

    b1_path = make_bracket(125, 110, 95, 130, 535)
    svg.append(f'  <path d="{b1_path}" fill="none" stroke="{MAIN_GREEN}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'  <text transform="rotate(-90 68 333)" x="68" y="333" font-family="sans-serif" font-size="24" font-weight="bold" fill="{MAIN_GREEN}" text-anchor="middle">Cheap: the cluster API</text>')

    # Bracket 2 spans steps 6 to 9: y1 = 681, y2 = 1060
    b2_path = make_bracket(125, 110, 95, 681, 1060)
    svg.append(f'  <path d="{b2_path}" fill="none" stroke="{MAIN_GREEN}" stroke-width="3" stroke-linecap="round" />')
    svg.append(f'  <text transform="rotate(-90 68 871)" x="68" y="871" font-family="sans-serif" font-size="24" font-weight="bold" fill="{MAIN_GREEN}" text-anchor="middle">Expensive: the node</text>')

    # Render each step
    box_x = 170
    box_w = 1390
    box_right = box_x + box_w # 1560

    # Icons SVGs (40x40 viewport, placed at transform translate)
    def get_icon(num, stroke_col):
        if num == 1:
            return f'<rect x="2" y="2" width="36" height="36" rx="6" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><circle cx="12" cy="14" r="3" fill="{stroke_col}" /><line x1="20" y1="14" x2="32" y2="14" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" /><circle cx="12" cy="24" r="3" fill="{stroke_col}" /><line x1="20" y1="24" x2="32" y2="24" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" />'
        elif num == 2:
            return f'<rect x="2" y="2" width="36" height="36" rx="6" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><line x1="2" y1="13" x2="38" y2="13" stroke="{stroke_col}" stroke-width="3" /><line x1="14" y1="13" x2="14" y2="38" stroke="{stroke_col}" stroke-width="3" /><line x1="19" y1="21" x2="32" y2="21" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="19" y1="29" x2="29" y2="29" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" />'
        elif num == 3:
            return f'<circle cx="20" cy="20" r="17" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><polyline points="20,9 20,20 28,24" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" />'
        elif num == 4:
            return f'<rect x="4" y="8" width="24" height="28" rx="3" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><path d="M 12 4 L 32 4 C 34 4 36 6 36 8 L 36 28" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" fill="none" /><line x1="9" y1="16" x2="23" y2="16" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="9" y1="22" x2="23" y2="22" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="9" y1="28" x2="19" y2="28" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" />'
        elif num == 5:
            return f'<rect x="2" y="4" width="36" height="32" rx="5" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><polyline points="8,16 15,20 8,24" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round" fill="none" /><line x1="18" y1="24" x2="28" y2="24" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" />'
        elif num == 6:
            return f'<rect x="2" y="6" width="36" height="12" rx="3" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><rect x="2" y="22" width="36" height="12" rx="3" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><circle cx="8" cy="12" r="2" fill="{stroke_col}" /><circle cx="8" cy="28" r="2" fill="{stroke_col}" /><line x1="16" y1="12" x2="32" y2="12" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="16" y1="28" x2="32" y2="28" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" />'
        elif num == 7:
            return f'<circle cx="20" cy="20" r="7" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><path d="M 20 4 L 20 9 M 20 31 L 20 36 M 4 20 L 9 20 M 31 20 L 36 20 M 8.7 8.7 L 12.2 12.2 M 27.8 27.8 L 31.3 31.3 M 8.7 31.3 L 12.2 27.8 M 27.8 12.2 L 31.3 8.7" stroke="{stroke_col}" stroke-width="3.5" stroke-linecap="round" />'
        elif num == 8:
            return f'<path d="M 20 3 L 36 12 L 36 28 L 20 37 L 4 28 L 4 12 Z" stroke="{stroke_col}" stroke-width="3.5" stroke-linejoin="round" fill="none" /><line x1="20" y1="20" x2="36" y2="12" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="20" y1="20" x2="4" y2="12" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="20" y1="20" x2="20" y2="37" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" />'
        elif num == 9:
            return f'<circle cx="8" cy="20" r="5" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><circle cx="32" cy="10" r="5" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><circle cx="32" cy="30" r="5" stroke="{stroke_col}" stroke-width="3.5" fill="none" /><line x1="13" y1="18" x2="27" y2="12" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="13" y1="22" x2="27" y2="28" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" /><line x1="32" y1="15" x2="32" y2="25" stroke="{stroke_col}" stroke-width="3" stroke-linecap="round" />'

    for num, title, chips, is_orange, y, h in steps_data:
        box_stroke = ORANGE if is_orange else MAIN_GREEN
        box_stroke_w = "3.5" if is_orange else "2"
        fill_col = WHITE

        svg.append(f'  <g id="step-{num}">')
        # Step box
        svg.append(f'    <rect x="{box_x}" y="{y}" width="{box_w}" height="{h}" rx="12" fill="{fill_col}" stroke="{box_stroke}" stroke-width="{box_stroke_w}" />')

        # Number circle (r=24, green, white number)
        cx = box_x + 36 # 206
        cy = y + (h // 2)
        circle_col = MAIN_GREEN
        svg.append(f'    <circle cx="{cx}" cy="{cy}" r="24" fill="{circle_col}" />')
        svg.append(f'    <text x="{cx}" y="{cy + 8}" font-family="sans-serif" font-size="24" font-weight="bold" fill="{WHITE}" text-anchor="middle">{num}</text>')

        # Icon
        icon_x = box_x + 76 # 246
        icon_y = cy - 20
        icon_stroke = MAIN_GREEN
        icon_markup = get_icon(num, icon_stroke)
        svg.append(f'    <g transform="translate({icon_x}, {icon_y})">')
        svg.append(f'      {icon_markup}')
        svg.append(f'    </g>')

        # Title text
        tx = box_x + 140 # 310
        if num == 4:
            # Wrap Step 4 into two lines
            svg.append(f'    <text x="{tx}" y="{y + 38}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{TEXT}">')
            svg.append(f'      <tspan x="{tx}" dy="0">Logs of the running container </tspan>')
            svg.append(f'      <tspan x="{tx}" dy="30">and the earlier one</tspan>')
            svg.append(f'    </text>')
        else:
            ty = y + 42
            svg.append(f'    <text x="{tx}" y="{ty}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{TEXT}">{title}</text>')

        # Command chips on the right
        if chips:
            curr_right = box_right - 20
            # iterate in reverse so rightmost chip is placed first
            for c in reversed(chips):
                cw = len(c) * 0.62 * 24
                chip_bw = int(cw + 36)
                chip_bx = curr_right - chip_bw
                chip_h = 44
                chip_y = cy - (chip_h // 2)
                chip_ty = chip_y + 30
                chip_tx = chip_bx + (chip_bw // 2)

                svg.append(f'    <rect x="{chip_bx}" y="{chip_y}" width="{chip_bw}" height="{chip_h}" rx="8" fill="{LIGHT_GREEN}" stroke="{MAIN_GREEN}" stroke-width="1.5" />')
                svg.append(f'    <text x="{chip_tx}" y="{chip_ty}" font-family="monospace" font-size="24" font-weight="bold" fill="{MAIN_GREEN}" text-anchor="middle">{c}</text>')

                curr_right = chip_bx - 16

        svg.append(f'  </g>')

    # Takeaway bar at bottom
    caption = "Each seam is a handoff between two teams, so ask who holds the object now."
    svg.append('  <g id="takeaway-bar">')
    svg.append(f'    <rect x="40" y="1100" width="1520" height="60" rx="10" fill="{MAIN_GREEN}" />')
    svg.append(f'    <text x="800" y="1139" font-family="sans-serif" font-size="26" font-weight="bold" fill="{WHITE}" text-anchor="middle">{caption}</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return "\n".join(svg)

with open("candidate_outward.svg", "w") as f:
    f.write(build_svg())

print("Built candidate_outward.svg successfully!")
