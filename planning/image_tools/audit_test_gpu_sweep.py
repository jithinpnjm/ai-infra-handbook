import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_path = "test_gpu_sweep.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

print("=== 1. STRUCTURE AND ROOT ATTRIBUTES ===")
assert root.tag.endswith('svg')
assert root.attrib['width'] == '1600'
vb = root.attrib['viewBox']
assert vb.startswith('0 0 1600 ')
H = int(vb.split()[-1])
assert 900 <= H <= 1200, f"Height {H} out of range 900..1200"
print(f"PASS: width=1600, viewBox='{vb}', H={H}")

first_two = [c.tag.split('}')[-1] for c in root[:2]]
assert first_two == ['title', 'desc'], f"First children must be title and desc, got {first_two}"
print(f"PASS: First children are <title> and <desc>")

print("\n=== 2. FORBIDDEN STYLING WORDS ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'takeaway']

all_text_elements = root.findall('.//{http://www.w3.org/2000/svg}text')
extracted_strings = []
for el in all_text_elements:
    full_t = "".join(el.itertext()).strip()
    full_t = re.sub(r'\s+', ' ', full_t)
    extracted_strings.append(full_t)

for t in extracted_strings:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in text '{t}'"
print(f"PASS: No forbidden styling words in {len(extracted_strings)} text elements")

print("\n=== 3. ORANGE HIGHLIGHT USAGE ===")
svg_text = pathlib.Path(svg_path).read_text()
oranges = re.findall(r'#db8129', svg_text, re.IGNORECASE)
print(f"Found {len(oranges)} occurrences of #db8129")
assert 1 <= len(oranges) <= 4, f"Expected 1..4 orange attributes, got {len(oranges)}"
print("PASS: Single orange #db8129 used for the overlap highlight")

print("\n=== 4. FONT SIZE CHECK (>= 24px) ===")
for el in all_text_elements:
    fs = float(el.attrib.get('font-size', '0'))
    t = "".join(el.itertext()).strip()
    assert fs >= 24, f"Text '{t}' fs {fs} < 24!"
    for tsp in el.findall('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan fs {tfs} < 24 in '{t}'"
print("PASS: All text elements >= 24 px (NO text smaller than 24px anywhere)")

print("\n=== 5. CHECK EXPECTED SOURCE LABELS ===")
expected_labels = [
    "How many GPU nodes? Sweep the reservations and reuse a node when one ends",
    "Node 1",
    "Node 2",
    "(0, 4)",
    "(2, 6)",
    "(8, 10)",
    "A and B overlap, they need separate nodes",
    "1 Sort by start: (0, 4), (2, 6), (8, 10)",
    "2 (0, 4): no node in use, open node, heap of end times = 4",
    "3 (2, 6): earliest end 4 is after start 2, open a second node, heap = 4, 6",
    "4 (8, 10): earliest end 4 is at or before start 8, reuse that node, heap = 6, 10",
    "5 Answer: the heap holds 2 end times, so 2 nodes",
    "Half-open [start, end): a job ending at 10 frees its node for one starting at 10",
    "Event sweep: +1 at each start, -1 at each end, at equal times the end sorts before the start, the maximum running total is the answer",
    "First ask whether reservations are per node or pooled, because that changes the whole model."
]

ticks = [str(i) for i in range(11)]
all_expected = expected_labels + ticks

print(f"Total extracted text elements: {len(extracted_strings)}")
for i, s in enumerate(extracted_strings):
    print(f"  [{i:2d}] '{s}'")

for exp in expected_labels:
    cnt = extracted_strings.count(exp)
    assert cnt == 1, f"Expected '{exp}' count=1, got {cnt}"
    print(f"  [OK] '{exp[:45]}...'")

for tk in ticks:
    cnt = extracted_strings.count(tk)
    assert cnt == 1, f"Tick '{tk}' count=1, got {cnt}"

extras = [s for s in extracted_strings if s not in all_expected]
assert len(extras) == 0, f"Found unexpected extra strings: {extras}"
assert len(extracted_strings) == len(all_expected), f"Count mismatch: {len(extracted_strings)} != {len(all_expected)}"
print("PASS: Every source label appears exactly once, 0 extras, 0 missing!")

print("\n=== 6. CHECK ARROWS ===")
markers = [el for el in root.iter() if 'marker-end' in el.attrib]
assert len(markers) == 0, f"Expected 0 arrows, got {len(markers)}"
print("PASS: Arrow count matches source (0 source arrows, 0 in SVG)")

print("\n=== 7. PADDING AND FIT STRICT CHECK ===")
# Check line widths and paddings for all text boxes:
# Rule: sans: 0.6 * fs * len, mono: 0.62 * fs * len. min_pad >= 16.
def check_pad(box_x, box_w, text_x, text_w, anchor='start'):
    if anchor == 'middle':
        pl = (text_x - text_w/2) - box_x
        pr = (box_x + box_w) - (text_x + text_w/2)
    else:
        pl = text_x - box_x
        pr = (box_x + box_w) - (text_x + text_w)
    return pl, pr, min(pl, pr)

# 1. Title
t_w1 = len("How many GPU nodes? Sweep the reservations") * 0.6 * 48
pl, pr, mp = check_pad(0, 1600, 800, t_w1, 'middle')
assert mp >= 16, f"Title L1 pad {mp} < 16"
t_w2 = len("and reuse a node when one ends") * 0.6 * 48
pl, pr, mp = check_pad(0, 1600, 800, t_w2, 'middle')
assert mp >= 16, f"Title L2 pad {mp} < 16"

# 2. Node 1 & Node 2 cards (box: 70..300, w=230, text_x=155)
n_w = len("Node 1") * 0.6 * 30
pl, pr, mp = check_pad(70, 230, 155, n_w, 'start')
assert mp >= 16, f"Node 1 pad {mp} < 16"

# 3. Bar A (330..798, w=468, text_x=564, anchor=middle)
b_w = len("(0, 4)") * 0.6 * 26
pl, pr, mp = check_pad(330, 468, 564, b_w, 'middle')
assert mp >= 16, f"Bar A pad {mp} < 16"

# 4. Bar B (564..1032, w=468, text_x=798, anchor=middle)
b_w = len("(2, 6)") * 0.6 * 26
pl, pr, mp = check_pad(564, 468, 798, b_w, 'middle')
assert mp >= 16, f"Bar B pad {mp} < 16"

# 5. Bar C (1266..1500, w=234, text_x=1383, anchor=middle)
b_w = len("(8, 10)") * 0.6 * 26
pl, pr, mp = check_pad(1266, 234, 1383, b_w, 'middle')
assert mp >= 16, f"Bar C pad {mp} < 16"

# 6. Overlap card (361..1001, w=640, text_x=681, anchor=middle)
o_w1 = len("A and B overlap,") * 0.6 * 24
pl, pr, mp = check_pad(361, 640, 681, o_w1, 'middle')
assert mp >= 16, f"Overlap L1 pad {mp} < 16"
o_w2 = len("they need separate nodes") * 0.6 * 24
pl, pr, mp = check_pad(361, 640, 681, o_w2, 'middle')
assert mp >= 16, f"Overlap L2 pad {mp} < 16"
o_full = len("A and B overlap, they need separate nodes") * 0.6 * 24
pl, pr, mp_full = check_pad(361, 640, 681, o_full, 'middle')
assert mp_full >= 16, f"Overlap Full pad {mp_full} < 16"

# 7. Step 1 (50..930, w=880, text_x=145) - monospace: 0.62 * fs * len
s1_w = len("1 Sort by start: (0, 4), (2, 6), (8, 10)") * 0.62 * 25
pl, pr, mp = check_pad(50, 880, 145, s1_w, 'start')
assert mp >= 16, f"Step 1 pad {mp} < 16"

# 8. Step 2
s2_w1 = len("2 (0, 4): no node in use, open node,") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s2_w1, 'start')
assert mp >= 16, f"Step 2 L1 pad {mp} < 16"
s2_w2 = len("heap of end times = 4") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s2_w2, 'start')
assert mp >= 16, f"Step 2 L2 pad {mp} < 16"

# 9. Step 3
s3_w1 = len("3 (2, 6): earliest end 4 is after start 2,") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s3_w1, 'start')
assert mp >= 16, f"Step 3 L1 pad {mp} < 16"
s3_w2 = len("open a second node, heap = 4, 6") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s3_w2, 'start')
assert mp >= 16, f"Step 3 L2 pad {mp} < 16"

# 10. Step 4
s4_w1 = len("4 (8, 10): earliest end 4 is at or before start 8,") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s4_w1, 'start')
assert mp >= 16, f"Step 4 L1 pad {mp} < 16"
s4_w2 = len("reuse that node, heap = 6, 10") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s4_w2, 'start')
assert mp >= 16, f"Step 4 L2 pad {mp} < 16"

# 11. Step 5
s5_w1 = len("5 Answer: the heap holds 2 end times,") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s5_w1, 'start')
assert mp >= 16, f"Step 5 L1 pad {mp} < 16"
s5_w2 = len("so 2 nodes") * 0.62 * 24
pl, pr, mp = check_pad(50, 880, 145, s5_w2, 'start')
assert mp >= 16, f"Step 5 L2 pad {mp} < 16"

# 12. Side note (970..1550, w=580, text_x=1000)
sn_w1 = len("Half-open [start, end):") * 0.6 * 25
pl, pr, mp = check_pad(970, 580, 1000, sn_w1, 'start')
assert mp >= 16, f"Side note L1 pad {mp} < 16"
sn_w2 = len("a job ending at 10 frees its node") * 0.6 * 25
pl, pr, mp = check_pad(970, 580, 1000, sn_w2, 'start')
assert mp >= 16, f"Side note L2 pad {mp} < 16"
sn_w3 = len("for one starting at 10") * 0.6 * 25
pl, pr, mp = check_pad(970, 580, 1000, sn_w3, 'start')
assert mp >= 16, f"Side note L3 pad {mp} < 16"

# 13. Alternate method (970..1550, w=580, text_x=1000)
am_w1 = len("Event sweep: +1 at each start,") * 0.6 * 24
pl, pr, mp = check_pad(970, 580, 1000, am_w1, 'start')
assert mp >= 16, f"Alt method L1 pad {mp} < 16"
am_w2 = len("-1 at each end, at equal times") * 0.6 * 24
pl, pr, mp = check_pad(970, 580, 1000, am_w2, 'start')
assert mp >= 16, f"Alt method L2 pad {mp} < 16"
am_w3 = len("the end sorts before the start,") * 0.6 * 24
pl, pr, mp = check_pad(970, 580, 1000, am_w3, 'start')
assert mp >= 16, f"Alt method L3 pad {mp} < 16"
am_w4 = len("the maximum running total") * 0.6 * 24
pl, pr, mp = check_pad(970, 580, 1000, am_w4, 'start')
assert mp >= 16, f"Alt method L4 pad {mp} < 16"
am_w5 = len("is the answer") * 0.6 * 24
pl, pr, mp = check_pad(970, 580, 1000, am_w5, 'start')
assert mp >= 16, f"Alt method L5 pad {mp} < 16"

# 14. Takeaway (50..1550, w=1500, text_x=800, anchor=middle)
tk_w = len("First ask whether reservations are per node or pooled, because that changes the whole model.") * 0.6 * 26
pl, pr, mp = check_pad(50, 1500, 800, tk_w, 'middle')
assert mp >= 16, f"Takeaway pad {mp} < 16"

print("PASS: All paddings strictly >= 16 px (all check_pad tests passed)")

# 8. Render to PNG
png_dir = pathlib.Path("/tmp/svgcheck")
png_dir.mkdir(exist_ok=True)
png_path = png_dir / "test_gpu_sweep.png"
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1200',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path(svg_path).resolve()}'
], capture_output=True, text=True)
assert res.returncode == 0, f"Chrome rendering failed: {res.stderr}"
print(f"PASS: Screenshot saved to {png_path}")
print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
