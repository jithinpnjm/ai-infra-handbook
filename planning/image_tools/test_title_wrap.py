#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text x="800" y="55" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">resourceVersion versus generation</tspan>
    <tspan x="800" dy="56">versus observedGeneration</tspan>
  </text>
</svg>'''

root = ET.fromstring(svg_snippet)
elem = root.find('{http://www.w3.org/2000/svg}text')
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(f"Extracted: '{full_text}'")
assert full_text == "resourceVersion versus generation versus observedGeneration"
print("SUCCESS!")
