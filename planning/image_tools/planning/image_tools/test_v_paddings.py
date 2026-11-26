#!/usr/bin/env python3

# Let's inspect the vertical padding in each row:
# Row 1: y = 130, h = 58 -> y_top = 130, y_bot = 188.
# Col 1: 2 lines. Line 1 y = 154 (top ~ 154 - 18 = 136, pad_top = 6).
# WAIT! Look at pad_top = 6! That is < 16 px!
# Let's fix Row 1 vertical positioning:
# If Row 1 has h = 64:
# y = 130 to 194.
# Line 1 y = 157. Line 2 y = 183.
# Top of Line 1: 157 - 18 = 139. pad_top = 139 - 130 = 9 px.
# Wait! If cap-height of 24px is ~17px:
# To have pad_top >= 16 px:
# y_baseline >= 130 + 16 + 17 = 163 px!
# If Line 1 baseline is at y = 158:
# Let's write a python solver to calculate the exact row heights and baselines so that EVERY cell has pad_top >= 16 and pad_bottom >= 16!
print("Calculating exact row heights for >= 16px vertical padding...")
