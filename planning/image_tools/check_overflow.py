import xml.etree.ElementTree as ET
import re

tree = ET.parse("test.svg")
root = tree.getroot()

# Let's verify all tspans and text elements
# Conservative width: sans = 0.6 * font_size * len(chars), mono = 0.62 * font_size * len(chars)
# Let's inspect each text element and its tspans

for te in root.findall(".//{http://www.w3.org/2000/svg}text"):
    full_text = "".join(te.itertext()).strip()
    full_text_norm = re.sub(r'\s+', ' ', full_text)
    
    # check if it has tspans
    tspans = te.findall("{http://www.w3.org/2000/svg}tspan")
    if tspans:
        for ts in tspans:
            t = "".join(ts.itertext()).strip()
            # If tspan contains nested tspan, itertext gets all
            if t:
                # measure width
                w = len(t) * 14.4
                print(f"[{len(t):2d} chars, {w:5.1f}px] {t}")
    else:
        w = len(full_text_norm) * 14.4
        print(f"[{len(full_text_norm):2d} chars, {w:5.1f}px] {full_text_norm}")
