#!/usr/bin/env python3

# Let's verify vertical budget with 40 px margins and gaps:
# Total H = 1180 or 1200
H = 1200
margin_top = 50
margin_bottom = 50
margin_left = 50
margin_right = 50
gap = 40

# Title: y = 50 to 115
title_h = 70
y_after_title = margin_top + title_h # 120

# Top bar (long bar split into segments)
y_top_bar = y_after_title + gap # 120 + 40 = 160
top_bar_h = 90
y_after_top_bar = y_top_bar + top_bar_h # 160 + 90 = 250

# Middle section: Row cards (left) and Side Key (right)
y_middle = y_after_top_bar + gap # 250 + 40 = 290
# 4 rows: each height row_h, with row_gap
# If row_h = 135, 4 * 135 + 3 * 20 = 540 + 60 = 600
# y_after_middle = 290 + 600 = 890
row_h = 140
row_gap = 20 # inside the middle container
middle_h = 4 * row_h + 3 * row_gap # 560 + 60 = 620
y_after_middle = y_middle + middle_h # 290 + 620 = 910

# Bottom strip:
y_bottom = y_after_middle + gap # 910 + 40 = 950
bottom_h = 150
y_after_bottom = y_bottom + bottom_h # 950 + 150 = 1100

remaining_bottom_margin = H - y_after_bottom # 1200 - 1100 = 100 >= 40!

print(f"H = {H}")
print(f"Title: y={margin_top}..{y_after_title}")
print(f"Top bar: y={y_top_bar}..{y_after_top_bar} (h={top_bar_h})")
print(f"Middle (Rows & Key): y={y_middle}..{y_after_middle} (h={middle_h})")
print(f"Bottom strip: y={y_bottom}..{y_after_bottom} (h={bottom_h})")
print(f"Bottom margin: {remaining_bottom_margin} px")
