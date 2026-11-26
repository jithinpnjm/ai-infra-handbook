import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_lossless.svg")
root = tree.getroot()

# Let's inspect all <text> elements, compute their conservative bounding boxes and compare with parent or enclosing rects!

# Text width factor: 0.60 * font_size per character
def get_tspan_bounds(elem):
    fs = float(elem.attrib.get('font-size', '24'))
    x_base = float(elem.attrib.get('x', '0'))
    y_base = float(elem.attrib.get('y', '0'))
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    lines = []
    if not tspans:
        txt = "".join(elem.itertext()).strip()
        lines.append((txt, x_base, y_base, fs))
    else:
        curr_y = y_base
        for tsp in tspans:
            txt = tsp.text or ""
            txt = txt.strip()
            tx = float(tsp.attrib.get('x', str(x_base)))
            dy = float(tsp.attrib.get('dy', '0'))
            curr_y += dy
            tfs = float(tsp.attrib.get('font-size', str(fs)))
            lines.append((txt, tx, curr_y, tfs))
            
    # Compute bounding box
    min_x = 999999
    max_x = -999999
    min_y = 999999
    max_y = -999999
    
    for txt, lx, ly, lfs in lines:
        w = len(txt) * 0.60 * lfs
        if anchor == 'middle':
            x0 = lx - w / 2.0
            x1 = lx + w / 2.0
        elif anchor == 'end':
            x0 = lx - w
            x1 = lx
        else: # start
            x0 = lx
            x1 = lx + w
            
        y0 = ly - lfs * 0.85 # approximate top of ascent
        y1 = ly + lfs * 0.20 # approximate descent
        
        min_x = min(min_x, x0)
        max_x = max(max_x, x1)
        min_y = min(min_y, y0)
        max_y = max(max_y, y1)
        
    return min_x, min_y, max_x, max_y, lines

all_texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x0, y0, x1, y1, lines = get_tspan_bounds(elem)
    full = "".join(elem.itertext()).strip()
    full = re.sub(r'\s+', ' ', full)
    all_texts.append({
        'text': full,
        'bbox': (x0, y0, x1, y1),
        'lines': lines
    })

print(f"Total analyzed texts: {len(all_texts)}")
for i, t in enumerate(all_texts, 1):
    x0, y0, x1, y1 = t['bbox']
    w = x1 - x0
    h = y1 - y0
    print(f"{i:2d}. [{w:6.1f} x {h:5.1f}] at ({x0:6.1f}, {y0:6.1f}) -> ({x1:6.1f}, {y1:6.1f}): '{t['text'][:35]}...'")
    # Verify inside 1600 x 1160 with 40px margin (except title which starts at x=40)
    assert x0 >= 40, f"Text overflows left canvas margin: {x0} < 40"
    assert x1 <= 1560, f"Text overflows right canvas margin: {x1} > 1560"
    assert y0 >= 30, f"Text overflows top margin: {y0} < 30"
    assert y1 <= 1130, f"Text overflows bottom margin: {y1} > 1130"

print("\nCanvas margin check passed for all text elements!")
