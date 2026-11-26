# Let's design an exact layout that satisfies:
# 1. Every text line has >= 16px padding on left, right, top, bottom
# 2. Total SVG height H <= 1200
# 3. All font-sizes >= 24px

# Widths:
# Canvas: 1600
# Margin left: 40, Margin right: 40 -> Content width = 1520
# Col 1 (Format): x=40, w=190
# Col 2 (Use for): x=238, w=224
# Col 3 (Safe call): x=470, w=542
# Col 4 (Trap): x=1020, w=540
# 1020 + 540 = 1560 (leaves 40px right margin)

# Let's check horizontal padding:
# Col 1:
# Header: 'Format' (fs=30, len=6, sans) -> w = 6 * 18 = 108. (190 - 108)/2 = 41px padding!
# JSON: fs=30, w=4*18=72. tx=135 -> left=99, right=171. In [40, 230], left_pad=59, right_pad=59.
# Icon JSON: at x=56, width=40. text at 135 (x_start=99) -> gap between icon and text = 99 - (56+40) = 3px!
# Wait! Let's check icon position:
# In Col 1 (w=190, [40, 230]):
# If icon is 36px wide at x=52 (ends at 88):
# Text: 'JSON' at x=145 (starts at 145 - 36 = 109, ends at 145 + 36 = 181).
# Gap between icon and text = 109 - 88 = 21px!
# Right pad = 230 - 181 = 49px!
# Left pad of icon = 52 - 40 = 12px? Wait! If icon is at x=56, icon width=32. Left pad = 16px!
# What about 'Parquet or JSON Lines'?
# Line 1: 'Parquet or' (len 10, fs=24) -> w = 10 * 14.4 = 144. (190 - 144)/2 = 23px pad!
# Line 2: 'JSON Lines' (len 10, fs=24) -> w = 10 * 14.4 = 144. 23px pad!

# Col 2 (w=224, [238, 462]):
# Header: 'Use for' (len 7, fs=30) -> w = 7 * 18 = 126. (224 - 126)/2 = 49px pad!
# 'machine' (len 7) -> w = 100.8. pad = 61.6px.
# 'interchange' (len 11) -> w = 158.4. pad = 32.8px.
# 'configs people' (len 14) -> w = 201.6. pad = (224 - 201.6)/2 = 11.2px! < 16px!
# AHA! 'configs people' has only 11.2px padding in 224px box!
# If Col 2 is 240px wide:
# pad = (240 - 201.6)/2 = 19.2px! (> 16px).
# So Col 2 MUST be at least 236px wide!
print("Col 2 needs w >= 236")
