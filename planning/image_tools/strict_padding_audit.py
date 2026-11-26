import xml.etree.ElementTree as ET

def audit_strict(svg_path):
    print(f"=== Strict Padding and Clearance Audit: {svg_path} ===")
    tree = ET.parse(svg_path)
    root = tree.getroot()

    all_ok = True

    # 1. Canvas margins (>= 40px)
    print("\n1. Checking Canvas Margins (>= 40px):")
    for elem in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(elem.attrib['font-size'])
        ff = elem.attrib.get('font-family', 'sans-serif')
        factor = 0.62 if 'mono' in ff else 0.60
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
            top = ly - fs * 0.75
            bot = ly + 4
            
            lm = left
            rm = 1600 - right
            tm = top
            bm = 1200 - bot
            
            if lm < 39.9 or rm < 39.9 or tm < 39.9 or bm < 39.9:
                print(f"  FAIL Canvas Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")
                all_ok = False
            else:
                print(f"  PASS Canvas Margin: '{line_txt[:30]}' lm={lm:.1f}, rm={rm:.1f}, tm={tm:.1f}, bm={bm:.1f}")

    # 2. Box paddings (>= 16px)
    print("\n2. Checking Box Paddings (>= 16px):")
    boxes_to_check = [
        ("Terminal Box", (40, 175, 1520, 95), None, [
            ("total 1.9Ti  used 120Gi  free 40Gi  shared 1.2Gi  buff/cache 1.7Ti  available 1.7Ti", 135, 218, 24, True, 'start'),
            ("0B 0B 0B", 135, 250, 24, True, 'start')
        ]),
        ("Card A (free)", (40, 300, 680, 195), (68, 368, 56, 56), [
            ("free", 150, 372, 30, False, 'start'),
            ("idle memory, deliberately small", 150, 428, 24, False, 'start')
        ]),
        ("Card B (available)", (760, 300, 800, 195), (788, 368, 56, 56), [
            ("available", 885, 358, 30, False, 'start'),
            ("MemAvailable: how much you can use to start", 866, 416, 24, False, 'start'),
            ("new applications without swapping; counts", 866, 444, 24, False, 'start'),
            ("reclaimable page cache and slab", 866, 472, 24, False, 'start')
        ]),
        ("Pill (available)", (865, 318, 202, 61), None, [
            ("available", 885, 358, 30, False, 'start')
        ]),
        ("Segment 1 (AnonPages)", (54, 538, 962, 81), (88, 550, 56, 56), [
            ("AnonPages: process private heap and stack", 164, 587, 24, False, 'start')
        ]),
        ("Segment 2 (Cached)", (54, 624, 962, 81), (88, 636, 56, 56), [
            ("Cached: page cache, including mapped files", 164, 659, 24, False, 'start'),
            ("and tmpfs through Shmem", 164, 685, 24, False, 'start')
        ]),
        ("Segment 3 (Slab)", (54, 710, 962, 81), (88, 722, 56, 56), [
            ("Slab = SReclaimable (can be freed) + SUnreclaim (cannot)", 164, 759, 24, False, 'start')
        ]),
        ("Segment 4 (PageTables)", (54, 796, 962, 81), (88, 808, 56, 56), [
            ("PageTables and KernelStack: kernel overhead", 164, 845, 24, False, 'start')
        ]),
        ("Segment 5 (HugePages)", (54, 882, 962, 81), (88, 894, 56, 56), [
            ("HugePages_*: explicitly reserved,", 164, 917, 24, False, 'start'),
            ("ordinary allocation cannot use it", 164, 943, 24, False, 'start')
        ]),
        ("Segment 6 (Mlocked)", (54, 968, 962, 81), (88, 980, 56, 56), [
            ("Mlocked and Unevictable: reclaim cannot touch", 164, 1017, 24, False, 'start')
        ]),
        ("Side Box", (1070, 530, 490, 530), (1287, 680, 56, 56), [
            ("In buff/cache, shared and", 1315, 785, 24, False, 'middle'),
            ("tmpfs pages and mlocked", 1315, 821, 24, False, 'middle'),
            ("pages are not reclaimable", 1315, 857, 24, False, 'middle')
        ]),
        ("Bottom Bar", (40, 1095, 1520, 65), None, [
            ("Read available, not free", 800, 1136, 28, False, 'middle')
        ])
    ]

    for bname, (bx, by, bw, bh), icon, lines in boxes_to_check:
        print(f"\n--- Box: {bname} ---")
        for line_txt, lx, ly, fs, is_mono, anchor in lines:
            factor = 0.62 if is_mono else 0.60
            w = len(line_txt) * fs * factor
            if anchor == 'middle':
                left = lx - w / 2.0
                right = lx + w / 2.0
            else:
                left = lx
                right = lx + w
            top = ly - fs * 0.75
            bot = ly + 4
            
            pad_left = left - bx
            pad_right = (bx + bw) - right
            pad_top = top - by
            pad_bot = (by + bh) - bot
            
            print(f"Line '{line_txt[:30]}...':")
            print(f"  pad_left={pad_left:.1f}, pad_right={pad_right:.1f}, pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f}")
            
            if pad_left < 15.9:
                print(f"  FAIL: pad_left {pad_left:.1f} < 16!")
                all_ok = False
            if pad_right < 15.9:
                print(f"  FAIL: pad_right {pad_right:.1f} < 16!")
                all_ok = False
            if pad_top < 15.9:
                print(f"  FAIL: pad_top {pad_top:.1f} < 16!")
                all_ok = False
            if pad_bot < 15.9:
                print(f"  FAIL: pad_bot {pad_bot:.1f} < 16!")
                all_ok = False
                
            if icon:
                ix, iy, iw, ih = icon
                if ix + iw <= left:
                    icon_gap = left - (ix + iw)
                    print(f"  icon_gap={icon_gap:.1f}px")
                    if icon_gap < 15.9:
                        print(f"  FAIL: icon_gap {icon_gap:.1f} < 16!")
                        all_ok = False
                elif iy + ih <= top:
                    icon_gap = top - (iy + ih)
                    print(f"  icon_gap={icon_gap:.1f}px (vertical)")
                    if icon_gap < 15.9:
                        print(f"  FAIL: vertical icon_gap {icon_gap:.1f} < 16!")
                        all_ok = False

    assert all_ok, "Some paddings or clearances failed!"
    print("\nALL BOX PADDINGS AND ICON CLEARANCES STRICTLY PASSED (>= 16px)!")

if __name__ == "__main__":
    audit_strict("test_candidate_meminfo2.svg")
