import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_outward.svg")
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
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
for t, fs in text_elements:
    print(f"   [{fs:2.0f}px] '{t}'")

# 4. Check expected labels
expected_labels = [
    "Debug from the object outward, cheapest question first",
    "Cheap: the cluster API",
    "STATUS column of the pod",
    "kubectl get pod",
    "Events table at the bottom",
    "kubectl describe pod",
    "Namespace events, sorted by time",
    "kubectl get events",
    "Logs of the running container and the earlier one",
    "kubectl logs",
    "kubectl logs --previous",
    "Exec into the container, only if the pod looks fine",
    "kubectl exec",
    "Node: Conditions, Taints and Lease",
    "kubectl describe node",
    "Kubelet journal",
    "journalctl -xeu kubelet",
    "Container runtime",
    "crictl",
    "Network plugin, then DNS",
    "Expensive: the node",
    "Each seam is a handoff between two teams, so ask who holds the object now."
]

step_numbers = {'1', '2', '3', '4', '5', '6', '7', '8', '9'}
found_texts = [t for t, fs in text_elements]

print("\n4. Label check:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (OK)")

# 6. Check orange usage
svg_str = open("candidate_outward.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows / markers
markers = [e for e in root.iter() if "marker-end" in e.attrib]
print(f"\n7. Markers count: {len(markers)}")
assert len(markers) == 0, f"Expected 0 markers, found {len(markers)}"

# 8. Check gaps and paddings
# Check box rects
rects = root.findall(".//{http://www.w3.org/2000/svg}rect")
step_rects = []
for r in rects:
    w = float(r.attrib.get('width', 0))
    h = float(r.attrib.get('height', 0))
    x = float(r.attrib.get('x', 0))
    y = float(r.attrib.get('y', 0))
    if w == 1390:
        step_rects.append((x, y, w, h))

print(f"\n8. Step boxes count: {len(step_rects)}")
assert len(step_rects) == 9, f"Expected 9 step boxes, found {len(step_rects)}"

for i in range(len(step_rects) - 1):
    b1 = step_rects[i]
    b2 = step_rects[i+1]
    g = b2[1] - (b1[1] + b1[3])
    print(f"   Gap between Step {i+1} and Step {i+2}: {g}px (>= 40: {g >= 40})")
    assert g >= 40, f"Gap between Step {i+1} and Step {i+2} is {g} < 40!"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
