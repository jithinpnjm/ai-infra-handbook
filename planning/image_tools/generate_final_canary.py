import re
import pathlib
import xml.etree.ElementTree as ET
import subprocess

def make_final_svg():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>The canary ladder moves traffic up in steps, and each step must pass its gates</title>')
    svg.append('  <desc>Visual infographic explaining the canary traffic staircase, latency and quality gates, promote, hold, and rollback decisions.</desc>')
    
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
    
    # Canvas background
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    
    # Title (48px bold, wrapped onto 2 lines with tspan)
    svg.append('  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">The canary ladder moves traffic up in steps, </tspan>')
    svg.append('    <tspan x="800" dy="56">and each step must pass its gates</tspan>')
    svg.append('  </text>')

    # ==================== GATE GROUPS ROW ====================
    # Above the staircase: row of two gate groups
    # Box 1: Latency gates (x=40..770, w=730, h=120, y=150..270)
    svg.append('  <g id="latency-gates">')
    svg.append('    <rect x="40" y="150" width="730" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Clock / Timer outline icon (56x56, stroke 4, green)
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

    # Box 2: Quality gates (x=830..1565, w=735, h=120, y=150..270)
    svg.append('  <g id="quality-gates">')
    svg.append('    <rect x="830" y="150" width="735" height="120" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Shield outline icon (56x56, stroke 4, green)
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

    # ==================== STAIRCASE OF SIX STEPS ====================
    # 6 steps rising from left to right.
    # Dimensions:
    # W_step = 158.0 (guarantees >= 16px pad for "traffic" and "percent")
    # W_dia = 104.0 (guarantees >= 16px pad for "gates")
    # Total span = 6 * 158 + 5 * 104 = 1468 px.
    # Start at x = 40.0.
    # Step 6 ends at 40 + 1468 = 1508.0 px.
    # Arrow line drops at x = 1555.0 px (47px to the right of Step 6, completely clear!).

    steps_data = [
        (1, "Shadow", "traffic", "shadow"),
        (2, "1", "percent", "gauge1"),
        (3, "5", "percent", "gauge5"),
        (4, "25", "percent", "gauge25"),
        (5, "50", "percent", "gauge50"),
        (6, "100", "percent", "target100"),
    ]

    cur_x = 40.0
    step_w = 158.0
    dia_w = 104.0
    step_h = 120.0
    dia_h = 76.0

    step_boxes = []
    diamonds = []

    for i in range(6):
        s_num, l1, l2, icon = steps_data[i]
        s_y = 640.0 - i * 60.0
        step_boxes.append((cur_x, s_y, step_w, step_h, s_num, l1, l2, icon))
        cur_x += step_w
        if i < 5:
            d_x = cur_x
            d_y = s_y - 30.0 + (step_h - dia_h)/2.0
            dcx = d_x + dia_w / 2.0
            dcy = s_y - 30.0 + step_h / 2.0
            diamonds.append((d_x, d_y, dia_w, dia_h, dcx, dcy))
            cur_x += dia_w

    # Connecting horizontal links between steps and diamonds
    for i in range(5):
        s_left = step_boxes[i]
        dia = diamonds[i]
        s_right = step_boxes[i+1]
        
        x_from = s_left[0] + s_left[2]
        y_mid = dia[5]
        # Thin connecting lines
        svg.append(f'  <line x1="{x_from:.1f}" y1="{y_mid:.1f}" x2="{dia[0]:.1f}" y2="{y_mid:.1f}" stroke="#207448" stroke-width="2.5" />')
        x_to = dia[0] + dia[2]
        svg.append(f'  <line x1="{x_to:.1f}" y1="{y_mid:.1f}" x2="{s_right[0]:.1f}" y2="{y_mid:.1f}" stroke="#207448" stroke-width="2.5" />')

    # Draw step boxes
    for x, y, w, h, num, l1, l2, icon in step_boxes:
        svg.append(f'  <g id="step-{num}">')
        svg.append(f'    <rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />')
        
        # Number circle (r=22, green, white text)
        nc_x = x + 34
        nc_y = y + 36
        svg.append(f'    <circle cx="{nc_x:.1f}" cy="{nc_y:.1f}" r="22" fill="#207448" />')
        svg.append(f'    <text x="{nc_x:.1f}" y="{nc_y + 8:.1f}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">{num}</text>')
        
        # Icon (40x40 outline)
        ic_x = x + 96
        ic_y = y + 16
        svg.append(f'    <g transform="translate({ic_x:.1f}, {ic_y:.1f})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
        if icon == "shadow":
            svg.append('      <path d="M 6 32 C 6 18 16 8 26 8 C 36 8 46 18 46 32" stroke-dasharray="4,3" />')
            svg.append('      <circle cx="26" cy="18" r="4" fill="#207448" />')
            svg.append('      <line x1="12" y1="36" x2="40" y2="36" />')
        elif icon == "gauge1":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="24" y2="10" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        elif icon == "gauge5":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="31" y2="12" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        elif icon == "gauge25":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="38" y2="24" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        elif icon == "gauge50":
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <line x1="24" y1="24" x2="24" y2="38" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        else: # target100
            svg.append('      <circle cx="24" cy="24" r="18" />')
            svg.append('      <circle cx="24" cy="24" r="9" />')
            svg.append('      <circle cx="24" cy="24" r="3" fill="#207448" />')
        svg.append('    </g>')
        
        # Step title: 30px bold
        t_cx = x + w / 2.0
        svg.append(f'    <text x="{t_cx:.1f}" y="{y + 82:.1f}" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">')
        svg.append(f'      <tspan x="{t_cx:.1f}" dy="0">{l1}</tspan>')
        svg.append(f'      <tspan x="{t_cx:.1f}" dy="32">{l2}</tspan>')
        svg.append('    </text>')
        svg.append('  </g>')

    # Draw 5 gate diamonds labelled "gates pass"
    for i, (dx, dy, dw, dh, dcx, dcy) in enumerate(diamonds, 1):
        svg.append(f'  <g id="gate-diamond-{i}">')
        p_top = f"{dcx:.1f},{dcy - dh/2.0:.1f}"
        p_right = f"{dcx + dw/2.0:.1f},{dcy:.1f}"
        p_bot = f"{dcx:.1f},{dcy + dh/2.0:.1f}"
        p_left = f"{dcx - dw/2.0:.1f},{dcy:.1f}"
        svg.append(f'    <polygon points="{p_top} {p_right} {p_bot} {p_left}" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
        svg.append(f'    <text x="{dcx:.1f}" y="{dcy - 2:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
        svg.append(f'      <tspan x="{dcx:.1f}" dy="0">gates</tspan>')
        svg.append(f'      <tspan x="{dcx:.1f}" dy="26">pass</tspan>')
        svg.append('    </text>')
        svg.append('  </g>')

    # ==================== OUTCOME BOXES ROW ====================
    # y = 840..1020 (height = 180)
    # Box 1: Promote (x = 40..520, w = 480)
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

    # Box 2: Hold (x = 555..1035, w = 480)
    svg.append('  <g id="outcome-hold">')
    svg.append('    <rect x="555" y="840" width="480" height="180" rx="14" fill="#f0f2f0" stroke="#707874" stroke-width="2.5" />')
    svg.append('    <g transform="translate(580, 865)" stroke="#707874" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <line x1="22" y1="18" x2="22" y2="38" />')
    svg.append('      <line x1="34" y1="18" x2="34" y2="38" />')
    svg.append('    </g>')
    svg.append('    <text x="660" y="902" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36">Hold</text>')
    svg.append('    <text x="795" y="960" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="795" dy="0">marginal results or </tspan>')
    svg.append('      <tspan x="795" dy="30">too few requests</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # Box 3: Rollback (x = 1070..1565, w = 495)
    svg.append('  <g id="outcome-rollback">')
    svg.append('    <rect x="1070" y="840" width="495" height="180" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3" />')
    svg.append('    <g transform="translate(1095, 865)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="24" />')
    svg.append('      <path d="M 18 24 L 28 14 L 38 24" />')
    svg.append('      <path d="M 28 16 V 36" />')
    svg.append('    </g>')
    svg.append('    <text x="1175" y="902" font-family="sans-serif" font-size="32" font-weight="bold" fill="#db8129">Rollback</text>')
    svg.append('    <text x="1317" y="960" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="1317" dy="0">hard failure such as </tspan>')
    svg.append('      <tspan x="1317" dy="30">quality drop or zero tokens</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')

    # ==================== ARROWS ====================
    # EXACTLY TWO ARROWS:
    # Arrow 1: Down arrow from Quality gates (x=1555) to Rollback (x=1555)
    # Starts at y = 270, ends at y = 838.
    # Clearance to Step 6 (ends at 1508) is 47 px! Completely clear!
    svg.append('  <!-- Arrow 1: Down arrow from gate row to Rollback (hard failure) -->')
    svg.append('  <line x1="1555" y1="270" x2="1555" y2="838" stroke="#db8129" stroke-width="3.5" marker-end="url(#arrow-orange)" />')
    # Pill label for "hard failure" placed to the left of the arrow line
    svg.append('  <rect x="1335" y="525" width="205" height="44" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="1.5" />')
    svg.append('  <text x="1437" y="555" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">hard failure</text>')

    # Arrow 2: From Hold up to Step 3 (the current step)
    # Step 3 center is at step_boxes[2][0] + step_boxes[2][2]/2
    s3_cx = step_boxes[2][0] + step_boxes[2][2] / 2.0
    s3_bot = step_boxes[2][1] + step_boxes[2][3]
    svg.append('  <!-- Arrow 2: Arrow from Hold back to the same step (wait for more evidence) -->')
    svg.append(f'  <line x1="{s3_cx:.1f}" y1="840" x2="{s3_cx:.1f}" y2="{s3_bot + 2:.1f}" stroke="#207448" stroke-width="3.5" marker-end="url(#arrow-green)" />')
    # Pill label for "wait for more evidence"
    svg.append(f'  <rect x="{s3_cx - 178:.1f}" y="718" width="356" height="44" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.5" />')
    svg.append(f'  <text x="{s3_cx:.1f}" y="748" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">wait for more evidence</text>')

    # ==================== TAKEAWAY BAR ====================
    svg.append('  <g id="takeaway-bar">')
    svg.append('    <rect x="40" y="1080" width="1520" height="64" rx="12" fill="#207448" />')
    svg.append('    <text x="800" y="1121" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#ffffff">Promote only on a clean pass with enough traffic, hold on thin data, roll back on a hard signal.</text>')
    svg.append('  </g>')

    svg.append('</svg>')
    return '\n'.join(svg)

# Save and verify
final_svg = make_final_svg()
pathlib.Path("candidate_final.svg").write_text(final_svg)
print("candidate_final.svg written successfully!")
