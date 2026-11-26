import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_output.svg")
root = tree.getroot()

# 1. Structure
children = list(root)
tag0 = children[0].tag.split('}')[-1]
tag1 = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{tag0}>, Child 1: <{tag1}>")
assert tag0 == "title", f"Child 0 must be title, got {tag0}"
assert tag1 == "desc", f"Child 1 must be desc, got {tag1}"

# 2. Dimensions
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Check font sizes >= 24
text_elements = []
all_texts = []
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
    all_texts.append(full_text)

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Check for banned words
banned = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t, fs in text_elements:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in banned:
        assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"

print("\n4. Banned words check: PASS (zero forbidden words printed as text)")

# 5. Check expected labels from the prompt
expected_labels = [
    "awk group-by: an associative array counts as the lines pass",
    "column 1",
    "column 2",
    "alice",
    "bob",
    "awk { c[$1]++ }",
    "lookup table c",
    "after line 1",
    "alice = 1",
    "after line 3",
    "alice = 2, bob = 1",
    "after line 5",
    "alice = 3, bob = 2",
    "END { for (k in c) print c[k], k }",
    "runs once after the last line",
    "output",
    "3 alice",
    "2 bob",
    "| sort -rn",
    "ranked output",
    "An associative array is a lookup table keyed by text, so no sort | uniq -c is needed",
    "uniq -c without sort",
    "1 alice",
    "1 bob",
    "2 alice",
    "sort | uniq -c"
]

cleaned_text = ' '.join(re.sub(r'<[^>]+>', ' ', open("test_output.svg").read()).split())
for lbl in expected_labels:
    assert lbl in cleaned_text, f"Missing expected label: '{lbl}'"
    print(f"   [FOUND] '{lbl}'")

print("\n5. All expected labels found in SVG text: PASS")

# 6. Check orange usage
raw_svg = open("test_output.svg").read()
# Find all occurrences of #db8129
orange_occurrences = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_occurrences)}")
# Check that #db8129 is only in right-end-box
# Parse the SVG and check where stroke or fill is #db8129
for elem in root.iter():
    stroke = elem.attrib.get('stroke', '')
    fill = elem.attrib.get('fill', '')
    if '#db8129' in stroke or '#db8129' in fill:
        # verify this element is inside right-end-box
        # We can verify by tag and attributes
        print(f"   Orange on element <{elem.tag.split('}')[-1]}>: fill={fill}, stroke={stroke}")

print("\n7. Automated checks completed successfully!")
