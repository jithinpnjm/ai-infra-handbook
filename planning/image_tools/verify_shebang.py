import xml.etree.ElementTree as ET
import re
import subprocess
import os

svg_path = "test_shebang.svg"

tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title'
assert second_tag == 'desc'

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Extract text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Total text elements: {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "The same #!/bin/sh line runs different shells on different distributions",
    "Debian and Ubuntu",
    "Script starts with #!/bin/sh",
    "/bin/sh is dash",
    "Small POSIX shell: no [[ ]], arrays, ${var//x/y} or process substitution",
    "bashisms fail",
    "RHEL family",
    "Script starts with #!/bin/sh",
    "/bin/sh is bash in POSIX mode",
    "bash extensions still work",
    "Rule: if you use any bash feature, write #!/usr/bin/env bash or #!/bin/bash.",
    "If you write #!/bin/sh, keep to POSIX and test with dash.",
    "Same shebang, different shell, so the script fails on one family only."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking all expected labels exist:")
for exp in set(expected_labels):
    cnt = found_texts.count(exp)
    print(f"  [{'PASS' if cnt >= 1 else 'FAIL'}] cnt={cnt}: '{exp}'")
    assert cnt >= 1, f"Missing expected label: '{exp}'"

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra / un-expected labels: {extras}")
assert len(extras) == 0, f"Found extra text: {extras}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Banned style word '{b}' found in text: '{t}'"
print("\n5. Banned style words check: PASS")

# 6. Arrows with marker
markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n6. Elements with markers: {len(markers)}")
assert len(markers) == 2, f"Expected exactly 2 arrows/markers, got {len(markers)}"

# 7. Orange #db8129 occurrences
raw_svg = open(svg_path).read()
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 3, f"Orange count {len(oranges)} not in [1, 3]"

# 8. Render check with Chrome
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if os.path.exists(chrome_path):
    H = int(vb[3])
    out_png = "/tmp/svgcheck/test_shebang.png"
    os.makedirs("/tmp/svgcheck", exist_ok=True)
    abs_svg = os.path.abspath(svg_path)
    subprocess.run([
        chrome_path, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        f'--window-size=1600,{H}', f'--screenshot={out_png}', f'file://{abs_svg}'
    ], check=True)
    print(f"8. Chrome rendered screenshot to {out_png}")

print("\nALL VERIFICATIONS PASSED!")
