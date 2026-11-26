import xml.etree.ElementTree as ET
import re

svg_snippet_nospace = '''<text font-family="sans-serif" font-size="24"><tspan x="100" dy="0">_start, </tspan><tspan x="100" dy="30">__libc_</tspan><tspan x="100" dy="30">start_main, </tspan><tspan x="100" dy="30">main</tspan></text>'''

elem = ET.fromstring(svg_snippet_nospace)
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(f"Full text no space: '{full_text}'")
assert full_text == "_start, __libc_start_main, main"
print("MATCHES EXACTLY!")
