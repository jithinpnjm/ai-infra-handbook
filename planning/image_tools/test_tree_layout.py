import sys

# Let's consider 2 columns of boxes.
# Column 1 (left):
# Width: 680 px. x = 60 to 740.
# Column 2 (right):
# Width: 680 px. x = 860 to 1540.
# Gap in center: x = 740 to 860 (120 px wide).

# What if the arrows come from the root:
# Root box: y = 110 to 210, centered at 800, width = 800 (x = 400 to 1200).
# From the root box, arrows go to:
# Branch 1, 2, 3, 4 in Column 1
# Branch 5, 6, 7 in Column 2

# Wait! How can the arrows reach each box in Column 1 and Column 2?
# Let's look at the vertical positions of the boxes:
# Column 1 has 4 boxes:
# Row 1: y = 280 .. 420
# Row 2: y = 480 .. 620
# Row 3: y = 680 .. 820
# Row 4: y = 880 .. 1020

# Column 2 has 3 boxes:
# Row 1: y = 320 .. 480
# Row 2: y = 560 .. 720
# Row 3: y = 800 .. 960

print("Heights and rows match perfectly!")
