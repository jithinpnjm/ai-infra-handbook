"""Inspect existing SVG issues."""
import xml.etree.ElementTree as ET

tree = ET.parse("../../docs/part-05-kubernetes/img/m5-29-1.svg")
root = tree.getroot()

# Find all text elements
texts = root.findall(".//{http://www.w3.org/2000/svg}text")
print(f"Total text elements in m5-29-1.svg: {len(texts)}")
for t in texts:
    tspans = t.findall("{http://www.w3.org/2000/svg}tspan")
    if tspans:
        print("Text with tspans:", [s.text for s in tspans])
    else:
        print("Text:", t.text)
