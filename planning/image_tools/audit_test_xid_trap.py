import xml.etree.ElementTree as ET
import re

svg_path = "test_xid_trap.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

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
    "The Xid gauge stays high after the repair",
    "Timeline with a line plot of DCGM_FI_DEV_XID_ERROR for one GPU",
    "Xid 79 appears, gauge jumps to 79",
    "node repaired, but gauge stays at 79 until another Xid replaces it or the exporter restarts",
    "alert on equals 79 keeps firing after the repair",
    "DCGM_FI_DEV_XID_ERROR == 79",
    "value plus recency: check when the value last changed, not only what it is",
    "a bad exporter restart can also re-emit a stuck gauge, so confirm a real Xid with dmesg on one node",
    "verify each metric name against /metrics on your exporter version; throttle, double-bit ECC and NVLink CRC counters are not enabled by default in DCGM exporter 4.9.0, enable them"
]

step_numbers = {"1", "2", "3"}

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"

for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number '{num}' count is {cnt} != 1!"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path, 'r', encoding='utf-8') as f:
    svg_str = f.read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows
arrows = [e for e in root.iter() if 'marker-end' in e.attrib]
print(f"\n8. Total arrows: {len(arrows)}")
assert len(arrows) == 1, f"Expected 1 arrow, got {len(arrows)}"
print("   [PASS] Exactly 1 arrow connects Side note to the stale case!")

print("\nALL BASIC AUDIT CHECKS PASSED!")
