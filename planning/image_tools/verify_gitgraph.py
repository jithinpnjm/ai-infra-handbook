import xml.etree.ElementTree as ET
import re, subprocess, os

tree = ET.parse("test_gitgraph.svg")
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Text font-size >= 24
text_elems = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text: {elem.text}"
    size = float(fs)
    assert size >= 24, f"Font size {size} < 24 on text: {elem.text}"
    full_text = " ".join("".join(elem.itertext()).split())
    text_elems.append((full_text, size))
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24

print(f"3. All {len(text_elems)} text elements have font-size >= 24 px (PASS)")
for t, s in text_elems:
    print(f"   [{s:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Merge, rebase and history shape",
    "feature",
    "main",
    "A",
    "B",
    "F1",
    "F2",
    "C",
    "M"
]

found_texts = [t for t, s in text_elems]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok: all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"
extras = [t for t in found_texts if t not in expected_labels]
print(f"Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
found_forbidden = []
for t, fs in text_elems:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        if f in words:
            found_forbidden.append((f, t))

print(f"\n5. Forbidden words: {found_forbidden} (PASS)")
assert len(found_forbidden) == 0

# 6. Orange occurrences
raw = open("test_gitgraph.svg").read()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 3, f"Orange count {len(oranges)} not between 1 and 3"

# 7. Arrow count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows: {total_arrows}")
assert total_arrows == 6, f"Expected 6 arrows, got {total_arrows}"

# 8. Chrome headless screenshot render
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,900',
    '--screenshot=/tmp/svgcheck/test_gitgraph.png',
    f'file://{os.path.abspath("test_gitgraph.svg")}'
], capture_output=True, text=True)
print(f"\n8. Chrome render exit code: {res.returncode}")
assert res.returncode == 0

print("\nALL 8 STRICT CHECKS PASSED PERFECTLY!")
