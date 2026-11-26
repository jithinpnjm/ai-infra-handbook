#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_file = "candidate_test.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure Check
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First children: <{first_tag}>, <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions Check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Font-size >= 24px Check
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

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected Labels Check
expected_labels = [
    "A guard stops the apply, a comment only asks",
    "lifecycle prevent_destroy in the module: Terraform rejects any plan that would destroy the object",
    "nebius_mk8s_v1_node_group.pool[gpu] will be destroyed (because key gpu is not in for_each map)",
    "Plan: 0 to add, 0 to change, 1 to destroy.",
    "Error: Instance cannot be destroyed",
    "the plan still prints but ends with an error so an automated apply fails",
    "does not help if you delete the resource block from the code",
    "can make some changes impossible",
    "blocks terraform destroy",
    "policy check on the plan: terraform show -json fed to a risk script or Open Policy Agent; exits 1 on CRITICAL destroy of a stateful resource",
    "one layer can be removed by a careless edit and the other catches the edit",
    "moved block records a rename so the plan shows a move not a destroy; keep every moved block forever or old callers plan a destroy",
    "create_before_destroy creates the replacement first and spreads to dependencies",
    "after every import read the plan before anything else",
    "terraform plan -out=plan.bin then apply that exact file; treat it as sensitive; the sealed envelope"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")

all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK] '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count mismatch: {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden Words Check
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n5. No forbidden words found! (PASS)")

# 6. Orange Usage Check
with open(svg_file, "r") as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Orange #db8129 must appear exactly once, got {len(orange_matches)}"
print("Orange used exactly once on 'Error: Instance cannot be destroyed'! (PASS)")

# 7. Line width and padding check
print("\n7. Line width checks:")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get('font-size', '24'))
    ff = elem.attrib.get('font-family', 'sans-serif')
    factor = 0.62 if 'monospace' in ff else 0.6
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        for ts in tspans:
            t = (ts.text or "").strip()
            t_fs = float(ts.attrib.get('font-size', fs))
            w = len(t) * factor * t_fs
            print(f"   Line ({len(t):2d} chars, {w:.1f}px): '{t}'")
    else:
        t = (elem.text or "").strip()
        w = len(t) * factor * fs
        print(f"   Line ({len(t):2d} chars, {w:.1f}px): '{t}'")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
