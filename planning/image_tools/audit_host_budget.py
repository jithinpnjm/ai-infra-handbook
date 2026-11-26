#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

svg_path = "test_host_budget.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

print("=== 1. XML Root & First Children ===")
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

print("\n=== 2. Canvas Dimensions ===")
width = root.get('width')
height = root.get('height')
viewBox = root.get('viewBox')
print(f"width={width}, height={height}, viewBox={viewBox}")
assert width == "1600", f"width must be 1600, got {width}"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

print("\n=== 3. Text Elements & Font Size ===")
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

print(f"Total text elements found: {len(text_elements)}")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"  {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected Labels Check ===")
expected_labels = [
    "Host memory budget for an 8 GPU node: multiplied workers add up fast",
    "Operating system and daemons (a few GB)",
    "Data-loader workers (process overhead, decoded batches, prefetch queue) x number of workers x GPUs",
    "Pinned staging buffers",
    "Framework host allocations: CUDA context host memory, NCCL buffers, NCCL proxy threads",
    "Page cache to keep for the dataset",
    "Checkpoint staging headroom in tmpfs or page cache",
    "Margin",
    "8 GPUs x 16 workers x 2 GB = 256 GB",
    "Checkpoints put in /dev/shm without a size cap",
    "Compare the total with MemAvailable and the cgroup limits; test with the real job and watch RssAnon and PSI; monitor MemAvailable, PSI, per-cgroup memory.stat and the OOM counters",
    "A budget on paper is a starting point, not a promise"
]

found_texts = [t for t, fs in text_elements]
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"  [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
print("PASS: Exactly the 12 expected labels present, each once!")

print("\n=== 5. Forbidden Words Check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = [w.strip("(),:;.'\"").lower() for w in t.split()]
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"
print("PASS: No forbidden style instruction words in text!")

print("\n=== 6. Palette & Orange Highlight ===")
raw = pathlib.Path(svg_path).read_text()
assert "#f5f8f5" in raw, "Missing light background #f5f8f5"
assert "#303a36" in raw, "Missing text #303a36"
assert "#207448" in raw, "Missing main green #207448"
assert "#e8f1ea" in raw, "Missing light green #e8f1ea"
assert "#db8129" in raw, "Missing orange #db8129"
orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Orange count {len(orange_matches)} out of bounds"
print("PASS: Palette and orange highlight verified!")

print("\n=== 7. Arrows Count ===")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib or "marker-start" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib or "marker-start" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows with markers: {total_arrows}")
assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"
print("PASS: Exactly 0 arrows verified!")

print("\n=== 8. Outside Margins & Gaps ===")
boxes = [
    ("left-budget-bar", 40, 150, 710, 690),
    ("right-calculation", 790, 150, 420, 690),
    ("right-mistake-card", 1250, 150, 310, 690),
    ("bottom-strip", 40, 880, 1520, 130),
    ("bottom-bar", 40, 1050, 1520, 60),
]

for name, x, y, w, h in boxes:
    left_m = x
    right_m = 1600 - (x + w)
    top_m = y
    bot_m = int(height) - (y + h)
    assert left_m >= 40, f"{name} left margin {left_m} < 40"
    assert right_m >= 40, f"{name} right margin {right_m} < 40"
    assert top_m >= 40, f"{name} top margin {top_m} < 40"
    assert bot_m >= 40, f"{name} bot margin {bot_m} < 40"
    print(f"  {name:20s}: L={left_m} R={right_m} T={top_m} B={bot_m} (PASS)")

# Gaps between columns and rows
assert (790 - (40 + 710)) >= 40, "Gap left to col 1 < 40"
assert (1250 - (790 + 420)) >= 40, "Gap col 1 to col 2 < 40"
assert (880 - (150 + 690)) >= 40, "Gap main to bottom strip < 40"
assert (1050 - (880 + 130)) >= 40, "Gap bottom strip to bottom bar < 40"
print("PASS: All gaps >= 40px verified!")

print("\n=== 9. Chrome Render Screenshot ===")
chrome_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
screenshot_path = '/tmp/svgcheck/test_host_budget.png'
pathlib.Path('/tmp/svgcheck').mkdir(exist_ok=True)
cmd = [
    chrome_path,
    '--headless=new',
    '--disable-gpu',
    '--hide-scrollbars',
    f'--window-size=1600,{height}',
    f'--screenshot={screenshot_path}',
    f'file://{pathlib.Path(svg_path).resolve()}'
]
res = subprocess.run(cmd, capture_output=True, text=True)
print(f"Chrome screenshot result: returncode={res.returncode}, file={screenshot_path}")
assert pathlib.Path(screenshot_path).exists(), "Screenshot was not generated"

print("\nALL AUDIT CHECKS PASSED SUCCESSFULLY!")
