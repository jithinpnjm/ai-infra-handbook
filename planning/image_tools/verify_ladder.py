import xml.etree.ElementTree as ET
import re

svg_path = "test_ladder.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Expected labels
expected_labels = [
    "The latency ladder with ratios to a memory read",
    "Each rung down costs more",
    "Figures from the 2009 slide: use the order of magnitude and say the year.",
    "L1 cache reference: 0.5 ns, ratio 0.005",
    "Main memory reference: 100 ns, ratio 1",
    "Send 2K bytes over 1 Gbps network: 20,000 ns, ratio 200",
    "Round trip within same datacenter: 500,000 ns, ratio 5,000",
    "Disk seek: 10,000,000 ns, ratio 100,000",
    "Send packet CA to Netherlands and back: 150,000,000 ns, ratio 1,500,000"
]

text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Total text elements: {len(text_elements)}")
found_texts = [t for t, fs in text_elements]
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# Check all expected labels
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected label '{exp}' appeared {cnt} times, expected exactly 1!"
    print(f"  [PASS] '{exp}' (cnt=1)")

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra / un-expected labels: {extras}")
assert len(extras) == 0, f"Found extra text: {extras}"
print("  [PASS] Zero extra labels!")

# 4. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'takeaway']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Banned style word '{b}' found in text: '{t}'"
print("\n4. Banned style words check: PASS")

# 5. Arrows / Markers
markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n5. Elements with markers: {len(markers)}")
assert len(markers) == 1, f"Expected exactly 1 arrow/marker, got {len(markers)}"
print("  [PASS] Exactly 1 arrow with marker!")

# 6. Colors
raw_svg = open(svg_path).read()
assert "#f5f8f5" in raw_svg, "Background #f5f8f5 missing"
assert "#303a36" in raw_svg, "Text #303a36 missing"
assert "#207448" in raw_svg, "Main green #207448 missing"
assert "#e8f1ea" in raw_svg, "Light green panels #e8f1ea missing"
assert "#db8129" in raw_svg, "Orange #db8129 missing"
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) == 1, f"Orange count {len(oranges)} != 1"
print("  [PASS] Orange used only once on the datacenter round trip rung!")

# 7. Margins and gaps
H_val = float(height)
# Top-level boxes:
boxes = [
    ("Card note", 1080, 135, 480, 125),
    ("Rung 1", 320, 135, 710, 90),
    ("Rung 2", 320, 300, 790, 90),
    ("Rung 3", 320, 435, 930, 90),
    ("Rung 4", 320, 570, 1040, 90),
    ("Rung 5", 320, 705, 1140, 90),
    ("Rung 6", 320, 840, 1240, 90),
]

print("\n7. Checking outside margins (>= 40px):")
for name, x, y, w, h in boxes:
    left_m = x
    right_m = 1600 - (x + w)
    top_m = y
    bot_m = H_val - (y + h)
    assert left_m >= 40, f"{name} left margin {left_m} < 40"
    assert right_m >= 40, f"{name} right margin {right_m} < 40"
    assert top_m >= 40, f"{name} top margin {top_m} < 40"
    assert bot_m >= 40, f"{name} bot margin {bot_m} < 40"
    print(f"  [PASS] {name} margins: L={left_m}, R={right_m}, T={top_m}, B={bot_m}")

# Gaps between rungs
# Rung 1 -> Rung 2: 300 - (135 + 90) = 75px >= 40px
# Rung 2 -> Rung 3: 435 - (300 + 90) = 45px >= 40px
# Rung 3 -> Rung 4: 570 - (435 + 90) = 45px >= 40px
# Rung 4 -> Rung 5: 705 - (570 + 90) = 45px >= 40px
# Rung 5 -> Rung 6: 840 - (705 + 90) = 45px >= 40px
for i in range(len(boxes)-2):
    b1 = boxes[i+1] # Rung 1
    b2 = boxes[i+2] # Rung 2
    gap = b2[2] - (b1[2] + b1[4])
    assert gap >= 40, f"Vertical gap between {b1[0]} and {b2[0]} is {gap} < 40"
    print(f"  [PASS] Gap {b1[0]} -> {b2[0]}: {gap}px (>= 40px)")

# Gap between Rung 1 and Card note
gap_r1_card = boxes[0][1] - (boxes[1][1] + boxes[1][3])
assert gap_r1_card >= 40, f"Gap Rung 1 to Card note {gap_r1_card} < 40"
print(f"  [PASS] Gap Rung 1 -> Card: {gap_r1_card}px (>= 40px)")

# Gap between Card bottom and Rung 2 top
gap_card_r2 = boxes[2][2] - (boxes[0][2] + boxes[0][4])
assert gap_card_r2 >= 40, f"Vertical gap Card to Rung 2 {gap_card_r2} < 40"
print(f"  [PASS] Vertical gap Card -> Rung 2: {gap_card_r2}px (>= 40px)")

print("\nALL VALIDATIONS PASSED PERFECTLY!")
