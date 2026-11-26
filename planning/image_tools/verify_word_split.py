#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, subprocess, os

svg_path = "test_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First tag must be title, got {first_tag}"
assert second_tag == 'desc', f"Second tag must be desc, got {second_tag}"

# 2. Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
vb = [float(x) for x in viewBox.split()]
assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
assert 900 <= vb[3] <= 1200
assert int(height) == int(vb[3])

# 3. Extract text elements and check font size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size', 0))
    assert fs >= 24, f"Text font size {fs} < 24! Text: '{full_text}'"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24! in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"\n3. Total text elements: {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Unquoted variables split on spaces and expand to the wrong arguments",
    "Unquoted (DANGER)",
    "Quoted (correct)",
    "rm $file",
    "my",
    "report.txt",
    "two arguments",
    "rm \"$file\"",
    "my report.txt",
    "one argument",
    "rm -rf $dir/*",
    "rm -rf /*",
    "rm -rf \"${dir:?dir is unset or empty}\"/*",
    "aborts instead",
    "Always double-quote every expansion, such as \"$var\", \"$(cmd)\" and \"$@\"."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking all {len(expected_labels)} expected labels exist:")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"  [{'PASS' if cnt == 1 else 'FAIL'}] cnt={cnt}: '{exp}'")
    assert cnt == 1, f"Expected label count failed for '{exp}': got {cnt}"

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra labels: {extras}")
assert len(extras) == 0, f"Found extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for b in forbidden:
        assert b not in words, f"Banned style word '{b}' found in text: '{t}'"
print("\n5. Banned style words check: PASS")

# 6. Arrows with marker
markers = [e for e in root.iter() if 'marker-end' in e.attrib or 'marker-start' in e.attrib]
print(f"\n6. Elements with markers: {len(markers)}")
assert len(markers) == 4, f"Expected exactly 4 arrows/markers, got {len(markers)}"

# 7. Orange #db8129 occurrences
raw_svg = open(svg_path).read()
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 8, f"Orange count {len(oranges)}"

# 8. Render check with Chrome
chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
if os.path.exists(chrome_path):
    H = int(vb[3])
    out_png = "/tmp/svgcheck/test_word_split.png"
    os.makedirs("/tmp/svgcheck", exist_ok=True)
    abs_svg = os.path.abspath(svg_path)
    subprocess.run([
        chrome_path, '--headless=new', '--disable-gpu', '--hide-scrollbars',
        f'--window-size=1600,{H}', f'--screenshot={out_png}', f'file://{abs_svg}'
    ], check=True)
    print(f"\n8. Rendered screenshot saved to {out_png}")
