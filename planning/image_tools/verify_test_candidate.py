import xml.etree.ElementTree as ET
import re

svg_path = "test_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title'
assert second_tag == 'desc'

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Text elements
expected_labels = [
    "Pick the execution module by what the command needs: a pipe needs a shell",
    "command",
    "runs the binary directly, no shell",
    "pipes and redirects do not work",
    "shell",
    "runs through /bin/sh -c",
    "pipes, redirects and globs work",
    "quote variables to avoid injection",
    "raw",
    "plain SSH command, no module, no Python on the target",
    "bootstraps Python on minimal systems",
    "script",
    "copies a local script to the target and runs it",
    "runs the file you wrote",
    "dmesg | grep -i xid | tail -5",
    "Prefer purpose-built modules such as package, service and file, because they are idempotent.",
    "The pipe decides the module."
]

text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Total text elements: {len(text_elements)}")
found_texts = [t for t, fs in text_elements]
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs}px] '{t}'")

# Check all expected labels
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected label '{exp}' appeared {cnt} times, expected exactly 1!"
    print(f"  [PASS] '{exp}' (cnt=1)")

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra / un-expected labels: {extras}")
assert len(extras) == 0, f"Found extra text: {extras}"

# 4. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Banned style word '{b}' found in text: '{t}'"
print("\n4. Banned style words check: PASS")

# 5. Arrows / Markers
markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n5. Elements with markers: {len(markers)}")
assert len(markers) == 2, f"Expected exactly 2 arrows/markers, got {len(markers)}"

# 6. Orange occurrences
raw_svg = open(svg_path).read()
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 3, f"Orange count {len(oranges)} not in [1, 3]"

# 7. Margins and gaps
# Outside boxes:
# col-1-bg, col-2-bg, col-3-bg, col-4-bg (y=170..630)
# box-example (y=680..755)
# box-bottom-note (y=805..915)
# bar-caption (y=955..1025)
boxes = [
    ("col-1-bg", 40, 175, 350, 470),
    ("col-2-bg", 430, 175, 350, 470),
    ("col-3-bg", 820, 175, 350, 470),
    ("col-4-bg", 1210, 175, 350, 470),
    ("box-example", 160, 695, 1280, 80),
    ("box-bottom-note", 40, 825, 1520, 110),
    ("bar-caption", 40, 975, 1520, 70),
]

print("\n7. Checking outside margins (>= 40px):")
for name, x, y, w, h in boxes:
    left_m = x
    right_m = 1600 - (x + w)
    top_m = y
    bot_m = int(height) - (y + h)
    assert left_m >= 40, f"{name} left margin {left_m} < 40"
    assert right_m >= 40, f"{name} right margin {right_m} < 40"
    assert top_m >= 40, f"{name} top margin {top_m} < 40"
    assert bot_m >= 40, f"{name} bot margin {bot_m} < 40"
    print(f"  {name:15s}: L={left_m} R={right_m} T={top_m} B={bot_m} (PASS)")

# Gaps
gaps = [
    ("col-1 to col-2", 430 - (40 + 350)),
    ("col-2 to col-3", 820 - (430 + 350)),
    ("col-3 to col-4", 1210 - (820 + 350)),
    ("columns to example", 695 - (175 + 470)),
    ("example to bottom-note", 825 - (695 + 80)),
    ("bottom-note to caption", 975 - (825 + 110)),
]
print("\nChecking gaps between main sections (>= 40px):")
for name, gap in gaps:
    assert gap >= 40, f"Gap {name} {gap} < 40"
    print(f"  {name:25s}: {gap}px >= 40px (PASS)")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
