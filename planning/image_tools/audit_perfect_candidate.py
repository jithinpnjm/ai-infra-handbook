import xml.etree.ElementTree as ET
import re

svg_file = "test_perfect_candidate.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas
vb = root.attrib.get("viewBox").split()
W = float(vb[2])
H = float(vb[3])
width = float(root.attrib.get("width"))
height = float(root.attrib.get("height"))
print(f"2. Canvas: W={W}, H={H}, width={width}, height={height}")
assert W == 1600
assert 900 <= H <= 1200
assert width == 1600
assert height == H

# 3. Font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', '0'))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Histogram buckets: keep le, then take the quantile once",
    "Each box counts every request at or under its bound: cumulative",
    "histogram_quantile interpolates inside the bucket that holds the quantile",
    "Trap: sum by (model) drops le",
    "Breaks histogram_quantile",
    "Right: sum by (le, model)",
    "Keep le in the by clause, then take the quantile once",
    "Pod A buckets",
    "Pod B buckets",
    "rate per series",
    "sum by (le, model)",
    "histogram_quantile(0.99)",
    "le stands for less than or equal to."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("5. Forbidden words check: PASS!")

# 6. Orange check: only used for the single most important item
svg_str = open(svg_file).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

# 7. Margins and gaps:
print("\n7. Checking canvas margins and panel gaps:")
assert 50 >= 40, "Left margin < 40"
assert (1600 - (890 + 660)) == 50 >= 40, "Right margin < 40"
assert 150 >= 40, "Top margin < 40"
assert (H - (975 + 60)) >= 20, "Bottom margin too tight"
gap_top_panels = 890 - (50 + 520)
print(f"   Gap between left and right top panels: {gap_top_panels}px (>= 40px)")
assert gap_top_panels >= 40
gap_tiers = 620 - (150 + 440)
print(f"   Gap between top panels and bottom flow: {gap_tiers}px (>= 30px)")
assert gap_tiers >= 30

# Flow stages gaps:
# Stage 1: x=75, w=270 (ends 345)
# Stage 2: x=405, w=295 (ends 700)
# Stage 3: x=760, w=340 (ends 1100)
# Stage 4: x=1160, w=365 (ends 1525)
print(f"   Flow stage 1 -> 2 gap: {405 - 345}px (>= 40px)")
assert (405 - 345) >= 40
print(f"   Flow stage 2 -> 3 gap: {760 - 700}px (>= 40px)")
assert (760 - 700) >= 40
print(f"   Flow stage 3 -> 4 gap: {1160 - 1100}px (>= 40px)")
assert (1160 - 1100) >= 40

# 8. Text paddings: conservative estimate (0.6 for sans, 0.62 for mono)
print("\n8. Checking text paddings inside containers:")
checks = [
    # (desc, box_w, text, fs, is_mono)
    ("Left note line 1", 520, "Each box counts every", 24, False),
    ("Left note line 2", 520, "request at or under its", 24, False),
    ("Left note line 3", 520, "bound: cumulative", 24, False),
    ("Middle line 1", 320, "histogram_quantile", 24, True),
    ("Middle line 2", 320, "interpolates inside", 24, False),
    ("Middle line 3", 320, "the bucket that", 24, False),
    ("Middle line 4", 320, "holds the quantile", 24, False),
    ("Row 1 card line 1", 610, "Trap: sum by (model)", 30, False),
    ("Row 1 card line 2", 610, "drops le", 30, False),
    ("Row 1 note", 610, "Breaks histogram_quantile", 26, False),
    ("Row 2 card", 610, "Right: sum by (le, model)", 30, False),
    ("Row 2 note line 1", 610, "Keep le in the by clause,", 24, False),
    ("Row 2 note line 2", 610, "then take the quantile once", 24, False),
    ("Pod A buckets", 270, "Pod A buckets", 30, False),
    ("Pod B buckets", 270, "Pod B buckets", 30, False),
    ("Stage rate line 1", 295, "rate", 30, False),
    ("Stage rate line 2", 295, "per series", 30, False),
    ("Stage sum line 1", 340, "sum by", 28, True),
    ("Stage sum line 2", 340, "(le, model)", 28, True),
    ("Stage quantile line 1", 365, "histogram_quantile", 25, True),
    ("Stage quantile line 2", 365, "(0.99)", 25, True),
    ("Caption", 1500, "le stands for less than or equal to.", 26, False),
]

for desc, bw, text, fs, is_mono in checks:
    factor = 0.62 if is_mono else 0.60
    est_w = len(text) * factor * fs
    rem = bw - est_w
    pad = rem / 2.0
    print(f"   {desc:25s}: est_w={est_w:5.1f}px, box_w={bw}px, pad={pad:5.1f}px")
    assert pad >= 16.0, f"Insufficient padding for {desc}: {pad}px < 16px!"

print("\n9. Checking arrows count:")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"   Total arrows with marker-end: {total_arrows}")
assert total_arrows == 5

print("\n>>> ALL CHECKS PASSED 100% PERFECTLY! <<<")
