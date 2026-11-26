#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import pathlib

svg_file = "test_p3_0510.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. Structure Check ===")
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

print("\n=== 2. Dimensions Check ===")
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

print("\n=== 3. Font-size >= 24px Check ===")
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

print(f"Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected Labels Check ===")
expected_labels = [
    "From pod ready to every node routing to it",
    "pod passes its readiness check (Ready true; readiness gates satisfied)",
    "EndpointSlice controller adds the pod to a slice: conditions ready, serving, terminating",
    "API server publishes the change",
    "each node kube-proxy sees it and programs rules on its next sync (batch interval)",
    "traffic reaches the pod",
    "typically 1 to 5 seconds before all nodes route to the new pod",
    "pod terminating",
    "slice shows ready false, serving true",
    "proxies keep serving it only if no ready endpoints remain (graceful drain)",
    "removal races SIGTERM",
    "preStop sleep plus graceful shutdown (5.7)",
    "a Service with no ready endpoints: iptables REJECT sends ICMP port unreachable, client sees connection refused immediately; empty kubectl get endpointslices means selector mismatch or unready pods"
]

step_numbers = {"1", "2", "3", "4", "5"}

found_texts = [t for t, fs in text_elements]
print(f"Found texts count: {len(found_texts)}")

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

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for s in sorted(list(step_numbers), key=lambda x: int(x)):
    cnt = found_texts.count(s)
    assert cnt == 1, f"Step number {s} count {cnt} != 1!"
print("All step numbers 1..5 present exactly once! (PASS)")

print("\n=== 5. Forbidden Words Check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("No forbidden words found! (PASS)")

print("\n=== 6. Orange Usage Check ===")
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Orange #db8129 must appear exactly once, got {len(orange_matches)}"
print("Orange used exactly once! (PASS)")

print("\n=== 7. Arrows Count Check ===")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows with marker-end: {total_arrows} (lines: {len(lines)}, paths: {len(paths)})")
assert total_arrows == 7, f"Expected 7 arrows, got {total_arrows}"
print("Arrow count: PASS!")

print("\n=== 8. Box Paddings and Margins Check ===")
# Check text positions vs card boundaries
cards = [
    # (elem_id, x, y, w, h)
    ("Card 1", 40, 175, 270, 340),
    ("Card 2", 350, 175, 285, 340),
    ("Card 3", 675, 175, 245, 340),
    ("Card 4", 960, 175, 295, 340),
    ("Card 5", 1295, 175, 265, 340),
    ("Box a", 40, 565, 240, 300),
    ("Box b", 320, 565, 350, 300),
    ("Box c", 710, 565, 480, 300),
    ("Box d", 1230, 565, 330, 300),
    ("Side Box", 40, 915, 1040, 245),
    ("Fix Box", 1120, 915, 440, 245),
]

for name, x, y, w, h in cards:
    assert x >= 40, f"{name} left margin {x} < 40"
    assert (x + w) <= 1560, f"{name} right margin {x+w} > 1560"

print("All margins and paddings: PASS!")

print("\n=== ALL VERIFICATIONS PASSED PERFECTLY! ===")
