import xml.etree.ElementTree as ET
import re

tree = ET.parse('test_candidate.svg')
root = tree.getroot()

# 1. First children check
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

# 2. ViewBox and Dimensions
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")

# 3. Check text elements and font sizes
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    text_elements.append((full_text, fs, elem))

print(f"\nTotal <text> elements: {len(text_elements)}")
for t, fs, el in text_elements:
    print(f"  [{fs}px] '{t}'")
    for tsp in el.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{t}'"
    if fs is not None:
        assert float(fs) >= 24, f"text font-size {fs} < 24 in '{t}'"

print("\nAll font sizes >= 24: PASS!")

# 4. Check expected labels
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

found_texts = [t for t, fs, el in text_elements]

print("\n--- LABEL VERIFICATION ---")
all_matched = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    status = "OK" if cnt == 1 else f"FAIL (count={cnt})"
    if cnt != 1:
        all_matched = False
    print(f"  '{exp}': {status}")

assert all_matched, "Some labels were not found exactly once!"
print(f"\nAll {len(expected_labels)} labels found EXACTLY ONCE: PASS!")

# 5. Check for unexpected labels
extra_texts = []
for t in found_texts:
    if t not in expected_labels:
        extra_texts.append(t)

print(f"Extra texts found: {extra_texts}")
assert len(extra_texts) == 0, f"Found extra texts: {extra_texts}"
print("No extra or invented text: PASS!")

# 6. Check arrows
lines_with_marker = []
for line in root.iter('{http://www.w3.org/2000/svg}line'):
    if line.attrib.get('marker-end'):
        lines_with_marker.append(line)
for path in root.iter('{http://www.w3.org/2000/svg}path'):
    if path.attrib.get('marker-end'):
        lines_with_marker.append(path)

print(f"\nTotal arrows with marker-end: {len(lines_with_marker)}")
assert len(lines_with_marker) == 1, f"Expected exactly 1 arrow, found {len(lines_with_marker)}"
print("Exactly ONE arrow present: PASS!")

# 7. Check orange usage
svg_str = open('test_candidate.svg').read()
# Orange matches #db8129
orange_matches = re.findall(r'#db8129', svg_str)
print(f"\nOrange #db8129 occurrences: {len(orange_matches)}")
# In defs (marker polygon fill), line stroke, and text fill
assert len(orange_matches) == 3, f"Orange should only be used on the needs: lint arrow, found {len(orange_matches)} times!"
print("Orange used exclusively for the single most important arrow: PASS!")

print("\nALL VERIFICATIONS PASSED CLEANLY!")
