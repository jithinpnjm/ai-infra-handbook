import xml.etree.ElementTree as ET

xml = '''<text x="1370" y="330" text-anchor="middle" font-family="sans-serif" fill="#303a36"><tspan x="1370" dy="0" font-size="32" font-weight="bold" fill="#207448">Step 6: </tspan><tspan x="1370" dy="44" font-size="28" font-weight="bold">compare with a </tspan><tspan x="1370" dy="42" font-size="28" font-weight="bold">healthy node</tspan></text>'''

elem = ET.fromstring(xml)
res = "".join(elem.itertext()).strip()
print("Result:", repr(res))
assert res == "Step 6: compare with a healthy node"
print("SUCCESS!")
