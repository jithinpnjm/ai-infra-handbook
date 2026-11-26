#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_hpa_metrics.svg")
root = tree.getroot()

# Let's inspect all rects and texts to check visual paddings and alignments
rects = []
for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', 0))
    y = float(elem.attrib.get('y', 0))
    w = float(elem.attrib.get('width', 0))
    h = float(elem.attrib.get('height', 0))
    rects.append((x, y, w, h, elem.attrib.get('fill', '')))

print(f"Total rects: {len(rects)}")
for r in rects[:15]:
    print(r)
