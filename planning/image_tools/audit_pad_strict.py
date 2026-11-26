import xml.etree.ElementTree as ET
import re

def check_strict_paddings(svg_path):
    tree = ET.parse(svg_path)
    root = tree.getroot()
    
    # Check all rects and texts
    print(f"Checking {svg_path}...")
    # Let's find each stage and its cards
    # For every text, find the innermost rect that contains it
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 0 and rh > 0 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))
            
    # Check each text line
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
                
                # Find smallest rect containing this line
                containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
                if containing:
                    # sort by area
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
            if not txt:
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
        print("ALL PADDINGS >= 16px STRICTLY PASSED!")
    else:
        print("Some paddings < 16px.")

check_strict_paddings("test_pipeline.svg")
