#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

def audit_svg(svg_path):
    print(f"\n================ AUDITING {svg_path} ================")
    tree = ET.parse(svg_path)
    root = tree.getroot()
    raw = open(svg_path, 'r', encoding='utf-8').read()

    # 1. Structure
    children = list(root)
    t1 = children[0].tag.split('}')[-1]
    t2 = children[1].tag.split('}')[-1]
    assert t1 == 'title', f"First child is {t1}, not title"
    assert t2 == 'desc', f"Second child is {t2}, not desc"
    print("1. First children <title> and <desc>: PASS")

    # 2. Dimensions
    w = root.get('width')
    h = root.get('height')
    vb = root.get('viewBox').split()
    assert w == '1600', f"Width is {w}, not 1600"
    assert vb[0] == '0' and vb[1] == '0' and vb[2] == '1600'
    assert 900 <= float(vb[3]) <= 1200, f"Height {vb[3]} not in [900, 1200]"
    assert float(h) == float(vb[3]), f"Height {h} != viewBox {vb[3]}"
    print(f"2. Dimensions {w}x{h}, viewBox {root.get('viewBox')}: PASS")

    # 3. Text elements & font sizes
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

    print(f"3. All {len(text_elements)} text elements have font-size >= 24px: PASS")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Expected labels
    expected_labels = [
        "Three layers that limit database access",
        "app host",
        "unlisted host",
        "ufw allow tcp 5432 from each app host",
        "limits the port at the firewall",
        "listen_addresses = localhost plus ansible_host",
        "limits the network interface",
        "pg_hba.conf host db_name db_user app host /32 scram-sha-256",
        "limits the client address",
        "PostgreSQL on db01",
        "passes all three",
        "stopped"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels against {len(text_elements)} found:")
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        ok = (cnt == 1)
        if not ok:
            all_ok = False
        print(f"   [{'OK' if ok else 'FAIL'}] count={cnt}: '{exp}'")

    assert all_ok, "Some expected labels failed count == 1 check!"
    assert len(found_texts) == len(expected_labels), f"Text count {len(found_texts)} != {len(expected_labels)}"
    print("   PASS: All expected labels found exactly once, text count matches")

    # 5. Extras check
    extras = [t for t in found_texts if t not in expected_labels]
    print(f"\n5. Extras count: {len(extras)}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    print("   PASS: No unrequested extra text elements")

    # 6. Forbidden words check
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    found_forbidden = []
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            if f in words:
                found_forbidden.append((f, t))
    assert len(found_forbidden) == 0, f"Forbidden words found: {found_forbidden}"
    print("\n6. Forbidden words check: PASS (zero forbidden style words)")

    # 7. Colors check
    assert "#f5f8f5" in raw, "Missing light background #f5f8f5"
    assert "#303a36" in raw, "Missing dark text #303a36"
    assert "#207448" in raw, "Missing main green #207448"
    assert "#e8f1ea" in raw, "Missing light green panels #e8f1ea"
    assert "#db8129" in raw, "Missing accent orange #db8129"
    orange_matches = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"\n7. Colors check: PASS. Orange #db8129 occurrences: {len(orange_matches)}")
    assert 1 <= len(orange_matches) <= 8, f"Too many or too few orange occurrences: {len(orange_matches)}"

    # 8. Arrows check
    lines_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if e.attrib.get('marker-end')]
    paths_with_marker = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if e.attrib.get('marker-end')]
    total_arrows = len(lines_with_marker) + len(paths_with_marker)
    print(f"\n8. Total arrows with marker-end: {total_arrows}")
    assert total_arrows == 2, f"Expected exactly 2 arrows, got {total_arrows}"
    print("   PASS: Exactly 2 arrows with marker-end")

    # 9. Strict paddings check
    print("\n9. Checking strict text paddings in enclosing rects...")
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 0 and rh > 0 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))

    all_pad_ok = True
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', 24))
        ff = el.attrib.get('font-family', 'sans-serif')
        anchor = el.attrib.get('text-anchor', 'start')
        rate = 0.62 if 'monospace' in ff else 0.60

        txt = "".join(el.itertext()).strip()
        txt = re.sub(r'\s+', ' ', txt)
        if not txt or txt == "Three layers that limit database access":
            continue

        tx = float(el.attrib.get('x', 0))
        ty = float(el.attrib.get('y', 0))
        tw = len(txt) * rate * fs
        if anchor == 'middle':
            tl = tx - tw / 2
            tr = tx + tw / 2
        elif anchor == 'end':
            tl = tx - tw
            tr = tx
        else:
            tl = tx
            tr = tx + tw
        ttop = ty - fs * 0.8
        tbot = ty

        containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
        assert containing, f"Text '{txt}' not contained in any rect!"
        containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
        best = containing[0]
        pad_l = tl - best[0]
        pad_r = best[2] - tr
        pad_t = ttop - best[1]
        pad_b = best[3] - tbot
        print(f"   '{txt[:35]}...' in rect ({best[0]:.0f},{best[1]:.0f},{best[2]:.0f},{best[3]:.0f}): L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
        if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
            print(f"   [FAIL] Padding < 16px in '{txt}'!")
            all_pad_ok = False

    assert all_pad_ok, "Some paddings failed < 16px check!"
    print("   PASS: All text elements have >= 16px padding on all 4 sides!")

    print("\n================ ALL CHECKS PASSED PERFECTLY ================")

audit_svg("test_three_db.svg")
