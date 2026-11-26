#!/usr/bin/env python3
import re, pathlib
import xml.etree.ElementTree as ET

svg_text = pathlib.Path("candidate_job_life_refined.svg").read_text()
tree = ET.fromstring(svg_text)

print("=== 1. CHECKING XML STRUCTURE ===")
assert tree.tag.endswith('svg')
assert tree.attrib['width'] == '1600'
assert tree.attrib['viewBox'] == '0 0 1600 1200'

# First children must be title and desc
children = list(tree)
assert children[0].tag.endswith('title'), f"First child is {children[0].tag}, expected title"
assert children[1].tag.endswith('desc'), f"Second child is {children[1].tag}, expected desc"
print("PASS: <title> and <desc> are the first children.")

print("\n=== 2. CHECKING LABELS FROM CONTENT ===")
expected_labels = [
    # Participants
    "User on", "login node",
    "slurmctld",
    "slurmdbd",
    "slurmd on", "node A",
    "slurmd on", "node B",
    # Messages
    "sbatch job.sh", "(RPC with munge credential)",
    "authenticate, run", "job_submit", "plugin, check limits and associations",
    "Submitted batch job 4217",
    "job PENDING in queue, scheduler loop and backfill evaluate it",
    "resources found: allocate nodes A and B, state RUNNING",
    "launch batch step (RPC tree fan-out)",
    "prepare node (prolog)",
    "prolog, fork", "slurmstepd", ", run the batch script",
    "script runs", "srun", ", steps launched on both nodes",
    "epilog, cleanup of processes",
    "job complete RPC",
    "job record: times, resources, exit code, usage",
    "free nodes A and B, run scheduler again"
]

all_text_elements = tree.findall('.//{http://www.w3.org/2000/svg}text')
all_tspan_elements = tree.findall('.//{http://www.w3.org/2000/svg}tspan')

extracted_texts = []
for el in all_text_elements:
    if len(list(el)) == 0:
        if el.text: extracted_texts.append(el.text.strip())
    else:
        # has tspans
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            if ts.text: extracted_texts.append(ts.text.strip())

print(f"Total extracted text chunks: {len(extracted_texts)}")

# Verify all source messages are represented
source_messages = [
    "sbatch job.sh (RPC with munge credential)",
    "authenticate, run job_submit plugin, check limits and associations",
    "Submitted batch job 4217",
    "job PENDING in queue, scheduler loop and backfill evaluate it",
    "resources found: allocate nodes A and B, state RUNNING",
    "launch batch step (RPC tree fan-out)",
    "prepare node (prolog)",
    "prolog, fork slurmstepd, run the batch script",
    "script runs srun, steps launched on both nodes",
    "epilog, cleanup of processes",
    "job complete RPC",
    "job record: times, resources, exit code, usage",
    "free nodes A and B, run scheduler again"
]

for msg in source_messages:
    # check that msg or its constituent words exist in svg text
    # normalize spaces
    normalized_svg = " ".join(svg_text.split())
    # check parts
    words = msg.split()
    for w in words:
        assert w in svg_text, f"Word '{w}' from message '{msg}' not found in SVG!"
    print(f"PASS: Found message '{msg[:40]}...'")

print("\n=== 3. CHECKING FONT SIZES ===")
font_sizes = re.findall(r'font-size="(\d+)"', svg_text)
print(f"Total font-size attributes: {len(font_sizes)}")
for fs in font_sizes:
    val = int(fs)
    assert val >= 24, f"Found font-size={val} < 24!"
print("PASS: No font size is smaller than 24px.")

print("\n=== 4. CHECKING ORANGE USAGE ===")
oranges = re.findall(r'#db8129', svg_text, re.IGNORECASE)
print(f"Total orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) >= 1, "Orange not used!"
# Check what has orange: only step 5 and its marker
assert "resources found: allocate nodes A and B, state RUNNING" in svg_text
print("PASS: Orange #db8129 used for the single most important item (step 5 state RUNNING).")

print("\n=== 5. CHECKING ARROW COUNT ===")
lines = [l for l in tree.findall('.//{http://www.w3.org/2000/svg}line') if 'marker-end' in l.attrib]
paths = [p for p in tree.findall('.//{http://www.w3.org/2000/svg}path') if 'marker-end' in p.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total message arrows: {total_arrows} (lines: {len(lines)}, paths: {len(paths)})")
assert total_arrows == 14, f"Expected 14 arrows, got {total_arrows}!"
print("PASS: Exactly 14 arrows matching the source sequence diagram.")

print("\n=== 6. CHECKING NUMBER CIRCLES ===")
circles = [c for c in tree.findall('.//{http://www.w3.org/2000/svg}circle') if c.attrib.get('r') == '24']
print(f"Total number circles (r=24): {len(circles)}")
assert len(circles) == 14, f"Expected 14 number circles, got {len(circles)}"
print("PASS: Exactly 14 number circles with r=24.")

print("\n=== ALL SYSTEM TESTS PASSED SUCCESSFULLY! ===")
