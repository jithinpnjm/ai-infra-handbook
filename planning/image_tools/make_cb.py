import math
import subprocess

def make_svg():
    # Dimensions
    W = 1600
    H = 960

    # Colors
    bg = "#f5f8f5"
    text_color = "#303a36"
    green = "#207448"
    panel_green = "#e8f1ea"
    orange = "#db8129"
    orange_panel = "#fff7f0"

    # Circle nodes
    R = 160
    # Closed: top-left
    cx_c, cy_c = 420, 360
    # Open: top-right
    cx_o, cy_o = 1180, 360
    # Half-open: bottom-center
    cx_h, cy_h = 800, 750

    # Let's compute exact arrow attachment points on circles
    # Function for point on circle at angle (degrees)
    def pt(cx, cy, r, deg):
        rad = math.radians(deg)
        return round(cx + r * math.cos(rad), 2), round(cy + r * math.sin(rad), 2)

    # 1. Closed -> Open (Arrow 1: too many failures)
    # Starts at top-right of Closed (e.g. -25 deg)
    # Ends at top-left of Open (e.g. -155 deg)
    p1_s = pt(cx_c, cy_c, R, -25)
    p1_e = pt(cx_o, cy_o, R, -155)
    # Control point: midpoint in x is 800, y = 200
    p1_ctrl = (800, 200)

    # 2. Open -> Half-open (Arrow 2: after a cool-down)
    # Outer right branch:
    # Starts at right-bottom of Open (e.g. 35 deg)
    p2_s = pt(cx_o, cy_o, R, 35)
    # Ends at right of Half-open (e.g. -10 deg)
    p2_e = pt(cx_h, cy_h, R, -10)
    # Control point for gentle outer curve: (1260, 620)
    p2_ctrl = (1260, 620)

    # 3. Half-open -> Closed (Arrow 3: trial succeeds)
    # Outer left branch:
    # Starts at left of Half-open (e.g. -170 deg)
    p3_s = pt(cx_h, cy_h, R, -170)
    # Ends at left-bottom of Closed (e.g. 145 deg)
    p3_e = pt(cx_c, cy_c, R, 145)
    # Control point for gentle outer curve: (340, 620)
    p3_ctrl = (340, 620)

    # 4. Half-open -> Open (Arrow 4: trial fails)
    # Inner branch:
    # Starts at top-right of Half-open (e.g. -65 deg)
    p4_s = pt(cx_h, cy_h, R, -65)
    # Ends at bottom-left of Open (e.g. 135 deg)
    p4_e = pt(cx_o, cy_o, R, 135)
    # Control point for gentle curve: (960, 520)
    p4_ctrl = (960, 520)

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>A circuit breaker has three states</title>')
    svg.append('  <desc>State transition diagram showing Closed, Open, and Half-open states of a circuit breaker.</desc>')
    
    # Markers
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append(f'      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{green}" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append(f'      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{orange}" />')
    svg.append('    </marker>')
    svg.append('  </defs>')

    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="{bg}" />')

    # Title
    svg.append(f'  <text x="800" y="75" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="{text_color}">A circuit breaker has three states</text>')

    # ARROWS (drawn before nodes so nodes are cleanly above, or nodes have exact end points)
    # Arrow 1: Closed -> Open ("too many failures")
    # Let's check marker color: green
    svg.append(f'  <path d="M {p1_s[0]} {p1_s[1]} Q {p1_ctrl[0]} {p1_ctrl[1]} {p1_e[0]} {p1_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <text x="800" y="205" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">too many failures</text>')

    # Arrow 2: Open -> Half-open ("after a cool-down")
    svg.append(f'  <path d="M {p2_s[0]} {p2_s[1]} Q {p2_ctrl[0]} {p2_ctrl[1]} {p2_e[0]} {p2_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <text x="1275" y="605" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">after a cool-down</text>')

    # Arrow 3: Half-open -> Closed ("trial succeeds")
    svg.append(f'  <path d="M {p3_s[0]} {p3_s[1]} Q {p3_ctrl[0]} {p3_ctrl[1]} {p3_e[0]} {p3_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <text x="325" y="605" text-anchor="end" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">trial succeeds</text>')

    # Arrow 4: Half-open -> Open ("trial fails")
    svg.append(f'  <path d="M {p4_s[0]} {p4_s[1]} Q {p4_ctrl[0]} {p4_ctrl[1]} {p4_e[0]} {p4_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />')
    svg.append(f'  <text x="965" y="505" text-anchor="end" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">trial fails</text>')

    # NODES
    # Node 1: Closed (calls pass, green)
    svg.append(f'  <!-- Node 1: Closed -->')
    svg.append(f'  <circle cx="{cx_c}" cy="{cy_c}" r="{R}" fill="{panel_green}" stroke="{green}" stroke-width="4" />')
    # Icon: Shield with checkmark (about 56px, stroke 4)
    # Center of icon: (cx_c, cy_c - 45)
    ix, iy = cx_c, cy_c - 45
    svg.append(f'  <g transform="translate({ix}, {iy})" stroke="{green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M -22 -18 L 0 -26 L 22 -18 L 22 4 C 22 18 0 28 0 28 C 0 28 -22 18 -22 4 Z" />')
    svg.append('    <polyline points="-10 2 -2 10 12 -4" />')
    svg.append('  </g>')
    # Title: Closed (32px bold)
    svg.append(f'  <text x="{cx_c}" y="{cy_c + 24}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="{green}">Closed</text>')
    # Subtitle: calls pass (24px)
    svg.append(f'  <text x="{cx_c}" y="{cy_c + 64}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="{text_color}">calls pass</text>')

    # Node 2: Open (calls fail fast, orange)
    svg.append(f'  <!-- Node 2: Open -->')
    svg.append(f'  <circle cx="{cx_o}" cy="{cy_o}" r="{R}" fill="{orange_panel}" stroke="{orange}" stroke-width="4" />')
    # Icon: Alert triangle / open switch (about 56px, stroke 4)
    ix, iy = cx_o, cy_o - 45
    svg.append(f'  <g transform="translate({ix}, {iy})" stroke="{orange}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <polygon points="0 -24 24 18 -24 18" />')
    svg.append('    <line x1="0" y1="-7" x2="0" y2="4" />')
    svg.append(f'    <circle cx="0" cy="11" r="2" fill="{orange}" stroke="none" />')
    svg.append('  </g>')
    # Title: Open (32px bold)
    svg.append(f'  <text x="{cx_o}" y="{cy_o + 24}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="{orange}">Open</text>')
    # Subtitle: calls fail fast (24px)
    svg.append(f'  <text x="{cx_o}" y="{cy_o + 64}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="{text_color}">calls fail fast</text>')

    # Node 3: Half-open (one trial call)
    svg.append(f'  <!-- Node 3: Half-open -->')
    svg.append(f'  <circle cx="{cx_h}" cy="{cy_h}" r="{R}" fill="{panel_green}" stroke="{green}" stroke-width="4" />')
    # Icon: Clock for timer (about 56px, stroke 4)
    ix, iy = cx_h, cy_h - 45
    svg.append(f'  <g transform="translate({ix}, {iy})" stroke="{green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="0" cy="0" r="23" />')
    svg.append('    <polyline points="0 -13 0 0 9 0" />')
    svg.append('    <line x1="0" y1="-23" x2="0" y2="-19" />')
    svg.append('    <line x1="0" y1="19" x2="0" y2="23" />')
    svg.append('    <line x1="-23" y1="0" x2="-19" y2="0" />')
    svg.append('    <line x1="19" y1="0" x2="23" y2="0" />')
    svg.append('  </g>')
    # Title: Half-open (32px bold)
    svg.append(f'  <text x="{cx_h}" y="{cy_h + 24}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="{green}">Half-open</text>')
    # Subtitle: one trial call (24px)
    svg.append(f'  <text x="{cx_h}" y="{cy_h + 64}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="{text_color}">one trial call</text>')

    svg.append('</svg>')
    return '\n'.join(svg)

with open('circuit_breaker.svg', 'w') as f:
    f.write(make_svg())

print('Wrote circuit_breaker.svg')
