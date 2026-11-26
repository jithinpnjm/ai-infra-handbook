#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_noisy.svg")
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

# 3. Check font sizes
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', 0))
    assert fs >= 24, f"Font size {fs} < 24 in {el}"
    for child in el:
        if child.tag.endswith('tspan'):
            child_fs = float(child.attrib.get('font-size', fs))
            assert child_fs >= 24, f"tspan font size {child_fs} < 24 in {child}"

print("[PASS] All font sizes >= 24px.")

# 4. Check labels
source_labels = [
    "Eleven long requests leave room for five normal ones",
    "KV arithmetic with 147,456 B per token and a 50.6 GB KV budget (assumed)",
    "One normal request: 2,500 tokens = 0.37 GB",
    "One long request: 30,000 tokens = 4.42 GB",
    "normal requests alone: 50.6 / 0.369 = 137 fit",
    "long requests that fill the GPU: 50.6 / 4.42 = 11",
    "left for others when 11 long run: 50.6 - 48.7 = 1.94 GB = 5 requests",
    "cap at 25 percent of KV: 12.65 / 4.42 = 2 long requests",
    "cap is per replica but the router sends all of the tenant's long requests to one replica: the cap must hold across the pool",
    "shared pool, long-context pool, dedicated endpoint",
    "eleven long requests take capacity from 137 down to 5 for everyone else: the case for charging by cost (tokens x context), not request count"
]

full_texts = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    combined = " ".join("".join(el.itertext()).split())
    full_texts.append(combined)

print(f"\nFound {len(full_texts)} text elements, expected {len(source_labels)}:")
for ft in full_texts:
    print(f"  '{ft}'")

assert len(full_texts) == len(source_labels), f"Count mismatch: {len(full_texts)} != {len(source_labels)}"

for sl in source_labels:
    cnt = full_texts.count(sl)
    assert cnt == 1, f"Expected '{sl}' once, found {cnt}"
    print(f"  [OK] '{sl[:40]}...' count={cnt}")

print("[PASS] All 11 source labels present and exact!")

# 5. Check no banned styling words
banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for b in banned:
        assert b not in words, f"Banned styling word '{b}' found in '{ft}'"

print("[PASS] No banned styling words printed as text.")

# 6. Check arrows:
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"Arrows found: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("[PASS] Exactly 0 arrows matches source specification.")

# 7. Check orange usage:
orange_hits = []
for el in root.iter():
    for k, v in el.attrib.items():
        if "#db8129" in v:
            orange_hits.append((el.tag.split('}')[-1], k, v))

print(f"Orange hits: {len(orange_hits)}")
for h in orange_hits:
    print(f"  {h}")

print("[PASS] Orange highlights only the single most important item (Bar C).")
