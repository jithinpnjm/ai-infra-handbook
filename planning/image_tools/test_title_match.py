#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text x="800" y="48" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">IPv4 and IPv6 headers side by side: </tspan>
    <tspan x="800" dy="54">what moved, what went away</tspan>
  </text>
</svg>'''

root = ET.fromstring(svg_snippet)
txt_el = root.find('{http://www.w3.org/2000/svg}text')
full_text = "".join(txt_el.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)
print("Extracted title:", repr(full_text))
assert full_text == "IPv4 and IPv6 headers side by side: what moved, what went away"
print("TITLE MATCHES EXACTLY!")
