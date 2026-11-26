#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib
import sys

svg_file = "test_candidate_p3_0226.svg"
print(f"Auditing {svg_file}...")
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# Title text check
title_text = "".join(children[0].itertext()).strip()
print(f"   Title text: '{title_text}'")
assert title_text == "Handshake outcomes: a missing SYN-ACK, a reset, or a repeating SYN", f"Unexpected title text: {title_text}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

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
    "Handshake outcomes: a missing SYN-ACK, a reset, or a repeating SYN",
    "Healthy",
    "SYN with options MSS, SACK permitted, timestamps, window scale",
    "SYN-ACK",
    "ACK",
    "Reset",
    "SYN",
    "RST",
    "a reset means someone is refusing you; usually the port is closed",
    "Silence",
    "SYN, then the same SYN repeated, each a little later",
    "silence means someone is ignoring you: a drop, a block or a missing route",
    "Options: one SYN with window scale and the other without suggests a middlebox stripping options; throughput then limited to 64 KB per RTT. Fix belongs to the middlebox, not the application",
    "Check the server's capture next: SYN there but no SYN-ACK leaves = the server or a firewall in front of it is ignoring the port; SYN never appears on the server = the path between the two hosts is the suspect",
    "Silence means ignored, a reset means refused"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK] '{exp[:60]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. No forbidden words found! (PASS)")

# 6. Check orange count: exactly one orange highlight
raw_svg = pathlib.Path(svg_file).read_text()
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange item/arrow, got {len(oranges)}"
print("  [PASS] Orange used only once on Ladder C!")

# 7. Check arrows count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\n8. Arrow count: {len(arrows)}")
assert len(arrows) == 7, f"Expected 7 arrows, got {len(arrows)}"
print("  [PASS] Exactly 7 arrows present (3 for A, 2 for B, 2 for C)!")

# 8. Check external resources: no external fonts, images or scripts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in raw_svg.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in raw_svg, "No external URLs"
print("\n9. No external images, scripts or fonts! (PASS)")

print("\n==========================================")
print("ALL VERIFICATIONS PASSED 100% PERFECTLY!!!")
print("==========================================")
