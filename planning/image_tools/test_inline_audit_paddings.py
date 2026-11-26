# Let's test the inline heights:
# Row 1 (1 line): rh = 58
# Row 2 (1 line): rh = 58
# Row 3 (3 lines for row 3, 6 lines for side note): rh = 186
# Row 4 (3 lines): rh = 114
# Row 5 (3 lines): rh = 114
# Row 6 (2 lines): rh = 86
# Row 7 (3 lines): rh = 114
# Row 8 (2 lines): rh = 86
# Row 9 (2 lines): rh = 86
# Row 10 (2 lines): rh = 86

row_heights = [58, 58, 186, 114, 114, 86, 114, 86, 86, 86]
gap = 6
total_table = sum(row_heights) + gap * 9
print(f"Total table height: {total_table}px")

table_start_y = 74
table_end_y = table_start_y + total_table
print(f"Table ends at y = {table_end_y}")

bb_h = 46
bb_y = table_end_y + 10
svg_total_h = bb_y + bb_h + 16
print(f"Bottom bar y = {bb_y}, h = {bb_h}")
print(f"Total SVG height = {svg_total_h}px")
