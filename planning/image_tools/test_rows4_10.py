from test_wrap import wrap_text, rows

print("Rows 4-10 in full width (max_chars = 72):")
total_h = 0
for i in range(3, 10):
    t, r = rows[i]
    r_lines = wrap_text(r, 72)
    h = max(60, len(r_lines) * 28 + 24)
    total_h += h + 8 # 8px gap
    print(f"Row {i+1:2d} ({len(r_lines)} lines, h={h}px):")
    for l in r_lines:
        print(f"   [{len(l):2d} chars] {l}")

print(f"\nTotal height of Rows 4-10: {total_h}px")
