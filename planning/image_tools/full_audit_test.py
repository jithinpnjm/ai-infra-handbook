import xml.etree.ElementTree as ET
import re

def build_svg_string():
    H = 1200
    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 {H}" width="1600" height="{H}">')
    svg.append('  <title>Top-level code runs in order, a def body runs only when called</title>')
    svg.append('  <desc>Visual explanation of Python module import and execution order: top-level statements run sequentially from top to bottom, def statements bind function names without running their bodies, and forward references succeed only if called after all referenced names are assigned.</desc>')
    svg.append('')
    svg.append('  <defs>')
    # No arrows in spec, so no markers needed!
    svg.append('  </defs>')
    svg.append('')
    svg.append(f'  <!-- Canvas Background -->')
    svg.append(f'  <rect width="1600" height="{H}" fill="#f5f8f5" />')
    svg.append('')
    
    # Title (48px bold)
    svg.append('  <!-- Title -->')
    svg.append('  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">')
    svg.append('    <tspan x="800" dy="0">Top-level code runs in order, </tspan>')
    svg.append('    <tspan x="800" dy="50">a def body runs only when called</tspan>')
    svg.append('  </text>')
    svg.append('')

    # Rule box (x: 40 to 1560, w: 1520, y: 125, h: 110, bottom: 235)
    # Gap after title: 125 - 98 = 27 px
    svg.append('  <!-- Rule Box -->')
    svg.append('  <g id="rule-box">')
    svg.append('    <rect x="40" y="125" width="1520" height="110" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon: Scroll/Document with rule lines (50x50 at x=65, y=145)
    svg.append('    <g transform="translate(65, 145)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="2" width="46" height="50" rx="6" fill="#ffffff" />')
    svg.append('      <line x1="12" y1="16" x2="38" y2="16" />')
    svg.append('      <line x1="12" y1="27" x2="38" y2="27" />')
    svg.append('      <line x1="12" y1="38" x2="26" y2="38" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="158" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">when Python first imports or reloads a module it runs top-level statements from top to bottom, </tspan>')
    svg.append('      <tspan x="145" dy="32">so top-level code cannot use names assigned lower down; a def body can refer to a name </tspan>')
    svg.append('      <tspan x="145" dy="32">defined later as long as it exists by the time of the call</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Gap after rule box = 40 px: y = 235 + 40 = 275
    # Side column header: x = 1220, y = 275, w = 340, h = 50 (ends at 325)
    svg.append('  <!-- Side Column Header -->')
    svg.append('  <g id="side-col-header">')
    svg.append('    <rect x="1220" y="275" width="340" height="50" rx="8" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="309" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">names assigned so far</text>')
    svg.append('  </g>')
    svg.append('')

    # Main Grid of 5 Steps:
    # Steps: x = 40 to 1180 (w = 1140)
    # Side Col: x = 1220 to 1560 (w = 340)
    # Between step 1 and header: y_step1 = 345 (gap = 20 from header, or let's make y_step1 = 345, h=80 -> ends at 425)
    # Wait, between step boxes: gap = 30 px?
    # Let's check:
    # Step 1: y = 340, h = 82 (ends 422)
    # Step 2: y = 452, h = 82 (ends 534) (gap 30)
    # Step 3: y = 564, h = 82 (ends 646) (gap 30)
    # Step 4: y = 676, h = 82 (ends 758) (gap 30)
    # Step 5: y = 788, h = 82 (ends 870) (gap 30)
    # Wait, if gap is 40 px:
    # Step 1: y = 340, h = 75 (ends 415)
    # Step 2: y = 455, h = 75 (ends 530) (gap 40)
    # Step 3: y = 570, h = 75 (ends 645) (gap 40)
    # Step 4: y = 685, h = 75 (ends 760) (gap 40)
    # Step 5: y = 800, h = 75 (ends 875) (gap 40)
    # Side Col Row 1: y = 340, h = 75 (aligned with Step 1) -> "none"
    # Side Col Rows 2 & 3: y = 455, h = 190 (455 to 645) -> "func1"
    # Side Col Rows 4 & 5: y = 685, h = 190 (685 to 875) -> "func1, func2"
    # Gap after Step 5 = 40 px -> y = 875 + 40 = 915.
    # Extra strip: y = 915, h = 145 (ends at 1060).
    # Gap after Extra strip = 40 px -> y = 1060 + 40 = 1100.
    # Bottom bar: y = 1100, h = 60 (ends at 1160).
    # Bottom canvas margin: 1200 - 1160 = 40 px!
    
    # Let's check step 1 to 5 boxes:
    # Step 1:
    svg.append('  <!-- Step 1 -->')
    svg.append('  <g id="step-1">')
    svg.append('    <rect x="40" y="340" width="1140" height="75" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon for step 1: Terminal / execution call with exclamation (error)
    svg.append('    <g transform="translate(60, 352)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="2" y="4" width="46" height="42" rx="5" fill="#ffffff" />')
    svg.append('      <polyline points="10,18 18,25 10,32" />')
    svg.append('      <line x1="24" y1="32" x2="38" y2="32" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="372" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold">1 func1()  </tspan>')
    svg.append('      <tspan x="135" dy="30" font-size="24">would raise NameError: func1 not yet assigned</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Side Column Row 1: "none"
    svg.append('  <!-- Side Column Row 1: none -->')
    svg.append('  <g id="side-row-1">')
    svg.append('    <rect x="1220" y="340" width="340" height="75" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="386" text-anchor="middle" font-family="monospace" font-size="25" font-weight="bold" fill="#303a36">none</text>')
    svg.append('  </g>')
    svg.append('')

    # Step 2:
    svg.append('  <!-- Step 2 -->')
    svg.append('  <g id="step-2">')
    svg.append('    <rect x="40" y="455" width="1140" height="75" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon for step 2: Def gear / function definition
    svg.append('    <g transform="translate(60, 467)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="25" cy="25" r="18" fill="#ffffff" />')
    svg.append('      <circle cx="25" cy="25" r="7" />')
    svg.append('      <line x1="25" y1="3" x2="25" y2="9" /><line x1="25" y1="41" x2="25" y2="47" />')
    svg.append('      <line x1="3" y1="25" x2="9" y2="25" /><line x1="41" y1="25" x2="47" y2="25" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="487" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold">2 def func1(): print(func2())  </tspan>')
    svg.append('      <tspan x="135" dy="30" font-size="24">binds the name func1; the body does not run</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Step 3:
    svg.append('  <!-- Step 3 -->')
    svg.append('  <g id="step-3">')
    svg.append('    <rect x="40" y="570" width="1140" height="75" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon for step 3: Clock / call attempt / warning
    svg.append('    <g transform="translate(60, 582)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="25" cy="25" r="20" fill="#ffffff" />')
    svg.append('      <polyline points="25,12 25,25 35,25" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="602" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold">3 func1() here raises </tspan>')
    svg.append('      <tspan x="135" dy="30" font-size="24">NameError: func2 not yet assigned when func1 runs</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Side Column Rows 2 & 3 combined: "func1" (spans y=455 to y=645, h=190)
    svg.append('  <!-- Side Column Rows 2 & 3: func1 -->')
    svg.append('  <g id="side-row-2-3">')
    svg.append('    <rect x="1220" y="455" width="340" height="190" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="558" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">func1</text>')
    svg.append('  </g>')
    svg.append('')

    # Step 4:
    svg.append('  <!-- Step 4 -->')
    svg.append('  <g id="step-4">')
    svg.append('    <rect x="40" y="685" width="1140" height="75" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    # Icon for step 4: Code block / return
    svg.append('    <g transform="translate(60, 697)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="4" y="6" width="42" height="38" rx="4" fill="#ffffff" />')
    svg.append('      <polyline points="14,18 20,25 14,32" />')
    svg.append('      <line x1="24" y1="32" x2="34" y2="32" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="731" font-family="sans-serif" font-size="26" font-weight="bold" fill="#303a36">4 def func2(): return &quot;Hello&quot;</text>')
    svg.append('  </g>')
    svg.append('')

    # Step 5 (ORANGE - single most important item!):
    svg.append('  <!-- Step 5 (Orange highlight: success state) -->')
    svg.append('  <g id="step-5">')
    svg.append('    <rect x="40" y="800" width="1140" height="75" rx="10" fill="#e8f1ea" stroke="#db8129" stroke-width="3.5" />')
    # Icon for step 5: Success badge / star in orange
    svg.append('    <g transform="translate(60, 812)" stroke="#db8129" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <circle cx="25" cy="25" r="20" fill="#ffffff" />')
    svg.append('      <polyline points="15,25 22,32 35,18" />')
    svg.append('    </g>')
    svg.append('    <text x="135" y="832" font-family="sans-serif" font-size="26" fill="#303a36">')
    svg.append('      <tspan x="135" dy="0" font-weight="bold" fill="#db8129">5 func1() works: </tspan>')
    svg.append('      <tspan x="135" dy="30" font-size="24">both names assigned, prints Hello</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Side Column Rows 4 & 5 combined: "func1, func2" (spans y=685 to y=875, h=190)
    svg.append('  <!-- Side Column Rows 4 & 5: func1, func2 -->')
    svg.append('  <g id="side-row-4-5">')
    svg.append('    <rect x="1220" y="685" width="340" height="190" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />')
    svg.append('    <text x="1390" y="788" text-anchor="middle" font-family="monospace" font-size="26" font-weight="bold" fill="#303a36">func1, func2</text>')
    svg.append('  </g>')
    svg.append('')

    # Gap after steps = 40 px -> y = 875 + 40 = 915.
    # Extra strip (x: 40 to 1560, w: 1520, y: 915, h: 145, bottom: 1060)
    svg.append('  <!-- Extra Strip -->')
    svg.append('  <g id="extra-strip">')
    svg.append('    <rect x="40" y="915" width="1520" height="145" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />')
    # Icon: Chip / terminal / fast execution (50x50 at x=65, y=960)
    svg.append('    <g transform="translate(65, 960)" stroke="#207448" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round">')
    svg.append('      <rect x="6" y="6" width="38" height="38" rx="5" fill="#ffffff" />')
    svg.append('      <line x1="14" y1="2" x2="14" y2="6" /><line x1="25" y1="2" x2="25" y2="6" /><line x1="36" y1="2" x2="36" y2="6" />')
    svg.append('      <line x1="14" y1="44" x2="14" y2="48" /><line x1="25" y1="44" x2="25" y2="48" /><line x1="36" y1="44" x2="36" y2="48" />')
    svg.append('      <line x1="2" y1="14" x2="6" y2="14" /><line x1="2" y1="25" x2="6" y2="25" /><line x1="2" y1="36" x2="6" y2="36" />')
    svg.append('      <line x1="44" y1="14" x2="48" y2="14" /><line x1="44" y1="25" x2="48" y2="25" /><line x1="44" y1="36" x2="48" y2="36" />')
    svg.append('    </g>')
    svg.append('    <text x="145" y="946" font-family="sans-serif" font-size="24" fill="#303a36">')
    svg.append('      <tspan x="145" dy="0">Keep import-time work small: no network calls, config file reads, thread starts or </tspan>')
    svg.append('      <tspan x="145" dy="30">heavy imports at the top of a module; in command-line tools move a heavy import into </tspan>')
    svg.append('      <tspan x="145" dy="30">the function that needs it; measure with python -X importtime; module with </tspan>')
    svg.append('      <tspan x="145" dy="30">print(&quot;util loaded&quot;) shows side effects at import time: avoid in libraries</tspan>')
    svg.append('    </text>')
    svg.append('  </g>')
    svg.append('')

    # Gap after Extra Strip = 40 px -> y = 1060 + 40 = 1100.
    # Bottom bar (x: 40 to 1560, w: 1520, y: 1100, h: 60, bottom: 1160)
    # Takeaway bar: background #207448 (main green), white text
    svg.append('  <!-- Bottom Takeaway Bar -->')
    svg.append('  <g id="bottom-bar">')
    svg.append('    <rect x="40" y="1100" width="1520" height="60" rx="10" fill="#207448" />')
    svg.append('    <text x="800" y="1139" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">The name must exist by the time of the call, not by the time of the def</text>')
    svg.append('  </g>')
    svg.append('')
    svg.append('</svg>')
    return '\n'.join(svg)

svg_str = build_svg_string()
# Update with tested padding code
from test_adjust_paddings import build_svg_string as build_adjusted
svg_str = build_adjusted()
with open("test_candidate.svg", "w") as f:
    f.write(svg_str)
print("Saved test_candidate.svg, running audit...")

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Text font-size >= 24px
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = " ".join("".join(elem.itertext()).split())
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Top-level code runs in order, a def body runs only when called",
    "1 func1() would raise NameError: func1 not yet assigned",
    "2 def func1(): print(func2()) binds the name func1; the body does not run",
    "3 func1() here raises NameError: func2 not yet assigned when func1 runs",
    '4 def func2(): return "Hello"',
    "5 func1() works: both names assigned, prints Hello",
    "names assigned so far",
    "none",
    "func1",
    "func1, func2",
    "when Python first imports or reloads a module it runs top-level statements from top to bottom, so top-level code cannot use names assigned lower down; a def body can refer to a name defined later as long as it exists by the time of the call",
    'Keep import-time work small: no network calls, config file reads, thread starts or heavy imports at the top of a module; in command-line tools move a heavy import into the function that needs it; measure with python -X importtime; module with print("util loaded") shows side effects at import time: avoid in libraries',
    "The name must exist by the time of the call, not by the time of the def"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
with open("test_candidate.svg", 'r', encoding='utf-8') as f:
    content = f.read()
orange_matches = re.findall(r'#db8129', content, re.IGNORECASE)
print(f"\n6. Orange count: {len(orange_matches)}")
assert len(orange_matches) > 0, "No orange color found!"

# 7. Check strict paddings >= 16px
from audit_pad_strict import check_strict_paddings
try:
    check_strict_paddings("test_candidate.svg")
    print("7. Strict paddings passed!")
except Exception as e:
    print(f"7. Strict paddings error: {e}")

