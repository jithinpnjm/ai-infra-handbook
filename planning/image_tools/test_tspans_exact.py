import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="30"><tspan font-family="sans-serif" font-weight="bold">ad hoc </tspan><tspan font-family="monospace" font-weight="bold">setup with filter=ansible_default_ipv4</tspan></text>
  <text font-size="30"><tspan font-family="sans-serif" font-weight="bold">ad hoc command </tspan><tspan font-family="monospace" font-weight="bold">which python3 with -vvv</tspan></text>
</svg>'''

root = ET.fromstring(svg_snippet)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    print("Found:", repr(full_text))

assert re.sub(r'\s+', ' ', "".join(root[0].itertext()).strip()) == "ad hoc setup with filter=ansible_default_ipv4"
assert re.sub(r'\s+', ' ', "".join(root[1].itertext()).strip()) == "ad hoc command which python3 with -vvv"
print("Exact match verified!")
