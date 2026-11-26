import xml.etree.ElementTree as ET
import re

svg_snippet = """<svg xmlns="http://www.w3.org/2000/svg">
  <text x="142" y="148" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="142" dy="0">PID 1 is </tspan><tspan font-family="monospace">/bin/sh</tspan><tspan> or a process</tspan>
    <tspan x="142" dy="38">with no SIGTERM handler</tspan>
  </text>
</svg>"""

root = ET.fromstring(svg_snippet)
elem = root.find('{http://www.w3.org/2000/svg}text')
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(f"Extracted: '{full_text}'")
expected = "PID 1 is /bin/sh or a process with no SIGTERM handler"
assert full_text == expected, f"Mismatch: got '{full_text}'"
print("SUCCESS!")
