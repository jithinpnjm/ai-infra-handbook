h_1line = 60
h_2line = 84
h_3line = 114
h_row3 = 184

heights = [
    h_1line, # Row 1
    h_1line, # Row 2
    h_row3,  # Row 3 + Side note
    h_3line, # Row 4
    h_3line, # Row 5
    h_2line, # Row 6
    h_3line, # Row 7
    h_2line, # Row 8
    h_2line, # Row 9
    h_2line  # Row 10
]

gap = 8
total_table = sum(heights) + gap * 9
print(f"Total table height: {total_table}px")

table_start_y = 80
table_end_y = table_start_y + total_table
print(f"Table ends at y = {table_end_y}")

bb_h = 48
bb_y = table_end_y + 14
svg_total_h = bb_y + bb_h + 16
print(f"Bottom bar y = {bb_y}, h = {bb_h}")
print(f"Total SVG height = {svg_total_h}px")
