#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# 1. Structure check
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Dimensions: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Check font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Check labels
expected_labels = [
    "Route by the endpoint's region, never by nearest",
    "Control plane: metadata only, global",
    "European customer",
    "Routed by endpoint region",
    "Nearest region: breaks the promise without an error",
    "US region",
    "EU region (promised region)",
    "Gateway",
    "Replica group",
    "Log store",
    "Prompts, completions and logs stay in region",
    "Metering",
    "Metering events leave only after content is stripped",
    "Cross-region failover is off by default for residency-bound tenants."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")

for exp in expected_labels:
    count = found_texts.count(exp)
    print(f"   - '{exp}': count = {count}")
    assert count == 1, f"Expected '{exp}' exactly once, found {count}"

assert len(found_texts) == len(expected_labels), f"Expected {len(expected_labels)} texts, got {len(found_texts)}"

# 5. Check orange usage
svg_str = open("test_candidate.svg").read()
orange_matches = re.findall(r'#db8129', svg_str)
print(f"\n5. Orange color (#db8129) occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Orange #db8129 must be used only once, got {len(orange_matches)}"

# 6. Check style instruction words not present as text
bad_words = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for t, fs in text_elements:
    for bw in bad_words:
        assert bw not in t.lower(), f"Style instruction word '{bw}' found in text '{t}'"

print("\nALL VERIFICATIONS PASSED!")
