import xml.etree.ElementTree as ET
import re

svg_file = "candidate_lossless_v2.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Canvas
vb = root.attrib.get("viewBox").split()
W = float(vb[2])
H = float(vb[3])
width = float(root.attrib.get("width"))
height = float(root.attrib.get("height"))
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

print(f"Total text elements = {len(text_elements)} (all >= 24px)")

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
for exp in set(expected_labels):
    exp_cnt = expected_labels.count(exp)
    cnt = found_texts.count(exp)
    assert cnt == exp_cnt, f"Mismatch for '{exp}': got {cnt}, expected {exp_cnt}"

extras = [t for t in found_texts if t not in expected_labels]
assert len(extras) == 0, f"Found unexpected extra text: {extras}"
assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

# 5. Forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in found_texts:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

# 6. Colors check
svg_str = open(svg_file).read()
for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert c in svg_str, f"Missing required color {c}"

oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 6, f"Unexpected orange count: {len(oranges)}"

# 7. Arrows check
lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
total_arrows = len(lines_with_marker) + len(paths_with_marker)
print(f"Total arrows: {total_arrows}")
assert total_arrows == 6, f"Expected 6 arrows, got {total_arrows}"

# 8. Bounds check
def get_tspan_bounds(elem):
    fs = float(elem.attrib.get('font-size', '24'))
    x_base = float(elem.attrib.get('x', '0'))
    y_base = float(elem.attrib.get('y', '0'))
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    lines = []
    if not tspans:
        txt = "".join(elem.itertext()).strip()
        lines.append((txt, x_base, y_base, fs))
    else:
        curr_y = y_base
        for tsp in tspans:
            txt = (tsp.text or "").strip()
            tx = float(tsp.attrib.get('x', str(x_base)))
            dy = float(tsp.attrib.get('dy', '0'))
            curr_y += dy
            tfs = float(tsp.attrib.get('font-size', str(fs)))
            lines.append((txt, tx, curr_y, tfs))
            
    min_x = 999999
    max_x = -999999
    min_y = 999999
    max_y = -999999
    
    for txt, lx, ly, lfs in lines:
        w = len(txt) * 0.60 * lfs
        if anchor == 'middle':
            x0 = lx - w / 2.0
            x1 = lx + w / 2.0
        elif anchor == 'end':
            x0 = lx - w
            x1 = lx
        else: # start
            x0 = lx
            x1 = lx + w
            
        y0 = ly - lfs * 0.85
        y1 = ly + lfs * 0.20
        
        min_x = min(min_x, x0)
        max_x = max(max_x, x1)
        min_y = min(min_y, y0)
        max_y = max(max_y, y1)
        
    return min_x, min_y, max_x, max_y, lines

print("\nChecking all text bounding boxes against canvas margin (40px):")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x0, y0, x1, y1, lines = get_tspan_bounds(elem)
    txt = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    print(f"  [{x0:6.1f}, {y0:6.1f}] -> [{x1:6.1f}, {y1:6.1f}]: '{txt[:35]}...'")
    assert x0 >= 40.0, f"Text '{txt}' left {x0} < 40!"
    assert x1 <= 1560.0, f"Text '{txt}' right {x1} > 1560!"
    assert y0 >= 40.0, f"Text '{txt}' top {y0} < 40!"
    assert y1 <= 1130.0, f"Text '{txt}' bottom {y1} > 1130!"

print("\nALL V2 AUDIT CHECKS PASSED PERFECTLY!")
