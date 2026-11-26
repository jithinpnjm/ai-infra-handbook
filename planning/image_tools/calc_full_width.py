from calc_table import wrap_text, rows

# If table is full width 1520:
# Col 1: Icon + Title: width 380px. (Title max_chars = 25)
# Col 2: Rule: width 1520 - 380 = 1140. Padding 16 each side -> 1108 px text width.
# At 14.4 px/char: 1108 / 14.4 = 76.9 -> 76 chars per line!

total_h = 0
for i in range(10):
    t, r = rows[i]
    r_lines = wrap_text(r, 76)
    t_lines = wrap_text(t, 25)
    lines_count = max(len(r_lines), len(t_lines))
    h = lines_count * 28 + 32
    total_h += h + 6 # 6px gap
    print(f"Row {i+1:2d} ({len(r_lines)} rule lines, {len(t_lines)} title lines): h={h}px")

print(f"\nTotal table height: {total_h}px")
