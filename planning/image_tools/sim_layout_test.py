# Let's test the vertical layout budget with >= 40px margins and >= 40px between boxes
# Total height <= 1200
# Margins: top >= 40, bottom >= 40, left >= 40, right >= 40
# Gap between all boxes >= 40

# Boxes to place:
# 1. Setup box (or Title + Subtitle + Setup)
# Can Title and Subtitle be outside a box, or inside a header section?
# Title is standalone text. Subtitle can be in a pill or subtitle text.
# If subtitle is in a box: gap to Setup box >= 40.
# Or: Setup box is Box 1.
# Table 1 is Box 2.
# Table 2 is Box 3.
# Takeaway bar is Box 4.

# Let's calculate:
# Top margin: 40px
# Title: y=65 (font 48px bold)
# Subtitle: y=110 (font 24px)
# Gap to Box 1 (Setup): 40px -> Box 1 top = 140
# Box 1 (Setup): y = 140 to 230 (h = 90)
# Gap: 40px -> Box 2 (Table 1) top = 270
# Box 2 (Table 1): y = 270 to 570 (h = 300)
# Gap: 40px -> Box 3 (Table 2) top = 610
# Box 3 (Table 2): y = 610 to 970 (h = 360)
# Gap: 40px -> Box 4 (Takeaway): top = 1010
# Box 4 (Takeaway): y = 1010 to 1150 (h = 140)
# Bottom margin: 1200 - 1150 = 50px >= 40px!

print("Vertical budget check:")
print(f"Total height = 1200")
print(f"Box 1: y=140..230 (h=90)")
print(f"Gap 1-2: {270-230}px")
print(f"Box 2: y=270..570 (h=300)")
print(f"Gap 2-3: {610-570}px")
print(f"Box 3: y=610..970 (h=360)")
print(f"Gap 3-4: {1010-970}px")
print(f"Box 4: y=1010..1150 (h=140)")
print(f"Bottom margin: {1200-1150}px")
