import re
import sys

def build_svg():
    # Colors
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    light_green = "#e8f1ea"
    orange = "#db8129"
    white = "#ffffff"
    
    # SVG Dimensions
    width = 1600
    height = 1200
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append('  <title>Read the vmstat columns to classify the bottleneck</title>')
    svg.append('  <desc>A decision tree for diagnosing system bottlenecks by reading vmstat columns across multiple lines.</desc>')
    svg.append(f'  <rect width="{width}" height="{height}" fill="{bg}" />')
    
    # Defs: marker for arrows
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    svg.append(f'      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{main_green}" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    svg.append(f'      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{orange}" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Title: 48px bold
    svg.append(f'  <text x="800" y="52" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">Read the vmstat columns to classify the bottleneck</text>')
    
    # Root Box (green panel):
    # 'Run vmstat 2 and start at line 2'
    # 'Line 1 is the average since boot'
    root_x = 60
    root_y = 78
    root_w = 1480
    root_h = 96
    svg.append(f'  <!-- Root Box -->')
    svg.append(f'  <rect x="{root_x}" y="{root_y}" width="{root_w}" height="{root_h}" rx="10" fill="{light_green}" stroke="{main_green}" stroke-width="3" />')
    
    # Root Icon: Terminal/Console outline icon (56px, green stroke 4)
    # Placed at (760, 95) or centered or beside text?
    # Let's put icon at (90, 98)
    svg.append(f'  <g transform="translate(85, 98)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="6" />')
    svg.append('    <polyline points="14,20 24,28 14,36" />')
    svg.append('    <line x1="28" y1="36" x2="42" y2="36" />')
    svg.append('  </g>')
    
    svg.append(f'  <text x="160" y="118" font-family="sans-serif" font-size="30" font-weight="bold" fill="{main_green}">Run vmstat 2 and start at line 2</text>')
    svg.append(f'  <text x="160" y="152" font-family="sans-serif" font-size="24" fill="{text_color}">Line 1 is the average since boot</text>')
    
    # Helpers for branch boxes
    def draw_box(x, y, w, h, fill_col, stroke_col, stroke_w=2):
        return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill_col}" stroke="{stroke_col}" stroke-width="{stroke_w}" />'

    # Icons helper
    # Icon 1 (Healthy): Shield with check
    icon_healthy = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 C 48 34 38 46 28 50 C 18 46 8 34 8 14 Z" />
      <polyline points="18,28 25,35 38,20" />
    </g>
    '''
    
    # Icon 2 (CPU-bound compute): Processor Chip
    icon_chip = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="12" y="12" width="32" height="32" rx="4" />
      <line x1="20" y1="4" x2="20" y2="12" />
      <line x1="28" y1="4" x2="28" y2="12" />
      <line x1="36" y1="4" x2="36" y2="12" />
      <line x1="20" y1="44" x2="20" y2="52" />
      <line x1="28" y1="44" x2="28" y2="52" />
      <line x1="36" y1="44" x2="36" y2="52" />
      <line x1="4" y1="20" x2="12" y2="20" />
      <line x1="4" y1="28" x2="12" y2="28" />
      <line x1="4" y1="36" x2="12" y2="36" />
      <line x1="44" y1="20" x2="52" y2="20" />
      <line x1="44" y1="28" x2="52" y2="28" />
      <line x1="44" y1="36" x2="52" y2="36" />
    </g>
    '''
    
    # Icon 3 (I/O-bound): Disk cylinder
    icon_disk = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="8" />
      <path d="M 8 14 L 8 42 C 8 46 17 50 28 50 C 39 50 48 46 48 42 L 48 14" />
      <path d="M 8 28 C 8 32 17 36 28 36 C 39 36 48 32 48 28" />
    </g>
    '''
    
    # Icon 4 (Memory exhausted): Memory / RAM module
    icon_ram = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="14" width="44" height="28" rx="3" />
      <line x1="12" y1="22" x2="16" y2="22" />
      <line x1="22" y1="22" x2="26" y2="22" />
      <line x1="32" y1="22" x2="36" y2="22" />
      <line x1="10" y1="42" x2="10" y2="48" />
      <line x1="16" y1="42" x2="16" y2="48" />
      <line x1="22" y1="42" x2="22" y2="48" />
      <line x1="28" y1="42" x2="28" y2="48" />
      <line x1="34" y1="42" x2="34" y2="48" />
      <line x1="40" y1="42" x2="40" y2="48" />
    </g>
    '''
    
    # Icon 5 (CPU contention): Chip with multiple competing queue threads
    icon_contention = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="16" width="24" height="24" rx="4" />
      <path d="M 40 12 L 48 12 L 48 20" />
      <line x1="36" y1="24" x2="48" y2="12" />
      <path d="M 40 44 L 48 44 L 48 36" />
      <line x1="36" y1="32" x2="48" y2="44" />
    </g>
    '''
    
    # Icon 6 (Lock contention / system calls): Lock
    icon_lock = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="22" width="36" height="26" rx="4" />
      <path d="M 18 22 L 18 14 C 18 8 38 8 38 14 L 38 22" />
      <circle cx="28" cy="34" r="3" fill="{stroke}" />
    </g>
    '''
    
    # Icon 7 (Noisy neighbours on shared VM): Multiple overlapping VM frames / windows
    icon_vm = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="32" height="26" rx="3" />
      <rect x="18" y="20" width="32" height="26" rx="3" />
      <line x1="18" y1="28" x2="50" y2="28" />
      <line x1="6" y1="16" x2="38" y2="16" />
    </g>
    '''

    # Layout Column 1
    # Box 1: Healthy (green box)
    b1_x, b1_y, b1_w, b1_h = 220, 265, 540, 100
    svg.append(f'  <!-- Branch 1 -->')
    # Arrow 1: straight down from root at x=280
    svg.append(f'  <path d="M 280 174 L 280 265" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    # Condition 1 label beside arrow (wrapped onto 2 lines)
    svg.append(f'  <text x="310" y="210" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append(f'    <tspan x="310" dy="0">All idle: id about 99,</tspan>')
    svg.append(f'    <tspan x="310" dy="28">si and so at 0</tspan>')
    svg.append(f'  </text>')
    # Box 1: green box 'Healthy'
    svg.append(f'  <rect x="{b1_x}" y="{b1_y}" width="{b1_w}" height="{b1_h}" rx="8" fill="{light_green}" stroke="{main_green}" stroke-width="3" />')
    svg.append(icon_healthy.format(x=b1_x + 20, y=b1_y + 22, stroke=main_green))
    svg.append(f'  <text x="{b1_x + 95}" y="{b1_y + 60}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{main_green}">Healthy</text>')

    # Box 2: CPU-bound compute
    b2_x, b2_y, b2_w, b2_h = 220, 480, 540, 100
    svg.append(f'  <!-- Branch 2 -->')
    # Arrow 2: down at x=160, turns right to 280, then down to 480
    svg.append(f'  <path d="M 160 174 L 160 425 L 280 425 L 280 480" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    # Condition 2 label beside arrow
    svg.append(f'  <text x="310" y="445" font-family="sans-serif" font-size="24" fill="{text_color}">High us, low wa</text>')
    # Box 2
    svg.append(f'  <rect x="{b2_x}" y="{b2_y}" width="{b2_w}" height="{b2_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_chip.format(x=b2_x + 20, y=b2_y + 22, stroke=main_green))
    svg.append(f'  <text x="{b2_x + 95}" y="{b2_y + 60}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">CPU-bound compute</text>')

    # Box 3: I/O-bound work: look at iostat
    b3_x, b3_y, b3_w, b3_h = 220, 695, 540, 125
    svg.append(f'  <!-- Branch 3 -->')
    # Arrow 3: down at x=115, turns right to 280, then down to 695
    svg.append(f'  <path d="M 115 174 L 115 640 L 280 640 L 280 695" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    # Condition 3 label beside arrow
    svg.append(f'  <text x="310" y="660" font-family="sans-serif" font-size="24" fill="{text_color}">High wa and b</text>')
    # Box 3
    svg.append(f'  <rect x="{b3_x}" y="{b3_y}" width="{b3_w}" height="{b3_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_disk.format(x=b3_x + 20, y=b3_y + 35, stroke=main_green))
    svg.append(f'  <text x="{b3_x + 95}" y="{b3_y + 55}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b3_x + 95}" dy="0">I/O-bound work: </tspan>')
    svg.append(f'    <tspan x="{b3_x + 95}" dy="36">look at iostat</tspan>')
    svg.append(f'  </text>')

    # Box 4: Memory exhausted: kernel is paging out (orange outline)
    b4_x, b4_y, b4_w, b4_h = 220, 935, 540, 135
    svg.append(f'  <!-- Branch 4 -->')
    # Arrow 4: down at x=70, turns right to 280, then down to 935
    svg.append(f'  <path d="M 70 174 L 70 880 L 280 880 L 280 935" stroke="{orange}" stroke-width="3" fill="none" marker-end="url(#arrow-orange)" />')
    # Condition 4 label beside arrow
    svg.append(f'  <text x="310" y="878" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append(f'    <tspan x="310" dy="0">Growing so, </tspan>')
    svg.append(f'    <tspan x="310" dy="28">falling free or cache</tspan>')
    svg.append(f'  </text>')
    # Box 4: orange outline!
    svg.append(f'  <rect x="{b4_x}" y="{b4_y}" width="{b4_w}" height="{b4_h}" rx="8" fill="{white}" stroke="{orange}" stroke-width="3" />')
    svg.append(icon_ram.format(x=b4_x + 20, y=b4_y + 40, stroke=orange))
    svg.append(f'  <text x="{b4_x + 95}" y="{b4_y + 58}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b4_x + 95}" dy="0">Memory exhausted: </tspan>')
    svg.append(f'    <tspan x="{b4_x + 95}" dy="36">kernel is paging out</tspan>')
    svg.append(f'  </text>')

    # Layout Column 2
    # Box 5: CPU contention
    b5_x, b5_y, b5_w, b5_h = 840, 285, 540, 110
    svg.append(f'  <!-- Branch 5 -->')
    # Arrow 5: straight down from root at x=900
    svg.append(f'  <path d="M 900 174 L 900 285" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    # Condition 5 label beside arrow
    svg.append(f'  <text x="930" y="220" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append(f'    <tspan x="930" dy="0">High r with </tspan>')
    svg.append(f'    <tspan x="930" dy="28">high us plus sy</tspan>')
    svg.append(f'  </text>')
    # Box 5
    svg.append(f'  <rect x="{b5_x}" y="{b5_y}" width="{b5_w}" height="{b5_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_contention.format(x=b5_x + 20, y=b5_y + 27, stroke=main_green))
    svg.append(f'  <text x="{b5_x + 95}" y="{b5_y + 65}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">CPU contention</text>')

    # Box 6: Many system calls or lock contention
    b6_x, b6_y, b6_w, b6_h = 840, 565, 540, 135
    svg.append(f'  <!-- Branch 6 -->')
    # Arrow 6: down at x=1435, turns left to 900, then down to 565
    svg.append(f'  <path d="M 1435 174 L 1435 505 L 900 505 L 900 565" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    # Condition 6 label beside arrow
    svg.append(f'  <text x="930" y="525" font-family="sans-serif" font-size="24" fill="{text_color}">High sy and cs</text>')
    # Box 6
    svg.append(f'  <rect x="{b6_x}" y="{b6_y}" width="{b6_w}" height="{b6_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_lock.format(x=b6_x + 20, y=b6_y + 40, stroke=main_green))
    svg.append(f'  <text x="{b6_x + 95}" y="{b6_y + 58}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b6_x + 95}" dy="0">Many system calls </tspan>')
    svg.append(f'    <tspan x="{b6_x + 95}" dy="36">or lock contention</tspan>')
    svg.append(f'  </text>')

    # Box 7: Noisy neighbours on a shared VM
    b7_x, b7_y, b7_w, b7_h = 840, 870, 540, 135
    svg.append(f'  <!-- Branch 7 -->')
    # Arrow 7: down at x=1490, turns left to 900, then down to 870
    svg.append(f'  <path d="M 1490 174 L 1490 810 L 900 810 L 900 870" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    # Condition 7 label beside arrow
    svg.append(f'  <text x="930" y="830" font-family="sans-serif" font-size="24" fill="{text_color}">High st</text>')
    # Box 7
    svg.append(f'  <rect x="{b7_x}" y="{b7_y}" width="{b7_w}" height="{b7_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_vm.format(x=b7_x + 20, y=b7_y + 40, stroke=main_green))
    svg.append(f'  <text x="{b7_x + 95}" y="{b7_y + 58}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b7_x + 95}" dy="0">Noisy neighbours </tspan>')
    svg.append(f'    <tspan x="{b7_x + 95}" dy="36">on a shared VM</tspan>')
    svg.append(f'  </text>')

    # Takeaway Bar at Bottom
    # 'Read the trend across several lines, not one number.'
    tb_x, tb_y, tb_w, tb_h = 60, 1115, 1480, 55
    svg.append(f'  <!-- Takeaway Bar -->')
    svg.append(f'  <rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" rx="8" fill="{main_green}" />')
    svg.append(f'  <text x="800" y="1152" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="{white}">Read the trend across several lines, not one number.</text>')

    svg.append('</svg>')
    return '\n'.join(svg)

content = build_svg()
with open("test_candidate.svg", "w") as f:
    f.write(content)

print("test_candidate.svg written successfully!")
