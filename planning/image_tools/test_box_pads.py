def check_box_paddings(x, y, w, h, text_lines, fs=24, is_mono=False, dy=25):
    # Glyphs bounding box:
    # Width per char: 0.62 * fs if mono else 0.60 * fs
    char_w = 0.62 * fs if is_mono else 0.60 * fs
    ascent = 0.75 * fs
    descent = 0.25 * fs
    
    # Text starts at ty = y + top_pad + ascent
    # Let's say top_pad is at least 16
    # Let's find optimal ty
    n = len(text_lines)
    text_block_height = (n - 1) * dy + fs
    avail_v = h - text_block_height
    top_pad = avail_v / 2
    bot_pad = avail_v / 2
    
    # Baseline of first line:
    ty = y + top_pad + ascent
    
    print(f"Box ({w}x{h}): {n} lines, dy={dy}, top_pad={top_pad:.1f}px, bot_pad={bot_pad:.1f}px")
    assert top_pad >= 16, f"top_pad {top_pad} < 16"
    assert bot_pad >= 16, f"bot_pad {bot_pad} < 16"
    
    for i, ln in enumerate(text_lines):
        line_w = len(ln) * char_w
        left_pad = (w - line_w) / 2 # if centered, or x-pad if left aligned
        pad_avail = w - line_w
        assert pad_avail >= 32, f"Line '{ln}' width {line_w:.1f} exceeds box width {w} (pad {pad_avail:.1f} < 32)"
    print("  All lines pass padding >= 16px!")

print("Row 1 & 2 (5 lines, h=160):")
check_box_paddings(0, 0, 525, 160, ["line 1", "line 2", "line 3", "line 4", "line 5"], dy=26)

print("Row 3 & 4 (3 lines, h=110):")
check_box_paddings(0, 0, 525, 110, ["line 1", "line 2", "line 3"], dy=26)

print("Row 5 (3 lines, h=110):")
check_box_paddings(0, 0, 525, 110, ["line 1", "line 2", "line 3"], dy=26)

print("Row 6 (2 lines, h=86):")
check_box_paddings(0, 0, 525, 86, ["line 1", "line 2"], dy=26)
