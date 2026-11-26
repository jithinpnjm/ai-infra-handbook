#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="30">
    <tspan x="100" dy="0">duplex.example.com </tspan>
    <tspan x="100" dy="36">(client)</tspan>
  </text>
</svg>'''

root = ET.fromstring(svg_snippet)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    print(f"Extracted: '{full_text}'")
    assert full_text == "duplex.example.com (client)"
print("PASS!")
