# For font-size 24:
# cap-height ~ 17 px, descent ~ 6 px.
# Total line height ~ 23 px.
# If baseline is y_b:
# Text top = y_b - 17
# Text bottom = y_b + 6

# For multi-line with dy=28:
# Line 1 baseline: y_b
# Line 2 baseline: y_b + 28
# Line 1 top: y_b - 17
# Line N bottom: y_b + (N-1)*dy + 6
# Box must have:
# box_y <= Text top - 16  ==> box_y <= y_b - 33
# box_y + box_h >= Text bottom + 16 ==> box_h >= (Text bottom + 16) - box_y

def check_v_padding(name, box_y, box_h, first_baseline, dy, num_lines, fs=24):
    cap = 0.72 * fs
    descent = 0.25 * fs
    text_top = first_baseline - cap
    text_bottom = first_baseline + (num_lines - 1) * dy + descent
    pad_top = text_top - box_y
    pad_bottom = (box_y + box_h) - text_bottom
    print(f"{name}: top_pad={pad_top:.1f}px, bottom_pad={pad_bottom:.1f}px (box_h={box_h})")
    assert pad_top >= 15.5, f"{name}: top_pad {pad_top:.1f} < 16!"
    assert pad_bottom >= 15.5, f"{name}: bottom_pad {pad_bottom:.1f} < 16!"

print("Checking paddings for test values...")
