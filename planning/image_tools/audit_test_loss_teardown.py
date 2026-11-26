#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, pathlib, subprocess

svg_path = "test_loss_teardown_candidate.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# 1. Structure
children = list(root)
first_tag = children[0].tag.split('}')[-1]
second_tag = children[1].tag.split('}')[-1]
print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
assert first_tag == 'title', f"First child must be title, got {first_tag}"
assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
print("   [PASS] <title> and <desc> are the first children.")

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
print("   [PASS] Dimensions and viewBox are valid.")

# 3. Check font-size >= 24 on all text and tspans
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
    "Transfer, loss recovery and teardown: why TIME_WAIT fills up",
    "Receiving the body",
    "segments arrive shuffled",
    "socket receive buffer",
    "sends ACKs, often one for every second segment, with delayed ACK timers",
    "advertises its window: the amount of data it is ready to accept right now",
    "curl reads with recv",
    "Loss",
    "fast retransmit after three duplicate ACKs, or through SACK",
    "retransmission timeout fires",
    "congestion window collapses, then regrows",
    "Closing",
    "FIN, ACK exchange (or RST on abort)",
    "the side that closes first holds the connection in TIME_WAIT for about 60 seconds on Linux",
    "stops late packets from corrupting a new connection that reuses the same 5-tuple",
    "Thousands of short connections can exhaust ephemeral ports (32768 to 60999) or fill the table with TIME_WAIT entries",
    "ss -s",
    "ss -tni dst 93.184.216.34 (rtt, cwnd, mss, retrans, bytes)",
    "If your service opens thousands of short connections, watch the TIME_WAIT count before you scale it up"
]

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
print("   [PASS] Every expected label appears exactly once.")

extras = [t for t in all_found if t not in expected_labels]
print(f"\n5. Extras count: {len(extras)}")
if extras:
    print("   Unexpected extras:", extras)
assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"
print("   [PASS] Exactly 0 extra texts.")

# 5. Check forbidden words
forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
for t in all_found:
    words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
    for f in forbidden:
        assert f not in words, f"Forbidden word '{f}' in '{t}'!"

print("\n6. [PASS] No forbidden words found in text.")

# 6. Check orange count
svg_str = pathlib.Path(svg_path).read_text()
orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"
print("   [PASS] Orange used only for warning card (count within 1-4).")

# 7. Check arrows count
lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
total_arrows = len(lines) + len(paths)
print(f"\n8. Total arrows with marker-end: {total_arrows}")
assert total_arrows >= 5, f"Expected at least 5 arrows, got {total_arrows}"
print(f"   [PASS] {total_arrows} arrows present.")

# 8. External check
assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
assert "http://" not in svg_str.replace("http://www.w3.org/2000/svg", ""), "No external URLs"
assert "https://" not in svg_str, "No external URLs"
print("\n9. [PASS] No external images, scripts or fonts.")

# Render with Chrome headless
d = pathlib.Path("/tmp/svgcheck")
d.mkdir(exist_ok=True)
png_path = d / "test_loss_teardown.png"
subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                '--headless=new', '--disable-gpu', '--hide-scrollbars',
                '--window-size=1600,1200',
                f'--screenshot={png_path}',
                f'file://{pathlib.Path(svg_path).resolve()}'],
               capture_output=True, timeout=30)
print(f"\nRendered screenshot: {png_path}")
print("ALL AUDIT CHECKS PASSED SUCCESSFULLY!")
