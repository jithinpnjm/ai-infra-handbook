import xml.etree.ElementTree as ET
import re

tree = ET.parse('output.svg')
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
print(f"2. Dimensions: {width}x{height}, viewBox='{viewBox}'")
assert width == "1600"
assert viewBox == "0 0 1600 1140"
assert int(height) <= 1200

# 3. Text elements & font size >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib.get('font-size'))
    assert fs >= 24, f"Text font size {fs} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            assert float(tfs) >= 24, f"tspan font size {tfs} < 24!"
    text_elements.append((full_text, fs))

print(f"3. Total text elements: {len(text_elements)} (all >= 24px)")

# 4. Label counts
expected_labels = [
    'The Ansible CI workflow: lint gates the Molecule matrix',
    'ansible-ci workflow',
    'lint',
    'runs-on ubuntu-latest',
    'yamllint . && ansible-lint',
    'needs: lint',
    'molecule',
    'role: kernel_tuning, chrony_client, dcgm_exporter',
    'distro: ubuntu2204, rockylinux9',
    'molecule test',
    'a broken file never starts a container',
    'gpu-hw',
    'runs-on self-hosted, gpu',
    'molecule test -s gpu_hw',
    'runs on schedule (nightly cron 0 4 * * *) or when a pull request has the test-gpu label'
]

found_texts = [t for t, fs in text_elements]
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"  '{exp}': count={cnt}")
    assert cnt == 1, f"Expected '{exp}' once, got {cnt}!"

for t in found_texts:
    assert t in expected_labels, f"Unexpected text '{t}' found!"

print("4. Exact label fidelity passed!")

# 5. Arrows
markers = [e for e in root.iter() if 'marker-end' in e.attrib]
print(f"5. Arrows with marker-end: {len(markers)}")
assert len(markers) == 1

# 6. Orange usage
raw_svg = open('output.svg').read()
oranges = re.findall(r'#db8129', raw_svg)
print(f"6. Orange color occurrences: {len(oranges)}")
assert len(oranges) == 3

print("\n--- ALL VALIDATIONS PASSED ---")
