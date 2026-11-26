# If Title top >= 40px:
# Baseline = 75 px (top = 75 - 34.5 = 40.5 px)
# Bottom of title text = 75 + 10 = 85 px
# Gap: 40 px -> Row 1 starts at y = 125 px!
# Available from y = 125 to y = 1160 (bottom bar end): 1035 px!
# If 6 gaps * 40 px = 240 px.
# Leaves 1035 - 240 = 795 px for all 7 items!
# If Bottom bar: h = 60 px -> leaves 735 px.
# If Guard strip: h = 135 px -> leaves 600 px.
# 600 / 5 rows = 120 px per row!

# Let's check: can a box of 120 px fit 3 lines with >=16px padding?
# 3 lines of 24px:
# line 1 (30px bold): cap = 21.6
# line 2 (24px): dy = 28
# line 3 (24px): dy = 28
# descender = 5.3
# Total text height = 21.6 + 28 + 28 + 5.3 = 82.9 px!
# 120 - 82.9 = 37.1 px padding total!
# top_pad = 18.5 px, bot_pad = 18.6 px! Both >= 16 px!

print("3 lines in 120 px box: top_pad=18.5, bot_pad=18.6! Both >= 16 px!")
