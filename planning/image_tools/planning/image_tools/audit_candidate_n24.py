#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

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
        "Spreading a flow across queues and cores",
        "A flow's addresses and ports are hashed (Toeplitz) to pick one queue, so each flow stays on one core, keeping packet order and cache.",
        "NIC with receive queues Q0 to Q3",
        "each with its own interrupt (IRQ)",
        "a different CPU core (core 0 to 3)",
        "RSS: hardware, NIC hashes to N receive queues (ethtool -l eth0)",
        "RPS: software, steers to other CPUs after the interrupt",
        "XPS: maps CPUs to TX queues, avoids lock contention and cross-NUMA transmit",
        "One core cannot process 100 Gb/s on its own",
        "mpstat -P ALL 1: is one core at 100%?"
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
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(all_found) == len(expected_labels), f"Text count {len(all_found)} != {len(expected_labels)}"

    # 6. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout']
    for t in all_found:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for w in forbidden:
            assert w not in words, f"Forbidden style word '{w}' in label: '{t}'"
    print("6. [PASS] No forbidden style words in any text!")

    # 7. Colors check
    with open(svg_path) as f:
        content = f.read()
    for col in ["#f5f8f5", "#303a36", "#207448", "#e8f1ea", "#db8129"]:
        assert col in content, f"Required color {col} not found in SVG!"
    print("7. [PASS] All required palette colors present!")

    # 8. Check arrows
    arrows = [e for e in root.iter() if 'marker-end' in e.attrib]
    print(f"8. Arrows found: {len(arrows)}")
    assert len(arrows) == 1, f"Expected exactly 1 arrow, got {len(arrows)}"
    print("8. [PASS] Exactly 1 arrow matching source connection!")

    print("\n==================== ALL CHECKS PASSED PERFECTLY! ====================")

if __name__ == '__main__':
    audit_svg('test_candidate_n24_rss.svg')
