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

# Check marker in defs has fill=#db8129, and body path has stroke=#db8129
defs_marker = root.find('.//{http://www.w3.org/2000/svg}marker[@id="arrow-orange"]')
assert defs_marker is not None, "arrow-orange marker must exist"

body_orange_paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('stroke') == "#db8129"]
print(f"Body orange paths: {len(body_orange_paths)}")
assert len(body_orange_paths) == 1, f"Expected exactly 1 orange path in body, got {len(body_orange_paths)}"
print("[PASS] Orange used only for the single alternating flapping arrow.")

print("\n=== 7. Checking No External Images / Scripts ===")
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in raw.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in raw, "No external URLs"
print("[PASS] No external images, scripts, or fonts.")

print("\n=== 8. Checking Paddings of All Text Elements Inside Their Containers ===")
boxes = [
    # (prefix, bx, by, bw, bh, is_mono, fs)
    ("Three log shapes", 0, 0, 1600, 100, False, 48),
    ("Node flapping", 50, 115, 460, 90, False, 30),
    ("slurmctld: error:", 88, 238, 384, 110, True, 24),
    ("slurmctld: Node", 88, 368, 384, 114, True, 24),
    ("rarely Slurm:", 74, 515, 412, 215, False, 24),
    ("investigate the network", 74, 750, 412, 245, False, 24),
    ("Job killed for memory", 570, 115, 460, 95, False, 30),
    ("slurmd log shows", 594, 225, 412, 270, False, 24),
    ("user asked for less", 594, 515, 412, 480, False, 24),
    ("Invalid RPC after", 1090, 115, 460, 95, False, 30),
    ("a compute node logs", 1114, 225, 412, 770, False, 24),
    ("exact wording differs", 50, 1055, 1500, 65, False, 26),
]

for el in root.iter('{http://www.w3.org/2000/svg}text'):
    combined = " ".join("".join(el.itertext()).split())
    matched = None
    for prefix, bx, by, bw, bh, is_mono, fs in boxes:
        if combined.startswith(prefix):
            matched = (prefix, bx, by, bw, bh, is_mono, fs)
            break
    assert matched is not None, f"No matching box for '{combined[:30]}'"
    prefix, bx, by, bw, bh, is_mono, fs = matched
    
    char_w = 0.62 * fs if is_mono else 0.6 * fs
    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        lines = [ts.text.strip() for ts in tspans if ts.text and ts.text.strip()]
        tx = float(tspans[0].attrib.get('x', el.attrib.get('x', '0')))
    else:
        lines = [el.text.strip()]
        tx = float(el.attrib.get('x', '0'))
        
    print(f"\nBox ({bx}, {by}, {bw}, {bh}) for '{prefix}...':")
    for l in lines:
        w = len(l) * char_w
        if el.attrib.get('text-anchor') == 'middle':
            pad_left = (tx - w/2) - bx
            pad_right = (bx + bw) - (tx + w/2)
        else:
            pad_left = tx - bx
            pad_right = (bx + bw) - (tx + w)
        print(f"  [{len(l):2d}c, {w:5.1f}px] left_pad={pad_left:4.1f}px, right_pad={pad_right:4.1f}px | '{l}'")
        assert pad_left >= 16, f"Left pad {pad_left} < 16 for '{l}'"
        assert pad_right >= 16, f"Right pad {pad_right} < 16 for '{l}'"

print("\n=== ALL STRICT RULES AND PADDINGS PASSED 100% PERFECTLY! ===")
