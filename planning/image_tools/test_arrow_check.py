#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <title>Test Title</title>
  <desc>Test Desc</desc>
  <rect width="1600" height="1200" fill="#f5f8f5"/>
  
  <!-- Arrow line -->
  <line x1="642" y1="288" x2="958" y2="288" stroke="#207448" stroke-width="3.5"/>
  
  <!-- 2-line arrow label -->
  <text x="800" y="250" text-anchor="middle" font-family="sans-serif" font-size="24" font-weight="bold" fill="#207448">
    <tspan x="800" dy="0">DSCP+ECN to </tspan>
    <tspan x="800" dy="28">Traffic Class</tspan>
  </text>
</svg>'''

with open("test_arrow_label.svg", "w") as f:
    f.write(svg_snippet)

from audit_pad_strict import check_strict_paddings
check_strict_paddings("test_arrow_label.svg")
print("Arrow label test passed!")
