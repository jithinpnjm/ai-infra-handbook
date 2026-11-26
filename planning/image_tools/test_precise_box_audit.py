import re

# Conservative text metric calculation:
# For font-size fs:
# Width: 0.6 * fs * num_chars (or 0.62 for monospace)
# Height:
# Top of glyph: y - 0.75 * fs
# Bottom of glyph: y + 0.25 * fs
# Between line 1 and line N:
# glyph_top = y1 - 0.75 * fs
# glyph_bottom = yN + 0.25 * fs

def check_box(name, box_x, box_y, box_w, box_h, lines, x_start, y_start, line_height, fs=24):
    print(f"--- Checking {name} ---")
    print(f"Box: x={box_x}, y={box_y}, w={box_w}, h={box_h} (Right: {box_x+box_w}, Bottom: {box_y+box_h})")
    
    pad_left_min = 999
    pad_right_min = 999
    
    y_current = y_start
    glyph_top = y_start - 0.75 * fs
    glyph_bottom = 0
    
    for i, line in enumerate(lines):
        w = len(line) * fs * 0.6
        x1 = x_start
        x2 = x_start + w
        
        pad_l = x1 - box_x
        pad_r = (box_x + box_w) - x2
        
        pad_left_min = min(pad_left_min, pad_l)
        pad_right_min = min(pad_right_min, pad_r)
        
        glyph_bottom = y_current + 0.25 * fs
        y_current += line_height
        
    pad_top = glyph_top - box_y
    pad_bottom = (box_y + box_h) - glyph_bottom
    
    print(f"Paddings: Left={pad_left_min:.1f}, Right={pad_right_min:.1f}, Top={pad_top:.1f}, Bottom={pad_bottom:.1f}")
    assert pad_left_min >= 16, f"Left padding fail: {pad_left_min}"
    assert pad_right_min >= 16, f"Right padding fail: {pad_right_min}"
    assert pad_top >= 16, f"Top padding fail: {pad_top}"
    assert pad_bottom >= 16, f"Bottom padding fail: {pad_bottom}"
    print("✓ PASSED ALL 4 PADDINGS >= 16px!")

# Test Scenario Box:
check_box("Scenario", 40, 96, 740, 96, 
          ["every health check green, average latency",
           "fine, one replica buried under long",
           "generations while the others sit idle"],
          x_start=114, y_start=126, line_height=26, fs=24)

