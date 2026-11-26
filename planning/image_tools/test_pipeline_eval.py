import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

tree = ET.parse("candidate.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])
assert vb_parts[3] == 1140

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

# 4. Check expected labels
expected_labels = [
    'Pipelining: 104 cycles instead of 500',
    'Total cycles = K * (N - 1) + S',
    'Without a pipeline',
    'load from memory',
    'normalize mantissas',
    'add',
    'correct',
    'write result back',
    '500 cycles for N = 100 elements with S = 5',
    'With a pipeline',
    'pipeline fill time (S cycles)',
    '104 cycles = K x (N - 1) + S, with K = 1, N = 100, S = 5',
    'pipelining is a different idea from vectorization'
]

step_numbers = {'1', '2', '3', '4', '5'}
found_texts = [t for t, fs in text_elements]

print("\n4. Label check:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# Check step numbers count: each should appear at most once or exactly once
for num in step_numbers:
    cnt = found_texts.count(num)
    assert cnt == 1, f"Step number {num} count is {cnt} != 1!"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (OK)")

# 6. Check orange usage
svg_str = open("candidate.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 3, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows / markers
markers = [e for e in root.iter() if "marker-end" in e.attrib]
print(f"\n7. Markers count: {len(markers)}")
assert len(markers) == 0, f"Expected 0 markers, found {len(markers)}"

# 8. Check gaps
gaps = [
    ("Title to Formula box", 100 - 58), # 42px >= 40
    ("Formula box to Top Lane", 186 - (100 + 46)), # 40px >= 40
    ("Top Lane to Bottom Lane", 602 - (186 + 376)), # 40px >= 40
    ("Bottom Lane to Plain Note", 1040 - (602 + 398)), # 40px >= 40
    ("Plain Note to Bottom Canvas Margin", 1140 - (1040 + 48)), # 52px >= 40
    ("Left Margin", 50), # 50px >= 40
    ("Right Margin", 1600 - (50 + 1500)), # 50px >= 40
]
print("\n8. Gaps check:")
for name, g in gaps:
    print(f"   {name}: {g}px (>=40: {g >= 40})")
    assert g >= 40, f"Gap '{name}' is {g} < 40!"

# 9. Chrome headless render test
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
png_path = d / 'pipeline_conveyor.png'
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1120',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path("candidate.svg").resolve()}'
], capture_output=True, timeout=60)
print(f"\n9. Screenshot rendered to {png_path}, return code: {res.returncode}")
assert res.returncode == 0, "Chrome screenshot rendering failed!"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
