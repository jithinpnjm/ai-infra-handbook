#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

tree = ET.parse("candidate_thread_tree.svg")
root = tree.getroot()

# 1. First children check: <title> and <desc>
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
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

# 3. Check text elements and font-size >= 24
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
    "One PyTorch job is a tree of processes and threads",
    "PyTorch job",
    "Launcher",
    "starts one process per GPU",
    "Process per GPU",
    "Main thread: runs the Python interpreter",
    "Extra threads: CUDA callbacks, NCCL and autograd",
    "forks",
    "DataLoader with num_workers=N",
    "N more processes",
    "Processes, not threads: Python's global interpreter lock limits CPU parallelism in threads.",
    "Threads share one process. Processes are started for data loading."
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected distinct labels:")
all_ok = True
for exp in expected_labels:
    cnt = found_texts.count(exp)
    ok = (cnt >= 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed presence check!"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for word in forbidden:
        assert word not in words, f"Forbidden word '{word}' found in '{t}'!"

print("\n5. No forbidden words found in text (PASS)")

# 6. Check orange #db8129 occurrences
svg_str = open("candidate_thread_tree.svg").read()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n7. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"

# 8. Render PNG with headless Chrome
d = pathlib.Path('/tmp/svgcheck')
d.mkdir(exist_ok=True)
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '--headless=new',
                '--disable-gpu',
                '--hide-scrollbars',
                f'--window-size=1600,{height}',
                f'--screenshot={d}/candidate_thread_tree.png',
                f'file://{pathlib.Path("candidate_thread_tree.svg").resolve()}'],
               capture_output=True, timeout=60)
print(f"\n8. Rendered PNG to {d}/candidate_thread_tree.png")

print("\nALL VERIFICATIONS PASSED PERFECTLY!")
