# Test wrapping of bad ELF interpreter inside width 340 (inner card width = 310)

def text_width(s, fs=24, is_mono=False):
    rate = 0.62 if is_mono else 0.60
    return len(s) * fs * rate

# Text: "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)"
# Can we break into lines?
lines = [
    ("bad ELF interpreter /", False),
    ("not found for a file", False),
    ("that exists", False),
    ("(glibc binary on", False),
    ("Alpine musl:", False),
    ("/lib64/ld-linux-", True),
    ("x86-64.so.2", True),
    ("missing)", False)
]

full = "bad ELF interpreter / not found for a file that exists (glibc binary on Alpine musl: /lib64/ld-linux-x86-64.so.2 missing)"
reconstructed = " ".join(line for line, _ in lines)
print(f"Full:          '{full}'")
print(f"Reconstructed: '{reconstructed}'")

# But wait! Look at:
# "/lib64/ld-linux-" and "x86-64.so.2"
# In SVG:
# If written as:
# <text font-family="sans-serif" font-size="24">
#   <tspan x="cx" dy="0">bad ELF interpreter / </tspan>
#   <tspan x="cx" dy="30">not found for a file </tspan>
#   <tspan x="cx" dy="30">that exists </tspan>
#   <tspan x="cx" dy="30">(glibc binary on </tspan>
#   <tspan x="cx" dy="30">Alpine musl: </tspan>
#   <tspan x="cx" dy="30" font-family="monospace">/lib64/ld-linux-</tspan><tspan x="cx" dy="30" font-family="monospace">x86-64.so.2 </tspan>
#   <tspan x="cx" dy="30">missing)</tspan>
# </text>
#
# Let's test what ET.itertext() gives:
import xml.etree.ElementTree as ET
import re

svg_xml = '''<text font-family="sans-serif" font-size="24">
  <tspan x="600" dy="0">bad ELF interpreter / </tspan>
  <tspan x="600" dy="30">not found for a file </tspan>
  <tspan x="600" dy="30">that exists </tspan>
  <tspan x="600" dy="30">(glibc binary on </tspan>
  <tspan x="600" dy="30">Alpine musl: </tspan>
  <tspan x="600" dy="30" font-family="monospace">/lib64/ld-linux-</tspan><tspan x="600" dy="30" font-family="monospace">x86-64.so.2 </tspan>
  <tspan x="600" dy="30">missing)</tspan>
</text>'''

elem = ET.fromstring(svg_xml)
parsed_text = re.sub(r'\s+', ' ', "".join(elem.itertext()).strip())
print(f"\nParsed text: '{parsed_text}'")
assert parsed_text == full
print("MATCHES EXACTLY TOKEN FOR TOKEN!")

print("\nChecking padding in box of width 310:")
for line, is_mono in lines:
    w = text_width(line, 24, is_mono)
    pad = (310 - w) / 2
    print(f"  '{line}': w={w:.1f}px, pad={pad:.1f}px [{'PASS' if pad >= 16 else 'FAIL'}]")
    assert pad >= 16
