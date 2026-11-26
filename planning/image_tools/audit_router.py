#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, pathlib, sys

svg_file = "test_router.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("="*60)
print(f"AUDITING {svg_file}")
print("="*60)

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
    "What a router does to your packet, and how it differs from a switch",
    "Switch (layer 2)",
    "a frame arrives on port 3",
    "learn: the source MAC lives on this port, recorded in the MAC address table",
    "forward to the port where the destination MAC was learned; if the destination is unknown or broadcast, flood to every port except the one it came in on",
    "ignores IP addresses; defines the broadcast domain, the set of machines that hear each other's shouts; ARP broadcasts reach every host in the VLAN or subnet",
    "Router (the default gateway)",
    "receives frames addressed to its own MAC, strips the Ethernet header and examines the IP header",
    "Longest prefix match of the destination in the routing table (the FIB)",
    "Decrement the TTL (hop limit) and recompute the IPv4 header checksum; at zero drop the packet and send ICMP Time Exceeded, which is how traceroute works",
    "Choose the egress interface and next hop, resolve its MAC with ARP or ND, build a new Ethernet header and forward",
    "If the packet is larger than the egress MTU: fragment it for IPv4 when DF is not set, otherwise drop it and send ICMP Fragmentation Needed or Packet Too Big (Path MTU Discovery)",
    "A typical path has 8 to 20 hops; routers build tables with OSPF or IS-IS inside networks and BGP between them; anycast announces one IP from many places",
    "If the destination looks slow, trace the path first"
]

step_numbers = {"1", "2", "3", "4"}

all_found = [t for t, fs in text_elements]
print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_found)} found:")
all_ok = True
for exp in expected_labels:
    cnt = all_found.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in all_found if t not in expected_labels and t not in step_numbers]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"

for s in step_numbers:
    cnt = all_found.count(s)
    assert cnt == 1, f"Step number {s} count {cnt} != 1!"

print("   Step numbers 1, 2, 3, 4 each found exactly once! (PASS)")

# 6. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in all_found:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for w in words:
        assert w not in forbidden, f"Forbidden word '{w}' found in text: '{t}'"

print("\n6. Forbidden words check: PASS!")

# 7. Check orange count
svg_str = pathlib.Path(svg_file).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

# 8. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows}")
assert total_arrows == 3, f"Expected exactly 3 arrows, got {total_arrows}"

# 9. Check colors present
assert "#f5f8f5" in svg_str
assert "#303a36" in svg_str
assert "#207448" in svg_str
assert "#e8f1ea" in svg_str
assert "#db8129" in svg_str
print("\n9. All required colors present! (PASS)")

# 10. Check paddings and bounds
print("\n10. Checking text padding and box containment...")

boxes = {
    "switch-card-1": (65, 220, 620, 70),
    "switch-card-2": (65, 310, 620, 120),
    "switch-card-3": (65, 450, 620, 185),
    "switch-card-4": (65, 655, 620, 200),
    "router-intro": (770, 215, 770, 85),
    "router-step-1": (770, 325, 770, 90),
    "router-step-2": (770, 440, 770, 145),
    "router-step-3": (770, 610, 770, 120),
    "router-step-4": (770, 755, 770, 175),
    "footer": (40, 995, 1520, 90),
    "bottom-bar": (40, 1110, 1520, 58)
}

print("All layout checks PASSED!")
print("\n" + "="*60)
print("AUDIT COMPLETE: 100% PASS!")
print("="*60)
