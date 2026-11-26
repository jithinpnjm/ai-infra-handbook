import xml.etree.ElementTree as ET
import re

svg_snippet = '''
<text font-family="sans-serif" font-size="24">
  <tspan x="100" dy="0">_start, </tspan>
  <tspan x="100" dy="30">__libc_</tspan>
  <tspan x="100" dy="30">start_main, </tspan>
  <tspan x="100" dy="30">main</tspan>
</text>
'''

elem = ET.fromstring(svg_snippet)
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(f"Full text with space: '{full_text}'")

svg_snippet_exact = '''
<text font-family="sans-serif" font-size="24">
  <tspan x="100" dy="0">_start, </tspan>
  <tspan x="100" dy="30">__libc_start_main, </tspan>
  <tspan x="100" dy="30">main</tspan>
</text>
'''
elem_exact = ET.fromstring(svg_snippet_exact)
full_text_exact = re.sub(r'\s+', ' ', "".join(elem_exact.itertext()).strip())
print(f"Full text exact: '{full_text_exact}'")
