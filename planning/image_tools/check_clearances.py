import xml.etree.ElementTree as ET
import re

tree = ET.parse('candidate_quoting_rules.svg')
root = tree.getroot()

# Map each text to its containing rectangle and icons
# Let's inspect each text element and its coordinates
SANS_FACTOR = 0.60
MONO_FACTOR = 0.62

all_ok = True
for text_elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(text_elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(text_elem.attrib['font-size'])
    ff = text_elem.attrib.get('font-family', 'sans-serif')
    anchor = text_elem.attrib.get('text-anchor', 'start')
    factor = MONO_FACTOR if ff == 'monospace' else SANS_FACTOR
    
    # Check tspans
    tspans = list(text_elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if tspans:
        lines = []
        for tsp in tspans:
            lines.append((tsp.text or "", float(tsp.attrib.get('x', text_elem.attrib.get('x', 0)))))
    else:
        lines = [(text_elem.text or "", float(text_elem.attrib.get('x', 0)))]

    for line_text, x_pos in lines:
        cleaned_line = line_text.strip()
        tw = len(cleaned_line) * fs * factor
        if anchor == 'middle':
            x1 = x_pos - tw / 2.0
            x2 = x_pos + tw / 2.0
        else:
            x1 = x_pos
            x2 = x_pos + tw
        print(f"Line '{cleaned_line[:35]}...' [fs={fs}, tw={tw:.1f}] spans x=[{x1:.1f}, {x2:.1f}]")

