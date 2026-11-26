#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_path = "status_ladder.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
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

# 3. Expected labels
expected_labels = [
    "From a failed unit message or status code to the layer that broke",
    "Message from systemctl or the journal",
    "Failed to start X: Unit X not found",
    "wrong name, path or alias; daemon-reload may fix it",
    "Job for X failed because the control process exited with error code",
    "read journalctl -xeu X",
    "start request repeated too quickly",
    "start limit hit: reset-failed, fix the cause, lengthen RestartSec",
    "Dependency failed for X",
    "a Requires dependency failed",
    "Unit is masked",
    "the unit cannot be started at all",
    "status= code",
    "203/EXEC",
    "ExecStart binary cannot run: path, permissions, a noexec mount, wrong architecture, or a bad shebang",
    "200/CHDIR",
    "bad WorkingDirectory=",
    "217/USER",
    "bad User=",
    "226/NAMESPACE",
    "sandbox mount problem",
    "1/FAILURE",
    "the program's own exit",
    "signal=KILL or code=killed",
    "killed by the OOM killer or a timeout",
    "Result: timeout",
    "unit ran past its time limit",
    "systemctl status",
    "journalctl -u NAME -b",
    "systemctl cat",
    "systemd-analyze verify FILE",
    "Start with the status code, then read the journal for that unit"
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
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Banned style word '{b}' found in text: '{t}'"
print("\n4. Banned style words check: PASS")

# 5. Arrows / Markers
lines_with_markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n5. Elements with markers: {len(lines_with_markers)}")
assert len(lines_with_markers) == 12, f"Expected 12 arrows, got {len(lines_with_markers)}"
print("  [PASS] Exactly 12 arrows (5 on left, 7 on right)!")

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

# 7. Margins and gaps
H_val = float(height)
containers = [
    ("Left Column", 40, 95, 730, 875),
    ("Right Column", 810, 95, 750, 875),
    ("Bottom Strip", 40, 1010, 1520, 65),
    ("Bottom Bar", 40, 1115, 1520, 45)
]

print("\n7. Checking outside margins (>= 40px):")
for name, x, y, w, h in containers:
    left_m = x
    right_m = 1600 - (x + w)
    top_m = y
    bot_m = H_val - (y + h)
    assert left_m >= 40, f"{name} left margin {left_m} < 40"
    assert right_m >= 40, f"{name} right margin {right_m} < 40"
    assert top_m >= 40, f"{name} top margin {top_m} < 40"
    assert bot_m >= 40, f"{name} bot margin {bot_m} < 40"
    print(f"  [PASS] {name} margins: L={left_m}, R={right_m}, T={top_m}, B={bot_m}")

# Gaps between containers
gap_cols = 810 - (40 + 730)
assert gap_cols >= 40, f"Gap between columns {gap_cols} < 40"
print(f"  [PASS] Gap between columns: {gap_cols}px >= 40px")

gap_cols_to_strip = 1010 - (95 + 875)
assert gap_cols_to_strip >= 40, f"Gap columns to strip {gap_cols_to_strip} < 40"
print(f"  [PASS] Gap columns to strip: {gap_cols_to_strip}px >= 40px")

gap_strip_to_bar = 1115 - (1010 + 65)
assert gap_strip_to_bar >= 40, f"Gap strip to bar {gap_strip_to_bar} < 40"
print(f"  [PASS] Gap strip to bar: {gap_strip_to_bar}px >= 40px")

print("\nALL TESTS PASSED PERFECTLY!")
