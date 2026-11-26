import xml.etree.ElementTree as ET
import re

svg_code = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1080" width="1600" height="1080">
  <title>Turning an Xid code into ignore, suspect or drain</title>
  <desc>Flowchart showing the fleet policy for handling NVIDIA GPU Xid errors by catalog action and repeat frequency into ignore, suspect, or drain.</desc>

  <defs>
    <!-- Proportional green arrowhead (18px) -->
    <marker id="arrow-green" viewBox="0 0 18 18" refX="16" refY="9" markerUnits="userSpaceOnUse" markerWidth="18" markerHeight="18" orient="auto">
      <path d="M 2 3 L 16 9 L 2 15 Z" fill="#207448"/>
    </marker>
    <!-- Arrow 8 definition without orange marker if not needed, or keep marker -->
  </defs>

  <!-- Background -->
  <rect width="1600" height="1080" fill="#f5f8f5"/>

  <!-- ==================== TITLE ==================== -->
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">Turning an Xid code into ignore, suspect or drain</text>

  <!-- ==================== START BOX ==================== -->
  <g id="start-box">
    <rect x="715" y="90" width="540" height="80" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Small chip icon (56px, stroke 4, #207448) -->
    <g transform="translate(735, 102)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="10" y="10" width="36" height="36" rx="4"/>
      <line x1="18" y1="4" x2="18" y2="10"/>
      <line x1="28" y1="4" x2="28" y2="10"/>
      <line x1="38" y1="4" x2="38" y2="10"/>
      <line x1="18" y1="46" x2="18" y2="52"/>
      <line x1="28" y1="46" x2="28" y2="52"/>
      <line x1="38" y1="46" x2="38" y2="52"/>
      <line x1="4" y1="18" x2="10" y2="18"/>
      <line x1="4" y1="28" x2="10" y2="28"/>
      <line x1="4" y1="38" x2="10" y2="38"/>
      <line x1="46" y1="18" x2="52" y2="18"/>
      <line x1="46" y1="28" x2="52" y2="28"/>
      <line x1="46" y1="38" x2="52" y2="38"/>
    </g>
    <text x="1030" y="141" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Xid reported on a node</text>
  </g>

  <!-- Arrow 1: Start box -> Step 1 -->
  <line x1="985" y1="170" x2="985" y2="218" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- ==================== STEP 1 DECISION ==================== -->
  <g id="step-1">
    <!-- Number circle 1 -->
    <circle cx="660" cy="260" r="24" fill="#207448"/>
    <text x="660" y="269" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">1</text>

    <!-- Step 1 Box -->
    <rect x="715" y="220" width="540" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Catalog icon -->
    <g transform="translate(735, 232)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="8" width="40" height="40" rx="4"/>
      <line x1="16" y1="18" x2="36" y2="18"/>
      <line x1="16" y1="28" x2="36" y2="28"/>
      <line x1="16" y1="38" x2="28" y2="38"/>
    </g>
    <text x="1030" y="271" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Code in the catalog?</text>
  </g>

  <!-- Arrow 2: Step 1 (If no) -> Suspect -->
  <path d="M 715 260 L 200 260 L 200 518" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 3: Step 1 (If yes) -> Step 2 -->
  <line x1="985" y1="300" x2="985" y2="348" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- ==================== STEP 2 DECISION ==================== -->
  <g id="step-2">
    <!-- Number circle 2 -->
    <circle cx="660" cy="390" r="24" fill="#207448"/>
    <text x="660" y="399" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">2</text>

    <!-- Step 2 Box -->
    <rect x="715" y="350" width="540" height="80" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Gear icon -->
    <g transform="translate(735, 362)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="10"/>
      <path d="M 28 8 L 28 14 M 28 42 L 28 48 M 8 28 L 14 28 M 42 28 L 48 28 M 14 14 L 18 18 M 38 38 L 42 42 M 14 42 L 18 38 M 38 18 L 42 14"/>
    </g>
    <text x="1030" y="401" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">Catalog action</text>
  </g>

  <!-- ==================== SUSPECT BOX (COLUMN 1) ==================== -->
  <g id="suspect-node">
    <rect x="40" y="520" width="320" height="200" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Shield/alert icon -->
    <g transform="translate(172, 538)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 12 10 L 28 4 L 44 10 C 44 32 28 48 28 48 C 28 48 12 32 12 10 Z"/>
      <line x1="28" y1="18" x2="28" y2="30"/>
      <circle cx="28" cy="37" r="1.5" fill="#207448"/>
    </g>
    <text x="200" y="628" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">Suspect</text>
    <text x="200" y="675" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="200" dy="0">never ignore an</tspan>
      <tspan x="200" dy="30">unknown code</tspan>
    </text>
  </g>

  <!-- ==================== BRANCH B: RESTART_APP & REPEAT DECISION (COLUMN 2) ==================== -->
  <!-- Arrow 5: Step 2 -> Repeat Decision -->
  <path d="M 780 430 L 780 455 L 440 455 L 440 568" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Branch B Badge beside Arrow 5 -->
  <rect x="460" y="465" width="280" height="85" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="600" y="500" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="600" dy="0" font-weight="bold" fill="#207448">application-level, RESTART_APP</tspan>
    <tspan x="600" dy="30">(for example Xid 13, 31, 94)</tspan>
  </text>

  <!-- Repeat Decision Box -->
  <g id="repeat-decision">
    <rect x="400" y="570" width="340" height="150" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Timer/Clock icon -->
    <g transform="translate(420, 582)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="24" cy="24" r="20"/>
      <polyline points="24,10 24,24 34,24"/>
    </g>
    <text x="580" y="628" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
      <tspan x="580" dy="0">Same code three</tspan>
      <tspan x="580" dy="32">times within an hour</tspan>
      <tspan x="580" dy="32">on this node?</tspan>
    </text>
  </g>

  <!-- Memory note beside Repeat Decision -->
  <g id="memory-note">
    <rect x="755" y="605" width="260" height="90" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2" stroke-dasharray="6 4"/>
    <!-- Memory RAM chip icon -->
    <g transform="translate(770, 622)" stroke="#207448" stroke-width="3" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="10" width="48" height="28" rx="3"/>
      <rect x="10" y="16" width="7" height="10" fill="#e8f1ea"/>
      <rect x="21" y="16" width="7" height="10" fill="#e8f1ea"/>
      <rect x="32" y="16" width="7" height="10" fill="#e8f1ea"/>
      <rect x="43" y="16" width="5" height="10" fill="#e8f1ea"/>
      <line x1="12" y1="38" x2="12" y2="44"/>
      <line x1="20" y1="38" x2="20" y2="44"/>
      <line x1="28" y1="38" x2="28" y2="44"/>
      <line x1="36" y1="38" x2="36" y2="44"/>
      <line x1="44" y1="38" x2="44" y2="44"/>
    </g>
    <text x="910" y="645" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="910" dy="0">recent Xid times</tspan>
      <tspan x="910" dy="30">kept per node</tspan>
    </text>
  </g>

  <!-- Arrow 6: Repeat Decision (If no) -> Suspect -->
  <line x1="400" y1="620" x2="362" y2="620" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Arrow 7: Repeat Decision (If yes) -> Drain -->
  <line x1="570" y1="720" x2="570" y2="778" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Drain Outcome Box -->
  <g id="drain-box">
    <rect x="440" y="780" width="260" height="110" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5"/>
    <!-- Drain/Exit icon -->
    <g transform="translate(460, 807)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 8 12 L 28 32 L 48 12"/>
      <line x1="28" y1="4" x2="28" y2="44"/>
      <line x1="12" y1="50" x2="44" y2="50"/>
    </g>
    <text x="600" y="848" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#303a36">Drain</text>
  </g>

  <!-- ==================== BRANCH A: IGNORE (COLUMN 3) ==================== -->
  <!-- Arrow 4: Step 2 -> Ignore -->
  <path d="M 1030 430 L 1030 455 L 1150 455 L 1150 778" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Branch A Badge beside Arrow 4 -->
  <rect x="1040" y="525" width="240" height="85" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="1160" y="560" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1160" dy="0" font-weight="bold" fill="#207448">IGNORE</tspan>
    <tspan x="1160" dy="30">(for example Xid 43, 63)</tspan>
  </text>

  <!-- Ignore Outcome Box (Green box) -->
  <g id="ignore-box">
    <rect x="1040" y="780" width="240" height="110" rx="14" fill="#e8f1ea" stroke="#207448" stroke-width="2.5"/>
    <!-- Pass/Check icon -->
    <g transform="translate(1060, 807)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="28" cy="28" r="22"/>
      <path d="M 18 28 L 25 35 L 38 21"/>
    </g>
    <text x="1180" y="848" text-anchor="middle" font-family="sans-serif" font-size="34" font-weight="bold" fill="#207448">Ignore</text>
  </g>

  <!-- ==================== BRANCH C: RESET/REBOOT/LINK (COLUMN 4) ==================== -->
  <!-- Arrow 8: Step 2 -> Drain at once -->
  <path d="M 1180 430 L 1180 455 L 1440 455 L 1440 778" fill="none" stroke="#207448" stroke-width="4" marker-end="url(#arrow-green)"/>

  <!-- Branch C Badge beside Arrow 8 -->
  <rect x="1310" y="515" width="260" height="115" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="1440" y="550" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="1440" dy="0" font-weight="bold" fill="#207448">reset, reboot or link</tspan>
    <tspan x="1440" dy="30">(for example Xid 48, 64,</tspan>
    <tspan x="1440" dy="30">79, 95, 119, 120, 74)</tspan>
  </text>

  <!-- Drain at once Outcome Box (Single orange highlight box) -->
  <g id="drain-at-once-box">
    <rect x="1320" y="780" width="250" height="110" rx="14" fill="#fff9f2" stroke="#db8129" stroke-width="3"/>
    <text x="1445" y="848" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#db8129">Drain at once</text>
  </g>

  <!-- ==================== GREEN TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="945" width="1520" height="100" rx="14" fill="#207448"/>
    <text x="800" y="988" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">
      <tspan x="800" dy="0">Translate the catalog into ignore, suspect and drain,</tspan>
      <tspan x="800" dy="34">and never ignore a code you do not recognise.</tspan>
    </text>
  </g>
</svg>'''

with open("test_xid_candidate.svg", "w") as f:
    f.write(svg_code)

print("Saved test_xid_candidate.svg")

tree = ET.parse("test_xid_candidate.svg")
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
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
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
    "Turning an Xid code into ignore, suspect or drain",
    "Xid reported on a node",
    "Code in the catalog?",
    "Catalog action",
    "IGNORE (for example Xid 43, 63)",
    "Ignore",
    "application-level, RESTART_APP (for example Xid 13, 31, 94)",
    "Same code three times within an hour on this node?",
    "Drain",
    "reset, reboot or link (for example Xid 48, 64, 79, 95, 119, 120, 74)",
    "Drain at once",
    "Suspect",
    "never ignore an unknown code",
    "recent Xid times kept per node",
    "Translate the catalog into ignore, suspect and drain, and never ignore a code you do not recognise."
]

step_numbers = {"1", "2"}
found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts (non-step): {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number {num} count is {cnt} != 1!"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (PASS)")

# 6. Check orange #db8129 occurrences
svg_str = open("test_xid_candidate.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 8, f"Expected exactly 8 arrows, got {total_arrows}"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")

