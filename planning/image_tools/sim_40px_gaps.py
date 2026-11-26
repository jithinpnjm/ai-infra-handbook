# Calculating positions with at least 40px between boxes:
# Canvas width = 1600, height = 1200 (or 1180)
# Outside margins:
# Left = 50 (margin 50 >= 40)
# Right = 1550 (margin 50 >= 40)
# Top: Title at y = 58
# Row 1 (Gates): y = 110, h = 115 -> ends at y = 225
# Gap 1: 40px -> next row at y = 265
# Row 2 (Rule 1): y = 265, h = 155 -> ends at y = 420
# Gap 2: 40px -> next row at y = 460
# Row 3 (Rule 2): y = 460, h = 75 -> ends at y = 535
# Gap 3: 40px -> next row at y = 575
# Row 4 (Rule 3): y = 575, h = 95 -> ends at y = 670
# Gap 4: 40px -> next row at y = 710
# Row 5 (Rule 4): y = 710, h = 75 -> ends at y = 785
# Gap 5: 40px -> next row at y = 825
# Row 6 (Operational rules): y = 825, h = 155 -> ends at y = 980
# Gap 6: 40px -> next row at y = 1020
# Row 7 (Takeaway bar): y = 1020, h = 110 -> ends at y = 1130
# Bottom margin: 1180 - 1130 = 50px >= 40px!
# Total H = 1180!

print(f"Row 1: 110..225 (gap to R2: {265-225}px)")
print(f"Row 2: 265..420 (gap to R3: {460-420}px)")
print(f"Row 3: 460..535 (gap to R4: {575-535}px)")
print(f"Row 4: 575..670 (gap to R5: {710-670}px)")
print(f"Row 5: 710..785 (gap to R6: {825-785}px)")
print(f"Row 6: 825..980 (gap to R7: {1020-980}px)")
print(f"Row 7: 1020..1130 (bottom margin: {1180-1130}px)")
