#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''
<text x="950" y="470" font-family="monospace" font-size="24" fill="#303a36">
  <tspan x="950" dy="0">train.py -&gt; </tspan><tspan x="950" dy="32">inode C</tspan>
</text>
'''

el = ET.fromstring(svg_snippet)
full_text = re.sub(r'\s+', ' ', "".join(el.itertext()).strip())
raw_join = "".join(el.itertext()).strip()

print("full_text:", repr(full_text))
print("raw_join: ", repr(raw_join))

expected = "train.py -> inode C"
assert full_text == expected, f"Failed: {repr(full_text)} != {repr(expected)}"
print("MATCHES EXACTLY!")
