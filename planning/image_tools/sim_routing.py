# Let's see:
# Suppose Root is centered: x=400 to 1200, y=100 to 200.
# Left column: Branches 1, 2, 3, 4.
# Right column: Branches 5, 6, 7.
#
# If boxes in Left Column are at x = 220 .. 760 (width 540)
# And boxes in Right Column are at x = 840 .. 1380 (width 540)
#
# Where do the arrows run?
# If arrows run in the OUTER lanes:
# Left outer lane: x = 50 .. 200
# Arrows for 1, 2, 3, 4 come from root (say x=420, 450, 480, 510) or left edge of root,
# go left to outer lane, down to each box, and turn right into the left edge of each box!
# Wait, if an arrow turns right into the left edge of the box:
# Where does the edge label go?
# The edge label could be above the box or along the arrow!
#
# What if arrows run in the INNER lane (between column 1 and column 2)?
# Inner lane: between x=760 and x=840 (width 80). That's too narrow for a 500px label!
#
# Wait! What if the boxes are at x=40..580 and x=1020..1560?
# Then the central space is x=580..1020 (width 440 px)!
# Could the central space hold the arrows and labels?
# Let's check!
