import re
import xml.etree.ElementTree as ET

# Define the SVG generator
def generate_svg():
    H = 960
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>The SRE variant: incidents, capacity and rollout safety [report]</title>')
    svg.append('  <desc>Visual flowchart illustrating the SRE variant: incidents, capacity and rollout safety.</desc>')
    svg.append('  <defs>')
    # 18px proportional green arrowhead marker
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    # 18px proportional orange arrowhead marker
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title (48px bold, 2 lines)
    svg.append('  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The SRE variant: incidents, capacity </tspan>')
    svg.append('    <tspan x="800" dy="58">and rollout safety [report]</tspan>')
    svg.append('  </text>')

    # Grid parameters
    col_w = 310
    col_gap = 80
    left_m = 60
    
    col_x = [
        left_m,                               # Col 1: 60
        left_m + col_w + col_gap,             # Col 2: 450
        left_m + 2*(col_w + col_gap),         # Col 3: 840
        left_m + 3*(col_w + col_gap)          # Col 4: 1230
    ]
    
    row_top_y = 190
    row_h = 240
    row_bot_y = 580
    row_mid_y = 385
    
    # Nodes configuration:
    # CAP: Col 1, Top
    # ROL: Col 1, Bottom
    # SLO: Col 2, Mid (Orange highlight!)
    # AL:  Col 3, Top
    # IC:  Col 4, Top
    # PM:  Col 4, Bottom
    # RB:  Col 3, Bottom
    
    # Arrow 1: CAP -> SLO
    # (370, 310) -> (410, 310) -> (410, 445) -> (450, 445)
    svg.append('  <!-- Connection: Capacity forecast -> SLOs -->')
    svg.append('  <path d="M 370 310 L 410 310 L 410 445 L 450 445" fill="none" stroke="#207448" stroke-width="4" stroke-linejoin="round" marker-end="url(#arrow-green)" />')
    
    # Arrow 2: ROL -> SLO
    # (370, 700) -> (410, 700) -> (410, 565) -> (450, 565)
    svg.append('  <!-- Connection: Canary rollout -> SLOs -->')
    svg.append('  <path d="M 370 700 L 410 700 L 410 565 L 450 565" fill="none" stroke="#207448" stroke-width="4" stroke-linejoin="round" marker-end="url(#arrow-green)" />')
    
    # Arrow 3: SLO -> AL
    # (760, 445) -> (800, 445) -> (800, 310) -> (840, 310)
    svg.append('  <!-- Connection: SLOs -> Burn-rate alerts -->')
    svg.append('  <path d="M 760 445 L 800 445 L 800 310 L 840 310" fill="none" stroke="#207448" stroke-width="4" stroke-linejoin="round" marker-end="url(#arrow-green)" />')
    
    # Arrow 4: AL -> IC
    # (1150, 310) -> (1230, 310)
    svg.append('  <!-- Connection: Burn-rate alerts -> Incident process -->')
    svg.append('  <path d="M 1150 310 L 1230 310" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    
    # Arrow 5: IC -> PM
    # (1385, 430) -> (1385, 580)
    svg.append('  <!-- Connection: Incident process -> Post-mortem -->')
    svg.append('  <path d="M 1385 430 L 1385 580" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')
    
    # Arrow 6: PM -> RB
    # (1230, 700) -> (1150, 700)
    svg.append('  <!-- Connection: Post-mortem -> Runbooks, automation -->')
    svg.append('  <path d="M 1230 700 L 1150 700" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # Node: CAP (Capacity forecast)
    x = col_x[0]
    y = row_top_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: Capacity forecast -->')
    svg.append(f'  <g id="node-cap">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Outline icon: Capacity / forecast (trend + bars)
    svg.append(f'    <g transform="translate({cx - 28}, {y + 30})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <rect x="6" y="30" width="8" height="18" rx="2" />')
    svg.append(f'      <rect x="20" y="20" width="8" height="28" rx="2" />')
    svg.append(f'      <rect x="34" y="10" width="8" height="38" rx="2" />')
    svg.append(f'      <polyline points="6,24 20,14 42,4" />')
    svg.append(f'      <polyline points="32,4 42,4 42,14" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 145}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{cx}" dy="0">Capacity </tspan>')
    svg.append(f'      <tspan x="{cx}" dy="40">forecast</tspan>')
    svg.append(f'    </text>')
    svg.append(f'  </g>')

    # Node: ROL (Canary rollout)
    x = col_x[0]
    y = row_bot_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: Canary rollout -->')
    svg.append(f'  <g id="node-rol">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Outline icon: Canary rollout (gauge dial with canary indicator needle)
    svg.append(f'    <g transform="translate({cx - 28}, {y + 30})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <path d="M 8 42 A 22 22 0 1 1 48 42" />')
    svg.append(f'      <line x1="28" y1="28" x2="40" y2="16" />')
    svg.append(f'      <circle cx="28" cy="28" r="4" fill="#207448" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 145}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{cx}" dy="0">Canary </tspan>')
    svg.append(f'      <tspan x="{cx}" dy="40">rollout</tspan>')
    svg.append(f'    </text>')
    svg.append(f'  </g>')

    # Node: SLO (SLOs) - HIGHLIGHTED in ORANGE (#db8129)
    x = col_x[1]
    y = row_mid_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: SLOs (Primary pivot highlighted in orange) -->')
    svg.append(f'  <g id="node-slo">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#ffffff" stroke="#db8129" stroke-width="3.5" />')
    # Outline icon: Target / Bullseye (crosshair) in orange
    svg.append(f'    <g transform="translate({cx - 28}, {y + 35})" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <circle cx="28" cy="28" r="22" />')
    svg.append(f'      <circle cx="28" cy="28" r="13" />')
    svg.append(f'      <circle cx="28" cy="28" r="4" fill="#db8129" />')
    svg.append(f'      <line x1="28" y1="2" x2="28" y2="10" />')
    svg.append(f'      <line x1="28" y1="46" x2="28" y2="54" />')
    svg.append(f'      <line x1="2" y1="28" x2="10" y2="28" />')
    svg.append(f'      <line x1="46" y1="28" x2="54" y2="28" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 160}" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">SLOs</text>')
    svg.append(f'  </g>')

    # Node: AL (Burn-rate alerts)
    x = col_x[2]
    y = row_top_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: Burn-rate alerts -->')
    svg.append(f'  <g id="node-al">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Outline icon: Alert bell
    svg.append(f'    <g transform="translate({cx - 28}, {y + 30})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <path d="M 28 8 C 20 8 16 14 16 24 C 16 34 10 38 10 40 H 46 C 46 38 40 34 40 24 C 40 14 36 8 28 8 Z" />')
    svg.append(f'      <path d="M 24 44 A 4 4 0 0 0 32 44" />')
    svg.append(f'      <line x1="28" y1="4" x2="28" y2="8" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 145}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{cx}" dy="0">Burn-rate </tspan>')
    svg.append(f'      <tspan x="{cx}" dy="40">alerts</tspan>')
    svg.append(f'    </text>')
    svg.append(f'  </g>')

    # Node: IC (Incident process)
    x = col_x[3]
    y = row_top_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: Incident process -->')
    svg.append(f'  <g id="node-ic">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Outline icon: Siren / Beacon
    svg.append(f'    <g transform="translate({cx - 28}, {y + 30})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <path d="M 16 42 H 40 L 36 20 C 36 14 20 14 20 20 Z" />')
    svg.append(f'      <line x1="10" y1="48" x2="46" y2="48" />')
    svg.append(f'      <line x1="16" y1="42" x2="10" y2="48" />')
    svg.append(f'      <line x1="40" y1="42" x2="46" y2="48" />')
    svg.append(f'      <line x1="28" y1="6" x2="28" y2="12" />')
    svg.append(f'      <line x1="12" y1="12" x2="17" y2="17" />')
    svg.append(f'      <line x1="44" y1="12" x2="39" y2="17" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 145}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{cx}" dy="0">Incident </tspan>')
    svg.append(f'      <tspan x="{cx}" dy="40">process</tspan>')
    svg.append(f'    </text>')
    svg.append(f'  </g>')

    # Node: PM (Post-mortem)
    x = col_x[3]
    y = row_bot_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: Post-mortem -->')
    svg.append(f'  <g id="node-pm">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Outline icon: Document review (report document)
    svg.append(f'    <g transform="translate({cx - 28}, {y + 35})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <path d="M 12 6 H 32 L 44 18 V 50 H 12 Z" />')
    svg.append(f'      <path d="M 32 6 V 18 H 44" />')
    svg.append(f'      <line x1="18" y1="26" x2="38" y2="26" />')
    svg.append(f'      <line x1="18" y1="34" x2="38" y2="34" />')
    svg.append(f'      <line x1="18" y1="42" x2="30" y2="42" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 160}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Post-mortem</text>')
    svg.append(f'  </g>')

    # Node: RB (Runbooks, automation)
    x = col_x[2]
    y = row_bot_y
    cx = x + col_w // 2
    svg.append(f'  <!-- Node: Runbooks, automation -->')
    svg.append(f'  <g id="node-rb">')
    svg.append(f'    <rect x="{x}" y="{y}" width="{col_w}" height="{row_h}" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    # Outline icon: Automation console window
    svg.append(f'    <g transform="translate({cx - 28}, {y + 30})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append(f'      <rect x="6" y="8" width="44" height="40" rx="6" />')
    svg.append(f'      <line x1="6" y1="20" x2="50" y2="20" />')
    svg.append(f'      <circle cx="14" cy="14" r="2" fill="#207448" />')
    svg.append(f'      <circle cx="22" cy="14" r="2" fill="#207448" />')
    svg.append(f'      <path d="M 14 30 L 20 35 L 14 40" />')
    svg.append(f'      <line x1="26" y1="40" x2="38" y2="40" />')
    svg.append(f'    </g>')
    svg.append(f'    <text x="{cx}" y="{y + 145}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
    svg.append(f'      <tspan x="{cx}" dy="0">Runbooks, </tspan>')
    svg.append(f'      <tspan x="{cx}" dy="40">automation</tspan>')
    svg.append(f'    </text>')
    svg.append(f'  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

svg_content = generate_svg()
with open('test_candidate_sre.svg', 'w') as f:
    f.write(svg_content)
print("Generated test_candidate_sre.svg successfully.")

