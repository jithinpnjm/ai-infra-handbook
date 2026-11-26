# If Title: y=50, y=104 (ends ~114)
# Question box: y=134 to y=196 (h=62)
# Row 1..7:
# We have 1200 - 196 = 1004 px available.
# We need:
# Bottom margin: 40 px -> y_max = 1160
# Bottom bar: y=1108 to 1160 (h=52)
# Gap: 24 px -> Warning box ends at 1084
# Warning box: y=1008 to 1084 (h=76)
# Gap: 24 px -> Row 7 ends at 984
# Rows space: from y=218 to 984 = 766 px!
# 7 rows: 7 * row_h + 6 * gap = 766
# If row_h = 88 px: 7 * 88 = 616. Gaps = (766 - 616) / 6 = 150 / 6 = 25 px!
# If row_h = 90 px: 7 * 90 = 630. Gaps = (766 - 630) / 6 = 136 / 6 = 22.6 px!
# Can 2 lines fit in row_h = 88 px?
# Let's check text padding inside 88 px:
# Font size: 30px (left), 24px (right).
# Left box: 2 lines of 30px:
# line 1 baseline = y_box + 38
# line 2 baseline = y_box + 70
# Top padding: 38 - 21 (cap) = 17 px (>= 16 px!)
# Bottom padding: 88 - (70 + 6) = 12 px (< 16 px!)
# Wait! What if Row 1 starts at y = 206 instead of 218?
# Let's check:
# Question box at y=124 to 180 (h=56):
# Title: line 1 at y=46, line 2 at y=96. Ends ~104.
# Gap to Question = 20 px (124 - 104 = 20 px).
# Gap from Question to Row 1 = 20 px (200 - 180 = 20 px).
# Row 1 starts at y = 200!
# Row 1..7: from y=200 to y=1005 (space = 805 px!)
# If row_h = 92 px: 7 * 92 = 644 px. 6 gaps of 22 px = 132 px. 644 + 132 = 776 px!
# Then Row 7 ends at 200 + 776 = 976 px!
# Gap to Warning box = 22 px.
# Warning box: y = 998 to 1074 (h=76).
# Gap to Bottom bar = 24 px.
# Bottom bar: y = 1098 to 1150 (h=52).
# Bottom margin = 1200 - 1150 = 50 px (>= 40 px!)
print("Calculated layout fits!")
