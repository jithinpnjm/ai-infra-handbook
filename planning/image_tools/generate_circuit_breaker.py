import math
import subprocess

W = 1600
H = 960

bg = "#f5f8f5"
text_color = "#303a36"
green = "#207448"
panel_green = "#e8f1ea"
orange = "#db8129"
orange_panel = "#fff7f0"

cx_c, cy_c = 420, 360
cx_o, cy_o = 1180, 360
cx_h, cy_h = 800, 750
R = 160

def circ_pt(cx, cy, r, deg):
    rad = math.radians(deg)
    return round(cx + r * math.cos(rad), 2), round(cy + r * math.sin(rad), 2)

# Arrow 1: Closed -> Open (too many failures)
p1_s = circ_pt(cx_c, cy_c, R, -25)
p1_e = circ_pt(cx_o, cy_o, R, -155)
p1_ctrl = (800, 185)

# Arrow 2: Open -> Half-open (after a cool-down)
p2_s = circ_pt(cx_o, cy_o, R, 45)
p2_e = circ_pt(cx_h, cy_h, R, -15)
p2_ctrl = (1163.8, 648.3)

# Arrow 3: Half-open -> Closed (trial succeeds)
p3_s = circ_pt(cx_h, cy_h, R, -135)
p3_e = circ_pt(cx_c, cy_c, R, 60)
p3_ctrl = (557.7, 615.9)

# Arrow 4: Half-open -> Open (trial fails)
p4_s = circ_pt(cx_h, cy_h, R, -75)
p4_e = circ_pt(cx_o, cy_o, R, 135)
p4_ctrl = (975.6, 573.8)

svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
  <title>A circuit breaker has three states</title>
  <desc>State transition diagram showing Closed, Open, and Half-open states with exact transition labels.</desc>

  <defs>
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{green}" />
    </marker>
    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="{orange}" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="{W}" height="{H}" fill="{bg}" />

  <!-- Title -->
  <text x="800" y="75" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="48" font-weight="bold" fill="{text_color}">A circuit breaker has three states</text>

  <!-- Arrows and edge labels -->
  <!-- 1. Closed to Open: too many failures -->
  <path d="M {p1_s[0]} {p1_s[1]} Q {p1_ctrl[0]} {p1_ctrl[1]} {p1_e[0]} {p1_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="800" y="195" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">too many failures</text>

  <!-- 2. Open to Half-open: after a cool-down -->
  <path d="M {p2_s[0]} {p2_s[1]} Q {p2_ctrl[0]} {p2_ctrl[1]} {p2_e[0]} {p2_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="1210" y="630" text-anchor="start" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">after a cool-down</text>

  <!-- 3. Half-open to Closed: trial succeeds -->
  <path d="M {p3_s[0]} {p3_s[1]} Q {p3_ctrl[0]} {p3_ctrl[1]} {p3_e[0]} {p3_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="510" y="635" text-anchor="end" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">trial succeeds</text>

  <!-- 4. Half-open to Open: trial fails -->
  <path d="M {p4_s[0]} {p4_s[1]} Q {p4_ctrl[0]} {p4_ctrl[1]} {p4_e[0]} {p4_e[1]}" fill="none" stroke="{green}" stroke-width="4" marker-end="url(#arrow-green)" />
  <text x="915" y="505" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="25" font-weight="bold" fill="{text_color}">trial fails</text>

  <!-- Nodes -->
  <!-- Node 1: Closed -->
  <g id="node-closed">
    <circle cx="{cx_c}" cy="{cy_c}" r="{R}" fill="{panel_green}" stroke="{green}" stroke-width="4" />
    <!-- Icon: Shield with checkmark (56px) -->
    <g transform="translate({cx_c}, {cy_c - 45})" stroke="{green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M -22 -18 L 0 -26 L 22 -18 L 22 4 C 22 18 0 28 0 28 C 0 28 -22 18 -22 4 Z" />
      <polyline points="-10 2 -2 10 12 -4" />
    </g>
    <text x="{cx_c}" y="{cy_c + 24}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="{green}">Closed</text>
    <text x="{cx_c}" y="{cy_c + 64}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="{text_color}">calls pass</text>
  </g>

  <!-- Node 2: Open -->
  <g id="node-open">
    <circle cx="{cx_o}" cy="{cy_o}" r="{R}" fill="{orange_panel}" stroke="{orange}" stroke-width="4" />
    <!-- Icon: Alert symbol (56px) -->
    <g transform="translate({cx_o}, {cy_o - 45})" stroke="{orange}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="0 -24 24 18 -24 18" />
      <line x1="0" y1="-7" x2="0" y2="4" />
      <circle cx="0" cy="11" r="2" fill="{orange}" stroke="none" />
    </g>
    <text x="{cx_o}" y="{cy_o + 24}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="{orange}">Open</text>
    <text x="{cx_o}" y="{cy_o + 64}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="{text_color}">calls fail fast</text>
  </g>

  <!-- Node 3: Half-open -->
  <g id="node-half-open">
    <circle cx="{cx_h}" cy="{cy_h}" r="{R}" fill="{panel_green}" stroke="{green}" stroke-width="4" />
    <!-- Icon: Clock for timer (56px) -->
    <g transform="translate({cx_h}, {cy_h - 45})" stroke="{green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="0" cy="0" r="23" />
      <polyline points="0 -13 0 0 9 0" />
      <line x1="0" y1="-23" x2="0" y2="-19" />
      <line x1="0" y1="19" x2="0" y2="23" />
      <line x1="-23" y1="0" x2="-19" y2="0" />
      <line x1="19" y1="0" x2="23" y2="0" />
    </g>
    <text x="{cx_h}" y="{cy_h + 24}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="32" font-weight="bold" fill="{green}">Half-open</text>
    <text x="{cx_h}" y="{cy_h + 64}" text-anchor="middle" font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="{text_color}">one trial call</text>
  </g>
</svg>
"""

with open("circuit_breaker.svg", "w") as f:
    f.write(svg)

print("Updated circuit_breaker.svg successfully.")
