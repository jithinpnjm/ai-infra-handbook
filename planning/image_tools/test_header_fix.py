#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Test 2-line header box with audit_pad_strict

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="1200" viewBox="0 0 1600 1200">
  <title>Test</title>
  <desc>Test</desc>
  <rect width="1600" height="1200" fill="#f5f8f5"/>
  
  <rect x="58" y="116" width="584" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="130" y="150">IPv4 header, </tspan>
    <tspan x="130" y="184">20 bytes minimum</tspan>
  </text>

  <rect x="958" y="116" width="584" height="80" rx="10" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">
    <tspan x="1030" y="150">IPv6 header, </tspan>
    <tspan x="1030" y="184">40 bytes fixed</tspan>
  </text>
</svg>'''

with open("test_header_fix.svg", "w") as f:
    f.write(svg_snippet)

from audit_pad_strict import check_strict_paddings
check_strict_paddings("test_header_fix.svg")
