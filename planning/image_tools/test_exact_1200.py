h_1line = 60
h_2line = 84
h_3line = 112
h_row3 = 180

heights = [
    h_1line, # Row 1: 60
    h_1line, # Row 2: 60
    h_row3,  # Row 3: 180
    h_3line, # Row 4: 112
    h_3line, # Row 5: 112
    h_2line, # Row 6: 84
    h_3line, # Row 7: 112
    h_2line, # Row 8: 84
    h_2line, # Row 9: 84
    h_2line  # Row 10: 84
]

gap = 7
total_table = sum(heights) + gap * 9
print(f"Total table height: {total_table}px")

table_start_y = 76
table_end_y = table_start_y + total_table
print(f"Table ends at y = {table_end_y}")

bb_h = 46
bb_y = table_end_y + 12
svg_total_h = 1200
print(f"Bottom bar y = {bb_y}, h = {bb_h}, bottom margin = {svg_total_h - (bb_y + bb_h)}")
