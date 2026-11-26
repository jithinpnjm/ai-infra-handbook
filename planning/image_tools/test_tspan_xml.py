import xml.etree.ElementTree as ET
import re

xml_snippet = """<svg xmlns="http://www.w3.org/2000/svg">
  <text font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="215" y="160" font-size="30" font-weight="bold" fill="#207448">Collect as you go: </tspan>
    <tspan x="95" y="215">incident log with UTC timeline, observations, </tspan>
    <tspan x="95" dy="36">commands run, changes made, who did what; </tspan>
  </text>
</svg>"""

root = ET.fromstring(xml_snippet)
elem = root.find('{http://www.w3.org/2000/svg}text')
full_text = "".join(elem.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)
print("full_text:", repr(full_text))
fs = float(elem.attrib.get('font-size'))
print("base font size:", fs)
for tsp in elem.findall('{http://www.w3.org/2000/svg}tspan'):
    tfs = tsp.attrib.get('font-size')
    print("tspan font size:", tfs)
