#!/usr/bin/env python3

# Strict vertical budget calculator ensuring EVERY box has:
# top_pad = (first_line_baseline - font_size) - box_y >= 16
# bot_pad = (box_y + box_h) - last_line_baseline >= 16

def min_box_h(num_lines, fs=24, dy=24):
    first_baseline_rel = 16 + fs
    last_baseline_rel = first_baseline_rel + (num_lines - 1) * dy
    min_h = last_baseline_rel + 16
    return min_h

print(f"1 line (fs=24): min_h = {min_box_h(1)}")
print(f"2 lines (fs=24, dy=24): min_h = {min_box_h(2)}")
print(f"3 lines (fs=24, dy=24): min_h = {min_box_h(3)}")
print(f"4 lines (fs=24, dy=24): min_h = {min_box_h(4)}")

# Row heights needed:
# Row 11: 4 lines => min_h = 128
# Row 12: 3 lines => min_h = 104
# Row 13: 2 lines => min_h = 80
# Row 14: 3 lines => min_h = 104
# Row 15: 3 lines => min_h = 104
# Row 16: 3 lines (in cmd) => min_h = 104
# Row 17: 2 lines (in cmd) => min_h = 80
# Row 18: 3 lines (in cmd) => min_h = 104

# Total row heights:
rhs = [128, 104, 80, 104, 104, 104, 80, 104]
total_rhs = sum(rhs)
print(f"Total row heights: {total_rhs}px")

# Footer (2 lines): min_h = 80
# Bottom bar (1 line): min_h = 56
# Table header (1 line, fs=28 or 30):
# for fs=28: 16 + 28 + 16 = 60
# If fs=24: 16 + 24 + 16 = 56
h_hdr = 56

# Let's see:
# y_top_margin = 40
# Title (48px, 2 lines, dy=48):
# baseline 1 = 40 + 48 = 88 (or 86)
# baseline 2 = 88 + 48 = 136
# Title ends at 136 + 12 = 148.
# Then header at y = 160, h = 56 (ends at 216).
# If rows start at y = 222:
# 222 + total_rhs (808) + 7*gap = 222 + 808 + 7*5 = 1065.
# Footer: y = 1070, h = 80 (ends at 1150).
# Bottom bar: y = 1155, h = 56 (ends at 1211 > 1200!).
