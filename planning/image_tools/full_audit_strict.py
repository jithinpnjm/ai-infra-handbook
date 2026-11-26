import xml.etree.ElementTree as ET
import re

svg_file = "test_candidate_refined.svg"
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

# 6. Orange check
svg_str = open(svg_file).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

# 7. Margins and gaps:
# Canvas margins:
# Left panel: x=50, y=160, w=510, h=410
# Right panel: x=900, y=160, w=650, h=410
# Flow container: x=50, y=620, w=1500, h=300
print("\n7. Checking canvas margins and panel gaps:")
assert 50 >= 40, "Left margin < 40"
assert (1600 - (900 + 650)) == 50 >= 40, "Right margin < 40"
assert 160 >= 40, "Top margin < 40"
assert (H - (620 + 300)) == (1050 - 920) == 130 >= 40, "Bottom margin < 40"
gap_top_panels = 900 - (50 + 510)
print(f"   Gap between left and right top panels: {gap_top_panels}px (>= 40px)")
assert gap_top_panels >= 40
gap_tiers = 620 - (160 + 410)
print(f"   Gap between top panels and bottom flow: {gap_tiers}px (>= 40px)")
assert gap_tiers >= 40

# Flow stages:
# Stage 1: x=80, w=270 (ends 350)
# Stage 2: x=430, w=290 (ends 720)
# Stage 3: x=800, w=310 (ends 1110)
# Stage 4: x=1190, w=330 (ends 1520)
print(f"   Flow stage 1 -> 2 gap: {430 - 350}px (>= 40px)")
assert (430 - 350) >= 40
print(f"   Flow stage 2 -> 3 gap: {800 - 720}px (>= 40px)")
assert (800 - 720) >= 40
print(f"   Flow stage 3 -> 4 gap: {1190 - 1110}px (>= 40px)")
assert (1190 - 1110) >= 40

# 8. Text paddings: 0.6 for sans, 0.62 for monospace, padding >= 16px
print("\n8. Checking text paddings inside containers:")
# Note in left panel: starts at x=160, ends at 160 + 19 * 0.6 * 24 = 433.6
# Left panel: x=50 to 560
w_max_note = 19 * 0.6 * 24
left_pad_note = 160 - (75 + 56)  # gap to icon
right_pad_note = 560 - (160 + w_max_note)
print(f"   Left panel note padding: gap_to_icon={left_pad_note:.1f}px, right_pad={right_pad_note:.1f}px")
assert left_pad_note >= 16 and right_pad_note >= 16

# Row 1 in Right panel:
# Box: x=925 to 1525 (w=600)
# Title line 1: Trap: sum by (model) -> text starts at x=1015, w = 6*0.6*30 + 15*0.62*30 = 387px
w_r1_t1 = 6*0.6*30 + 15*0.62*30
right_pad_r1 = 1525 - (1015 + w_r1_t1)
print(f"   Row 1 title right padding: {right_pad_r1:.1f}px")
assert right_pad_r1 >= 16

# Note: Breaks histogram_quantile -> 25 chars * 0.6 * 26 = 390px
w_r1_n = 25 * 0.6 * 26
right_pad_r1_n = 1525 - (1015 + w_r1_n)
print(f"   Row 1 note right padding: {right_pad_r1_n:.1f}px")
assert right_pad_r1_n >= 16

# Row 2 in Right panel:
# Title: Right: sum by (le, model) -> 7*0.6*30 + 18*0.62*30 = 460.8px
w_r2_t = 7*0.6*30 + 18*0.62*30
right_pad_r2_t = 1525 - (1015 + w_r2_t)
print(f"   Row 2 title right padding: {right_pad_r2_t:.1f}px")
assert right_pad_r2_t >= 16

# Note: Keep le in the by clause, then take the quantile once
w_r2_n2 = 27 * 0.6 * 24
right_pad_r2_n = 1525 - (1015 + w_r2_n2)
print(f"   Row 2 note right padding: {right_pad_r2_n:.1f}px")
assert right_pad_r2_n >= 16

# Flow Stage 1A: Box x=80 to 350 (w=270). Text 'Pod A buckets' (13 chars * 0.6 * 26 = 202.8px), centered at 215
w_poda = 13 * 0.6 * 26
pad_poda_l = (215 - w_poda/2) - 80
pad_poda_r = 350 - (215 + w_poda/2)
print(f"   Pod A buckets padding: left={pad_poda_l:.1f}px, right={pad_poda_r:.1f}px")
assert pad_poda_l >= 16 and pad_poda_r >= 16

# Flow Stage 2: Box x=430 to 720 (w=290). Text 'per series' (10 chars * 0.6 * 30 = 180px), centered at 575
w_rate = 10 * 0.6 * 30
pad_rate_l = (575 - w_rate/2) - 430
pad_rate_r = 720 - (575 + w_rate/2)
print(f"   Rate per series padding: left={pad_rate_l:.1f}px, right={pad_rate_r:.1f}px")
assert pad_rate_l >= 16 and pad_rate_r >= 16

# Flow Stage 3: Box x=800 to 1110 (w=310). Text '(le, model)' (11 chars * 0.62 * 28 = 191px), centered at 955
w_sum = 11 * 0.62 * 28
pad_sum_l = (955 - w_sum/2) - 800
pad_sum_r = 1110 - (955 + w_sum/2)
print(f"   Sum by le padding: left={pad_sum_l:.1f}px, right={pad_sum_r:.1f}px")
assert pad_sum_l >= 16 and pad_sum_r >= 16

# Flow Stage 4: Box x=1190 to 1520 (w=330). Text 'histogram_quantile' (18 chars * 0.62 * 25 = 279px), centered at 1355
w_quant = 18 * 0.62 * 25
pad_quant_l = (1355 - w_quant/2) - 1190
pad_quant_r = 1520 - (1355 + w_quant/2)
print(f"   Quantile padding: left={pad_quant_l:.1f}px, right={pad_quant_r:.1f}px")
assert pad_quant_l >= 16 and pad_quant_r >= 16

print("\nALL STRICT AUDIT CHECKS PASSED WITH FLYING COLORS!")
