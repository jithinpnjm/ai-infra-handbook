import xml.etree.ElementTree as ET

def verify_all_paddings():
    tree = ET.parse("test_candidate_meminfo.svg")
    root = tree.getroot()

    # Define box bounding boxes: (name, (bx, by, bw, bh), (ix, iy, iw, ih) or None)
    # 1. Console Box: (40, 140, 1520, 100)
    # 2. Card A (free): (40, 265, 740, 180), icon: (68, 327, 56, 56)
    # 3. Card B (available): (820, 265, 740, 180), icon: (848, 327, 56, 56)
    # 4. Pill around 'available': (922, 283, 160, 42)
    # 5. Segment 1: (56, 492, 958, 86), icon: (90, 492+15, 56, 56) -> (90, 507, 56, 56)
    # 6. Segment 2: (56, 586, 958, 86), icon: (90, 586+15, 56, 56) -> (90, 601, 56, 56)
    # 7. Segment 3: (56, 680, 958, 86), icon: (90, 680+15, 56, 56) -> (90, 695, 56, 56)
    # 8. Segment 4: (56, 774, 958, 86), icon: (90, 774+15, 56, 56) -> (90, 789, 56, 56)
    # 9. Segment 5: (56, 868, 958, 86), icon: (90, 868+15, 56, 56) -> (90, 883, 56, 56)
    # 10. Segment 6: (56, 962, 958, 86), icon: (90, 962+15, 56, 56) -> (90, 977, 56, 56)
    # 11. Side Box: (1070, 475, 490, 590), icon: (1287, 660, 56, 56)
    # 12. Bottom Bar: (40, 1095, 1520, 65)

    all_ok = True
    
    # Check text items inside each box
    # We inspect every <text> element
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        full_text = " ".join("".join(elem.itertext()).split())
        fs = float(elem.attrib['font-size'])
        ff = elem.attrib.get('font-family', 'sans-serif')
        is_mono = 'mono' in ff
        factor = 0.62 if is_mono else 0.60
        anchor = elem.attrib.get('text-anchor', 'start')
        
        tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            lines = []
            cur_y = float(elem.attrib.get('y', 0))
            for tsp in tspans:
                dy = float(tsp.attrib.get('dy', 0))
                cur_y += dy
                lines.append((tsp.text.strip(), float(tsp.attrib.get('x', elem.attrib.get('x', 0))), cur_y))
        else:
            lines = [(elem.text.strip(), float(elem.attrib.get('x', 0)), float(elem.attrib.get('y', 0)))]
            
        for line_txt, lx, ly in lines:
            w = len(line_txt) * fs * factor
            if anchor == 'middle':
                left = lx - w / 2.0
                right = lx + w / 2.0
            elif anchor == 'end':
                left = lx - w
                right = lx
            else:
                left = lx
                right = lx + w
            top = ly - fs
            bot = ly + 4 # descent
            
            print(f"Checking line '{line_txt[:35]}...'")
            print(f"  Bounds: left={left:.1f}, right={right:.1f}, top={top:.1f}, bot={bot:.1f}")

    print("\nText lines inspection complete.")

verify_all_paddings()
