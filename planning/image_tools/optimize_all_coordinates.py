# Let's find exact coordinates for all elements in 1600x1200 canvas.

# Margins:
# Left = 40, Right = 40
# Cards width = 715
# Left cards: x = 40 to 755
# Gap: 90 px -> x = 755 to 845
# Right cards: x = 845 to 1560

# Vertical items:
# Title at y = 62 (fs=48)
# R1: y1..y1+h
# R2: y2..y2+h
# R3: y3..y3+h
# R4: y4..y4+h
# R5: y5..y5+h
# Guard: yg..yg+hg
# Bottom: yb..yb+hb (ends at 1160)

# All gaps = 40 px.
# Let's test:
# y1 = 115
# h = 122
# gap = 40
# R1: 115..237 (122)
# R2: 277..399 (122)
# R3: 439..561 (122)
# R4: 601..723 (122)
# R5: 763..885 (122)
# Guard: 925..1067 (142)
# Gap: 40 -> Bottom starts at 1107
# Wait, 1107 + 53 = 1160.
# If Bottom is 1098..1160 (62 px), gap between Guard and Bottom is 1098 - 1058 = 40 px if Guard is 918..1058 (140 px).
# Let's check R1..R5 starting at 110:
# R1: 110..232 (122)
# R2: 272..394 (122)
# R3: 434..556 (122)
# R4: 596..718 (122)
# R5: 758..880 (122)
# Guard: 920..1065 (145)
# Gap: 40 -> Bottom starts at 1105
# Bottom: 1105..1160 (55) -> wait, earlier Bottom needed h=62 for top/bot pad >= 16px if fs=30.
# BUT what if Bottom bar has font-size 28?
# Let's check Bottom bar at fs=28 with height=55:
# Cap height = 28 * 0.72 = 20.16.
# Descender = 28 * 0.22 = 6.16.
# Total text height = 26.32 px.
# In a 55 px bar: 55 - 26.32 = 28.68 px total padding!
# top_pad = 14.3 px < 16 px!
# So Bottom bar MUST have height >= 59 px (e.g. 60 or 62 px)!

# To give Bottom bar height 62 px, and Guard strip height 144 px:
# Total heights = 5 * h + 144 + 62.
# Total gaps = 6 * 40 = 240 px.
# Available from y1 to 1160: 1160 - y1.
# If y1 = 110:
# Available = 1050 px.
# 1050 - 240 = 810 px.
# 810 - 144 - 62 = 604 px.
# 604 / 5 = 120.8 px -> h = 120 px!
# 5 * 120 = 600 px.
# 600 + 146 (guard) + 64 (bottom) = 810 px!
# Then:
# R1: 110..230 (120)
# R2: 270..390 (120)
# R3: 430..550 (120)
# R4: 590..710 (120)
# R5: 750..870 (120)
# Guard: 910..1056 (146)
# Bottom: 1096..1160 (64)
# Gaps:
# 270 - 230 = 40
# 430 - 390 = 40
# 590 - 550 = 40
# 750 - 710 = 40
# 910 - 870 = 40
# 1096 - 1056 = 40
# Bottom margin: 1200 - 1160 = 40 px!
# Top margin to R1: 110 px! Title at y=58, gap from Title bottom to R1 = 110 - 68 = 42 px >= 40 px!
print("PERFECT VERTICAL BUDGET FOUND!")
