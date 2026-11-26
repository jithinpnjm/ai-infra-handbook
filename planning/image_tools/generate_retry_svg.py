import xml.etree.ElementTree as ET
import re
import pathlib

def build_svg():
    svg = []
    W = 1600
    H = 1200
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">')
    svg.append('  <title>Retry layers multiply</title>')
    svg.append('  <desc>Architecture diagram illustrating how retry layers multiply attempts, the mathematical formula for expected attempts, and the single-layer gateway budget rule.</desc>')
    svg.append('  <defs>')
    svg.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="9" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
    svg.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
    svg.append('    </marker>')
    svg.append('  </defs>')
    
    # Canvas background
    svg.append(f'  <rect width="{W}" height="{H}" fill="#f5f8f5" />')

    # Main Title (48px bold)
    svg.append('  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Retry layers multiply</text>')

    # ==================== COLUMN 1: STACK OF LAYERS ====================
    # Outer container for Column 1: x = 40, y = 110, width = 640, height = 870
    svg.append('  <rect x="40" y="110" width="640" height="870" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />')

    # Layers geometry:
    # 5 layer boxes: x = 70, width = 330, height = 95
    # y = 150, 290, 430, 570, 710
    layer_x = 70
    layer_w = 330
    layer_h = 95
    layer_y = [150, 290, 430, 570, 710]

    # --- Layer 1: SDK ---
    svg.append(f'  <rect x="{layer_x}" y="{layer_y[0]}" width="{layer_w}" height="{layer_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Window / App Icon (56px) at (85, 170)
    svg.append('  <g transform="translate(85, 170)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="4" y="6" width="48" height="44" rx="6" />')
    svg.append('    <line x1="4" y1="18" x2="52" y2="18" />')
    svg.append('    <circle cx="12" cy="12" r="2" fill="#207448" stroke="none" />')
    svg.append('    <circle cx="18" cy="12" r="2" fill="#207448" stroke="none" />')
    svg.append('    <polyline points="14,28 22,34 14,40" />')
    svg.append('    <line x1="26" y1="40" x2="38" y2="40" />')
    svg.append('  </g>')
    # Retry cycle mini-icon on right of layer box
    svg.append('  <g transform="translate(345, 180)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 14 A 12 12 0 1 1 20 6" />')
    svg.append('    <polyline points="20,1 20,7 26,7" />')
    svg.append('  </g>')
    svg.append('  <text x="235" y="208" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">SDK</text>')

    # Arrow 1: SDK -> gateway
    svg.append(f'  <line x1="235" y1="{layer_y[0] + layer_h}" x2="235" y2="{layer_y[1] - 5}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # --- Layer 2: gateway ---
    svg.append(f'  <rect x="{layer_x}" y="{layer_y[1]}" width="{layer_w}" height="{layer_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Portal / Gateway Arch Icon (56px) at (85, 310)
    svg.append('  <g transform="translate(85, 310)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 8 50 L 8 24 A 20 20 0 0 1 48 24 L 48 50" />')
    svg.append('    <line x1="4" y1="50" x2="52" y2="50" />')
    svg.append('    <path d="M 20 50 L 20 32 A 8 8 0 0 1 36 32 L 36 50" />')
    svg.append('  </g>')
    # Retry cycle mini-icon
    svg.append('  <g transform="translate(345, 320)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 14 A 12 12 0 1 1 20 6" />')
    svg.append('    <polyline points="20,1 20,7 26,7" />')
    svg.append('  </g>')
    svg.append('  <text x="235" y="348" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">gateway</text>')

    # Arrow 2: gateway -> mesh sidecar
    svg.append(f'  <line x1="235" y1="{layer_y[1] + layer_h}" x2="235" y2="{layer_y[2] - 5}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # --- Layer 3: mesh sidecar ---
    svg.append(f'  <rect x="{layer_x}" y="{layer_y[2]}" width="{layer_w}" height="{layer_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Gear / Sidecar Service Icon (56px) at (85, 450)
    svg.append('  <g transform="translate(85, 450)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <circle cx="28" cy="28" r="10" />')
    svg.append('    <path d="M 28 8 L 28 14 M 28 42 L 28 48 M 8 28 L 14 28 M 42 28 L 48 28 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 14 L 42 18" />')
    svg.append('  </g>')
    # Retry cycle mini-icon
    svg.append('  <g transform="translate(345, 460)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 14 A 12 12 0 1 1 20 6" />')
    svg.append('    <polyline points="20,1 20,7 26,7" />')
    svg.append('  </g>')
    svg.append('  <text x="240" y="488" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#303a36">mesh sidecar</text>')

    # Arrow 3: mesh sidecar -> router
    svg.append(f'  <line x1="235" y1="{layer_y[2] + layer_h}" x2="235" y2="{layer_y[3] - 5}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # --- Layer 4: router ---
    svg.append(f'  <rect x="{layer_x}" y="{layer_y[3]}" width="{layer_w}" height="{layer_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Network Router Icon (56px) at (85, 590)
    svg.append('  <g transform="translate(85, 590)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="6" y="16" width="44" height="24" rx="4" />')
    svg.append('    <line x1="16" y1="28" x2="20" y2="28" />')
    svg.append('    <line x1="26" y1="28" x2="30" y2="28" />')
    svg.append('    <line x1="36" y1="28" x2="40" y2="28" />')
    svg.append('    <line x1="16" y1="16" x2="16" y2="8" />')
    svg.append('    <line x1="40" y1="16" x2="40" y2="8" />')
    svg.append('  </g>')
    # Retry cycle mini-icon
    svg.append('  <g transform="translate(345, 600)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 14 A 12 12 0 1 1 20 6" />')
    svg.append('    <polyline points="20,1 20,7 26,7" />')
    svg.append('  </g>')
    svg.append('  <text x="235" y="628" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">router</text>')

    # Arrow 4: router -> (and sometimes more)
    svg.append(f'  <line x1="235" y1="{layer_y[3] + layer_h}" x2="235" y2="{layer_y[4] - 5}" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)" />')

    # --- Layer 5: (and sometimes more) ---
    svg.append(f'  <rect x="{layer_x}" y="{layer_y[4]}" width="{layer_w}" height="{layer_h}" rx="12" fill="#f5f8f5" stroke="#207448" stroke-width="2" stroke-dasharray="8 6" />')
    svg.append('  <text x="235" y="767" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">(and sometimes more)</text>')

    # --- Bracket and Card for 'retries on its own' ---
    # The bracket spans layers 1 to 4: from y = 180 to y = 635, center = 407.5
    svg.append('  <path d="M 415 170 C 428 170, 428 395, 436 407.5 C 428 420, 428 645, 415 645" fill="none" stroke="#207448" stroke-width="3" stroke-linecap="round" />')
    
    # Card for 'retries on its own' at x = 445, y = 358, width = 215, height = 100
    svg.append('  <rect x="445" y="358" width="215" height="100" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('  <text x="552" y="399" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
    svg.append('    <tspan x="552" dy="0">retries on</tspan>')
    svg.append('    <tspan x="552" dy="32">its own</tspan>')
    svg.append('  </text>')


    # ==================== COLUMN 2: ARITHMETIC PANEL ====================
    # Outer container for Column 2: x = 720, y = 110, width = 840, height = 870
    svg.append('  <rect x="720" y="110" width="840" height="870" rx="16" fill="#ffffff" stroke="#207448" stroke-width="2" />')

    # Arithmetic panel Header & Icon
    # Calculator / Sigma Icon (56px) at (750, 130)
    svg.append('  <g transform="translate(750, 130)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <rect x="8" y="4" width="40" height="48" rx="6" />')
    svg.append('    <line x1="14" y1="16" x2="42" y2="16" stroke-width="3" />')
    svg.append('    <circle cx="18" cy="26" r="2" fill="#207448" stroke="none" />')
    svg.append('    <circle cx="28" cy="26" r="2" fill="#207448" stroke="none" />')
    svg.append('    <circle cx="38" cy="26" r="2" fill="#207448" stroke="none" />')
    svg.append('    <circle cx="18" cy="36" r="2" fill="#207448" stroke="none" />')
    svg.append('    <circle cx="28" cy="36" r="2" fill="#207448" stroke="none" />')
    svg.append('    <circle cx="38" cy="36" r="2" fill="#207448" stroke="none" />')
    svg.append('  </g>')
    svg.append('  <text x="1140" y="166" text-anchor="middle" font-family="sans-serif" font-size="32" font-weight="bold" fill="#207448">Arithmetic panel</text>')

    # Geometry of Cards in Column 2:
    # All cards x = 760, width = 760
    card_x = 760
    card_w = 760

    # Card 1 (Formula & probability table):
    # y = 205, height = 195
    c1_y = 205
    c1_h = 195
    svg.append(f'  <rect x="{card_x}" y="{c1_y}" width="{card_w}" height="{c1_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('  <text x="1140" y="243" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1140" dy="0" font-weight="bold">One client, k attempts, failure chance p:</tspan>')
    svg.append('    <tspan x="1140" dy="32">expected attempts = 1 + p + p squared ...</tspan>')
    svg.append('    <tspan x="1140" dy="32">p to the power k - 1;</tspan>')
    svg.append('    <tspan x="1140" dy="32">for k = 4: p 0.1 gives 1.11,</tspan>')
    svg.append('    <tspan x="1140" dy="32">p 0.5 gives 1.875, p 0.8 gives 2.95</tspan>')
    svg.append('  </text>')

    # Card 2 (SRE chapter 3 layers -> 64 attempts):
    # y = 440, height = 135
    c2_y = 440
    c2_h = 135
    svg.append(f'  <rect x="{card_x}" y="{c2_y}" width="{card_w}" height="{c2_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('  <text x="1140" y="482" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1140" dy="0">SRE chapter: three layers each making 3 retries</tspan>')
    svg.append('    <tspan x="1140" dy="32">(4 attempts) can create 64 attempts</tspan>')
    svg.append('    <tspan x="1140" dy="32" font-weight="bold">at the bottom (4 x 4 x 4)</tspan>')
    svg.append('  </text>')

    # Card 3 (AWS builders 5-deep chain -> 243 times):
    # y = 615, height = 135
    c3_y = 615
    c3_h = 135
    svg.append(f'  <rect x="{card_x}" y="{c3_y}" width="{card_w}" height="{c3_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" />')
    svg.append('  <text x="1140" y="657" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="1140" dy="0">AWS builders article: 243 times for</tspan>')
    svg.append('    <tspan x="1140" dy="32">a five-deep call chain = 3 to the power 5,</tspan>')
    svg.append('    <tspan x="1140" dy="32">three attempts per layer</tspan>')
    svg.append('  </text>')

    # Card 4 (ORANGE HIGHLIGHT: 5 layers give 1,024):
    # y = 790, height = 85
    c4_y = 790
    c4_h = 85
    svg.append(f'  <rect x="{card_x}" y="{c4_y}" width="{card_w}" height="{c4_h}" rx="12" fill="#ffffff" stroke="#db8129" stroke-width="3" />')
    svg.append('  <text x="1140" y="842" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#303a36">With 4 attempts per layer, five layers give 1,024</text>')


    # ==================== BOTTOM RULE BAR ====================
    # Outer bar: x = 40, y = 1030, width = 1520, height = 130
    rule_y = 1030
    rule_h = 130
    svg.append(f'  <rect x="40" y="{rule_y}" width="1520" height="{rule_h}" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Shield / Policy Check Icon (56px) at (65, 1065)
    svg.append('  <g transform="translate(65, 1065)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('    <path d="M 28 6 L 10 14 L 10 28 C 10 42 28 50 28 50 C 28 50 46 42 46 28 L 46 14 Z" fill="#ffffff" />')
    svg.append('    <polyline points="20,28 26,34 36,22" />')
    svg.append('  </g>')
    svg.append('  <text x="820" y="1070" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('    <tspan x="820" dy="0" font-weight="bold">set the budget at the gateway in one layer and turn off every other retry loop;</tspan>')
    svg.append('    <tspan x="820" dy="32">retry at the layer directly above the one rejecting, not at every layer;</tspan>')
    svg.append('    <tspan x="820" dy="32">if a large share of backends is overloaded, do not retry at all</tspan>')
    svg.append('  </text>')

    svg.append('</svg>')
    return '\n'.join(svg)

content = build_svg()
with open("candidate_retry.svg", "w") as f:
    f.write(content)

print("candidate_retry.svg written successfully!")
