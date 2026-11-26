#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

svg_file = "candidate_retry.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. First children check: <title> and <desc> ===")
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] <title> and <desc> are the first children.")

print("\n=== 2. Dimensions check ===")
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"Width: {w}, Height: {h}, viewBox: {vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
print("[PASS] Canvas dimensions and viewBox valid.")

print("\n=== 3. Extract text elements and check font-sizes ===")
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on: {full_text}"
    size = float(fs)
    assert size >= 24, f"Font size {size} < 24 on: {full_text}"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"Total text elements found: {len(text_elements)}")
for i, (t, s) in enumerate(text_elements, 1):
    print(f" {i:2d}. [{s:.0f}px] '{t}'")

print("\n=== 4. Expected Labels Check ===")
expected_labels = [
    "Retry layers multiply",
    "SDK",
    "gateway",
    "mesh sidecar",
    "router",
    "(and sometimes more)",
    "retries on its own",
    "Arithmetic panel",
    "One client, k attempts, failure chance p: expected attempts = 1 + p + p squared ... p to the power k - 1; for k = 4: p 0.1 gives 1.11, p 0.5 gives 1.875, p 0.8 gives 2.95",
    "SRE chapter: three layers each making 3 retries (4 attempts) can create 64 attempts at the bottom (4 x 4 x 4)",
    "AWS builders article: 243 times for a five-deep call chain = 3 to the power 5, three attempts per layer",
    "With 4 attempts per layer, five layers give 1,024",
    "set the budget at the gateway in one layer and turn off every other retry loop; retry at the layer directly above the one rejecting, not at every layer; if a large share of backends is overloaded, do not retry at all"
]

found_texts = [t for t, fs in text_elements]

all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK] count=1: '{exp[:45]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("[PASS] Exactly the 13 expected labels, each appearing once, zero extras!")

print("\n=== 5. Forbidden Words Check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("[PASS] No forbidden style words in any text element.")

print("\n=== 6. Orange Usage Check ===")
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Orange #db8129 must appear exactly once, got {len(orange_matches)}"
print("[PASS] Orange #db8129 used exactly once for the key item.")

print("\n=== 7. Arrows Check ===")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows: {total_arrows}")
assert total_arrows == 4, f"Expected 4 arrows in the 5-layer stack, got {total_arrows}"
print("[PASS] Exactly 4 arrows connecting the layers top to bottom.")

print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY! ===")
