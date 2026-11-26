#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

title_text = "Pick the algorithm by the unit of work it counts"
bottom_bar_text = "Name the unit of work first, then pick the algorithm that counts it"
right_panel_title = "Four principles"

# Table column geometry:
x_col1 = 40
w_col1 = 360

arrow1_x1 = x_col1 + w_col1 # 400
arrow1_x2 = arrow1_x1 + 22  # 422

x_col2 = arrow1_x2          # 422
w_col2 = 324

arrow2_x1 = x_col2 + w_col2 # 746
arrow2_x2 = arrow2_x1 + 22  # 768

x_col3 = arrow2_x2          # 768
w_col3 = 382

# Right panel geometry:
x_rp = 1180
w_rp = 380

# Total width check: 1180 + 380 = 1560. Margins: left 40, right 40 (1560+40=1600).
# Gap between table and right panel: 1180 - (768 + 382) = 1180 - 1150 = 30 px.

# Rows vertical layout:
# Top start y = 92
# Heights: 3-line rows: 98px, 2-line rows: 74px
row_specs = [
    # (row_index, height, is_orange)
    (1,  74, False),
    (2,  98, False), # 3 lines
    (3,  74, False),
    (4,  74, False),
    (5,  74, True),  # orange on col 3
    (6,  74, False),
    (7,  98, False), # 3 lines
    (8,  98, False), # 3 lines in col 3
    (9,  74, False),
    (10, 74, False),
    (11, 74, False)
]

# Calculate y positions for each row:
gap_y = 12
y_cursor = 92
row_coords = []
for idx, h, is_orange in row_specs:
    row_coords.append((idx, y_cursor, h, is_orange))
    y_cursor += h + gap_y

# Table ends at y_cursor - gap_y:
table_bot = y_cursor - gap_y
print(f"Table starts at y=92, ends at y={table_bot} (height={table_bot - 92})")

# Right panel container:
rp_y = 92
rp_h = table_bot - rp_y
print(f"Right panel y={rp_y}, h={rp_h}")

# Row content:
# Each item is (full_text, [lines])
table_data = [
    # Row 1
    (
        ("Short stateless equal requests", ["Short stateless", "equal requests"]),
        ("round robin or weighted round robin", ["round robin or", "weighted round robin"]),
        ("ignores request cost and backend load", ["ignores request cost", "and backend load"])
    ),
    # Row 2
    (
        ("Long-lived connections or variable-length requests", ["Long-lived connections", "or variable-length", "requests"]),
        ("least connections", ["least connections"]),
        ("counts connections, not work; needs shared state across LB instances", ["counts connections, not", "work; needs shared state", "across LB instances"])
    ),
    # Row 3
    (
        ("HTTP or gRPC requests", ["HTTP or gRPC requests"]),
        ("least outstanding requests", ["least outstanding", "requests"]),
        ("same, request-granular", ["same, request-granular"])
    ),
    # Row 4
    (
        ("Heterogeneous backends", ["Heterogeneous", "backends"]),
        ("least response time, EWMA, peak-EWMA", ["least response time,", "EWMA, peak-EWMA"]),
        ("needs measurement; can oscillate (herding)", ["needs measurement; can", "oscillate (herding)"])
    ),
    # Row 5 (orange on pitfall)
    (
        ("Large pools with imperfect load info", ["Large pools with", "imperfect load info"]),
        ("power of two random choices", ["power of two", "random choices"]),
        ("needs load info per backend", ["needs load info", "per backend"])
    ),
    # Row 6
    (
        ("Session affinity or cache locality", ["Session affinity or", "cache locality"]),
        ("source, URL or header hash", ["source, URL or", "header hash"]),
        ("remaps most keys when N changes", ["remaps most keys", "when N changes"])
    ),
    # Row 7
    (
        ("Caches, sticky sessions, sharded stores", ["Caches, sticky", "sessions, sharded", "stores"]),
        ("consistent hashing (ring, rendezvous, jump hash)", ["consistent hashing", "(ring, rendezvous,", "jump hash)"]),
        ("load imbalance; virtual nodes help; hot keys", ["load imbalance; virtual", "nodes help; hot keys"])
    ),
    # Row 8
    (
        ("L4 LBs behind ECMP", ["L4 LBs behind ECMP"]),
        ("Maglev hashing", ["Maglev hashing"]),
        ("table rebuild cost; small disruption on change", ["table rebuild cost;", "small disruption", "on change"])
    ),
    # Row 9
    (
        ("Cost and latency", ["Cost and latency"]),
        ("locality or zone-aware", ["locality or", "zone-aware"]),
        ("capacity imbalance across zones", ["capacity imbalance", "across zones"])
    ),
    # Row 10
    (
        ("DR and spillover", ["DR and spillover"]),
        ("priority or failover groups", ["priority or failover", "groups"]),
        ("cold backups", ["cold backups"])
    ),
    # Row 11
    (
        ("LLM inference", ["LLM inference"]),
        ("load-aware custom: GPU, queue, KV-cache", ["load-aware custom:", "GPU, queue, KV-cache"]),
        ("needs telemetry; careful staleness handling", ["needs telemetry; careful", "staleness handling"])
    )
]

# Right panel principles:
principles_data = [
    # Card 1 (5 lines)
    (
        "choose the metric that represents work: connections, requests, tokens and GPU-seconds differ",
        [
            "choose the metric that",
            "represents work:",
            "connections, requests,",
            "tokens and GPU-seconds",
            "differ"
        ],
        176 # height
    ),
    # Card 2 (8 lines)
    (
        "many LB instances each doing local least connections herd onto the same backend, like drivers following one satnav to one empty car park; a randomised pick breaks it up",
        [
            "many LB instances each",
            "doing local least",
            "connections herd onto",
            "the same backend, like",
            "drivers following one",
            "satnav to one empty",
            "car park; a randomised",
            "pick breaks it up"
        ],
        254 # height
    ),
    # Card 3 (7 lines)
    (
        "hash affinity serves cache locality and state but accepts uneven load: plan for reshuffling with consistent or resilient hashing",
        [
            "hash affinity serves",
            "cache locality and",
            "state but accepts",
            "uneven load: plan for",
            "reshuffling with",
            "consistent or",
            "resilient hashing"
        ],
        228 # height
    ),
    # Card 4 (5 lines)
    (
        "slow start ramps up the weight of a new or recovered backend while its JIT, caches and GPU warm up",
        [
            "slow start ramps up",
            "the weight of a new or",
            "recovered backend",
            "while its JIT, caches",
            "and GPU warm up"
        ],
        176 # height
    )
]

# Generate SVG
lines = []
lines.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">')
lines.append('  <title>Pick the algorithm by the unit of work it counts</title>')
lines.append('  <desc>A table pairing each unit of work with its load balancing algorithm and pitfall, with four key principles and takeaway rule.</desc>')
lines.append('  <defs>')
lines.append('    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448" />')
lines.append('    </marker>')
lines.append('    <marker id="arrow-orange" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">')
lines.append('      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#db8129" />')
lines.append('    </marker>')
lines.append('  </defs>')
lines.append('  <!-- Canvas Background -->')
lines.append('  <rect width="1600" height="1200" fill="#f5f8f5" />')
lines.append('  <!-- Title -->')
lines.append('  <text x="800" y="54" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Pick the algorithm by the unit of work it counts</text>')

# Table rows
for idx, (r_idx, ry, rh, is_orange) in enumerate(row_coords):
    c1_info, c2_info, c3_info = table_data[idx]
    y_center = ry + rh / 2

    # Column 1 box (Unit of work)
    lines.append(f'  <!-- Row {r_idx} Col 1 -->')
    lines.append(f'  <rect x="{x_col1}" y="{ry}" width="{w_col1}" height="{rh}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    c1_lines = c1_info[1]
    if len(c1_lines) == 1:
        ty = ry + rh / 2 + 8
        lines.append(f'  <text x="{x_col1 + w_col1/2}" y="{ty:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">{c1_lines[0]}</text>')
    elif len(c1_lines) == 2:
        ty1 = ry + rh / 2 - 5
        lines.append(f'  <text x="{x_col1 + w_col1/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
        lines.append(f'    <tspan x="{x_col1 + w_col1/2}" dy="0">{c1_lines[0]}</tspan>')
        lines.append(f'    <tspan x="{x_col1 + w_col1/2}" dy="26">{c1_lines[1]}</tspan>')
        lines.append(f'  </text>')
    elif len(c1_lines) == 3:
        ty1 = ry + rh / 2 - 18
        lines.append(f'  <text x="{x_col1 + w_col1/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
        lines.append(f'    <tspan x="{x_col1 + w_col1/2}" dy="0">{c1_lines[0]}</tspan>')
        lines.append(f'    <tspan x="{x_col1 + w_col1/2}" dy="26">{c1_lines[1]}</tspan>')
        lines.append(f'    <tspan x="{x_col1 + w_col1/2}" dy="26">{c1_lines[2]}</tspan>')
        lines.append(f'  </text>')

    # Arrow 1: Col 1 -> Col 2
    lines.append(f'  <line x1="{arrow1_x1}" y1="{y_center:.1f}" x2="{arrow1_x2}" y2="{y_center:.1f}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')

    # Column 2 box (Algorithm)
    lines.append(f'  <!-- Row {r_idx} Col 2 -->')
    lines.append(f'  <rect x="{x_col2}" y="{ry}" width="{w_col2}" height="{rh}" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="1.8" />')
    c2_lines = c2_info[1]
    if len(c2_lines) == 1:
        ty = ry + rh / 2 + 8
        lines.append(f'  <text x="{x_col2 + w_col2/2}" y="{ty:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">{c2_lines[0]}</text>')
    elif len(c2_lines) == 2:
        ty1 = ry + rh / 2 - 5
        lines.append(f'  <text x="{x_col2 + w_col2/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
        lines.append(f'    <tspan x="{x_col2 + w_col2/2}" dy="0">{c2_lines[0]}</tspan>')
        lines.append(f'    <tspan x="{x_col2 + w_col2/2}" dy="26">{c2_lines[1]}</tspan>')
        lines.append(f'  </text>')
    elif len(c2_lines) == 3:
        ty1 = ry + rh / 2 - 18
        lines.append(f'  <text x="{x_col2 + w_col2/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">')
        lines.append(f'    <tspan x="{x_col2 + w_col2/2}" dy="0">{c2_lines[0]}</tspan>')
        lines.append(f'    <tspan x="{x_col2 + w_col2/2}" dy="26">{c2_lines[1]}</tspan>')
        lines.append(f'    <tspan x="{x_col2 + w_col2/2}" dy="26">{c2_lines[2]}</tspan>')
        lines.append(f'  </text>')

    # Arrow 2: Col 2 -> Col 3
    if is_orange:
        lines.append(f'  <line x1="{arrow2_x1}" y1="{y_center:.1f}" x2="{arrow2_x2}" y2="{y_center:.1f}" stroke="#db8129" stroke-width="2.5" marker-end="url(#arrow-orange)" />')
    else:
        lines.append(f'  <line x1="{arrow2_x1}" y1="{y_center:.1f}" x2="{arrow2_x2}" y2="{y_center:.1f}" stroke="#207448" stroke-width="2.5" marker-end="url(#arrow-green)" />')

    # Column 3 box (Pitfall)
    lines.append(f'  <!-- Row {r_idx} Col 3 -->')
    c3_lines = c3_info[1]
    if is_orange:
        lines.append(f'  <rect x="{x_col3}" y="{ry}" width="{w_col3}" height="{rh}" rx="8" fill="#ffffff" stroke="#db8129" stroke-width="2.5" />')
        text_fill = "#303a36"
    else:
        lines.append(f'  <rect x="{x_col3}" y="{ry}" width="{w_col3}" height="{rh}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
        text_fill = "#303a36"

    if len(c3_lines) == 1:
        ty = ry + rh / 2 + 8
        lines.append(f'  <text x="{x_col3 + w_col3/2}" y="{ty:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_fill}">{c3_lines[0]}</text>')
    elif len(c3_lines) == 2:
        ty1 = ry + rh / 2 - 5
        lines.append(f'  <text x="{x_col3 + w_col3/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_fill}">')
        lines.append(f'    <tspan x="{x_col3 + w_col3/2}" dy="0">{c3_lines[0]}</tspan>')
        lines.append(f'    <tspan x="{x_col3 + w_col3/2}" dy="26">{c3_lines[1]}</tspan>')
        lines.append(f'  </text>')
    elif len(c3_lines) == 3:
        ty1 = ry + rh / 2 - 18
        lines.append(f'  <text x="{x_col3 + w_col3/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="{text_fill}">')
        lines.append(f'    <tspan x="{x_col3 + w_col3/2}" dy="0">{c3_lines[0]}</tspan>')
        lines.append(f'    <tspan x="{x_col3 + w_col3/2}" dy="26">{c3_lines[1]}</tspan>')
        lines.append(f'    <tspan x="{x_col3 + w_col3/2}" dy="26">{c3_lines[2]}</tspan>')
        lines.append(f'  </text>')

# Right panel: Four principles
lines.append('  <!-- Right Panel: Four principles -->')
lines.append(f'  <rect x="{x_rp}" y="{rp_y}" width="{w_rp}" height="{rp_h}" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')

# Outline Icon (Gear / Rules icon 56px) in Right Panel Header
# Center of panel header: y = rp_y + 16 .. rp_y + 60
lines.append(f'  <g transform="translate({x_rp + 24}, {rp_y + 14})" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
lines.append('    <circle cx="20" cy="20" r="14" />')
lines.append('    <line x1="20" y1="2" x2="20" y2="6" stroke-width="4.5" />')
lines.append('    <line x1="20" y1="34" x2="20" y2="38" stroke-width="4.5" />')
lines.append('    <line x1="2" y1="20" x2="6" y2="20" stroke-width="4.5" />')
lines.append('    <line x1="34" y1="20" x2="38" y2="20" stroke-width="4.5" />')
lines.append('    <line x1="7" y1="7" x2="10" y2="10" stroke-width="4.5" />')
lines.append('    <line x1="30" y1="30" x2="33" y2="33" stroke-width="4.5" />')
lines.append('    <line x1="7" y1="33" x2="10" y2="30" stroke-width="4.5" />')
lines.append('    <line x1="30" y1="10" x2="33" y2="7" stroke-width="4.5" />')
lines.append('    <circle cx="20" cy="20" r="6" fill="#207448" />')
lines.append('  </g>')
lines.append(f'  <text x="{x_rp + 76}" y="{rp_y + 44}" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">{right_panel_title}</text>')

# 4 Principle cards
card_w = 350
card_x = x_rp + 15
card_gap = 22
card_y = rp_y + 76

for p_idx, (p_full, p_lines, ch) in enumerate(principles_data, 1):
    lines.append(f'  <!-- Principle Card {p_idx} -->')
    lines.append(f'  <rect x="{card_x}" y="{card_y}" width="{card_w}" height="{ch}" rx="8" fill="#ffffff" stroke="#207448" stroke-width="1.8" />')
    
    # Calculate starting baseline ty1 to vertically center lines in card
    num_l = len(p_lines)
    total_text_h = (num_l - 1) * 26 + 24
    top_pad = (ch - total_text_h) / 2
    ty1 = card_y + top_pad + 24
    
    lines.append(f'  <text x="{card_x + card_w/2}" y="{ty1:.1f}" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">')
    for l_idx, pl in enumerate(p_lines):
        dy_val = 0 if l_idx == 0 else 26
        lines.append(f'    <tspan x="{card_x + card_w/2}" dy="{dy_val}">{pl}</tspan>')
    lines.append(f'  </text>')
    
    card_y += ch + card_gap

# Bottom Bar
lines.append('  <!-- Bottom Takeaway Bar -->')
lines.append('  <rect x="40" y="1132" width="1520" height="52" rx="8" fill="#207448" />')
lines.append(f'  <text x="800" y="1165" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#ffffff">{bottom_bar_text}</text>')
lines.append('</svg>')

svg_content = "\n".join(lines)
with open("planning/image_tools/test_algo_pick.svg", "w", encoding="utf-8") as f:
    f.write(svg_content)

print("Generated planning/image_tools/test_algo_pick.svg successfully!")
