#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
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
        "Eight rules that keep many servers acting as one",
        "one illusion of a giant computer",
        "1 Identical software state: same OS image, kernel patch level, GPU driver, NIC firmware",
        "2 Synchronized time and identity: chrony or NTP; same numeric UID and GID everywhere",
        "3 Predictable naming and networking: DNS, hosts, DHCP and PXE, out-of-band management network, compute fabric",
        "4 Uniform shared storage: same mount paths, enforced quotas",
        "5 Centralized scheduling and accounting: users never start work on compute nodes directly; scheduler places jobs, isolates them in cgroups, logs usage",
        "6 Comprehensive observability: node health, temperatures, power supplies, air conditioning, UPS, fabric symbol errors, GPU faults",
        "7 Repeatable provisioning: a replacement server boots into an identical state within minutes",
        "8 Spares and SLA discipline: on-site stock of key spares, vendor replacement SLAs",
        "clock drift of a few seconds makes ranks disagree and looks like an application bug",
        "one node with an older GPU driver runs slightly slower or different and nothing in the job log points to it; compare driver versions",
        "a different UID makes a user unable to read their own checkpoint"
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
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"

    print("\n5. No forbidden words found! (PASS)")

    # 6. Check orange count
    with open(svg_path, 'r', encoding='utf-8') as f:
        svg_str = f.read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Unexpected orange count: {len(orange_matches)}"

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 0, f"Expected exactly 0 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    # 9. Check text padding and bounds
    print("\n9. Checking text bounds & paddings...")
    # For every text element and its tspans, verify that it fits inside its containing box
    # Boxes:
    boxes = {
        "tile-1": (40, 115, 480, 215),
        "tile-2": (560, 115, 480, 215),
        "tile-3": (1080, 115, 480, 215),
        "tile-8": (40, 370, 480, 200),
        "center-node": (560, 370, 480, 200),
        "tile-4": (1080, 370, 480, 200),
        "tile-7": (40, 610, 480, 320),
        "tile-6": (560, 610, 480, 320),
        "tile-5": (1080, 610, 480, 320),
        "fail-1": (40, 970, 480, 190),
        "fail-2": (560, 970, 480, 190),
        "fail-3": (1080, 970, 480, 190),
    }

    for gid, (bx, by, bw, bh) in boxes.items():
        g = root.find(f".//*[@id='{gid}']")
        assert g is not None, f"Group {gid} not found"
        for text in g.findall('{http://www.w3.org/2000/svg}text'):
            base_fs = float(text.attrib.get('font-size', 24))
            tspans = text.findall('{http://www.w3.org/2000/svg}tspan')
            if not tspans:
                tspans = [text]
            for tsp in tspans:
                t = (tsp.text or "").strip()
                if not t: continue
                fs = float(tsp.attrib.get('font-size', base_fs))
                w = len(t) * 0.60 * fs
                anchor = tsp.attrib.get('text-anchor', text.attrib.get('text-anchor', 'start'))
                tx = float(tsp.attrib.get('x', text.attrib.get('x', 0)))
                ty = float(tsp.attrib.get('y', text.attrib.get('y', 0)))
                if anchor == 'middle':
                    x_start = tx - w / 2
                    x_end = tx + w / 2
                elif anchor == 'end':
                    x_start = tx - w
                    x_end = tx
                else:
                    x_start = tx
                    x_end = tx + w

                # Check horizontal padding >= 16px
                assert x_start >= bx + 16, f"Text '{t}' left padding {x_start - bx:.1f} < 16 in {gid}"
                assert x_end <= bx + bw - 16, f"Text '{t}' right padding {bx + bw - x_end:.1f} < 16 in {gid}"

                # Check vertical padding >= 16px
                # For y, baseline is ty. Top is ty - fs, bottom is ty + 0.25*fs
                top_y = ty - fs
                bot_y = ty + 0.25 * fs
                assert top_y >= by + 16, f"Text '{t}' top padding {top_y - by:.1f} < 16 in {gid}"
                assert bot_y <= by + bh - 16, f"Text '{t}' bot padding {by + bh - bot_y:.1f} < 16 in {gid}"

    print("All text elements have >= 16px padding on all sides! (PASS)")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg(sys.argv[1])
