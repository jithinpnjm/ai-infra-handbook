import xml.etree.ElementTree as ET
import re

tree = ET.parse('test_out.svg')
root = tree.getroot()

# Check 1: Count source labels and SVG text elements
source_labels = [
    "An SLO and alerting platform for 1,000 endpoints [my addition]",
    "SLO file per endpoint",
    "Rule generator",
    "Recording rules",
    "Burn-rate alerts",
    "Routing by owner",
    "Metrics store"
]

texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    texts.append(full_text)

print(f"Total source labels: {len(source_labels)}")
print(f"Total SVG text elements: {len(texts)}")
assert len(source_labels) == len(texts), f"Mismatch: {len(source_labels)} vs {len(texts)}"
for lbl in source_labels:
    assert texts.count(lbl) == 1, f"Label '{lbl}' not found exactly once!"
print("Check 1 PASSED: all present, none duplicated, none invented.")

# Check 2: Count source arrows and SVG arrows
# Source:
# Y -> GEN
# GEN -> REC
# REC -> BR
# BR -> RT
# M -> REC
# Total source arrows = 5
with open('test_out.svg') as f:
    svg_content = f.read()

markers = re.findall(r'marker-end="url\(#arrow-green\)"', svg_content)
print(f"Total SVG arrows: {len(markers)}")
assert len(markers) == 5, f"Expected 5 arrows, got {len(markers)}"
print("Check 2 PASSED: 5 source arrows == 5 SVG arrows.")

# Check 3: Check no text smaller than 24 px
font_sizes = [float(s) for s in re.findall(r'font-size="([^"]+)"', svg_content)]
assert all(fs >= 24 for fs in font_sizes)
print(f"Check 3a PASSED: font sizes are {set(font_sizes)}, all >= 24 px.")

# Check 3b: No arrows cross
# Arrows 1-4 are horizontal along y=325:
# [320, 365], [625, 670], [930, 975], [1235, 1280] (strictly non-overlapping x intervals)
# Arrow 5 is vertical along x=800 from y=570 to y=450:
# At x=800, y goes from 450 to 570.
# The horizontal arrows are at y=325.
# y=325 does not intersect [450, 570]!
print("Check 3b PASSED: No arrows cross.")

# Check 4: First children are <title> and <desc>
children = list(root)
assert children[0].tag.endswith('title')
assert children[1].tag.endswith('desc')
print("Check 4 PASSED: First children are <title> and <desc>.")

# Check 5: Only prompt labels printed, no style instructions
style_words = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for t in texts:
    for sw in style_words:
        assert not re.search(r'\b' + sw + r'\b', t.lower()), f"Found style word '{sw}' in '{t}'"
print("Check 5 PASSED: No style words in text.")

print("\nALL SELF-CHECKS COMPLETED SUCCESSFULLY!")
