#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_path = "candidate_qos.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"1. First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", f"First child must be <title>, got <{tag1}>"
assert tag2 == "desc", f"Second child must be <desc>, got <{tag2}>"
print("   [PASS] <title> and <desc> are the first children.")

# 2. Canvas dimensions and viewBox
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"2. Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb.startswith("0 0 1600"), f"viewBox must start with '0 0 1600', got {vb}"
h_val = int(vb.split()[-1])
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("   [PASS] Canvas dimensions and viewBox valid.")

# 3. Check font sizes >= 24 px
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

print(f"\n3. Checking font sizes ({len(font_sizes)} text spans):")
for t, fs in font_sizes:
    if fs < 24:
        print(f"   [FAIL] Text '{t}' has font-size {fs} < 24 px!")
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"
print("   [PASS] All text elements >= 24 px.")

# 4. Check source labels
source_labels = [
    "How the three QoS classes are derived and what they change",
    "QoS is derived by the API server, never set by a field; check with kubectl get pod -o jsonpath={.status.qosClass}",
    "Guaranteed",
    "every container sets CPU and memory requests equal to limits",
    "oom_score_adj -997",
    "cgroup kubepods.slice/guaranteed",
    "evicted last; required for CPU Manager static policy exclusive cores and Topology Manager alignment",
    "Burstable",
    "some requests or limits set, but not Guaranteed rules",
    "oom_score_adj scaled between 2 and 999",
    "cgroup kubepods.slice/burstable",
    "BestEffort",
    "no requests or limits at all",
    "oom_score_adj 1000",
    "cgroup kubepods.slice/besteffort",
    "first to be killed or evicted under pressure",
    "GPU extended resources must be whole integers and requests equal limits (no overcommit); setting only limits defaults requests to the same value"
]

full_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    txt = " ".join("".join(el.itertext()).split())
    if txt.isdigit():
        continue
    full_texts.append(txt)

print(f"\n4. Checking {len(source_labels)} source labels:")
for sl in source_labels:
    cnt = full_texts.count(sl)
    if cnt != 1:
        print(f"   [FAIL] Label '{sl}': count={cnt}")
    else:
        print(f"   [OK] Label '{sl}'")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

assert len(full_texts) == len(source_labels), f"Expected {len(source_labels)} text labels, got {len(full_texts)}:\n{full_texts}"
print("   [PASS] Every source label appears exactly once, and no extra text exists.")

# 5. Check no banned styling words
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
print("\n5. Checking for banned styling words:")
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"
print("   [PASS] No styling words printed as text.")

# 6. Check arrows count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\n6. Arrow count: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("   [PASS] Exactly 0 arrows present.")

# 7. Check orange #db8129 count
with open(svg_path) as f:
    raw_svg = f.read()

orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Orange #db8129 must be used only once, got {len(orange_matches)}"
print("   [PASS] Exactly one orange #db8129 occurrence.")

print("\n=== ALL STRICT RULES PASSED PERFECTLY ===")
