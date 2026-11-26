import xml.etree.ElementTree as ET
import re

tree = ET.parse("output.svg")
root = tree.getroot()

style_words = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]

# Check all text and tspan elements
bad_matches = []
for elem in root.iter():
    if elem.tag.endswith("text") or elem.tag.endswith("tspan"):
        if elem.text:
            for word in style_words:
                # search for word boundary
                if re.search(r'\b' + word + r'\b', elem.text, re.IGNORECASE):
                    bad_matches.append((elem.tag, elem.text, word))

print(f"Style words found in visible text: {len(bad_matches)}")
for b in bad_matches:
    print("  BAD:", b)
