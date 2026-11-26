import re

with open("generate_svg.py") as f:
    s = f.read()

# In recipe-2:
old_r2 = '''    <!-- Recipe 2 Title (Two lines beside icon) -->
    <text x="904" y="440" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="904" dy="0">multi-node, one process</tspan>
      <tspan x="904" dy="32">per GPU (PyTorch):</tspan>
    </text>'''

new_r2 = '''    <!-- Recipe 2 Title (Two lines beside icon) -->
    <text x="904" y="440" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="bold" fill="#207448">multi-node, one process</text>
    <text x="904" y="472" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="bold" fill="#207448">per GPU (PyTorch):</text>'''

# In recipe-3:
old_r3 = '''    <!-- Recipe 3 Title (Two lines beside icon) -->
    <text x="130" y="688" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="bold" fill="#207448">
      <tspan x="130" dy="0">several independent tasks</tspan>
      <tspan x="130" dy="32">in one allocation:</tspan>
    </text>'''

new_r3 = '''    <!-- Recipe 3 Title (Two lines beside icon) -->
    <text x="130" y="688" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="bold" fill="#207448">several independent tasks</text>
    <text x="130" y="720" font-family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif" font-size="26" font-weight="bold" fill="#207448">in one allocation:</text>'''

s = s.replace(old_r2, new_r2).replace(old_r3, new_r3)

with open("generate_svg.py", "w") as f:
    f.write(s)

print("Applied fix_lines")
