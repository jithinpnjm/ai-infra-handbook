# Print all rects and their parents/transforms
import xml.etree.ElementTree as ET

tree = ET.parse('output_candidate.svg')
root = tree.getroot()

for elem in root.iter('{http://www.w3.org/2000/svg}rect'):
    x = float(elem.attrib.get('x', '0'))
    y = float(elem.attrib.get('y', '0'))
    w = float(elem.attrib.get('width', '0'))
    h = float(elem.attrib.get('height', '0'))
    print(f"Rect: x={x}, y={y}, w={w}, h={h}")
