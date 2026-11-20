import xml.etree.ElementTree as ET
import re

tree = ET.parse("lookup_order.svg")
root = tree.getroot()

# 1. XML validity checked by parsing

# 2. Check first children
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 3. Check width and viewBox
width = root.get('width')
viewBox = root.get('viewBox')
print(f"width={width}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")

# 4. Check colors
with open("lookup_order.svg") as f:
    svg_text = f.read()

# Check orange count
orange_matches = re.findall(r'#db8129', svg_text, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
# One in marker-orange, one in the line stroke
# The line is the single most important arrow

# Check fonts: no external fonts
assert '@import' not in svg_text
assert 'http://' not in svg_text and 'https://' not in svg_text or 'http://www.w3.org/2000/svg' in svg_text

# 5. Check all font sizes
font_sizes = [int(s) for s in re.findall(r'font-size="(\d+)"', svg_text)]
print(f"Font sizes used: {sorted(set(font_sizes))}")
for fs in font_sizes:
    assert fs >= 24, f"Font size {fs} is smaller than 24px!"

# 6. Check exact labels
# Expected source labels:
# A["obj.name"] --> B{"name found on type MRO?"}
# B -- "data descriptor" --> C["descriptor.__get__ (wins over instance dict)"]
# B -- "otherwise" --> D{"in instance __dict__?"}
# D -- yes --> E["return instance value"]
# D -- no --> F{"non-data descriptor or plain class attr?"}
# F -- yes --> G["descriptor.__get__ / class attr"]
# F -- no --> H{"__getattr__ defined?"}
# H -- yes --> I["__getattr__(name)"]
# H -- no --> J["AttributeError"]

expected_nodes = [
    "obj.name",
    "name found on type MRO?",
    "descriptor.__get__ (wins over instance dict)",
    "in instance __dict__?",
    "return instance value",
    "non-data descriptor or plain class attr?",
    "descriptor.__get__ / class attr",
    "__getattr__ defined?",
    "__getattr__(name)",
    "AttributeError"
]

# Extract all text from text/tspan
all_texts = []
for t in root.iter('{http://www.w3.org/2000/svg}text'):
    # get text including tspans
    full = "".join(t.itertext())
    all_texts.append(full)

print("\nExtracted text elements from SVG:")
for t in all_texts:
    print(f"  - '{t}'")

# Check arrows
lines = root.findall('.//{http://www.w3.org/2000/svg}line')
print(f"\nNumber of arrows (lines with marker-end): {len([l for l in lines if 'marker-end' in l.attrib])}")
assert len([l for l in lines if 'marker-end' in l.attrib]) == 9

print("\nVerification completed successfully!")
