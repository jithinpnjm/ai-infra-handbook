import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_output.svg")
root = tree.getroot()

# Let's inspect the positions of all rects and lines
rects = []
for el in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(el.get('x', 0))
    y = float(el.get('y', 0))
    w = float(el.get('width', 0))
    h = float(el.get('height', 0))
    gid = el.get('id', '')
    rects.append((x, y, w, h, gid))

print("Rectangles count:", len(rects))
for r in rects:
    print(r)
