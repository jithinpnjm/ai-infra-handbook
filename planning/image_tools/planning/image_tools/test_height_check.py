# Let's test the 2-column layout vertical heights and paddings

W = 1600
H = 1200

# Margins:
# Left = 40, Right = 40 -> Usable W = 1520
# Left col: x = 40 to 1020 (width = 980)
# Gap: 40 px (x = 1020 to 1060)
# Right col: x = 1060 to 1560 (width = 500)

# Vertical coordinates:
# Top margin: 40
# Title: y = 40 to 118 (ends at 118)
# Gap = 40 -> y starts at 158

# Bottom margin: 40 (ends at 1160)
# Bottom bar: y = 1100 to 1160 (h = 60). Gap to bottom = 40.
# Gap = 40 -> y ends at 1060
# Test strip: y = 940 to 1060 (h = 120).
# Gap = 40 -> y ends at 900.

# Available height for Middle Section: y = 158 to 900 -> 742 px.

# Let's see: Left column has:
# 1. cli.py card: y = 158 to 238 (h = 80)
# Arrow 1: y = 238 to 278 (gap = 40)
# 2. collect.py card: y = 278 to 368 (h = 90)
# Arrow 2: y = 368 to 408 (gap = 40)
# 3. Pure layers container: y = 408 to 900 (h = 492)
# Inside Pure Layers:
#   parsers.py card: y = 422 to 626 (h = 204)
#   Arrow 3: y = 626 to 666 (gap = 40)
#   rules.py card: y = 666 to 886 (h = 220)
#   Bottom pad of Pure layers: 900 - 886 = 14 px? We can make it 16 px by tuning!

print(f"Total middle section used: {900 - 158} px / 742 px")
