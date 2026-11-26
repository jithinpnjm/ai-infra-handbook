#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_candidate_facts.svg")
root = tree.getroot()

# Map boxes
boxes = [
    # (name, x, y, w, h)
    ("Left Card 1", 40, 100, 860, 90),
    ("Left Card 2", 40, 230, 860, 90),
    ("Left Card 3", 40, 360, 860, 120),
    ("Right Panel", 940, 100, 620, 380),
    ("Example Box", 40, 520, 1520, 220),
    ("Prefer Strip", 40, 780, 1520, 130),
    ("Cost Strip", 40, 950, 1520, 100),
    ("Bottom Bar", 40, 1090, 1520, 70)
]

# Let's inspect each text element and its tspans
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x_base = float(elem.attrib.get('x', 0))
    y_base = float(elem.attrib.get('y', 0))
    anchor = elem.attrib.get('text-anchor', 'start')
    fs = float(elem.attrib.get('font-size', 24))
    font_fam = elem.attrib.get('font-family', 'sans-serif')
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)

    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        # Single text
        is_mono = (font_fam == 'monospace')
        rate = 0.62 if is_mono else 0.60
        w = len(full_text) * fs * rate
        print(f"Text '{full_text[:30]}...': fs={fs}, anchor={anchor}, x={x_base}, y={y_base}, est_w={w:.1f}")
    else:
        print(f"\nParent text '{full_text[:30]}...':")
        cur_y = y_base
        for tsp in tspans:
            tx = float(tsp.attrib.get('x', x_base))
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            t_font = tsp.attrib.get('font-family', font_fam)
            is_mono = (t_font == 'monospace')
            rate = 0.62 if is_mono else 0.60
            txt = tsp.text or ""
            # strip trailing space for width calc
            txt_clean = txt.rstrip()
            w = len(txt_clean) * fs * rate
            print(f"  tspan '{txt_clean[:35]}...': len={len(txt_clean)}, x={tx}, y={cur_y}, w={w:.1f}, right={tx+w:.1f}")
