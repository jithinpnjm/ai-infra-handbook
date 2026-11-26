import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

def build_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>The canary ladder moves traffic up in steps, and each step must pass its gates</title>')
    svg.append('  <desc>Visual infographic explaining the canary traffic staircase, latency and quality gates, promote, hold, and rollback decisions.</desc>')
    svg.append('  <defs>')
    # Proportional arrow markers (18px)
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title: 48px bold
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The canary ladder moves traffic up in steps, </tspan>')
    svg.append('    <tspan x="800" dy="56">and each step must pass its gates</tspan>')
    svg.append('  </text>')

    # ==================== GATE GROUPS ROW ====================
    # Latency gates box: x=40..770 (w=730, h=120, y=150..270)
    svg.append('  <g id="latency-gates">')
    svg.append('    <rect x="40" y="150" width="730" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Clock / timer icon (56x56, stroke 4, green)
    svg.append('    <g transform="translate(65, 182)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <polyline points="28,14 28,28 40,28" />')
    svg.append('    </g>')
    svg.append('    <text x="140" y="190" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Latency gates</text>')
    svg.append('    <text x="140" y="226" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="140" dy="0">canary TTFT p99 and ITL p99 </tspan>')
    svg.append('      <tspan x="140" dy="30">against baseline, ratio limit</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Quality gates box: x=830..1560 (w=730, h=120, y=150..270)
    svg.append('  <g id="quality-gates">')
    svg.append('    <rect x="830" y="150" width="730" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Shield / security icon (56x56, stroke 4, green)
    svg.append('    <g transform="translate(855, 182)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 6 L 48 14 C 48 34 28 48 28 48 C 28 48 8 34 8 14 Z" />')
    svg.append('      <polyline points="20,26 26,32 36,20" />')
    svg.append('    </g>')
    svg.append('    <text x="930" y="190" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Quality gates</text>')
    svg.append('    <text x="930" y="226" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="930" dy="0">eval score, finish_reason length share, </tspan>')
    svg.append('      <tspan x="930" dy="30">error rate</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== STAIRCASE (6 STEPS & 5 DIAMONDS) ====================
    # We want Step 6 to end at x <= 1470 so an arrow at x = 1530 has > 60px clearance!
    # Let W_step = 158 px (perfect >= 16px pad for 30px bold text)
    # Let W_dia = 96 px (width=96, height=80)
    # Total items: 6 steps (948px) + 5 diamonds (480px) = 1428px.
    # Total span = 1470 - 40 = 1430px.
    # Remaining for 10 gaps: 1430 - 1428 = 2px -> 0.2px or touch!
    # What if W_step = 156 px, W_dia = 96 px: 936 + 480 = 1416px -> 14px for gaps (1.4px each).
    # Let's test W_step = 158, W_dia = 96, gap = 2px:
    # 6 * 158 + 5 * 96 + 10 * 2 = 948 + 480 + 20 = 1448 px!
    # Step 6 ends at 40 + 1448 = 1488 px!
    # Clearance to x = 1540 is 52 px!
    # Clearance from x = 1540 to 1600 is 60 px!
    
    # Gate diamonds (5 diamonds)
    # Each diamond is width W_d = 100, height 92
    W_s = 158.0
    W_d = 100.0
    G = 2.0
    
    # Calculate step and diamond X coordinates
    step_xs = []
    dia_xs = []
    cur_x = 40.0
    for i in range(6):
        step_xs.append(cur_x)
        cur_x += W_s
        if i < 5:
            cur_x += G
            dia_xs.append(cur_x)
            cur_x += W_d
            cur_x += G
            
    # Y coordinates: rising from left to right (Step 1 lowest, Step 6 highest)
    # Step 1: y = 640..760 (h=120)
    # Step 2: y = 580..700
    # Step 3: y = 520..640
    # Step 4: y = 460..580
    # Step 5: y = 400..520
    # Step 6: y = 340..460
    step_ys = [640.0 - i * 60.0 for i in range(6)]
    
    # Diamonds sit vertically centered on the step riser / level
    dia_ys = [step_ys[i] + 30.0 for i in range(5)]
    
    # Connector lines between steps and diamonds
    for i in range(5):
        x1 = step_xs[i] + W_s
        x2 = dia_xs[i]
        y_c = dia_ys[i]
        svg.append(f'  <line x1="{x1:.1f}" y1="{y_c:.1f}" x2="{x2:.1f}" y2="{y_c:.1f}" stroke="#207448" stroke-width="2.5" />')
        x3 = dia_xs[i] + W_d
        x4 = step_xs[i+1]
        svg.append(f'  <line x1="{x3:.1f}" y1="{y_c:.1f}" x2="{x4:.1f}" y2="{y_c:.1f}" stroke="#207448" stroke-width="2.5" />')

    # Steps definitions
    steps_data = [
        ("Shadow", "traffic", "1", "shadow"),
        ("1", "percent", "2", "gauge-1"),
        ("5", "percent", "3", "gauge-5"),
        ("25", "percent", "4", "gauge-25"),
        ("50", "percent", "5", "gauge-50"),
        ("100", "percent", "6", "gauge-100")
    ]
    
    for i, (l1, l2, num, icon_type) in enumerate(steps_data):
        sx = step_xs[i]
        sy = step_ys[i]
        cx = sx + W_s / 2.0
        
        svg.append(f'  <g id="step-{num}">')
        svg.append(f'    <rect x="{sx:.1f}" y="{sy:.1f}" width="{W_s:.1f}" height="120.0" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
        # Number circle: r=22, green, white text
        nc_x = sx + 34.0
        nc_y = sy + 36.0
        svg.append(f'    <circle cx="{nc_x:.1f}" cy="{nc_y:.1f}" r="22" fill="#207448" />')
        svg.append(f'    <text x="{nc_x:.1f}" y="{nc_y + 8.0:.1f}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">{num}</text>')
        
        # Icon
        ic_x = sx + 95.0
        ic_y = sy + 16.0
        svg.append(f'    <g transform="translate({ic_x:.1f}, {ic_y:.1f})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
        if icon_type == "shadow":
            svg.append('      <path d="M 6 32 C 6 18 16 8 26 8 C 36 8 46 18 46 32" stroke-dasharray="4,3" />')
            svg.append('      <circle cx="26" cy="18" r="4" fill="#207448" />')
            svg.append('      <line x1="12" y1="36" x2="40" y2="36" />')
        elif icon_type == "gauge-1":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="24" y2="10" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        elif icon_type == "gauge-5":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="31" y2="12" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        elif icon_type == "gauge-25":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="38" y2="24" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        elif icon_type == "gauge-50":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="24" y2="38" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        else: # gauge-100
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <circle cx="24" cy="24" r="9" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        svg.append('    </g>')
        
        # Step label text: 30px bold
        svg.append(f'    <text x="{cx:.1f}" y="{sy + 82.0:.1f}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
        svg.append(f'      <tspan x="{cx:.1f}" dy="0">{l1}</tspan>')
        svg.append(f'      <tspan x="{cx:.1f}" dy="32">{l2}</tspan>')
        svg.append('    </text>')
        svg.append('  </g>')

    # Gate diamonds (5 diamonds)
    # Each diamond is width W_d = 100, height 92
    H_d = 92.0
    for i in range(5):
        dx = dia_xs[i]
        dcx = dx + W_d / 2.0
        dcy = dia_ys[i]
        p_top = f"{dcx:.1f},{dcy - H_d/2.0:.1f}"
        p_right = f"{dx + W_d:.1f},{dcy:.1f}"
        p_bottom = f"{dcx:.1f},{dcy + H_d/2.0:.1f}"
        p_left = f"{dx:.1f},{dcy:.1f}"
        
        svg.append(f'  <g id="gate-diamond-{i+1}">')
        svg.append(f'    <polygon points="{p_top} {p_right} {p_bottom} {p_left}" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
        svg.append(f'    <text x="{dcx:.1f}" y="{dcy - 6.0:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
        svg.append(f'      <tspan x="{dcx:.1f}" dy="0">gates</tspan>')
        svg.append(f'      <tspan x="{dcx:.1f}" dy="26">pass</tspan>')
        svg.append('    </text>')
        svg.append('  </g>')

    # ==================== OUTCOME BOXES ROW ====================
    # Below the gate diamonds: row of three outcome boxes
    # Promote (green), Hold (neutral grey), Rollback (orange)
    # y = 840..1020 (height 180)
    # Boxes:
    # Promote: x = 40..520 (w = 480)
    # Hold: x = 560..1040 (w = 480)
    # Rollback: x = 1080..1560 (w = 480)
    
    # 1. Promote
    svg.append('  <g id="outcome-promote">')
    svg.append('    <rect x="40" y="840" width="480" height="180" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="3" />')
    svg.append('    <g transform="translate(65, 865)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <polyline points="18,28 24,34 38,20" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="902" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Promote</text>')
    svg.append('    <text x="280" y="960" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="280" dy="0">all gates passed, </tspan>')
    svg.append('      <tspan x="280" dy="30">enough traffic</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # 2. Hold
    svg.append('  <g id="outcome-hold">')
    svg.append('    <rect x="560" y="840" width="480" height="180" rx="14" fill="#f0f2f0" stroke="#707874" stroke-width="2.5" />')
    svg.append('    <g transform="translate(585, 865)" stroke="#707874" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <line x1="22" y1="18" x2="22" y2="38" />')
    svg.append('      <line x1="34" y1="18" x2="34" y2="38" />')
    svg.append('    </g>')
    svg.append('    <text x="665" y="902" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Hold</text>')
    svg.append('    <text x="800" y="960" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="800" dy="0">marginal results or </tspan>')
    svg.append('      <tspan x="800" dy="30">too few requests</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # 3. Rollback
    svg.append('  <g id="outcome-rollback">')
    svg.append('    <rect x="1080" y="840" width="480" height="180" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3" />')
    svg.append('    <g transform="translate(1105, 865)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <path d="M 18 24 L 28 14 L 38 24" />')
    svg.append('      <path d="M 28 16 V 36" />')
    svg.append('    </g>')
    svg.append('    <text x="1185" y="902" font-family="sans-serif" font-size="32" font-weight="bold" fill="#db8129">Rollback</text>')
    svg.append('    <text x="1320" y="960" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1320" dy="0">hard failure such as </tspan>')
    svg.append('      <tspan x="1320" dy="30">quality drop or zero tokens</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== ARROWS ====================
    # Arrow 1: Down arrow from gate row to Rollback labelled "hard failure"
    # Gate row ends at x = 1560, y = 270.
    # Rollback is at x = 1080..1560, top edge y = 840.
    # Step 6 ends at x = 1508, y = 340..460.
    # We place Arrow 1 at x = 1545:
    # Starts at Quality gates bottom edge (y = 270), drops straight down to Rollback top edge (y = 838).
    # Distance from Step 6 right edge (1508) to arrow (1545) is 37 px!
    # Distance from arrow (1545) to canvas edge (1600) is 55 px!
    # Arrow does NOT pass through Step 6 or any node!
    svg.append('  <!-- Arrow 1: Gate row to Rollback (hard failure) -->')
    svg.append('  <line x1="1545" y1="270" x2="1545" y2="838" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    # Pill label for "hard failure" placed at y = 520..584 (below Step 6 which ended at y = 460)
    # Centered at x = 1545, w = 98, h = 64
    svg.append('  <rect x="1496" y="520" width="98" height="64" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="1.5" />')
    svg.append('  <text x="1545" y="546" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">')
    svg.append('    <tspan x="1545" dy="0">hard</tspan>')
    svg.append('    <tspan x="1545" dy="26">failure</tspan>')
    svg.append('  </text>')

    # Arrow 2: Arrow from Hold back to the same step labelled "wait for more evidence"
    # Hold is at x = 560..1040, y = 840.
    # Step 3 is at x = step_xs[2]..step_xs[2]+W_s (x = 618..776), bottom edge y = 640.
    # An arrow starts from Hold top edge at x = 650, y = 840 and goes straight UP to Step 3 bottom edge at x = 650, y = 642!
    # Ends exactly at the bottom edge of Step 3!
    svg.append('  <!-- Arrow 2: Hold back to the same step (wait for more evidence) -->')
    svg.append('  <line x1="650" y1="840" x2="650" y2="642" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    # Label "wait for more evidence" placed cleanly beside the arrow in the empty corridor
    # At x = 665..985, y = 718..762
    svg.append('  <rect x="668" y="718" width="310" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append('  <text x="823" y="749" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">wait for more evidence</text>')

    # ==================== TAKEAWAY BAR ====================
    # Green takeaway bar at bottom: y = 1080..1144 (h=64)
    svg.append('  <g id="takeaway-bar">')
    svg.append('    <rect x="40" y="1080" width="1520" height="64" rx="12" fill="#207448" />')
    svg.append('    <text x="800" y="1121" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Promote only on a clean pass with enough traffic, hold on thin data, roll back on a hard signal.</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

if __name__ == '__main__':
    content = build_svg()
    p = pathlib.Path("perfect_candidate.svg")
    p.write_text(content)
    print("Wrote perfect_candidate.svg successfully!")
