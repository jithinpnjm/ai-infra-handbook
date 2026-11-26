import re

content = open("solve_perfect_svg.py").read()

# Change y="210" to y="222" for Col 3 title
content = content.replace(
    'svg.append(\'    <text x="1175" y="210" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">\')',
    'svg.append(\'    <text x="1175" y="222" font-family="sans-serif" font-size="30" font-weight="bold" fill="#207448">\')'
)

# And dy="32"
content = content.replace(
    'svg.append(\'      <tspan x="1175" dy="34">how fairly under</tspan>\')\n    svg.append(\'      <tspan x="1175" dy="34">contention?</tspan>\')',
    'svg.append(\'      <tspan x="1175" dy="32">how fairly under</tspan>\')\n    svg.append(\'      <tspan x="1175" dy="32">contention?</tspan>\')'
)

# Card 1 in Col 3 and all cols: let's make y = 295, h = 160
# Let's check text y in Col 3 Card 1: text at y = 338 instead of 352
content = content.replace(
    'svg.append(\'    <text x="1122" y="352" font-family="monospace" font-size="24" fill="#303a36">\')',
    'svg.append(\'    <text x="1122" y="338" font-family="monospace" font-size="24" fill="#303a36">\')'
)

# In Col 1 Card 1: rect y = 295, h = 160, text at y = 328
content = content.replace(
    'svg.append(\'    <rect x="60" y="285" width="440" height="168" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="60" y="295" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# In Col 2 Card 1: rect y = 295, h = 160
content = content.replace(
    'svg.append(\'    <rect x="580" y="285" width="440" height="168" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="580" y="295" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# In Col 3 Card 1: rect y = 295, h = 160
content = content.replace(
    'svg.append(\'    <rect x="1100" y="285" width="440" height="168" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="1100" y="295" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# In Col 1 Card 2 (Picture): y = 470, h = 75
content = content.replace(
    'svg.append(\'    <rect x="60" y="465" width="440" height="76" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="60" y="470" width="440" height="75" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# In Col 2 Card 2 (Picture): y = 470, h = 155
content = content.replace(
    'svg.append(\'    <rect x="580" y="465" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="580" y="470" width="440" height="155" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# In Col 3 Card 2 (Picture): y = 470, h = 155
content = content.replace(
    'svg.append(\'    <rect x="1100" y="465" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="1100" y="470" width="440" height="155" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# Bottom bar: height 64 (y = 1096..1160) so pad_t and pad_b >= 16
content = content.replace(
    'svg.append(\'    <rect x="40" y="1100" width="1520" height="60" rx="10" fill="#207448"/>\')',
    'svg.append(\'    <rect x="40" y="1096" width="1520" height="64" rx="10" fill="#207448"/>\')'
)

open("solve_perfect_svg.py", "w").write(content)
print("Updated solve_perfect_svg.py successfully!")
