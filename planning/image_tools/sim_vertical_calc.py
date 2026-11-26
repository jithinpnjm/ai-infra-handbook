# Let's test the vertical dimensions.
# Title: y = 25..75 (font-size 48 bold)
# Gap: 35 px -> y = 110

# What if:
# Row 1 (Q1 & Module):
#   Q1: y = 110..220 (h = 110)
#   Module: y = 110..220 (h = 110)
# Gap: 35 px -> y = 255

# Row 2 (Q2 & Raw):
#   Q2: y = 255..365 (h = 110)
#   Raw: y = 255..365 (h = 110)
# Gap: 35 px -> y = 400

# Row 3 (Q3 & Shell & Command):
#   Wait, if Q3, Shell, Command are in Row 3:
#   How tall is Row 3?
#   If Q3 is on the left, Shell on right top, Command on right bottom:
#   Shell: h = 95
#   Gap: 20
#   Command: h = 95
#   Total right height = 95 + 20 + 95 = 210.
#   Q3 on left: h = 110, centered at y = 400 + 105 = 505.
#   Then where does Injection example go?
#   Wait! If Injection example is next to Shell or under Shell, how tall is it?
