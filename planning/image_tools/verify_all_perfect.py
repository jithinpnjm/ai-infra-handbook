import xml.etree.ElementTree as ET
import re
import subprocess
import pathlib

def test_full():
    svg_path = "service_path_candidate.svg"
    tree = ET.parse(svg_path)
    root = tree.getroot()

    # 1. Structure
    children = list(root)
    c0 = children[0].tag.split('}')[-1]
    c1 = children[1].tag.split('}')[-1]
    assert c0 == 'title', f"First child must be title, got {c0}"
    assert c1 == 'desc', f"Second child must be desc, got {c1}"
    print("1. <title> and <desc> are first children (PASS)")

    # 2. Dimensions
    width = root.get('width')
    height = root.get('height')
    viewBox = root.get('viewBox')
    assert width == "1600"
    vb = [float(x) for x in viewBox.split()]
    assert vb[0] == 0 and vb[1] == 0 and vb[2] == 1600
    assert 900 <= vb[3] <= 1200
    assert int(height) == int(vb[3])
    print(f"2. Dimensions: {width}x{height}, viewBox: {viewBox} (PASS)")

    # 3. Text font-size >= 24
    text_elems = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = elem.attrib.get('font-size')
        assert fs is not None, f"Missing font-size on text: {elem.text}"
        size = float(fs)
        assert size >= 24, f"Font size {size} < 24 on text: {elem.text}"
        full_text = " ".join("".join(elem.itertext()).split())
        text_elems.append((full_text, size))
        for tsp in elem.iter('{http://www.w3.org/2000/svg}tspan'):
            tfs = tsp.attrib.get('font-size')
            if tfs:
                assert float(tfs) >= 24, f"tspan font size {tfs} < 24 in '{full_text}'"

    print(f"3. All {len(text_elems)} text elements have font-size >= 24 px (PASS)")

    # 4. Expected labels
    expected_labels = [
        "When a Service fails, confirm in order",
        "read top to bottom",
        "the first failing rung is where to look",
        "Pod",
        "call the pod IP and pod port directly from another pod",
        "Service",
        "the Service exists, otherwise lookup fails with Name or service not known",
        "DNS",
        "short, namespaced and full names resolve",
        "Endpoints",
        "kubectl get endpointslices -l kubernetes.io/service-name=hostnames",
        "ENDPOINTS shows none means the Service selector does not match pod labels",
        "Ports",
        "Service port listed, targetPort correct, named port matched",
        "kube-proxy rules",
        "iptables-save grep hostnames, or ipvsadm -ln",
        "Conntrack",
        "table usage, since iptables Service load balancing depends on connection tracking",
        "Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack"
    ]
    step_numbers = {"1", "2", "3", "4", "5", "6", "7"}

    found_texts = [t for t, fs in text_elems]
    all_ok = True
    for exp in expected_labels:
        cnt = found_texts.count(exp)
        if cnt != 1:
            all_ok = False
            print(f"FAILED: count={cnt} for '{exp}'")
    assert all_ok, "Some expected labels failed count == 1 check!"

    extras = [t for t in found_texts if t not in expected_labels and t not in step_numbers]
    assert len(extras) == 0, f"Found unexpected extra text: {extras}"

    for s in step_numbers:
        cnt = found_texts.count(s)
        assert cnt == 1, f"Step number {s} count {cnt} != 1!"

    print("4. All labels and step numbers present exactly once! (PASS)")

    # 5. Check forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    found_forbidden = []
    for t in found_texts:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            if f in words:
                found_forbidden.append((f, t))
    assert len(found_forbidden) == 0, f"Forbidden words found: {found_forbidden}"
    print("5. No forbidden words! (PASS)")

    # 6. Check orange count
    raw = open(svg_path).read()
    oranges = re.findall(r'#db8129', raw, re.IGNORECASE)
    print(f"6. Orange #db8129 occurrences: {len(oranges)}")
    assert 1 <= len(oranges) <= 4

    # 7. Check arrows count
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"7. Arrows found: {total_arrows}")
    assert total_arrows == 1, f"Expected 1 arrow, got {total_arrows}"

    # 8. Check colors present
    assert "#f5f8f5" in raw
    assert "#303a36" in raw
    assert "#207448" in raw
    assert "#e8f1ea" in raw
    assert "#db8129" in raw
    print("8. All required colors present! (PASS)")

    # 9. Deep padding and card containment check using the standard formula
    cards = {
        "Small Box": (1190, 140, 370, 92),
        "Rung 1": (160, 140, 990, 92),
        "Rung 2": (160, 274, 1400, 92),
        "Rung 3": (160, 408, 1400, 92),
        "Rung 4": (160, 542, 780, 120),
        "Orange Callout": (980, 542, 580, 120),
        "Rung 5": (160, 704, 1400, 92),
        "Rung 6": (160, 838, 1400, 92),
        "Rung 7": (160, 972, 1400, 92),
        "Takeaway": (40, 1104, 1520, 56)
    }

    text_to_card = [
        ("Small Box", "the first failing rung is where to look"),
        ("Rung 1", "Pod"),
        ("Rung 1", "call the pod IP and pod port directly from another pod"),
        ("Rung 2", "Service"),
        ("Rung 2", "the Service exists, otherwise lookup fails with Name or service not known"),
        ("Rung 3", "DNS"),
        ("Rung 3", "short, namespaced and full names resolve"),
        ("Rung 4", "Endpoints"),
        ("Rung 4", "kubectl get endpointslices -l kubernetes.io/service-name=hostnames"),
        ("Orange Callout", "ENDPOINTS shows none means the Service selector does not match pod labels"),
        ("Rung 5", "Ports"),
        ("Rung 5", "Service port listed, targetPort correct, named port matched"),
        ("Rung 6", "kube-proxy rules"),
        ("Rung 6", "iptables-save grep hostnames, or ipvsadm -ln"),
        ("Rung 7", "Conntrack"),
        ("Rung 7", "table usage, since iptables Service load balancing depends on connection tracking"),
        ("Takeaway", "Pod, Service, DNS, endpoints, ports, kube-proxy rules, then conntrack")
    ]

    all_card_ok = True
    for card_id, full_txt in text_to_card:
        cx, cy, cw, ch = cards[card_id]
        matched = None
        for elem in root.findall('.//{http://www.w3.org/2000/svg}text'):
            txt = " ".join("".join(elem.itertext()).split())
            if txt == full_txt:
                matched = elem
                break
        assert matched is not None, f"Could not find text for {card_id}: {full_txt}"

        tspans = matched.findall('{http://www.w3.org/2000/svg}tspan')
        base_x = float(matched.attrib.get('x', 0))
        base_y = float(matched.attrib.get('y', 0))
        base_fs = float(matched.attrib.get('font-size', 24))
        base_fam = matched.attrib.get('font-family', 'sans-serif')
        anchor = matched.attrib.get('text-anchor', 'start')

        if not tspans:
            lines = [(full_txt, base_x, base_y, base_fs, base_fam, anchor)]
        else:
            lines = []
            cur_y = base_y
            for tsp in tspans:
                txt = tsp.text or ""
                tx = float(tsp.attrib.get('x', base_x))
                dy = float(tsp.attrib.get('dy', 0))
                cur_y += dy
                tfs = float(tsp.attrib.get('font-size', base_fs))
                tfam = tsp.attrib.get('font-family', base_fam)
                tanch = tsp.attrib.get('text-anchor', anchor)
                lines.append((txt.strip(), tx, cur_y, tfs, tfam, tanch))

        for l_idx, (txt, lx, ly, lfs, lfam, lanch) in enumerate(lines):
            rate = 0.62 if 'mono' in lfam else 0.60
            w = len(txt) * lfs * rate
            if lanch == 'middle':
                xmin = lx - w/2
                xmax = lx + w/2
            else:
                xmin = lx
                xmax = lx + w
            ytop = ly - lfs * 0.8
            ybot = ly + lfs * 0.2
            pad_l = xmin - cx
            pad_r = (cx + cw) - xmax
            pad_t = ytop - cy
            pad_b = (cy + ch) - ybot
            ok = (pad_l >= 15.9 and pad_r >= 15.9 and pad_t >= 15.9 and pad_b >= 15.9)
            if not ok:
                all_card_ok = False
            print(f"[{'PASS' if ok else 'FAIL'}] [{card_id:14s}] L{l_idx+1} '{txt[:35]:35s}': pad_l={pad_l:5.1f}, pad_r={pad_r:5.1f}, pad_t={pad_t:5.1f}, pad_b={pad_b:5.1f}")

    assert all_card_ok, "Some card lines failed padding checks!"
    print("\n9. ALL CARDS HAVE AT LEAST 16 PX PADDING ON ALL SIDES! (PASS)")

test_full()
