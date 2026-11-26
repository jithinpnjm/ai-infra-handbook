import xml.etree.ElementTree as ET

# Let's inspect all icons in candidate_throttling.svg
tree = ET.parse("candidate_throttling.svg")
root = tree.getroot()

for g in root.iter('{http://www.w3.org/2000/svg}g'):
    tr = g.attrib.get('transform', '')
    if 'translate' in tr:
        print(f"Group {g.attrib.get('id', '')} transform={tr}")
