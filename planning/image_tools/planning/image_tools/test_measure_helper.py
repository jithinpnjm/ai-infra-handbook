#!/usr/bin/env python3
import re

# Font estimation functions according to luna_rules.md:
# sans: 0.6 * font_size per character
# monospace: 0.62 * font_size per character
def text_width(text, font_size, is_mono=False):
    factor = 0.62 if is_mono else 0.60
    return len(text) * font_size * factor

print("Font measurement helper loaded.")
