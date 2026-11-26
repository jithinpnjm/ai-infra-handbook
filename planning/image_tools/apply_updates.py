import re

with open("final_svg.svg") as f:
    content = f.read()

# 1. card-streetlight flaw
content = content.replace(
    '<rect x="56" y="342" width="568" height="50" rx="8" fill="#fbebe8" stroke="#d93829" stroke-width="1.5" />\n    <text x="72" y="375"',
    '<rect x="56" y="334" width="568" height="56" rx="8" fill="#fbebe8" stroke="#d93829" stroke-width="1.5" />\n    <text x="72" y="374"'
)

# 2. card-random-change flaw
content = content.replace(
    '<rect x="56" y="622" width="568" height="74" rx="8" fill="#fbebe8" stroke="#d93829" stroke-width="1.5" />\n    <text x="72" y="654" font-family="sans-serif" font-size="24" font-weight="bold" fill="#c03020">\n      <tspan x="72" dy="0">unexplained, fragile, may encode</tspan>\n      <tspan x="72" dy="30">workarounds, risk at peak</tspan>',
    '<rect x="56" y="622" width="568" height="80" rx="8" fill="#fbebe8" stroke="#d93829" stroke-width="1.5" />\n    <text x="72" y="662" font-family="sans-serif" font-size="24" font-weight="bold" fill="#c03020">\n      <tspan x="72" dy="0">unexplained, fragile, may encode</tspan>\n      <tspan x="72" dy="30">workarounds, risk at peak</tspan>'
)

# 3. card-blame-someone-else flaw
content = content.replace(
    '<rect x="56" y="924" width="568" height="120" rx="8" fill="#fbebe8" stroke="#d93829" stroke-width="1.5" />\n    <text x="72" y="958" font-family="sans-serif" font-size="24" font-weight="bold" fill="#c03020">\n      <tspan x="72" dy="0">wastes other teams;</tspan>\n      <tspan x="72" dy="32">a ticket bounces for a week;</tspan>\n      <tspan x="72" dy="32">demand screenshots of tools run</tspan>',
    '<rect x="56" y="926" width="568" height="122" rx="8" fill="#fbebe8" stroke="#d93829" stroke-width="1.5" />\n    <text x="72" y="966" font-family="sans-serif" font-size="24" font-weight="bold" fill="#c03020">\n      <tspan x="72" dy="0">wastes other teams;</tspan>\n      <tspan x="72" dy="30">a ticket bounces for a week;</tspan>\n      <tspan x="72" dy="30">demand screenshots of tools run</tspan>'
)

# 4. node-diagnosis-cycle
content = content.replace(
    '<text x="850" y="974" font-family="sans-serif" fill="#303a36">\n      <tspan font-size="30" font-weight="bold" fill="#207448">Diagnosis cycle:</tspan>\n    </text>\n    <text x="850" y="1010" font-family="sans-serif" font-size="24" fill="#303a36">\n      <tspan x="850" dy="0" font-weight="bold">hypothesis, instrumentation, data, hypothesis,</tspan>\n      <tspan x="850" dy="30">quickly so bad theories die early</tspan>',
    '<text x="850" y="978" font-family="sans-serif" fill="#303a36">\n      <tspan font-size="30" font-weight="bold" fill="#207448">Diagnosis cycle:</tspan>\n    </text>\n    <text x="850" y="1014" font-family="sans-serif" font-size="24" fill="#303a36">\n      <tspan x="850" dy="0" font-weight="bold">hypothesis, instrumentation, data, hypothesis,</tspan>\n      <tspan x="850" dy="30">quickly so bad theories die early</tspan>'
)

# 5. bottom-takeaway-bar
content = content.replace(
    '<text x="800" y="1139"',
    '<text x="800" y="1141"'
)

# 6. test-observational
content = content.replace(
    '<text x="1164" y="405" font-family="sans-serif" font-size="24" fill="#303a36">\n      <tspan x="1164" dy="0">watch the system</tspan>\n      <tspan x="1164" dy="30">while it runs</tspan>',
    '<text x="1164" y="403" font-family="sans-serif" font-size="24" fill="#303a36">\n      <tspan x="1164" dy="0">watch the system</tspan>\n      <tspan x="1164" dy="30">while it runs</tspan>'
)

with open("final_svg.svg", "w") as f:
    f.write(content)

print("Updated final_svg.svg successfully.")
