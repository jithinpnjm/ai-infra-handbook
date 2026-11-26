#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_path = "candidate_final.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

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
    "Sizing the tail sampler and what happens at 8,000 traces per second",
    "traces held = new traces per second x decision_wait",
    "Design point",
    "5,000 new traces per second x 30 s = 150,000 traces held",
    "num_traces set to 200,000 gives headroom",
    "with 20 spans of 1 KB each (assumptions, not measurements) = 3 GB of buffered span data before overhead",
    "After a traffic increase",
    "8,000 per second x 30 s = 240,000 needed, which exceeds num_traces 200,000, so traces are dropped and the viewer shows fragments",
    "raise num_traces and memory together",
    "or reduce decision_wait",
    "add sampler replicas",
    "apply a head sample in tier one to cut the rate",
    "alert on refusals",
    "otelcol_receiver_refused_spans non-zero means the memory limiter is shedding load",
    "if the load balancing tier was scaled up, spans of one trace may be split across samplers while the routing pool changes"
]

all_found = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_found)} found:")
all_ok = True
for exp in expected_labels:
    cnt = all_found.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in all_found if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in all_found:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path, 'r', encoding='utf-8') as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check colors
assert '#f5f8f5' in svg_str
assert '#303a36' in svg_str
assert '#207448' in svg_str
assert '#e8f1ea' in svg_str

# 8. Check paddings for all text elements
checks = [
    # Formula Box
    ("Formula", "traces held = new traces per second x decision_wait", 30, False, 800 - 51*0.6*30/2, 195, 195, 40, 1560, 145, 225),
    # Left Header
    ("Design point", "Design point", 32, False, 135, 316, 316, 40, 780, 265, 690),
    # Left Card 1
    ("Left Card 1 Line 1", "5,000 new traces per second x 30 s ", 24, False, 80, 388, 388, 60, 760, 350, 446),
    ("Left Card 1 Line 2", "= 150,000 traces held", 24, False, 80, 422, 422, 60, 760, 350, 446),
    # Left Card 2
    ("Left Card 2", "num_traces set to 200,000 gives headroom", 24, False, 80, 499, 499, 60, 760, 460, 522),
    # Left Card 3
    ("Left Card 3 Line 1", "with 20 spans of 1 KB each (assumptions, ", 24, False, 80, 576, 576, 60, 760, 538, 670),
    ("Left Card 3 Line 2", "not measurements) = 3 GB of buffered span ", 24, False, 80, 610, 610, 60, 760, 538, 670),
    ("Left Card 3 Line 3", "data before overhead", 24, False, 80, 644, 644, 60, 760, 538, 670),
    # Right Header
    ("After a traffic increase", "After a traffic increase", 32, False, 915, 316, 316, 820, 1560, 265, 690),
    # Right Big Card
    ("Right Line 1", "8,000 per second x 30 s = 240,000 needed, ", 24, False, 860, 398, 398, 840, 1540, 350, 670),
    ("Right Line 2", "which exceeds num_traces 200,000, so ", 24, False, 860, 436, 436, 840, 1540, 350, 670),
    ("Right Line 3", "traces are dropped and the viewer ", 24, False, 860, 474, 474, 840, 1540, 350, 670),
    ("Right Line 4", "shows fragments", 24, False, 860, 512, 512, 840, 1540, 350, 670),
    # Fix 1
    ("Fix 1", "raise num_traces and memory together", 24, False, 148, 783, 783, 130, 760, 744, 806),
    # Fix 2
    ("Fix 2", "or reduce decision_wait", 24, False, 78, 859, 859, 60, 760, 820, 882),
    # Fix 3
    ("Fix 3", "add sampler replicas", 24, False, 78, 935, 935, 60, 760, 896, 958),
    # Fix 4
    ("Fix 4 Line 1", "apply a head sample in tier one ", 24, False, 78, 1010, 1010, 60, 760, 972, 1068),
    ("Fix 4 Line 2", "to cut the rate", 24, False, 78, 1044, 1044, 60, 760, 972, 1068),
    # Fix 5
    ("Fix 5", "alert on refusals", 24, False, 78, 1121, 1121, 60, 760, 1082, 1144),
    # Check 1
    ("Check 1 Line 1", "otelcol_receiver_refused_spans non-zero ", 24, True, 860, 856, 856, 840, 1540, 810, 940),
    ("Check 1 Line 2", "means the memory limiter is shedding load", 24, False, 860, 894, 894, 840, 1540, 810, 940),
    # Check 2
    ("Check 2 Line 1", "if the load balancing tier was scaled up, ", 24, False, 860, 1006, 1006, 840, 1540, 960, 1135),
    ("Check 2 Line 2", "spans of one trace may be split across ", 24, False, 860, 1042, 1042, 840, 1540, 960, 1135),
    ("Check 2 Line 3", "samplers while the routing pool changes", 24, False, 860, 1078, 1078, 840, 1540, 960, 1135),
]

all_pad_ok = True
print("\n8. Checking all text paddings (>= 16px):")
for name, text, fs, is_mono, x, y_first, y_last, bx1, bx2, by1, by2 in checks:
    factor = 0.62 if is_mono else 0.60
    w = len(text) * factor * fs
    left_pad = x - bx1
    right_pad = bx2 - (x + w)
    top_pad = (y_first - fs * 0.75) - by1
    bottom_pad = by2 - (y_last + fs * 0.25)
    
    ok_l = left_pad >= 16
    ok_r = right_pad >= 16
    ok_t = top_pad >= 16
    ok_b = bottom_pad >= 16
    
    status = "OK" if (ok_l and ok_r and ok_t and ok_b) else "FAIL"
    if not (ok_l and ok_r and ok_t and ok_b):
        all_pad_ok = False
    print(f"[{status}] {name:25s} | L:{left_pad:5.1f} R:{right_pad:5.1f} T:{top_pad:5.1f} B:{bottom_pad:5.1f}")

assert all_pad_ok, "Some paddings were < 16px!"

print("\n>>> ALL CHECKS AND PADDINGS PASSED WITH FLYING COLORS! <<<")
