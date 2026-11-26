import xml.etree.ElementTree as ET
import re

# In the SVG file itself, we write:
# double quotes support escapes such as \n, \t and the e-acute character: "line one\nline two" holds a real line break

xml_snippet = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24">
    <tspan x="10" dy="0">double quotes support escapes such as \\n, \\t </tspan>
    <tspan x="10" dy="30">and the e-acute character: </tspan>
    <tspan x="10" dy="30">&quot;line one\\nline two&quot; holds a real line break</tspan>
  </text>
</svg>'''

root = ET.fromstring(xml_snippet)
elem = root.find('{http://www.w3.org/2000/svg}text')
text = re.sub(r'\s+', ' ', ''.join(elem.itertext()).strip())

import json
data = json.load(open('specs/p3_04_04.json'))
spec = data[1]['spec']
expected = [s for s in spec.split("'") if 'double quotes' in s][0]

print('Text from SVG:   ', repr(text))
print('Expected from spec:', repr(expected))
assert text == expected
print("MATCH SUCCESSFUL!")

xml_snippet2 = '''<svg xmlns="http://www.w3.org/2000/svg">
  <text font-size="24">
    <tspan x="10" dy="0">single quotes are literal: </tspan>
    <tspan x="10" dy="30">C:\\temp keeps its backslash; </tspan>
    <tspan x="10" dy="30">only two single quotes escape a quote inside</tspan>
  </text>
  <text font-size="24">
    <tspan x="10" dy="0">spaces only, never tabs: a tab breaks the count even when it looks like two spaces; </tspan>
    <tspan x="10" dy="30">use two spaces per level; key:\\n- a and key:\\n  - a are both valid, </tspan>
    <tspan x="10" dy="30">pick one style across the repository</tspan>
  </text>
</svg>'''

root2 = ET.fromstring(xml_snippet2)
texts = [re.sub(r'\s+', ' ', ''.join(e.itertext()).strip()) for e in root2.findall('{http://www.w3.org/2000/svg}text')]

expected_single = [s for s in spec.split("'") if 'single quotes' in s][0]
expected_indent = [s for s in spec.split("'") if 'spaces only' in s][0]

print('Single quotes match:', texts[0] == expected_single)
print('Indentation match:  ', texts[1] == expected_indent)
assert texts[0] == expected_single
assert texts[1] == expected_indent
print("ALL ESCAPES MATCH!")
