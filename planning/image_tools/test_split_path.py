import xml.etree.ElementTree as ET
import re

svg_snippet = '''<text font-family="monospace" font-size="24">
  <tspan x="800" dy="0">bad ELF interpreter / not found for a file </tspan>
  <tspan x="800" dy="32">that exists (glibc binary on Alpine musl: </tspan>
  <tspan x="800" dy="32">/lib64/ld-linux-</tspan><tspan x="800" dy="32">x86-64.so.2 </tspan>
  <tspan x="800" dy="32">missing)</tspan>
</text>'''

elem = ET.fromstring(svg_snippet)
full_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
expected = "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)"

print(f"Reconstructed: '{full_text}'")
print(f"Expected:      '{expected}'")
assert full_text == expected
print("MATCHES 100% PERFECTLY TOKEN FOR TOKEN!")
