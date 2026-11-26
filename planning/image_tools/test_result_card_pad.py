import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <!-- Result Card -->
  <rect x="845" y="460" width="690" height="140" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  
  <text font-family="sans-serif" font-size="24" fill="#303a36">
    <tspan x="940" y="496">the quota is burned early</tspan>
    <tspan x="940" y="524">in each period, then every</tspan>
    <tspan x="940" y="552">thread pauses even though</tspan>
    <tspan x="940" y="580">other CPUs are idle</tspan>
  </text>
</svg>'''

with open("test_result.svg", "w") as f:
    f.write(svg_snippet)

from audit_pad_strict import check_strict_paddings
check_strict_paddings("test_result.svg")
