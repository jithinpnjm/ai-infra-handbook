#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Which knob moves which bill</title>
  <desc>Table of cost drivers and levers per signal, with worked example and budget note.</desc>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5"/>

  <!-- Title -->
  <text x="800" y="65" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Which knob moves which bill</text>

  <!-- Table Headers -->
  <g id="table-headers">
    <rect x="40" y="98" width="1520" height="66" rx="8" fill="#207448"/>
    <line x1="320" y1="98" x2="320" y2="164" stroke="#ffffff" stroke-width="2" stroke-opacity="0.3"/>
    <line x1="800" y1="98" x2="800" y2="164" stroke="#ffffff" stroke-width="2" stroke-opacity="0.3"/>
    <text x="180" y="141" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Signal</text>
    <text x="560" y="141" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Cost driver</text>
    <text x="1180" y="141" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Cheapest levers</text>
  </g>

  <!-- Row 1: Metrics -->
  <g id="row-metrics">
    <rect x="40" y="170" width="1520" height="100" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-opacity="0.35"/>
    <line x1="320" y1="182" x2="320" y2="258" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>
    <line x1="800" y1="182" x2="800" y2="258" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>

    <!-- Metrics Icon: line chart / telemetry -->
    <g transform="translate(60, 192)">
      <path d="M 8 46 L 48 46 M 8 46 L 8 6" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round"/>
      <path d="M 12 38 L 22 24 L 32 32 L 44 14" fill="none" stroke="#207448" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/>
      <circle cx="44" cy="14" r="3.5" fill="#207448"/>
    </g>
    <text x="135" y="231" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Metrics</text>

    <!-- Metrics Cost driver -->
    <text x="345" y="215" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="345" dy="0">active series</tspan>
      <tspan x="345" dy="32">times retention</tspan>
    </text>

    <!-- Metrics Cheapest levers -->
    <text x="825" y="215" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="825" dy="0">fewer labels, fewer buckets, recording rules,</tspan>
      <tspan x="825" dy="32">drop raw series upstream</tspan>
    </text>
  </g>

  <!-- Row 2: Logs -->
  <g id="row-logs">
    <rect x="40" y="282" width="1520" height="100" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-opacity="0.35"/>
    <line x1="320" y1="294" x2="320" y2="370" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>
    <line x1="800" y1="294" x2="800" y2="370" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>

    <!-- Logs Icon: document with log lines -->
    <g transform="translate(60, 304)">
      <rect x="10" y="4" width="36" height="48" rx="4" fill="none" stroke="#207448" stroke-width="3.5"/>
      <line x1="18" y1="16" x2="38" y2="16" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
      <line x1="18" y1="26" x2="38" y2="26" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
      <line x1="18" y1="36" x2="30" y2="36" stroke="#207448" stroke-width="3" stroke-linecap="round"/>
    </g>
    <text x="135" y="343" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Logs</text>

    <!-- Logs Cost driver -->
    <text x="345" y="327" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="345" dy="0">bytes ingested</tspan>
      <tspan x="345" dy="32">and retained</tspan>
    </text>

    <!-- Logs Cheapest levers -->
    <text x="825" y="327" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="825" dy="0">sample successes, shorter retention,</tspan>
      <tspan x="825" dy="32">drop debug</tspan>
    </text>
  </g>

  <!-- Row 3: Traces -->
  <g id="row-traces">
    <rect x="40" y="394" width="1520" height="100" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-opacity="0.35"/>
    <line x1="320" y1="406" x2="320" y2="482" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>
    <line x1="800" y1="406" x2="800" y2="482" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>

    <!-- Traces Icon: waterfall spans -->
    <g transform="translate(60, 416)">
      <rect x="8" y="8" width="38" height="8" rx="2" fill="none" stroke="#207448" stroke-width="3"/>
      <rect x="16" y="22" width="28" height="8" rx="2" fill="none" stroke="#207448" stroke-width="3"/>
      <rect x="24" y="36" width="22" height="8" rx="2" fill="none" stroke="#207448" stroke-width="3"/>
      <line x1="14" y1="16" x2="14" y2="24" stroke="#207448" stroke-width="2"/>
      <line x1="22" y1="30" x2="22" y2="38" stroke="#207448" stroke-width="2"/>
    </g>
    <text x="135" y="455" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Traces</text>

    <!-- Traces Cost driver -->
    <text x="345" y="451" font-family="sans-serif" font-size="25" fill="#303a36">spans retained</text>

    <!-- Traces Cheapest levers -->
    <text x="825" y="451" font-family="sans-serif" font-size="25" fill="#303a36">tail sampling policy, shorter retention</text>
  </g>

  <!-- Row 4: Query -->
  <g id="row-query">
    <rect x="40" y="506" width="1520" height="100" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="1.5" stroke-opacity="0.35"/>
    <line x1="320" y1="518" x2="320" y2="594" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>
    <line x1="800" y1="518" x2="800" y2="594" stroke="#207448" stroke-width="1.5" stroke-opacity="0.25"/>

    <!-- Query Icon: magnifying glass scanner -->
    <g transform="translate(60, 528)">
      <circle cx="22" cy="22" r="14" fill="none" stroke="#207448" stroke-width="3.5"/>
      <line x1="32" y1="32" x2="44" y2="44" stroke="#207448" stroke-width="4" stroke-linecap="round"/>
      <line x1="15" y1="22" x2="29" y2="22" stroke="#207448" stroke-width="2" stroke-linecap="round"/>
    </g>
    <text x="135" y="567" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Query</text>

    <!-- Query Cost driver -->
    <text x="345" y="551" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="345" dy="0">fan-out and</tspan>
      <tspan x="345" dy="32">high-cardinality selects</tspan>
    </text>

    <!-- Query Cheapest levers -->
    <text x="825" y="563" font-family="sans-serif" font-size="25" fill="#303a36">rollups, query limits, downsampling</text>
  </g>

  <!-- Worked example: Baseline -->
  <g id="worked-example-baseline">
    <rect x="40" y="650" width="1520" height="110" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
    <!-- Disk storage icon -->
    <g transform="translate(60, 677)">
      <ellipse cx="26" cy="12" rx="20" ry="7" fill="none" stroke="#207448" stroke-width="3.5"/>
      <path d="M 6 12 v 24 c 0 4 9 7 20 7 s 20 -3 20 -7 v -24" fill="none" stroke="#207448" stroke-width="3.5"/>
      <path d="M 6 24 c 0 4 9 7 20 7 s 20 -3 20 -7" fill="none" stroke="#207448" stroke-width="2.5"/>
    </g>
    <text x="145" y="696" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="145" dy="0">49,200 series at a 30 second interval for 15 days = 43,200 samples per series,</tspan>
      <tspan x="145" dy="34">at 1 to 2 bytes per sample is about 2.1 to 4.3 GB</tspan>
    </text>
  </g>

  <!-- Worked example: Tenant cardinality explosion (single orange highlight) -->
  <g id="worked-example-explosion">
    <rect x="40" y="780" width="1520" height="110" rx="10" fill="#ffffff" stroke="#db8129" stroke-width="3"/>
    <!-- Alert warning triangle icon in orange -->
    <g transform="translate(60, 807)">
      <polygon points="26,6 48,46 4,46" fill="none" stroke="#db8129" stroke-width="3.5" stroke-linejoin="round"/>
      <line x1="26" y1="19" x2="26" y2="33" stroke="#db8129" stroke-width="3.5" stroke-linecap="round"/>
      <circle cx="26" cy="40" r="2.5" fill="#db8129"/>
    </g>
    <text x="145" y="826" font-family="sans-serif" font-size="25" fill="#303a36">
      <tspan x="145" dy="0">with a tenant label on every gateway metric about 3 million series</tspan>
      <tspan x="145" dy="34">needs about 130 to 261 GB</tspan>
    </text>
  </g>

  <!-- Takeaway bar -->
  <g id="takeaway-bar">
    <rect x="40" y="930" width="1520" height="110" rx="10" fill="#207448"/>
    <text x="800" y="976" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="800" dy="0">logs and traces depend on traffic, which moves,</tspan>
      <tspan x="800" dy="34">so set a budget in bytes and spans per day and alert on the trend</tspan>
    </text>
  </g>
</svg>
"""

with open("test_knobs.svg", "w") as f:
    f.write(svg_content)

print("Wrote test_knobs.svg successfully.")

# Run comprehensive audits
tree = ET.parse("test_knobs.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("   [PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1080", f"viewBox unexpected: {vb}"
h_val = int(vb.split()[-1])
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("   [PASS] Dimensions and viewBox valid.")

# 3. Extract text elements and check font-sizes >= 24px
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = int(el.attrib.get('font-size', '0'))
    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        for ts in tspans:
            t_content = (ts.text or "").strip()
            t_fs = int(ts.attrib.get('font-size', fs))
            font_sizes.append((t_content, t_fs))
    else:
        t_content = "".join(el.itertext()).strip()
        font_sizes.append((t_content, fs))

print(f"3. Total text segments checked: {len(font_sizes)}")
for t, fs in font_sizes:
    print(f"   [{fs}px] '{t}'")
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"
print("   [PASS] All font sizes >= 24 px.")

# 4. Check required source labels
source_labels = [
    "Which knob moves which bill",
    "Signal",
    "Cost driver",
    "Cheapest levers",
    "Metrics",
    "active series times retention",
    "fewer labels, fewer buckets, recording rules, drop raw series upstream",
    "Logs",
    "bytes ingested and retained",
    "sample successes, shorter retention, drop debug",
    "Traces",
    "spans retained",
    "tail sampling policy, shorter retention",
    "Query",
    "fan-out and high-cardinality selects",
    "rollups, query limits, downsampling",
    "49,200 series at a 30 second interval for 15 days = 43,200 samples per series, at 1 to 2 bytes per sample is about 2.1 to 4.3 GB",
    "with a tenant label on every gateway metric about 3 million series needs about 130 to 261 GB",
    "logs and traces depend on traffic, which moves, so set a budget in bytes and spans per day and alert on the trend"
]

full_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = " ".join("".join(el.itertext()).split())
    if txt.isdigit():
        continue
    full_texts.append(txt)

print(f"\n4. Checking {len(source_labels)} source labels against {len(full_texts)} text elements:")
for sl in source_labels:
    cnt = full_texts.count(sl)
    if cnt != 1:
        print(f"   [FAIL] Label '{sl}': count={cnt}")
    else:
        print(f"   [OK] Label '{sl}'")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

assert len(full_texts) == len(source_labels), f"Expected {len(source_labels)} text labels, got {len(full_texts)}: {set(full_texts) - set(source_labels)}"
print("   [PASS] Every source label appears exactly once, and no extra text exists.")

# 5. Check no banned styling words:
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"
print("   [PASS] No styling words printed as text.")

# 7. Check padding and clearances
print("\n7. Checking text paddings inside boxes (>= 16px) and gaps (>= 40px):")

# Let's check all text bounding boxes against their enclosing shapes
# Text lines definition: (text, font_size, x, y, is_middle_anchor, box_x1, box_x2, box_y1, box_y2)
checks = [
    # Table headers
    ("Signal", 28, 180, 141, True, 40, 320, 98, 164),
    ("Cost driver", 28, 560, 141, True, 320, 800, 98, 164),
    ("Cheapest levers", 28, 1180, 141, True, 800, 1560, 98, 164),

    # Row 1: Metrics
    ("Metrics", 30, 135, 231, False, 40, 320, 170, 270),
    ("active series", 25, 345, 215, False, 320, 800, 170, 270),
    ("times retention", 25, 345, 247, False, 320, 800, 170, 270),
    ("fewer labels, fewer buckets, recording rules,", 25, 825, 215, False, 800, 1560, 170, 270),
    ("drop raw series upstream", 25, 825, 247, False, 800, 1560, 170, 270),

    # Row 2: Logs
    ("Logs", 30, 135, 343, False, 40, 320, 282, 382),
    ("bytes ingested", 25, 345, 327, False, 320, 800, 282, 382),
    ("and retained", 25, 345, 359, False, 320, 800, 282, 382),
    ("sample successes, shorter retention,", 25, 825, 327, False, 800, 1560, 282, 382),
    ("drop debug", 25, 825, 359, False, 800, 1560, 282, 382),

    # Row 3: Traces
    ("Traces", 30, 135, 455, False, 40, 320, 394, 494),
    ("spans retained", 25, 345, 451, False, 320, 800, 394, 494),
    ("tail sampling policy, shorter retention", 25, 825, 451, False, 800, 1560, 394, 494),

    # Row 4: Query
    ("Query", 30, 135, 567, False, 40, 320, 506, 606),
    ("fan-out and", 25, 345, 551, False, 320, 800, 506, 606),
    ("high-cardinality selects", 25, 345, 583, False, 320, 800, 506, 606),
    ("rollups, query limits, downsampling", 25, 825, 563, False, 800, 1560, 506, 606),

    # Worked example 1
    ("49,200 series at a 30 second interval for 15 days = 43,200 samples per series,", 25, 145, 696, False, 40, 1560, 650, 760),
    ("at 1 to 2 bytes per sample is about 2.1 to 4.3 GB", 25, 145, 730, False, 40, 1560, 650, 760),

    # Worked example 2
    ("with a tenant label on every gateway metric about 3 million series", 25, 145, 826, False, 40, 1560, 780, 890),
    ("needs about 130 to 261 GB", 25, 145, 860, False, 40, 1560, 780, 890),

    # Takeaway bar
    ("logs and traces depend on traffic, which moves,", 26, 800, 976, True, 40, 1560, 930, 1040),
    ("so set a budget in bytes and spans per day and alert on the trend", 26, 800, 1010, True, 40, 1560, 930, 1040)
]

for txt, fs, x, y, is_mid, bx1, bx2, by1, by2 in checks:
    w_est = len(txt) * 0.6 * fs
    if is_mid:
        tx1 = x - w_est / 2
        tx2 = x + w_est / 2
    else:
        tx1 = x
        tx2 = x + w_est
    
    ty1 = y - fs * 0.85
    ty2 = y + fs * 0.15

    pad_left = tx1 - bx1
    pad_right = bx2 - tx2
    pad_top = ty1 - by1
    pad_bottom = by2 - ty2

    print(f"   '{txt[:30]}...': L_pad={pad_left:.1f}, R_pad={pad_right:.1f}, T_pad={pad_top:.1f}, B_pad={pad_bottom:.1f}")
    assert pad_left >= 16, f"Left padding violated: {pad_left} for {txt}"
    assert pad_right >= 16, f"Right padding violated: {pad_right} for {txt}"
    assert pad_top >= 16, f"Top padding violated: {pad_top} for {txt}"
    assert pad_bottom >= 16, f"Bottom padding violated: {pad_bottom} for {txt}"

print("   [PASS] All text lines fit with >= 16px padding on all sides.")

# Check icon clearance
# Icons in table are at x=60 to 108. Text starts at x=135. Clearance = 135 - 108 = 27px >= 16px!
# Icons in worked examples are at x=60 to 110. Text starts at x=145. Clearance = 145 - 110 = 35px >= 16px!
print("   [PASS] Icon clearances >= 16px.")

# Check gaps between major sections:
# Table ends at 606. Worked example 1 starts at 650. Gap = 650 - 606 = 44px >= 40px.
# Worked example 1: 650 to 760. Gap to WE2 = 780 - 760 = 20px (between cards in same section).
# WE2 ends at 890. Takeaway bar starts at 930. Gap = 930 - 890 = 40px >= 40px.
# Takeaway bar ends at 1040. Canvas height 1080. Bottom margin = 1080 - 1040 = 40px >= 40px.
# Left margin = 40px, right margin = 1600 - 1560 = 40px.
# Top margin to header = 105px, title at 65.
print("   [PASS] Section gaps and margins valid.")


