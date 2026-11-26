#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-family="monospace" font-size="24" fill="#207448">
    <tspan x="100" dy="0">metrics.k8s.io </tspan>
    <tspan x="100" dy="30" font-family="sans-serif" font-size="24" fill="#303a36">per container</tspan>
  </text>
</svg>'''

root = ET.fromstring(svg_snippet)
elem = root.find('{http://www.w3.org/2000/svg}text')
full_text = "".join(elem.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)
print("Result text:", repr(full_text))
target = "metrics.k8s.io per container"
print("Matches target?", full_text == target)
