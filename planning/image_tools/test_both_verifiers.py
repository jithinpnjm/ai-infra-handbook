import xml.etree.ElementTree as ET
import re

svg_str = """<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24" x="100" y="200">slurmd not responding (SlurmdTimeout) / admin</text>
</svg>"""

root = ET.fromstring(svg_str)

# 1. test_rules.py approach:
texts = []
def walk(el):
    if el.tag.endswith('text') or el.tag.endswith('tspan'):
        t = (el.text or "").strip()
        if t: texts.append(t)
    for child in el: walk(child)

walk(root)

# 2. verify_candidate.py approach:
found_texts = []
for elem in root.iter('{http://www.w3.org/2000/svg}text'):
    full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
    found_texts.append(full_text)

req = "slurmd not responding (SlurmdTimeout) / admin"
print(f"test_rules check: count = {texts.count(req)}")
print(f"verify_candidate check: count = {found_texts.count(req)}")
assert texts.count(req) == 1
assert found_texts.count(req) == 1
print("BOTH PASS 100%!")
