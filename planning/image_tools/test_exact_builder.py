import re
import xml.etree.ElementTree as ET

def generate_svg():
    W = 1600
    H = 1060
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>awk group-by: an associative array counts as the lines pass</title>')
    svg.append('  <desc>Technical infographic illustrating how awk uses an associative array to count occurrences per key as lines pass, compared with uniq -c pipelines.</desc>')
    svg.append('  <defs>')
    # Marker for green arrows (18px)
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Background
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')
    
    # Main Title (48px bold)
    svg.append('  <text x="800" y="72" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">awk group-by: an associative array counts as the lines pass</text>')
    
    # ==================== MAIN PIPELINE ROW (y = 120 to 650) ====================
    
    # 1. LEFT PANEL: Small input table (x = 40, y = 120, width = 270, height = 520)
    svg.append('  <g id="left-input-table">')
    svg.append('    <rect x="40" y="120" width="270" height="520" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Table Icon (56px) at (x=60, y=138)
    svg.append('    <g transform="translate(60, 138)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="4" width="48" height="48" rx="6" />')
    svg.append('      <line x1="4" y1="20" x2="52" y2="20" />')
    svg.append('      <line x1="28" y1="20" x2="28" y2="52" />')
    svg.append('      <line x1="4" y1="36" x2="52" y2="36" stroke-width="2" />')
    svg.append('    </g>')
    # Table Header Box (column 1, column 2)
    svg.append('    <rect x="58" y="215" width="234" height="54" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="116" y="251" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">column 1</text>')
    svg.append('    <text x="232" y="251" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">column 2</text>')
    svg.append('    <line x1="175" y1="215" x2="175" y2="269" stroke="#207448" stroke-width="2" />')
    
    # Table Rows (5 lines)
    names = ["alice", "bob", "alice", "alice", "bob"]
    row_y_start = 285
    row_h = 65
    for i, name in enumerate(names):
        ry = row_y_start + i * row_h
        svg.append(f'    <rect x="58" y="{ry}" width="234" height="54" rx="8" fill="#f5f8f5" stroke="#207448" stroke-width="1.5" />')
        svg.append(f'    <line x1="175" y1="{ry}" x2="175" y2="{ry + 54}" stroke="#207448" stroke-width="1.5" stroke-dasharray="4,4" />')
        svg.append(f'    <text x="116" y="{ry + 36}" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">{name}</text>')
    svg.append('  </g>')
    
    # Arrow 1: Left Input Table -> Middle awk box
    svg.append('  <path d="M 310 380 L 350 380" stroke="#207448" stroke-width="4" fill="none" marker-end="url(#arrow-green)" />')
    
    # 2. MIDDLE PANEL: awk { c[$1]++ } with lookup table 'c' and 3 snapshots
    # x = 350, y = 120, width = 610, height = 520
    svg.append('  <g id="middle-awk-box">')
    svg.append('    <rect x="350" y="120" width="610" height="520" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Terminal / Code Icon (56px) at (x=372, y=138)
    svg.append('    <g transform="translate(372, 138)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="44" rx="6" />')
    svg.append('      <polyline points="14,22 24,30 14,38" />')
    svg.append('      <line x1="28" y1="38" x2="42" y2="38" stroke-width="3" />')
    svg.append('    </g>')
    # Title: awk { c[$1]++ } (32px bold monospace)
    svg.append('    <text x="445" y="176" font-family="monospace" font-size="32" font-weight="bold" fill="#207448">awk { c[$1]++ }</text>')
    
    # Lookup table 'c' header bar
    svg.append('    <rect x="372" y="215" width="566" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="655" y="249" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">lookup table c</text>')
    
    # Snapshots 1 to 3
    snap_configs = [
        (1, "after line 1", "alice = 1", 280),
        (2, "after line 3", "alice = 2, bob = 1", 390),
        (3, "after line 5", "alice = 3, bob = 2", 500),
    ]
    
    for num, step_lbl, val_lbl, sy in snap_configs:
        svg.append(f'    <rect x="372" y="{sy}" width="566" height="95" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2" />')
        # Number circle (r=24, green, white number) at (x=406, y=sy+47)
        svg.append(f'    <circle cx="406" cy="{sy + 47}" r="24" fill="#207448" />')
        svg.append(f'    <text x="406" y="{sy + 56}" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">{num}</text>')
        # Step label: e.g. "after line 1" (30px bold)
        svg.append(f'    <text x="448" y="{sy + 40}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">{step_lbl}</text>')
        # Value label: e.g. "alice = 1" (26px monospace)
        svg.append(f'    <rect x="448" y="{sy + 50}" width="474" height="36" rx="6" fill="#e8f1ea" />')
        svg.append(f'    <text x="462" y="{sy + 76}" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">{val_lbl}</text>')
    svg.append('  </g>')
    
    # Arrow 2: Middle awk box -> Right END box
    svg.append('  <path d="M 960 245 L 1000 245" stroke="#207448" stroke-width="4" fill="none" marker-end="url(#arrow-green)" />')
    
    # 3. RIGHT PANEL: END box (orange highlight) and | sort -rn box
    # x = 1000, y = 120, width = 560
    
    # Top box: END { for (k in c) print c[k], k } (Orange highlight on END box only!)
    svg.append('  <g id="right-end-box">')
    # Orange bordered container with warm background tint
    svg.append('    <rect x="1000" y="120" width="560" height="250" rx="14" fill="#fff5ea" stroke="#db8129" stroke-width="3.5" />')
    # Icon with orange stroke (56px) at (x=1022, y=138)
    svg.append('    <g transform="translate(1022, 138)" stroke="#db8129" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="48" height="44" rx="6" />')
    svg.append('      <circle cx="28" cy="28" r="10" />')
    svg.append('      <line x1="28" y1="12" x2="28" y2="18" />')
    svg.append('      <line x1="28" y1="38" x2="28" y2="44" />')
    svg.append('      <line x1="12" y1="28" x2="18" y2="28" />')
    svg.append('      <line x1="38" y1="28" x2="44" y2="28" />')
    svg.append('    </g>')
    # Title: END { for (k in c) print c[k], k } (24px bold monospace)
    svg.append('    <text x="1095" y="174" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">END { for (k in c) print c[k], k }</text>')
    # Sub-label: runs once after the last line
    svg.append('    <text x="1280" y="235" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">runs once after the last line</text>')
    # Output box: 3 alice, 2 bob
    svg.append('    <rect x="1022" y="255" width="516" height="95" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="2" />')
    svg.append('    <text x="1050" y="310" font-family="sans-serif" font-size="24" font-weight="bold" fill="#db8129">output</text>')
    svg.append('    <text x="1280" y="290" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">3 alice</text>')
    svg.append('    <text x="1280" y="330" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">2 bob</text>')
    svg.append('  </g>')
    
    # Arrow 3: END box -> | sort -rn box
    svg.append('  <path d="M 1280 370 L 1280 410" stroke="#207448" stroke-width="4" fill="none" marker-end="url(#arrow-green)" />')
    
    # Bottom box: | sort -rn giving the ranked output
    # x = 1000, y = 410, width = 560, height = 230
    svg.append('  <g id="right-sort-box">')
    svg.append('    <rect x="1000" y="410" width="560" height="230" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Sort Icon (56px) at (x=1022, y=428)
    svg.append('    <g transform="translate(1022, 428)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <line x1="10" y1="12" x2="42" y2="12" stroke-width="5" />')
    svg.append('      <line x1="10" y1="24" x2="34" y2="24" stroke-width="5" />')
    svg.append('      <line x1="10" y1="36" x2="26" y2="36" stroke-width="5" />')
    svg.append('      <line x1="10" y1="48" x2="18" y2="48" stroke-width="5" />')
    svg.append('    </g>')
    # Title: | sort -rn (30px bold monospace)
    svg.append('    <text x="1095" y="466" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">| sort -rn</text>')
    # Subtitle: ranked output
    svg.append('    <text x="1280" y="505" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">ranked output</text>')
    # Output box
    svg.append('    <rect x="1022" y="525" width="516" height="95" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1280" y="562" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">3 alice</text>')
    svg.append('    <text x="1280" y="602" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#207448">2 bob</text>')
    svg.append('  </g>')
    
    # ==================== SECOND PANEL: Comparison (y = 665 to 925) ====================
    # x = 40, y = 665, width = 1520, height = 260
    svg.append('  <g id="second-panel-comparison">')
    svg.append('    <rect x="40" y="665" width="1520" height="260" rx="14" fill="#ffffff" stroke="#207448" stroke-width="3" />')
    # Icon for comparison (56px) at (x=65, y=685)
    svg.append('    <g transform="translate(65, 685)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="28" cy="28" r="22" />')
    svg.append('      <line x1="28" y1="12" x2="28" y2="44" />')
    svg.append('      <line x1="16" y1="20" x2="40" y2="20" />')
    svg.append('      <line x1="16" y1="36" x2="40" y2="36" />')
    svg.append('    </g>')
    
    # Column A: uniq -c without sort (x = 145, y = 685, width = 675)
    svg.append('    <rect x="145" y="685" width="675" height="220" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="482" y="725" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#303a36">uniq -c without sort</text>')
    # 4 outputs in a horizontal row
    outputs_a = ["1 alice", "1 bob", "2 alice", "1 bob"]
    for i, out_txt in enumerate(outputs_a):
        ox = 168 + i * 155
        svg.append(f'    <rect x="{ox}" y="755" width="140" height="130" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
        svg.append(f'    <text x="{ox + 70}" y="830" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">{out_txt}</text>')
        
    # Column B: sort | uniq -c (x = 845, y = 685, width = 695)
    svg.append('    <rect x="845" y="685" width="695" height="220" rx="10" fill="#f5f8f5" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1192" y="725" text-anchor="middle" font-family="monospace" font-size="28" font-weight="bold" fill="#207448">sort | uniq -c</text>')
    outputs_b = ["3 alice", "2 bob"]
    for i, out_txt in enumerate(outputs_b):
        ox = 915 + i * 290
        svg.append(f'    <rect x="{ox}" y="755" width="260" height="130" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
        svg.append(f'    <text x="{ox + 130}" y="830" text-anchor="middle" font-family="monospace" font-size="30" font-weight="bold" fill="#207448">{out_txt}</text>')
    svg.append('  </g>')
    
    # ==================== NOTE / TAKEAWAY BAR (y = 955 to 1025) ====================
    # x = 40, y = 955, width = 1520, height = 70
    svg.append('  <g id="bottom-takeaway-bar">')
    svg.append('    <rect x="40" y="955" width="1520" height="70" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    svg.append('    <text x="800" y="999" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">An associative array is a lookup table keyed by text, so no sort | uniq -c is needed</text>')
    svg.append('  </g>')
    
    svg.append('</svg>')
    return '\n'.join(svg)

with open("test_output.svg", "w") as f:
    f.write(generate_svg())

print("Updated test_output.svg generated.")
