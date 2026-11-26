import re
import xml.etree.ElementTree as ET

tree = ET.parse("test_run_cache.svg")
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

# 3. Text elements font sizes >= 24
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
    "A prompt-cache or KV-cache tier [my addition]",
    "Request",
    "Prefix hash + tenant",
    "Cache-aware router",
    "GPU KV: hot",
    "Host RAM: warm",
    "NVMe: cold"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != expected {len(expected_labels)}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (PASS)")

# 6. Check colors
svg_str = open("test_run_cache.svg").read()
assert "#f5f8f5" in svg_str, "Background #f5f8f5 missing"
assert "#303a36" in svg_str, "Text #303a36 missing"
assert "#207448" in svg_str, "Main green #207448 missing"
assert "#e8f1ea" in svg_str, "Light green panels #e8f1ea missing"
assert "#db8129" in svg_str, "Orange #db8129 missing"

orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 5, f"Expected exactly 5 arrows, got {total_arrows}"

# 8. Check text padding / fit inside boxes
# Each box is 420 wide, 260 high
# Text is 30px bold sans-serif (~18px per char)
for t, fs in text_elements:
    if t == "A prompt-cache or KV-cache tier [my addition]":
        continue
    # Node titles are 30px
    assert fs >= 30, f"Node title '{t}' has font-size {fs} < 30!"
    chars = len(t)
    est_w = chars * 0.6 * fs
    print(f"Text '{t}': len={chars}, est_w={est_w:.1f}px (box=420px, pad={(420-est_w)/2:.1f}px)")
    assert 420 - est_w >= 32, f"Text '{t}' does not fit in 420px with 16px padding on each side!"

print("\nALL CHECKS PASSED PERFECTLY!")
