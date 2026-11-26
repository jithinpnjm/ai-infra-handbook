import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_experiment.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children tags: 0=<{first_tag}>, 1=<{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"3. All {len(text_elements)} text elements have font-size >= 24: PASS!")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "The ten-minute experiment: the same job run three ways",
    "Three lanes for 8 jobs of burn(seed), each chaining 1,000,000 SHA-256 hashes.",
    "sequential",
    "one interpreter runs jobs 0 to 7 one after another",
    "4 threads: ThreadPoolExecutor(max_workers=4)",
    "four threads share one GIL and take turns, so 'about as long as sequential, or a little longer'",
    "4 processes: ProcessPoolExecutor(max_workers=4)",
    "four interpreters, each with its own GIL, 'clearly faster' on a machine with at least four free cores",
    "change burn to time.sleep(1) and rerun: now threads win because the GIL is released while a thread sleeps",
    "timed() prints label and seconds with perf_counter; your timings depend on your hardware, so record your own",
    "a thread that computes for a long time is paused every 5 ms (sys.getswitchinterval()), an asyncio task is never paused that way and runs until an await",
    "The GIL gives threads turns, processes get their own lock"
]

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
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check unexpected extra text
extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"

# 6. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("6. No forbidden words found: PASS!")

# 7. Check orange usage
svg_str = open("candidate_experiment.svg").read()
orange_matches = re.findall(r'#db8129', svg_str)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
# Stroke and fills on Lane 2
assert len(orange_matches) > 0, "Orange should be used on Lane 2"

# 8. Check arrows
markers = re.findall(r'marker-end', svg_str)
print(f"\n8. Markers count: {len(markers)} (expected 0 arrows in spec)")
assert len(markers) == 0, "No arrows should be present"

print("\n--- ALL CHECKS PASSED PERFECTLY! ---")
