#!/usr/bin/env python3
# Layout planner for HPA Metric Types SVG

# Canvas dimensions: width=1600, height=1180 or 1200
# Margins: left=40, right=40 (content width = 1520)

# Y coordinates:
# Title: y = 58 (font-size 48 bold)
# Gap: 30
# Table start: y = 100
# Header height: 50 (y = 100 to 150)
# Gap: 12
# 5 Rows:
# Row 1: y = 162, height = 110 (y = 162 to 272)
# Gap: 12
# Row 2: y = 284, height = 110 (y = 284 to 394)
# Gap: 12
# Row 3: y = 406, height = 110 (y = 406 to 516)
# Gap: 12
# Row 4: y = 528, height = 110 (y = 528 to 638)
# Gap: 12
# Row 5: y = 650, height = 110 (y = 650 to 760)

# Table bottom = 760.
# Gap: 28
# Footer rules container / 3 cards:
# Rule 1 card: y = 800, height = 76 (y = 800 to 876)
# Gap: 14
# Rule 2 card (Orange alert): y = 890, height = 76 (y = 890 to 966)
# Gap: 14
# Rule 3 card: y = 980, height = 104 (y = 980 to 1084)
# Total height = 1120 or 1150!

print("Total height would be ~1120. Perfectly within 900 <= H <= 1200!")
