import xml.etree.ElementTree as ET
import re

svg_file = "test_engine_upgrade.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. First children: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas
vb = root.attrib.get("viewBox").split()
W = float(vb[2])
H = float(vb[3])
width = float(root.attrib.get("width"))
height = float(root.attrib.get("height"))
print(f"2. Canvas: W={W}, H={H}, width={width}, height={height}")
assert W == 1600
assert 900 <= H <= 1200
assert width == 1600
assert height == H

# 3. Expected labels
expected_labels = [
    "What an engine upgrade silently changes",
    "things that move with the version",
    "compile cache invalidated by any change to the model, config, relevant VLLM_ environment variables, the torch build or the GPU model, so the first start after an upgrade is slow again",
    "sha256 prefix hashes may differ across Python or vLLM versions, so cache contents and hash-based routing are not portable",
    "defaults move: V1 has chunked prefill on by default and recompute as the preemption mode",
    "Ray Serve LLM installed with pip install ray[llm] pulls in vLLM, so the engine version is chosen by the Ray release and your pin, not only the image tag: record both",
    "1 pin by tag or digest",
    "2 pre-pull the image and warm the compile cache",
    "3 canary on a small slice and compare latency percentiles, preemptions and finish_reason shares",
    "4 keep the old version pods until the new ones pass",
    "maxUnavailable 0 and maxSurge 1 keeps all serving pods while the new one starts, but needs a spare GPU or the surge pod stays Pending and the roll stalls; with no spare GPU use maxUnavailable 1 and maxSurge 0 and accept lower capacity (author's reasoning)",
    "old image plus old flags in version control"
]

# Extract all text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    # Check tspans
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        combined = " ".join([ts.text.strip() for ts in tspans if ts.text])
        full_text = combined
    else:
        full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    
    fs = float(elem.attrib.get('font-size', '0'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# Check expected labels
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

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("5. Forbidden words check: PASS!")

# 6. Orange check
svg_str = open(svg_file).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
