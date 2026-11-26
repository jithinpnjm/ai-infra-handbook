import xml.etree.ElementTree as ET
import re, pathlib

svg_path = "candidate_failures.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure check: First children must be title and desc
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas size check
viewBox = root.attrib.get("viewBox")
width = root.attrib.get("width")
height = root.attrib.get("height")
print(f"2. Canvas: viewBox: {viewBox}, width: {width}, height: {height}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert float(height) == vb_parts[3]

# 3. Check font sizes >= 24
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

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t[:50]}...'")

# 4. Check expected labels
expected_labels = [
    "Eight early failures and where to look",
    "1 Invalid authentication credential or Unable to contact slurm controller: different munge keys, clock skew over a few minutes, munged not running, wrong permissions on /etc/munge or /run/munge",
    "2 Node invalid or drain with Low RealMemory: node line does not match what slurmd discovers; run slurmd -C",
    "3 Jobs rejected or sacctmgr hangs, Invalid account or account/partition combination: slurmdbd not running, wrong DB credentials, max_allowed_packet too small, blocked port, no association; follow the request: command to slurmdbd to database to login",
    "4 Controller will not start or empty queue: StateSaveLocation not writable, full, not shared, wiped",
    "5 Can't find an address, wrong user, Invalid user id: NodeName differs from hostname with no NodeHostname or NodeAddr, DNS or hosts inconsistencies, UID mismatch",
    "6 slurmd will not start after an OS upgrade: OS switched to cgroup v2 while Slurm built without v2, cgroup.conf forces v1, missing systemd delegation; stat -fc %T /sys/fs/cgroup",
    "7 Socket timed out on send/recv operation: polling loops from hundreds of clients running squeue every second, too small MaxJobCount, accounting back-pressure; run sdiag, look at RPC statistics by type and by user; use sacct for history, exporters that poll once, RPC rate limiting",
    "8 squeue and sinfo time out but running jobs continue: accounting database under strain, very wide sacct or sreport query; sdiag thread count and agent queue, slurmdbd.log lock waits, SHOW FULL PROCESSLIST in the database",
    "read the first error, not the last"
]

found_texts = [t for t, fs in text_elements]

print("\n4. Checking single-occurrence expected labels:")
for lbl in expected_labels:
    cnt = found_texts.count(lbl)
    assert cnt == 1, f"Expected label '{lbl[:40]}...' count {cnt} != 1"
    print(f"   [PASS] count=1: '{lbl[:50]}...'")

# Check extras
extras = [t for t in found_texts if t not in expected_labels]
print(f"\n   Extra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Total count {len(found_texts)} != {len(expected_labels)}"

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f_word in forbidden:
        assert f_word not in words, f"Forbidden word '{f_word}' found in '{t}'!"

print("\n5. No forbidden style words found in text: PASS!")

# 6. Check orange usage
svg_str = pathlib.Path(svg_path).read_text()
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange #db8129 occurrences: {len(oranges)}")
assert len(oranges) == 1, f"Expected exactly 1 orange usage, got {len(oranges)}"

# 7. Check arrows count
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"\n7. Total arrows with marker-end: {total_arrows} (expected 0)")
assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

# 8. Check external resources: no external fonts, images or scripts
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("\n8. No external images, scripts or fonts: PASS!")

print("\nALL 8 STRICT AUDIT CHECKS PASSED PERFECTLY!")
