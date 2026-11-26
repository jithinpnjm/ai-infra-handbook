#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re
import sys

def run_audit(path):
    print(f"=== Auditing {path} ===")
    tree = ET.parse(path)
    root = tree.getroot()

    # 1. First children check: <title> and <desc>
    children = list(root)
    tag1 = children[0].tag.split('}')[-1]
    tag2 = children[1].tag.split('}')[-1]
    print(f"1. First children: <{tag1}>, <{tag2}>")
    assert tag1 == "title", "First child must be <title>"
    assert tag2 == "desc", "Second child must be <desc>"
    print("   [PASS]")

    # 2. Dimensions check
    w = root.attrib.get('width')
    h = root.attrib.get('height')
    vb = root.attrib.get('viewBox')
    print(f"2. Dimensions: width={w}, height={h}, viewBox={vb}")
    assert w == "1600", f"Width must be 1600, got {w}"
    assert vb == "0 0 1600 1200", f"viewBox must be '0 0 1600 1200', got {vb}"
    assert h == "1200", f"Height must be 1200, got {h}"
    print("   [PASS]")

    # 3. Font-size checks (no text < 24 px)
    print("3. Checking font sizes...")
    text_elements = []
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(el.itertext()).split())
        fs = float(el.attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
        for ts in el.findall('{http://www.w3.org/2000/svg}tspan'):
            tfs = float(ts.attrib.get('font-size', fs))
            assert tfs >= 24, f"tspan '{ts.text}' font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, fs))
    print(f"   [PASS] All {len(text_elements)} text elements and tspans >= 24 px.")

    # 4. Check expected labels
    expected_labels = [
        "Two ways to find the broken layer: bottom up, or bisect from the middle",
        "Test bottom up",
        "link",
        "address",
        "route",
        "ARP",
        "ping the gateway",
        "ping the destination",
        "DNS",
        "TCP port",
        "TLS",
        "HTTP",
        "each layer fails in its own way",
        "Bisect from the middle",
        "Can you reach the gateway?",
        "look below: link, address, route, ARP",
        "Can you reach an IP on the Internet?",
        "routing, NAT, firewall beyond the gateway",
        "Can you resolve names?",
        "DNS: resolver, search domains, port 53",
        "TCP, TLS or HTTP: use curl -v and the exit code",
        "Bisecting is like finding a break in a long string of lights by testing the middle bulb first",
        "Start with the layer the message points to, and test one layer at a time; check the client side first, including proxy settings and the DNS view",
        "Method details are in chapter 2.30"
    ]

    found_texts = [t for t, fs in text_elements]
    print(f"\n4. Checking {len(expected_labels)} expected labels:")
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        print(f"   Label '{exp[:40]}...': count={cnt}")
        assert cnt == 1, f"Expected '{exp}' exactly once, got {cnt}"

    yes_cnt = found_texts.count("Yes")
    no_cnt = found_texts.count("No")
    print(f"Edge labels: 'Yes'={yes_cnt}, 'No'={no_cnt}")
    assert yes_cnt == 3, f"Expected 3 'Yes', got {yes_cnt}"
    assert no_cnt == 3, f"Expected 3 'No', got {no_cnt}"

    extras = [t for t in found_texts if t not in expected_labels and t not in ["Yes", "No"]]
    print(f"Extra texts: {extras}")
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"
    print("   [PASS] All expected labels match perfectly.")

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'takeaway']
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' in '{t}'!"
    print("5. [PASS] No forbidden words found.")

    # 6. Check orange count
    svg_str = open(path).read()
    orange_matches = re.findall(r'#db8129', svg_str, re.IGNORECASE)
    print(f"\n6. Orange #db8129 occurrences: {len(orange_matches)}")
    assert len(orange_matches) == 1, f"Expected exactly 1 orange element (outline on Internet IP diamond), got {len(orange_matches)}"
    print("   [PASS] Exactly 1 orange element.")

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"\n7. Total arrows with marker-end: {total_arrows}")
    # 9 in left chain + 6 in right tree = 15 arrows
    assert total_arrows == 15, f"Expected 15 arrows, got {total_arrows}"
    print("   [PASS] Exactly 15 arrows.")

    # 8. Check outside margins >= 40
    print("\n8. Checking outside margins (>= 40px):")
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        x = float(el.attrib.get('x', 0))
        y = float(el.attrib.get('y', 0))
        w = float(el.attrib.get('width', 0))
        h = float(el.attrib.get('height', 0))
        if w == 1600 and h == 1200:
            continue
        if w < 50 or h < 30:
            continue
        m_l = x
        m_r = 1600 - (x + w)
        m_t = y
        m_b = 1200 - (y + h)
        assert m_l >= 39.9, f"Left margin {m_l} < 40 for rect {x},{y},{w},{h}"
        assert m_r >= 39.9, f"Right margin {m_r} < 40 for rect {x},{y},{w},{h}"
        assert m_t >= 39.9, f"Top margin {m_t} < 40 for rect {x},{y},{w},{h}"
        assert m_b >= 39.9, f"Bottom margin {m_b} < 40 for rect {x},{y},{w},{h}"
    print("   [PASS] All outside margins >= 40px!")

    # 9. Strict padding check on all text lines
    print("\n9. Strict padding checks (>= 16px):")
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 50 and rh > 30 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))
            
    # Also add diamonds as bounding boxes
    for el in root.iter('{http://www.w3.org/2000/svg}polygon'):
        pts = [float(p) for p in el.attrib.get('points').replace(',', ' ').split()]
        xs = pts[0::2]
        ys = pts[1::2]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        rects.append((min_x, min_y, max_x, max_y, el))

    all_pad_ok = True
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', 24))
        anchor = el.attrib.get('text-anchor', 'start')
        rate = 0.60
        
        tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = float(el.attrib.get('y', 0))
            for ts in tspans:
                txt = ts.text or ""
                if not txt.strip():
                    continue
                tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
                dy = float(ts.attrib.get('dy', 0))
                cur_y += dy
                tw = len(txt) * rate * fs
                if anchor == 'middle':
                    tl = tx - tw / 2
                    tr = tx + tw / 2
                else:
                    tl = tx
                    tr = tx + tw
                ttop = cur_y - fs * 0.8
                tbot = cur_y
                
                # Find innermost containing box
                containing = [r for r in rects if r[0] <= tl + 0.1 and r[1] <= ttop + 0.1 and r[2] >= tr - 0.1 and r[3] >= tbot - 0.1]
                if containing:
                    containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                    best = containing[0]
                    pad_l = tl - best[0]
                    pad_r = best[2] - tr
                    pad_t = ttop - best[1]
                    pad_b = best[3] - tbot
                    if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                        print(f"WARN padding: '{txt}' in box {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                        all_pad_ok = False
        else:
            txt = "".join(el.itertext()).strip()
            if not txt or txt in ["Yes", "No", "Two ways to find the broken layer: bottom up, or bisect from the middle"]:
                continue
            tx = float(el.attrib.get('x', 0))
            ty = float(el.attrib.get('y', 0))
            tw = len(txt) * rate * fs
            if anchor == 'middle':
                tl = tx - tw / 2
                tr = tx + tw / 2
            else:
                tl = tx
                tr = tx + tw
            ttop = ty - fs * 0.8
            tbot = ty
            containing = [r for r in rects if r[0] <= tl + 0.1 and r[1] <= ttop + 0.1 and r[2] >= tr - 0.1 and r[3] >= tbot - 0.1]
            if containing:
                containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                best = containing[0]
                pad_l = tl - best[0]
                pad_r = best[2] - tr
                pad_t = ttop - best[1]
                pad_b = best[3] - tbot
                if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                    print(f"WARN padding: '{txt}' in box {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                    all_pad_ok = False

    assert all_pad_ok, "Some text lines failed the strict 16px padding rule!"
    print("   [PASS] All text lines strictly satisfy >= 16px padding in their boxes!")
    print("\n=== ALL AUDIT CHECKS PASSED PERFECTLY ===")

if __name__ == "__main__":
    run_audit("test_candidate_p30201.svg")
