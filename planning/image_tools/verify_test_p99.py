#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_path = "test_p99_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
tag1 = children[0].tag.split('}')[-1]
tag2 = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{tag1}>, Child 1: <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("   [PASS] <title> and <desc> are first children.")

# 2. Dimensions check
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height must be 900..1200, got {vb_parts[3]}"
assert float(height) == vb_parts[3]
print("   [PASS] Canvas dimensions valid.")

# 3. Extract text and check font sizes
def get_full_text(elem):
    text = elem.text or ""
    for child in elem:
        text += get_full_text(child)
        text += child.tail or ""
    return text

text_elements = []
for t in root.iter("{http://www.w3.org/2000/svg}text"):
    content = " ".join(get_full_text(t).split())
    fs = float(t.attrib.get('font-size', 24))
    assert fs >= 24, f"Text '{content}' has font-size {fs} < 24!"
    for tsp in t.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{content}'"
    text_elements.append((content, fs))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (txt, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:.0f}px] {txt}")

# 4. Check forbidden words
forbidden_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "icon", "callout", "sub-line", "subline", "takeaway"]
for txt, fs in text_elements:
    words = re.findall(r'\b[A-Za-z]+\b', txt.lower())
    for fw in forbidden_words:
        assert fw not in words, f"Forbidden word '{fw}' found in text: '{txt}'"
print("   [PASS] No style instruction words printed as text.")

# 5. Check expected labels
expected_labels = [
    "Averaging percentiles weights a ten-request server the same as a thousand-request server.",
    "quiet server",
    "1,000 requests",
    "p99 of 10 ms",
    "busy server",
    "10 requests",
    "p99 of 100 ms",
    "average of the two p99s",
    "55",
    "wrong",
    "gives a weight of one request to each server regardless of size",
    "all 1,010 requests merged",
    "true p99 at 12 ms",
    "merge the histograms or the raw samples",
    "then take the percentile",
    "To combine servers, merge the histograms or the raw samples, then take the percentile."
]
step_numbers = {"1", "2"}

all_svg_texts = [txt for txt, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_svg_texts)} found:")
for req in expected_labels:
    count = all_svg_texts.count(req)
    print(f"   [{'OK' if count == 1 else 'FAIL'}] count={count}: '{req[:50]}...'")
    assert count == 1, f"Expected '{req}' to appear exactly once, got {count}!"

extras = [t for t in all_svg_texts if t not in expected_labels and t not in step_numbers]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(text_elements) == len(expected_labels) + len(step_numbers), f"Text count {len(text_elements)} != {len(expected_labels) + len(step_numbers)}"
print(f"   [PASS] Exact label count matches: {len(expected_labels)} labels + {len(step_numbers)} step numbers.")

for num in step_numbers:
    cnt = all_svg_texts.count(num)
    assert cnt == 1, f"Step number '{num}' count is {cnt} != 1"
print("   [PASS] Step numbers 1 and 2 present exactly once.")

# 6. Check arrows count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"\n5. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"
print("   [PASS] Exactly 2 arrows.")

# 7. Check color palette and orange count
with open(svg_path) as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Missing background #f5f8f5"
assert "#303a36" in raw, "Missing text #303a36"
assert "#207448" in raw, "Missing green #207448"
assert "#e8f1ea" in raw, "Missing light green #e8f1ea"

orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 3, f"Orange should only be used on the single key item, got {len(orange_matches)}"
print("   [PASS] Orange used strictly on key item.")

print("\nALL 7 VERIFICATIONS PASSED PERFECTLY!")
