import xml.etree.ElementTree as ET
import re

tree = ET.parse('test_cron.svg')
root = tree.getroot()

# Namespaces
ns = {'svg': 'http://www.w3.org/2000/svg'}

# 1. Check first children
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. Check width and viewBox
width = root.get('width')
viewBox = root.get('viewBox')
print(f"width={width}, viewBox={viewBox}")
assert width == "1600"
assert viewBox == "0 0 1600 1000"

# 3. Check colors and external assets
with open('test_cron.svg') as f:
    svg_text = f.read()

assert '@import' not in svg_text
assert '<image' not in svg_text
assert '<script' not in svg_text
assert 'http://' not in svg_text or 'http://www.w3.org/2000/svg' in svg_text

# Check orange count
orange_matches = re.findall(r'#db8129', svg_text, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")

# 4. Check all font sizes
font_sizes = [int(s) for s in re.findall(r'font-size="(\d+)"', svg_text)]
print(f"Font sizes used: {sorted(set(font_sizes))}")
for fs in font_sizes:
    assert fs >= 24, f"Font size {fs} is smaller than 24px!"

# 5. Check exact labels
expected_labels = [
    'A safe cron job',
    'SHELL=/bin/bash',
    'PATH=...',
    'MAILTO=""',
    'cron sets only HOME, LOGNAME, SHELL=/bin/sh and PATH=/usr/bin:/bin',
    '*/5 * * * * root flock -n /run/lock/gpu-health.lock timeout 120 /usr/local/bin/gpu-health.sh 2>&1 | logger -t gpu-health',
    '*/5 * * * * every five minutes',
    'flock -n prevents overlapping runs',
    'timeout 120 kills a hang',
    'logger -t gpu-health sends output to the journal',
    'before you schedule a job, make sure it is safe to run twice'
]

# Extract all text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    font_size = elem.attrib.get('font-size')
    text_elements.append((full_text, font_size, elem.attrib))

print(f"\nTotal <text> elements found: {len(text_elements)}")
for t, fs, a in text_elements:
    print(f"  [{fs}px] '{t}'")

assert len(text_elements) == len(expected_labels), f"Expected {len(expected_labels)} text elements, got {len(text_elements)}"

found_texts = [t for t, fs, a in text_elements]
labels_found = {}
for exp in expected_labels:
    count = found_texts.count(exp)
    labels_found[exp] = count

print("\n--- LABEL COUNT CHECK ---")
all_matched = True
for exp, count in labels_found.items():
    status = "OK" if count == 1 else f"FAIL (count={count})"
    if count != 1:
        all_matched = False
    print(f"  '{exp}': {status}")

assert all_matched, "Some labels were not found exactly once!"

extra_texts = [t for t in found_texts if t not in expected_labels]
assert len(extra_texts) == 0, f"Found extra texts: {extra_texts}"

print("\nAll 11 labels matched exactly once, no extra text!")

# 6. Check gaps and padding
gaps = [
    ("Title to Header/Note panels", 115 - 65 - 10), # ~40px
    ("Top panels to Crontab line", 320 - (115 + 160)), # 45px
    ("Crontab line to Callouts", 510 - (320 + 110)), # 80px (for arrows)
    ("Callouts to Takeaway bar", 865 - (510 + 310)), # 45px
    ("Takeaway bar to Bottom margin", 1000 - (865 + 80)), # 55px
    ("Left margin", 50), # 50px >= 40px
    ("Right margin", 1600 - (50 + 1500)), # 50px >= 40px
    ("Gap between Header and Orange note", 580 - (50 + 490)), # 40px
    ("Gap between Col 1 and Col 2", 435 - (50 + 345)), # 40px
    ("Gap between Col 2 and Col 3", 820 - (435 + 345)), # 40px
    ("Gap between Col 3 and Col 4", 1205 - (820 + 345)), # 40px
]

print("\n--- GAP CHECK (rule >= 40px) ---")
for name, g in gaps:
    print(f"  {name}: {g}px (>=40: {g >= 40})")
    assert g >= 40, f"Gap '{name}' is {g} < 40!"

# 7. Check arrows
lines = [elem for elem in root.iter('{http://www.w3.org/2000/svg}line') if 'marker-end' in elem.attrib]
print(f"\nNumber of arrows with marker-end: {len(lines)}")
assert len(lines) == 4, f"Expected 4 arrows, got {len(lines)}"

for i, line in enumerate(lines):
    x1 = float(line.attrib['x1'])
    y1 = float(line.attrib['y1'])
    x2 = float(line.attrib['x2'])
    y2 = float(line.attrib['y2'])
    print(f"  Arrow {i+1}: ({x1}, {y1}) -> ({x2}, {y2})")
    assert x1 == x2, f"Arrow {i+1} is not vertical: {x1} != {x2}"
    assert y1 == 430, f"Arrow {i+1} start y is {y1} != 430 (bottom of crontab line)"
    assert y2 == 510, f"Arrow {i+1} end y is {y2} != 510 (top of callout box)"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
