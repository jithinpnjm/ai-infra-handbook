import xml.etree.ElementTree as ET
import re

# Let's test the text extraction behavior
test_xml = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="26" font-family="sans-serif">
    <tspan font-weight="bold" fill="#207448">Training, multi-GPU, performance-sensitive: </tspan>
    <tspan font-family="monospace" fill="#303a36">whole GPUs, never share</tspan>
  </text>
</svg>'''

root = ET.fromstring(test_xml)
elem = root.find('.//{http://www.w3.org/2000/svg}text')
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(f"Extracted: '{full_text}'")
assert full_text == "Training, multi-GPU, performance-sensitive: whole GPUs, never share"
print("SUCCESS!")
