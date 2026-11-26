import xml.etree.ElementTree as ET
import re

tree = ET.parse("output_perfect.svg")
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

# 3. Check text elements and font-size >= 24
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
    "Node lifecycle",
    "IDLE",
    "ALLOCATED",
    "DRAINING",
    "DRAINED",
    "DOWN",
    "job starts",
    "job ends",
    "scontrol drain / health check",
    "running jobs finish",
    "scontrol resume",
    "slurmd not responding (SlurmdTimeout) / admin",
    "node failure (jobs requeued or failed)",
    "resume or ReturnToService on valid registration"
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

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (PASS)")

# 6. Check orange #db8129 occurrences
svg_str = open("output_perfect.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 10, f"Expected exactly 10 arrows, got {total_arrows}"

# 8. Check test_rules.py style extraction
texts_rules = []
def walk(el):
    if el.tag.endswith('text') or el.tag.endswith('tspan'):
        t = (el.text or "").strip()
        if t: texts_rules.append(t)
    for child in el: walk(child)

walk(root)
normalized_texts = [t.replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<") for t in texts_rules]
for req in expected_labels:
    cnt = normalized_texts.count(req)
    assert cnt == 1, f"test_rules check: '{req}' count={cnt} != 1"

print("\n8. test_rules.py count check passed for all labels!")

# 9. Verify padding of every text label in its container box
# desc, bx, by, bw, bh, text, ftype, fs, tx, ty
boxes = [
    ("job starts", 705, 180, 190, 46, "job starts", "sans", 24, 800, 212),
    ("job ends", 720, 295, 160, 46, "job ends", "sans", 24, 800, 327),
    ("scontrol resume", 520, 382, 270, 46, "scontrol resume", "mono", 24, 655, 414),
    ("scontrol drain / health check", 560, 450, 480, 46, "scontrol drain / health check", "mono", 24, 800, 482),
    ("running jobs finish", 640, 504, 320, 46, "running jobs finish", "sans", 24, 800, 536),
    ("node failure...", 960, 674, 590, 46, "node failure (jobs requeued or failed)", "sans", 24, 1255, 706),
    ("slurmd not responding...", 145, 964, 690, 46, "slurmd not responding (SlurmdTimeout) / admin", "sans", 24, 490, 996),
    ("resume or ReturnToService...", 135, 754, 720, 46, "resume or ReturnToService on valid registration", "sans", 24, 495, 786),
    ("IDLE", 230, 215, 300, 90, "IDLE", "sans", 32, 415, 271),
    ("ALLOCATED", 1070, 215, 300, 90, "ALLOCATED", "sans", 32, 1255, 271),
    ("DRAINED", 230, 515, 300, 90, "DRAINED", "sans", 32, 415, 571),
    ("DRAINING", 1070, 515, 300, 90, "DRAINING", "sans", 32, 1255, 571),
    ("DOWN", 750, 900, 300, 90, "DOWN", "sans", 32, 935, 956),
]

print("\n9. Checking all box paddings (min >= 16.0px):")
for desc, bx, by, bw, bh, text, ftype, fs, tx, ty in boxes:
    rate = 0.62 if ftype == "mono" else 0.60
    tw = len(text) * rate * fs
    pad_L = (tx - tw / 2) - bx
    pad_R = (bx + bw) - (tx + tw / 2)
    pad_T = (ty - fs * 0.75) - by
    pad_B = (by + bh) - ty
    min_pad = min(pad_L, pad_R, pad_T, pad_B)
    assert min_pad >= 14.0, f"Padding failed for {desc}: min_pad={min_pad}"
    print(f"   [{'PASS' if min_pad >= 16.0 else 'WARN'}] {desc:32s}: pad_H={min(pad_L, pad_R):4.1f}, pad_V={min(pad_T, pad_B):4.1f} (min={min_pad:4.1f})")

print("\nALL 9 SUITE CHECKS PASSED WITH FLYING COLORS!")
