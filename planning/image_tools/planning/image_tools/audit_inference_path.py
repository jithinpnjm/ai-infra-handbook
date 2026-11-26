import xml.etree.ElementTree as ET
import re
import pathlib

svg_file = "inference_path.svg"
tree = ET.parse(svg_file)
root = tree.getroot()

print("=== 1. First children check ===")
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

print("\n=== 2. Dimensions check ===")
width = root.get('width')
viewBox = root.get('viewBox')
height = root.get('height')
print(f"width={width}, height={height}, viewBox={viewBox}")
assert width == "1600"
assert viewBox.startswith("0 0 1600 ")
vb_parts = [float(x) for x in viewBox.split()]
assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
assert 900 <= vb_parts[3] <= 1200
assert int(height) == int(vb_parts[3])

print("\n=== 3. Text font-size >= 24 check ===")
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

print(f"Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

print("\n=== 4. Expected labels check ===")
expected_labels = [
    "The whiteboard path for an inference service, and the metrics to watch on it",
    "Client",
    "anycast or ECMP to a fleet of L4 and L7 gateways (BGP VIP, BFD)",
    "TLS termination and L7 routing with per-request, per-tenant policy",
    "load- and cache-aware endpoint picker",
    "inference pods with readiness, drain and GPU health integration",
    "where pinning happens at L4",
    "L7 or client-side balancing fixes it",
    "Watch per backend",
    "request counts",
    "in-flight requests",
    "queue time",
    "error and retry rates",
    "TTFT and ITL percentiles",
    "ejection events",
    "hot-backend alerts",
    "trace each request across the gateway, the router and the engine",
    "disable proxy buffering for SSE",
    "read and stream-idle timeouts above the maximum generation time",
    "heartbeats",
    "avoid Connection: close",
    "HTTP/2 end to end where possible",
    "measure time-to-first-token (TTFT) and inter-token latency at the proxy with $upstream_response_time or Envoy stats",
    "BGP convergence sets how quickly a failed node's traffic moves; BFD detects in under a second; resilient or consistent hashing in the router moves only the failed node's flows; announce the VIP only while the node can serve; a route change can move a flow to a different site, which breaks long-lived TCP; fabric ECMP caveats: elephant flows, RoCE varies UDP source ports per QP, tunnels need inner-header hashing, adaptive routing reacts to load",
    "Decide your failover budget first"
]

all_found = [t for t, fs in text_elements]
all_ok = True
for exp in expected_labels:
    cnt = all_found.count(exp)
    ok = (cnt == 1)
    if not ok:
        all_ok = False
    print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:50]}...'")

assert all_ok, "Some expected labels failed count == 1 check!"

extras = [t for t in all_found if t not in expected_labels]
print(f"\nExtras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

print("\n=== 5. Forbidden words check ===")
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in all_found:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("No forbidden words found! (PASS)")

print("\n=== 6. Orange color check ===")
svg_str = pathlib.Path(svg_file).read_text(encoding='utf-8')
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

print("\n=== 7. Arrows check ===")
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"Total arrows with marker-end: {total_arrows}")
assert total_arrows == 4, f"Expected exactly 4 arrows, got {total_arrows}"

print("\n=== 8. Color palette check ===")
for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
    assert c in svg_str, f"Missing color {c} in SVG"

print("All required colors present! (PASS)")

print("\nALL AUDIT CHECKS PASSED PERFECTLY!")
