import xml.etree.ElementTree as ET

svg_str = """<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24" x="100" y="200">
    <tspan x="100" dy="0">slurmd not responding</tspan>
    <tspan x="100" dy="30">(SlurmdTimeout) / admin</tspan>
  </text>
</svg>"""

root = ET.fromstring(svg_str)

# Exactly as in test_rules.py:
texts = []
font_sizes = []
def walk(el):
    if el.tag.endswith('text') or el.tag.endswith('tspan'):
        t = (el.text or "").strip()
        if t:
            texts.append(t)
            fs = el.attrib.get('font-size')
            if fs:
                font_sizes.append((t, int(fs)))
    for child in el:
        walk(child)

walk(root)
print("test_rules extracted texts:")
for t in texts:
    print(f"  '{t}'")

required = "slurmd not responding (SlurmdTimeout) / admin"
print(f"Is '{required}' in texts? {required in texts}")
