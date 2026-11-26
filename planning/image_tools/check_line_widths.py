import xml.etree.ElementTree as ET
import re

svg_path = "candidate_ca_generated.svg"
tree = ET.parse(svg_path)
root = tree.getroot()

# Let's inspect every text element, its tspans, its font-family, font-size, position, and enclosing box
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    fs = float(elem.attrib.get('font-size', 24))
    ff = elem.attrib.get('font-family', 'sans-serif')
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        text = elem.text.strip() if elem.text else ""
        multiplier = 0.62 if 'monospace' in ff else 0.6
        est_w = len(text) * fs * multiplier
        print(f"Text: '{text}' x={x} y={y} fs={fs} ff={ff} anchor={anchor} est_w={est_w:.1f}")
    else:
        curr_y = y
        for tsp in tspans:
            tx = float(tsp.attrib.get('x', x))
            dy = float(tsp.attrib.get('dy', 0))
            curr_y += dy
            tfs = float(tsp.attrib.get('font-size', fs))
            tff = tsp.attrib.get('font-family', ff)
            text = tsp.text.strip() if tsp.text else ""
            multiplier = 0.62 if 'monospace' in tff else 0.6
            est_w = len(text) * tfs * multiplier
            print(f"  Tspan: '{text}' x={tx} y={curr_y} fs={tfs} ff={tff} len={len(text)} est_w={est_w:.1f}")
