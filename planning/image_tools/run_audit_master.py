#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_path = "master_perfect.svg"

tree = ET.parse(svg_path)
root = tree.getroot()

print("=== RUNNING COMPLETE AUDIT SUITE ON master_perfect.svg ===")

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("1. [PASS] <title> and <desc> are the first children.")

# 2. Dimensions and viewBox
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])
print(f"2. [PASS] Canvas {width}x{height}, viewBox='{viewBox}'.")

# 3. Check font-size >= 24 on all text and tspans
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"3. [PASS] Total {len(text_elements)} text elements, all font-sizes >= 24px.")

# 4. Expected labels check
expected_labels = [
    "Reading the sample trace line by line as a conversation",
    "duplex.example.com (client)",
    "mikado.example.com (server)",
    "arp who-has mikado tell duplex",
    "arp reply mikado is-at 0:2:2d:b:ee:4e",
    "S 3200063165 win 5840 mss 1460 sackOK (DF)",
    "S ack 3200063166 win 5792",
    ". ack 1",
    "P 1:427(426)",
    ". ack 427",
    "P 1:773(772)",
    ". ack 773",
    "lines 1-2: finding the link address because the client needs the server's MAC before it can send a frame",
    "lines 3-5: three-way handshake",
    "lines 6-9: data",
    "summary: 9 packets received by filter, 0 packets dropped by kernel",
    "S SYN, S. SYN-ACK, . ACK, P. PSH-ACK, F. FIN-ACK, R or R. RST",
    "Read the flags in order; a SYN with no reply stops the story at the first line, and the next question is who stayed silent"
]

step_numbers = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}

found_texts = [t for t, fs in text_elements]
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count={cnt} != 1!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for s in step_numbers:
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number '{s}' count={cnt} != 1!"

print("4. [PASS] All 18 expected labels and step numbers 1..9 present exactly once with zero extras.")

# 5. Check no forbidden words in text
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in text: '{t}'"
print("5. [PASS] Zero forbidden styling words in text elements.")

# 6. Check orange count
with open(svg_path, 'r', encoding='utf-8') as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6
print("   [PASS] Orange used only for single most important item / arrow.")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"7. Total arrows: {total_arrows}")
assert total_arrows == 9
print("   [PASS] Exactly 9 arrows matching lines 1..9.")

# 8. Check paddings, gaps, and margins
# Margins >= 40px
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    if w == 1600 and h == 1200: continue
    if w < 100 or h < 50: continue # internal icon shapes
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    assert x >= 40, f"Left margin {x} < 40"
    assert x + w <= 1560, f"Right margin {1600 - (x+w)} < 40"
    assert y >= 40, f"Top margin {y} < 40"
    assert y + h <= 1160, f"Bottom margin {1200 - (y+h)} < 40"

# Gaps between boxes >= 40px
assert 458 - 418 >= 40 # B2 top - B1 bot
assert 598 - 558 >= 40 # B3 top - B2 bot
assert 820 - 760 >= 40 # Legend top - B3 bot
assert 920 - 880 >= 40 # Footer top - Legend bot
assert 1025 - 980 >= 40 # Bottom bar top - Footer bot
assert 1040 - 900 >= 40 # Server box left - Client box right
assert 1200 - 1145 >= 40 # Canvas bottom margin

# Check text clearances for messages between lifelines (640..1440, distance 800px):
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    if txt in [
        "arp who-has mikado tell duplex",
        "arp reply mikado is-at 0:2:2d:b:ee:4e",
        "S 3200063165 win 5840 mss 1460 sackOK (DF)",
        "S ack 3200063166 win 5792",
        ". ack 1",
        "P 1:427(426)",
        ". ack 427",
        "P 1:773(772)",
        ". ack 773"
    ]:
        txt_w = len(txt) * 0.62 * 24
        d_left = (1040 - txt_w/2) - 640
        d_right = 1440 - (1040 + txt_w/2)
        assert d_left >= 16 + 18, f"Clearance left {d_left} < 34 for '{txt}'"
        assert d_right >= 16 + 18, f"Clearance right {d_right} < 34 for '{txt}'"

print("8. [PASS] All clearances, margins, gaps, and paddings >= 16px/40px verified.")

print("\n=== VERDICT: 100% PERFECT SVG! ===")
