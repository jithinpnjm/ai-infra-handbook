import re

# Font estimation functions
def text_width(text, font_family, font_size):
    rate = 0.62 if font_family == "monospace" else 0.60
    return len(text) * rate * font_size

def font_height_bounds(baseline_y, font_size):
    ascent = 0.75 * font_size
    descent = 0.22 * font_size
    top = baseline_y - ascent
    bottom = baseline_y + descent
    return top, bottom

# Let's inspect test_adjusted.svg paddings!
import xml.etree.ElementTree as ET
tree = ET.parse("test_adjusted.svg")
root = tree.getroot()

print("Parsed test_adjusted.svg successfully!")
