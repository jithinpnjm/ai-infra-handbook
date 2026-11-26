#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_flow.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb.startswith("0 0 1600"), f"viewBox must start with '0 0 1600', got {vb}"
h_val = int(vb.split()[-1])
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("[PASS] Canvas dimensions and viewBox valid.")

# 3. Extract text elements and check font-sizes
texts = []
font_sizes = []
for el in root.iter():
    if el.tag.endswith('text'):
        fs = int(el.attrib.get('font-size', '0'))
        # check child tspans
        tspans = [child for child in el if child.tag.endswith('tspan')]
        if tspans:
            for ts in tspans:
                t_content = (ts.text or "").strip()
                texts.append(t_content)
                t_fs = int(ts.attrib.get('font-size', fs))
                font_sizes.append((t_content, t_fs))
        else:
            t_content = "".join(el.itertext()).strip()
            texts.append(t_content)
            font_sizes.append((t_content, fs))

print("\n--- All text elements and font-sizes ---")
for t, fs in font_sizes:
    print(f"[{fs}px] '{t}'")
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"

print("[PASS] All text elements >= 24 px.")

# 4. Check required labels from source:
# Content:
#   U["Teams"] --> Q["Queue and fair share"]
#   Q --> P["Topology-aware placer"]
#   P --> N["Nodes in fabric blocks"]
#   H["Node health feed"] --> P
#   N --> C["Checkpoint store"]
#   C --> Q
source_labels = [
    "Teams",
    "Queue and fair share",
    "Topology-aware placer",
    "Nodes in fabric blocks",
    "Node health feed",
    "Checkpoint store"
]

# For multi-line text, join tspans by space
full_texts = []
for el in root.iter():
    if el.tag.endswith('text'):
        combined = " ".join("".join(el.itertext()).split())
        full_texts.append(combined)

print("\n--- Full text elements ---")
for ft in full_texts:
    print(f"'{ft}'")

# Check title:
title_found = [ft for ft in full_texts if "GPU job scheduling" in ft]
print(f"Title text: {title_found}")
assert len(title_found) == 1, "Title must appear once"

# Check each source label:
print("\n--- Checking source labels ---")
for sl in source_labels:
    cnt = full_texts.count(sl)
    print(f"Label '{sl}': count={cnt}")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

print("[PASS] Every source label appears exactly once.")

# 5. Check no banned styling words:
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"

print("[PASS] No styling words printed as text.")

# 6. Check arrows count
# Arrows in SVG have marker-end
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\nArrow count: {len(arrows)}")
assert len(arrows) == 6, f"Expected 6 arrows, got {len(arrows)}"
print("[PASS] Exactly 6 arrows present.")

# 7. Check orange usage: exactly one orange highlight
orange_els = []
for el in root.iter():
    for k, v in el.attrib.items():
        if "#db8129" in v or "arrow-orange" in v:
            orange_els.append((el.tag, k, v))

print(f"\nOrange highlights: {len(orange_els)}")
for o in orange_els:
    print(f"  {o}")
# In defs, marker has fill="#db8129". In body, exactly one path uses stroke="#db8129" and marker-end="url(#arrow-orange)"
body_orange_paths = [el for el in root.iter() if el.tag.endswith('path') and el.attrib.get('stroke') == "#db8129"]
print(f"Body orange paths: {len(body_orange_paths)}")
assert len(body_orange_paths) == 1, f"Expected exactly 1 orange item/arrow, got {len(body_orange_paths)}"
print("[PASS] Exactly one orange item/arrow used.")

# 8. Check external resources: no external fonts, images or scripts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
svg_str = ET.tostring(root, encoding='unicode')
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("[PASS] No external images, scripts or fonts.")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
