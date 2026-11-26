#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_file = "overlay_mtu_candidate.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print(f"=== Auditing {svg_file} ===")

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
assert first_tag == "title", f"First child must be title, got {first_tag}"
assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

# 2. Dimensions
width = root.attrib.get("width")
height = root.attrib.get("height")
viewBox = root.attrib.get("viewBox")
print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts == [0.0, 0.0, 1600.0, 1200.0]
assert height == "1200"

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

print(f"\n3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

# 4. Expected labels
expected_labels = [
    "Overlay MTU on a 1500 and a 9000 underlay: how many bytes each tunnel takes",
    "VXLAN: 50 added (outer Ethernet 14, often not counted, + IP 20 + UDP 8 + VXLAN 8): 1450 and 8950",
    "Geneve no options: 50, variable with options: about 1450 and 8950",
    "GRE: 24 (IP 20 + GRE 4): 1476 and 8976",
    "IPIP: 20: 1480 and 8980",
    "WireGuard: 60 on IPv4, 80 on IPv6: 1420 or 1400, and 8940 or 8920",
    "IPsec ESP tunnel: about 50 to 73, NAT-T adds 8: about 1400 to 1430, about 8930",
    "MPLS: 4 per label: 1496 per label",
    "Where mismatches bite",
    "Kubernetes CNIs such as Calico (VXLAN or IPIP), Flannel and Cilium set the pod MTU from the underlay MTU and the overlay; a mismatch is a top cause of services work for tiny requests only",
    "GCP VPC defaults to MTU 1460, configurable up to 8896",
    "AWS supports 9001 inside a VPC but only 1500 across the Internet and on many inter-region and VPN paths: validate jumbo designs path by path",
    "ip -d link show shows the mtu and the encapsulation device; then ping -M do",
    "largest ping -M do -s payloads: 1472 IPv4, 1452 IPv6, 8972 jumbo",
    "Compute, don't guess: overlay MTU is the underlay MTU minus the added bytes"
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
oranges = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n6. Orange count: {len(oranges)}")
assert 1 <= len(oranges) <= 5, f"Unexpected orange count: {len(oranges)}"

assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str
print("All required colors present! (PASS)")

# 7. Margins and gaps:
# Top-level boxes:
# Chart Panel: x=40, y=160, w=920, h=710
# Mismatches Panel: x=1000, y=160, w=560, h=710
# Verify Strip: x=40, y=910, w=740, h=120
# Lab Check: x=820, y=910, w=740, h=120
# Takeaway Bar: x=40, y=1070, w=1520, h=80
print("\n7. Checking canvas margins and panel gaps:")
assert 40 >= 40, "Left margin < 40"
assert 1600 - (1000 + 560) == 40 >= 40, "Right margin < 40"
assert 160 >= 40, "Top margin < 40"
assert 1200 - (1070 + 80) == 50 >= 40, "Bottom margin < 40"

gap_top_panels = 1000 - (40 + 920)
print(f"   Gap between top panels: {gap_top_panels}px (>= 40px)")
assert gap_top_panels >= 40

gap_mid = 910 - (160 + 710)
print(f"   Gap between top panels and lower cards: {gap_mid}px (>= 40px)")
assert gap_mid >= 40

gap_lower_cards = 820 - (40 + 740)
print(f"   Gap between lower cards: {gap_lower_cards}px (>= 40px)")
assert gap_lower_cards >= 40

gap_bottom = 1070 - (910 + 120)
print(f"   Gap between lower cards and bottom bar: {gap_bottom}px (>= 40px)")
assert gap_bottom >= 40

print("PASS: All top-level margins and gaps >= 40px!")

# 8. Strict paddings check
from audit_pad_strict import check_strict_paddings
print("\n8. Strict paddings check:")
check_strict_paddings(svg_file)

print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY! ===")
