import re
import xml.etree.ElementTree as ET

def generate_svg():
    bg = "#f5f8f5"
    text_color = "#303a36"
    main_green = "#207448"
    light_green = "#e8f1ea"
    orange = "#db8129"
    white = "#ffffff"
    
    width = 1600
    height = 1200
    
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">')
    svg.append('  <title>Read the vmstat columns to classify the bottleneck</title>')
    svg.append('  <desc>A decision tree for diagnosing system bottlenecks by reading vmstat columns across multiple lines.</desc>')
    svg.append(f'  <rect width="{width}" height="{height}" fill="{bg}" />')
    
    svg.append('  <defs>')
    svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    svg.append(f'      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{main_green}" />')
    svg.append('    </marker>')
    svg.append('    <marker id="arrow-orange" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">')
    svg.append(f'      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="{orange}" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Title: 48px bold
    svg.append(f'  <text x="800" y="78" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">Read the vmstat columns to classify the bottleneck</text>')
    
    # Root Box (green panel)
    root_x, root_y, root_w, root_h = 60, 125, 1480, 96
    svg.append(f'  <!-- Root Box -->')
    svg.append(f'  <rect x="{root_x}" y="{root_y}" width="{root_w}" height="{root_h}" rx="10" fill="{light_green}" stroke="{main_green}" stroke-width="3" />')
    
    # Root Icon (Console / Terminal)
    svg.append(f'  <g transform="translate(85, 145)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="0" y="0" width="56" height="56" rx="6" />')
    svg.append('    <polyline points="14,20 24,28 14,36" />')
    svg.append('    <line x1="28" y1="36" x2="42" y2="36" />')
    svg.append('  </g>')
    
    # Root Text
    svg.append(f'  <text x="165" y="166" font-family="sans-serif" font-size="30" font-weight="bold" fill="{main_green}">Run vmstat 2 and start at line 2</text>')
    svg.append(f'  <text x="165" y="200" font-family="sans-serif" font-size="24" fill="{text_color}">Line 1 is the average since boot</text>')
    
    # Icons
    icon_healthy = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 28 6 L 48 14 C 48 34 38 46 28 50 C 18 46 8 34 8 14 Z" />
      <polyline points="18,28 25,35 38,20" />
    </g>'''
    
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
    </g>'''
    
    icon_disk = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <ellipse cx="28" cy="14" rx="20" ry="8" />
      <path d="M 8 14 L 8 42 C 8 46 17 50 28 50 C 39 50 48 46 48 42 L 48 14" />
      <path d="M 8 28 C 8 32 17 36 28 36 C 39 36 48 32 48 28" />
    </g>'''
    
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
    </g>'''
    
    icon_contention = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="16" width="24" height="24" rx="4" />
      <path d="M 40 12 L 48 12 L 48 20" />
      <line x1="36" y1="24" x2="48" y2="12" />
      <path d="M 40 44 L 48 44 L 48 36" />
      <line x1="36" y1="32" x2="48" y2="44" />
    </g>'''
    
    icon_lock = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="22" width="36" height="26" rx="4" />
      <path d="M 18 22 L 18 14 C 18 8 38 8 38 14 L 38 22" />
      <circle cx="28" cy="34" r="3" fill="{stroke}" />
    </g>'''
    
    icon_vm = '''
    <g transform="translate({x}, {y})" stroke="{stroke}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="6" y="8" width="32" height="26" rx="3" />
      <rect x="18" y="20" width="32" height="26" rx="3" />
      <line x1="18" y1="28" x2="50" y2="28" />
      <line x1="6" y1="16" x2="38" y2="16" />
    </g>'''

    # Branch 1
    svg.append('  <!-- Branch 1 -->')
    svg.append(f'  <path d="M 280 221 L 280 305" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    svg.append(f'  <text x="310" y="255" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append(f'    <tspan x="310" dy="0">All idle: id about 99,</tspan>')
    svg.append(f'    <tspan x="310" dy="28">si and so at 0</tspan>')
    svg.append(f'  </text>')
    b1_x, b1_y, b1_w, b1_h = 220, 305, 540, 80
    svg.append(f'  <rect x="{b1_x}" y="{b1_y}" width="{b1_w}" height="{b1_h}" rx="8" fill="{light_green}" stroke="{main_green}" stroke-width="3" />')
    svg.append(icon_healthy.format(x=b1_x + 20, y=b1_y + 12, stroke=main_green))
    svg.append(f'  <text x="{b1_x + 95}" y="{b1_y + 50}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{main_green}">Healthy</text>')

    # Branch 2
    svg.append('  <!-- Branch 2 -->')
    svg.append(f'  <path d="M 160 221 L 160 425 L 280 425 L 280 475" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    svg.append(f'  <text x="310" y="445" font-family="sans-serif" font-size="24" fill="{text_color}">High us, low wa</text>')
    b2_x, b2_y, b2_w, b2_h = 220, 475, 540, 80
    svg.append(f'  <rect x="{b2_x}" y="{b2_y}" width="{b2_w}" height="{b2_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_chip.format(x=b2_x + 20, y=b2_y + 12, stroke=main_green))
    svg.append(f'  <text x="{b2_x + 95}" y="{b2_y + 50}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">CPU-bound compute</text>')

    # Branch 3
    svg.append('  <!-- Branch 3 -->')
    svg.append(f'  <path d="M 115 221 L 115 595 L 280 595 L 280 650" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    svg.append(f'  <text x="310" y="615" font-family="sans-serif" font-size="24" fill="{text_color}">High wa and b</text>')
    b3_x, b3_y, b3_w, b3_h = 220, 650, 540, 115
    svg.append(f'  <rect x="{b3_x}" y="{b3_y}" width="{b3_w}" height="{b3_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_disk.format(x=b3_x + 20, y=b3_y + 30, stroke=main_green))
    svg.append(f'  <text x="{b3_x + 95}" y="{b3_y + 50}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b3_x + 95}" dy="0">I/O-bound work: </tspan>')
    svg.append(f'    <tspan x="{b3_x + 95}" dy="36">look at iostat</tspan>')
    svg.append(f'  </text>')

    # Branch 4 (Orange outline)
    svg.append('  <!-- Branch 4 -->')
    svg.append(f'  <path d="M 70 221 L 70 810 L 280 810 L 280 865" stroke="{orange}" stroke-width="3" fill="none" marker-end="url(#arrow-orange)" />')
    svg.append(f'  <text x="310" y="810" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append(f'    <tspan x="310" dy="0">Growing so, </tspan>')
    svg.append(f'    <tspan x="310" dy="28">falling free or cache</tspan>')
    svg.append(f'  </text>')
    b4_x, b4_y, b4_w, b4_h = 220, 865, 540, 120
    svg.append(f'  <rect x="{b4_x}" y="{b4_y}" width="{b4_w}" height="{b4_h}" rx="8" fill="{white}" stroke="{orange}" stroke-width="3" />')
    svg.append(icon_ram.format(x=b4_x + 20, y=b4_y + 32, stroke=orange))
    svg.append(f'  <text x="{b4_x + 95}" y="{b4_y + 52}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b4_x + 95}" dy="0">Memory exhausted: </tspan>')
    svg.append(f'    <tspan x="{b4_x + 95}" dy="36">kernel is paging out</tspan>')
    svg.append(f'  </text>')

    # Branch 5
    svg.append('  <!-- Branch 5 -->')
    svg.append(f'  <path d="M 900 221 L 900 320" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    svg.append(f'  <text x="930" y="265" font-family="sans-serif" font-size="24" fill="{text_color}">')
    svg.append(f'    <tspan x="930" dy="0">High r with </tspan>')
    svg.append(f'    <tspan x="930" dy="28">high us plus sy</tspan>')
    svg.append(f'  </text>')
    b5_x, b5_y, b5_w, b5_h = 840, 320, 540, 80
    svg.append(f'  <rect x="{b5_x}" y="{b5_y}" width="{b5_w}" height="{b5_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_contention.format(x=b5_x + 20, y=b5_y + 12, stroke=main_green))
    svg.append(f'  <text x="{b5_x + 95}" y="{b5_y + 50}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">CPU contention</text>')

    # Branch 6
    svg.append('  <!-- Branch 6 -->')
    svg.append(f'  <path d="M 1435 221 L 1435 475 L 900 475 L 900 535" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    svg.append(f'  <text x="930" y="495" font-family="sans-serif" font-size="24" fill="{text_color}">High sy and cs</text>')
    b6_x, b6_y, b6_w, b6_h = 840, 535, 540, 115
    svg.append(f'  <rect x="{b6_x}" y="{b6_y}" width="{b6_w}" height="{b6_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_lock.format(x=b6_x + 20, y=b6_y + 30, stroke=main_green))
    svg.append(f'  <text x="{b6_x + 95}" y="{b6_y + 50}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b6_x + 95}" dy="0">Many system calls </tspan>')
    svg.append(f'    <tspan x="{b6_x + 95}" dy="36">or lock contention</tspan>')
    svg.append(f'  </text>')

    # Branch 7
    svg.append('  <!-- Branch 7 -->')
    svg.append(f'  <path d="M 1490 221 L 1490 730 L 900 730 L 900 790" stroke="{main_green}" stroke-width="3" fill="none" marker-end="url(#arrow)" />')
    svg.append(f'  <text x="930" y="750" font-family="sans-serif" font-size="24" fill="{text_color}">High st</text>')
    b7_x, b7_y, b7_w, b7_h = 840, 790, 540, 120
    svg.append(f'  <rect x="{b7_x}" y="{b7_y}" width="{b7_w}" height="{b7_h}" rx="8" fill="{white}" stroke="{main_green}" stroke-width="2" />')
    svg.append(icon_vm.format(x=b7_x + 20, y=b7_y + 32, stroke=main_green))
    svg.append(f'  <text x="{b7_x + 95}" y="{b7_y + 52}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    svg.append(f'    <tspan x="{b7_x + 95}" dy="0">Noisy neighbours </tspan>')
    svg.append(f'    <tspan x="{b7_x + 95}" dy="36">on a shared VM</tspan>')
    svg.append(f'  </text>')

    # Takeaway Bar at bottom
    tb_x, tb_y, tb_w, tb_h = 60, 1095, 1480, 65
    svg.append('  <!-- Takeaway Bar -->')
    svg.append(f'  <rect x="{tb_x}" y="{tb_y}" width="{tb_w}" height="{tb_h}" rx="8" fill="{main_green}" />')
    svg.append(f'  <text x="800" y="1136" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="{white}">Read the trend across several lines, not one number.</text>')

    svg.append('</svg>')
    return '\n'.join(svg)

content = generate_svg()
with open("vmstat_decision_tree.svg", "w") as f:
    f.write(content)
print("vmstat_decision_tree.svg written.")
