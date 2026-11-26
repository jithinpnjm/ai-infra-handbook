# Font metrics for 24px text:
# ascent: ~18px, descent: ~6px
# For 30px bold text:
# ascent: ~23px, descent: ~7px
# For 48px bold title:
# ascent: ~36px, descent: ~12px

def audit_card(box_name, bx, by, bw, bh, text_lines, fs=24, is_mono=False, text_anchor="start"):
    # Check outside canvas
    if bx < 40 or bx + bw > 1560 or by < 40 or by + bh > 1160:
        print(f"[FAIL] {box_name} outside canvas margin 40px: x=[{bx}, {bx+bw}], y=[{by}, {by+bh}]")
        return False
    
    char_w = 14.88 if is_mono else 14.4
    ascent = 18 if fs == 24 else (23 if fs == 30 else 36)
    descent = 6 if fs == 24 else (7 if fs == 30 else 12)
    
    # Check padding for all lines
    for line_text, lx, ly in text_lines:
        line_w = len(line_text) * char_w
        if text_anchor == "middle":
            x_min = lx - line_w / 2
            x_max = lx + line_w / 2
        else:
            x_min = lx
            x_max = lx + line_w
        
        y_min = ly - ascent
        y_max = ly + descent
        
        pad_left = x_min - bx
        pad_right = (bx + bw) - x_max
        pad_top = y_min - by
        pad_bottom = (by + bh) - y_max
        
        if pad_left < 15.5 or pad_right < 15.5 or pad_top < 15.5 or pad_bottom < 15.5:
            print(f"[FAIL] {box_name} text padding violation for '{line_text[:30]}...':")
            print(f"       L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
            return False
            
    print(f"[PASS] {box_name}: min pads L={pad_left:.1f}, R={pad_right:.1f}, T={pad_top:.1f}, B={pad_bottom:.1f}")
    return True

print("Audit script template ready")
