# Let's test if Title on line 1, Rule on line 2+ fits in H=1200!

# Heights:
# 2-line rows (Row 1, Row 2, Row 6, Row 8, Row 9, Row 10):
# Line 1 (title, 30px bold): y = 30
# Line 2 (rule, 24px): y = 58
# Box height = 76 px (top pad 16, bottom pad 18)
h_2line = 76

# 3-line rows (Row 5, Row 7):
# Line 1 (title, 30px bold): y = 30
# Line 2 (rule, 24px): y = 58
# Line 3 (rule, 24px): y = 86
# Box height = 104 px (top pad 16, bottom pad 18)
h_3line = 104

# 4-line rows (Row 4):
# Line 1 (title, 30px bold): y = 30
# Line 2 (rule, 24px): y = 58
# Line 3 (rule, 24px): y = 86
# Line 4 (rule, 24px): y = 114
# Box height = 132 px (top pad 16, bottom pad 18)
h_4line = 132

# Row 3 + Side note:
# Row 3 (title + 4 rule lines = 5 lines):
# Line 1: y = 28 (font 30 bold)
# Line 2: y = 55 (font 24)
# Line 3: y = 82
# Line 4: y = 109
# Line 5: y = 136
# Side note (6 lines at 24px):
# Line 1: y = 28
# Line 2: y = 54
# Line 3: y = 80
# Line 4: y = 106
# Line 5: y = 132
# Line 6: y = 158
# Box height = 176 px (top pad 16, bottom pad 18)
h_row3 = 176

heights = [
    h_2line, # Row 1: 76
    h_2line, # Row 2: 76
    h_row3,  # Row 3: 176
    h_4line, # Row 4: 132
    h_3line, # Row 5: 104
    h_2line, # Row 6: 76
    h_3line, # Row 7: 104
    h_2line, # Row 8: 76
    h_2line, # Row 9: 76
    h_2line  # Row 10: 76
]

gap = 7
total_table = sum(heights) + gap * 9
print(f"Row heights: {heights}")
print(f"Total table height: {total_table}px")

table_start_y = 74
table_end_y = table_start_y + total_table
print(f"Table ends at y = {table_end_y}")

bb_h = 44
bb_y = table_end_y + 10
svg_total_h = 1200
print(f"Bottom bar y = {bb_y}, h = {bb_h}, bottom margin = {svg_total_h - (bb_y + bb_h)}")
