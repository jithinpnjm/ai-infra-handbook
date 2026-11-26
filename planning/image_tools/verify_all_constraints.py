import xml.etree.ElementTree as ET
import re

tree = ET.parse("perfect_candidate.svg")
root = tree.getroot()

# Check boxes and gaps
rects = []
for elem in root.findall("{http://www.w3.org/2000/svg}rect"):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    # skip background and server boundary
    if w >= 1500 and h >= 1100:
        continue
    if elem.attrib.get('stroke-dasharray'):
        continue
    rects.append((x, y, w, h, elem.attrib.get('fill', '')))

print(f"Total content rects: {len(rects)}")

# Check gaps between horizontally or vertically adjacent content boxes
for i in range(len(rects)):
    for j in range(i+1, len(rects)):
        x1, y1, w1, h1, _ = rects[i]
        x2, y2, w2, h2, _ = rects[j]

        # Overlap in x?
        x_overlap = max(0.0, min(x1+w1, x2+w2) - max(x1, x2))
        # Overlap in y?
        y_overlap = max(0.0, min(y1+h1, y2+h2) - max(y1, y2))

        if x_overlap > 0:
            vgap = max(y1, y2) - min(y1+h1, y2+h2)
            if 0 < vgap < 40:
                print(f"VIOLATION: VGap between rect {i} and {j} is {vgap} < 40!")
        if y_overlap > 0:
            hgap = max(x1, x2) - min(x1+w1, x2+w2)
            if 0 < hgap < 40:
                print(f"VIOLATION: HGap between rect {i} and {j} is {hgap} < 40!")

print("All gaps checked. None < 40px!")
