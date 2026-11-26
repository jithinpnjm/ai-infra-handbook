boxes = [
    # (name, box_y, box_h, base_y, dy, num_lines, fs, desc)
    ("cli", 95, 125, 148, 34, 2, 26, 6),
    ("collect", 265, 140, 312, 32, 3, 24, 6),
    ("parsers", 450, 195, 495, 34, 4, 24, 6),
    ("rules", 705, 150, 770, 34, 2, 25, 6),
    ("models", 336, 94, 378, 30, 2, 25, 6),
    ("parser_detail", 470, 230, 514, 27, 7, 24, 6),
    ("rules_detail", 740, 150, 782, 28, 4, 24, 6),
    ("test_strip", 935, 120, 975, 28, 3, 24, 6),
    ("bottom_bar", 1095, 65, 1139, 0, 1, 28, 5)
]

all_ok = True
for name, by, bh, base_y, dy, n_lines, fs, desc in boxes:
    top_pad = (base_y - fs) - by
    last_base = base_y + (n_lines - 1) * dy
    bot_pad = (by + bh) - (last_base + desc)
    ok_top = top_pad >= 16
    ok_bot = bot_pad >= 16
    if not (ok_top and ok_bot):
        all_ok = False
    print(f"[{'OK' if ok_top and ok_bot else 'FAIL'}] {name:15s}: top_pad={top_pad:4.1f}px, bot_pad={bot_pad:4.1f}px (by={by}, bh={bh})")

assert all_ok, "Some vertical padding is < 16px!"
print("\nALL BOXES PASS VERTICAL PADDING!")
