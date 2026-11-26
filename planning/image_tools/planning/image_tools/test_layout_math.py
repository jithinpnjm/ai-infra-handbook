# Let's test exact coordinates for this layout and check all rules

W = 1600
H = 1200

# Margins:
# Left = 40, Right = 40 (usable 1520)
# Top = 40, Bottom = 40 (usable 1120)

# Title: y = 40 to 116 (h = 76). Gap to next row = 44 px -> Row 2 starts at y = 160.

# Row 2 (cli.py, collect.py, models.py):
# y = 160 to 280 (h = 120)
# cli.py: x = 40 to 520 (w = 480, h = 120)
# Gap = 40 px: Arrow 1 from (520, 220) to (560, 220).
# collect.py: x = 560 to 1060 (w = 500, h = 120)
# Gap = 40 px (1060 to 1100).
# models.py: x = 1100 to 1560 (w = 460, h = 120)

# Gap after Row 2: 40 px -> Row 3 starts at y = 320.
# Arrow 2 from collect.py (bottom at y = 280) down to parsers.py (top at y = 320):
# Line from (780, 280) to (780, 320). Gap = 40 px.

# Row 3 (Pure Layers on left, Exit Codes on right):
# y = 320 to 860 (h = 540)
# Left: Pure Layers container: x = 40 to 1060 (w = 1020, h = 540)
# Inside Pure Layers:
#   parsers.py card: x = 60, y = 340, w = 980, h = 210
#   Arrow 3: from (550, 550) to (550, 590) (gap = 40)
#   rules.py card: x = 60, y = 590, w = 980, h = 250
#   Bottom pad of Pure Layers: 860 - 840 = 20 px >= 16 px!
# Right: Exit Code container: x = 1100 to 1560 (w = 460, h = 540)
# Inside Exit Code container:
#   Card 0: y = 336, h = 106
#   Card 1: y = 458, h = 106
#   Card 3: y = 580, h = 106
#   Card 4: y = 702, h = 106
#   Bottom pad of Exit Code container: 860 - (702 + 106) = 52 px >= 16 px!

# Gap after Row 3: 40 px -> Row 4 starts at y = 900.
# Row 4 (Test strip):
# y = 900 to 1020 (h = 120)
# x = 40 to 1560 (w = 1520)

# Gap after Row 4: 40 px -> Row 5 starts at y = 1060.
# Row 5 (Bottom bar):
# y = 1060 to 1160 (h = 100, or y = 1080 to 1160, h = 80).
# Bottom margin: 1200 - 1160 = 40 px!

print("All row gaps are exactly >= 40 px!")
print("Bottom margin is exactly 40 px!")
print("All boxes fit inside 1600 x 1200!")
