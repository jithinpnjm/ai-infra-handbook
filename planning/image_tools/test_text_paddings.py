# Verify padding of every text line inside its box

def check_box(name, box_x, box_y, box_w, box_h, lines, font_type, font_size, text_x, text_y, line_height, icon_rect=None):
    char_w = 0.62 * font_size if font_type == "mono" else 0.6 * font_size
    print(f"\n--- Checking {name} ---")
    print(f"Box: x={box_x}, y={box_y}, w={box_w}, h={box_h} | Text start: x={text_x}, y={text_y}, fs={font_size}")
    
    # Check vertical bounds
    # In SVG, text baseline is at text_y. The ascent is roughly 0.8 * font_size, descent is 0.2 * font_size.
    # Total text block top = text_y - 0.8 * font_size
    # Total text block bottom = text_y + (len(lines) - 1) * line_height + 0.25 * font_size
    top_pad = (text_y - 0.8 * font_size) - box_y
    bot_pad = (box_y + box_h) - (text_y + (len(lines) - 1) * line_height + 0.25 * font_size)
    print(f"  Vertical pad: top={top_pad:.1f}px, bottom={bot_pad:.1f}px")
    assert top_pad >= 16, f"{name}: top padding {top_pad:.1f} < 16"
    assert bot_pad >= 16, f"{name}: bottom padding {bot_pad:.1f} < 16"

    # Check horizontal bounds for each line
    for i, line in enumerate(lines):
        # strip any trailing space for width calc
        clean_line = line.strip()
        width = len(clean_line) * char_w
        left_pad = text_x - box_x
        right_pad = (box_x + box_w) - (text_x + width)
        print(f"  Line {i+1}: '{clean_line[:30]}...' len={len(clean_line)} w={width:.1f}px | left_pad={left_pad:.1f}px, right_pad={right_pad:.1f}px")
        assert left_pad >= 16, f"{name} line {i+1}: left padding {left_pad:.1f} < 16"
        assert right_pad >= 16, f"{name} line {i+1}: right padding {right_pad:.1f} < 16"
        
        # Check icon collision if icon present
        if icon_rect:
            ix, iy, iw, ih = icon_rect
            # Icon is at left of text. Ensure text_x >= ix + iw + 10
            assert text_x >= ix + iw + 10, f"{name}: text touches icon!"

print("Check helper defined.")
# 1. f1
# "[gpu] gpu01 ansible_host=10.0.10.11, gpu02 ansible_host=10.0.10.12"
# box: 40, 90, 760, 100
# lines:
# Line 1: "[gpu] "
# Line 2: "gpu01 ansible_host=10.0.10.11, " (30 chars)
# Line 3: "gpu02 ansible_host=10.0.10.12" (29 chars)
# icon at (60, 112, 56, 56). text_x = 135, text_y = 120, line_height = 28
# wait, 3 lines at line_height 28:
# text_y = 122. line 1: 122, line 2: 150, line 3: 178.
# top_pad = 122 - 0.8*24 - 90 = 122 - 19.2 - 90 = 12.8 < 16!
# To get top_pad >= 16: text_y >= 90 + 16 + 19.2 = 125.2.
# If text_y = 126, line 3 = 126 + 56 = 182.
# bot_pad = 90 + h - (182 + 6) = 90 + h - 188.
# To get bot_pad >= 16: h >= 188 - 90 + 16 = 114.
# So box height for f1 should be 115 px!
