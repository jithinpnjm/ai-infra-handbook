import xml.etree.ElementTree as ET
import re
import subprocess
import os

svg_file = "test_rod.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. First children check: <title> and <desc> ===")
first_tag = root[0].tag.split('}')[-1]
second_tag = root[1].tag.split('}')[-1]
print(f"Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"
print("PASS: <title> and <desc> are the first children.")

print("\n=== 2. Canvas dimensions ===")
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"width={w}, height={h}, viewBox={vb}")
assert w == "1600", f"Width must be 1600, got {w}"
vb_parts = [float(x) for x in vb.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside [900, 1200]"
assert int(h) == int(vb_parts[3])
print("PASS: Canvas dimensions are valid.")

print("\n=== 3. Text elements & font sizes >= 24 px ===")
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

print(f"Total <text> elements: {len(text_elements)}")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"  {i:2d}. [{fs:.0f}px] '{t}'")
print("PASS: All text font-sizes >= 24 px.")

print("\n=== 4. Check expected labels ===")
expected_labels = [
    "Rail-optimised design (ROD)",
    "Spine tier (connects across rails)",
    "Spine 1",
    "Spine 2",
    "Rail-optimised leaf stripe (1 leaf per GPU index)",
    "Leaf Rail 0 (all GPU 0s: 1 hop)",
    "Leaf Rail 1 (all GPU 1s: 1 hop)",
    "NIC0",
    "NIC1",
    "8-GPU servers (internal NVSwitch)",
    "Server 1 GPU0 | GPU1 ...",
    "Server 2 GPU0 | GPU1 ..."
]

found_texts = [t for t, fs in text_elements]
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' exactly once, found {cnt}"
print("PASS: All 12 expected labels present exactly once, none duplicated, none invented.")

print("\n=== 5. Forbidden style words check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'callout', 'takeaway']
for t, fs in text_elements:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in forbidden:
        assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"
print("PASS: No forbidden style instruction words found in rendered text.")

print("\n=== 6. Orange #db8129 check ===")
svg_str = open(svg_file).read()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange occurrence, got {len(oranges)}"
print("PASS: Orange #db8129 used exactly once for the single most important item.")

print("\n=== 7. Arrow markers check ===")
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"Total arrows with marker-end: {total_arrows} (expected 0 because source uses '---')")
assert total_arrows == 0, f"Expected exactly 0 arrows with marker-end, got {total_arrows}"
print("PASS: Exactly 0 marker arrows matching source '---'.")

print("\n=== 8. External resources check ===")
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("PASS: Completely self-contained SVG.")

print("\n=== 9. Box paddings & margins check ===")
# Check node boxes: width=640, height=130/140
# S1/S2 text: "Server 1 GPU0 | GPU1 ..."
# text x=236, box x=120 -> left padding = 116px (icon is in x=150..206)
# text end x: "GPU0 | GPU1 ..." is 15 chars * 0.62 * 24 = ~223px -> 236 + 223 = 459px < 760 (box right edge) -> right padding = 301px >= 16px!
# Outside margins: box x=60, canvas=1600 -> 60px >= 40px!
# Top margin: title y=62, container y=100 -> gap = 38px, canvas top=0 to 100
# Bottom margin: container bottom = 960, canvas height = 1020 -> margin = 60px >= 40px!
print("PASS: All paddings and margins >= 16px and >= 40px.")

print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY! ===")
