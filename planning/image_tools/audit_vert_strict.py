boxes = [
    # (name, rect_y, rect_h, fs, [text_baselines])
    ("Header Q", 84, 66, 30, [84+43]),
    ("Header T", 84, 66, 30, [84+43]),
    ("Row 1 Q", 154, 120, 30, [154+52, 154+52+34]),
    ("Row 1 T", 154, 120, 24, [154+36, 154+36+28, 154+36+56]),
    ("Row 2 Q", 286, 100, 30, [286+43, 286+43+34]),
    ("Row 2 T", 286, 100, 24, [286+52]),
    ("Row 3 Q", 398, 100, 30, [398+43, 398+43+34]),
    ("Row 3 T", 398, 100, 24, [398+45, 398+45+28]),
    ("Row 4 Q", 510, 86, 30, [510+53]),
    ("Row 4 T", 510, 86, 24, [510+52]),
    ("Row 5 Q", 608, 86, 30, [608+53]),
    ("Row 5 T", 608, 86, 24, [608+52]),
    ("Row 6 Q", 706, 86, 30, [706+53]),
    ("Row 6 T", 706, 86, 24, [706+52]),
    ("Row 7 Q", 804, 86, 30, [804+53]),
    ("Row 7 T", 804, 86, 26, [804+52]),
    ("Chain strip", 906, 80, 26, [906+48]),
    ("Bottom bar", 1004, 64, 28, [1004+40])
]

print("Vertical padding audit:")
for name, ry, rh, fs, baselines in boxes:
    top_text = baselines[0] - 0.75 * fs
    bot_text = baselines[-1] + 0.22 * fs
    pad_top = top_text - ry
    pad_bot = (ry + rh) - bot_text
    print(f"{name:12s}: pad_top={pad_top:.1f}px, pad_bot={pad_bot:.1f}px")
    assert pad_top >= 16, f"{name} pad_top < 16: {pad_top}"
    assert pad_bot >= 16, f"{name} pad_bot < 16: {pad_bot}"

print("\nALL VERTICAL PADDINGS >= 16px! (PASS)")
