import xml.etree.ElementTree as ET
import re

tree = ET.parse("candidate_and_or_trap.svg")
root = tree.getroot()

banned = ["orange", "green", "grey", "gray", "bold", "monospace", "arrow"]
for t in root.iter("{http://www.w3.org/2000/svg}text"):
    full = "".join(t.itertext())
    words = re.findall(r"\b[A-Za-z]+\b", full.lower())
    for b in banned:
        if b in words:
            print(f"ERROR: Banned word '{b}' found in '{full}'")
            assert False

print("PASS: No banned styling words in any text element!")
