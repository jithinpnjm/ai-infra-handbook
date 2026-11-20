#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse('output_candidate.svg')
root = tree.getroot()
ns = {'svg': 'http://www.w3.org/2000/svg'}

# Check title and desc as first children
children = list(root)
print(f"Child 0: {children[0].tag}")
print(f"Child 1: {children[1].tag}")
assert children[0].tag.endswith('title'), "First child must be <title>"
assert children[1].tag.endswith('desc'), "Second child must be <desc>"
assert root.attrib.get('viewBox') == '0 0 1600 1200'
assert root.attrib.get('width') == '1600'
assert root.attrib.get('height') == '1200'

# Extract all text elements
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = elem.attrib.get('font-size')
    text_elements.append((full_text, fs, elem))

print(f"\nTotal <text> elements: {len(text_elements)}")
for t, fs, el in text_elements:
    print(f"  [{fs}px] '{t}'")

# Check font sizes >= 24
for t, fs, el in text_elements:
    if fs is not None:
        size = float(fs)
        assert size >= 24, f"Text '{t}' has font-size {size} < 24!"

print("\nAll font sizes >= 24px: PASS!")

# Expected source labels
expected_labels = [
    'site.yml imports the tiers in dependency order',
    'playbooks/site.yml',
    '- import_playbook: baseline.yml',
    '- import_playbook: database.yml',
    '- import_playbook: app.yml',
    '- import_playbook: web.yml',
    '- import_playbook: verify.yml',
    'baseline.yml',
    'baseline',
    'OS baseline on every host',
    'database.yml',
    'db',
    'PostgreSQL on the db group',
    'app.yml',
    'app',
    'application on the app group',
    'web.yml',
    'web',
    'nginx reverse proxy',
    'verify.yml',
    'verify',
    'end-to-end verification',
    '--tags db runs only the tagged tier',
    '-l app limits the run to one host group',
    'the database must exist before the app tries to connect',
    'the app must answer before the proxy sends it traffic',
    'The database must exist before the app tries to connect, and the app must answer before the proxy sends it traffic.'
]

step_numbers = {'1', '2', '3', '4', '5'}

found_texts = [t for t, fs, el in text_elements]

print("\n--- LABEL VERIFICATION ---")
matched = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    status = "OK" if cnt == 1 else f"FAIL (count={cnt})"
    if cnt != 1:
        matched = False
    print(f"  '{exp}': {status}")

assert matched, "Some expected labels failed matching!"
print("\nAll 27 expected labels matched EXACTLY ONCE!")

# Check extra text
extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found extra texts: {extras}"
print("No extra or unexpected text: PASS!")

# Check forbidden style instruction words
forbidden = ['orange', 'green', 'grey', 'bold', 'monospace', 'arrow']
for t in found_texts:
    for word in forbidden:
        # Check as standalone word in visible text
        # (Note: 'arrow' or 'green' should not appear in visible text)
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        if word in words:
            print(f"WARNING: Forbidden word '{word}' found in text '{t}'!")
            raise AssertionError(f"Forbidden style word '{word}' in text: '{t}'")

print("No forbidden style instruction words in visible text: PASS!")

print("\nALL VERIFICATIONS PASSED CLEANLY!")
