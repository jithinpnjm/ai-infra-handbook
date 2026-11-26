import re

# Font conservative widths:
# sans: 0.6 * fs * chars
# mono: 0.62 * fs * chars
# Every line must have >= 16px padding on left and right inside its box.

def check_line_fits(line, box_width, fs=24, is_mono=False, pad=20):
    factor = 0.62 if is_mono else 0.6
    w = len(line) * factor * fs
    rem_pad = (box_width - w) / 2
    return rem_pad >= 16, w, rem_pad

# Let's test the wrapping of each label in their prospective boxes.
