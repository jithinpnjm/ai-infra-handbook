#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("test_p99_candidate.svg")
root = tree.getroot()

# Check text fitting
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    fs = float(elem.attrib.get('font-size', 24))
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        for tsp in tspans:
            t = tsp.text or ""
            tfs = float(tsp.attrib.get('font-size', fs))
            font_fam = tsp.attrib.get('font-family', elem.attrib.get('font-family', 'sans-serif'))
            char_w = 0.62 if 'monospace' in font_fam else 0.6
            est_w = len(t) * char_w * tfs
            print(f"[{tfs}px] '{t}' -> est width: {est_w:.1f}px")
    else:
        t = "".join(elem.itertext()).strip()
        font_fam = elem.attrib.get('font-family', 'sans-serif')
        char_w = 0.62 if 'monospace' in font_fam else 0.6
        est_w = len(t) * char_w * fs
        print(f"[{fs}px] '{t}' -> est width: {est_w:.1f}px")
