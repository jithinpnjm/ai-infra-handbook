import xml.etree.ElementTree as ET
import re

svg_snippet = """
<svg xmlns="http://www.w3.org/2000/svg">
  <text x="800" y="68" text-anchor="middle" font-family="sans-serif" font-size="48" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">An SLO and alerting platform </tspan>
    <tspan x="800" dy="58">for 1,000 endpoints [my addition]</tspan>
  </text>
  <text x="190" y="340" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="190" dy="0">SLO file </tspan>
    <tspan x="190" dy="40">per endpoint</tspan>
  </text>
  <text x="495" y="340" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="495" dy="0">Rule </tspan>
    <tspan x="495" dy="40">generator</tspan>
  </text>
  <text x="800" y="340" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Recording </tspan>
    <tspan x="800" dy="40">rules</tspan>
  </text>
  <text x="1105" y="340" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="1105" dy="0">Burn-rate </tspan>
    <tspan x="1105" dy="40">alerts</tspan>
  </text>
  <text x="1410" y="340" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="1410" dy="0">Routing by </tspan>
    <tspan x="1410" dy="40">owner</tspan>
  </text>
  <text x="800" y="710" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">
    <tspan x="800" dy="0">Metrics </tspan>
    <tspan x="800" dy="40">store</tspan>
  </text>
</svg>
"""

root = ET.fromstring(svg_snippet)
text_elements = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = "".join(elem.itertext()).strip()
    full_text = re.sub(r'\s+', ' ', full_text)
    fs = float(elem.attrib.get('font-size', 30))
    text_elements.append((full_text, fs))

expected_labels = [
    "An SLO and alerting platform for 1,000 endpoints [my addition]",
    "SLO file per endpoint",
    "Rule generator",
    "Recording rules",
    "Burn-rate alerts",
    "Routing by owner",
    "Metrics store"
]

found_texts = [t for t, fs in text_elements]
for i, (t, fs) in enumerate(text_elements, 1):
    print(f"{i}. [{fs:2.0f}px] '{t}'")

assert len(found_texts) == len(expected_labels)
for exp in expected_labels:
    assert found_texts.count(exp) == 1
print("All assertions passed!")
