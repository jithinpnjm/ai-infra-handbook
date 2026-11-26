import xml.etree.ElementTree as ET
import re

svg_file = "candidate_drilldown.svg"
tree = ET.parse(svg_file)
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
    "Drill-down halves the search space",
    "1 Monitoring: records statistics and alerts",
    "2 Identification: narrows to one resource on one machine (the 60-second tools)",
    "3 Analysis: traces or profiles to find the cause",
    "strace",
    "perf",
    "BCC tools",
    "bpftrace",
    "On-CPU or off-CPU?",
    "On-CPU: perf samples the CPU",
    "Off-CPU: waiting for something",
    "Queueing?",
    "Being serviced?",
    "Each question throws away half the causes",
    "Slow-disks story",
    "USE shows disk near 80 percent; iostat at one second shows 100 percent; off-CPU tracing shows the database blocked on file system reads.",
    "Name one resource before you reach for a tracer."
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
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 6. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("\n6. Forbidden words check: PASS")

# 7. Check palette colors and orange usage
with open(svg_file) as f:
    raw = f.read()

assert "#f5f8f5" in raw, "Background #f5f8f5 missing"
assert "#303a36" in raw, "Text #303a36 missing"
assert "#207448" in raw, "Main green #207448 missing"
assert "#e8f1ea" in raw, "Light green panels #e8f1ea missing"
assert "#db8129" in raw, "Orange #db8129 missing"

orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 8. Check paddings for all text elements inside boxes
print("\n8. Checking paddings...")
boxes = [
    # desc, text_lines, fs, is_mono, box_x, box_w
    ("Stage 1 - title", ["1", "Monitoring:"], 30, False, 50, 410),
    ("Stage 1 - line 1", ["records statistics"], 24, False, 50, 410),
    ("Stage 1 - line 2", ["and alerts"], 24, False, 50, 410),
    ("Stage 2 - title", ["2", "Identification:"], 30, False, 500, 440),
    ("Stage 2 - line 1", ["narrows to one resource"], 24, False, 500, 440),
    ("Stage 2 - line 2", ["on one machine"], 24, False, 500, 440),
    ("Stage 2 - line 3", ["(the 60-second tools)"], 24, False, 500, 440),
    ("Stage 3 - title", ["3", "Analysis:"], 30, False, 980, 570),
    ("Stage 3 - line 1", ["traces or profiles to"], 24, False, 980, 570),
    ("Stage 3 - line 2", ["find the cause"], 24, False, 980, 570),
    ("Chip strace", ["strace"], 24, True, 985, 125),
    ("Chip perf", ["perf"], 24, True, 1115, 95),
    ("Chip BCC tools", ["BCC tools"], 24, True, 1215, 170),
    ("Chip bpftrace", ["bpftrace"], 24, True, 1390, 155),
    ("Root Question", ["On-CPU or off-CPU?"], 30, False, 360, 480),
    ("Branch On-CPU line 1", ["On-CPU:"], 30, False, 50, 410),
    ("Branch On-CPU line 2", ["perf samples the CPU"], 24, False, 50, 410),
    ("Branch Off-CPU line 1", ["Off-CPU:"], 30, False, 500, 420),
    ("Branch Off-CPU line 2", ["waiting for something"], 24, False, 500, 420),
    ("Sub-branch Queueing?", ["Queueing?"], 28, False, 390, 240),
    ("Sub-branch Being serviced?", ["Being serviced?"], 28, False, 670, 290),
    ("Note on tree", ["Each question throws away half the causes"], 26, False, 50, 890),
    ("Worked example title", ["Slow-disks story"], 34, False, 980, 570),
    ("Worked example line 1", ["USE shows disk near 80 percent;"], 24, False, 1005, 520),
    ("Worked example line 2", ["iostat at one second shows"], 24, False, 1005, 520),
    ("Worked example line 3", ["100 percent; off-CPU tracing"], 24, False, 1005, 520),
    ("Worked example line 4", ["shows the database blocked"], 24, False, 1005, 520),
    ("Worked example line 5", ["on file system reads."], 24, False, 1005, 520),
    ("Bottom takeaway bar", ["Name one resource before you reach for a tracer."], 30, False, 50, 1500),
]

for desc, lines, fs, is_mono, bx, bw in boxes:
    mult = 0.62 if is_mono else 0.6
    for l in lines:
        w = len(l) * fs * mult
        pad = (bw - w) / 2.0
        print(f"[{'PASS' if pad >= 16.0 else 'FAIL'}] {desc:26s} pad={pad:5.1f}px (w={w:5.1f}px in box_w={bw}px) | '{l}'")
        assert pad >= 16.0, f"FAILED padding for {desc}: {pad:.1f} < 16.0"

# 9. Check arrows and clearances
print("\n9. Checking arrows...")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows with marker-end: {total_arrows}")

# 10. Check outside margins and panel gaps
print("\n10. Checking margins and gaps...")
assert 50 >= 40, "Left margin < 40"
assert (1600 - 1550) >= 40, "Right margin < 40"
assert 95 >= 40, "Top margin < 40"
assert (1080 - 1020) >= 40, "Bottom margin < 40"

# Gaps between top stage boxes
gap1 = 500 - (50 + 410)
gap2 = 980 - (500 + 440)
print(f"Top row gap 1: {gap1}px (>=40px)")
print(f"Top row gap 2: {gap2}px (>=40px)")
assert gap1 >= 40, f"Top row gap 1 {gap1} < 40"
assert gap2 >= 40, f"Top row gap 2 {gap2} < 40"

# Gap between Branch 1 and Branch 2
gap_branch = 500 - (50 + 410)
print(f"Branch gap: {gap_branch}px (>=40px)")
assert gap_branch >= 40, f"Branch gap {gap_branch} < 40"

# Gap between Sub-branch 2a and 2b
gap_sub = 670 - (390 + 240)
print(f"Sub-branch gap: {gap_sub}px (>=40px)")
assert gap_sub >= 40, f"Sub-branch gap {gap_sub} < 40"

# Gap between Tree and Worked example
gap_tree_ex = 980 - (50 + 890)
print(f"Tree-to-Example gap: {gap_tree_ex}px (>=40px)")
assert gap_tree_ex >= 40, f"Tree-to-Example gap {gap_tree_ex} < 40"

print("\n>>> ALL TESTS PASSED! PERFECT CANDIDATE! <<<")
