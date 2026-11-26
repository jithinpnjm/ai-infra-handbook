import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate.svg")
root = tree.getroot()

vb = [float(x) for x in root.attrib['viewBox'].split()]
W, H = vb[2], vb[3]

# Top-level rects
boxes = []
for child in root:
    tag = child.tag.split('}')[-1]
    if tag == 'rect':
        w = float(child.attrib['width'])
        h = float(child.attrib['height'])
        if w == W and h == H:
            continue
        boxes.append({
            'x': float(child.attrib['x']),
            'y': float(child.attrib['y']),
            'w': w,
            'h': h
        })

print("Checking text inside boxes:")
# Let's check each text element whether it falls inside any box
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    anchor = elem.attrib.get('text-anchor', 'start')
    fs = float(elem.attrib.get('font-size', '24'))
    x0 = float(elem.attrib.get('x', '0'))
    y0 = float(elem.attrib.get('y', '0'))
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        lines = [(elem.text.strip(), x0, y0)]
    else:
        lines = []
        cur_y = y0
        for tsp in tspans:
            tx = float(tsp.attrib.get('x', str(x0)))
            dy = float(tsp.attrib.get('dy', '0'))
            cur_y += dy
            lines.append((tsp.text.strip(), tx, cur_y))
            
    # Check if lines fall inside a box
    for text_line, lx, ly in lines:
        char_w = 0.6 * fs
        w_line = len(text_line) * char_w
        if anchor == 'middle':
            x_min = lx - w_line / 2
            x_max = lx + w_line / 2
        elif anchor == 'end':
            x_min = lx - w_line
            x_max = lx
        else:
            x_min = lx
            x_max = lx + w_line
            
        y_min = ly - 0.8 * fs
        y_max = ly + 0.25 * fs
        
        # Check if center of text is in any box
        cx = (x_min + x_max) / 2
        cy = (y_min + y_max) / 2
        for b in boxes:
            if b['x'] <= cx <= b['x'] + b['w'] and b['y'] <= cy <= b['y'] + b['h']:
                # It is inside this box! Check padding
                pad_l = x_min - b['x']
                pad_r = (b['x'] + b['w']) - x_max
                pad_t = y_min - b['y']
                pad_b = (b['y'] + b['h']) - y_max
                print(f"Inside box [x={b['x']}, y={b['y']}, w={b['w']}, h={b['h']}]:")
                print(f"  Line: '{text_line[:30]}...' -> pad: L={pad_l:.1f}, R={pad_r:.1f}, T={pad_t:.1f}, B={pad_b:.1f}")
                assert pad_l >= 16, f"Left padding {pad_l:.1f} < 16 for '{text_line}'"
                assert pad_r >= 16, f"Right padding {pad_r:.1f} < 16 for '{text_line}'"
                assert pad_t >= 16, f"Top padding {pad_t:.1f} < 16 for '{text_line}'"
                assert pad_b >= 16, f"Bottom padding {pad_b:.1f} < 16 for '{text_line}'"

print("\nALL IN-BOX TEXTS SATISFY >= 16px PADDING ON ALL SIDES!")
