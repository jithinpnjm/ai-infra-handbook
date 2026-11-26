def check_pad(box_name, bx, by, bw, bh, lines, font_size, is_mono, text_anchor="middle", tx=None, start_y=None, line_spacing=32):
    rate = 0.62 if is_mono else 0.6
    max_w = max(len(l) * font_size * rate for l in lines)
    
    # Horizontal padding
    if text_anchor == "middle":
        # centered at tx
        left = tx - max_w / 2
        right = tx + max_w / 2
        pad_left = left - bx
        pad_right = (bx + bw) - right
    elif text_anchor == "start":
        pad_left = tx - bx
        pad_right = (bx + bw) - (tx + max_w)
    
    # Vertical padding
    # Font ascender roughly 0.75 * font_size, descender roughly 0.25 * font_size
    top_text = start_y - 0.75 * font_size
    bottom_text = (start_y + (len(lines) - 1) * line_spacing) + 0.25 * font_size
    pad_top = top_text - by
    pad_bottom = (by + bh) - bottom_text
    
    ok = (pad_left >= 16 and pad_right >= 16 and pad_top >= 16 and pad_bottom >= 16)
    print(f"[{'PASS' if ok else 'FAIL'}] {box_name:25s}: pad_l={pad_left:5.1f}, pad_r={pad_right:5.1f}, pad_t={pad_top:5.1f}, pad_b={pad_bottom:5.1f} | max_w={max_w:5.1f}, bw={bw}")
    return ok

print("Testing padding calculator:")
check_pad("Test box", 100, 100, 300, 80, ["Line 1", "Line 2"], 24, False, "middle", 250, 135, 30)
