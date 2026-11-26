import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

tree = ET.parse("test_output.svg")
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

# 3. Check font-size >= 24
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
    "A filter chain is a conveyor belt: each filter changes the value once",
    "gpu01 gpus 8",
    "gpu02 gpus 8",
    "login01 gpus 0",
    "selectattr(gpus, ge, 8): keep nodes with 8 or more GPUs",
    "gpu01, gpu02",
    "map(attribute=name): pull out the name of each node",
    "gpu01, gpu02",
    "join(,): glue the names with commas",
    "gpu01,gpu02",
    "gpu01,gpu02",
    "If the first filter keeps nothing, later filters receive an empty list and the output is an empty string.",
    "Read a filter chain left to right, one change at a time."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking expected labels:")
for exp in set(expected_labels):
    expected_cnt = expected_labels.count(exp)
    cnt = found_texts.count(exp)
    ok = (cnt == expected_cnt)
    print(f"   [{'PASS' if ok else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp}'")
    assert ok, f"Expected '{exp}' count {cnt} != expected {expected_cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path("test_output.svg").read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrow marker usage
markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n7. Arrows with marker: {len(markers)}")
assert len(markers) > 0, "No arrows found!"

# 8. Render to Chrome
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
H = int(vb_parts[3])
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '--headless=new', '--disable-gpu', '--hide-scrollbars',
                f'--window-size=1600,{H}', f'--screenshot={d}/test_filter_chain.png',
                f'file://{pathlib.Path("test_output.svg").resolve()}'],
               capture_output=True, timeout=60)
print(f"\n8. Rendered PNG to {d}/test_filter_chain.png (PASS)")
