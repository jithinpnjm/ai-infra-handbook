#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_eui64.svg")
root = tree.getroot()

# For each <text> element, extract lines from tspans (or the text itself)
# and calculate conservative width: sans 0.6 * fs * chars, mono 0.62 * fs * chars
lines_data = [
    # (box_w, box_rx, font_size, is_mono, text)
]

for el in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(el.attrib['font-size'])
    tspans = list(el.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        for tsp in tspans:
            tfs = float(tsp.attrib.get('font-size', fs))
            font = tsp.attrib.get('font-family', el.attrib.get('font-family', 'sans-serif'))
            txt = tsp.text or ""
            is_mono = 'monospace' in font
            factor = 0.62 if is_mono else 0.6
            w = len(txt) * factor * tfs
            print(f"[{tfs:2.0f}px {'mono' if is_mono else 'sans'}] len={len(txt):2d} est_w={w:6.1f}px : '{txt}'")
    else:
        txt = "".join(el.itertext()).strip()
        font = el.attrib.get('font-family', 'sans-serif')
        is_mono = 'monospace' in font
        factor = 0.62 if is_mono else 0.6
        w = len(txt) * factor * fs
        print(f"[{fs:2.0f}px {'mono' if is_mono else 'sans'}] len={len(txt):2d} est_w={w:6.1f}px : '{txt}'")
