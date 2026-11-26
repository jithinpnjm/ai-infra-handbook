#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def build_svg():
    # Canvas dimensions
    W = 1600
    H = 1050

    # Colors
    bg = "#f5f8f5"
    panel_bg = "#e8f1ea"
    card_bg = "#ffffff"
    text_color = "#303a36"
    main_green = "#207448"
    accent_green = "#1a5e3a"
    sub_green = "#3b8c63"
    orange = "#db8129"
    orange_bg = "#fffaf3"

    lines = []
    lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    
    # 1. First children MUST be <title> and <desc>
    lines.append('  <title>Sizing a 3-stage fabric</title>')
    lines.append('  <desc>Infographic explaining sizing formulas and worked example for a 3-stage Clos network fabric</desc>')

    # Background
    lines.append(f'  <rect x="0" y="0" width="{W}" height="{H}" fill="{bg}" />')

    # Top Title
    # Title 48 px bold, at most two lines, well inside canvas
    lines.append(f'  <text x="40" y="85" font-family="sans-serif" font-size="48" font-weight="bold" fill="{text_color}">Sizing a 3-stage fabric</text>')

    # Layout parameters
    # Margin = 40
    # Two main columns: Left (formulas) and Right (worked example)
    # y: 130 to 880 (height = 750)
    col_y = 130
    col_h = 750
    col_w = 740
    left_x = 40
    right_x = 820 # gap = 820 - (40+740) = 40

    # ==========================================
    # LEFT PANEL: formulas for R-port switches at 1:1
    # ==========================================
    lines.append(f'  <!-- Left Panel Container -->')
    lines.append(f'  <rect x="{left_x}" y="{col_y}" width="{col_w}" height="{col_h}" rx="16" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')

    # Left Header Icon (Network switch / fabric outline icon, 56 px, green stroke 4)
    # Placed at x = left_x + 30 = 70, y = col_y + 25 = 155
    lines.append(f'  <g transform="translate(70, 155)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="2" y="2" width="52" height="52" rx="8" />')
    lines.append('    <line x1="14" y1="16" x2="42" y2="16" />')
    lines.append('    <line x1="14" y1="28" x2="42" y2="28" />')
    lines.append('    <line x1="14" y1="40" x2="42" y2="40" />')
    lines.append('    <circle cx="20" cy="16" r="3" fill="#207448" />')
    lines.append('    <circle cx="36" cy="28" r="3" fill="#207448" />')
    lines.append('    <circle cx="24" cy="40" r="3" fill="#207448" />')
    lines.append('  </g>')

    # Left Panel Title: "formulas for R-port switches at 1:1"
    # Node title: at least 30 px bold
    lines.append(f'  <text x="145" y="193" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">formulas for R-port switches at 1:1</text>')

    # Small leaf-spine drawing container inside Left Panel
    # drawing card: x = 70, y = 240, w = 680, h = 260
    draw_x = 70
    draw_y = 240
    draw_w = 680
    draw_h = 260
    lines.append(f'  <!-- Small leaf-spine drawing container -->')
    lines.append(f'  <rect x="{draw_x}" y="{draw_y}" width="{draw_w}" height="{draw_h}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')

    # Visual leaf-spine topology drawing
    # Spines tier: 4 small spine blocks at top
    # Leaf tier: 1 featured split leaf block in middle
    # Server tier: 4 server blocks at bottom
    # Connecting fabric lines (NO marker-end)
    
    # Spine boxes (y = 260, h = 26)
    # 4 spines across x = 160, 240, 320, 400
    spine_ys = 260
    spine_xs = [170, 250, 330, 410]
    for sx in spine_xs:
        lines.append(f'  <rect x="{sx}" y="{spine_ys}" width="50" height="24" rx="4" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
        lines.append(f'  <circle cx="{sx+15}" cy="{spine_ys+12}" r="2.5" fill="{main_green}" />')
        lines.append(f'  <circle cx="{sx+25}" cy="{spine_ys+12}" r="2.5" fill="{main_green}" />')
        lines.append(f'  <circle cx="{sx+35}" cy="{spine_ys+12}" r="2.5" fill="{main_green}" />')

    # Featured Leaf switch box (y = 330 to 410, h = 80, x = 150, w = 480)
    leaf_bx = 110
    leaf_by = 325
    leaf_bw = 600
    leaf_bh = 90
    
    # Outer leaf box
    lines.append(f'  <rect x="{leaf_bx}" y="{leaf_by}" width="{leaf_bw}" height="{leaf_bh}" rx="8" fill="#f0f7f2" stroke="{main_green}" stroke-width="2.5" />')
    # Horizontal split line through the leaf
    lines.append(f'  <line x1="{leaf_bx}" y1="{leaf_by + 45}" x2="{leaf_bx + leaf_bw}" y2="{leaf_by + 45}" stroke="{main_green}" stroke-width="2" stroke-dasharray="6,4" />')
    
    # Uplink ports along top edge of leaf
    # Downlink ports along bottom edge of leaf
    for px in [180, 230, 280, 330, 380, 430, 480, 530, 580, 630]:
        lines.append(f'  <rect x="{px-6}" y="{leaf_by+4}" width="12" height="10" rx="2" fill="{main_green}" />')
        lines.append(f'  <rect x="{px-6}" y="{leaf_by+leaf_bh-14}" width="12" height="10" rx="2" fill="{main_green}" />')

    # Connections between Spines and Leaf uplinks (clean lines, NO arrowheads)
    for i, sx in enumerate(spine_xs):
        lx = 200 + i * 110
        lines.append(f'  <line x1="{sx+25}" y1="{spine_ys+24}" x2="{lx}" y2="{leaf_by+4}" stroke="{sub_green}" stroke-width="2" />')

    # Server boxes (y = 445, h = 26)
    server_xs = [170, 250, 330, 410, 490, 570]
    server_ys = 455
    for sx in server_xs:
        lines.append(f'  <rect x="{sx}" y="{server_ys}" width="50" height="24" rx="4" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
        lines.append(f'  <line x1="{sx+8}" y1="{server_ys+8}" x2="{sx+42}" y2="{server_ys+8}" stroke="{main_green}" stroke-width="1.5" />')
        lines.append(f'  <line x1="{sx+8}" y1="{server_ys+16}" x2="{sx+42}" y2="{server_ys+16}" stroke="{main_green}" stroke-width="1.5" />')

    # Connections between Leaf downlinks and servers
    for i, sx in enumerate(server_xs):
        lx = 200 + i * 85
        lines.append(f'  <line x1="{lx}" y1="{leaf_by+leaf_bh-4}" x2="{sx+25}" y2="{server_ys}" stroke="{sub_green}" stroke-width="2" />')

    # Split Leaf Label: 'half down to servers / half up to spines'
    # Font size >= 24 px. Must be a single text element!
    lines.append(f'  <text x="{draw_x + draw_w//2}" y="{leaf_by + 53}" font-family="sans-serif" font-size="26" font-weight="bold" fill="{accent_green}" text-anchor="middle">half down to servers / half up to spines</text>')

    # Formula Cards below drawing
    # We have 3 formulas:
    # 1. 'spines = R/2'
    # 2. 'max leaves = R'
    # 3. 'max servers = R x R/2 = R^2/2'
    f_card_x = 70
    f_card_w = 680
    f_card_h = 95
    f_start_y = 525
    f_gap = 25

    # Formula 1: spines = R/2
    y1 = f_start_y
    lines.append(f'  <rect x="{f_card_x}" y="{y1}" width="{f_card_w}" height="{f_card_h}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <circle cx="{f_card_x + 45}" cy="{y1 + f_card_h//2}" r="18" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <path d="M {f_card_x+37} {y1+f_card_h//2-7} L {f_card_x+53} {y1+f_card_h//2+7} M {f_card_x+53} {y1+f_card_h//2-7} L {f_card_x+37} {y1+f_card_h//2+7}" stroke="{main_green}" stroke-width="2.5" />')
    lines.append(f'  <text x="{f_card_x + 90}" y="{y1 + 57}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">spines = R/2</text>')

    # Formula 2: max leaves = R
    y2 = y1 + f_card_h + f_gap
    lines.append(f'  <rect x="{f_card_x}" y="{y2}" width="{f_card_w}" height="{f_card_h}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <circle cx="{f_card_x + 45}" cy="{y2 + f_card_h//2}" r="18" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <rect x="{f_card_x+37}" y="{y2+f_card_h//2-7}" width="16" height="14" rx="2" fill="none" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <text x="{f_card_x + 90}" y="{y2 + 57}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">max leaves = R</text>')

    # Formula 3: max servers = R x R/2 = R^2/2
    y3 = y2 + f_card_h + f_gap
    lines.append(f'  <rect x="{f_card_x}" y="{y3}" width="{f_card_w}" height="{f_card_h}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <circle cx="{f_card_x + 45}" cy="{y3 + f_card_h//2}" r="18" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <path d="M {f_card_x+37} {y3+f_card_h//2} L {f_card_x+53} {y3+f_card_h//2} M {f_card_x+45} {y3+f_card_h//2-8} L {f_card_x+45} {y3+f_card_h//2+8}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <text x="{f_card_x + 90}" y="{y3 + 57}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">max servers = R x R/2 = R^2/2</text>')


    # ==========================================
    # RIGHT PANEL: worked example with 64-port 400G switches
    # ==========================================
    lines.append(f'  <!-- Right Panel Container -->')
    lines.append(f'  <rect x="{right_x}" y="{col_y}" width="{col_w}" height="{col_h}" rx="16" fill="{panel_bg}" stroke="{main_green}" stroke-width="2" />')

    # Right Header Icon (Calculator / rack unit icon, 56 px, green stroke 4)
    # Placed at x = right_x + 30 = 850, y = col_y + 25 = 155
    lines.append(f'  <g transform="translate(850, 155)" stroke="{main_green}" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="2" y="2" width="52" height="52" rx="8" />')
    lines.append('    <rect x="12" y="10" width="32" height="12" rx="3" fill="#207448" />')
    lines.append('    <circle cx="18" cy="32" r="3" fill="#207448" />')
    lines.append('    <circle cx="28" cy="32" r="3" fill="#207448" />')
    lines.append('    <circle cx="38" cy="32" r="3" fill="#207448" />')
    lines.append('    <circle cx="18" cy="42" r="3" fill="#207448" />')
    lines.append('    <circle cx="28" cy="42" r="3" fill="#207448" />')
    lines.append('    <circle cx="38" cy="42" r="3" fill="#207448" />')
    lines.append('  </g>')

    # Right Panel Title: "worked example with 64-port 400G switches"
    # Wrap into 2 lines with tspan so it stays well padded
    lines.append(f'  <text x="925" y="180" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">')
    lines.append(f'    <tspan x="925" dy="0">worked example with</tspan>')
    lines.append(f'    <tspan x="925" dy="38">64-port 400G switches</tspan>')
    lines.append('  </text>')

    # Right Panel 4 Worked Example Cards:
    # 1. 'each leaf 32 downlinks + 32 uplinks'
    # 2. '32 spines'
    # 3. 'up to 64 leaves'
    # 4. 'up to 2,048 endpoint ports = 256 servers with eight GPUs each'
    r_card_x = 850
    r_card_w = 680

    # Card 1: each leaf 32 downlinks + 32 uplinks (y = 250, h = 100)
    ry1 = 250
    rh1 = 100
    lines.append(f'  <rect x="{r_card_x}" y="{ry1}" width="{r_card_w}" height="{rh1}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <g transform="translate({r_card_x+25}, {ry1+28})" stroke="{main_green}" stroke-width="3" fill="none">')
    lines.append('    <path d="M 10 32 L 10 12 M 4 18 L 10 12 L 16 18" stroke-linecap="round" stroke-linejoin="round" />')
    lines.append('    <path d="M 26 12 L 26 32 M 20 26 L 26 32 L 32 26" stroke-linecap="round" stroke-linejoin="round" />')
    lines.append('  </g>')
    lines.append(f'  <text x="{r_card_x + 85}" y="{ry1 + 60}" font-family="sans-serif" font-size="28" font-weight="bold" fill="{text_color}">each leaf 32 downlinks + 32 uplinks</text>')

    # Card 2: 32 spines (y = 375, h = 100)
    ry2 = 375
    rh2 = 100
    lines.append(f'  <rect x="{r_card_x}" y="{ry2}" width="{r_card_w}" height="{rh2}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <g transform="translate({r_card_x+25}, {ry2+28})" stroke="{main_green}" stroke-width="3" fill="none">')
    lines.append('    <rect x="4" y="8" width="32" height="28" rx="4" />')
    lines.append('    <circle cx="12" cy="22" r="3" fill="{main_green}" />')
    lines.append('    <circle cx="20" cy="22" r="3" fill="{main_green}" />')
    lines.append('    <circle cx="28" cy="22" r="3" fill="{main_green}" />')
    lines.append('  </g>')
    lines.append(f'  <text x="{r_card_x + 85}" y="{ry2 + 60}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">32 spines</text>')

    # Card 3: up to 64 leaves (y = 500, h = 100)
    ry3 = 500
    rh3 = 100
    lines.append(f'  <rect x="{r_card_x}" y="{ry3}" width="{r_card_w}" height="{rh3}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    lines.append(f'  <g transform="translate({r_card_x+25}, {ry3+28})" stroke="{main_green}" stroke-width="3" fill="none">')
    lines.append('    <rect x="4" y="6" width="32" height="14" rx="3" />')
    lines.append('    <rect x="4" y="24" width="32" height="14" rx="3" />')
    lines.append('  </g>')
    lines.append(f'  <text x="{r_card_x + 85}" y="{ry3 + 60}" font-family="sans-serif" font-size="30" font-weight="bold" fill="{text_color}">up to 64 leaves</text>')

    # Card 4: up to 2,048 endpoint ports = 256 servers with eight GPUs each (y = 625, h = 220)
    ry4 = 625
    rh4 = 220
    lines.append(f'  <rect x="{r_card_x}" y="{ry4}" width="{r_card_w}" height="{rh4}" rx="12" fill="{card_bg}" stroke="{main_green}" stroke-width="2" />')
    # Decorative cluster of GPU server icons inside Card 4
    lines.append(f'  <g transform="translate({r_card_x+35}, {ry4+30})" stroke="{main_green}" stroke-width="2.5" fill="none">')
    lines.append('    <rect x="0" y="0" width="50" height="24" rx="4" fill="#e8f1ea" />')
    lines.append('    <line x1="8" y1="8" x2="42" y2="8" />')
    lines.append('    <line x1="8" y1="16" x2="42" y2="16" />')
    lines.append('    <rect x="0" y="32" width="50" height="24" rx="4" fill="#e8f1ea" />')
    lines.append('    <line x1="8" y1="40" x2="42" y2="40" />')
    lines.append('    <line x1="8" y1="48" x2="42" y2="48" />')
    lines.append('    <rect x="0" y="64" width="50" height="24" rx="4" fill="#e8f1ea" />')
    lines.append('    <line x1="8" y1="72" x2="42" y2="72" />')
    lines.append('    <line x1="8" y1="80" x2="42" y2="80" />')
    lines.append('  </g>')
    # Text wrapped cleanly into two lines
    lines.append(f'  <text x="{r_card_x + 115}" y="{ry4 + 92}" font-family="sans-serif" font-size="28" font-weight="bold" fill="{text_color}">')
    lines.append(f'    <tspan x="{r_card_x + 115}" dy="0">up to 2,048 endpoint ports =</tspan>')
    lines.append(f'    <tspan x="{r_card_x + 115}" dy="42">256 servers with eight GPUs each</tspan>')
    lines.append('  </text>')

    # ==========================================
    # BOTTOM ORANGE NOTE:
    # 'beyond R^2/2 endpoints, build pods: 5-stage reaches R^3/4 (65,536 for R = 64)'
    # ==========================================
    note_x = 40
    note_y = 920
    note_w = 1520
    note_h = 90
    lines.append(f'  <!-- Orange Note Banner -->')
    lines.append(f'  <rect x="{note_x}" y="{note_y}" width="{note_w}" height="{note_h}" rx="14" fill="{orange_bg}" stroke="{orange}" stroke-width="3" />')
    
    # Orange decorative icon: 5-stage / expansion star or pod icon
    lines.append(f'  <g transform="translate(65, 936)" stroke="{orange}" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    lines.append('    <rect x="4" y="4" width="48" height="48" rx="8" />')
    lines.append('    <line x1="16" y1="28" x2="40" y2="28" />')
    lines.append('    <line x1="28" y1="16" x2="28" y2="40" />')
    lines.append('    <circle cx="28" cy="28" r="6" fill="#db8129" />')
    lines.append('  </g>')

    # Orange note text: exact label
    lines.append(f'  <text x="145" y="976" font-family="sans-serif" font-size="28" font-weight="bold" fill="{text_color}">beyond R^2/2 endpoints, build pods: 5-stage reaches R^3/4 (65,536 for R = 64)</text>')

    lines.append('</svg>')
    return "\n".join(lines)

if __name__ == "__main__":
    svg_content = build_svg()
    with open("candidate_n18_sizing.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
    print("Generated candidate_n18_sizing.svg successfully!")
