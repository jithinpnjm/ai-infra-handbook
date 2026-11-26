import xml.etree.ElementTree as ET
import re

svg_content = open("test_build.py").read()
# extract svg_template
m = re.search(r"svg_template = '''(.*?)'''", svg_content, re.DOTALL)
svg_str = m.group(1)
with open("idle_timeout_candidate.svg", "w") as f:
    f.write(svg_str)

tree = ET.parse("idle_timeout_candidate.svg")
root = tree.getroot()

print("Parsed SVG successfully.")
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    x = elem.attrib.get('x', '0')
    y = elem.attrib.get('y', '0')
    anchor = elem.attrib.get('text-anchor', 'start')
    fs = float(elem.attrib.get('font-size', '24'))
    ff = elem.attrib.get('font-family', 'sans-serif')
    tspans = list(elem.iter('{http://www.w3.org/2000/svg}tspan'))
    if not tspans:
        txt = elem.text.strip() if elem.text else ""
        multiplier = 0.62 if "monospace" in ff else 0.6
        w = len(txt) * fs * multiplier
        print(f"TEXT: '{txt}' | fs={fs} | w={w:.1f} | x={x} y={y} anchor={anchor}")
    else:
        for t in tspans:
            txt = t.text.strip() if t.text else ""
            t_ff = t.attrib.get('font-family', ff)
            multiplier = 0.62 if "monospace" in t_ff else 0.6
            w = len(txt) * fs * multiplier
            tx = t.attrib.get('x', x)
            dy = t.attrib.get('dy', '0')
            print(f"  TSPAN: '{txt}' | fs={fs} | w={w:.1f} | x={tx} dy={dy} anchor={anchor}")
