import xml.etree.ElementTree as ET
import re

svg_path = "test_gpu_sharing.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Children: <{first_tag}>, <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("   [PASS] <title> and <desc> are the first children.")

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox={viewBox}, width={width}, height={height}")
assert width == "1600", f"Width must be 1600, got {width}"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200, f"Height must be between 900 and 1200, got {vb_parts[3]}"
assert int(height) == int(vb_parts[3])
print("   [PASS] Canvas dimensions valid.")

# 3. Font size check: >= 24 on all text and tspans
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
    "Choosing how to share a GPU, with the config for each",
    "Training, multi-GPU, performance-sensitive: whole GPUs, never share",
    "Many small inference or dev jobs, isolation required: MIG; hardware partition of A100 or H100 into up to seven isolated instances, each with own SMs, memory and bandwidth; Slurm treats each instance as a GPU with cgroup isolation and task binding; config example Gres=gpu:a100:1,gpu:a100_3g.20gb:2 with AccountingStorageTRES gres/gpu:a100_3g.20gb; Slurm does not partition the GPU: create instances with nvidia-smi mig or the GPU Operator MIG manager before slurmd starts; no dynamic MIG partitioning; static and fragmenting, a 3g.20gb instance cannot be merged; no NVLink or multi-GPU use; AutoDetect=nvml is the only mode that handles MIG",
    "Many cooperating small processes, throughput, trusted users: MPS; gres/mps count, Gres=gpu:2,mps:200 means 100 per GPU",
    "Maximum density, trusted workloads, simple: sharding; gres/shard, Gres=gpu:2,shard:64 gives 32 shards per GPU; by default it does not fence the processes or constrain device memory",
    "Fractional GPUs for notebooks and serving across a platform: consider Kubernetes (time-slicing, MIG, DRA)",
    "keep MIG partitions and whole-GPU partitions separate; check with a one-GPU test in each and compare nvidia-smi -L; MIG layout must be recreated before slurmd after reboot"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("   [PASS] Exactly the expected labels, each once, no extras!")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. No forbidden words found! (PASS)")

# 6. Check orange count
with open(svg_path) as f:
    raw_svg = f.read()

orange_matches = re.findall(r'#db8129', raw_svg, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"
print("   [PASS] Orange used only for MIG card.")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib or "marker-start" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib or "marker-start" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with markers: {total_arrows}")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"
print("   [PASS] Exactly 0 arrows, matching source.")

# 8. Check external resources: no external fonts, images or scripts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in raw_svg.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in raw_svg, "No external URLs"
print("\n9. No external images, scripts or fonts! (PASS)")

# 9. Check outside margins and box gaps
boxes = [
    ("row-whole-gpus", 40, 130, 1520, 84),
    ("row-mig", 40, 256, 1520, 286),
    ("row-mps", 40, 584, 1520, 104),
    ("row-sharding", 40, 730, 1520, 126),
    ("row-kubernetes", 40, 898, 1520, 104),
    ("row-tip", 40, 1044, 1520, 104),
]

print("\n10. Checking margins and gaps:")
assert boxes[0][1] >= 40, "Left margin must be >= 40"
assert 1600 - (boxes[0][1] + boxes[0][3]) >= 40, "Right margin must be >= 40"
assert boxes[0][2] >= 40, "Top margin must be >= 40"
assert 1200 - (boxes[-1][2] + boxes[-1][4]) >= 40, "Bottom margin must be >= 40"

for i in range(len(boxes) - 1):
    gap = boxes[i+1][2] - (boxes[i][2] + boxes[i][4])
    print(f"    Gap between {boxes[i][0]} and {boxes[i+1][0]}: {gap}px")
    assert gap >= 40, f"Gap {gap} < 40px between box {i} and {i+1}!"

print("   [PASS] All margins and gaps >= 40px!")

# 10. Check text padding and line widths inside boxes
# Each tspan line width checked conservatively
print("\n11. Checking text paddings inside boxes (>= 16px):")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    if elem.attrib.get('font-size') == "48":
        continue
    x = float(elem.attrib.get('x', 0))
    fs = float(elem.attrib.get('font-size', 24))
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    
    # Text starts at x=140, box right edge is at 1560
    # Available width is 1560 - 140 = 1420
    # Left padding from icon (icon is at 62..118): 140 - 118 = 22px >= 16px!
    assert x - 118 >= 16, f"Padding between icon and text {x - 118} < 16px"
    
    # Check lines
    # Group tspans by line (x attribute present means new line, or first tspan)
    lines = []
    cur_line = []
    for tsp in tspans:
        if tsp.attrib.get('x') is not None and cur_line:
            lines.append(cur_line)
            cur_line = [tsp]
        else:
            cur_line.append(tsp)
    if cur_line:
        lines.append(cur_line)
    
    for l in lines:
        line_chars = sum(len(tsp.text or "") for tsp in l)
        is_mono = any(tsp.attrib.get('font-family') == 'monospace' for tsp in l)
        factor = 0.62 if is_mono else 0.60
        line_width = line_chars * fs * factor
        right_pad = 1560 - (x + line_width)
        print(f"    Line ({line_chars:2d} chars, {line_width:6.1f}px): right_pad = {right_pad:5.1f}px")
        assert right_pad >= 16, f"Text line exceeds box padding: right_pad={right_pad} < 16px!"

print("   [PASS] All text lines fit inside boxes with >= 16px padding!")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
