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
    fs = float(el.attrib.get('font-size', 24))
    
    tspans = [c for c in el if c.tag.endswith('tspan')]
    if tspans:
        ys = []
        cur_y = float(el.attrib.get('y', 0))
        for ts in tspans:
            if 'y' in ts.attrib:
                cur_y = float(ts.attrib['y'])
            elif 'dy' in ts.attrib:
                cur_y += float(ts.attrib['dy'])
            ys.append((cur_y, (ts.text or "").strip()))
        tx = float(tspans[0].attrib.get('x', el.attrib.get('x', 0)))
    else:
        ys = [(float(el.attrib.get('y', 0)), (el.text or "").strip())]
        tx = float(el.attrib.get('x', 0))
    
    top_y = ys[0][0] - (0.75 * fs) # approx cap height
    bot_y = ys[-1][0] + (0.25 * fs) # approx descent
    
    # find containing rect
    matched_rect = None
    for rx, ry, rw, rh, _ in rects:
        if rx - 5 <= tx <= rx + rw + 5 and ry - 5 <= top_y and bot_y <= ry + rh + 15:
            matched_rect = (rx, ry, rw, rh)
            break
            
    if matched_rect:
        rx, ry, rw, rh = matched_rect
        pad_top = top_y - ry
        pad_bot = (ry + rh) - bot_y
        line_repr = ys[0][1][:20]
        print(f"Text '{line_repr}' in rect [y={ry}, h={rh}]: pad_top={pad_top:.1f}, pad_bot={pad_bot:.1f}")
        if pad_top < 16:
            errors.append(f"pad_top {pad_top:.1f} < 16 for '{line_repr}'")
        if pad_bot < 16:
            errors.append(f"pad_bot {pad_bot:.1f} < 16 for '{line_repr}'")
    else:
        print(f"No rect for '{ys[0][1][:20]}'")

if errors:
    print("\nVERTICAL ERRORS:")
    for e in errors:
        print(" ", e)
else:
    print("\nALL VERTICAL PADDINGS >= 16px!")
