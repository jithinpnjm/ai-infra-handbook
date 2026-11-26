#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

svg_path = "p2_2004_test.svg"
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
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check font-size >= 24
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
    "What one open call does, step by step",
    "Program",
    "Program passes a file name",
    "Kernel walks the directory names until it reaches the inode",
    "Creates an open file description with its own offset",
    "Places a pointer in the first free slot of the process table",
    "Returns the slot number, for example 3",
    "Later read and write name only the slot",
    "The program never touches the inode directly.",
    "Each error in this chapter has a place on this path."
]

step_numbers = {"1", "2", "3", "4", "5"}

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for s in step_numbers:
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number {s} count {cnt} != 1!"
print("\nAll step numbers 1..5 present exactly once! (PASS)")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path(svg_path).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 1, f"Expected exactly 1 arrow, got {total_arrows}"

# 8. Check gaps and margins
# We can check specific boxes
rects = {}
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.get('id')
    if gid:
        r = g.find('{http://www.w3.org/2000/svg}rect')
        if r is not None:
            rects[gid] = {
                'x': float(r.get('x')),
                'y': float(r.get('y')),
                'w': float(r.get('width')),
                'h': float(r.get('height')),
            }

# Add kernel panel and takeaway bar
for r in root.iter('{http://www.w3.org/2000/svg}rect'):
    fill = r.get('fill')
    w = float(r.get('width'))
    h = float(r.get('height'))
    if fill == '#e8f1ea' and w > 1000:
        rects['kernel-panel'] = {'x': float(r.get('x')), 'y': float(r.get('y')), 'w': w, 'h': h}
    elif fill == '#207448' and w > 1000:
        rects['takeaway-bar'] = {'x': float(r.get('x')), 'y': float(r.get('y')), 'w': w, 'h': h}

print("\n8. Checking gaps (all >= 40px):")
gaps = [
    ("Left margin (Kernel Panel)", rects['kernel-panel']['x']),
    ("Left margin (Boxes)", rects['node-program']['x']),
    ("Right margin (Takeaway bar)", 1600 - (rects['takeaway-bar']['x'] + rects['takeaway-bar']['w'])),
    ("Right margin (Side note)", 1600 - (rects['side-note']['x'] + rects['side-note']['w'])),
    ("Bottom margin (Takeaway bar)", 1200 - (rects['takeaway-bar']['y'] + rects['takeaway-bar']['h'])),
    ("Program -> Step 1", rects['step-1']['y'] - (rects['node-program']['y'] + rects['node-program']['h'])),
    ("Step 1 -> Kernel panel", rects['kernel-panel']['y'] - (rects['step-1']['y'] + rects['step-1']['h'])),
    ("Kernel panel top -> Step 2", rects['step-2']['y'] - rects['kernel-panel']['y']),
    ("Step 2 -> Step 3", rects['step-3']['y'] - (rects['step-2']['y'] + rects['step-2']['h'])),
    ("Step 3 -> Step 4", rects['step-4']['y'] - (rects['step-3']['y'] + rects['step-3']['h'])),
    ("Step 4 -> Kernel panel bottom", (rects['kernel-panel']['y'] + rects['kernel-panel']['h']) - (rects['step-4']['y'] + rects['step-4']['h'])),
    ("Kernel panel -> Step 5", rects['step-5']['y'] - (rects['kernel-panel']['y'] + rects['kernel-panel']['h'])),
    ("Kernel panel -> Side note (horizontal)", rects['side-note']['x'] - (rects['kernel-panel']['x'] + rects['kernel-panel']['w'])),
]

for name, val in gaps:
    print(f"   [{'OK' if val >= 40 else 'FAIL'}] {name}: {val}px")
    assert val >= 40, f"Gap '{name}' is {val}px < 40px!"

print("\nALL 8 STRICT CHECKS PASSED PERFECTLY!")
