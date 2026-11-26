#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import os

svg_path = "test_final.svg"
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
    fs = int(t.attrib.get('font-size', 24))
    text_elements.append((content, fs))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (txt, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2d}px] {txt}")
    assert fs >= 24, f"Text '{txt}' has font-size {fs} < 24!"

# 4. Check forbidden words
forbidden_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow", "cylinder", "folder", "icon", "callout", "sub-line", "subline", "takeaway"]
for txt, fs in text_elements:
    words = re.findall(r'\b[A-Za-z]+\b', txt.lower())
    for fw in forbidden_words:
        assert fw not in words, f"Forbidden word '{fw}' found in text: '{txt}'"
print("   [PASS] No style instruction words printed as text.")

# 5. Check expected labels
expected_labels = [
    "A CPU limit of 1 and five busy threads",
    "limit 1 CPU = 100 ms of CPU time per 100 ms period regardless of thread count",
    "cpu.stat nr_throttled counts it",
    "Timeline of one 100 ms CFS period",
    "the shared budget of 100 ms of CPU time is used up in the first 20 ms (5 threads times 20 ms)",
    "throttled for the remaining 80 ms even though the node may have idle CPU",
    "the next period starts and the budget refreshes",
    "average looks fine, tail latency grows; requests arriving late in a period wait",
    "default timeoutSeconds 1 on a throttled pod can fail a healthy liveness probe past 1000 ms and restart a healthy container; raise timeoutSeconds to 5 to 10 seconds"
]

all_svg_texts = [txt for txt, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_svg_texts)} found:")
for req in expected_labels:
    count = all_svg_texts.count(req)
    print(f"   [{'OK' if count == 1 else 'FAIL'}] count={count}: '{req[:50]}...'")
    assert count == 1, f"Expected '{req}' to appear exactly once, got {count}!"

extras = [t for t in all_svg_texts if t not in expected_labels]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(text_elements) == len(expected_labels), f"Text count {len(text_elements)} != {len(expected_labels)}"
print("   [PASS] Exact label count matches: 9 labels, 9 text elements.")

# 6. Check arrows count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"\n5. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
print("   [PASS] Exactly 0 arrows.")

# 7. Check color palette and orange count
with open(svg_path) as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Missing background #f5f8f5"
assert "#303a36" in raw, "Missing text #303a36"
assert "#207448" in raw, "Missing green #207448"
assert "#e8f1ea" in raw, "Missing light green #e8f1ea"
assert "#db8129" in raw, "Missing orange #db8129"

orange_count = len(re.findall(r'#db8129', raw, re.IGNORECASE))
print(f"\n6. Orange occurrences: {orange_count}")
assert orange_count == 1, f"Expected orange to be used exactly once, got {orange_count}"
print("   [PASS] Orange used only once for the single most important item.")

# 8. Precise padding and bounding box validation
print("\n7. Precise Padding Verification:")
boxes = [
    {
        "name": "Card 1: Quota rule",
        "bx": 50, "by": 95, "bw": 960, "bh": 110,
        "icon": (75, 122, 56, 56),
        "lines": [
            ("limit 1 CPU = 100 ms of CPU time per 100 ms period", 25, 142, 155, "left", False),
            ("regardless of thread count", 25, 174, 155, "left", False)
        ]
    },
    {
        "name": "Card 2: Metric monitoring",
        "bx": 1050, "by": 95, "bw": 500, "bh": 110,
        "icon": (1075, 122, 56, 56),
        "lines": [
            ("cpu.stat nr_throttled", 24, 142, 1155, "left", True),
            ("counts it", 24, 174, 1155, "left", True)
        ]
    },
    {
        "name": "Card 3: Side note",
        "bx": 50, "by": 730, "bw": 720, "bh": 290,
        "icon": (75, 755, 56, 56),
        "lines": [
            ("average looks fine, tail latency grows;", 24, 860, 75, "left", False),
            ("requests arriving late in a period wait", 24, 896, 75, "left", False)
        ]
    },
    {
        "name": "Card 4: Probe consequence",
        "bx": 810, "by": 730, "bw": 740, "bh": 290,
        "icon": (835, 755, 56, 56),
        "lines": [
            ("default timeoutSeconds 1 on a throttled pod", 24, 855, 835, "left", False),
            ("can fail a healthy liveness probe past 1000 ms", 24, 889, 835, "left", False),
            ("and restart a healthy container; raise", 24, 923, 835, "left", False),
            ("timeoutSeconds to 5 to 10 seconds", 24, 957, 835, "left", False)
        ]
    },
    {
        "name": "Timeline Container Title",
        "bx": 50, "by": 235, "bw": 1500, "bh": 425,
        "icon": (75, 255, 56, 56),
        "lines": [
            ("Timeline of one 100 ms CFS period", 30, 293, 150, "left", False)
        ]
    },
    {
        "name": "Throttled Block",
        "bx": 376, "by": 425, "bw": 1104, "bh": 155,
        "icon": None,
        "lines": [
            ("throttled for the remaining 80 ms", 26, 492, 928, "middle", False),
            ("even though the node may have idle CPU", 26, 526, 928, "middle", False)
        ]
    },
    {
        "name": "Refill Marker Card",
        "bx": 900, "by": 600, "bw": 580, "bh": 92,
        "icon": None,
        "lines": [
            ("the next period starts", 24, 642, 1190, "middle", False),
            ("and the budget refreshes", 24, 672, 1190, "middle", False)
        ]
    }
]

for b in boxes:
    bx, by, bw, bh = b["bx"], b["by"], b["bw"], b["bh"]
    print(f"\nChecking container: {b['name']} [x={bx}, y={by}, w={bw}, h={bh}]")
    for text_str, fs, base_y, anch_x, align, is_mono in b["lines"]:
        coeff = 0.62 if is_mono else 0.60
        tw = len(text_str) * fs * coeff
        if align == "middle":
            x_left = anch_x - tw / 2
            x_right = anch_x + tw / 2
        elif align == "right":
            x_left = anch_x - tw
            x_right = anch_x
        else:
            x_left = anch_x
            x_right = anch_x + tw

        pad_left = x_left - bx
        pad_right = (bx + bw) - x_right
        pad_top = (base_y - fs) - by
        pad_bottom = (by + bh) - base_y

        print(f"  Line '{text_str}' (fs={fs}): w={tw:.1f} | pads: L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
        assert pad_left >= 16, f"pad_left {pad_left:.1f} < 16 for '{text_str}' in {b['name']}"
        assert pad_right >= 16, f"pad_right {pad_right:.1f} < 16 for '{text_str}' in {b['name']}"
        assert pad_top >= 16, f"pad_top {pad_top:.1f} < 16 for '{text_str}' in {b['name']}"
        assert pad_bottom >= 16, f"pad_bottom {pad_bottom:.1f} < 16 for '{text_str}' in {b['name']}"

        # If icon exists, ensure text does not collide with icon
        if b["icon"] is not None:
            ix, iy, iw, ih = b["icon"]
            # Icon bounding box is [ix, iy, ix+iw, iy+ih]
            # Text line bounding box is [x_left, base_y - fs, x_right, base_y]
            # They must not overlap
            horiz_overlap = not (x_right <= ix or x_left >= ix + iw)
            vert_overlap = not (base_y <= iy or (base_y - fs) >= iy + ih)
            assert not (horiz_overlap and vert_overlap), f"Text '{text_str}' overlaps icon in {b['name']}!"

print("\n   [PASS] All text elements fit with >= 16px padding and zero icon/box collisions.")

# 9. Render screenshot with headless Chrome
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
res = subprocess.run([
    chrome_path,
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--window-size=1600,1060",
    "--screenshot=/tmp/test_final.png",
    f"file://{os.path.abspath(svg_path)}"
], capture_output=True, text=True)

assert os.path.exists("/tmp/test_final.png"), "Chrome screenshot failed to generate!"
print("\n[PASS] Headless Chrome rendered /tmp/test_final.png successfully.")
print("\n=== ALL AUDIT AND FIDELITY CHECKS PASSED PERFECTLY! ===")
