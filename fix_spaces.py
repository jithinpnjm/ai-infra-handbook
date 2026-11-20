import xml.etree.ElementTree as ET

with open("lookup_order.svg") as f:
    s = f.read()

# Fix spaces before tspan
s = s.replace('descriptor.__get__<tspan', 'descriptor.__get__ <tspan')
s = s.replace('non-data descriptor or<tspan', 'non-data descriptor or <tspan')
s = s.replace('descriptor.__get__ /<tspan', 'descriptor.__get__ / <tspan')

with open("lookup_order.svg", "w") as f:
    f.write(s)

tree = ET.parse("lookup_order.svg")
root = tree.getroot()
for t in root.iter('{http://www.w3.org/2000/svg}text'):
    full = "".join(t.itertext())
    print(f"  - '{full}'")

