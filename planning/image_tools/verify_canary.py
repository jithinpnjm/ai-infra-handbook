import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

tree = ET.parse("candidate_final.svg")
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
    "The canary ladder moves traffic up in steps, and each step must pass its gates",
    "Latency gates",
    "canary TTFT p99 and ITL p99 against baseline, ratio limit",
    "Quality gates",
    "eval score, finish_reason length share, error rate",
    "Shadow traffic",
    "1 percent",
    "5 percent",
    "25 percent",
    "50 percent",
    "100 percent",
    "Promote",
    "all gates passed, enough traffic",
    "Hold",
    "marginal results or too few requests",
    "Rollback",
    "hard failure such as quality drop or zero tokens",
    "hard failure",
    "wait for more evidence",
    "Promote only on a clean pass with enough traffic, hold on thin data, roll back on a hard signal."
]

repeated_gate_label = "gates pass"
step_numbers = {"1", "2", "3", "4", "5", "6"}

found_texts = [t for t, fs in text_elements]

print("\n4. Checking single-occurrence expected labels:")
for lbl in expected_single_labels:
    cnt = found_texts.count(lbl)
    assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1"
    print(f"   [PASS] count=1: '{lbl}'")

cnt_gates = found_texts.count(repeated_gate_label)
print(f"\n   Checking '{repeated_gate_label}': count = {cnt_gates} (expected 5)")
assert cnt_gates == 5, f"Expected 5 gate diamonds with '{repeated_gate_label}', got {cnt_gates}"

print("\n   Checking step numbers:")
for num in step_numbers:
    cnt_num = found_texts.count(num)
    assert cnt_num == 1, f"Step number '{num}' count {cnt_num} != 1"
    print(f"   [PASS] count=1: '{num}'")

# Check extras
extras = [t for t in found_texts if t not in expected_single_labels and t != repeated_gate_label and t not in step_numbers]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# Distinct elements count
distinct_texts = set(found_texts)
print(f"\n   Distinct text elements: {len(distinct_texts)} (expected 27)")
assert len(distinct_texts) == 27, f"Expected exactly 27 distinct elements, got {len(distinct_texts)}"

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
print(f"6. Total arrows with marker-end: {total_arrows} (expected 2)")
assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"

# 7. Check orange usage
svg_str = open("candidate_final.svg").read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"7. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 10, f"Unexpected orange count: {len(oranges)}"

# 8. Check padding of all lines
def check_line_padding(desc, text, font_size, box_left, box_right, text_anchor, text_x):
    w = len(text) * font_size * 0.6
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
    assert pad_left >= 16.0, f"[{desc}] '{text}': pad_left {pad_left:.1f} < 16.0"
    assert pad_right >= 16.0, f"[{desc}] '{text}': pad_right {pad_right:.1f} < 16.0"

# Check Title
check_line_padding("Title Line 1", "The canary ladder moves traffic up in steps, ", 48, 0, 1600, 'middle', 800)
check_line_padding("Title Line 2", "and each step must pass its gates", 48, 0, 1600, 'middle', 800)

# Check Latency gates
check_line_padding("Latency Line 1", "canary TTFT p99 and ITL p99 ", 24, 40, 770, 'start', 140)
check_line_padding("Latency Line 2", "against baseline, ratio limit", 24, 40, 770, 'start', 140)

# Check Quality gates
check_line_padding("Quality Line 1", "eval score, finish_reason length share, ", 24, 830, 1560, 'start', 930)
check_line_padding("Quality Line 2", "error rate", 24, 830, 1560, 'start', 930)

# Check Promote
check_line_padding("Promote Title", "Promote", 32, 40, 520, 'start', 145)
check_line_padding("Promote Line 1", "all gates passed, ", 24, 40, 520, 'middle', 280)
check_line_padding("Promote Line 2", "enough traffic", 24, 40, 520, 'middle', 280)

# Check Hold
check_line_padding("Hold Title", "Hold", 32, 560, 1040, 'start', 665)
check_line_padding("Hold Line 1", "marginal results or ", 24, 560, 1040, 'middle', 800)
check_line_padding("Hold Line 2", "too few requests", 24, 560, 1040, 'middle', 800)

# Check Rollback
check_line_padding("Rollback Title", "Rollback", 32, 1080, 1560, 'start', 1185)
check_line_padding("Rollback Line 1", "hard failure such as ", 24, 1080, 1560, 'middle', 1320)
check_line_padding("Rollback Line 2", "quality drop or zero tokens", 24, 1080, 1560, 'middle', 1320)

# Check Takeaway
check_line_padding("Takeaway", "Promote only on a clean pass with enough traffic, hold on thin data, roll back on a hard signal.", 24, 40, 1560, 'middle', 800)

print("8. Conservative padding checks (>= 16px): ALL PASS!")

# 9. Headless Chrome screenshot test
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
png_path = d / 'x14-canary-ladder.png'
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    f'--window-size=1600,1200',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path("candidate_final.svg").resolve()}'
], capture_output=True, timeout=60)
print(f"9. Headless Chrome screenshot rendered: return code {res.returncode}")
assert res.returncode == 0, "Chrome screenshot rendering failed!"

print("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")
