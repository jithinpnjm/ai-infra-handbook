import xml.etree.ElementTree as ET
import re

svg_file = "candidate_lossless.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas
vb = root.attrib.get("viewBox").split()
W = float(vb[2])
H = float(vb[3])
width = float(root.attrib.get("width"))
height = float(root.attrib.get("height"))
print(f"2. Canvas: W={W}, H={H}, width={width}, height={height}")
assert W == 1600
assert 900 <= H <= 1200
assert width == 1600
assert height == H

# 3. Font sizes >= 24
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', '0'))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if fs == 0 and tspans:
        fs = float(tspans[0].attrib.get('font-size', '0'))
    assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
    for tsp in tspans:
        tfs = tsp.attrib.get('font-size')
        if tfs is not None:
            assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
    text_elements.append((full_text, fs))

print(f"3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "A lossless Ethernet class needs every piece set the same, end to end",
    "PFC (802.1Qbb) for the RoCE priority, on the NIC and on every switch",
    "ECN marking with DCQCN or similar rate control",
    "DSCP and PCP trust and mapping set correctly",
    "buffer allocation and headroom sized for each port speed and cable length",
    "per-port counters watched: CRC, FEC uncorrected, symbol errors, PFC pause counts per priority, ECN-marked packets, buffer occupancy, link flaps, optical power (DOM)",
    "NIC",
    "Leaf switch port",
    "Spine switch port",
    "Leaf switch port",
    "NIC",
    "the lossless class works only end to end",
    "PFC missing on one switch port: drops, and RDMA retransmits are costly",
    "misconfigured the other way: pause storms and deadlocks",
    "InfiniBand: credit-based flow control per virtual lane, lossless by construction; LIDs and GIDs replace MACs and IPs; the Subnet Manager programs forwarding tables",
    "Rail-optimised: one NIC per GPU, often its own subnet, VLAN or VRF; 8 x 400G back end; a single x4 link at 100G instead of 400G slows the whole job because collectives move at the speed of the slowest participant",
    "Treat a PFC change on one switch as a change to the whole fabric"
]

found_texts = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(found_texts)} found:")

for exp in set(expected_labels):
    exp_cnt = expected_labels.count(exp)
    cnt = found_texts.count(exp)
    ok = (cnt == exp_cnt)
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt} (exp {exp_cnt}): '{exp}'")
    assert ok, f"Mismatch for '{exp}': got {cnt}, expected {exp_cnt}"

extras = [t for t in found_texts if t not in expected_labels]
print(f"\nExtra texts: {extras}")
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n5. Forbidden words check: PASS!")

# 6. Colors check
svg_str = open(svg_file).read()
for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert c in svg_str, f"Missing required color {c}"

oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 6, f"Unexpected orange count: {len(oranges)}"

# 7. Arrows check
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"7. Total arrows: {total_arrows}")
assert total_arrows == 6, f"Expected 6 arrows, got {total_arrows}"

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
