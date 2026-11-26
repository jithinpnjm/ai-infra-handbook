import re

svg_snippet = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1600 1200" width="1600" height="1200">
  <!-- Host Box -->
  <rect x="845" y="245" width="690" height="195" rx="12" fill="#ffffff" stroke="#207448" stroke-width="2"/>
  <text x="935" y="288" font-family="sans-serif" font-size="30" font-weight="bold" fill="#303a36">64 CPUs</text>

  <!-- Container Box -->
  <rect x="865" y="310" width="650" height="120" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>
  <text x="885" y="348" font-family="monospace" font-size="24" font-weight="bold" fill="#303a36">cpu.max = 200000 100000 (2 CPUs)</text>

  <!-- Runtime reads nproc = 64 -->
  <rect x="885" y="358" width="220" height="56" rx="8" fill="#fff9f5" stroke="#db8129" stroke-width="2.5"/>
  <text x="995" y="395" text-anchor="middle" font-family="monospace" font-size="24" font-weight="bold" fill="#db8129">nproc = 64</text>
</svg>'''

with open("test_nproc.svg", "w") as f:
    f.write(svg_snippet)

from audit_pad_strict import check_strict_paddings
check_strict_paddings("test_nproc.svg")
