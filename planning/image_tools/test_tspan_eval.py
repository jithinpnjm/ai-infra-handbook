import xml.etree.ElementTree as ET
import re

svg_snippet = """<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24" x="100" y="200">
    <tspan x="100" dy="0">slurmd not responding</tspan>
    <tspan x="100" dy="30">(SlurmdTimeout) / admin</tspan>
  </text>
</svg>"""

root = ET.fromstring(svg_snippet)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    print(f"Extracted: '{full_text}'")
    assert full_text == "slurmd not responding (SlurmdTimeout) / admin"
print("SUCCESS!")
