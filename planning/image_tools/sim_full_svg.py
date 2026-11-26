import re

# Let's test a complete layout and verify every single text line width, box padding, and gap!

CANVAS_W = 1600
CANVAS_H = 1200
MARGIN = 40

# Fonts:
# Title: 48 bold
# Node titles: >= 30 bold
# Secondary text: >= 24
# Monospace: >= 24

# Let's test the positions of major sections:
# Top: Title at y=40..120
# y=120..160: Gap (40px)
# y=160..780: Main section (Left flow + Fixes, Right panel "Docker network modes") (h=620)
# y=780..820: Gap (40px)
# y=820..900: Model strip (h=80)
# y=900..940: Gap (40px)
# y=940..1040: Footer & Inspect commands (h=100)
# y=1040..1080: Gap (40px)
# y=1080..1160: Bottom bar (h=80)
# y=1160..1200: Margin (40px)

print("Vertical budget check:")
print("Title: y=40..120")
print("Gap 1: 120..160 (40px)")
print("Main section: 160..780 (620px)")
print("Gap 2: 780..820 (40px)")
print("Model strip: 820..900 (80px)")
print("Gap 3: 900..940 (40px)")
print("Footer & Commands: 940..1040 (100px)")
print("Gap 4: 1040..1080 (40px)")
print("Bottom bar: 1080..1160 (80px)")
print("Bottom margin: 1160..1200 (40px)")
print("Sum =", 120 + 40 + 620 + 40 + 80 + 40 + 100 + 40 + 80 + 40)
