#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

svg_file = "iptables_random_probabilities.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Check title and desc as first children
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Check dimensions and viewBox
width = root.attrib.get('width')
viewBox = root.attrib.get('viewBox')
print(f"2. Dimensions: width={width}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
H = int(viewBox.split()[3])
assert 900 <= H <= 1200, f"Height {H} outside [900, 1200]"

# 3. Extract and verify text elements & font sizes
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    fs_val = float(fs.replace('px', ''))
    assert fs_val >= 24, f"Text '{full_text}' font-size {fs_val} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            tfs_val = float(tfs.replace('px', ''))
            assert tfs_val >= 24, f"tspan font-size {tfs_val} < 24 in '{full_text}'"
    text_elements.append((full_text, fs_val))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "How iptables picks a backend: the 1 over N minus i chain",
    "Worked example with four backends AAAA, BBBB, CCCC, DDDD in a KUBE-SVC-XXXX chain",
    "Rule 1",
    "statistic mode random probability 0.25 -> KUBE-SEP-AAAA",
    "(1/4)",
    "Rule 2",
    "probability 0.33333 -> KUBE-SEP-BBBB",
    "(1/3 of the remaining 3/4)",
    "Rule 3",
    "probability 0.50 -> KUBE-SEP-CCCC",
    "(1/2 of the remaining)",
    "Rule 4",
    "no condition -> KUBE-SEP-DDDD",
    "always matches because nothing is left",
    "each backend ends up with 25 percent of new connections",
    "0.25",
    "0.75 x 0.3333 = 0.25",
    "0.75 x 0.6667 x 0.5 = 0.25",
    "remainder 0.25",
    "random, not real round robin; applies to new connections only; established flows stay on their backend via conntrack",
    "rule i uses 1 / (N - i)"
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
print("   [PASS] Content fidelity: exactly expected labels, none missing, none extra, none duplicated!")

# 5. Check forbidden style words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in forbidden:
        assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"
print("   [PASS] No forbidden words found!")

# 6. Check orange count
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("   [PASS] Orange used only for single important transition/item!")

# 7. Check external resources: no <image>, <script>, external fonts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert '@import' not in svg_str, "No external fonts allowed"
print("   [PASS] No external assets or scripts!")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
