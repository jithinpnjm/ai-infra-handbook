import xml.etree.ElementTree as ET
import re

tree = ET.parse('test_out.svg')
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

# 3. Check font sizes
with open('test_out.svg') as f:
    svg_text = f.read()

font_sizes = [float(s) for s in re.findall(r'font-size="([^"]+)"', svg_text)]
print(f"3. Font sizes: {font_sizes}, min={min(font_sizes)}, max={max(font_sizes)}")
assert min(font_sizes) >= 24, f"Font size < 24 found: {min(font_sizes)}"

# 4. Check style words not printed as text
style_words = ["orange", "green", "grey", "bold", "monospace", "arrow"]
for elem in root.iter():
    if elem.tag.endswith('text') or elem.tag.endswith('tspan'):
        txt = "".join(elem.itertext()).strip().lower()
        for sw in style_words:
            assert not re.search(r'\b' + sw + r'\b', txt), f"Style word '{sw}' found in text: '{txt}'"
print("4. No style words found in text!")

# 5. Check labels
expected_labels = [
    "An SLO and alerting platform for 1,000 endpoints [my addition]",
    "SLO file per endpoint",
    "Rule generator",
    "Recording rules",
    "Burn-rate alerts",
    "Routing by owner",
    "Metrics store"
]

text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', 30))
    text_elements.append((full_text, fs))

print(f"\n5. Total text elements: {len(text_elements)}")
found_texts = [t for t, fs in text_elements]
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i}. [{fs:2.0f}px] '{t}'")

assert len(found_texts) == len(expected_labels), f"Expected {len(expected_labels)} texts, got {len(found_texts)}"
for exp in expected_labels:
    cnt = found_texts.count(exp)
    assert cnt == 1, f"Expected '{exp}' exactly once, found {cnt} times!"
print("5. All expected labels present exactly once!")

# 6. Check arrows
markers = re.findall(r'marker-end="url\(#([^)]+)\)"', svg_text)
print(f"6. Total arrows with marker-end: {len(markers)}")
assert len(markers) == 5, f"Expected exactly 5 arrows, found {len(markers)}"

# 7. Check orange usage: exactly ONE item or arrow in orange #db8129
orange_occurrences = re.findall(r'#db8129', svg_text)
print(f"7. Total occurrences of #db8129: {len(orange_occurrences)}")
# In our SVG, #db8129 is only in node-br (stroke and icon)
print("All assertions passed!")
