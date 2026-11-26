#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse('test_candidate_p3_0225.svg')
root = tree.getroot()

# For every text element and its tspans, calculate conservative width and verify padding inside its container
# Let's inspect each text element and its visual bounds
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    text_content = "".join(elem.itertext()).strip()
    fs = float(elem.attrib.get('font-size', 24))
    font_family = elem.attrib.get('font-family', '')
    is_mono = 'mono' in font_family
    factor = 0.62 if is_mono else 0.60
    anchor = elem.attrib.get('text-anchor', 'start')
    
    tspans = elem.findall('{http://www.w3.org/2000/svg}tspan')
    if not tspans:
        tspans = [elem]
        
    print(f"\nText: '{text_content[:40]}...' (fs={fs}, is_mono={is_mono}, anchor={anchor})")
    for tsp in tspans:
        t = (tsp.text or "").strip()
        tfs = float(tsp.attrib.get('font-size', fs))
        tw = len(t) * factor * tfs
        tx = float(tsp.attrib.get('x', elem.attrib.get('x', 0)))
        ty = float(tsp.attrib.get('y', elem.attrib.get('y', 0)))
        
        if anchor == 'middle':
            left = tx - tw / 2
            right = tx + tw / 2
        elif anchor == 'end':
            left = tx - tw
            right = tx
        else:
            left = tx
            right = tx + tw
            
        print(f"  tspan '{t}': len={len(t)}, width={tw:.1f}px, bounds=({left:.1f}, {right:.1f})")
