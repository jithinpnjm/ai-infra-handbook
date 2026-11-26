# Let's test line wraps for Rules if card usable width is 690px:
# 690 / 14.4 = 47.9 chars.
# If card width = 716px (column 740px, x=52 to 768), padding = 16 each side -> 716 - 32 = 684px.
# 684 / 14.4 = 47.5 chars.

# Can we wrap each rule to minimum lines?
# Rule 1:
# Line 1: print for program output, logging for diagnostics (49 chars -> 49 * 14.4 = 705.6. In card width 738? Column = 740. Card = 724. 724 - 32 = 692. 49 is 705.6.)
# What if Rule 1 is 3 lines?
# L1: print for program output, logging for (37 chars)
# L2: diagnostics with levels, destinations (37 chars)
# L3: and structure (13 chars)
# Height: 24px font, line-height 27px:
# 3 lines: padding 14 top, 14 bottom: 14 + 18 + 27 + 27 + 5 + 14 = 105px.
# Wait! Rule says: "Every text line must fit inside its box with at least 16 px padding."
# So top padding >= 16, bottom padding >= 16, left >= 16, right >= 16.
# With 16px padding and font-size 24:
# baseline 1: y0 + 16 + 17 = y0 + 33.
# for 1 line: height = 33 + 5 + 16 = 54px.
# for 2 lines (dy=27): height = 33 + 27 + 5 + 16 = 81px.
# for 3 lines (dy=27): height = 33 + 27*2 + 5 + 16 = 108px.
# for 4 lines (dy=27): height = 33 + 27*3 + 5 + 16 = 135px.
# for 5 lines (dy=27): height = 33 + 27*4 + 5 + 16 = 162px.

# Let's see:
# Rule 1 (3 lines): 108px
# Rule 2 (5 lines): 162px
# Rule 3 (3 lines): 108px
# Rule 4 (2 lines): 81px
# Rule 5 (3 lines): 108px
# Rule 6 (3 lines): 108px
# Rule 7 (3 lines): 108px
# Total = 108 + 162 + 108 + 81 + 108 + 108 + 108 = 791px!
# Gaps: 6 * 8px = 48px -> 839px!
# Header: 60px -> 899px!
# Total Rules column height = 899px!

# If Rules column is 900px tall:
# y = 140 to 1040.
# Then where does Structured Logging go?
# Structured Logging would start at y = 1055.
# Bottom panel: height 120px -> y = 1055 to 1175.
# Bottom bar: height 50px -> y = 1185 to 1235.
# Total height = 1240!
print("If H=1240, it fits with 3 lines per rule.")
