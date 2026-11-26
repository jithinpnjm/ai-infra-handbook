import xml.etree.ElementTree as ET

tree = ET.parse("candidate_decision_tree.svg")
root = tree.getroot()
for i, el in enumerate(root.iter('{http://www.w3.org/2000/svg}text'), 1):
    txt = " ".join("".join(el.itertext()).split())
    fs = el.attrib.get('font-size')
    print(f"{i:2d}. [{fs}px] {txt}")
