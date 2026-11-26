import xml.etree.ElementTree as ET
import re

svg_snippet = """
<svg xmlns="http://www.w3.org/2000/svg">
  <text font-family="sans-serif" font-size="24">
    <tspan x="280" dy="0"><tspan font-family="monospace">traceroute</tspan> shows only the </tspan>
    <tspan x="280" dy="32">forward path; the return </tspan>
    <tspan x="280" dy="32">path can differ and the round </tspan>
    <tspan x="280" dy="32">trip includes it; run <tspan font-family="monospace">mtr</tspan> </tspan>
    <tspan x="280" dy="32">from both ends</tspan>
  </text>
</svg>
"""

root = ET.fromstring(svg_snippet)
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    print("Extracted text:", repr(full_text))

expected = "traceroute shows only the forward path; the return path can differ and the round trip includes it; run mtr from both ends"
print("Matches?", full_text == expected)
