import xml.etree.ElementTree as ET
import re

H = 1040
svg = []
svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
svg.append('  <title>The latency ladder with ratios to a memory read</title>')
svg.append('  <desc>Visual infographic of the latency ladder showing operations from L1 cache to intercontinental network round trip, with times and ratios to a main memory read.</desc>')

# Defs
svg.append('  <defs>')
svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
svg.append('    </marker>')
svg.append('  </defs>')

# Background
svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')

# Title: 48px bold
svg.append('  <text x="800" y="70" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The latency ladder with ratios to a memory read</text>')

# Left side vertical arrow: line at x=45 from y=135 to y=940
svg.append('  <line x1="45" y1="135" x2="45" y2="940" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

# Arrow label: 'Each rung down costs more'
svg.append('  <text x="70" y="525" font-family="sans-serif" font-size="26" font-weight="bold" fill="#207448">')
svg.append('    <tspan x="70" dy="0">Each rung down </tspan>')
svg.append('    <tspan x="70" dy="34">costs more</tspan>')
svg.append('  </text>')

# Side note card: x=1080, y=135, w=480, h=125, rx=14
svg.append('  <rect x="1080" y="135" width="480" height="125" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
# Note text: 'Figures from the 2009 slide: use the order of magnitude and say the year.'
svg.append('  <text x="1320" y="174" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
svg.append('    <tspan x="1320" dy="0">Figures from the 2009 slide: </tspan>')
svg.append('    <tspan x="1320" dy="29">use the order of magnitude </tspan>')
svg.append('    <tspan x="1320" dy="29">and say the year.</tspan>')
svg.append('  </text>')

# Rungs data: (idx, y, width, is_orange, is_base, label, value, right_start_x)
rungs = [
    (1, 135, 710, False, False, "L1 cache reference: ", "0.5 ns, ratio 0.005", 726),
    (2, 300, 790, False, True,  "Main memory reference: ", "100 ns, ratio 1", 768),
    (3, 435, 930, False, False, "Send 2K bytes over 1 Gbps network: ", "20,000 ns, ratio 200", 936),
    (4, 570, 1040, True, False, "Round trip within same datacenter: ", "500,000 ns, ratio 5,000", 952),
    (5, 705, 1140, False, False, "Disk seek: ", "10,000,000 ns, ratio 100,000", 952),
    (6, 840, 1240, False, False, "Send packet CA to Netherlands and back: ", "150,000,000 ns, ratio 1,500,000", 1024),
]

rx = 320
text_start_x = rx + 90

for idx, ry, rw, is_orange, is_base, l_text, r_text, r_start in rungs:
    stroke_color = "#db8129" if is_orange else "#207448"
    stroke_w = "4" if is_orange else "2.5"
    
    # Rung bar
    svg.append(f'  <rect x="{rx}" y="{ry}" width="{rw}" height="90" rx="14" fill="#e8f1ea" stroke="{stroke_color}" stroke-width="{stroke_w}" />')
    
    # If Main memory rung (idx == 2), add green marker as the ratio base
    if is_base:
        # Green accent notch on left edge
        svg.append(f'  <path d="M {rx} {ry+14} A 14 14 0 0 1 {rx+14} {ry} L {rx+22} {ry} L {rx+22} {ry+90} L {rx+14} {ry+90} A 14 14 0 0 1 {rx} {ry+76} Z" fill="#207448" />')
        # Green marker badge on right side
        badge_x = rx + rw - 70
        svg.append(f'  <g transform="translate({badge_x}, {ry+18})">')
        svg.append('    <rect x="0" y="0" width="54" height="54" rx="10" fill="#207448" />')
        svg.append('    <circle cx="27" cy="27" r="14" fill="none" stroke="#ffffff" stroke-width="3.5" />')
        svg.append('    <circle cx="27" cy="27" r="5" fill="#ffffff" />')
        svg.append('  </g>')
    
    # Icon (centered vertically: y = ry + 17)
    icon_x = rx + 16
    icon_y = ry + 17
    svg.append(f'  <g transform="translate({icon_x}, {icon_y})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    if idx == 1:
        # CPU chip
        svg.append('    <rect x="10" y="10" width="36" height="36" rx="4" />')
        svg.append('    <line x1="18" y1="3" x2="18" y2="10" /><line x1="28" y1="3" x2="28" y2="10" /><line x1="38" y1="3" x2="38" y2="10" />')
        svg.append('    <line x1="18" y1="46" x2="18" y2="53" /><line x1="28" y1="46" x2="28" y2="53" /><line x1="38" y1="46" x2="38" y2="53" />')
        svg.append('    <line x1="3" y1="18" x2="10" y2="18" /><line x1="3" y1="28" x2="10" y2="28" /><line x1="3" y1="38" x2="10" y2="38" />')
        svg.append('    <line x1="46" y1="18" x2="53" y2="18" /><line x1="46" y1="28" x2="53" y2="28" /><line x1="46" y1="38" x2="53" y2="38" />')
        svg.append('    <rect x="20" y="20" width="16" height="16" rx="2" fill="#207448" />')
    elif idx == 2:
        # RAM module
        svg.append('    <rect x="6" y="14" width="44" height="28" rx="3" />')
        svg.append('    <rect x="12" y="20" width="8" height="10" rx="1" fill="#207448" />')
        svg.append('    <rect x="24" y="20" width="8" height="10" rx="1" fill="#207448" />')
        svg.append('    <rect x="36" y="20" width="8" height="10" rx="1" fill="#207448" />')
        svg.append('    <line x1="10" y1="42" x2="10" y2="47" /><line x1="16" y1="42" x2="16" y2="47" /><line x1="22" y1="42" x2="22" y2="47" />')
        svg.append('    <line x1="28" y1="42" x2="28" y2="47" /><line x1="34" y1="42" x2="34" y2="47" /><line x1="40" y1="42" x2="40" y2="47" /><line x1="46" y1="42" x2="46" y2="47" />')
    elif idx == 3:
        # Network NIC / LAN node
        svg.append('    <circle cx="28" cy="18" r="10" />')
        svg.append('    <rect x="8" y="38" width="14" height="12" rx="2" />')
        svg.append('    <rect x="34" y="38" width="14" height="12" rx="2" />')
        svg.append('    <line x1="28" y1="28" x2="28" y2="34" />')
        svg.append('    <line x1="15" y1="34" x2="41" y2="34" />')
        svg.append('    <line x1="15" y1="34" x2="15" y2="38" /><line x1="41" y1="34" x2="41" y2="38" />')
    elif idx == 4:
        # Datacenter chassis
        svg.append('    <rect x="8" y="6" width="40" height="44" rx="4" />')
        svg.append('    <line x1="8" y1="18" x2="48" y2="18" /><line x1="8" y1="30" x2="48" y2="30" /><line x1="8" y1="42" x2="48" y2="42" />')
        svg.append('    <circle cx="15" cy="12" r="2" fill="#207448" /><circle cx="15" cy="24" r="2" fill="#207448" /><circle cx="15" cy="36" r="2" fill="#207448" />')
    elif idx == 5:
        # Disk cylinder
        svg.append('    <ellipse cx="28" cy="14" rx="20" ry="8" />')
        svg.append('    <path d="M 8 14 L 8 42 A 20 8 0 0 0 48 42 L 48 14" />')
        svg.append('    <path d="M 8 28 A 20 8 0 0 0 48 28" />')
    elif idx == 6:
        # Globe / intercontinental
        svg.append('    <circle cx="28" cy="28" r="22" />')
        svg.append('    <line x1="6" y1="28" x2="50" y2="28" />')
        svg.append('    <ellipse cx="28" cy="28" rx="11" ry="22" />')
        svg.append('    <line x1="28" y1="6" x2="28" y2="50" />')
    svg.append('  </g>')
    
    # Text
    ty = ry + 54
    svg.append(f'  <text x="{text_start_x}" y="{ty}" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append(f'    <tspan x="{text_start_x}" y="{ty}" font-weight="bold">{l_text}</tspan>')
    svg.append(f'    <tspan x="{r_start}" y="{ty}">{r_text}</tspan>')
    svg.append('  </text>')

svg.append('</svg>')
final_svg = '\n'.join(svg)

with open("test_ladder.svg", "w") as f:
    f.write(final_svg)
print("Updated test_ladder.svg with solved coordinates")
