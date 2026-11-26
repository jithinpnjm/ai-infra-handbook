import xml.etree.ElementTree as ET

tree = ET.parse("test_out.svg")
root = tree.getroot()

rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(el.attrib.get('x', 0))
    y = float(el.attrib.get('y', 0))
    w = float(el.attrib.get('width', 0))
    h = float(el.attrib.get('height', 0))
    if w > 0 and h > 0 and w < 1600:
        rects.append((x, y, w, h, el))

errors = []
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    anchor = el.attrib.get('text-anchor', 'start')
    fs = float(el.attrib.get('font-size', 24))
    
    tspans = [c for c in el if c.tag.endswith('tspan')]
    if tspans:
        lines = []
        for ts in tspans:
            tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
            lines.append((tx, (ts.text or "").strip()))
    else:
        tx = float(el.attrib.get('x', 0))
        lines = [(tx, (el.text or "").strip())]
    
    for tx, line in lines:
        est_w = len(line) * (0.6 * fs)
        if anchor == 'middle':
            left = tx - est_w / 2
            right = tx + est_w / 2
        else:
            left = tx
            right = tx + est_w
        
        # Find containing rect
        matched_rect = None
        for rx, ry, rw, rh, _ in rects:
            if rx - 1 <= left and right <= rx + rw + 1:
                matched_rect = (rx, ry, rw, rh)
                break
        
        if matched_rect:
            rx, ry, rw, rh = matched_rect
            pad_left = left - rx
            pad_right = (rx + rw) - right
            print(f"Line '{line[:30]}...' in [{rx}, {rw}]: pad_L={pad_left:.1f}, pad_R={pad_right:.1f}")
            if pad_left < 14:
                errors.append(f"pad_left {pad_left} < 14 for '{line}'")
            if pad_right < 14:
                errors.append(f"pad_right {pad_right} < 14 for '{line}'")
        else:
            print(f"No container rect for '{line[:30]}...' (Title)")

if errors:
    print("\nERRORS:")
    for e in errors:
        print(" ", e)
else:
    print("\nALL PADDINGS PASS WITH AT LEAST 14-16px PADDING!")
