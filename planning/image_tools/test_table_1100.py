from test_wrap import wrap_text, rows

# Col 1: Icon (48px) + Number & Decision Title: width 310
# Col 2: Rule: width 1100 - 310 = 790. Padding 16 each side -> 758 px text width.
# At 14.4 px/char: 758 / 14.4 = 52.6 -> 52 chars per line!

total_h = 0
for i in range(10):
    t, r = rows[i]
    r_lines = wrap_text(r, 52)
    # text height: len(r_lines) * 28
    # box height = top_pad(16) + text_height + bottom_pad(16)
    # But wait, decision title might also wrap!
    t_lines = wrap_text(t, 20)
    lines_count = max(len(r_lines), len(t_lines))
    h = lines_count * 28 + 32
    total_h += h + 6 # 6px gap
    print(f"Row {i+1:2d} ({len(r_lines)} rule lines, {len(t_lines)} title lines): h={h}px")

print(f"\nTotal table height: {total_h}px")
