import sys

# Let's inspect:
# In Column 1, we have 4 boxes: Box 1, Box 2, Box 3, Box 4.
# In Column 2, we have 3 boxes: Box 5, Box 6, Box 7.
#
# If Box 1 is at x = 200..740 (width 540).
# What if the arrow enters Box 1 from the top, or from the left?
# If arrow enters from the top:
# Where does the arrow come from?
# For Box 1: straight down from the root box!
# Root box bottom is at y=190.
# Box 1 top is at y=290.
# The arrow is a straight line from (x_c, 190) to (x_c, 290)!
# That's a 100px vertical arrow!
# Beside that vertical arrow (between y=190 and 290):
# We have a width from x=50 to 740 (690 px)!
# The label "All idle: id about 99, si and so at 0" fits COMPLETELY on one line beside the arrow!
#
# Now, what about Box 2?
# Box 2 is at y=500..590.
# How does the arrow from Root reach Box 2?
# Path from Root:
# It starts at Root bottom (say x=120, 190).
# It goes DOWN on the left of Box 1 (say along x=120).
# Box 1 is at x=200..740, so x=120 is to the left of Box 1!
# At y=440 (above Box 2, which is at y=500), the arrow turns RIGHT to x=470 (center of Box 2),
# and then turns DOWN into the top of Box 2 at y=500!
# OR it turns right and enters the LEFT edge of Box 2 at (200, 545)!
#
# WAIT! Look at both options:
# If it enters the left edge of Box 2 at (200, 545):
# Then the horizontal segment is from x=120 to x=200 (only 80 px).
# But if it turns RIGHT to x=470 and points DOWN into the top of Box 2:
# The space above Box 2 (y = 400..500) has width from x=140 to 740 (600 px)!
# And in that space above Box 2, beside the arrow, sits the label:
# "High us, low wa"!
# And for Box 3:
# Arrow starts at Root (x=90, 190).
# Goes DOWN along x=90 (outside Box 1 and Box 2).
# Turns RIGHT into the space above Box 3, points down into Box 3!
# Beside the arrow is the label: "High wa and b"!
# And for Box 4:
# Arrow starts at Root (x=60, 190).
# Goes DOWN along x=60 (outside Box 1, 2, 3).
# Turns RIGHT into the space above Box 4, points down into Box 4!
# Beside the arrow is the label: "Growing so, falling free or cache"!

print("Testing this concept...")
