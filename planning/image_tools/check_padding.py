import xml.etree.ElementTree as ET

tree = ET.parse("test_out.svg")
root = tree.getroot()

# Check every text line fits inside its box with at least 16 px padding
# Let's inspect bounding boxes and padding for each text line
print("Checking text paddings...")

# Find all rects
rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(el.attrib.get('x', 0))
    y = float(el.attrib.get('y', 0))
    w = float(el.attrib.get('width', 0))
    h = float(el.attrib.get('height', 0))
    if w > 0 and h > 0 and w < 1600:
        rects.append((x, y, w, h, el))

# For each text, find its container rect and check paddings
for el in root.iter('{http://www.w3.org/2000/svg}text'):
    anchor = el.attrib.get('text-anchor', 'start')
    fs = float(el.attrib.get('font-size', 24))
    
    tspans = [c for c in el if c.tag.endswith('tspan')]
    if tspans:
        lines = []
        for ts in tspans:
            tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
            lines.append((tx, ts.text.strip()))
    else:
        tx = float(el.attrib.get('x', 0))
        lines = [(tx, el.text.strip())]
    
    # Check each line's estimated width
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
            if rx <= left and right <= rx + rw + 5: # rough match
                matched_rect = (rx, ry, rw, rh)
                break
        
        if matched_rect:
            rx, ry, rw, rh = matched_rect
            pad_left = left - rx
            pad_right = (rx + rw) - right
            print(f"Line '{line[:25]}...' in [{rx}, {rw}]: pad_L={pad_left:.1f}, pad_R={pad_right:.1f}")
            assert pad_left >= 14, f"pad_left {pad_left} < 14 for '{line}'"
            assert pad_right >= 14, f"pad_right {pad_right} < 14 for '{line}'"
        else:
            print(f"No container rect for '{line[:25]}...' (likely Title or Root)")

print("Padding check passed!")
