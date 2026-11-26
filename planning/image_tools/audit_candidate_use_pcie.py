import xml.etree.ElementTree as ET
import re
import sys

def audit(svg_path):
    print(f"Auditing {svg_path}...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. First child: <{first_tag}>, Second child: <{second_tag}>")
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"

    title_text = "".join(children[0].itertext()).strip()
    assert title_text == "The USE method applied to a NIC and its PCIe slot", f"Unexpected title text: '{title_text}'"

    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"Expected width 1600, got {width}"
    assert viewBox.startswith("0 0 1600 "), f"viewBox must start with '0 0 1600 ', got {viewBox}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"Height {vb_parts[3]} outside 900-1200 range"
    assert int(height) == int(vb_parts[3]), f"height {height} != viewBox height {vb_parts[3]}"

    # 3. Font-size check >= 24
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

    # 4. Expected labels check
    expected_labels = [
        "The USE method applied to a NIC and its PCIe slot",
        "Utilization: the busy fraction = throughput divided by the negotiated speed, counting all headers; with cloud caps use the limit the cloud imposes",
        "Saturation: queueing: qdisc backlog and drops, application threads blocked on send, TCP retransmits as a symptom, NIC ring overruns",
        "Errors: on RX bad checksums and frames too short or too long; on TX late collisions and carrier errors; check errors first",
        "PCIe Gen4 x16: about 252 Gb/s usable; one 400G NIC in that slot reaches only 252 / 400 = 0.63, about 63 percent of line rate",
        "PCIe Gen5 x16: about 504 Gb/s, enough for a 400G port",
        "apply the same method to the NIC controller and the bus: sum the port throughputs and compare the total with the PCIe bandwidth; and to the kernel stack: softirq CPU, memory for socket buffers, the conntrack table",
        "USE report for a 400G NIC: Gen4 x16 252 Gb/s versus Gen5 x16 504 Gb/s",
        "A slot can cap a NIC before the link does"
    ]

    all_found = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(all_found)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = all_found.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp[:60]}...'")

    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in all_found if t not in expected_labels]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in all_found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n6. Forbidden words check: PASS! (None found)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n7. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 6, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n8. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected 0 arrows, got {total_arrows}"

    # 8. Check colors present
    for c in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert c in svg_str, f"Missing color {c} in SVG"
    print("\n9. All palette colors present: PASS!")

    print("\nALL 9 STRICT AUDIT CHECKS PASSED PERFECTLY!")

audit("candidate.svg")
