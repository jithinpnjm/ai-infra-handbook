import re

# Font width estimators:
# sans: 0.6 * fs
# mono: 0.62 * fs

def measure(segs):
    total = 0
    for text, is_mono, fs in segs:
        cw = (0.62 if is_mono else 0.6) * fs
        total += len(text) * cw
    return total

# Card dimensions
card_w = 710
card_h = 490
# Card 1: x=50, y=105, w=710, h=490. Right edge = 760.
# Card 2: x=840, y=105, w=710, h=490. Right edge = 1550.
# Corridor: y from 595 to 655 (height 60).
# Card 4: x=50, y=655, w=710, h=490. Right edge = 760.
# Card 3: x=840, y=655, w=710, h=490. Right edge = 1550.

# Available text width in card:
# card_w = 710. If text starts at x_rel = 35, x_end_rel = 675 -> width = 640.
# 710 - 640 = 70px total margin (35px left, 35px right) >= 16px required padding!

print(f"Max text width allowed: 640px")
