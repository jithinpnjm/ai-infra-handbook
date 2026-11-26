# Let's check dimensions for a side-entering arrow layout.
# If Canvas width is 1600.
# Suppose Left Column has boxes at x = 280 to 760 (width 480).
# Then the space to the left is x = 40 to 280 (width 240).
# If the arrow enters from the left:
# Is 240 px enough for "All idle: id about 99, si and so at 0"?
# No, that's 532 px on 1 line, or ~316 px on 2 lines.

# BUT WHAT IF the boxes are in the outer area, and arrows come from the center?
# Suppose Left Column boxes are at x = 40 to 520 (width 480).
# Center of canvas is 800.
# The space between Box 1 (x_right = 520) and Center (800) is 280 px!
# Still 280 px.

# WAIT! What if the boxes are arranged in TWO COLUMNS, but inside each column:
# What if each branch is a horizontal structure?
# Let's see: Left column is x = 40 to 780 (width 740 px).
# Right column is x = 820 to 1560 (width 740 px).
# Total width of one column: 740 px!
# Inside 740 px:
# What if the arrow goes into the TOP of each box, or what if the arrow comes down?
