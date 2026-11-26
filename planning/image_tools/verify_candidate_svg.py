import re
import xml.etree.ElementTree as ET

def verify_svg(svg_content):
    root = ET.fromstring(svg_content)
    
    # 1. Structure: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    print(f"1. Structure: Child 0: <{first_tag}>, Child 1: <{second_tag}>")
    assert first_tag == "title", f"First child must be title, got {first_tag}"
    assert second_tag == "desc", f"Second child must be desc, got {second_tag}"

    # 2. Canvas
    width = root.attrib.get("width")
    height = root.attrib.get("height")
    viewBox = root.attrib.get("viewBox")
    print(f"2. Dimensions: width={width}, height={height}, viewBox={viewBox}")
    assert width == "1600", f"width must be 1600, got {width}"
    vb_parts = [float(x) for x in viewBox.split()]
    assert vb_parts[0] == 0 and vb_parts[1] == 0 and vb_parts[2] == 1600
    assert 900 <= vb_parts[3] <= 1200, f"H={vb_parts[3]} outside 900..1200"
    assert float(height) == vb_parts[3]

    # 3. Text font-size >= 24
    text_elements = []
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = "".join(elem.itertext()).strip()
        full_text = re.sub(r'\s+', ' ', full_text)
        fs = float(elem.attrib.get('font-size', '0'))
        tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
        if fs == 0 and tspans:
            fs = float(tspans[0].attrib.get('font-size', '0'))
        assert fs >= 24, f"Text '{full_text}' font-size {fs} < 24!"
        for tsp in tspans:
            tfs = tsp.attrib.get('font-size')
            if tfs is not None:
                assert float(tfs) >= 24, f"tspan font-size {tfs} < 24 in '{full_text}'"
        text_elements.append((full_text, fs))

    print(f"3. Font sizes: Total text elements = {len(text_elements)} (all >= 24px)")
    for i, (t, fs) in enumerate(text_elements, 1):
        print(f"   {i:2d}. [{fs:2.0f}px] '{t}'")

    # 4. Forbidden words
    forbidden = ['orange', 'green', 'grey', 'gray', 'bold', 'monospace', 'arrow', 'cylinder', 'folder', 'icon', 'callout', 'sub-line', 'subline', 'takeaway']
    for t, fs in text_elements:
        words = re.findall(r'\b[a-zA-Z]+\b', t.lower())
        for f in forbidden:
            assert f not in words, f"Forbidden word '{f}' found in '{t}'!"
    print("4. Forbidden words check: PASS")

    # 5. Orange #db8129 check
    orange_matches = re.findall(r'#db8129', svg_content, re.IGNORECASE)
    print(f"5. Orange #db8129 count: {len(orange_matches)}")
    # Should only be used for the single most important item
    assert len(orange_matches) >= 1, "Orange #db8129 must be present"

    # 6. Arrows count check
    lines = [e for e in root.iter('{http://www.w3.org/2000/svg}line') if "marker-end" in e.attrib]
    paths = [e for e in root.iter('{http://www.w3.org/2000/svg}path') if "marker-end" in e.attrib]
    total_arrows = len(lines) + len(paths)
    print(f"6. Arrows with marker-end: {total_arrows}")

    # 7. Strict Paddings Check (>= 16px)
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 0 and rh > 0 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))

    all_passed = True
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', 24))
        ff = el.attrib.get('font-family', 'sans-serif')
        anchor = el.attrib.get('text-anchor', 'start')
        rate = 0.62 if 'monospace' in ff else 0.60
        
        tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = float(el.attrib.get('y', 0))
            for ts in tspans:
                txt = ts.text or ""
                if not txt.strip(): continue
                tfs = float(ts.attrib.get('font-size', fs))
                tff = ts.attrib.get('font-family', ff)
                trate = 0.62 if 'monospace' in tff else 0.60
                tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
                dy = float(ts.attrib.get('dy', 0))
                cur_y += dy
                tw = len(txt) * trate * tfs
                if anchor == 'middle':
                    tl = tx - tw / 2
                    tr = tx + tw / 2
                else:
                    tl = tx
                    tr = tx + tw
                ttop = cur_y - tfs * 0.8
                tbot = cur_y
                containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
                if containing:
                    containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                    best = containing[0]
                    pad_l = tl - best[0]
                    pad_r = best[2] - tr
                    pad_t = ttop - best[1]
                    pad_b = best[3] - tbot
                    if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                        print(f"WARN padding: '{txt}' in rect {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                        all_passed = False
        else:
            txt = "".join(el.itertext()).strip()
            if not txt: continue
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
            containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
            if containing:
                containing.sort(key=lambda r: (r[2]-r[0])*(r[3]-r[1]))
                best = containing[0]
                pad_l = tl - best[0]
                pad_r = best[2] - tr
                pad_t = ttop - best[1]
                pad_b = best[3] - tbot
                if pad_l < 15.9 or pad_r < 15.9 or pad_t < 15.9 or pad_b < 15.9:
                    print(f"WARN padding: '{txt}' in rect {best[:4]}: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                    all_passed = False
    
    if all_passed:
        print("7. Strict Paddings Check: PASS (all >= 16px)")
    else:
        print("7. Strict Paddings Check: FAIL")
    return all_passed
