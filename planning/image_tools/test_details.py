# Let's inspect the vertical space in detail:

# Available Y range: 0 to 1200
# Margins: top >= 40, bottom >= 40, left >= 40, right >= 40
# Gaps between boxes >= 40

# Section 1: Title
# 2 lines:
# Line 1: y = 55 (font-size: 48px)
# Line 2: y = 110 (font-size: 48px)
# Title bottom is around y = 120.

# Analogy box:
# y = 145 to 205 (height 60px)
# Gap between Title and Analogy box: 145 - 120 = 25px (Title is text, not a box, but 25-30px is good. Or start analogy at 150)

# Gap after Analogy box: >= 40px!
# So Main content (Card & Checks) starts at y = 205 + 40 = 245.

# Let's check Main content height:
# From y = 245 to y = 845 -> height = 600px!
# Can 10 card rows and 6 checks fit in 600px?
# Let's check: 600px / 10 rows = 60px per row!
# 60px per row is plenty of space for 24px text! (24px text line height is ~28-30px, 1-2 lines fits in 50-60px).

# Gap after Main content: >= 40px!
# Command strip starts at y = 845 + 40 = 885.
# Height of command strip:
# If command strip ends at 1095 -> height = 210px.

# Gap after Command strip: >= 40px!
# Bottom bar starts at y = 1095 + 40 = 1135.
# Height of bottom bar = 50px (ends at 1185).
# Bottom margin = 1200 - 1185 = 15px -> WAIT! Bottom margin must be >= 40px!

print("Let us tune the budget so bottom margin >= 40px and gaps >= 40px!")
