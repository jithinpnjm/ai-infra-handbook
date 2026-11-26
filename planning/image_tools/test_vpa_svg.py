#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_path = "vpa_recommendation_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure: <title> and <desc> are first children
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("   [PASS] <title> and <desc> are the first children.")

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
print("   [PASS] Canvas dimensions valid.")

# 3. Required Labels
expected_labels = [
    "Reading a VPA recommendation",
    "Annotated kubectl describe vpa Status for container coredns",
    "Lower Bound: Cpu 25m, Memory 262144k",
    "Target: Cpu 25m, Memory 262144k (use as the baseline for requests)",
    "Uncapped Target: Cpu 25m, Memory 262144k",
    "Upper Bound: Cpu 427m, Memory 916943343",
    "a wide gap between lower and upper means the workload varies a lot",
    "range the recommender thinks is safe",
    "25m",
    "427m",
    "1 run VPA in Off mode",
    "2 describe vpa after real traffic",
    "3 engineers set requests by hand from Target",
    "4 nothing is evicted at peak"
]

print(f"\n3. Checking {len(expected_labels)} expected labels:")
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0).replace('px', ''))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            tfs_val = float(tfs.replace('px', ''))
            assert tfs_val >= 24, f"tspan font size {tfs_val} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

found_texts = [t for t, fs in text_elements]
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected label '{exp}' appeared {cnt} times, expected exactly 1!"
    print(f"  [PASS] '{exp}' (cnt=1)")

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Found extra text: {extras}"
print("  [PASS] Zero extra labels!")

# 4. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'callout']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Banned style word '{b}' found in text: '{t}'"
print("\n4. Banned style words check: PASS")

# 5. Arrows / Markers
lines_with_markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n5. Elements with markers: {len(lines_with_markers)}")
assert len(lines_with_markers) == 0, f"Expected 0 source arrows, got {len(lines_with_markers)}"
print("  [PASS] Equal arrow count (0 source arrows == 0 SVG arrows)!")

# 6. Colors
raw_svg = open(svg_path).read()
assert "#f5f8f5" in raw_svg, "Background #f5f8f5 missing"
assert "#303a36" in raw_svg, "Text #303a36 missing"
assert "#207448" in raw_svg, "Main green #207448 missing"
assert "#e8f1ea" in raw_svg, "Light green panels #e8f1ea missing"
assert "#db8129" in raw_svg, "Orange #db8129 missing"
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(oranges)}")
print("  [PASS] Colors check passed!")

# 7. Check number circles: r=24
circles_24 = [c for c in root.iter('{http://www.w3.org/2000/svg}circle') if c.attrib.get('r') == '24']
print(f"\n7. Number circles with r=24: {len(circles_24)}")
assert len(circles_24) == 4, f"Expected 4 number circles for the 4 steps, got {len(circles_24)}"
print("  [PASS] Exactly 4 number circles (r=24)!")

print("\nALL CHECKS PASSED PERFECTLY!")
