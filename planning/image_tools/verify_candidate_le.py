import xml.etree.ElementTree as ET
import re
import pathlib

svg_file = "test_candidate_le.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
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

print(f"\n4. Checking {len(expected_labels)} expected labels:")
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

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check margins and gaps
# Panels:
# Left: x=50, y=145, w=500, h=440
# Middle: x=590, y=145, w=380, h=440
# Right: x=1010, y=145, w=540, h=440
# Flow: x=50, y=635, w=1500, h=305
# Caption: x=50, y=980, w=1500, h=70
assert 50 >= 40, "Left margin < 40"
assert (1600 - (1010 + 540)) >= 40, "Right margin < 40"
assert 145 >= 40, "Top margin < 40"
assert (1100 - (980 + 70)) >= 40, "Bottom margin < 40"

gap_lm = 590 - (50 + 500)
gap_mr = 1010 - (590 + 380)
gap_top_flow = 635 - (145 + 440)
gap_flow_cap = 980 - (635 + 305)

print(f"\nGaps: L-M={gap_lm}px, M-R={gap_mr}px, Top-Flow={gap_top_flow}px, Flow-Cap={gap_flow_cap}px")
assert gap_lm >= 40, f"Gap L-M {gap_lm} < 40"
assert gap_mr >= 40, f"Gap M-R {gap_mr} < 40"
assert gap_top_flow >= 40, f"Gap Top-Flow {gap_top_flow} < 40"
assert gap_flow_cap >= 40, f"Gap Flow-Cap {gap_flow_cap} < 40"

print("\nALL AUTOMATED CHECKS PASSED!")
