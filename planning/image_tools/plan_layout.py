import re

# Font estimation factors
SANS_FACTOR = 0.60
MONO_FACTOR = 0.62

def check_line_width(text, font_size, is_mono):
    factor = MONO_FACTOR if is_mono else SANS_FACTOR
    return len(text) * font_size * factor

print("Testing text widths...")
