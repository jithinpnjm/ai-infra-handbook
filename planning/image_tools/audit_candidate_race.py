import xml.etree.ElementTree as ET
import re

def audit(svg_path):
    print("="*20, f"AUDITING {svg_path}", "="*20)
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = open(svg_path).read()

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

    # 3. Font-size >= 24 on all text and tspans
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
        "How parallel A and AAAA queries race in conntrack and cause a 5-second stall",
        "pod",
        "glibc resolver",
        "one UDP socket",
        "both to the same source IP and port",
        "A query",
        "AAAA query",
        "netfilter",
        "conntrack",
        "two side-by-side insertion slots",
        "kube-proxy DNAT to a CoreDNS pod chosen by KUBE-SVC",
        "the two packets may go to different CoreDNS pods",
        "the second insertion collides with the first",
        "insert_failed",
        "the packet is silently dropped",
        "waits for default 5 s timeout, then retries",
        "NodeLocal DNSCache removes the DNAT with a NOTRACK note",
        "single-request-reopen separates the two queries",
        "TCP to DNS avoids the UDP path",
        "two parallel queries on one socket can collide in the kernel, and the lost packet costs a timeout."
    ]

    step_numbers = ["1", "2", "3", "4"]

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

    # Check step numbers
    for sn in step_numbers:
        cnt = found_texts.count(sn)
        assert cnt == 1, f"Step number '{sn}' count {cnt} != 1!"
        print(f"   [OK] step number '{sn}' present once")

    # Check extras
    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    print(f"\n5. Extras count: {len(extras)}")
    if extras:
        print("   Unexpected extras:", extras)
    assert len(extras) == 0, f"Unexpected extras: {extras}"
    assert len(found_texts) == len(expected_labels) + len(step_numbers), f"Total text elements {len(found_texts)} != {len(expected_labels) + len(step_numbers)}"

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

    # 7. Orange usage - ONLY on the collision X!
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"\n8. Orange #db8129 occurrences: {len(orange_matches)}")
    # Verify orange is ONLY in collision-x
    root_clean = ET.fromstring(raw)
    collision_x = root_clean.find('.//*[@id="collision-x"]')
    assert collision_x is not None, "collision-x element missing"
    collision_x_raw = ET.tostring(collision_x, encoding='unicode')
    collision_orange_count = len(re.findall(r'#db8129', collision_x_raw, re.IGNORECASE))
    assert collision_orange_count == len(orange_matches), f"Orange used outside collision-x! Found in x: {collision_orange_count}, total: {len(orange_matches)}"
    print("   Orange used STRICTLY and ONLY on the collision X. PASS!")

    # 8. External resources
    assert not any(el.tag.endswith('image') for el in root.iter()), "No <image> allowed"
    assert not any(el.tag.endswith('script') for el in root.iter()), "No <script> allowed"
    clean_raw = raw.replace("http://www.w3.org/2000/svg", "")
    assert "http://" not in clean_raw and "https://" not in clean_raw, "No external URLs"
    print("\n9. External resources check: PASS!")

    print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY ===")

audit("candidate_conntrack_race.svg")
