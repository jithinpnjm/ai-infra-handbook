import re

content = open("solve_perfect_svg.py").read()

# Update Card 1 y to 285, h to 170 in all columns
content = content.replace(
    'svg.append(\'    <rect x="60" y="295" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="60" y="285" width="440" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)
content = content.replace(
    'svg.append(\'    <rect x="580" y="295" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="580" y="285" width="440" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)
content = content.replace(
    'svg.append(\'    <rect x="1100" y="295" width="440" height="160" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')',
    'svg.append(\'    <rect x="1100" y="285" width="440" height="170" rx="10" fill="#ffffff" stroke="#207448" stroke-width="1.5"/>\')'
)

# Bottom strip: y = 980, h = 100
content = content.replace(
    'svg.append(\'    <rect x="40" y="985" width="1520" height="95" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>\')',
    'svg.append(\'    <rect x="40" y="980" width="1520" height="100" rx="12" fill="#e8f1ea" stroke="#207448" stroke-width="2"/>\')'
)
# Bottom strip text at y = 1024
content = content.replace(
    'svg.append(\'    <text x="130" y="1030" font-family="sans-serif" font-size="24" fill="#303a36">\')',
    'svg.append(\'    <text x="130" y="1024" font-family="sans-serif" font-size="24" fill="#303a36">\')'
)

# Bottom bar: y = 1094, h = 66
content = content.replace(
    'svg.append(\'    <rect x="40" y="1096" width="1520" height="64" rx="10" fill="#207448"/>\')',
    'svg.append(\'    <rect x="40" y="1094" width="1520" height="66" rx="10" fill="#207448"/>\')'
)
# Bottom bar text at y = 1137
content = content.replace(
    'svg.append(\'    <text x="800" y="1139" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Choose placement, ceiling or proportion by what the job needs</text>\')',
    'svg.append(\'    <text x="800" y="1137" text-anchor="middle" font-family="sans-serif" font-size="26" font-weight="bold" fill="#ffffff">Choose placement, ceiling or proportion by what the job needs</text>\')'
)

open("solve_perfect_svg.py", "w").write(content)
print("Updated solve_perfect_svg.py")
