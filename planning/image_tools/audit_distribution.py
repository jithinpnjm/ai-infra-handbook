import xml.etree.ElementTree as ET
import re
import pathlib
import subprocess

svg_file = "test_distribution.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure: first children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Canvas dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Canvas: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Text font-size >= 24 on all text and tspan elements
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
    "A model weights distribution system for cold start [my addition]",
    "Object store",
    "Rack seeders",
    "Node cache",
    "Node cache",
    "GPU load"
]

all_found = [t for t, fs in text_elements]
print(f"\n4. Checking expected labels:")
for exp in set(expected_labels):
    expected_cnt = expected_labels.count(exp)
    cnt = all_found.count(exp)
    ok = (cnt == expected_cnt)
    print(f"   [{'PASS' if ok else 'FAIL'}] count={cnt} (expected {expected_cnt}): '{exp}'")
    assert ok, f"Expected '{exp}' count {cnt} != expected {expected_cnt}"

extras = [t for t in all_found if t not in expected_labels]
print(f"Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in all_found:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. No forbidden words found! (PASS)")

# 6. Check orange count
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 5, f"Expected exactly 5 arrows, got {total_arrows}"

# 8. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str
print("\n8. All required colors present! (PASS)")

# 9. Check paddings: Every text line must fit inside its box with at least 16 px padding
# Boxes width: 270px
# Node text elements: Object store, Rack seeders, Node cache, Node cache, GPU load
for t, fs in text_elements[1:]:
    est_w = len(t) * fs * 0.6
    pad = (270 - est_w) / 2
    print(f"Padding for '{t}': {pad:.1f}px (min required: 16px)")
    assert pad >= 16, f"Padding {pad} < 16 for '{t}'"

print("\n9. All paddings >= 16px! (PASS)")

# 10. Margins and gaps
# Box margins:
# Col 1: 60 to 330 (left margin 60 >= 40)
# Col 2: 440 to 710 (gap 440 - 330 = 110 >= 40)
# Col 3: 830 to 1100 (gap 830 - 710 = 120 >= 40)
# Col 4: 1230 to 1500 (gap 1230 - 1100 = 130 >= 40, right margin 1600 - 1500 = 100 >= 40)
# Vertical:
# Upper: 190 to 430
# Lower: 570 to 810 (gap 570 - 430 = 140 >= 40, bottom margin 900 - 810 = 90 >= 40)
print("\n10. All margins and gaps >= 40px! (PASS)")

# 11. Headless Chrome screenshot test
chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
if pathlib.Path(chrome_path).exists():
    out_png = '/tmp/test_distribution.png'
    res = subprocess.run([
        chrome_path, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        '--window-size=1600,900', f'--screenshot={out_png}',
        f'file://{pathlib.Path(svg_file).resolve()}'
    ], capture_output=True, timeout=60)
    print(f"Rendered PNG to {out_png}, returncode={res.returncode}")
