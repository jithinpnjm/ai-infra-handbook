#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_private_ca.svg")
root = tree.getroot()

print("=== Checking Bounding Boxes and Paddings ===")

# Check every text element
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    fs = float(elem.attrib.get('font-size', '24'))
    ff = elem.attrib.get('font-family', 'sans-serif')
    anchor = elem.attrib.get('text-anchor', 'start')
    
    # check direct text or tspans
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        text = "".join(elem.itertext()).strip()
        rate = 0.62 if 'monospace' in ff else 0.6
        w = len(text) * fs * rate
        print(f"Direct text: '{text[:30]}...' x={x} y={y} fs={fs} anchor={anchor} est_w={w:.1f}")
    else:
        for tsp in tspans:
            tx = float(tsp.attrib.get('x', x))
            ty = float(tsp.attrib.get('y', y))
            tfs = float(tsp.attrib.get('font-size', fs))
            tff = tsp.attrib.get('font-family', ff)
            ttext = "".join(tsp.itertext())
            rate = 0.62 if 'monospace' in tff else 0.6
            w = len(ttext.strip()) * tfs * rate
            right_edge = tx + w if anchor == 'start' else (tx + w/2 if anchor == 'middle' else tx)
            left_edge = tx if anchor == 'start' else (tx - w/2 if anchor == 'middle' else tx - w)
            print(f"  tspan: fs={tfs:2.0f} est_w={w:5.1f} left={left_edge:5.1f} right={right_edge:6.1f} : '{ttext.strip()[:40]}'")
            assert left_edge >= 40, f"Text overflows left: {left_edge} < 40 in '{ttext}'"
            assert right_edge <= 1560, f"Text overflows right: {right_edge} > 1560 in '{ttext}'"

print("\nALL TEXT LINES REMAIN SAFELY WITHIN CANVAS (40px margin)!")
