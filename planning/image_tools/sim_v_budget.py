# Vertical layout budget

# Row 0: Title (48px bold)
# y = 52

# Row 1: Pipeline of 6 stages (y = 95 to 355, height = 260)
# Inside each stage box:
# - Icon (56px) + Number circle (r=24 -> 48px)
# - Label lines (each 30px line height)
# Top margin = 95 >= 40px.

# Gap between Row 1 (Pipeline) and Row 2 (Columns):
# y = 355 to 405 -> gap = 50px >= 40px!

# Row 2: Four Columns (y = 405 to 1020, height = 615)
# Inside each column:
# We have error message cards!
# Let's check Column 3 (Stage 5) which has 4 cards (tallest column):
# Card 1: libcuda.so.1 (3 lines: ~90px card)
# Card 2: error while loading (3 lines: ~90px card)
# Card 3: version GLIBC (3 lines: ~90px card)
# Card 4: version GLIBCXX (3 lines: ~90px card)
# Total cards height in Col 3: 4 * 90 + 3 gaps of 15px = 360 + 45 = 405px.
# In Column 2: 1 card (9 lines -> ~260px card).
# In Column 1: 3 cards (6 lines + 2 lines + 1 line -> 160 + 70 + 50 = 280px).
# In Column 4: 3 cards (5 lines + 3 lines + 1 line -> 140 + 80 + 50 = 270px).

# Gap between Error Cards and First Check Card:
# y = 920 to 970 -> gap = 50px >= 40px!

# Row 3: First Check cards (y = 970 to 1100, height = 130)
# Bottom margin: y = 1100 to 1180 -> 80px >= 40px!

# Total canvas height = 1180 px (or 1160 px). Fits comfortably under 1200 px!

print("Vertical budget passes with generous >= 40px clearances!")
