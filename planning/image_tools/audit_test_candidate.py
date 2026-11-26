import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("   [PASS] <title> and <desc> are the first children.")

# 2. Dimensions and viewBox
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600", f"Width must be 1600, got {width}"
assert viewBox == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got '{viewBox}'"
assert height == "1200", f"height must be 1200, got '{height}'"
print("   [PASS] Dimensions and viewBox valid.")

# 3. Check font-size >= 24 on all text and tspans
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

# 4. Expected labels
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

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("   [PASS] Exact label match 100%!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"
print("   [PASS] No forbidden words found.")

# 6. Check arrows
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n6. Total arrows: {total_arrows} (expected 0)")
assert total_arrows == 0, f"Expected 0 arrows, found {total_arrows}"
print("   [PASS] Arrow count matches source (0 arrows).")

# 7. Check orange
raw_svg = open("test_candidate.svg").read()
orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n7. Orange #db8129 count: {len(orange_matches)}")
