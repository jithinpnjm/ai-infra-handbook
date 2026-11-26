# Let's write a script to find coordinates where ALL bounding boxes are strictly disjoint!
# We have:
# 6 step boxes: S1, S2, S3, S4, S5, S6
# 5 gate diamonds: D1, D2, D3, D4, D5

# Each step box has traffic title:
# Step 1: "Shadow traffic"
# Can "Shadow traffic" be:
# line 1: "Shadow" (len 6)
# line 2: "traffic" (len 7)
# At font-size 30 bold: max line width = 7 * 0.6 * 30 = 126 px.
# With 16px pad on each side, step box width >= 126 + 32 = 158 px.

# Each gate diamond has:
# line 1: "gates" (len 5)
# line 2: "pass" (len 4)
# At font-size 24 bold: max line width = 5 * 0.6 * 24 = 72 px.
# With 16px pad on each side, diamond width >= 72 + 32 = 104 px.

# Total width available on canvas = 1600.
# If S1..S6 and D1..D5 are separated in X:
# Total width needed = 6 * 158 + 5 * 104 = 948 + 520 = 1468 px!
# 1600 - 1468 = 132 px!
# 132 px can be distributed:
# Margins: 40 px left, 40 px right -> 132 - 80 = 52 px!
# Remaining gap across 10 spaces = 5.2 px per gap.
# That's 5.2 px gap between EVERY step and diamond!
# All 11 elements are 100% DISJOINT IN X!
# None of them overlap in X, so none of them overlap in 2D space!
print("100% disjoint in X is mathematically possible!")
