# Let's test a complete layout and check:
# 1. Box dimensions for text fit (no overflow, padding >= 16px)
# 2. Font sizes (>= 30px bold for titles, >= 24px for secondary)
# 3. Arrow paths (orthogonal, no crossings, no touching nodes)

import math

def check_text_fit(box_w, box_h, lines, font_sizes, font_types, has_icon=True):
    # has_icon = True means icon is either above (56px + gap) or left (56px + gap)
    # Let's say icon is placed at top center (56px high + 10px gap)
    icon_h = 66 if has_icon else 0
    total_text_h = sum(fs * 1.3 for fs in font_sizes)
    required_h = icon_h + total_text_h + 32 # 16px top + 16px bottom padding
    
    max_line_w = 0
    for text, fs, ftype in zip(lines, font_sizes, font_types):
        coeff = 0.62 if ftype == 'mono' else 0.60
        lw = len(text) * coeff * fs
        if lw > max_line_w:
            max_line_w = lw
    required_w = max_line_w + 32 # 16px left + 16px right padding
    
    fits = (box_w >= required_w) and (box_h >= required_h)
    return fits, required_w, required_h

print("Checker function ready")
