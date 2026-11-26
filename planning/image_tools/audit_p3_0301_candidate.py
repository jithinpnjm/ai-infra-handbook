import xml.etree.ElementTree as ET
import re
import pathlib

svg_file = "test_p3_0301_candidate.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print(f"=== Validating {svg_file} ===")

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
    "How the first matching case in handle(event) is chosen",
    "case {\"type\": \"node_down\", \"node\": str(name)}",
    "drain name",
    "case {\"type\": \"temp\", \"value\": float(v)} if v > 85",
    "throttle",
    "case {\"type\": \"gpu\", \"ids\": [first, *_]}",
    "first gpu first",
    "case {\"type\": t}",
    "unhandled t",
    "case _",
    "unknown",
    "event {type: node_down, node: gpu07} matches case 1 and binds name to gpu07, result 'drain gpu07'",
    "event {type: temp, value: 91.0} matches case 2 because the guard v > 85 holds, result 'throttle'",
    "event {type: gpu, ids: [3, 4]} matches case 3 binding first to 3, result 'first gpu 3'",
    "event {type: fan} reaches case 4 binding t to fan, result 'unhandled fan'",
    "literals, captures, wildcard _, sequences, mappings, class patterns Point(x=0, y=0), alternatives with |, guards with if",
    "match cmd.split(): case [\"start\", service], case [\"stop\", service, *flags], case [\"status\"]",
    "Not a C-style switch: the first matching case wins, and matched parts are bound to names"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against found:")
all_ok = True
for exp in expected_labels:
    expected_cnt = expected_labels.count(exp)
    cnt = found_texts.count(exp)
    ok = (cnt == expected_cnt)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp}'")

assert all_ok, "Some expected labels failed count check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print(f"   Exact text count match: {len(found_texts)} == {len(expected_labels)} (PASS)")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 12, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 4, f"Expected exactly 4 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str

# Palette check
hex_colors = set(re.findall(r'#[0-9a-fA-F]{6}', svg_str.lower()))
print(f"\n9. Colors used in SVG: {sorted(hex_colors)}")
allowed_colors = {"#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129", "#ffffff", "#fffaf5", "#fff0e0"}
for c in hex_colors:
    assert c in allowed_colors, f"Disallowed color {c} found in SVG!"
print("   All colors strictly within allowed palette! (PASS)")

print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY! ===")
