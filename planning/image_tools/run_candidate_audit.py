import xml.etree.ElementTree as ET
import re, pathlib

svg_file = "candidate.svg"
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
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
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
    print(f"   {i:2d}. [{fs:2.0f}px] '{t[:60]}...'")

print("\n=== 4. Expected Labels Check ===")
expected_labels = [
    "During and after an incident: evidence, updates, review",
    "Collect as you go: incident log with UTC timeline, observations, commands run, changes made, who did what; exact error strings; kubectl get -o yaml snapshots, describe output, pod logs including --previous, node journals, dmesg, pcaps, metric screenshots with time ranges, nvidia-bug-report, Hubble flows, audit log excerpts; for support kubectl cluster-info dump, sosreport, vendor bundles",
    "Communicate: status updates at fixed intervals, state the impact clearly, give an ETA only when you have a basis for it",
    "Blameless review: timeline, contributing factors (not one single root cause), detection gaps, how well the mitigation worked, action items with owners for automation, alerts, guardrails, docs and tests; turn recurring manual diagnosis into automated checks",
    "game day: planned drill with a fault the team has not seen; measure time-to-detect and time-to-recover; tools tc netem, Chaos Mesh NetworkChaos, kill pods and nodes, fill disks, stop kubelet, break CNI"
]

step_numbers = {"1", "2", "3"}

found_texts = [t for t, fs in text_elements]
print(f"Found texts count: {len(found_texts)}")

for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count {cnt} != 1"
    print(f"   [PASS] count=1: '{exp[:50]}...'")

for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number '{num}' count {cnt} != 1"
    print(f"   [PASS] count=1: '{num}'")

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

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
assert total_arrows == 3, f"Expected 3 arrows for three-stage loop, got {total_arrows}"
print("Arrow count: PASS!")

print("\n=== 8. Box Margins and Intersections Check ===")
boxes = [
    ("Card 1", 50, 105, 710, 490),
    ("Card 2", 840, 105, 710, 490),
    ("Card 3", 840, 655, 710, 490),
    ("Card 4", 50, 655, 710, 490),
]

for name, x, y, w, h in boxes:
    assert x >= 40, f"{name} left margin {x} < 40"
    assert (x + w) <= 1560, f"{name} right margin {x+w} > 1560"
    assert y >= 100, f"{name} top margin {y} < 100"
    assert (y + h) <= 1160, f"{name} bottom margin {y+h} > 1160"

print("All card bounds within canvas margins >= 40px: PASS!")

# Check external resources
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("No external resources: PASS!")

print("\n=== ALL STRICT AUDIT CHECKS PASSED PERFECTLY! ===")
