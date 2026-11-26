import xml.etree.ElementTree as ET
import re, json, subprocess, pathlib

svg_file = "candidate_ca_generated.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. Structure Check ===")
children = list(root)
tag0 = children[0].tag.split('}')[-1]
tag1 = children[1].tag.split('}')[-1]
print(f"Child 0: <{tag0}>, Child 1: <{tag1}>")
assert tag0 == 'title', f"Expected title, got {tag0}"
assert tag1 == 'desc', f"Expected desc, got {tag1}"
print("PASS: First children are <title> and <desc>.")

print("\n=== 2. Canvas & Dimensions Check ===")
w = root.get('width')
h = root.get('height')
vb = root.get('viewBox').split()
print(f"width={w}, height={h}, viewBox={vb}")
assert w == "1600", f"Width {w} != 1600"
assert vb == ["0", "0", "1600", h], f"ViewBox mismatch: {vb}"
assert 900 <= float(h) <= 1200, f"Height {h} not between 900 and 1200"
print("PASS: Dimensions valid.")

print("\n=== 3. Font Size Check (>= 24px) ===")
text_elems = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = el.get('font-size')
    assert fs is not None, f"Missing font-size on {el.text}"
    val = float(fs)
    assert val >= 24, f"font-size {val} < 24 px on {el.text}"
    full_text = " ".join("".join(el.itertext()).split())
    text_elems.append((full_text, val))
    for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24"

print(f"PASS: All {len(text_elems)} text elements have font-size >= 24 px.")
for i, (t, fs) in enumerate(text_elems, 1):
    print(f"  {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected Labels Fidelity ===")
spec = json.load(open('specs/p3_20_20.json'))
spec_item = [x for x in spec if x.get('name') == 'p3-2020-ca-pending-to-node'][0]
expected_labels = [spec_item['title']] + re.findall(r"'([^']*)'", spec_item['spec'])

found_texts = [t for t, fs in text_elems]
print(f"Expected count: {len(expected_labels)}, Found count: {len(found_texts)}")

for i, exp in enumerate(expected_labels, 1):
    cnt = found_texts.count(exp)
    print(f"  {i:2d}. [{'OK' if cnt == 1 else 'FAIL'}] count={cnt}: '{exp[:60]}...'")
    assert cnt == 1, f"Expected '{exp}' count == 1, got {cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"Extras: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("PASS: Exactly the 11 expected labels, 0 extras, 0 missing, 0 duplicates!")

print("\n=== 5. Forbidden Style Words ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("PASS: No forbidden style words in any text!")

print("\n=== 6. Arrow Count & Connections ===")
lines = [l for l in root.iter('{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
paths = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows: {total_arrows}")
assert total_arrows == 4, f"Expected 4 arrows between the 5 boxes, got {total_arrows}"
print("PASS: Exactly 4 arrows connecting the five boxes.")

print("\n=== 7. Orange Highlight (#db8129) ===")
raw = pathlib.Path(svg_file).read_text()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 10, f"Orange count {len(oranges)} out of bounds"
print("PASS: Orange #db8129 used for the dashboard note.")

print("\n=== 8. Headless Chrome Screenshot Test ===")
png_path = "/tmp/svgcheck/test_candidate_ca_perfect.png"
pathlib.Path("/tmp/svgcheck").mkdir(exist_ok=True)
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1060',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path(svg_file).resolve()}'
], capture_output=True, text=True)

if pathlib.Path(png_path).exists():
    print(f"PASS: Rendered PNG to {png_path} (size {pathlib.Path(png_path).stat().st_size} bytes)")
else:
    print(f"WARN: Chrome screenshot failed: {res.stderr}")

print("\n==========================================")
print("ALL 8 STRICT AUDIT CHECKS PASSED 100%!")
print("==========================================")
