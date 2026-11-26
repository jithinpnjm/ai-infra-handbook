import xml.etree.ElementTree as ET
import re
import asyncio
from playwright.async_api import async_playwright
import pathlib

# Verify candidate_reader_map.svg
tree = ET.parse("candidate_reader_map.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
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

# 3. Extract text elements and font-size >= 24
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

print(f"\n3. Total text elements: {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Which chapters serve which interview stage",
    "Recruiter call, CV",
    "20.1, 20.2",
    "Linux console and troubleshooting",
    "20.3, 20.4, 20.5, 20.6, 20.7",
    "Coding and algorithms",
    "20.8, 20.9, 20.10, 20.11",
    "System design",
    "20.12, 20.13, 20.14, 20.15, 20.16",
    "20.17 timed drills",
    "Stress interview, 30-minute incident",
    "20.26, 20.27",
    "Final hour, project deep dive",
    "20.28",
    "[official]",
    "[official] and [report]",
    "[report]",
    "[official]",
    "Start with Part B console and Part D design, because both appear in every report."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking expected labels:")
for exp in set(expected_labels):
    expected_cnt = expected_labels.count(exp)
    cnt = found_texts.count(exp)
    ok = (cnt == expected_cnt)
    print(f"   [{'PASS' if ok else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp}'")
    assert ok, f"Expected '{exp}' count {cnt} != expected {expected_cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("5. Forbidden words check: PASS!")

# 6. Color check
with open("candidate_reader_map.svg") as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Background #f5f8f5 missing"
assert "#303a36" in raw, "Text #303a36 missing"
assert "#207448" in raw, "Main green #207448 missing"
assert "#e8f1ea" in raw, "Light green panels #e8f1ea missing"
assert "#db8129" in raw, "Orange #db8129 missing"
print("6. Color palette check: PASS!")

# 7. Check orange usage (used only for the single most important item)
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 8, f"Unexpected orange count: {len(oranges)}"

# 8. Check arrows count
arrow_markers = re.findall(r'marker-end', raw)
print(f"Arrow marker count: {len(arrow_markers)}")
assert len(arrow_markers) == 1, f"Expected 1 arrow, got {len(arrow_markers)}"

print("\nALL BASIC CHECKS PASSED!")
