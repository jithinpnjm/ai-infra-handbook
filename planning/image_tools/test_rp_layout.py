#!/usr/bin/env python3
import math

# Test coordinates for the decision tree in Right Panel
# Right Panel: x = 625 to 1560, width = 935
# Inside padding: left = 25, right = 25 -> available width = 885
# Col 1 (Diamonds): x = 650 to 1050 (width = 400)
# Gap between Col 1 and Col 2: 50 px
# Col 2 (Leaves): x = 1100 to 1530 (width = 430)
# Available horizontal: 400 + 50 + 430 = 880 px! (Fits in 885 with 25px margins!)

# Vertical spacing inside Right Panel:
# Header: 'Bisect from the middle' at y = 115
# Row 1 (D1, L1): y = 145 to 255 (h = 110)
# gap = 45
# Row 2 (D2, L2): y = 300 to 410 (h = 110)
# gap = 45
# Row 3 (D3, L3): y = 455 to 565 (h = 110)
# gap = 45
# Row 4 (L4): y = 610 to 720 (h = 110)
# gap = 45
# Comparison note: y = 765 to 875 (h = 110) or y = 780 to 860 (h = 80)
# Panel bottom at y = 960!

print("Vertical breakdown in Right Panel:")
rows = [
    ("Row 1 D1/L1", 145, 255),
    ("Row 2 D2/L2", 300, 410),
    ("Row 3 D3/L3", 455, 565),
    ("Row 4 L4", 610, 720),
    ("Comparison Note", 765, 870),
]
for name, y1, y2 in rows:
    print(f"{name:15s}: y={y1}..{y2} (h={y2-y1})")
