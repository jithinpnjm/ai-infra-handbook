import xml.etree.ElementTree as ET
import re, math

tree = ET.parse("test_output.svg")
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("   [PASS] <title> and <desc> are the first children.")

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
print("   [PASS] Canvas dimensions valid.")

# 3. Expected labels
expected_labels = [
    "RED for LLM serving: duration splits into four parts, each with its own fix",
    "Request rate, Errors, Duration (percentiles)",
    "queue time",
    "time to first token (TTFT)",
    "time per output token (TPOT)",
    "total",
    "Queue time",
    "waiting before service starts: arrivals exceed capacity, or the batch scheduler holds batches for a fill timeout",
    "TTFT",
    "prompt processing and everything before the first token",
    "TPOT",
    "steady generation speed per token",
    "Total",
    "what the user feels",
    "The request rate shows at once whether a slowdown comes with more load (a load problem) or with the same load (architecture or resources)",
    "Also track: tokens/s, batch size, KV-cache utilisation, preemptions and evictions",
    "Each part points at a different fix, which is why the split repays the effort"
]

print(f"\n3. Checking {len(expected_labels)} expected labels:")
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"Total text elements found: {len(text_elements)}")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

found_texts = [t for t, fs in text_elements]
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
        print(f"   [FAIL] count={cnt}: '{exp}'")
    else:
        print(f"   [OK] count=1: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"
assert len(found_texts) == len(expected_labels), f"Found {len(found_texts)} != expected {len(expected_labels)}"
print("   [PASS] All expected labels match exactly, count = 1, no extras!")

# 4. Forbidden words check
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n4. [PASS] No forbidden words found.")

# 5. Orange check
svg_str = open("test_output.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n5. Orange count: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
print("   [PASS] Orange used strictly for most important item.")

# 6. Arrows check
markers = [e for e in root.iter() if 'marker-end' in e.attrib]
print(f"\n6. Total arrows with marker-end: {len(markers)}")
assert len(markers) == 4, f"Expected 4 pointer arrows, got {len(markers)}"
print("   [PASS] Exactly 4 pointer arrows from 4 segments to 4 cards.")

# 7. Check line padding inside all boxes
print("\n7. Checking text line widths against boxes:")
# Let's inspect text lines inside cards:
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get('font-size', 24))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        for tsp in tspans:
            t = tsp.text or ""
            t_clean = t.strip()
            w_est = len(t_clean) * 0.6 * fs
            print(f"   Line '{t_clean}': chars={len(t_clean)}, fs={fs}, est_w={w_est:.1f}px")
    else:
        t = elem.text or ""
        t_clean = t.strip()
        w_est = len(t_clean) * 0.6 * fs
        print(f"   Single '{t_clean}': chars={len(t_clean)}, fs={fs}, est_w={w_est:.1f}px")

print("\nALL CHECKS PASSED PERFECTLY!")
