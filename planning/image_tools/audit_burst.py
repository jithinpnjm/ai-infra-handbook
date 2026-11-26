import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_path = "test_candidate_burst.svg"
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
    "The 16-request burst: same traffic, two memory budgets",
    "Llama-2-7B FP16 on a 24 GB GPU: weights 14 GB leave 10 GB; 0.5 MB per token = 20,480 tokens of cache; 16 requests of 3,000 prompt plus 1,000 output tokens, each growing to 4,000",
    "10 GB free",
    "capacity 20,480 tokens; peak KV usage 1.0; 2 preemptions; 11 requests waiting at the worst moment; 6,759 recomputed tokens; 3,000 steps",
    "34 GB free (the L40S case from the book)",
    "no preemptions; 1,000 steps",
    "by prompt size six are admitted, the rest wait; as admitted requests grow the cache fills; the newest is preempted and recomputed",
    "KV exhaustion with queueing. Now: lower batch size limits or send the job to a bigger pool. Later: size the endpoint for the longest realistic request or add replicas",
    "three times as many steps on the small GPU because admission is limited"
]

found_texts = [t for t, fs in text_elements]

print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:45]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("\n6. Forbidden words check: PASS!")

# 6. Check orange count
svg_str = pathlib.Path(svg_path).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert len(orange_matches) == 1, f"Expected exactly 1 orange highlight, got {len(orange_matches)}"

# 7. Check arrows count
arrows = [el for el in root.iter() if 'marker-end' in el.attrib]
print(f"\n8. Arrow count: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"

# 8. External resources check
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"

print("\nALL BASIC VERIFICATIONS PASSED!")
