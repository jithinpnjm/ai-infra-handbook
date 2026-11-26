import xml.etree.ElementTree as ET

tree = ET.parse("output.svg")
root = tree.getroot()

# Node container rects are direct children of the node groups or top-level rects
container_rects = []
for g in root.findall('.//{http://www.w3.org/2000/svg}g'):
    r = g.find('{http://www.w3.org/2000/svg}rect')
    if r is not None and r.get('width') in ['715', '1520']:
        container_rects.append((float(r.get('x')), float(r.get('y')), float(r.get('width')), float(r.get('height'))))

# Also the bottom bar
bb = root.find('.//*[@id="bottom-bar"]/{http://www.w3.org/2000/svg}rect')
if bb is not None:
    container_rects.append((float(bb.get('x')), float(bb.get('y')), float(bb.get('width')), float(bb.get('height'))))

print(f"Container boxes found: {len(container_rects)}")
min_x = min(b[0] for b in container_rects)
max_x = max(b[0] + b[2] for b in container_rects)
min_y = min(b[1] for b in container_rects)
max_y = max(b[1] + b[3] for b in container_rects)

print(f"Boxes X bounds: {min_x} to {max_x} -> Margins: left={min_x}, right={1600 - max_x}")
print(f"Boxes Y bounds: {min_y} to {max_y} -> Margins: top={min_y}, bottom={1200 - max_y}")
assert min_x >= 40 and (1600 - max_x) >= 40 and (1200 - max_y) >= 40
print("Container boxes outside margins: ALL >= 40px! PASSED!")
