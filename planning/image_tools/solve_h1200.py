# Vertical budget solver for H=1200

# Let's inspect heights:
# Title: 2 lines. y=45, y=90. Title area: y=0..105.
# Group 1: Top Lane: y = 115 .. 335 (height = 220)
# Gap: 40px -> y = 375
# Group 2: Routing table container: y = 375 .. 675 (height = 300)
#   - Row 1: y = 390 .. 465 (height = 75)
#   - Row 2: y = 485 .. 560 (height = 75)
#   - Row 3: y = 580 .. 655 (height = 75)
# Gap: 40px -> y = 715
# Group 3: Async libraries + Side note (uvloop): y = 715 .. 870 (height = 155)
# Gap: 40px -> y = 910
# Group 4: Debug strip: y = 910 .. 1080 (height = 170)
# Gap: 40px -> y = 1120
# Group 5: Bottom bar: y = 1120 .. 1180 (height = 60)
# Bottom margin: 1200 - 1180 = 20px (or y=1130..1185, margin 15px)

# Let's print the gaps:
boxes = [
    ("Title", 0, 105),
    ("Top Lane", 115, 335),
    ("Routing Table", 375, 675),
    ("Async + uvloop", 715, 870),
    ("Debug Strip", 910, 1080),
    ("Bottom Bar", 1120, 1180)
]

for i in range(len(boxes)-1):
    b1 = boxes[i]
    b2 = boxes[i+1]
    gap = b2[1] - b1[2]
    print(f"Gap between {b1[0]} and {b2[0]}: {gap}px")
