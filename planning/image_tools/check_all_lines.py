import xml.etree.ElementTree as ET

# Update test.svg with the wrapped Card 1
with open("test.svg") as f:
    c = f.read()

c = c.replace(
    '<text x="82" y="286" font-family="sans-serif" font-size="24" fill="#303a36">linear walk of <tspan font-family="monospace">KUBE-SERVICES,</tspan> O(n)</text>',
    """<text x="82" y="286" font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="82" dy="0">linear walk of</tspan>
    <tspan x="82" dy="34"><tspan font-family="monospace">KUBE-SERVICES,</tspan> O(n)</tspan>
  </text>"""
)

with open("test.svg", "w") as f:
    f.write(c)

print("Card 1 updated. Now testing all text lines...")
