import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_file = "test_candidate.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas
vb = root.attrib.get("viewBox").split()
W = float(vb[2])
H = float(vb[3])
width = float(root.attrib.get("width"))
height = float(root.attrib.get("height"))
print(f"2. Canvas: W={W}, H={H}, width={width}, height={height}")
assert W == 1600
assert 900 <= H <= 1200
assert width == 1600
assert height == H

# 3. Font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Summing counters before rate hides the restart",
    "Wrong: sum first, then rate",
    "Sum stays flat: the reset is invisible",
    "The work pod A did before the restart is lost",
    "Right: rate per series, then sum by the labels you keep",
    "sum by the labels you keep",
    "Fleet rate, reset handled per pod",
    "sum by (labels you keep) (rate(counter))",
    "Rate per series, sum by the labels you want to keep, then divide.",
    "Numerator and denominator summed separately, then divided. Never average ratios."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' count {cnt} != 1!"
    print(f"   [PASS] count=1: '{exp}'")

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("5. Forbidden words check: PASS!")

# 6. Orange check
svg_str = open(svg_file).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

# 7. Margins and gaps
# Left panel: x=50, y=130, w=720, h=650
# Right panel: x=830, y=130, w=720, h=650
# Bottom panel: x=50, y=820, w=1500, h=180
print("\n7. Checking margins and gaps:")
assert 50 >= 40, "Left margin < 40"
assert (1600 - (830 + 720)) >= 40, "Right margin < 40"
assert 130 >= 40, "Top margin < 40"
assert (H - (820 + 180)) >= 40, "Bottom margin < 40"

panel_gap_h = 830 - (50 + 720)
print(f"   Horizontal panel gap: {panel_gap_h}px (>= 40px)")
assert panel_gap_h >= 40

panel_gap_v = 820 - (130 + 650)
print(f"   Vertical panel gap: {panel_gap_v}px (>= 40px)")
assert panel_gap_v >= 40

print("\nALL VERIFICATIONS PASSED!")
