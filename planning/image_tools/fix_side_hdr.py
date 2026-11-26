with open("test_adjust_paddings.py") as f:
    code = f.read()

code = code.replace(
    """    <rect x="1220" y="285" width="340" height="65" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1390" y="312" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
      <tspan x="1390" dy="0">names assigned </tspan>
      <tspan x="1390" dy="26">so far</tspan>
    </text>""",
    """    <rect x="1220" y="280" width="340" height="75" rx="10" fill="#e8f1ea" stroke="#207448" stroke-width="2" />
    <text x="1390" y="318" text-anchor="middle" font-family="sans-serif" font-size="25" font-weight="bold" fill="#303a36">
      <tspan x="1390" dy="0">names assigned </tspan>
      <tspan x="1390" dy="25">so far</tspan>
    </text>"""
)

with open("test_adjust_paddings.py", "w") as f:
    f.write(code)

import os
os.system("python3 test_adjust_paddings.py")
