#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

def audit(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    tag1 = children[0].tag.split('}')[-1]
    tag2 = children[1].tag.split('}')[-1]
    print(f"1. First children: <{tag1}>, <{tag2}>")
    assert tag1 == 'title', f"First child must be title, got {tag1}"
    assert tag2 == 'desc', f"Second child must be desc, got {tag2}"

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    print(f"2. Dimensions: width={width}, height={height}, viewBox='{viewBox}'")
    assert width == "1600", f"width must be 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

    # 3. Check font-size >= 24 on all text and tspans
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text '{full_text}'"
        size = float(fs)
        assert size >= 24, f"Text '{full_text}' font-size {size} < 24!"
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, size))

    print(f"3. Total text elements: {len(text_elements)} (all font-sizes >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "What the client sees when a connection fails, and where to look",
        "Error the client sees",
        "What actually happened on the wire",
        "Where to look",
        "Connection refused (ECONNREFUSED)",
        "a RST came back: host reachable, nobody listening on that port, or a firewall using reject --tcp-reset",
        "the listener: somebody was home and said no",
        "Connection timed out (ETIMEDOUT)",
        "no reply to the SYNs, retried with exponential backoff 1, 2, 4 seconds and so on; tcp_syn_retries=6 gives about 127 seconds",
        "route and firewall or security group, host down: nobody answered the door at all",
        "No route to host or Network is unreachable",
        "ICMP unreachable from a router, or no local route",
        "the routing table (chapter 2.5)",
        "Connection reset by peer",
        "a RST during an established connection",
        "peer crashed, app closed with unread data, firewall or NAT state expired, load balancer idle timeout",
        "SYN retried",
        "SYN then RST",
        "A refusal means the host answered, so look at the listener; a timeout means the SYNs never got a reply, so look at the route and firewall"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
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

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'callout']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n5. No forbidden words found! (PASS)")

    # 6. Colors present
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    for color in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert color in svg_str, f"Missing color {color}"
    print("\n6. All required colors present! (PASS)")

    # 7. Check orange count
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 8. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n8. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 5, f"Expected exactly 5 arrows, got {total_arrows}"

    print("\n================== ALL AUDIT CHECKS PASSED PERFECTLY! ==================")

if __name__ == '__main__':
    audit("test_connection_fails.svg")
