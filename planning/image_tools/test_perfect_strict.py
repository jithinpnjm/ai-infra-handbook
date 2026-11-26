import xml.etree.ElementTree as ET
import re

tree = ET.parse('perfect_candidate.svg')
root = tree.getroot()

# 1. First children check
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
assert int(height) <= 1200

# 3. Font sizes >= 24 px
font_sizes = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{elem.text}'"
    font_sizes.append(float(fs))
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs:
            font_sizes.append(float(tfs))

too_small = [s for s in font_sizes if s < 24]
assert len(too_small) == 0, f"Found font sizes < 24: {too_small}"
print(f"3. All font sizes >= 24 px: min={min(font_sizes)}, max={max(font_sizes)} (OK)")

# 4. Check labels
expected_labels = [
    'Deleted but open: the name is gone, the blocks stay until the descriptor closes',
    'a process opens app.log and writes 20 MB',
    'rm removes the name',
    'link count 0',
    'ls and du no longer see the file',
    'the process still holds the descriptor, so df still counts the blocks',
    '/tmp/.../app.log (deleted)',
    'rescue, copy out, then truncate through /proc/PID/fd/N',
    'df used space falls',
    'copy what you need out of /proc/PID/fd/N',
    ': > /proc/PID/fd/N',
    'the process keeps writing',
    'lasting fix: make the writer reopen its file after rotation',
    'The space comes back when the last descriptor closes or the file is truncated.'
]

step_numbers = {'1', '2', '3', '4'}

found_texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    found_texts.append(full_text)

print(f"\n4. Checking labels ({len(found_texts)} text elements found):")
for exp in expected_labels:
    cnt = found_texts.count(exp)
    print(f"  '{exp[:40]}...': count={cnt}")
    assert cnt == 1, f"Expected label '{exp}' count={cnt}, must be exactly 1!"

extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
print(f"Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"
print("\n5. No forbidden words found in text (OK)")

# 6. Check arrows
arrows = root.findall('.//{http://www.w3.org/2000/svg}line[@marker-end]')
print(f"\n6. Total arrows with marker-end: {len(arrows)}")
assert len(arrows) == 3, f"Expected exactly 3 arrows between 4 steps, got {len(arrows)}"

print("\nALL VERIFICATIONS PASSED!")
