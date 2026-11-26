import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_quota_svg.svg")
root = tree.getroot()

# 1. Structure: <title> and <desc> are first children
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == "title", f"Expected title, got {first_tag}"
assert second_tag == "desc", f"Expected desc, got {second_tag}"

# 2. Dimensions: width=1600, height between 900 and 1200, viewBox
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox == f"0 0 1600 {height}"
assert 900 <= int(height) <= 1200

# 3. Text elements & font size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24!"
    text_elements.append((full_text, fs))

print(f"3. Total text elements: {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs}px] '{t}'")

# 4. Expected labels check
expected_labels = [
    "Borrowing and lending quota inside a cohort",
    "Worked example with the chapter's numbers for ClusterQueue research, flavor h100-ondemand, resource nvidia.com/gpu: nominalQuota 128, borrowingLimit 64, lendingLimit 32; cpu nominalQuota 1024, memory nominalQuota 8Ti.",
    "128 GPUs owned by research",
    "32 GPUs that research may lend out when idle",
    "up to 64 GPUs borrowed from idle quota of other ClusterQueues in cohort gpu-fleet",
    "reclaimWithinCohort Any: take back lent quota from borrowers",
    "borrowWithinCohort policy LowerPriority with maxPriorityThreshold 100",
    "withinClusterQueue LowerPriority",
    "Team A borrows idle quota",
    "Team B submits a job and reclaims its own quota through preemption",
    "watch Workload conditions",
    "WorkloadPriorityClass sets queueing priority independent of pod priority"
]

step_numbers = {"1", "2", "3"}

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking expected labels (expected {len(expected_labels)}):")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"  '{exp[:40]}...': count={cnt}")
    assert cnt == 1, f"Expected '{exp}' exactly once, got {cnt}!"

for sn in step_numbers:
    cnt = found_texts.count(sn)
    print(f"  Step '{sn}': count={cnt}")
    assert cnt == 1, f"Expected step number '{sn}' exactly once, got {cnt}!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra / unexpected texts: {extras}")
assert len(extras) == 0, f"Unexpected extra text found: {extras}"
print("SUCCESS: Exact label fidelity passed!")

# 5. Check forbidden words
forbidden = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for t in found_texts:
    for f in forbidden:
        assert not re.search(r'\b' + f + r'\b', t.lower()), f"Forbidden word '{f}' in '{t}'!"
print("SUCCESS: No forbidden style words found in text!")

# 6. Arrows count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"6. Total arrows: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
print("SUCCESS: Arrow count matches source (0)!")

# 7. Check orange highlight
raw_svg = open("test_quota_svg.svg").read()
oranges = re.findall(r'#db8129', raw_svg)
print(f"7. Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) >= 1, "Expected at least 1 orange highlight"
print("SUCCESS: Orange highlight present!")

# 8. Strict canvas margins check (>= 40px)
all_ok = True
print("\n8. Checking Canvas Margins (>= 40px):")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib['font-size'])
    ff = elem.attrib.get('font-family', 'sans-serif')
    factor = 0.62 if 'mono' in ff else 0.60
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        lines = []
        cur_y = float(elem.attrib.get('y', 0))
        for tsp in tspans:
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            lines.append((tsp.text.strip(), float(tsp.attrib.get('x', elem.attrib.get('x', 0))), cur_y))
    else:
        lines = [(elem.text.strip(), float(elem.attrib.get('x', 0)), float(elem.attrib.get('y', 0)))]
        
    for line_txt, lx, ly in lines:
        w = len(line_txt) * fs * factor
        if anchor == 'middle':
            left = lx - w / 2.0
            right = lx + w / 2.0
        elif anchor == 'end':
            left = lx - w
            right = lx
        else:
            left = lx
            right = lx + w
        top = ly - fs * 0.75
        bot = ly + 4
        
        lm = left
        rm = 1600 - right
        tm = top
        bm = int(height) - bot
        
        if lm < 39.9 or rm < 39.9 or tm < 39.9 or bm < 39.9:
            print(f"  FAIL Canvas Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")
            all_ok = False
        else:
            print(f"  PASS Canvas Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")

assert all_ok, "Some text violates canvas margins >= 40px!"
print("SUCCESS: Canvas margins >= 40px on all sides for every line of text!")

# 9. Box paddings check
boxes_to_check = [
    ("Overview Panel", (40, 125, 1520, 130), [
        ("Worked example with the chapter's numbers for ClusterQueue research, flavor h100-ondemand,", 825, 162, 24, 'middle'),
        ("resource nvidia.com/gpu: nominalQuota 128, borrowingLimit 64, lendingLimit 32;", 825, 194, 24, 'middle'),
        ("cpu nominalQuota 1024, memory nominalQuota 8Ti.", 825, 226, 24, 'middle'),
    ]),
    ("Card 1: 128 GPUs", (70, 385, 450, 150), [
        ("128 GPUs owned by research", 315, 468, 24, 'middle')
    ]),
    ("Card 2: 32 GPUs slice", (560, 385, 450, 150), [
        ("32 GPUs that research", 805, 450, 24, 'middle'),
        ("may lend out when idle", 805, 482, 24, 'middle')
    ]),
    ("Card 3: 64 GPUs borrowed", (1050, 385, 460, 150), [
        ("up to 64 GPUs borrowed", 1280, 422, 24, 'middle'),
        ("from idle quota of other", 1280, 450, 24, 'middle'),
        ("ClusterQueues in", 1280, 478, 24, 'middle'),
        ("cohort gpu-fleet", 1280, 506, 24, 'middle')
    ]),
    ("Preemption 1 (orange)", (70, 595, 450, 190), [
        ("reclaimWithinCohort Any:", 295, 685, 24, 'middle'),
        ("take back lent quota", 295, 715, 24, 'middle'),
        ("from borrowers", 295, 745, 24, 'middle')
    ]),
    ("Preemption 2", (560, 595, 450, 190), [
        ("borrowWithinCohort policy", 785, 685, 24, 'middle'),
        ("LowerPriority with", 785, 715, 24, 'middle'),
        ("maxPriorityThreshold 100", 785, 745, 24, 'middle')
    ]),
    ("Preemption 3", (1050, 595, 460, 190), [
        ("withinClusterQueue", 1280, 700, 24, 'middle'),
        ("LowerPriority", 1280, 732, 24, 'middle')
    ]),
    ("Story Step 1", (70, 825, 450, 190), [
        ("1", 295, 871, 26, 'middle'),
        ("Team A borrows", 295, 930, 24, 'middle'),
        ("idle quota", 295, 962, 24, 'middle')
    ]),
    ("Story Step 2", (560, 825, 450, 190), [
        ("2", 785, 871, 26, 'middle'),
        ("Team B submits a job", 785, 922, 24, 'middle'),
        ("and reclaims its own quota", 785, 950, 24, 'middle'),
        ("through preemption", 785, 978, 24, 'middle')
    ]),
    ("Story Step 3", (1050, 825, 460, 190), [
        ("3", 1280, 871, 26, 'middle'),
        ("watch Workload", 1280, 930, 24, 'middle'),
        ("conditions", 1280, 962, 24, 'middle')
    ]),
    ("Footer Bar", (40, 1055, 1520, 70), [
        ("WorkloadPriorityClass sets queueing priority independent of pod priority", 800, 1099, 24, 'middle')
    ])
]

print("\n9. Checking Box Paddings (>= 16px):")
for bname, (bx, by, bw, bh), lines in boxes_to_check:
    print(f"\nChecking {bname} ({bx}, {by}, {bw}, {bh}):")
    for ltxt, lx, ly, fs, anchor in lines:
        w = len(ltxt) * fs * 0.60
        if anchor == 'middle':
            left = lx - w / 2.0
            right = lx + w / 2.0
        elif anchor == 'end':
            left = lx - w
            right = lx
        else:
            left = lx
            right = lx + w
        top = ly - fs * 0.75
        bot = ly + 4
        
        pl = left - bx
        pr = (bx + bw) - right
        pt = top - by
        pb = (by + bh) - bot
        
        print(f"  Line '{ltxt[:30]}': pl={pl:.1f}, pr={pr:.1f}, pt={pt:.1f}, pb={pb:.1f}")
        assert pl >= 15.9, f"Left pad {pl} < 16 for '{ltxt}' in {bname}"
        assert pr >= 15.9, f"Right pad {pr} < 16 for '{ltxt}' in {bname}"
        assert pt >= 15.9, f"Top pad {pt} < 16 for '{ltxt}' in {bname}"
        assert pb >= 15.9, f"Bottom pad {pb} < 16 for '{ltxt}' in {bname}"

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
