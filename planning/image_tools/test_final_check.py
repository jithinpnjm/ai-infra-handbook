import re

with open("test_auto_tune.py", "r") as f:
    code = f.read()

# 1. Bottom bar: rect y=1098, height=62, text y=1139
code = code.replace('rect x="40" y="1102" width="1520" height="58"', 'rect x="40" y="1098" width="1520" height="62"')
code = code.replace('text x="800" y="1140"', 'text x="800" y="1139"')

# 2. Lane Shell Card 3: rect y=404, height=62, text y=445
code = code.replace('rect x="58" y="406" width="704" height="58"', 'rect x="58" y="404" width="704" height="62"')
code = code.replace('text x="76" y="444"', 'text x="76" y="445"')

# 3. Lane Daemon Card 3: rect y=404, height=62, text y=445
code = code.replace('rect x="838" y="406" width="704" height="58"', 'rect x="838" y="404" width="704" height="62"')
code = code.replace('text x="856" y="444"', 'text x="856" y="445"')

# 4. Checks Card 4: rect height=92, line 1 y=825
code = code.replace('rect x="696" y="786" width="844" height="88"', 'rect x="696" y="786" width="844" height="92"')
code = code.replace('text x="716" y="827"', 'text x="716" y="825"')

with open("test_auto_tune.py", "w") as f:
    f.write(code)

