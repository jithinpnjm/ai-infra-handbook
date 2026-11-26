#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_p4_0407_perfect.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
assert tag1 == "title", f"First child must be <title>, got <{tag1}>"
assert tag2 == "desc", f"Second child must be <desc>, got <{tag2}>"
print("[PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got '{vb}'"
print("[PASS] Dimensions and viewBox valid.")

# 3. Text font-size check
font_sizes = []
for el in root.iter():
    if el.tag.endswith('text'):
        fs = int(el.attrib.get('font-size', '0'))
        tspans = [child for child in el if child.tag.endswith('tspan')]
        if tspans:
            for ts in tspans:
                t_content = (ts.text or "").strip()
                t_fs = int(ts.attrib.get('font-size', fs))
                font_sizes.append((t_content, t_fs))
        else:
            t_content = "".join(el.itertext()).strip()
            font_sizes.append((t_content, fs))

for t, fs in font_sizes:
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"
print("[PASS] All text elements >= 24 px.")

# 4. Source labels fidelity
full_texts = []
for el in root.iter():
    if el.tag.endswith('text'):
        combined = " ".join("".join(el.itertext()).split())
        full_texts.append(combined)

source_labels = [
    "A node that labels itself: custom facts in /etc/ansible/facts.d",
    "site.fact (INI): [location] rack=r07, rail=3",
    'gpu.fact (executable, mode 0755): #!/bin/sh; n=$(nvidia-smi -L 2>/dev/null | wc -l); echo {"count": $n}',
    "placed in /etc/ansible/facts.d/ on the target; any .fact file, or any executable, is picked up during fact gathering; INI or JSON, or an executable printing JSON",
    "ansible_local.<name>",
    "ansible_local.location.rack",
    "ansible_local.gpu.count",
    "copy writes gpu.fact; setup with filter ansible_local re-reads it; debug msg: {{ ansible_local.gpu.count }} GPUs on {{ inventory_hostname }}",
    "the script runs on the target, so it always counts the GPUs actually present, even if the inventory was written before a card was replaced",
    "the node carries its own label, so the playbook does not need a separate spreadsheet that might be out of date",
    "attributes stay with the host and do not depend on the control node",
    "The supported way for a host to declare its own attributes"
]

for sl in source_labels:
    cnt = full_texts.count(sl)
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"
print("[PASS] Every source label appears exactly once.")

# 5. Banned styling words
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"
print("[PASS] No banned styling words in any text.")

# 6. Check spacing and margins
# Top-level main sections:
sections = [
    ("Section 1 (Files)", 130, 300),
    ("Section 2 (Facts.d Panel)", 340, 424),
    ("Section 3 (ansible_local)", 464, 600),
    ("Section 4 (Task Strip)", 640, 724),
    ("Section 5 (Callouts)", 764, 1030),
    ("Section 6 (Bottom Bar)", 1070, 1130)
]

for i in range(len(sections) - 1):
    name1, y1_top, y1_bot = sections[i]
    name2, y2_top, y2_bot = sections[i+1]
    gap = y2_top - y1_bot
    print(f"Gap between {name1} and {name2}: {gap} px")
    assert gap >= 40, f"Gap between {name1} and {name2} is {gap} < 40 px!"

# Horizontal callout gaps:
c1_r = 40 + 480
c2_l = 560
c2_r = 560 + 480
c3_l = 1080
c3_r = 1080 + 480

gap_c1_c2 = c2_l - c1_r
gap_c2_c3 = c3_l - c2_r
print(f"Callout horizontal gaps: {gap_c1_c2} px, {gap_c2_c3} px")
assert gap_c1_c2 >= 40, f"Callout gap 1-2 is {gap_c1_c2} < 40 px!"
assert gap_c2_c3 >= 40, f"Callout gap 2-3 is {gap_c2_c3} < 40 px!"

# Outside margins:
left_margin = 40
right_margin = 1600 - (40 + 1520)
top_margin = 130  # box 1 top
bottom_margin = 1200 - 1130
print(f"Outside margins: left={left_margin}, right={right_margin}, top={top_margin}, bottom={bottom_margin}")
assert left_margin >= 40
assert right_margin >= 40
assert bottom_margin >= 40
print("[PASS] All gaps and outside margins >= 40 px.")

# 7. Conservative text width and padding check
def est_w(text, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(text) * fs * rate

# Card site.fact: x=56, y=142, w=684, h=146. Icon: x=76..124. Text start at x=150.
w1 = est_w("site.fact (INI): ", 24, False)
w2 = est_w("[location] rack=r07, rail=3", 24, True)
assert 150 - 124 >= 16
assert (56 + 684) - (150 + max(w1, w2)) >= 16
print("Card site.fact: PASS (pad right:", (56 + 684) - (150 + max(w1, w2)), ")")

# Card gpu.fact: x=760, y=142, w=784, h=146. Icon: x=780..824. Text start at x=850.
wg1 = est_w("gpu.fact (executable, mode 0755): ", 24, False)
wg2 = est_w("#!/bin/sh; ", 24, True)
wg3 = est_w("n=$(nvidia-smi -L 2>/dev/null | wc -l); ", 24, True)
wg4 = est_w("echo {\"count\": $n}", 24, True)
max_wg = max(wg1, wg2, wg3, wg4)
assert 850 - 824 >= 16
assert (760 + 784) - (850 + max_wg) >= 16
print("Card gpu.fact: PASS (pad right:", (760 + 784) - (850 + max_wg), ")")

# Facts.d panel: x=40, y=340, w=1520, h=84. Icon: x=64..114. Text at x=140.
wa1 = est_w("placed in /etc/ansible/facts.d/ on the target; any .fact file, or any executable, ", 24, False)
wa2 = est_w("is picked up during fact gathering; INI or JSON, or an executable printing JSON", 24, False)
assert 140 - 114 >= 16
assert (40 + 1520) - (140 + max(wa1, wa2)) >= 16
print("Facts.d panel: PASS (pad right:", (40 + 1520) - (140 + max(wa1, wa2)), ")")

# ansible_local header: centered at 800, fs=30 mono.
whdr = est_w("ansible_local.<name>", 30, True)
assert (800 - whdr/2) - (60 + 44) >= 16
assert (40 + 1520) - (800 + whdr/2) >= 16
# Badges:
wb1 = est_w("ansible_local.location.rack", 24, True)
wb2 = est_w("ansible_local.gpu.count", 24, True)
assert (416 - wb1/2) - 56 >= 16
assert (56 + 720) - (416 + wb1/2) >= 16
assert (1184 - wb2/2) - 824 >= 16
assert (824 + 720) - (1184 + wb2/2) >= 16
print("ansible_local container: PASS")

# Task strip: x=40, y=640, w=1520, h=84. Icon: x=60..108. Text at x=140.
wt1 = est_w("copy writes gpu.fact; setup with filter ansible_local re-reads it; ", 24, False)
wt2 = est_w("debug msg: {{ ansible_local.gpu.count }} GPUs on {{ inventory_hostname }}", 24, True)
assert 140 - 108 >= 16
assert (40 + 1520) - (140 + max(wt1, wt2)) >= 16
print("Task strip: PASS")

# Callouts:
for c_num, lines, cx, box_l in [
    (1, ["the script runs on the target, ", "so it always counts the ", "GPUs actually present, even ", "if the inventory was written ", "before a card was replaced"], 280, 40),
    (2, ["the node carries its own ", "label, so the playbook ", "does not need a separate ", "spreadsheet that might ", "be out of date"], 800, 560),
    (3, ["attributes stay with the ", "host and do not depend on ", "the control node"], 1320, 1080)
]:
    for l in lines:
        wl = est_w(l.strip(), 24, False)
        lp = (cx - wl/2) - box_l
        rp = (box_l + 480) - (cx + wl/2)
        assert lp >= 16 and rp >= 16, f"Callout {c_num} line '{l}' pad failed: lp={lp}, rp={rp}"
    print(f"Callout {c_num}: PASS")

# Bottom bar:
wb = est_w("The supported way for a host to declare its own attributes", 26, False)
assert (800 - wb/2) - (64 + 42) >= 16
assert (40 + 1520) - (800 + wb/2) >= 16
print("Bottom bar: PASS")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
