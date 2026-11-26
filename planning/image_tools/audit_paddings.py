#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def audit_paddings(svg_path):
    print("Checking exact text bounds and paddings...")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    boxes = [
        (40, 15, 1520, 140),    # 0: Title
        (65, 285, 240, 60),     # 1: SYN then RST
        (75, 693, 220, 60),     # 2: SYN retried
        (350, 165, 350, 90),    # 3: Col 1 Header
        (720, 165, 460, 90),    # 4: Col 2 Header
        (1200, 165, 360, 90),   # 5: Col 3 Header
        (350, 270, 350, 180),   # 6: R1 C1
        (720, 270, 460, 180),   # 7: R1 C2
        (1200, 270, 360, 180),  # 8: R1 C3
        (350, 465, 350, 180),   # 9: R2 C1
        (720, 465, 460, 180),   # 10: R2 C2
        (1200, 465, 360, 180),  # 11: R2 C3
        (350, 660, 350, 180),   # 12: R3 C1
        (720, 660, 460, 180),   # 13: R3 C2
        (1200, 660, 360, 180),  # 14: R3 C3
        (350, 855, 350, 180),   # 15: R4 C1
        (720, 855, 460, 180),   # 16: R4 C2
        (1200, 855, 360, 180),  # 17: R4 C3
        (40, 1070, 1520, 95)    # 18: Takeaway
    ]

    texts = root.findall('.//{http://www.w3.org/2000/svg}text')
    assert len(texts) == len(boxes), f"Texts count {len(texts)} != boxes count {len(boxes)}"

    all_passed = True
    for idx, (elem, (bx, by, bw, bh)) in enumerate(zip(texts, boxes)):
        fs = float(elem.attrib.get('font-size', 24))
        anchor = elem.attrib.get('text-anchor', 'start')
        base_x = float(elem.attrib.get('x', 0))
        base_y = float(elem.attrib.get('y', 0))
        
        tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
        if not tspans:
            tspans = [elem]
            
        cur_y = base_y
        min_x = 99999
        max_x = -99999
        min_y = 99999
        max_y = -99999
        
        for tsp in tspans:
            t = (tsp.text or "").strip()
            if not t: continue
            t_fs = float(tsp.attrib.get('font-size', fs))
            t_x = float(tsp.attrib.get('x', base_x))
            
            # y position calculation
            dy = tsp.attrib.get('dy')
            y_val = tsp.attrib.get('y')
            if y_val is not None and tsp is not elem:
                cur_y = float(y_val)
            elif dy is not None and tsp is not elem:
                cur_y += float(dy)
            elif tsp is elem:
                cur_y = base_y
                
            w = len(t) * 0.60 * t_fs
            if anchor == 'middle':
                x1 = t_x - w / 2
                x2 = t_x + w / 2
            elif anchor == 'end':
                x1 = t_x - w
                x2 = t_x
            else:
                x1 = t_x
                x2 = t_x + w
                
            y1 = cur_y - 0.75 * t_fs
            y2 = cur_y + 0.25 * t_fs
            
            min_x = min(min_x, x1)
            max_x = max(max_x, x2)
            min_y = min(min_y, y1)
            max_y = max(max_y, y2)

        pad_left = min_x - bx
        pad_right = (bx + bw) - max_x
        pad_top = min_y - by
        pad_bottom = (by + bh) - max_y

        full_t = "".join(elem.itertext()).strip()[:40]
        ok_x = (pad_left >= 16 and pad_right >= 16)
        ok_y = (pad_top >= 16 and pad_bottom >= 16)
        
        status = "PASS" if (ok_x and ok_y) else "WARN"
        if not (ok_x and ok_y):
            all_passed = False
            
        print(f"[{status}] #{idx:2d} '{full_t:40s}' | pad: L={pad_left:4.1f}, R={pad_right:4.1f}, T={pad_top:4.1f}, B={pad_bottom:4.1f}")

    if all_passed:
        print("\n>>> ALL PADDINGS >= 16px! (STRICT PASS) <<<")
    else:
        print("\n>>> SOME PADDINGS NEED ADJUSTMENT! <<<")

audit_paddings("test_connection_fails.svg")
