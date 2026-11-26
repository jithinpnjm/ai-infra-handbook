#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, pathlib, subprocess

svg_path = "test_output.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Check font sizes >= 24
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

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Check expected labels
expected_labels = [
    "Planned exits versus failures",
    "Clean planned exit",
    "meta end_host",
    "stop this host",
    "no failure",
    "when skip_this_host",
    "meta end_play",
    "end the play for everyone",
    "not a failure",
    "when dry_run_only",
    "end_batch",
    "Explicit stop",
    "fail",
    "explicit stop",
    "msg Refusing to run in production without change ticket",
    "when env is prod and no change_ticket",
    "Use rarely",
    "meta clear_host_errors",
    "resets failed hosts",
    "rare",
    "hides the reason"
]

found_texts = [t for t, fs in text_elements]

print("\n4. Checking single-occurrence expected labels:")
for lbl in expected_labels:
    cnt = found_texts.count(lbl)
    assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1"
    print(f"   [PASS] count=1: '{lbl}'")

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path(svg_path).read_text(encoding="utf-8")
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 10, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check colors present
for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert c in svg_str.lower(), f"Missing color {c}"
print("\n7. All required colors present! (PASS)")

print("\n=== ALL ASSERTIONS PASSED! ===")
