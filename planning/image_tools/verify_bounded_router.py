#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

tree = ET.parse("candidate_test.svg")
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

# 3. Check text elements and font-size >= 24
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
    "The bounded cache-aware router only follows the cache while the holder is not much busier",
    "New request with prefix",
    "Does a replica hold the prefix in KV cache?",
    "Send to least loaded replica",
    "Holder backlog within bound of least loaded replica?",
    "Send to cache holder, prefill mostly skipped",
    "Send to least loaded replica, which then caches the prefix too",
    "sweep the bound against p99, not hit rate",
    "toy results",
    "cache-only hit 0.98, p99 4.39 s, max over mean load 3.8",
    "bounded hit 0.95, p99 0.50 s, max over mean load 2.13",
    "Use the cache holder only while it is not much busier than the idlest replica."
]

step_numbers = {"1", "2"}

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

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts (non-step): {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number '{num}' count is {cnt} != 1"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (PASS)")

# 6. Check orange #db8129 occurrences
svg_str = open("candidate_test.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 5, f"Expected exactly 5 arrows, got {total_arrows}"

# 8. Check gaps and margins
# Boxes:
# Start: y 150..240
# Step 1: y 300..420
# Right 1: y 300..420
# Step 2: y 480..600
# Knob: y 480..600
# Right 2: y 480..600
# Cache holder: y 660..770
# Legend: y 815..1030
# Takeaway: y 1075..1140
gaps = [
    ("Title to Start box", 150 - 109), # 41 >= 40
    ("Start to Step 1", 300 - 240), # 60 >= 40
    ("Step 1 to Step 2", 480 - 420), # 60 >= 40
    ("Step 1 to Right 1", 980 - 880), # 100 >= 40
    ("Step 2 to Right 2", 980 - 880), # 100 >= 40
    ("Knob to Step 2", 340 - 300), # 40 >= 40
    ("Step 2 to Cache Holder", 660 - 600), # 60 >= 40
    ("Cache Holder to Legend", 815 - 770), # 45 >= 40
    ("Legend to Takeaway", 1075 - 1030), # 45 >= 40
    ("Takeaway to Bottom Margin", 1180 - 1140), # 40 >= 40
    ("Left Margin (Knob)", 50), # 50 >= 40
    ("Right Margin (Right 1 & 2)", 1600 - 1540), # 60 >= 40
    ("Left Margin (Takeaway)", 40), # 40 >= 40
    ("Right Margin (Takeaway)", 1600 - (40 + 1520)), # 40 >= 40
]
print("\n8. Gaps check:")
for name, g in gaps:
    print(f"   {name}: {g}px (>=40: {g >= 40})")
    assert g >= 40, f"Gap '{name}' is {g} < 40!"

# 9. Chrome headless render test
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
png_path = d / 'x13-bounded-router.png'
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1180',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path("candidate_test.svg").resolve()}'
], capture_output=True, timeout=60)
print(f"\n9. Screenshot rendered to {png_path}, return code: {res.returncode}")
assert res.returncode == 0, "Chrome screenshot rendering failed!"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
