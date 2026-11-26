import xml.etree.ElementTree as ET

tree = ET.parse("test_out.svg")
root = tree.getroot()

# Map of groups to test
groups = [
    ("node-client", False, 116),
    ("node-middle", False, 558),
    ("node-server", False, 1256),
    ("case-a", False, 0),
    ("case-b", False, 0),
    ("case-c", False, 0),
    ("case-d", False, 0),
    ("case-e", False, 0),
    ("example-pairing", False, 0),
    ("clock-note", False, 121),
    ("bottom-bar", False, 0)
]

for gid, is_mono, icon_r in groups:
    g = root.find(f'.//*[@id="{gid}"]')
    rects = g.findall('{http://www.w3.org/2000/svg}rect')
    texts = g.findall('{http://www.w3.org/2000/svg}text')
    
    print(f"\nGroup: {gid} (rects: {len(rects)}, texts: {len(texts)})")
    
    # In case-a..e, there are two rects and two texts (left and right)
    if gid.startswith("case-"):
        r_left, r_right = rects[0], rects[1]
        t_left, t_right = texts[0], texts[1]
        
        # Test left
        bx = float(r_left.attrib['x'])
        by = float(r_left.attrib['y'])
        bw = float(r_left.attrib['width'])
        bh = float(r_left.attrib['height'])
        
        fs = float(t_left.attrib.get('font-size', '24'))
        tx = float(t_left.attrib.get('x', '0'))
        ty = float(t_left.attrib.get('y', '0'))
        
        tspans = t_left.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = ty
            for ts in tspans:
                dy = float(ts.attrib.get('dy', '0'))
                cur_y += dy
                txt = (ts.text or "").strip()
                lw = len(txt) * 0.6 * fs
                pad_l = tx - bx
                pad_r = (bx + bw) - (tx + lw)
                pad_t = (cur_y - 0.72 * fs) - by
                pad_b = (by + bh) - (cur_y + 0.22 * fs)
                print(f"  [L] '{txt}': pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
                assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, f"Padding violated in {gid} L"
        else:
            txt = "".join(t_left.itertext()).strip()
            lw = len(txt) * 0.6 * fs
            pad_l = tx - bx
            pad_r = (bx + bw) - (tx + lw)
            pad_t = (ty - 0.72 * fs) - by
            pad_b = (by + bh) - (ty + 0.22 * fs)
            print(f"  [L] '{txt}': pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
            assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, f"Padding violated in {gid} L"

        # Test right
        bx = float(r_right.attrib['x'])
        by = float(r_right.attrib['y'])
        bw = float(r_right.attrib['width'])
        bh = float(r_right.attrib['height'])
        
        fs = float(t_right.attrib.get('font-size', '24'))
        tx = float(t_right.attrib.get('x', '0'))
        ty = float(t_right.attrib.get('y', '0'))
        
        tspans = t_right.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = ty
            for ts in tspans:
                dy = float(ts.attrib.get('dy', '0'))
                cur_y += dy
                txt = (ts.text or "").strip()
                lw = len(txt) * 0.6 * fs
                pad_l = tx - bx
                pad_r = (bx + bw) - (tx + lw)
                pad_t = (cur_y - 0.72 * fs) - by
                pad_b = (by + bh) - (cur_y + 0.22 * fs)
                print(f"  [R] '{txt}': pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
                assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, f"Padding violated in {gid} R"
        else:
            txt = "".join(t_right.itertext()).strip()
            lw = len(txt) * 0.6 * fs
            pad_l = tx - bx
            pad_r = (bx + bw) - (tx + lw)
            pad_t = (ty - 0.72 * fs) - by
            pad_b = (by + bh) - (ty + 0.22 * fs)
            print(f"  [R] '{txt}': pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
            assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, f"Padding violated in {gid} R"
            
    else:
        # Single box or container
        r = rects[0]
        t = texts[0]
        bx = float(r.attrib['x'])
        by = float(r.attrib['y'])
        bw = float(r.attrib['width'])
        bh = float(r.attrib['height'])
        
        fs = float(t.attrib.get('font-size', '24'))
        tx = float(t.attrib.get('x', '0'))
        ty = float(t.attrib.get('y', '0'))
        anchor = t.attrib.get('text-anchor', 'start')
        
        tspans = t.findall('{http://www.w3.org/2000/svg}tspan')
        if tspans:
            cur_y = ty
            for ts in tspans:
                dy = float(ts.attrib.get('dy', '0'))
                cur_y += dy
                # Check inner tspans if any
                txt = "".join(ts.itertext()).strip()
                lw = len(txt) * 0.6 * fs
                if anchor == 'middle':
                    pad_l = (tx - lw/2) - bx
                    pad_r = (bx + bw) - (tx + lw/2)
                else:
                    pad_l = tx - bx
                    pad_r = (bx + bw) - (tx + lw)
                
                if icon_r > 0:
                    pad_icon = tx - icon_r
                    assert pad_icon >= 16, f"Icon padding violated in {gid}: {pad_icon} < 16"
                
                pad_t = (cur_y - 0.72 * fs) - by
                pad_b = (by + bh) - (cur_y + 0.22 * fs)
                print(f"  '{txt}': pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
                assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, f"Padding violated in {gid}"
        else:
            txt = "".join(t.itertext()).strip()
            lw = len(txt) * 0.6 * fs
            if anchor == 'middle':
                pad_l = (tx - lw/2) - bx
                pad_r = (bx + bw) - (tx + lw/2)
            else:
                pad_l = tx - bx
                pad_r = (bx + bw) - (tx + lw)
            
            if icon_r > 0:
                pad_icon = tx - icon_r
                assert pad_icon >= 16, f"Icon padding violated in {gid}: {pad_icon} < 16"
            
            pad_t = (ty - 0.72 * fs) - by
            pad_b = (by + bh) - (ty + 0.22 * fs)
            print(f"  '{txt}': pad_l={pad_l:.1f}, pad_r={pad_r:.1f}, pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
            assert pad_l >= 16 and pad_r >= 16 and pad_t >= 16 and pad_b >= 16, f"Padding violated in {gid}"

print("\nALL BOX PADDINGS >= 16px! PERFECT!")
