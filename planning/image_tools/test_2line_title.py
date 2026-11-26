#!/usr/bin/env python3

# Title:
# Line 1: y = 50
# Line 2: y = 102
# Gap: 43px
# Host boxes: y = 145 .. 245 (h = 100)
# Gap: 45px -> Line 1 at y = 290

lines_y = [290 + i * 58 for i in range(9)]
for i, y in enumerate(lines_y, 1):
    print(f"Line {i}: y={y}")

line9_y = lines_y[-1]
lifeline_end = line9_y + 30 # 784

# Legend: y = 825 .. 885 (h = 60)
# Gap: 45px
# Footer: y = 930 .. 990 (h = 60)
# Gap: 45px
# Bottom bar: y = 1035 .. 1150 (h = 115)
# Margin to 1200: 1200 - 1150 = 50px (> 40px)!

print(f"Line 9: y={line9_y}")
print(f"Legend: 825..885")
print(f"Footer: 930..990")
print(f"Bottom bar: 1035..1150")
print(f"Bottom margin: {1200 - 1150}px")
assert 1200 - 1150 >= 40
print("Vertical budget with 2-line title FITS PERFECTLY!")
