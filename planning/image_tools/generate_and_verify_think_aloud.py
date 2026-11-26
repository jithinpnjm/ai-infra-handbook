import xml.etree.ElementTree as ET
import re

svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <title>The seven-step think-aloud script</title>
  <desc>A vertical sequence of seven numbered steps for technical interviews with an orange-highlighted plan step, right-hand note panel for console and incident rounds, and a bottom practice takeaway.</desc>

  <!-- Background -->
  <rect width="1600" height="1200" fill="#f5f8f5" />

  <!-- Canvas Title (48px bold) -->
  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">The seven-step think-aloud script</text>

  <!-- ==================== LEFT COLUMN: SEVEN STEPS ==================== -->
  <!-- Step 1: Restate the problem in one sentence -->
  <g id="step-1">
    <rect x="40" y="110" width="1020" height="116" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="85" cy="168" r="24" fill="#207448" />
    <text x="85" y="177" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">1</text>
    <g transform="translate(125, 143)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 5 8 H 45 A 3 3 0 0 1 48 11 V 33 A 3 3 0 0 1 45 36 H 20 L 10 44 V 36 H 5 A 3 3 0 0 1 2 33 V 11 A 3 3 0 0 1 5 8 Z" />
      <line x1="12" y1="18" x2="38" y2="18" />
      <line x1="12" y1="26" x2="28" y2="26" />
    </g>
    <text x="196" y="158" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Restate the problem in one sentence</text>
    <text x="196" y="200" font-family="monospace" font-size="24" fill="#303a36">So the input is, the output is, and the limit is</text>
  </g>

  <!-- Step 2: Ask two clarifying questions -->
  <g id="step-2">
    <rect x="40" y="249" width="1020" height="116" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="85" cy="307" r="24" fill="#207448" />
    <text x="85" y="316" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">2</text>
    <g transform="translate(125, 282)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="25" cy="25" r="21" />
      <path d="M 18 17 C 18 11 32 11 32 18 C 32 23 25 24 25 29" />
      <circle cx="25" cy="36" r="1.5" fill="#207448" />
    </g>
    <text x="196" y="297" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Ask two clarifying questions</text>
    <text x="196" y="339" font-family="sans-serif" font-size="24" fill="#303a36">Can the input be empty? What size should I plan for?</text>
  </g>

  <!-- Step 3: Say your plan before you act (ORANGE OUTLINE) -->
  <g id="step-3">
    <rect x="40" y="388" width="1020" height="116" rx="14" fill="#ffffff" stroke="#db8129" stroke-width="4" />
    <circle cx="85" cy="446" r="24" fill="#207448" />
    <text x="85" y="455" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">3</text>
    <g transform="translate(125, 421)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="8" y="10" width="34" height="36" rx="4" />
      <path d="M 17 10 V 6 A 2 2 0 0 1 19 4 H 31 A 2 2 0 0 1 33 6 V 10" />
      <line x1="15" y1="20" x2="35" y2="20" />
      <line x1="15" y1="28" x2="35" y2="28" />
      <line x1="15" y1="36" x2="27" y2="36" />
    </g>
    <text x="196" y="436" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Say your plan before you act</text>
    <text x="196" y="478" font-family="sans-serif" font-size="24" fill="#303a36">My first approach is X. It costs about Y.</text>
  </g>

  <!-- Step 4: Work in small steps and name each one -->
  <g id="step-4">
    <rect x="40" y="527" width="1020" height="116" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="85" cy="585" r="24" fill="#207448" />
    <text x="85" y="594" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">4</text>
    <g transform="translate(125, 560)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 6 42 H 18 V 30 H 30 V 18 H 42 V 6" />
      <line x1="6" y1="42" x2="42" y2="42" />
    </g>
    <text x="196" y="575" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Work in small steps and name each one</text>
    <text x="196" y="617" font-family="sans-serif" font-size="24" fill="#303a36">Now I am parsing the line. Next I will count.</text>
  </g>

  <!-- Step 5: Check as you go -->
  <g id="step-5">
    <rect x="40" y="666" width="1020" height="116" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="85" cy="724" r="24" fill="#207448" />
    <text x="85" y="733" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">5</text>
    <g transform="translate(125, 699)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <path d="M 25 6 L 42 12 V 24 C 42 34 35 41 25 44 C 15 41 8 34 8 24 V 12 Z" />
      <polyline points="16,24 22,30 34,18" />
    </g>
    <text x="196" y="714" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Check as you go</text>
    <text x="196" y="756" font-family="sans-serif" font-size="24" fill="#303a36">Let me test this on a small example.</text>
  </g>

  <!-- Step 6: Review at the end -->
  <g id="step-6">
    <rect x="40" y="805" width="1020" height="116" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="85" cy="863" r="24" fill="#207448" />
    <text x="85" y="872" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">6</text>
    <g transform="translate(125, 838)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="20" cy="20" r="14" />
      <line x1="30" y1="30" x2="43" y2="43" stroke-width="4.5" />
      <line x1="13" y1="20" x2="27" y2="20" />
    </g>
    <text x="196" y="853" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Review at the end</text>
    <text x="196" y="895" font-family="sans-serif" font-size="24" fill="#303a36">Let me read it once for off-by-one errors and empty input.</text>
  </g>

  <!-- Step 7: Offer an alternative -->
  <g id="step-7">
    <rect x="40" y="944" width="1020" height="116" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2.5" />
    <circle cx="85" cy="1002" r="24" fill="#207448" />
    <text x="85" y="1011" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">7</text>
    <g transform="translate(125, 977)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <line x1="25" y1="44" x2="25" y2="26" />
      <path d="M 25 26 C 25 18 12 16 12 10 V 5" />
      <path d="M 25 26 C 25 18 38 16 38 10 V 5" />
      <circle cx="12" cy="5" r="2.5" fill="#207448" />
      <circle cx="38" cy="5" r="2.5" fill="#207448" />
    </g>
    <text x="196" y="992" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Offer an alternative</text>
    <text x="196" y="1034" font-family="sans-serif" font-size="24" fill="#303a36">A different way is Z, which trades memory for speed.</text>
  </g>

  <!-- ==================== RIGHT COLUMN: NOTE PANEL ==================== -->
  <g id="right-panel">
    <rect x="1100" y="110" width="460" height="950" rx="16" fill="#e8f1ea" stroke="#207448" stroke-width="2.5" />
    
    <!-- Panel Title -->
    <text x="1330" y="166" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">Same steps, other rounds</text>

    <!-- Sub-card 1: Console -->
    <rect x="1120" y="200" width="420" height="400" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(1305, 220)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <rect x="4" y="6" width="42" height="34" rx="4" />
      <polyline points="14,18 21,23 14,28" />
      <line x1="25" y1="28" x2="36" y2="28" />
    </g>
    <text x="1330" y="300" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1330" dy="0">Console: state the</tspan>
      <tspan x="1330" dy="44">symptom, say what you</tspan>
      <tspan x="1330" dy="44">will check first, run</tspan>
      <tspan x="1330" dy="44">one command, say what</tspan>
      <tspan x="1330" dy="44">the output means, name</tspan>
      <tspan x="1330" dy="44">the next hypothesis.</tspan>
    </text>

    <!-- Sub-card 2: Incident -->
    <rect x="1120" y="630" width="420" height="400" rx="14" fill="#ffffff" stroke="#207448" stroke-width="2" />
    <g transform="translate(1305, 660)" stroke="#207448" stroke-width="3.5" fill="none" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="25,5 45,41 5,41" />
      <line x1="25" y1="17" x2="25" y2="28" />
      <circle cx="25" cy="35" r="1.5" fill="#207448" />
    </g>
    <text x="1330" y="756" text-anchor="middle" font-family="sans-serif" font-size="24" fill="#303a36">
      <tspan x="1330" dy="0">Incident: step 3 says</tspan>
      <tspan x="1330" dy="46">what you will do to</tspan>
      <tspan x="1330" dy="46">protect users before</tspan>
      <tspan x="1330" dy="46">you know the cause.</tspan>
    </text>
  </g>

  <!-- ==================== BOTTOM TAKEAWAY BAR ==================== -->
  <g id="takeaway-bar">
    <rect x="40" y="1100" width="1520" height="60" rx="12" fill="#207448" />
    <text x="800" y="1140" text-anchor="middle" font-family="sans-serif" font-size="28" font-weight="bold" fill="#ffffff">Practise until the sentences are boring.</text>
  </g>
</svg>"""

with open("candidate_think_aloud.svg", "w") as f:
    f.write(svg_content)

print("SVG written to candidate_think_aloud.svg")

# Now verify candidate_think_aloud.svg
tree = ET.parse("candidate_think_aloud.svg")
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
    "The seven-step think-aloud script",
    "Restate the problem in one sentence",
    "So the input is, the output is, and the limit is",
    "Ask two clarifying questions",
    "Can the input be empty? What size should I plan for?",
    "Say your plan before you act",
    "My first approach is X. It costs about Y.",
    "Work in small steps and name each one",
    "Now I am parsing the line. Next I will count.",
    "Check as you go",
    "Let me test this on a small example.",
    "Review at the end",
    "Let me read it once for off-by-one errors and empty input.",
    "Offer an alternative",
    "A different way is Z, which trades memory for speed.",
    "Same steps, other rounds",
    "Console: state the symptom, say what you will check first, run one command, say what the output means, name the next hypothesis.",
    "Incident: step 3 says what you will do to protect users before you know the cause.",
    "Practise until the sentences are boring."
]

step_numbers = {"1", "2", "3", "4", "5", "6", "7"}
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
print(f"\nExtras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"

for s in step_numbers:
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number {s} count {cnt} != 1!"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = open("candidate_think_aloud.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str
print("8. All required colors present! (PASS)")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
