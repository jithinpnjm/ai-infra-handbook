#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_qos.svg")
root = tree.getroot()

print("=== CHECKING GEOMETRY AND CLEARANCES ===")

# Check outer margins
boxes = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(el.attrib.get('x', 0))
    y = float(el.attrib.get('y', 0))
    w = float(el.attrib.get('width', 0))
    h = float(el.attrib.get('height', 0))
    # skip background
    if w >= 1599:
        continue
    boxes.append((x, y, w, h, el.attrib.get('id', '')))

# Check padding of texts inside their parent boxes
# For each text, find which rect contains it
rects = [b for b in boxes if b[2] > 200] # larger boxes

for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib.get('font-size', 24))
    ff = el.attrib.get('font-family', 'sans-serif')
    anchor = el.attrib.get('text-anchor', 'start')
    
    tspans = [child for child in el if child.tag.endswith('tspan')]
    lines = []
    if tspans:
        for ts in tspans:
            t = ts.text or ""
            t_fs = float(ts.attrib.get('font-size', fs))
            t_ff = ts.attrib.get('font-family', ff)
            t_x = float(ts.attrib.get('x', el.attrib.get('x', 0)))
            t_y = float(ts.attrib.get('y', el.attrib.get('y', 0)))
            lines.append((t, t_fs, t_ff, t_x, t_y, anchor))
    else:
        t = "".join(el.itertext())
        t_x = float(el.attrib.get('x', 0))
        t_y = float(el.attrib.get('y', 0))
        lines.append((t, fs, ff, t_x, t_y, anchor))
        
    for t, l_fs, l_ff, lx, ly, l_anchor in lines:
        coeff = 0.62 if 'monospace' in l_ff else 0.60
        text_width = len(t) * coeff * l_fs
        
        # Calculate text bounding box
        if l_anchor == 'middle':
            text_x1 = lx - text_width / 2
            text_x2 = lx + text_width / 2
        else:
            text_x1 = lx
            text_x2 = lx + text_width
            
        text_y1 = ly - l_fs
        text_y2 = ly
        
        # Find containing rect
        containing = []
        for rx, ry, rw, rh, _ in rects:
            # check if inside
            if rx <= text_x1 and rx + rw >= text_x2 and ry <= text_y1 and ry + rh >= text_y2:
                pad_l = text_x1 - rx
                pad_r = (rx + rw) - text_x2
                pad_t = text_y1 - ry
                pad_b = (ry + rh) - text_y2
                containing.append((pad_l, pad_r, pad_t, pad_b, (rx, ry, rw, rh)))
        
        if not containing:
            # might be title or top level
            print(f"Top-level / unboxed text: '{t}' at ({lx}, {ly}) width={text_width:.1f}")
        else:
            best = min(containing, key=lambda c: c[4][2] * c[4][3]) # innermost rect
            pl, pr, pt, pb, r = best
            min_pad = min(pl, pr, pt, pb)
            status = "PASS" if min_pad >= 16 else "FAIL"
            print(f"[{status}] (min pad {min_pad:.1f}px) '{t}' inside rect w={r[2]}, h={r[3]} | L={pl:.1f}, R={pr:.1f}, T={pt:.1f}, B={pb:.1f}")
            assert min_pad >= 16, f"Padding {min_pad} < 16 px for text '{t}'!"

print("\n=== ALL PADDINGS >= 16 PX CONFIRMED! ===")
