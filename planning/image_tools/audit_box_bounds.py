import re
import xml.etree.ElementTree as ET

with open("output.svg") as f:
    svg_content = f.read()

root = ET.fromstring(svg_content)

# Define font width factors
# sans: 0.6 * size
# mono: 0.62 * size

# Let's inspect all <rect> elements that act as content boxes:
rects = [el for el in root.iter() if el.tag.split('}')[-1] == 'rect' and el.attrib.get('x') == '40']
for r in rects:
    y = float(r.attrib['y'])
    h = float(r.attrib['h'] if 'h' in r.attrib else r.attrib['height'])
    print(f"Content box at y={y}, height={h}, bottom={y+h}")

# Check distances between consecutive content boxes:
for i in range(len(rects) - 1):
    b1_bot = float(rects[i].attrib['y']) + float(rects[i].attrib['height'])
    b2_top = float(rects[i+1].attrib['y'])
    gap = b2_top - b1_bot
    print(f"Gap between box {i+1} and box {i+2}: {gap}px")
    assert gap >= 40, f"Gap {gap} < 40px!"

# Check bottom margin:
last_bot = float(rects[-1].attrib['y']) + float(rects[-1].attrib['height'])
bot_margin = 1200 - last_bot
print(f"Bottom margin: {bot_margin}px")
assert bot_margin >= 40, f"Bottom margin {bot_margin} < 40px!"

# Check top margin:
title_top = 65 - 48*0.75 # ~29
print(f"Top margin: {title_top}px")
