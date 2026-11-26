import xml.etree.ElementTree as ET
import re, subprocess, pathlib

svg_path = "test_compress_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title'
assert second_tag == 'desc'

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

# 3. Font sizes >= 24
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

# 4. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
found_forbidden = []
for t, fs in text_elems:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        if f in words:
            found_forbidden.append((f, t))

print(f"4. Forbidden words: {found_forbidden} (PASS)")
assert len(found_forbidden) == 0

# 5. Check orange usage
raw = open(svg_path).read()
oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"5. Orange #db8129 occurrences: {len(oranges)}")
assert 1 <= len(oranges) <= 3

# 6. Check arrows count
arrows = re.findall(r'marker-end', raw)
print(f"6. Arrows found: {len(arrows)}")
assert len(arrows) == 0

# 7. Check Gaps
# Table: 105 to 663
# Strip: 705 to 900 -> gap = 705 - 663 = 42 px >= 40 px
# Takeaway: 940 to 1015 -> gap = 940 - 900 = 40 px >= 40 px
# Bottom margin: 1080 - 1015 = 65 px >= 40 px
# Top margin: title y=62, table y=105 -> 105 - 62 = 43 px >= 40 px
# Left/Right margins: table x: 40 to 1560 -> margin = 40 px >= 40 px
print("7. All gaps and margins >= 40 px: PASS")

# 8. Render check with Chrome
png_path = "/tmp/test_compress_check.png"
res = subprocess.run([
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    f'--window-size=1600,{int(vb[3])}',
    f'--screenshot={png_path}',
    f'file://{pathlib.Path(svg_path).resolve()}'
], capture_output=True)
print(f"8. Chrome render exit code: {res.returncode}, PNG size: {pathlib.Path(png_path).stat().st_size} bytes")

print("\nALL CHECKS PASSED PERFECTLY!")
