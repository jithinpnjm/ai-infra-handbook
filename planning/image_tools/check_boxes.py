#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

tree = ET.parse("test_eui64.svg")
root = tree.getroot()

# Let's inspect all boxes and all text elements
boxes = []
for g in root.iter('{http://www.w3.org/2000/svg}g'):
    gid = g.attrib.get('id', '')
    rect = g.find('{http://www.w3.org/2000/svg}rect')
    if rect is not None:
        rx = float(rect.attrib['x'])
        ry = float(rect.attrib['y'])
        rw = float(rect.attrib['width'])
        rh = float(rect.attrib['height'])
        boxes.append((gid, rx, ry, rw, rh))

for b in boxes:
    print(f"Box {b[0]}: x={b[1]}, y={b[2]}, w={b[3]}, h={b[4]}")
