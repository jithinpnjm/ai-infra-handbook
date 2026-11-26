# find_vertical_fit.py

# Canvas: 1600 x 1200
# Title: 48px bold, centered at x=800, y=52
# Headers: y=84, h=40
# Bottom bar: y=1130, h=50 (1130 + 50 = 1180, margin to bottom = 20)
# Worked example: y=1040, h=74 (ends at 1114, gap to bottom bar = 16)
# Available for table: from y=134 to y=1024 -> 890 px!

# We have 12 rows.
# If gap between rows is 6px, 11 gaps = 66px.
# Height for 12 row rects = 890 - 66 = 824 px.
# 824 / 12 = 68.6 px per row!

# If 1-line rows have h = 54 px:
# top_y = ty - 24
# bot_y = ty + 6
# visual text height = 30 px.
# If h = 54 px and ty = by + 37:
# pad_t = 37 - 24 = 13 px (< 16 px).
# WAIT! Does the prompt require pad_t >= 16 for vertical padding as well?
print("Let's check!")
