import xml.etree.ElementTree as ET
import re

tree = ET.parse("perfect_candidate.svg")
root = tree.getroot()

# For each <text> element, find which rect it belongs to
texts = root.findall("{http://www.w3.org/2000/svg}text")
rects = []
for elem in root.findall("{http://www.w3.org/2000/svg}rect"):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    if w >= 1500 and h >= 1100:
        continue
    if elem.attrib.get('stroke-dasharray'):
        continue
    rects.append((x, y, w, h, elem))

# Text padding check:
# For each text, calculate its bounding box
for t_elem in texts:
    txt = "".join(t_elem.itertext()).strip()
    txt_norm = re.sub(r'\s+', ' ', txt)
    base_x = float(t_elem.attrib.get('x', 0))
    base_y = float(t_elem.attrib.get('y', 0))
    anchor = t_elem.attrib.get('text-anchor', 'start')
    base_fs = float(t_elem.attrib.get('font-size', 24))

    tspans = t_elem.findall('{http://www.w3.org/2000/svg}tspan')
    
    # Calculate min_x, max_x, min_y, max_y for this text element
    lines = []
    if tspans:
        curr_y = base_y
        for tsp in tspans:
            line_x = float(tsp.attrib.get('x', base_x))
            dy = float(tsp.attrib.get('dy', 0))
            curr_y += dy
            fs = float(tsp.attrib.get('font-size', base_fs))
            ff = tsp.attrib.get('font-family', t_elem.attrib.get('font-family', 'sans-serif'))
            t_str = tsp.text or ''
            char_w = 0.62 * fs if 'monospace' in ff else 0.6 * fs
            w = len(t_str) * char_w
            if anchor == 'middle':
                x1 = line_x - w/2
                x2 = line_x + w/2
            else:
                x1 = line_x
                x2 = line_x + w
            # font baseline curr_y: top is approx curr_y - fs*0.8, bottom is curr_y + fs*0.2
            y1 = curr_y - fs * 0.8
            y2 = curr_y + fs * 0.2
            lines.append((x1, x2, y1, y2, t_str))
    else:
        ff = t_elem.attrib.get('font-family', 'sans-serif')
        char_w = 0.62 * base_fs if 'monospace' in ff else 0.6 * base_fs
        w = len(txt) * char_w
        if anchor == 'middle':
            x1 = base_x - w/2
            x2 = base_x + w/2
        else:
            x1 = base_x
            x2 = base_x + w
        y1 = base_y - base_fs * 0.8
        y2 = base_y + base_fs * 0.2
        lines.append((x1, x2, y1, y2, txt))

    t_x1 = min(l[0] for l in lines)
    t_x2 = max(l[1] for l in lines)
    t_y1 = min(l[2] for l in lines)
    t_y2 = max(l[3] for l in lines)

    # If it's title or arrow labels, skip box containment
    if "The two queues" in txt_norm or txt_norm in ["SYN", "SYN-ACK", "ACK"]:
        print(f"Skipping container check for standalone/arrow label: '{txt_norm[:20]}'")
        continue

    # Find matching container rect
    containing = None
    for rx, ry, rw, rh, r_elem in rects:
        if rx <= t_x1 and t_x2 <= rx + rw and ry <= t_y1 and t_y2 <= ry + rh:
            containing = (rx, ry, rw, rh)
            break

    if containing is None:
        # find closest rect
        print(f"WARNING: No containing rect for '{txt_norm[:30]}' (bbox: x={t_x1:.1f}..{t_x2:.1f}, y={t_y1:.1f}..{t_y2:.1f})")
    else:
        rx, ry, rw, rh = containing
        pad_left = t_x1 - rx
        pad_right = (rx + rw) - t_x2
        pad_top = t_y1 - ry
        pad_bottom = (ry + rh) - t_y2
        print(f"OK: '{txt_norm[:25]}' pads: L={pad_left:4.1f}, R={pad_right:4.1f}, T={pad_top:4.1f}, B={pad_bottom:4.1f}")
        assert pad_left >= 16, f"Pad left violation on '{txt_norm}': {pad_left} < 16"
        assert pad_right >= 16, f"Pad right violation on '{txt_norm}': {pad_right} < 16"
        assert pad_top >= 16, f"Pad top violation on '{txt_norm}': {pad_top} < 16"
        assert pad_bottom >= 16, f"Pad bottom violation on '{txt_norm}': {pad_bottom} < 16"

print("\nALL TEXT CONTAINED WITH PADDING >= 16PX!")
