import xml.etree.ElementTree as ET
import re

svg_snippet = '''
<svg xmlns="http://www.w3.org/2000/svg">
  <text font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="105" y="470" font-size="30" font-weight="bold">Write the extension file srv.ext: </tspan>
    <tspan x="105" y="500" font-family="monospace" font-size="24">subjectAltName=DNS:api.lab.internal,</tspan>
    <tspan x="105" y="530" font-family="monospace" font-size="24">DNS:*.lab.internal,IP:10.0.0.5; </tspan>
    <tspan x="105" y="560" font-family="monospace" font-size="24">extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE</tspan>
  </text>
</svg>
'''

root = ET.fromstring(svg_snippet)
txt = root.find('{http://www.w3.org/2000/svg}text')
full_text = "".join(txt.itertext()).strip()
full_text = re.sub(r'\s+', ' ', full_text)

expected = "Write the extension file srv.ext: subjectAltName=DNS:api.lab.internal,DNS:*.lab.internal,IP:10.0.0.5; extendedKeyUsage=serverAuth; basicConstraints=CA:FALSE"
print("Matches expected?", full_text == expected)
if full_text != expected:
    print("Found:   ", repr(full_text))
    print("Expected:", repr(expected))
