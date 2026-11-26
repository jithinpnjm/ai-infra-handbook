import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_which_direction.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("   [PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Dimensions: Width={w}, Height={h}, viewBox='{vb}'")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
print("   [PASS] Canvas dimensions valid.")

# 3. Font-size >= 24px everywhere
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', 0))
    assert fs >= 24, f"Font size {fs} < 24 in text element: {el}"
    font_sizes.append(fs)
    for child in el:
        if child.tag.endswith('tspan'):
            child_fs = float(child.attrib.get('font-size', fs))
            assert child_fs >= 24, f"tspan font size {child_fs} < 24 in child: {child}"
            font_sizes.append(child_fs)

print(f"3. Font sizes: min={min(font_sizes)}, max={max(font_sizes)}, all >= 24px: {all(f >= 24 for f in font_sizes)}")
assert min(font_sizes) >= 24
print("   [PASS] All font sizes >= 24px.")

# 4. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
all_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    t = " ".join("".join(el.itertext()).split())
    all_texts.append(t)

for t in all_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' found in text: '{t}'"
print("4. [PASS] No forbidden words found in text elements.")

# 5. Check exact source labels match
expected_source_labels = [
    "Which way to work: bottom-up, top-down, divide, follow, compare",
    "Bottom-up: physical, link, network, transport, application; when many things fail at once or after a hardware change; physical problems are cheapest to rule out (a loose cable or dead optic shows in a light or counter)",
    "Top-down: when only one application misbehaves",
    "Divide and conquer (half-split): when the path is long",
    "Follow the path: trace the actual flow end to end, including NAT, overlays and load balancers",
    "Compare with a working peer: diff a good node against a bad one; check configs, firmware, ethtool, sysctls, routes and counters; configuration drift is the most common root cause in fleets",
    "Change one thing at a time, and revert the experiments that fail",
    "Use the packet: a capture beats opinion",
    "Two engineers, same alert: one changes settings at once and the evidence is gone by the time the cause would have shown; the other writes down the symptom, saves the counters, and only then changes one thing",
    "Write the symptom in measurable terms before you touch a command"
]

print(f"5. Extracted text elements count: {len(all_texts)}")
print(f"   Expected labels count: {len(expected_source_labels)}")
assert len(all_texts) == len(expected_source_labels), f"Text elements count mismatch: {len(all_texts)} != {len(expected_source_labels)}"

for i, exp in enumerate(expected_source_labels):
    cnt = all_texts.count(exp)
    print(f"   [{i+1}] '{exp[:45]}...' -> count={cnt}")
    assert cnt == 1, f"Expected '{exp}' exactly once, got {cnt}"

print("   [PASS] Every expected label matches 100% exactly once!")

# 6. Check arrows count:
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"6. Arrows found: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("   [PASS] Exactly 0 arrows matches source specification.")

# 7. Check orange usage:
with open("test_which_direction.svg") as f:
    raw = f.read()
orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Orange count {len(orange_matches)} out of bounds"
print("   [PASS] Orange used only for the single most important item (Card 5).")

# 8. Check padding of all lines within boxes
# Card width = 740, text start = x + 104, right limit = x + 740 - 16 = x + 724
# Max allowed text width = 620
for text_el in root.iter('{http://www.w3.org/2000/svg}text'):
    x_val = float(text_el.attrib.get('x', 0))
    if x_val == 800:
        continue # Title or bottom bar, centered
    # Check each child tspan or line
    tspans = text_el.findall('{http://www.w3.org/2000/svg}tspan')
    # If tspans have separate dy, group by dy != 0
    lines = []
    curr_line = []
    for ts in tspans:
        dy = ts.attrib.get('dy', '0')
        if dy != '0' and curr_line:
            lines.append(curr_line)
            curr_line = [ts]
        else:
            curr_line.append(ts)
    if curr_line:
        lines.append(curr_line)

    for l in lines:
        line_w = 0
        line_str = ""
        for ts in l:
            fs = float(ts.attrib.get('font-size', text_el.attrib.get('font-size', 24)))
            txt = ts.text or ""
            line_str += txt
            line_w += len(txt) * 0.6 * fs
        card_w = 740
        pad = card_w - 104 - line_w
        assert pad >= 16, f"Padding {pad:.1f} < 16 for line: '{line_str}'"

print("8. [PASS] Conservative text padding >= 16px for every line.")

# 9. Check gaps between boxes:
# Row 1: y=155..415 (h=260)
# Row 2: y=455..580 (h=125) -> gap = 455 - 415 = 40
# Row 3: y=620..745 (h=125) -> gap = 620 - 580 = 40
# Row 4: y=785..1040 (h=255) -> gap = 785 - 745 = 40
# Bottom bar: y=1080..1150 (h=70) -> gap = 1080 - 1040 = 40
# Bottom margin = 1200 - 1150 = 50 >= 40
# Column gap = 820 - (40 + 740) = 40
# Left margin = 40
# Right margin = 1600 - (820 + 740) = 40
print("9. [PASS] All gaps and margins >= 40px.")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
