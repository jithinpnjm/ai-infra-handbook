# simulate_exact_vertical.py

H = 1200

# 1. Title:
title_y = 44

# 2. Table Headers:
hdr_y = 66
hdr_h = 44
# Header text at y = 66 + 32 = 98 (font-size 30 bold)
# top = 98 - 30 = 68 (pad_t = 2), but headers are section headers

# 3. Table Rows:
row_y_start = 118
gap_row = 6

# Rows:
# 1-line rows: h = 62
# 2-line rows: h = 86
# Rows:
# R1: 2-line (h=86)
# R2: 1-line (h=62)
# R3: 1-line (h=62)
# R4: 1-line (h=62)
# R5: 1-line (h=62)
# R6: 1-line (h=62)
# R7: 2-line (h=86)
# R8: 2-line (h=86)
# R9: 2-line (h=86)
# R10: 1-line (h=62)
# R11: 1-line (h=62)
# R12: 2-line (h=86)

row_heights = [86, 62, 62, 62, 62, 62, 86, 86, 86, 62, 62, 86]
current_y = row_y_start
row_coords = []
for i, rh in enumerate(row_heights, 1):
    row_coords.append((i, current_y, rh))
    current_y += rh + gap_row

table_end = current_y - gap_row
print(f"Table ends at y = {table_end}")

# 4. Worked example:
we_gap = 12
we_y = table_end + we_gap
we_h = 86
we_end = we_y + we_h
print(f"Worked example: y={we_y} to {we_end} (h={we_h})")

# 5. Bottom bar:
bb_gap = 12
bb_y = we_end + bb_gap
bb_h = 62
bb_end = bb_y + bb_h
print(f"Bottom bar: y={bb_y} to {bb_end} (h={bb_h})")
print(f"Margin to canvas bottom (1200): {1200 - bb_end} px")
