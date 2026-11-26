import xml.etree.ElementTree as ET

# Test standard SVG text with tspans on the same line
svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <title>Ten things to decide for a GPU or HPC pod's network</title>
  <desc>Ten things to decide for a GPU or HPC pod's network</desc>
  <text font-family="system-ui, -apple-system, sans-serif" font-size="24" fill="#303a36">
    <tspan x="120" y="100" font-size="30" font-weight="bold">1 Primary versus data plane: </tspan>
    <tspan font-size="24">eth0 for control, secondary RDMA NICs for GPU and storage traffic</tspan>
  </text>
</svg>'''

root = ET.fromstring(svg)
elem = root.find('{http://www.w3.org/2000/svg}text')
full_text = "".join(elem.itertext()).strip()
print("full_text:", full_text)
assert full_text == "1 Primary versus data plane: eth0 for control, secondary RDMA NICs for GPU and storage traffic"
print("SUCCESS: full_text matches expected string perfectly!")
