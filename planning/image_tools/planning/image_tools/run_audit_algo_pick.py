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
        "Pick the algorithm by the unit of work it counts",
        "Short stateless equal requests",
        "round robin or weighted round robin",
        "ignores request cost and backend load",
        "Long-lived connections or variable-length requests",
        "least connections",
        "counts connections, not work; needs shared state across LB instances",
        "HTTP or gRPC requests",
        "least outstanding requests",
        "same, request-granular",
        "Heterogeneous backends",
        "least response time, EWMA, peak-EWMA",
        "needs measurement; can oscillate (herding)",
        "Large pools with imperfect load info",
        "power of two random choices",
        "needs load info per backend",
        "Session affinity or cache locality",
        "source, URL or header hash",
        "remaps most keys when N changes",
        "Caches, sticky sessions, sharded stores",
        "consistent hashing (ring, rendezvous, jump hash)",
        "load imbalance; virtual nodes help; hot keys",
        "L4 LBs behind ECMP",
        "Maglev hashing",
        "table rebuild cost; small disruption on change",
        "Cost and latency",
        "locality or zone-aware",
        "capacity imbalance across zones",
        "DR and spillover",
        "priority or failover groups",
        "cold backups",
        "LLM inference",
        "load-aware custom: GPU, queue, KV-cache",
        "needs telemetry; careful staleness handling",
        "Four principles",
        "choose the metric that represents work: connections, requests, tokens and GPU-seconds differ",
        "many LB instances each doing local least connections herd onto the same backend, like drivers following one satnav to one empty car park; a randomised pick breaks it up",
        "hash affinity serves cache locality and state but accepts uneven load: plan for reshuffling with consistent or resilient hashing",
        "slow start ramps up the weight of a new or recovered backend while its JIT, caches and GPU warm up",
        "Name the unit of work first, then pick the algorithm that counts it"
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
    lines_arr = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths_arr = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines_arr) + len(paths_arr)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 22, f"Expected exactly 22 arrows, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in svg_str
    assert "#303a36" in svg_str
    assert "#207448" in svg_str
    assert "#e8f1ea" in svg_str
    assert "#db8129" in svg_str
    print("\n8. All required colors present! (PASS)")

    print("\nALL AUDIT CHECKS PASSED PERFECTLY!")

if __name__ == "__main__":
    audit_svg("planning/image_tools/test_algo_pick.svg")
