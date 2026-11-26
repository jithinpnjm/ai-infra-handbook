import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_label_budget.svg")
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

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

print(f"3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Check expected labels
expected_single_labels = [
    "Enforce the label budget at review, scrape and run time",
    "A rule that lives only in a wiki does not hold",
    "Budget enforced earlier, then later",
    "Review time",
    "A linter reads the declared metric design and fails on forbidden or unbounded labels",
    "Scrape time",
    "sample_limit",
    "label_limit",
    "label_name_length_limit",
    "label_value_length_limit",
    "Default 0 means no limit. A scrape over a limit fails whole.",
    "Run time",
    "TSDB status endpoint: series by metric name",
    "scrape_series_added",
    "A sudden rise is the signature of a new unbounded label",
    "Lint at review, limit at scrape, alert on series churn."
]

step_numbers = {"1", "2", "3"}

found_texts = [t for t, fs in text_elements]

print("\n4. Checking single-occurrence expected labels:")
for lbl in expected_single_labels:
    cnt = found_texts.count(lbl)
    assert cnt == 1, f"Expected label '{lbl}' count {cnt} != 1"
    print(f"   [PASS] count=1: '{lbl}'")

print("\n   Checking step numbers:")
for num in step_numbers:
    cnt_num = found_texts.count(num)
    assert cnt_num == 1, f"Step number '{num}' count {cnt_num} != 1"
    print(f"   [PASS] count=1: '{num}'")

# Check extras
extras = [t for t in found_texts if t not in expected_single_labels and t not in step_numbers]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# Distinct elements count: 16 labels + 3 step numbers = 19 text elements
assert len(found_texts) == len(expected_single_labels) + len(step_numbers), f"Total count {len(found_texts)} != 19"

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
print(f"\n6. Total arrows with marker-end: {total_arrows} (expected 2)")
assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"

# 7. Check orange usage
svg_str = open("test_label_budget.svg").read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange usage, got {len(oranges)}"

print("\nALL AUTOMATED VERIFICATIONS PASSED!")
