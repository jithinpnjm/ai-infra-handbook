import xml.etree.ElementTree as ET
import re

tree = ET.parse('output.svg')
root = tree.getroot()

# Namespaces
ns = {'svg': 'http://www.w3.org/2000/svg'}

# Extract title and desc
title = root.find('svg:title', ns)
desc = root.find('svg:desc', ns)

print("Title:", title.text if title is not None else "MISSING")
print("Desc:", desc.text if desc is not None else "MISSING")

# Extract all text nodes
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    # gather full text including tspans
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    font_size = elem.attrib.get('font-size')
    text_elements.append((full_text, font_size, elem.attrib))

print(f"\nTotal <text> elements found: {len(text_elements)}")
for t, fs, a in text_elements:
    print(f"  [{fs}px] '{t}'")

# Check font sizes >= 24
for t, fs, a in text_elements:
    if fs is not None:
        size = float(fs)
        assert size >= 24, f"Text '{t}' has font-size {size} < 24!"

print("\nAll font sizes are >= 24px: PASS!")

# Expected labels from prompt
expected_labels = [
    'Reading a tcpdump trace',
    'duplex.example.com.48455',
    'mikado.example.com.www',
    'arp who-has mikado.example.com tell duplex.example.com',
    'arp reply mikado.example.com is-at 0:2:2d:b:ee:4e',
    'hosts finding each other\'s link address',
    'S',
    'S ... ack 3200063166',
    '. ack 1',
    'TCP three-way handshake (SYN, SYN-ACK, ACK)',
    'P 1:427(426)',
    'request',
    'P 1:773(772)',
    'response',
    '. ack',
    '9 packets received by filter',
    '0 packets dropped by kernel',
    'summary'
]

# Check each expected label
found_texts = [t for t, fs, a in text_elements]

allowed_step_numbers = {'1', '2', '3', '4'}

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
print("\nAll 18 labels appear EXACTLY ONCE: PASS!")

# Check for unexpected labels
extra_texts = []
for t in found_texts:
    if t not in expected_labels and t not in allowed_step_numbers:
        extra_texts.append(t)

print(f"\nExtra texts found: {extra_texts}")
assert len(extra_texts) == 0, f"Found extra texts: {extra_texts}"
print("No unexpected or invented text: PASS!")

# Check arrows
# Look for marker-end, marker-start, <marker>, polygon/polyline arrowheads
markers = root.findall('.//{http://www.w3.org/2000/svg}marker')
print(f"\nMarker elements: {len(markers)}")
assert len(markers) == 0, "Found unexpected markers!"

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
