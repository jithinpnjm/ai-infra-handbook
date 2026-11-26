#!/usr/bin/env python3

# Let's budget vertical space with:
# Top margin >= 40px
# Title at top
# Gap >= 40px between boxes
# Bottom margin >= 40px
# Total H = 1200

# Available height = 1200
# Margins: top 40px, bottom 40px. Remaining = 1120px.
# Title: font-size 48px bold.
# If title is at y = 65 (starts around 25, ends around 75).
# Box row 1 starts at y = 120 (45px gap after title).
# We have 4 rows of boxes: Row 1, Row 2, Row 3, Row 4 (Failures).
# Between Row 1 and Row 2: gap >= 40px
# Between Row 2 and Row 3: gap >= 40px
# Between Row 3 and Row 4: gap >= 40px
# 3 gaps of 40px = 120px.
# Row 4 ends at 1200 - 40 = 1160.
# Available height for Row 1 + Row 2 + Row 3 + Row 4:
# 1160 - 120 - 120 = 920px!

# Let's allocate 920px across the 4 rows:
# Row 1 (Tile 1, 2, 3): 215px
# Row 2 (Tile 8, Center, 4): 180px
# Row 3 (Tile 7, 6, 5): 275px
# Row 4 (Failure examples): 250px
# Sum = 215 + 180 + 275 + 250 = 920px!

print("Testing exact coordinates:")
y1 = 120
h1 = 215
y2 = y1 + h1 + 40 # 120 + 215 + 40 = 375
h2 = 180
y3 = y2 + h2 + 40 # 375 + 180 + 40 = 595
h3 = 275
y4 = y3 + h3 + 40 # 595 + 275 + 40 = 910
h4 = 250
y_end = y4 + h4 # 910 + 250 = 1160
margin_bottom = 1200 - y_end # 40px!

print(f"Row 1: y={y1}, h={h1}, bottom={y1+h1}")
print(f"Gap 1-2: {y2 - (y1+h1)}px")
print(f"Row 2: y={y2}, h={h2}, bottom={y2+h2}")
print(f"Gap 2-3: {y3 - (y2+h2)}px")
print(f"Row 3: y={y3}, h={h3}, bottom={y3+h3}")
print(f"Gap 3-4: {y4 - (y3+h3)}px")
print(f"Row 4: y={y4}, h={h4}, bottom={y_end}")
print(f"Bottom margin: {margin_bottom}px")
