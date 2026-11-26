import xml.etree.ElementTree as ET
import re, subprocess, pathlib

tree = ET.parse("test_p3_0501.svg")
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"
print("   [PASS] <title> and <desc> are first children.")

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]
print("   [PASS] Canvas dimensions valid.")

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

# 4. Check expected labels
expected_labels = [
    "Layer order decides how much a code edit rebuilds",
    "Careless order",
    "edit one line of code",
    "rebuilt: every commit forces a full dependency reinstall (a 10-minute reinstall in the checkpoint example)",
    "RUN pip install",
    "COPY . .",
    "FROM base",
    "Cache-friendly order",
    "rebuilt in about 1 second",
    "COPY src/",
    "cache hit, digest matches",
    "RUN pip install",
    "COPY requirements.lock",
    "FROM base",
    "Same idea in the Node.js example: COPY package*.json, RUN npm install, then COPY . . so editing server.js rebuilds only the last layer",
    "rarely changing pieces first, so a change near the front is the only one that knocks the rest down.",
    "Layers match RUN, COPY and ADD; ENV, LABEL and CMD change only metadata.",
    "Copy the lockfile before the source."
]

found_texts = [t for t, fs in text_elements]

print("\n4. Checking expected labels:")
for lbl in expected_labels:
    cnt = found_texts.count(lbl)
    assert cnt >= 1, f"Expected label '{lbl}' not found!"
    print(f"   [FOUND] count={cnt}: '{lbl[:40]}...'")

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
print("   [PASS] No unexpected extra texts!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in forbidden:
        assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"

print("\n5. No forbidden style words found in text: PASS!")

# 6. Check arrow count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"\n6. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 1, f"Expected exactly 1 arrow, got {total_arrows}"
print("   [PASS] Exactly 1 arrow present.")

# 7. Check orange usage
svg_str = pathlib.Path("test_p3_0501.svg").read_text()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(oranges)}")

print("\nALL AUTOMATED VERIFICATIONS PASSED!")
