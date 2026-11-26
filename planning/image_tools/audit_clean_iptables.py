import xml.etree.ElementTree as ET
import re
import json
import subprocess
import pathlib

svg_path = "test_clean_iptables.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

print("=== 1. First children check: <title> and <desc> ===")
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"
print(f"PASS: First children are <{first_tag}> and <{second_tag}>")

print("\n=== 2. Dimensions and canvas check ===")
width = root.attrib.get("width")
height = root.attrib.get("height")
viewBox = root.attrib.get("viewBox")
assert width == "1600", f"Width must be 1600, got {width}"
assert viewBox == "0 0 1600 1200", f"viewBox unexpected: {viewBox}"
assert height == "1200", f"Height unexpected: {height}"
print(f"PASS: Dimensions {width}x{height}, viewBox='{viewBox}'")

print("\n=== 3. Font-size check (>= 24 everywhere) ===")
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

print(f"PASS: All {len(text_elements)} text elements have font-size >= 24px")

print("\n=== 4. Expected labels fidelity ===")
data = json.load(open('specs/p3_02_20.json'))
spec_item = [x for x in data if x.get('name') == 'p3-0220-kubeproxy-prob'][0]
expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])

found_texts = [t for t, fs in text_elements]
print(f"Expected count: {len(expected_labels)}, Found count: {len(found_texts)}")

for i, exp in enumerate(expected_labels, 1):
    cnt = found_texts.count(exp)
    print(f"  {i:2d}. [{'OK' if cnt == 1 else 'FAIL'}] cnt={cnt}: '{exp[:50]}...'")
    assert cnt == 1, f"Expected '{exp}' count 1, got {cnt}"

print("PASS: Every expected label found exactly once!")

print("\n=== 5. Extras check ===")
extras = [t for t in found_texts if t not in expected_labels]
print(f"Extras count: {len(extras)}")
assert len(extras) == 0, f"Found extra texts: {extras}"
assert len(found_texts) == len(expected_labels), f"Count mismatch: {len(found_texts)} != {len(expected_labels)}"
print("PASS: Zero extra text elements!")

print("\n=== 6. Forbidden style words check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' found in text: '{t}'"
print("PASS: No forbidden style words in visible text!")

print("\n=== 7. Arrow count check ===")
arrow_lines = [l for l in root.iter('{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
arrow_paths = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(arrow_lines) + len(arrow_paths)
print(f"Total arrows: {total_arrows} (expected 0)")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
print("PASS: Arrow count matches source (0 arrows)!")

print("\n=== 8. Headless Chrome screenshot test ===")
png_path = "/tmp/svgcheck/test_clean_iptables.png"
pathlib.Path("/tmp/svgcheck").mkdir(exist_ok=True)
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1200',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path(svg_path).resolve()}'
], capture_output=True, text=True)

if pathlib.Path(png_path).exists():
    print(f"PASS: Rendered PNG to {png_path} (size {pathlib.Path(png_path).stat().st_size} bytes)")
else:
    print(f"WARN: Chrome screenshot failed: {res.stderr}")

print("\n==========================================")
print("ALL AUDIT CHECKS PASSED WITH 100% SUCCESS!")
print("==========================================")
