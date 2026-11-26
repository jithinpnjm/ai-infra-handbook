import xml.etree.ElementTree as ET
import re

svg_path = "test_lost_update_out.svg"
tree = ET.parse(svg_path)
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
assert viewBox.startswith("0 0 1600"), f"viewBox must start with 0 0 1600, got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"
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
    "How counter += 1 loses an update, and what the lock changes",
    "Two thread lanes and a shared variable counter",
    "Without lock",
    "the steps of counter += 1 are 'load, add, store'",
    "Thread A",
    "counter",
    "Thread B",
    "Thread A loads counter = 5",
    "thread B loads counter = 5",
    "A adds and stores 6",
    "B adds and stores 6",
    "final counter is 6 where two increments should give 7",
    "one update lost",
    "With lock",
    "'with lock:' makes load, add and store one protected unit",
    "A holds the lock, B waits",
    "A stores 6",
    "B then loads 6 and stores 7",
    "lock = threading.Lock(); def incr(n): global counter; for _ in range(n): with lock: counter += 1",
    "data race: loses updates or breaks an invariant",
    "deadlock: two threads each hold a lock the other needs",
    "livelock: keep reacting without progress",
    "starvation: a thread never gets its turn",
    "priority inversion: a low-priority task holds a lock a high-priority task needs",
    "keep critical sections tiny and free of I/O",
    "never call unknown callbacks while holding a lock",
    "prefer queues and immutable messages",
    "test with stress loops",
    "Without the lock, the steps interleave"
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

print("\n5. Forbidden words check: PASS!")

# 6. Check orange count
svg_str = open(svg_path).read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("   [PASS] Orange used selectively!")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 6, f"Expected exactly 6 arrows, got {total_arrows}"
print("   [PASS] Arrows count verified!")

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str
print("\n8. All required colors present! (PASS)")

print("\nALL 8 STRICT CHECKS PASSED PERFECTLY!")
