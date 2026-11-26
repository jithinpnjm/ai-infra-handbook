import math

# Total canvas: width = 1600, height = 1200
# Outside margin: >= 40 px everywhere.
# Gaps between boxes: >= 40 px.

# Let's check:
# 1. Gate row:
# y = 145 to 265 (height = 120)
# Latency gates: x = 50 to 765 (width = 715)
# Quality gates: x = 835 to 1550 (width = 715)
# Gap between Latency and Quality: 835 - 765 = 70 px >= 40 px.
# Left margin: 50 >= 40 px. Right margin: 1600 - 1550 = 50 >= 40 px.
# Gap to title (ends y=110): 145 - 110 = 35 px -> make y = 150 to 270 (gap = 40 px)!

# 2. Outcome boxes row:
# y = 840 to 1020 (height = 180)
# Promote: x = 50 to 510 (width = 460)
# Hold: x = 570 to 1030 (width = 460)
# Rollback: x = 1090 to 1550 (width = 460)
# Gaps between outcome boxes: 570 - 510 = 60 px, 1090 - 1030 = 60 px (both >= 40 px).
# Left margin: 50 >= 40 px. Right margin: 50 >= 40 px.

# 3. Takeaway bar:
# y = 1080 to 1144 (height = 64)
# x = 50 to 1550 (width = 1500)
# Gap to outcome boxes: 1080 - 1020 = 60 px >= 40 px.
# Bottom margin: 1200 - 1144 = 56 px >= 40 px.

# 4. Vertical space for Staircase:
# From bottom of Gate row (y = 270) to top of Outcome row (y = 840):
# Available height = 840 - 270 = 570 px!
# With 40 px gap from Gate row: y_start = 310
# With 40 px gap to Outcome row: y_end = 800
# Usable height = 800 - 310 = 490 px!

print("Usable vertical space for staircase: y = 310 to 800 (height 490 px)")
