def check_box(label, text_lines, box_x, box_y, box_w, box_h, align="left", font_family="sans"):
    factor = 0.62 if font_family == "monospace" else 0.6
    for i, (line_text, fs, baseline_y, anchor_x) in enumerate(text_lines):
        line_w = len(line_text) * fs * factor
        if align == "middle":
            t_left = anchor_x - line_w / 2
            t_right = anchor_x + line_w / 2
        elif align == "right":
            t_left = anchor_x - line_w
            t_right = anchor_x
        else: # left
            t_left = anchor_x
            t_right = anchor_x + line_w
        
        pad_left = t_left - box_x
        pad_right = (box_x + box_w) - t_right
        pad_top = (baseline_y - fs) - box_y
        pad_bottom = (box_y + box_h) - baseline_y
        
        msg = f"'{line_text}' in {label}: pad_l={pad_left:.1f}, pad_r={pad_right:.1f}, pad_t={pad_top:.1f}, pad_b={pad_bottom:.1f}"
        if pad_left < 16 or pad_right < 16 or pad_top < 16 or pad_bottom < 16:
            print("FAIL:", msg)
            return False
        else:
            print("PASS:", msg)
    return True

print("Test harness ready")
