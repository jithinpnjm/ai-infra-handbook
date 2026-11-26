import re

# Font width formulas from prompt:
# sans: 0.6 * font-size per character
# monospace: 0.62 * font-size per character

def text_width(text, fs=24, is_mono=False):
    factor = 0.62 if is_mono else 0.6
    return len(text) * factor * fs

print("Testing text widths...")
