#!/usr/bin/env python3

# Let's compute exact y coordinates for both columns and check all gaps:

# Canvas: 1600 x 1200
# Title at y = 65 (fs=48)
# Gap to content: columns start at y = 130

# LEFT COLUMN: x = 40..770 (w = 730)
# Item 1: Anatomy
# y1 = 130, h1 = 130 -> y = 130..260
# Gap = 25
# Item 2: Rule
# y2 = 285, h2 = 180 -> y = 285..465
# Gap = 25
# Item 3: Query picture container
# y3 = 490, h3 = 490 -> y = 490..980

# Inside Query picture container (y = 490..980, h=490):
# Container icon at y = 505 (56x56)
# 4 query rows:
# Row 1: y = 575..660 (h = 85)
# Row 2: y = 675..760 (h = 85)
# Row 3: y = 775..860 (h = 85)
# Row 4: y = 875..960 (h = 85)
# Left column ends at y = 980!

# RIGHT COLUMN: x = 830..1560 (w = 730)
# Item 1: Load box
# y1 = 130, h1 = 300 -> y = 130..430
# Gap = 25
# Item 2: Result
# y2 = 455, h2 = 150 -> y = 455..605
# Gap = 25
# Item 3: Fix from outside in
# y3 = 630, h3 = 195 -> y = 630..825
# Gap = 25
# Item 4: Risky
# y4 = 850, h4 = 130 -> y = 850..980
# Right column ends at y = 980!

# BOTH COLUMNS END AT EXACTLY y = 980! (PERFECT VERTICAL ALIGNMENT!)

# Gap between columns and bottom strip:
# y = 980..1030 -> GAP = 50 px! (>= 40 px requirement!)

# BOTTOM STRIP (Test note):
# x = 40..1560 (w = 1520)
# y = 1030..1150 (h = 120)
# Bottom margin: 1200 - 1150 = 50 px! (>= 40 px requirement!)

print("Grid layout perfectly aligned!")
print("Top gap: 130 - 65 = 65 px")
print("Left margin: 40 px")
print("Col 1 width: 730 px")
print("Inter-column gap: 830 - 770 = 60 px (>= 40 px)")
print("Col 2 width: 730 px")
print("Right margin: 1600 - 1560 = 40 px")
print("Both columns height: 980 - 130 = 850 px")
print("Inter-row gap to bottom strip: 1030 - 980 = 50 px (>= 40 px)")
print("Bottom strip: x=40..1560, y=1030..1150 (h=120)")
print("Bottom margin: 1200 - 1150 = 50 px (>= 40 px)")
