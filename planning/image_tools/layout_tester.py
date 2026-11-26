#!/usr/bin/env python3
import sys

def check_fit(text_lines, box_x, box_y, box_w, box_h, font_size, is_mono=False, has_icon=False, icon_pos="top"):
    padding = 16
    char_factor = 0.62 if is_mono else 0.60
    
    # Check horizontal fit
    max_line_w = 0
    avail_w = box_w - 2 * padding
    if has_icon and icon_pos == "left":
        avail_w -= 65 # 56px icon + 9px gap
        
    for line in text_lines:
        line_w = len(line) * char_factor * font_size
        if line_w > max_line_w:
            max_line_w = line_w
        if line_w > avail_w:
            print(f"[FAIL WIDTH] '{line}' ({len(line)} chars): {line_w:.1f}px > avail {avail_w:.1f}px (box_w={box_w})")
            return False
            
    # Check vertical fit
    line_height = font_size * 1.3
    total_text_h = len(text_lines) * line_height
    avail_h = box_h - 2 * padding
    if has_icon and icon_pos == "top":
        avail_h -= 65 # 56px icon + 9px gap
        
    if total_text_h > avail_h:
        print(f"[FAIL HEIGHT] Total text height {total_text_h:.1f}px > avail {avail_h:.1f}px (box_h={box_h})")
        return False
        
    return True

print("Helper defined.")
