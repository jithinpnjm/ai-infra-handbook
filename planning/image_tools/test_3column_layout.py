# Let's explore 3 columns of width:
# Canvas width = 1600
# Col 1: X = 80 .. 420 (width 340, center 250)
# Col 2: X = 630 .. 970 (width 340, center 800)
# Col 3: X = 1180 .. 1520 (width 340, center 1350)
# Gap between Col 1 and Col 2: 630 - 420 = 210px!
# Gap between Col 2 and Col 3: 1180 - 970 = 210px!
# Still, 210px is tight for 260px.

# BUT WHAT IF arrows flow VERTICALLY between boxes?
# In a vertical gap between rows (height 180px):
# The horizontal width available for text is the FULL 340px box width (or even 450px)!
# When an arrow goes vertically, the text can be 340px wide!
# 340px / 14.4px = 23.6 characters per line!
# That means ANY label wraps in 2 lines!
# Line 1: ~25 chars
# Line 2: ~25 chars
# Height of 2 lines: 56px.
# In a 180px vertical gap, a 56px label fits with 60px of padding above and below!

print("Vertical gaps allow up to 400px width for transition labels!")
