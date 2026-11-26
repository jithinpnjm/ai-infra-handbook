#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("planning/image_tools/perfect_engines.svg")
root = tree.getroot()

# Let's check all text elements and tspans:
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    fs = float(elem.attrib['font-size'])
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        cur_y = y
        for tsp in tspans:
            t = (tsp.text or "").strip()
            dy = float(tsp.attrib.get('dy', 0))
            cur_y += dy
            tx = float(tsp.attrib.get('x', x))
            t_is_mono = tsp.attrib.get('font-family') == 'monospace' or elem.attrib.get('font-family') == 'monospace'
            factor = 0.62 if t_is_mono else 0.6
            w = len(t) * fs * factor
            if anchor == 'middle':
                x1 = tx - w/2
                x2 = tx + w/2
            else:
                x1 = tx
                x2 = tx + w
            top = cur_y - fs * 0.75
            bot = cur_y + fs * 0.2
            # print details
            # print(f"  tspan '{t[:25]}': x=[{x1:.1f}, {x2:.1f}], y=[{top:.1f}, {bot:.1f}]")
    else:
        is_mono = elem.attrib.get('font-family') == 'monospace'
        factor = 0.62 if is_mono else 0.6
        w = len(full_text) * fs * factor
        if anchor == 'middle':
            x1 = x - w/2
            x2 = x + w/2
        else:
            x1 = x
            x2 = x + w
        top = y - fs * 0.75
        bot = y + fs * 0.2
        # print(f"  text '{full_text[:25]}': x=[{x1:.1f}, {x2:.1f}], y=[{top:.1f}, {bot:.1f}]")

print("All text coordinate checks computed without error!")
