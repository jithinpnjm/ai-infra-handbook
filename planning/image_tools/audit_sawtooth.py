import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_sawtooth.svg")
root = tree.getroot()

# 1. Structure check: first children must be title and desc
assert root[0].tag.endswith('title'), f"First child not title: {root[0].tag}"
assert root[1].tag.endswith('desc'), f"Second child not desc: {root[1].tag}"
print("1. Title and desc: PASS")

# 2. Dimensions check
w = root.get('width')
h = root.get('height')
vb = root.get('viewBox')
assert w == "1600", f"Width {w} != 1600"
assert h == "1060", f"Height {h} != 1060"
assert vb == "0 0 1600 1060", f"viewBox {vb} != 0 0 1600 1060"
assert 900 <= float(h) <= 1200
print(f"2. Dimensions: PASS ({w}x{h}, viewBox='{vb}')")

# 3. Text font-size check >= 24px
text_nodes = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', '0'))
    assert fs >= 24, f"Text font size {fs} < 24 for '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24 in '{full_text}'"
    text_nodes.append((full_text, fs))

print(f"3. Font sizes: PASS (All {len(text_nodes)} text nodes >= 24px)")

# 4. Expected labels check
expected_labels = [
    "The sawtooth and the cut streams need two separate fixes",
    "short burst every six minutes; autoscaler removes replicas after each burst and adds them back a few minutes later; users report streams that stop halfway",
    "flapping wastes cold starts: in-flight policy with no window starts 130 replicas in an hour and reverses direction 19 times; with a 300 s window it starts 13 and reverses once",
    "scale-down without a drain cuts streams: waiting-queue policy with no drain cut 168 streams",
    "lengthen the window beyond the cold start and slow the scale-down (removes most cold starts); then add the drain stack from section 7: grace period, preStop pause, engine drain, PodDisruptionBudget",
    "fixing only flapping leaves users on a removed pod unprotected; fixing only the drain keeps the waste; all counts are simulator output"
]

found_texts = [t for t, fs in text_nodes]
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' once, got {cnt}"
    print(f"   [OK] Label present once: '{exp[:40]}...'")

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Unexpected extra texts: {extras}"
print("4. Exact label fidelity: PASS (No extras, none missing, none duplicated)")

# 5. Forbidden style words check
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout']
for t in found_texts:
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Forbidden style word '{b}' found in '{t}'"
print("5. Forbidden style words: PASS (None found)")

# 6. Arrows check
markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
assert len(markers) == 0, f"Expected 0 arrows, got {len(markers)}"
print("6. Arrows count: PASS (0 source arrows == 0 SVG arrows)")

# 7. Colors check
raw_svg = open("test_sawtooth.svg").read()
assert "#f5f8f5" in raw_svg, "Missing #f5f8f5"
assert "#303a36" in raw_svg, "Missing #303a36"
assert "#207448" in raw_svg, "Missing #207448"
assert "#e8f1ea" in raw_svg, "Missing #e8f1ea"
assert "#db8129" in raw_svg, "Missing #db8129"

oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"7. Colors check: PASS (All present, #db8129 count={len(oranges)})")

# 8. Box Margins and Gaps check
box_rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    w = float(elem.attrib.get('width', '0'))
    h = float(elem.attrib.get('height', '0'))
    if (w == 1600 and h == 1060) or w < 50 or h < 50:
        continue
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    box_rects.append((x, y, w, h))

print(f"Major boxes: {len(box_rects)}")
for x, y, w, h in box_rects:
    m_l = x
    m_r = 1600 - (x + w)
    m_t = y
    m_b = 1060 - (y + h)
    assert m_l >= 40, f"Left margin {m_l} < 40"
    assert m_r >= 40, f"Right margin {m_r} < 40"
    assert m_t >= 40, f"Top margin {m_t} < 40"
    assert m_b >= 40, f"Bottom margin {m_b} < 40"

print("8. Margins: PASS (All >= 40px)")
print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
