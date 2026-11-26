#!/usr/bin/env python3
import xml.etree.ElementTree as ET

# Check exact paddings for all text lines in candidate SVG
tree = ET.parse("test_candidate_p3_0103.svg")
root = tree.getroot()

boxes = [
    # (name, box_x, box_y, box_w, box_h)
    ("Table 1", 40, 285, 240, 295),
    ("Table 1 cell", 55, 465, 210, 90),
    ("Table 2", 455, 285, 240, 295),
    ("Table 2 cell", 470, 465, 210, 90),
    ("Table 3", 870, 285, 250, 295),
    ("Table 3 cell", 885, 465, 220, 90),
    ("Final box (Inode C)", 1300, 285, 260, 340),
    ("Data blocks", 1300, 765, 260, 175),
    ("Orange callout", 805, 650, 380, 230),
    ("Bottom note", 40, 990, 1520, 68),
    ("Path box", 420, 150, 760, 96),
]

# Let's map each text element to its container box and verify margins/paddings
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    anchor = elem.attrib.get('text-anchor', 'start')
    font_family = elem.attrib.get('font-family', 'sans-serif')
    is_mono = 'monospace' in font_family
    fs = float(elem.attrib.get('font-size', 24))

    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        cur_y = y
        for ts in tspans:
            t_text = ts.text or ""
            t_fs = float(ts.attrib.get('font-size', fs))
            t_x = float(ts.attrib.get('x', x))
            dy = float(ts.attrib.get('dy', 0))
            cur_y += dy
            coeff = 0.62 if is_mono else 0.6
            w = len(t_text) * t_fs * coeff
            if anchor == 'middle':
                t_left = t_x - w/2
                t_right = t_x + w/2
            elif anchor == 'end':
                t_left = t_x - w
                t_right = t_x
            else:
                t_left = t_x
                t_right = t_x + w
            print(f"Line '{t_text}' (fs={t_fs}) -> x=[{t_left:.1f} .. {t_right:.1f}], y={cur_y:.1f}")
    else:
        text = "".join(elem.itertext()).strip()
        coeff = 0.62 if is_mono else 0.6
        w = len(text) * fs * coeff
        if anchor == 'middle':
            t_left = x - w/2
            t_right = x + w/2
        elif anchor == 'end':
            t_left = x - w
            t_right = x
        else:
            t_left = x
            t_right = x + w
        print(f"Text '{text}' (fs={fs}) -> x=[{t_left:.1f} .. {t_right:.1f}], y={y:.1f}")
