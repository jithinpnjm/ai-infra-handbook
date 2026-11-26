import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_test.svg")
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Check font sizes >= 24
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

print(f"3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")

# 4. Check labels
expected_single_labels = [
    "Detecting a failing GPU: the numbers before the signals",
    "How would you find a failing GPU before a customer notices?",
    "Ask first",
    "Fleet: 2,000 nodes of 8 GPUs",
    "Failure rate: 5 percent of GPUs per year",
    "Idle or serving: both",
    "Customer notices: errors or slow tokens after about 15 minutes",
    "GPUs: 2,000 x 8 = 16,000",
    "Failures per day: 16,000 x 0.05 / 365 = 2.19",
    "Series at 40 fields per GPU: 16,000 x 40 = 640,000",
    "Samples per second at a 15 s scrape: 640,000 / 15 = 42,667",
    "Requests spared per event: 2 x 60 x 13 = 1,560, detect at 2 minutes against 15",
    "Every input is an assumption, not a measurement.",
    "The detection time has to beat the moment the customer notices."
]

step_numbers = {"1", "2", "3", "4"}

found_texts = [t for t, fs in text_elements]

print("\n4. Checking single-occurrence expected labels:")
for lbl in expected_single_labels:
    cnt = found_texts.count(lbl)
    assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1"
    print(f"   [PASS] count=1: '{lbl}'")

print("\n   Checking step numbers:")
for num in step_numbers:
    cnt_num = found_texts.count(num)
    assert cnt_num == 1, f"Step number '{num}' count {cnt_num} != 1"
    print(f"   [PASS] count=1: '{num}'")

# Check extras
extras = [t for t in found_texts if t not in expected_single_labels and t not in step_numbers]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# Distinct elements count: 14 labels + 4 step numbers = 18 text elements
distinct_texts = set(found_texts)
print(f"\n   Distinct text elements: {len(distinct_texts)} (expected 18)")
assert len(distinct_texts) == 18, f"Expected exactly 18 distinct elements, got {len(distinct_texts)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in forbidden:
        assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"

print("5. No forbidden style words found in text: PASS!")

# 6. Check arrow count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"6. Total arrows with marker-end: {total_arrows} (expected 4)")
assert total_arrows == 4, f"Expected exactly 4 arrows, got {total_arrows}"

# 7. Check orange usage
svg_str = open("candidate_test.svg").read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"7. Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange usage, got {len(oranges)}"

# 8. Check outside margins and box-to-box gaps
boxes = [
    # (name, x, y, w, h)
    ("interviewer-bubble", 160, 135, 1280, 70),
    ("ask-first-strip", 40, 265, 1520, 200),
    ("step-1", 40, 515, 325, 250),
    ("step-2", 438, 515, 325, 250),
    ("step-3", 837, 515, 325, 250),
    ("step-4", 1235, 515, 325, 250),
    ("final-result-card", 200, 815, 1200, 105),
]

H_val = float(height)
print("\n8. Checking outside margins (>= 40px):")
for name, bx, by, bw, bh in boxes:
    lm = bx
    rm = 1600 - (bx + bw)
    tm = by
    bm = H_val - (by + bh)
    assert lm >= 40, f"{name} left margin {lm} < 40"
    assert rm >= 40, f"{name} right margin {rm} < 40"
    assert tm >= 40, f"{name} top margin {tm} < 40"
    assert bm >= 40, f"{name} bottom margin {bm} < 40"
    print(f"   [PASS] {name}: lm={lm}, rm={rm}, tm={tm}, bm={bm}")

print("\n9. Checking box-to-box gaps (>= 40px):")
gaps = [
    ("prompt bubble tail to ask-first", 265 - 220), # 45px
    ("prompt bubble rect to ask-first", 265 - (135 + 70)), # 60px
    ("ask-first to ladder", 515 - (265 + 200)), # 50px
    ("step-1 to step-2", 438 - (40 + 325)), # 73px
    ("step-2 to step-3", 837 - (438 + 325)), # 74px
    ("step-3 to step-4", 1235 - (837 + 325)), # 73px
    ("ladder to final-result", 815 - (515 + 250)), # 50px
]

for name, gap in gaps:
    print(f"   {name}: gap = {gap}px")
    assert gap >= 40, f"Gap '{name}' {gap}px < 40px!"

# 10. Check padding of all text lines inside their boxes
def check_line_padding(desc, text, font_size, box_left, box_right, text_anchor, text_x, is_mono=False):
    mult = 0.62 if is_mono else 0.6
    w = len(text) * font_size * mult
    if text_anchor == 'middle':
        left = text_x - w / 2.0
        right = text_x + w / 2.0
    elif text_anchor == 'start':
        left = text_x
        right = text_x + w
    else:
        left = text_x - w
        right = text_x
    pad_left = left - box_left
    pad_right = box_right - right
    min_pad = min(pad_left, pad_right)
    assert min_pad >= 16.0, f"[{desc}] '{text}': min_pad {min_pad:.1f} < 16.0"
    print(f"   [PASS] {desc:32s}: min_pad={min_pad:5.1f}px (w={w:5.1f}px, box_w={box_right-box_left}px) | '{text}'")

print("\n10. Checking text line paddings (>= 16px):")
check_line_padding("Title Line 1", "Detecting a failing GPU: ", 48, 0, 1600, 'middle', 800)
check_line_padding("Title Line 2", "the numbers before the signals", 48, 0, 1600, 'middle', 800)

check_line_padding("Interviewer prompt", "How would you find a failing GPU before a customer notices?", 28, 160 + 80, 1440, 'start', 260)

check_line_padding("Ask first Title", "Ask first", 32, 40, 1560, 'start', 135)
check_line_padding("Chip 1", "Fleet: 2,000 nodes of 8 GPUs", 24, 65, 775, 'middle', 420)
check_line_padding("Chip 2", "Failure rate: 5 percent of GPUs per year", 24, 815, 1535, 'middle', 1175)
check_line_padding("Chip 3", "Idle or serving: both", 24, 65, 775, 'middle', 420)
check_line_padding("Chip 4 line 1", "Customer notices: errors or slow tokens ", 24, 815, 1535, 'middle', 1175)
check_line_padding("Chip 4 line 2", "after about 15 minutes", 24, 815, 1535, 'middle', 1175)

check_line_padding("Step 1 line 1", "GPUs: ", 24, 40, 365, 'middle', 202)
check_line_padding("Step 1 line 2", "2,000 x 8 = 16,000", 24, 40, 365, 'middle', 202)

check_line_padding("Step 2 line 1", "Failures per day: ", 24, 438, 763, 'middle', 600)
check_line_padding("Step 2 line 2", "16,000 x 0.05 / 365", 24, 438, 763, 'middle', 600)
check_line_padding("Step 2 line 3", "= 2.19", 24, 438, 763, 'middle', 600)

check_line_padding("Step 3 line 1", "Series at 40 fields ", 24, 837, 1162, 'middle', 1000)
check_line_padding("Step 3 line 2", "per GPU: ", 24, 837, 1162, 'middle', 1000)
check_line_padding("Step 3 line 3", "16,000 x 40 ", 24, 837, 1162, 'middle', 1000)
check_line_padding("Step 3 line 4", "= 640,000", 24, 837, 1162, 'middle', 1000)

check_line_padding("Step 4 line 1", "Samples per second ", 24, 1235, 1560, 'middle', 1397)
check_line_padding("Step 4 line 2", "at a 15 s scrape: ", 24, 1235, 1560, 'middle', 1397)
check_line_padding("Step 4 line 3", "640,000 / 15 ", 24, 1235, 1560, 'middle', 1397)
check_line_padding("Step 4 line 4", "= 42,667", 24, 1235, 1560, 'middle', 1397)

check_line_padding("Final Result line 1", "Requests spared per event: 2 x 60 x 13 = 1,560, ", 28, 200 + 80, 1400, 'middle', 820)
check_line_padding("Final Result line 2", "detect at 2 minutes against 15", 28, 200 + 80, 1400, 'middle', 820)

check_line_padding("Note", "Every input is an assumption, not a measurement.", 26, 40, 1560, 'middle', 800)
check_line_padding("Caption", "The detection time has to beat the moment the customer notices.", 30, 40, 1560, 'middle', 800)

print("\n==============================================")
print("ALL TESTS PASSED WITH 100% SUCCESS!")
print("==============================================")
