#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_p4_0407.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] <title> and <desc> are the first children.")

# 2. Dimensions check
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb.startswith("0 0 1600"), f"viewBox must start with '0 0 1600', got {vb}"
h_val = int(vb.split()[-1])
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("[PASS] Canvas dimensions and viewBox valid.")

# 3. Extract text elements and check font-sizes
texts = []
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

print("\n--- All text elements and font-sizes ---")
for t, fs in font_sizes:
    print(f"[{fs}px] '{t}'")
    assert fs >= 24, f"Text '{t}' has font-size {fs} < 24 px!"

print("[PASS] All text elements >= 24 px.")

# 4. Check full texts
full_texts = []
for el in root.iter():
    if el.tag.endswith('text'):
        combined = " ".join("".join(el.itertext()).split())
        full_texts.append(combined)

print("\n--- Full text elements ---")
for ft in full_texts:
    print(f"'{ft}'")

# Title check
expected_title = "A node that labels itself: custom facts in /etc/ansible/facts.d"
assert full_texts[0] == expected_title, f"Expected title '{expected_title}', got '{full_texts[0]}'"

# Expected labels
source_labels = [
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

print("\n--- Checking source labels ---")
for sl in source_labels:
    cnt = full_texts.count(sl)
    print(f"Label '{sl}': count={cnt}")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

print("[PASS] Every source label appears exactly once.")

# 5. Check no banned styling words:
banned_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for bw in banned_words:
        assert bw not in words, f"Banned styling word '{bw}' found in text: '{ft}'"

print("[PASS] No banned words found in any text element.")
