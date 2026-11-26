#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse('candidate_surge_stall.svg')
root = tree.getroot()

rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    rx = float(el.attrib.get('x', 0))
    ry = float(el.attrib.get('y', 0))
    rw = float(el.attrib.get('width', 0))
    rh = float(el.attrib.get('height', 0))
    if rw > 0 and rh > 0 and rw < 1600:
        rects.append((rx, ry, rx + rw, ry + rh, el))

for el in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(el.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(el.attrib.get('font-size', 24))
    
    tspans = el.findall('{http://www.w3.org/2000/svg}tspan')
    if tspans:
        cur_y = float(el.attrib.get('y', 0))
        for ts in tspans:
            txt = ts.text or ""
            if not txt.strip(): continue
            tx = float(ts.attrib.get('x', el.attrib.get('x', 0)))
            dy = float(ts.attrib.get('dy', 0))
            cur_y += dy
            tfs = float(ts.attrib.get('font-size', fs))
            ff = ts.attrib.get('font-family', el.attrib.get('font-family', 'sans-serif'))
            rate = 0.62 if 'monospace' in ff else 0.60
            tw = len(txt) * rate * tfs
            tl = tx
            tr = tx + tw
            ttop = cur_y - tfs * 0.8
            tbot = cur_y
            print(f"TSPAN: '{txt}' -> x=[{tl:.1f}, {tr:.1f}], y=[{ttop:.1f}, {tbot:.1f}]")
    else:
        tx = float(el.attrib.get('x', 0))
        ty = float(el.attrib.get('y', 0))
        ff = el.attrib.get('font-family', 'sans-serif')
        anchor = el.attrib.get('text-anchor', 'start')
        rate = 0.62 if 'monospace' in ff else 0.60
        tw = len(full_text) * rate * fs
        if anchor == 'middle':
            tl = tx - tw / 2
            tr = tx + tw / 2
        else:
            tl = tx
            tr = tx + tw
        ttop = ty - fs * 0.8
        tbot = ty
        print(f"TEXT: '{full_text}' -> x=[{tl:.1f}, {tr:.1f}], y=[{ttop:.1f}, {tbot:.1f}]")
