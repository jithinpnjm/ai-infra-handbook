#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

def compute_text_bounds(lines, font_family, font_size, x, y, dy):
    # lines is a list of strings
    # multiplier:
    mult = 0.62 if "mono" in font_family else 0.6
    max_w = max(len(l) * font_size * mult for l in lines)
    
    # baseline of line 0 is y
    # top of line 0 is y - font_size
    # baseline of line k is y + k * dy
    # bottom of line k is y + k * dy + 0.25 * font_size (approx descent)
    top = y - font_size
    bot = y + (len(lines) - 1) * dy + 0.25 * font_size
    return x, top, max_w, bot - top, bot

print("Layout helper loaded")
