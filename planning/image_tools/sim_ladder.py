import math

# Dimensions
W = 1600
H = 1200

# Margins
margin_x = 50
margin_top = 110 # below title
margin_bottom = 50

# Title
title_text = "Investigation commands from cheapest to most targeted"
title_fs = 48
title_y = 65

# 8 rows
num_rows = 8
gap_y = 41
box_h = 92
# Check vertical space:
total_h = 8 * box_h + 7 * gap_y
print(f"Total ladder height: {total_h}px")
print(f"Top: {margin_top}, Bottom: {margin_top + total_h}")
assert margin_top + total_h <= H - 40, f"Exceeds H: {margin_top + total_h} > {H - 40}"

box_w = 1500 # x from 50 to 1550

# Row 5: split into Step 5 and Warning box
w_step5 = 730
gap_r5 = 40
w_warn = box_w - w_step5 - gap_r5
print(f"Row 5: Step 5 width={w_step5}, gap={gap_r5}, Warning width={w_warn}")
assert w_warn >= 700
