from calc_table import wrap_text, rows

# Rule column width: 900 px -> max_chars = 62
# Let's check line counts for each row:

row_lines = []
for i in range(10):
    t, r = rows[i]
    if i == 2: # Row 3 rule width is 520 px -> max_chars = 36
        r_lines = wrap_text(r, 36)
    else:
        r_lines = wrap_text(r, 62)
    row_lines.append(r_lines)

# Heights:
# Row 3 needs to accommodate Side note (7 lines at 24px) -> height = 216 px
# Other rows:
heights = []
for i in range(10):
    if i == 2:
        h = 216
    else:
        n_lines = len(row_lines[i])
        h = max(58, n_lines * 27 + 28)
    heights.append(h)
    print(f"Row {i+1:2d}: {len(row_lines[i])} lines -> h={h}px")

gap = 6
total_table_h = sum(heights) + gap * 9
print(f"\nTotal table height: {total_table_h}px")

title_h = 65
bottom_bar_h = 45
total_svg_h = title_h + total_table_h + bottom_bar_h + 16 # padding
print(f"Total SVG height: {total_svg_h}px (must be <= 1200)")
