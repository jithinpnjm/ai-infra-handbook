import xml.etree.ElementTree as ET
import re

svg_snippet = '''
<svg xmlns="http://www.w3.org/2000/svg">
  <text x="40" y="75" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="40" dy="0">Five AI fabrics against the layers:</tspan>
    <tspan x="40" dy="55">which one carries what</tspan>
  </text>
</svg>
'''
root = ET.fromstring(svg_snippet)
for text_el in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(text_el.itertext())
    normalized = re.sub(r'\s+', ' ', full_text).strip()
    print("Normalized text:", normalized)
    assert normalized == "Five AI fabrics against the layers: which one carries what"
print("MATCHES EXACTLY!")
