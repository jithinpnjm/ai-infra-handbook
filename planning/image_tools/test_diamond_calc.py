def check_diamond_multiline(w, h, max_chars, num_lines, font_size=30, line_height=34):
    tw = max_chars * font_size * 0.6
    th = (num_lines - 1) * line_height + font_size
    pad = 16
    val = (tw/2 + pad)/(w/2) + (th/2 + pad)/(h/2)
    print(f"Diamond {w}x{h} multi-line ({font_size}px): tw={tw:.1f}, th={th:.1f}, capacity val={val:.3f} ({'PASS' if val <= 1.0 else 'FAIL'})")

# "a succeeds?" -> "a" / "succeeds?" (9 chars, 2 lines)
# "b succeeded?" -> "b" / "succeeded?" (10 chars, 2 lines)
for w in [320, 340, 360, 380]:
    for h in [130, 140, 150]:
        check_diamond_multiline(w, h, 10, 2, 30, 34)
