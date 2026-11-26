import xml.etree.ElementTree as ET
import re
import pathlib
import sys

svg_path = "test_gpu_probe_pipefail.svg"
print(f"Auditing {svg_path}...")
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. First children check: <title> and <desc>
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

title_text = children[0].text.strip()
desc_text = children[1].text.strip()
assert title_text == "The GPU count probe, and the pipe that hides a failure", f"Wrong title: {title_text}"
assert "The GPU count probe, and the pipe that hides a failure" not in desc_text, "Title must not be repeated verbatim in desc!"
print("   PASS: Title and desc are valid first children")

# 2. Dimensions
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"Expected width 1600, got {width}"
assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"
print("   PASS: Canvas dimensions and viewBox valid")

# 3. Check font-size >= 24 on all text and tspans
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = elem.attrib.get('font-size')
    assert fs is not None, f"Missing font-size on text '{full_text}'"
    size = float(fs)
    assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
    for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, size))

print(f"\n3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "The GPU count probe, and the pipe that hides a failure",
    "Count visible GPUs: shell nvidia-smi -L | wc -l, args executable /bin/bash, register gpu_count, changed_when false (read-only, never changed), failed_when gpu_count.rc != 0 or (gpu_count.stdout | int) != expected_gpus, check_mode false (run even under --check, safe because read-only)",
    "Ansible starts /bin/bash, which runs nvidia-smi -L and pipes the listing into wc -l; the count comes back as text in gpu_count.stdout; failed_when converts it with int and compares with the expected count; a node showing seven GPUs when eight are expected fails the task at once and the message names the task",
    "nvidia-smi fails with an error while wc succeeds on empty output: the pipeline reports success and the playbook believes the node has no GPUs and moves on",
    "set -o pipefail works only in bash, so the probe needs executable /bin/bash and set -o pipefail; if that gets fragile keep the probe simple or split it into a module call plus Jinja filters",
    "A pipe takes the exit code of its last command"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:50]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"
print("   PASS: All expected labels found exactly once")

# 5. Extras check
extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("   PASS: Zero extra text elements")

# 6. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("\n6. PASS: No forbidden styling words found in text")

# 7. Check orange count
svg_str = pathlib.Path(svg_path).read_text(encoding='utf-8')
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("   PASS: Orange used selectively for the trap only")

# 8. Check arrows count
arrows = list(root.iter('{http://www.w3.org/2000/svg}line'))
arrow_lines = [l for l in arrows if 'marker-end' in l.attrib]
paths_with_marker = [p for p in root.iter('{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(arrow_lines) + len(paths_with_marker)
print(f"\n8. Total arrows: {total_arrows} (expected 0)")
assert total_arrows == 0, f"Expected 0 arrows, found {total_arrows}"
print("   PASS: Arrow count matches source (0 arrows)")

# 9. Colors present
for col in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert col in svg_str, f"Missing required color: {col}"
print("\n9. PASS: All required palette colors present")

# 10. Check text padding and bounds
print("\n10. Checking text bounds & paddings...")
# Boxes:
# Card 1: (40, 150, 740, 380)
# Card 2: (40, 570, 740, 360)
# Card 3: (820, 150, 740, 380)
# Card 4: (820, 570, 740, 360)
# Bottom bar: (40, 970, 1520, 70)

# Card 1 text:
def verify_card_text(card_id, box_x, box_y, box_w, box_h, icon_x, icon_y, icon_w, icon_h):
    g = root.find(f".//*[@id='{card_id}']")
    assert g is not None, f"Group {card_id} not found"
    text = g.find('{http://www.w3.org/2000/svg}text')
    assert text is not None, f"Text in {card_id} not found"
    
    base_fs = float(text.attrib.get('font-size', 24))
    base_x = float(text.attrib.get('x', box_x + 30))
    base_y = float(text.attrib.get('y', box_y + 50))
    
    tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
    
    # Track position
    cur_y = base_y
    # We iterate over top-level tspans (lines)
    for i, tsp in enumerate(tspans):
        # If it's a nested tspan, handle in parent
        # Only process lines that have an x attribute
        if 'x' not in tsp.attrib:
            continue
        line_x = float(tsp.attrib['x'])
        dy = float(tsp.attrib.get('dy', 0))
        cur_y += dy
        
        # Calculate conservative width for the line
        # Full text of this line:
        line_text = "".join(tsp.itertext()).strip()
        fs = float(tsp.attrib.get('font-size', base_fs))
        ff = tsp.attrib.get('font-family', '')
        # Check if any nested tspan is mono
        has_mono = 'monospace' in ff or any('monospace' in sub.attrib.get('font-family', '') for sub in tsp.findall('.//{http://www.w3.org/2000/svg}tspan'))
        cw = 0.62 * fs if has_mono else 0.60 * fs
        w = len(line_text) * cw
        
        pad_l = line_x - box_x
        pad_r = (box_x + box_w) - (line_x + w)
        pad_b = (box_y + box_h) - cur_y
        
        print(f"   [{card_id}] Line {i+1} ({fs}px): \"{line_text[:25]}...\" w={w:.1f} pl={pad_l:.1f} pr={pad_r:.1f} pb={pad_b:.1f}")
        assert pad_l >= 16, f"Left padding {pad_l} < 16 on line {i+1} in {card_id}"
        assert pad_r >= 16, f"Right padding {pad_r} < 16 on line {i+1} in {card_id}: {line_text}"
        assert pad_b >= 16, f"Bottom padding {pad_b} < 16 on line {i+1} in {card_id}"
        
        # Check icon clearance if on same vertical span
        if not (cur_y < icon_y or (cur_y - fs) > (icon_y + icon_h)):
            # On same vertical span, line must end at least 16px before icon_x
            pad_icon = icon_x - (line_x + w)
            print(f"      (Shares vertical span with icon: clearance={pad_icon:.1f}px)")
            assert pad_icon >= 16, f"Text touches icon on line {i+1} in {card_id}: pad={pad_icon}"

verify_card_text('card-annotated-task', 40, 150, 740, 380, 694, 175, 56, 56)
verify_card_text('card-walk', 40, 570, 740, 360, 694, 595, 56, 56)
verify_card_text('card-the-trap', 820, 150, 740, 380, 1474, 175, 56, 56)
verify_card_text('card-fix', 820, 570, 740, 360, 1474, 595, 56, 56)

print("\n==========================================")
print("ALL AUDIT CHECKS PASSED WITH 100% SUCCESS!")
print("==========================================")
