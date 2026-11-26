import xml.etree.ElementTree as ET
import re

svg_path = "test_candidate_p3_2022.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("1. Title and desc first children: PASS")

# 2. Dimensions and viewBox
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
print(f"2. Dimensions width={width}, height={height}, viewBox={viewBox}: PASS")

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
print(f"3. All font sizes >= 24 px (min={min(font_sizes)}, max={max(font_sizes)}): PASS")

# 4. Extract all text elements and check labels
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size'))
    text_elements.append((full_text, fs))

print(f"\nTotal <text> elements: {len(text_elements)}")
for t, fs in text_elements:
    print(f"  [{fs}px] '{t}'")

expected_labels = [
    "A command line that passes review and still preempts",
    "--max-model-len=16384 --max-num-seqs=128 --max-num-batched-tokens=8192 --gpu-memory-utilization=0.90 on one H100 serving Llama 3.1 8B",
    "Step 1: read the start-up log for GPU KV cache size; with the section 3 inputs the cache holds about 389,100 tokens",
    "Step 2: divide by max-num-seqs: 389,100 / 128 is about 3,040 tokens, the average request length at which 128 running requests fill the cache",
    "Step 3: compare with traffic: if the afternoon average prompt plus output is 4,000 tokens the cache cannot hold the batch, so vLLM preempts and recomputes; preemptions climb every afternoon",
    "lower max-num-seqs to what the cache holds at the real average length: 389,100 / 4,000 is about 97, so a cap near 90 leaves margin; or quantise to grow the cache",
    "the reviewer prints this as information when you give it the log token count"
]
step_numbers = {'1', '2', '3'}

found_texts = [t for t, fs in text_elements]

print("\n--- LABEL VERIFICATION ---")
all_matched = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    status = "OK" if cnt == 1 else f"FAIL (count={cnt})"
    if cnt != 1:
        all_matched = False
    print(f"  '{exp[:50]}...': {status}")

assert all_matched, "Some expected labels failed matching!"
print("\nAll expected labels found EXACTLY ONCE: PASS")

# 5. Check for extra text
for t in found_texts:
    if t in expected_labels or t in step_numbers:
        continue
    assert False, f"Unexpected extra text element: '{t}'"
print("No extra text elements: PASS")

# 6. Check forbidden style words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in forbidden:
        assert f_word not in words, f"Forbidden word '{f_word}' in text '{t}'!"
print("No forbidden style words found in text: PASS")

# 7. Check orange usage: exactly 1 #db8129
raw_svg = open(svg_path).read()
oranges = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\nOrange occurrences (#db8129): {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange usage, found {len(oranges)}"
print("Orange used exactly once: PASS")

# 8. Check arrows: equal to source arrows (0)
arrows = re.findall(r'marker-end', raw_svg)
print(f"Arrows found: {len(arrows)}")
assert len(arrows) == 0, f"Expected 0 arrows, got {len(arrows)}"
print("Arrow count equals 0: PASS")

# 9. Check external references
assert '<image' not in raw_svg
assert '<script' not in raw_svg
assert '@import' not in raw_svg
assert 'http://' not in raw_svg.replace('http://www.w3.org/2000/svg', '')
print("No external resources/fonts/scripts: PASS")

# 10. Check color palette
colors = set(re.findall(r'#[0-9a-fA-F]{6}', raw_svg))
print(f"Colors used: {sorted(colors)}")
allowed_colors = {'#f5f8f5', '#303a36', '#207448', '#e8f1ea', '#ffffff', '#db8129'}
for c in colors:
    assert c.lower() in allowed_colors, f"Unexpected color '{c}'!"
print("All colors adhere strictly to required palette: PASS")

# 11. Check number circles
circles_24 = [c for c in root.iter('{http://www.w3.org/2000/svg}circle') if c.attrib.get('r') == '24']
print(f"\nNumber circles with r=24: {len(circles_24)}")
assert len(circles_24) == 3, f"Expected 3 number circles for the 3 steps, got {len(circles_24)}"
print("Number circles check: PASS")

print("\nALL VERIFICATION CHECKS PASSED PERFECTLY!")
