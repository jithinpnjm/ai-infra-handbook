#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = """<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24"><tspan x="60" dy="0">1 allow the required ICMP messages </tspan><tspan x="60" dy="30">(IPv4 type 3 code 4 Fragmentation Needed, </tspan><tspan x="60" dy="30">IPv6 type 2 Packet Too Big)</tspan></text>
</svg>"""

root = ET.fromstring(svg_snippet)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    print("Parsed text:", repr(full_text))
