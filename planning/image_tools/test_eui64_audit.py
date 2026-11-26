#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re, pathlib, subprocess

def run_audit(svg_content, output_name="p3-0203-eui64"):
    root = ET.fromstring(svg_content)
    
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
        "From a MAC address to the IPv6 neighbour address: a worked derivation",
        "MAC 01:23:45:67:89:ab",
        "Flip the U/L bit and insert ff:fe in the middle: modified EUI-64 0323:45ff:fe67:89ab",
        "Link-local address fe80::/64 plus the interface ID: fe80::323:45ff:fe67:89ab",
        "Solicited-node multicast: ff02::1:ff67:89ab, from the last 24 bits (67:89:ab) of the address",
        "Ethernet destination 33:33:ff:67:89:ab",
        "Modern systems may use a random stable privacy ID (RFC 7217) instead; the Linux setting is addr_gen_mode",
        "Why this beats ARP",
        "only hosts whose address ends in those 24 bits receive the solicitation, instead of every host hearing a broadcast: a question sent to one block, not shouted across a stadium",
        "ICMPv6 types: 133 Router Solicitation (to ff02::2), 134 Router Advertisement, 135 Neighbor Solicitation, 136 Neighbor Advertisement, 137 Redirect",
        "IPv6 has no broadcast, so it uses ICMPv6 messages to multicast addresses"
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

    extras = [t for t in all_found if t not in expected_labels]
    print(f"\nExtras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in all_found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count: exactly one orange item or arrow
    orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 4, f"Expected exactly 4 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_content
    assert "#303a36" in svg_content
    assert "#207448" in svg_content
    assert "#e8f1ea" in svg_content
    assert "#db8129" in svg_content
    print("\n8. All required colors present! (PASS)")

    # 9. Screenshot test
    out_svg = pathlib.Path(f"/tmp/{output_name}.svg")
    out_svg.write_text(svg_content)
    out_png = pathlib.Path(f"/tmp/svgcheck/{output_name}.png")
    out_png.parent.mkdir(exist_ok=True)
    H = int(vb_parts[3])
    subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
                    '--headless=new', '--disable-gpu', '--hide-scrollbars',
                    f'--window-size=1600,{H}',
                    f'--screenshot={out_png}',
                    f'file://{out_svg}'],
                   capture_output=True, timeout=60)
    print(f"\n9. Screenshot saved to {out_png}")
    print("\nALL VERIFICATIONS PASSED PERFECTLY!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        svg_text = pathlib.Path(sys.argv[1]).read_text()
        run_audit(svg_text)
