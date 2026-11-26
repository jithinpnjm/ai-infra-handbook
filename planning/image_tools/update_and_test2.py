with open("generate_perfect_svg.py") as f:
    code = f.read()

code = code.replace("row_y = [72, 312, 582, 820]", "row_y = [72, 312, 580, 816]")
code = code.replace("row_h = [222, 252, 220, 265]", "row_h = [222, 252, 218, 275]")
code = code.replace('lines.append(\'    <rect x="40" y="1103" width="1520" height="68" rx="14" fill="#207448"/>\')', 'lines.append(\'    <rect x="40" y="1107" width="1520" height="68" rx="14" fill="#207448"/>\')')
code = code.replace('lines.append(\'    <text x="800" y="1146"', 'lines.append(\'    <text x="800" y="1150"')

with open("generate_perfect_svg.py", "w") as f:
    f.write(code)

