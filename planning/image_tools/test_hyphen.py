text = """<text>
  <tspan>scheduler, a</tspan>
  <tspan>higher-priority pod</tspan>
  <tspan>needs a place</tspan>
</text>"""
import xml.etree.ElementTree as ET
import re

el = ET.fromstring(text)
s = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
print(f"'{s}'")
assert s == "scheduler, a higher-priority pod needs a place"
print("MATCHES EXACTLY!")
