# Let's test if we can have gap >= 40 px between all boxes
# Canvas height H = 1200
# Top margin = 40
# Title (48px)
# Question box
# 7 rows
# Warning box
# Bottom bar
# Bottom margin = 40

# If gap between rows is 40 px:
# 7 rows of height H_row + 6 gaps of 40 = 7 * H_row + 240.
# If H_row = 80: 7 * 80 + 240 = 560 + 240 = 800 px.
# But can 2 lines of 30px text fit inside H_row = 80 with >= 16px padding?
# Let's check:
# 2 lines of 30px: line 1 baseline at y=32, line 2 baseline at y=64.
# Top padding = 32 - 21 = 11 px -> LESS than 16px!
# For 16px top and bottom padding:
# Top padding >= 16: baseline 1 >= 16 + 21 = 37.
# Line 2 baseline = 37 + 34 = 71.
# Bottom padding >= 16: H_row >= 71 + 7 + 16 = 94 px!
# So H_row MUST be at least 94 px (say 96 px)!

# If H_row = 96 px:
# 7 rows * 96 = 672 px.
# What gaps between the 7 rows can we afford if H = 1200?
# Let's see:
# y=0 to 1200:
# Title at y=50 (1 line or 2 lines?)
# If Title is at y=50:
# Let's check Title length in Helvetica: 1446 px. Margins = (1600 - 1446)/2 = 77 px.
# At 1446 px, with 77 px left and right margins, Title fits on 1 line!
# But what about conservative estimate: 67 * 0.6 * 48 = 1929.6 px.
# Wait, does the conservative estimate apply to the TITLE (which is not in a box)?
# The prompt says: "Every text line must fit inside its box with at least 16 px padding."
# The title is not inside a box!
# But let's check: what if Title is 2 lines?
# Line 1: y=46, Line 2: y=98.
