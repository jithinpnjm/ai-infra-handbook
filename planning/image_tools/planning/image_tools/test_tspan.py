#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24">
    <tspan x="100" dy="0">CPU or memory average utilisation </tspan>
    <tspan x="100" dy="30">relative to requests, or average value</tspan>
  </text>
</svg>'''

root = ET.fromstring(svg_snippet)
elem = root.find('{http://www.w3.org/2000/svg}text')
full_text = "".join(elem.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)
print("Result text:", repr(full_text))
target = "CPU or memory average utilisation relative to requests, or average value"
print("Matches target?", full_text == target)
