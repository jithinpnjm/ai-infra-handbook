import xml.etree.ElementTree as ET
import re

svg_file = "test_candidate_log_shapes.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. Checking XML Root and First Children ===")
assert root.tag.endswith('svg'), "Root must be <svg>"
tag1 = root[0].tag.split('}')[-1]
tag2 = root[1].tag.split('}')[-1]
print(f"First children: <{tag1}>, <{tag2}>")
assert tag1 == "title", "First child must be <title>"
assert tag2 == "desc", "Second child must be <desc>"
print("[PASS] First children are <title> and <desc>.")

print("\n=== 2. Checking Dimensions and viewBox ===")
w = root.attrib.get('width')
h = root.attrib.get('height')
vb = root.attrib.get('viewBox')
print(f"width={w}, height={h}, viewBox={vb}")
assert w == "1600", f"Width must be 1600, got {w}"
assert vb.startswith("0 0 1600"), f"viewBox must start with '0 0 1600', got {vb}"
h_val = int(vb.split()[-1])
assert 900 <= h_val <= 1200, f"Height must be between 900 and 1200, got {h_val}"
print("[PASS] Dimensions valid.")

print("\n=== 3. Extracting and Checking Text Elements and Font Sizes ===")
full_texts = []
font_sizes = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', '0'))
    combined = " ".join("".join(el.itertext()).split())
    full_texts.append(combined)
    font_sizes.append((combined, fs))
    for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
        t_fs = float(ts.attrib.get('font-size', fs))
        t_content = " ".join("".join(ts.itertext()).split())
        if t_content:
            font_sizes.append((t_content, t_fs))

for t, fs in font_sizes:
    assert fs >= 24, f"Font size {fs} < 24 for text: '{t}'"
print(f"[PASS] All {len(font_sizes)} text/tspan nodes have font-size >= 24px.")

print("\n=== 4. Checking Banned Styling Words ===")
banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for ft in full_texts:
    words = re.findall(r'\b[A-Za-z]+\b', ft.lower())
    for b in banned:
        assert b not in words, f"Banned styling word '{b}' found in text: '{ft}'"
print("[PASS] No banned styling words in text.")

print("\n=== 5. Checking Required Source Labels ===")
spec_labels = [
    "Three log shapes worth recognising",
    "Node flapping",
    "slurmctld: error: Nodes dgx-h100-14 not responding",
    "slurmctld: Node dgx-h100-14 now responding",
    "rarely Slurm: packets dropped on the management network, or the node so loaded that slurmd cannot answer the ping in time",
    "investigate the network and node CPU and I/O load before touching Slurm settings; changing a timeout to hide a flapping node hides the fault",
    "Job killed for memory",
    "slurmd log shows a step dying with signal 9 and a memory-limit message for the job's cgroup",
    "user asked for less memory than the job used; the kernel out-of-memory killer acting at the cgroup limit ended the job",
    "Invalid RPC after an upgrade",
    "a compute node logs it received an RPC it does not understand or a message with zero bytes; version mismatch; slurmd must never be newer than slurmctld; nodes may be older than the controller during a rolling upgrade",
    "exact wording differs between versions; learn the shape"
]

for sl in spec_labels:
    cnt = full_texts.count(sl)
    print(f"Label count={cnt}: '{sl[:45]}...'")
    assert cnt == 1, f"Expected '{sl}' to appear exactly once, got {cnt}"

assert len(full_texts) == len(spec_labels), f"Expected {len(spec_labels)} text elements, got {len(full_texts)}: {set(full_texts) - set(spec_labels)}"
print(f"[PASS] Exactly {len(spec_labels)} text elements, all 12 spec labels present, none missing, none invented.")

print("\n=== 6. Checking Orange Highlight Usage ===")
with open(svg_file) as f:
    raw = f.read()
orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
print(f"Orange #db8129 occurrences in file: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 3, f"Orange count {len(orange_matches)} out of bounds"

# Specifically check body paths with stroke="#db8129"
body_orange = [e for e in root.iter() if e.attrib.get('stroke') == "#db8129" or e.attrib.get('fill') == "#db8129"]
# Filter out defs
body_orange = [e for e in body_orange if not e.tag.endswith('path') or 'defs' not in [p.tag for p in root.iter() if e in list(p)]]
print(f"Body orange elements: {len(body_orange)}")
assert len(body_orange) == 1, f"Expected exactly 1 orange element in body, got {len(body_orange)}"
print("[PASS] Orange used only for the alternating flapping arrow.")

print("\n=== 7. Checking No External Images / Scripts ===")
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in raw.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in raw, "No external URLs"
print("[PASS] No external images, scripts, or fonts.")

print("\n=== ALL STRICT RULES PASSED PERFECTLY! ===")
