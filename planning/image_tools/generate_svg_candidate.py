#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_perfect_svg():
    W = 1600
    H = 950
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>One node\'s drain, change, validate, return path</title>')
    svg.append('  <desc>Visual flowchart of one GPU node lifecycle: Drain from Slurm, Wait until no jobs remain, block with apply_changes and Validate, Return to service, and rescue path on failure to fail with message leaving node DRAINED for investigation.</desc>')
    svg.append('')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 14 14" refX="11" refY="7" markerWidth="10" markerHeight="10" orient="auto-start-reverse">')
    svg.append('      <path d="M 1 2 L 11 7 L 1 12 Z" fill="#207448"/>')
    svg.append('    </marker>')
    svg.append('  </defs>')
    svg.append('')
    svg.append('  <!-- Background -->')
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5"/>')
    svg.append('')
    svg.append('  <!-- Title (48px bold) -->')
    svg.append('  <text x="800" y="62" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36" text-anchor="middle">One node\'s drain, change, validate, return path</text>')
    svg.append('')
    
    # Coordinates of 4 main steps:
    # Available width: 1600 - 80 = 1520 px.
    # Margins: left=40, right=40.
    # 3 arrows between 4 boxes: gap = 36 px.
    # Box 1: x = 40, w = 296 (ends at 336)
    # Arrow 1->2: x=336 to x=372
    # Box 2: x = 372, w = 296 (ends at 668)
    # Arrow 2->3: x=668 to x=704
    # Box 3: x = 704, w = 556 (ends at 1260)
    # Arrow 3->4: x=1260 to x=1296
    # Box 4: x = 1296, w = 264 (ends at 1560)
    
    b_y = 110
    b_h = 420
    
    # ==================== STEP 1 ====================
    svg.append('  <!-- ==================== STEP 1: Drain from Slurm ==================== -->')
    svg.append('  <g id="step-1">')
    svg.append(f'    <rect x="40" y="{b_y}" width="296" height="{b_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Number circle 1
    svg.append(f'    <circle cx="82" cy="{b_y + 40}" r="24" fill="#207448"/>')
    svg.append(f'    <text x="82" y="{b_y + 40}" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">1</text>')
    # Barrier / Gate outline icon (56px)
    svg.append(f'    <g transform="translate(258, {b_y + 12})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="8" y1="8" x2="8" y2="48"/>')
    svg.append('      <line x1="48" y1="8" x2="48" y2="48"/>')
    svg.append('      <line x1="4" y1="18" x2="52" y2="18"/>')
    svg.append('      <line x1="4" y1="36" x2="52" y2="36"/>')
    svg.append('      <line x1="16" y1="18" x2="40" y2="36"/>')
    svg.append('      <line x1="16" y1="36" x2="40" y2="18"/>')
    svg.append('    </g>')
    # Title
    svg.append(f'    <text x="188" y="{b_y + 115}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448" text-anchor="middle">')
    svg.append(f'      <tspan x="188" dy="0">Drain from</tspan>')
    svg.append(f'      <tspan x="188" dy="38">Slurm</tspan>')
    svg.append('    </text>')
    # Line divider
    svg.append(f'    <line x1="60" y1="{b_y + 185}" x2="316" y2="{b_y + 185}" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 4"/>')
    # Command: scontrol update State=DRAIN
    svg.append(f'    <text x="188" y="{b_y + 245}" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append(f'      <tspan x="188" dy="0">scontrol update</tspan>')
    svg.append(f'      <tspan x="188" dy="34">State=DRAIN</tspan>')
    svg.append('    </text>')
    # Secondary: delegate_to the Slurm controller
    svg.append(f'    <text x="188" y="{b_y + 345}" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append(f'      <tspan x="188" dy="0">delegate_to the</tspan>')
    svg.append(f'      <tspan x="188" dy="34">Slurm controller</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # Arrow 1 -> 2
    svg.append('  <!-- Arrow 1 -> 2 -->')
    svg.append(f'  <line x1="336" y1="{b_y + 210}" x2="372" y2="{b_y + 210}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>')
    svg.append('')
    
    # ==================== STEP 2 ====================
    svg.append('  <!-- ==================== STEP 2: Wait until no jobs remain ==================== -->')
    svg.append('  <g id="step-2">')
    svg.append(f'    <rect x="372" y="{b_y}" width="296" height="{b_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Number circle 2
    svg.append(f'    <circle cx="414" cy="{b_y + 40}" r="24" fill="#207448"/>')
    svg.append(f'    <text x="414" y="{b_y + 40}" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">2</text>')
    # Clock / Timer outline icon (56px)
    svg.append(f'    <g transform="translate(590, {b_y + 12})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22"/>')
    svg.append('      <polyline points="28,14 28,28 38,28"/>')
    svg.append('    </g>')
    # Title
    svg.append(f'    <text x="520" y="{b_y + 115}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448" text-anchor="middle">')
    svg.append(f'      <tspan x="520" dy="0">Wait until no</tspan>')
    svg.append(f'      <tspan x="520" dy="38">jobs remain</tspan>')
    svg.append('    </text>')
    # Line divider
    svg.append(f'    <line x1="392" y1="{b_y + 185}" x2="648" y2="{b_y + 185}" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 4"/>')
    # Command: squeue -h -w
    svg.append(f'    <text x="520" y="{b_y + 225}" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">squeue -h -w</text>')
    # until stdout is empty
    svg.append(f'    <text x="520" y="{b_y + 278}" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append(f'      <tspan x="520" dy="0">until stdout</tspan>')
    svg.append(f'      <tspan x="520" dy="32">is empty</tspan>')
    svg.append('    </text>')
    # retries 120
    svg.append(f'    <text x="520" y="{b_y + 365}" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">retries 120</text>')
    # delay 30
    svg.append(f'    <text x="520" y="{b_y + 400}" font-family="sans-serif" font-size="24" fill="#303a36" text-anchor="middle">delay 30</text>')
    svg.append('  </g>')
    svg.append('')
    
    # Arrow 2 -> 3
    svg.append('  <!-- Arrow 2 -> 3 -->')
    svg.append(f'  <line x1="668" y1="{b_y + 210}" x2="704" y2="{b_y + 210}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>')
    svg.append('')
    
    # ==================== STEP 3: Block Container ====================
    svg.append('  <!-- ==================== STEP 3: block ==================== -->')
    svg.append('  <g id="step-3-block">')
    svg.append(f'    <rect x="704" y="{b_y}" width="556" height="{b_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Number circle 3
    svg.append(f'    <circle cx="744" cy="{b_y + 40}" r="24" fill="#207448"/>')
    svg.append(f'    <text x="744" y="{b_y + 40}" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">3</text>')
    # Container title: block
    svg.append(f'    <text x="785" y="{b_y + 49}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">block</text>')
    
    # Sub-box A: apply_changes
    # x = 724, w = 246
    svg.append(f'    <rect x="724" y="{b_y + 85}" width="246" height="305" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Gear outline icon (56px)
    svg.append(f'    <g transform="translate(819, {b_y + 115})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="10"/>')
    svg.append('      <line x1="28" y1="6" x2="28" y2="14"/>')
    svg.append('      <line x1="28" y1="42" x2="28" y2="50"/>')
    svg.append('      <line x1="6" y1="28" x2="14" y2="28"/>')
    svg.append('      <line x1="42" y1="28" x2="50" y2="28"/>')
    svg.append('      <line x1="12" y1="12" x2="18" y2="18"/>')
    svg.append('      <line x1="38" y1="38" x2="44" y2="44"/>')
    svg.append('      <line x1="12" y1="44" x2="18" y2="38"/>')
    svg.append('      <line x1="38" y1="18" x2="44" y2="12"/>')
    svg.append('    </g>')
    # apply_changes text
    svg.append(f'    <text x="847" y="{b_y + 260}" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36" text-anchor="middle">apply_changes</text>')
    
    # Arrow inside block: apply_changes -> Validate
    svg.append(f'    <line x1="970" y1="{b_y + 237}" x2="994" y2="{b_y + 237}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>')
    
    # Sub-box B: Validate
    # x = 994, w = 246
    svg.append(f'    <rect x="994" y="{b_y + 85}" width="246" height="305" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>')
    # Shield checkmark outline icon (56px)
    svg.append(f'    <g transform="translate(1089, {b_y + 115})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 28 8 L 48 16 C 48 34 28 48 28 50 C 28 48 8 34 8 16 Z"/>')
    svg.append('      <polyline points="18,28 25,35 38,20"/>')
    svg.append('    </g>')
    # Validate text
    svg.append(f'    <text x="1117" y="{b_y + 260}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36" text-anchor="middle">Validate</text>')
    svg.append('  </g>')
    svg.append('')
    
    # Arrow 3 -> 4
    svg.append('  <!-- Arrow 3 -> 4 -->')
    svg.append(f'  <line x1="1260" y1="{b_y + 210}" x2="1296" y2="{b_y + 210}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>')
    svg.append('')
    
    # ==================== STEP 4 ====================
    svg.append('  <!-- ==================== STEP 4: Return to service ==================== -->')
    svg.append('  <g id="step-4">')
    svg.append(f'    <rect x="1296" y="{b_y}" width="264" height="{b_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Number circle 4
    svg.append(f'    <circle cx="1336" cy="{b_y + 40}" r="24" fill="#207448"/>')
    svg.append(f'    <text x="1336" y="{b_y + 40}" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff" text-anchor="middle" dominant-baseline="central">4</text>')
    # Server rack / Return outline icon (56px)
    svg.append(f'    <g transform="translate(1488, {b_y + 12})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="8" width="44" height="15" rx="3"/>')
    svg.append('      <rect x="6" y="27" width="44" height="15" rx="3"/>')
    svg.append('      <circle cx="14" cy="15.5" r="2" fill="#207448"/>')
    svg.append('      <circle cx="14" cy="34.5" r="2" fill="#207448"/>')
    svg.append('      <polyline points="28,34 35,40 46,26"/>')
    svg.append('    </g>')
    # Title
    svg.append(f'    <text x="1428" y="{b_y + 115}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448" text-anchor="middle">')
    svg.append(f'      <tspan x="1428" dy="0">Return to</tspan>')
    svg.append(f'      <tspan x="1428" dy="38">service</tspan>')
    svg.append('    </text>')
    # Line divider
    svg.append(f'    <line x1="1314" y1="{b_y + 185}" x2="1542" y2="{b_y + 185}" stroke="#207448" stroke-width="1.5" stroke-dasharray="4 4"/>')
    # Command: scontrol update State=RESUME
    svg.append(f'    <text x="1428" y="{b_y + 270}" font-family="monospace" font-size="24" fill="#303a36" text-anchor="middle">')
    svg.append(f'      <tspan x="1428" dy="0">scontrol update</tspan>')
    svg.append(f'      <tspan x="1428" dy="34">State=RESUME</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # ==================== RESCUE ARROW ====================
    # Vertical line straight down from block container to rescue box
    svg.append('  <!-- ==================== RESCUE PATH ==================== -->')
    svg.append(f'  <line x1="982" y1="{b_y + b_h}" x2="982" y2="590" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>')
    svg.append('')
    
    # ==================== RESCUE BOX ====================
    # Orange only on rescue box: border #db8129, stroke-width 3.5, background #fffaf5
    res_y = 590
    res_w = 660
    res_x = 982 - res_w // 2 # 652
    res_h = 190
    
    svg.append('  <!-- Rescue box (ORANGE ONLY) -->')
    svg.append('  <g id="rescue-box">')
    svg.append(f'    <rect x="{res_x}" y="{res_y}" width="{res_w}" height="{res_h}" rx="14" fill="#fffaf5" stroke="#db8129" stroke-width="3.5"/>')
    # Warning triangle outline icon in orange (56px)
    svg.append(f'    <g transform="translate({res_x + 36}, {res_y + 67})" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <polygon points="28,6 52,48 4,48"/>')
    svg.append('      <line x1="28" y1="20" x2="28" y2="32"/>')
    svg.append('      <circle cx="28" cy="41" r="2" fill="#db8129" stroke="none"/>')
    svg.append('    </g>')
    # fail with message
    svg.append(f'    <text x="{res_x + 360}" y="{res_y + 70}" font-family="sans-serif" font-size="32" font-weight="bold" fill="#303a36" text-anchor="middle">fail with message</text>')
    # node left DRAINED for investigation
    svg.append(f'    <text x="{res_x + 360}" y="{res_y + 125}" font-family="sans-serif" font-size="26" fill="#303a36" text-anchor="middle">')
    svg.append(f'      <tspan x="{res_x + 360}" dy="0">node left DRAINED for</tspan>')
    svg.append(f'      <tspan x="{res_x + 360}" dy="34">investigation</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')
    
    # ==================== NOTE UNDER RESCUE BOX ====================
    note_y = 824
    note_w = 1180
    note_x = 800 - note_w // 2 # 210
    note_h = 76
    
    svg.append('  <!-- Note under the rescue box -->')
    svg.append('  <g id="rescue-note">')
    svg.append(f'    <rect x="{note_x}" y="{note_y}" width="{note_w}" height="{note_h}" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>')
    # Shield / Safe check outline icon (56px)
    svg.append(f'    <g transform="translate({note_x + 24}, {note_y + 14})" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <path d="M 24 6 L 40 14 C 40 30 24 40 24 42 C 24 40 8 30 8 14 Z"/>')
    svg.append('      <polyline points="16,24 22,30 32,18"/>')
    svg.append('    </g>')
    svg.append(f'    <text x="815" y="{note_y + 47}" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36" text-anchor="middle">no always resume on purpose, only a healthy node returns to service</text>')
    svg.append('  </g>')
    svg.append('')
    
    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = build_perfect_svg()
with open("candidate_test.svg", "w") as f:
    f.write(svg_str)
print("Updated candidate_test.svg successfully!")
