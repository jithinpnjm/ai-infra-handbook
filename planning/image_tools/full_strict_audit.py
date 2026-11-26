import xml.etree.ElementTree as ET
import re

svg_file = "candidate_alignment.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure
children = list(root)
t0 = children[0].tag.split('}')[-1]
t1 = children[1].tag.split('}')[-1]
print(f"1. Children: <{t0}>, <{t1}>")
assert t0 == 'title', f"Child 0 must be <title>, got <{t0}>"
assert t1 == 'desc', f"Child 1 must be <desc>, got <{t1}>"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"width must be 1600, got {width}"
assert height == "1200", f"height must be 1200, got {height}"
assert viewBox == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {viewBox}"

# 3. Text font-size >= 24px everywhere
text_elements = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', '0'))
    combined = " ".join("".join(el.itertext()).split())
    assert fs >= 24, f"Text '{combined}' font-size {fs} < 24!"
    for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
        tfs = float(ts.attrib.get('font-size', fs))
        assert tfs >= 24, f"tspan in '{combined}' font-size {tfs} < 24!"
    text_elements.append((combined, fs))

print(f"3. Total text elements: {len(text_elements)} (all font sizes >= 24 px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels fidelity
expected_labels = [
    "Is this partition aligned? Divide the start sector by 8",
    "Start sector 2048 (1 MiB)",
    "2048 / 8 = 256, a whole number, remainder 0",
    "the partition boundary line sits exactly on a page edge",
    "aligned",
    "cat /sys/block/sdf/sdf2/start prints 1953126",
    "1953126 / 8 = 244140.75, remainder 6",
    "the partition boundary line falls inside a page, six sectors in",
    "a single 4 KiB read straddles two physical pages",
    "NOT aligned",
    "Why 8: eight 512-byte sectors make one 4,096-byte page",
    "Check with a tool: parted /dev/sdb align-check optimal 1 prints 1 aligned",
    "Existing partitions are not realigned by the tools, so check them yourself"
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

# 5. Extras check
extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("   PASS: Zero extra text elements.")

# 6. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("   PASS: No forbidden words found.")

# 7. Check arrows
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows: {total_arrows} (expected 0)")
assert total_arrows == 0, f"Expected 0 arrows, found {total_arrows}"
print("   PASS: Arrow count matches source (0 arrows).")

# 8. Orange #db8129 check
raw_svg = open(svg_file).read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n8. Orange #db8129 count: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Orange #db8129 must appear exactly once, got {len(orange_matches)}"
print("   PASS: Orange used exactly once for NOT aligned verdict box outline.")

print("\nALL 8 STRICT AUDIT CHECKS PASSED PERFECTLY!")
