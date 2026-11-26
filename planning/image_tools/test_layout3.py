# 1-line: 58px
# 2-line: 82px
# 3-line: 108px
# Gaps: 6px

heights = [82, 82, 82, 58, 82, 58, 58, 58, 108, 82, 82]
row_gaps = 6

y_start = 204
y = y_start
for i, h in enumerate(heights, 1):
    print(f"Row {i:2d}: y={y:4d} to {y+h:4d} (h={h})")
    y += h + row_gaps
y -= row_gaps
print(f"Rows end at y={y}")
bottom_bar_y = y + 14
bottom_bar_h = 60
print(f"Bottom bar: y={bottom_bar_y} to {bottom_bar_y + bottom_bar_h}")
print(f"Bottom margin: {1200 - (bottom_bar_y + bottom_bar_h)}")
