import re
import xml.etree.ElementTree as ET

snippet = """<svg xmlns="http://www.w3.org/2000/svg">
<text x="70" y="145" font-family="monospace" font-size="24" fill="#303a36">
  <tspan x="70" dy="0">[gpu]</tspan>
  <tspan x="70" dy="32">gpu01 ansible_host=10.0.10.11,</tspan>
  <tspan x="70" dy="32">gpu02 ansible_host=10.0.10.12</tspan>
</text>
</svg>"""

root = ET.fromstring(snippet)
elem = root.find("{http://www.w3.org/2000/svg}text")
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(repr(full_text))
assert full_text == "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12"
print("SUCCESS!")
