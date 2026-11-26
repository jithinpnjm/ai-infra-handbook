import xml.etree.ElementTree as ET
import re

svg_snippet = '''
<text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
  <tspan x="116" y="100" font-size="30" font-weight="bold">1 Primary versus data plane: </tspan>
  <tspan x="638" y="100" font-size="24">eth0 for control, secondary RDMA</tspan>
  <tspan x="116" y="126" font-size="24">NICs for GPU and storage traffic</tspan>
</text>
'''
root = ET.fromstring(svg_snippet)
full_text = "".join(root.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)
print("full_text:", full_text)
expected = "1 Primary versus data plane: eth0 for control, secondary RDMA NICs for GPU and storage traffic"
assert full_text == expected, f"Mismatch!\nGot: {full_text}\nExp: {expected}"
print("PERFECT MATCH!")
