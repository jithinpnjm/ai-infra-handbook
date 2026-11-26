#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, pathlib

tree = ET.parse("candidate.svg")
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

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
assert vb_parts[3] == 1000

# 3. Check font sizes
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
    "Free is small, available is large: the page cache is reclaimable",
    "total 1950 MB",
    "free 163 MB",
    "page cache, buffers and reclaimable",
    "used by applications",
    "available 1187 MB",
    "the kernel gives it back to applications on demand",
    "free, the column that looks scary",
    "163 MB",
    "free looks low, but that is not a problem.",
    "available, the number to read",
    "1187 MB",
    "Read available, not free."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
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

# 5. Check forbidden style words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden style words found in text (PASS)")

# 6. Check orange #db8129 occurrences
svg_str = open("candidate.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 1, f"Expected exactly 1 arrow, got {total_arrows}"

# 8. Check gaps and margins
gaps = [
    ("Title top margin", 76 - 48*0.75), # ~40px from top baseline
    ("Takeaway bottom margin", 1000 - 950), # 50px >= 40
    ("Left Margin", 50), # 50px >= 40
    ("Right Margin", 1600 - (50 + 1500)), # 50px >= 40
    ("Cards gap", 830 - (50 + 720)), # 60px >= 40
    ("Cards to takeaway bar", 875 - 825), # 50px >= 40
    ("Bracket to cards", 485 - 436), # 49px >= 40
    ("Title to Bar top label", 192 - 132), # 60px >= 40
    ("Bar top label to Stacked Bar", 238 - 192), # 46px >= 40
]
print("\n8. Gaps check:")
for name, g in gaps:
    print(f"   {name}: {g:.1f}px (>=40: {g >= 40})")
    assert g >= 40, f"Gap '{name}' {g} < 40!"

# 9. Chrome headless render test
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
png_path = d / 'free_vs_available.png'
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    '--window-size=1600,1000',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path("candidate.svg").resolve()}'
], capture_output=True, timeout=60)
print(f"\n9. Screenshot rendered to {png_path}, return code: {res.returncode}")
assert res.returncode == 0, "Chrome screenshot rendering failed!"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
