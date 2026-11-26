H = 1180
title_y = 56
top_box_y = 90
top_box_h = 76
row_h = 106
gap = 14
row1_y = 188
bottom_box_h = 80

row_ys = [row1_y + i * (row_h + gap) for i in range(7)]
print("Row Ys:", row_ys)
last_row_bottom = row_ys[-1] + row_h
print("Last row bottom:", last_row_bottom)
bottom_box_y = last_row_bottom + 22
print("Bottom box Y:", bottom_box_y, "bottom:", bottom_box_y + bottom_box_h)
bottom_margin = H - (bottom_box_y + bottom_box_h)
print("Bottom margin:", bottom_margin)
assert bottom_margin >= 40
