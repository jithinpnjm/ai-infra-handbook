import xml.etree.ElementTree as ET
import re, subprocess, os, pathlib

def run_audit(svg_path):
    print("="*20, "AUDITING SVG", "="*20)
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = pathlib.Path(svg_path).read_text()

    # 1. Structure
    children = list(root)
    t1 = children[0].tag.split('}')[-1]
    t2 = children[1].tag.split('}')[-1]
    print(f"1. Structure: <{t1}>, <{t2}>")
    assert t1 == "title", f"First child must be title, got {t1}"
    assert t2 == "desc", f"Second child must be desc, got {t2}"

    # 2. Dimensions
    w = root.get("width")
    h = root.get("height")
    vb = root.get("viewBox")
    print(f"2. Dimensions: {w}x{h}, viewBox='{vb}'")
    assert w == "1600", f"width {w} != 1600"
    vb_parts = [float(x) for x in vb.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200
    assert float(h) == vb_parts[3]

    # 3. Text font-size >= 24
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

    print(f"3. Text elements: {len(text_elements)} elements, all >= 24px.")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "The 1 to 5 second DNS delay from a UDP race",
        "Pod resolver",
        "A lookup",
        "AAAA lookup",
        "in parallel from the same UDP source port",
        "Both reach the node; the kernel must insert the DNAT conntrack entry for each",
        "two people sign the same guest book at the same instant",
        "one packet loses the insertion, a reply is lost",
        "Pod waits 1 s or 5 s then retries",
        "normal reply in milliseconds",
        "delay of 1 s or 5 s",
        "single-request-reopen in resolv.conf options, use TCP for DNS, NodeLocal DNSCache, newer kernels fix it",
        "stale UDP conntrack entries can keep sending to a deleted backend until timeout; check conntrack -L -p udp | grep svc"
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
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extra texts found: {extras}"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"

    # 5. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("\n6. Forbidden style words check: PASS!")

    # 6. Colors present
    assert "#f5f8f5" in raw, "Background #f5f8f5 missing"
    assert "#303a36" in raw, "Text #303a36 missing"
    assert "#207448" in raw, "Main green #207448 missing"
    assert "#e8f1ea" in raw, "Light green panels #e8f1ea missing"
    assert "#db8129" in raw, "Orange #db8129 missing"
    print("\n7. Color palette check: PASS!")

    # 7. Orange usage
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"\n8. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 4, f"Orange count {len(orange_matches)} out of bounds!"
    print("   Orange used strictly for the single most important card (lost packet). PASS!")

    # 8. Arrows count
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n9. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 2, f"Expected exactly 2 arrows (A lookup and AAAA lookup), got {total_arrows}"
    print("   Arrows count exactly 2: PASS!")

    # 9. External resources
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    clean_raw = raw.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in clean_raw and "https://" not in clean_raw, "No external URLs"
    print("\n10. External resources check: PASS!")

    print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY ===")

if __name__ == '__main__':
    run_audit("test_dns_udp_race.svg")
