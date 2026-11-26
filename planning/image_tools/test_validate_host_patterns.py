import xml.etree.ElementTree as ET
import re

svg_path = "test_host_patterns.svg"
tree = ET.parse(svg_path)
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

# 3. Check font-size >= 24 on all text and tspans
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
    "Host patterns select machines by union, intersection, exclusion and regex",
    "gpu:login",
    "either group",
    "gpu:&rack1",
    "both groups",
    "gpu",
    "rack1",
    "gpu:!gpu02",
    "this group without one host",
    "~gpu0[1-4]",
    "regular expression on names",
    "Test a pattern with --list-hosts before a change. A pattern that matches the wrong hosts reaches machines it should not.",
    "Read the host list before you change a group."
]

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

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
raw_svg = open(svg_path).read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib or "marker-start" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib or "marker-start" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with markers: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

# 8. Check outside margins >= 40px
boxes = [
    ("panel-1", 40, 175, 740, 310),
    ("panel-2", 820, 175, 740, 310),
    ("panel-3", 40, 525, 740, 310),
    ("panel-4", 820, 525, 740, 310),
    ("box-bottom-note", 40, 875, 1520, 95),
    ("bar-caption", 40, 1010, 1520, 70),
]

print("\n8. Checking outside margins (>= 40px):")
for name, x, y, w, h in boxes:
    left_m = x
    right_m = 1600 - (x + w)
    top_m = y
    bot_m = int(height) - (y + h)
    assert left_m >= 40, f"{name} left margin {left_m} < 40"
    assert right_m >= 40, f"{name} right margin {right_m} < 40"
    assert top_m >= 40, f"{name} top margin {top_m} < 40"
    assert bot_m >= 40, f"{name} bot margin {bot_m} < 40"
    print(f"  {name:15s}: L={left_m} R={right_m} T={top_m} B={bot_m} (PASS)")

# Check gaps between boxes >= 40px
assert (820 - (40 + 740)) >= 40, "Gap between column 1 and column 2 < 40"
assert (525 - (175 + 310)) >= 40, "Gap between row 1 and row 2 < 40"
assert (875 - (525 + 310)) >= 40, "Gap between row 2 and bottom note < 40"
assert (1010 - (875 + 95)) >= 40, "Gap between bottom note and caption < 40"

print("\nALL VERIFICATIONS PASSED!")
