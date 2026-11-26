#!/usr/bin/env python3

# Let's test the Query Row geometry:
# Row box: x=65, width=680 (ends at 745)
# Row 1: y = 580..665 (h = 85)

# Text: "suffix 1 -> NXDOMAIN"
# Length: 20 chars
# Width at fs=24 monospace: 20 * 24 * 0.62 = 297.6 px
# Text x = 95 -> ends at 95 + 297.6 = 392.6 px

# Target badge:
# x = 660, y = 595, width = 65, height = 55, rx = 8
# Badge has an X mark drawn with 2 lines (stroke-width=3.5, stroke='#db8129' or '#207448')

# Arrow:
# Starts at x1 = 440, ends at x2 = 660
# y1 = 622, y2 = 622
# marker-end="url(#arrow)"
# Arrow length = 660 - 440 = 220 px!
# Arrow ends exactly at x=660, which is the left edge of the badge!

# Clearance between text end (392.6) and arrow start (440):
# 440 - 392.6 = 47.4 px! (>= 16 px requirement!)

# Let's check Row 4: "idp.example.test -> answer"
# Length: 26 chars
# Width at fs=24 monospace: 26 * 24 * 0.62 = 386.9 px
# Text x = 95 -> ends at 95 + 386.9 = 481.9 px
# Arrow starts at x1 = 510, ends at x2 = 660
# Arrow length = 660 - 510 = 150 px
# Clearance between text end (481.9) and arrow start (510):
# 510 - 481.9 = 28.1 px! (>= 16 px requirement!)

print("Row 1..3 clearance:", 440 - 392.6, "px")
print("Row 4 clearance:", 660 - 510, "px length, text clearance:", 510 - 481.9, "px")
assert 440 - 392.6 >= 16
assert 510 - 481.9 >= 16
print("ALL CLEARANCES EXCEED 16px REQUIREMENT!")
