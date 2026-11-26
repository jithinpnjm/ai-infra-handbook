#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def check_all_strict_paddings(svg_text):
    root = ET.fromstring(svg_text)
    
    # 1. First children check: <title> and <desc>
    children = list(root)
    first_tag = children[0].tag.split('}')[-1]
    second_tag = children[1].tag.split('}')[-1]
    assert first_tag == 'title', f"First child must be title, got {first_tag}"
    assert second_tag == 'desc', f"Second child must be desc, got {second_tag}"
    
    # 2. Dimensions
    width = root.get('width')
    viewBox = root.get('viewBox')
    height = root.get('height')
    assert width == "1600"
    assert viewBox.startswith("0 0 1600 ")
    vb_parts = [float(x) for x in viewBox.split()]
    assert 900 <= vb_parts[3] <= 1200
    assert int(height) == int(vb_parts[3])
    
    rects = []
    for el in root.iter('{http://www.w3.org/2000/svg}rect'):
        rx = float(el.attrib.get('x', 0))
        ry = float(el.attrib.get('y', 0))
        rw = float(el.attrib.get('width', 0))
        rh = float(el.attrib.get('height', 0))
        if rw > 0 and rh > 0 and rw < 1600:
            rects.append((rx, ry, rx + rw, ry + rh, el))
            
    # Check each text and tspan
    all_passed = True
    for el in root.iter('{http://www.w3.org/2000/svg}text'):
        fs = float(el.attrib.get('font-size', 24))
        ff = el.attrib.get('font-family', 'sans-serif')
        anchor = el.attrib.get('text-anchor', 'start')
        
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
                tfs = float(ts.attrib.get('font-size', fs))
                tff = ts.attrib.get('font-family', ff)
                rate = 0.62 if 'monospace' in tff else 0.60
                tw = len(txt) * rate * tfs
                if anchor == 'middle':
                    tl = tx - tw / 2
                    tr = tx + tw / 2
                else:
                    tl = tx
                    tr = tx + tw
                ttop = cur_y - tfs * 0.8
                tbot = cur_y
                
                # Check containing rect
                containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
                if not containing:
                    print(f"ERROR: No rect contains tspan '{txt}' (bounds: [{tl:.1f}, {ttop:.1f}, {tr:.1f}, {tbot:.1f}])")
                    all_passed = False
                else:
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
                        print(f"PASS tspan: '{txt[:30]}' pads: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
        else:
            txt = "".join(el.itertext()).strip()
            if not txt:
                continue
            tx = float(el.attrib.get('x', 0))
            ty = float(el.attrib.get('y', 0))
            rate = 0.62 if 'monospace' in ff else 0.60
            tw = len(txt) * rate * fs
            if anchor == 'middle':
                tl = tx - tw / 2
                tr = tx + tw / 2
            else:
                tl = tx
                tr = tx + tw
            ttop = ty - fs * 0.8
            tbot = ty
            
            # Title doesn't have to be in a rect (canvas padding)
            if 'Why maxSurge 1' in txt:
                print(f"PASS Title '{txt[:30]}' bounds: [{tl:.1f}, {ttop:.1f}, {tr:.1f}, {tbot:.1f}]")
                continue
                
            containing = [r for r in rects if r[0] <= tl and r[1] <= ttop and r[2] >= tr and r[3] >= tbot]
            if not containing:
                print(f"ERROR: No rect contains text '{txt}' (bounds: [{tl:.1f}, {ttop:.1f}, {tr:.1f}, {tbot:.1f}])")
                all_passed = False
            else:
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
                    print(f"PASS text: '{txt[:30]}' pads: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")

    assert all_passed, "Padding verification failed!"
    print("\nALL BOXES AND PADDINGS STRICTLY PASSED!")

if __name__ == "__main__":
    print("Ready to test.")
