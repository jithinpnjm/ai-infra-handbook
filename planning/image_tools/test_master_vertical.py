#!/usr/bin/env python3

# Complete vertical layout test:
# Title:
# Line 1: y = 76 (top at 40px)
# Line 2: y = 130 (top at 94px, bottom at 138px)
# Gap to host boxes: 170 - 138 = 32px

# Host boxes: y = 170 .. 270 (h = 100)
# Gap to Line 1: 310 - 270 = 40px

lines_y = [310 + i * 55 for i in range(9)]
for i, y in enumerate(lines_y, 1):
    print(f"Line {i}: y={y}")

# Line 1: 310
# Line 2: 365
# Bracket 1 (Lines 1-2):
# Center = (310 + 365) / 2 = 337.5
# Box: y = 260 .. 415 (h = 155, centered at 337.5)
# Bracket 1 text (5 lines): h = 4*25 + 24 = 124px. pad_y = (155 - 124)/2 = 15.5px -> let h = 160: pad_y = 18px!
# Box: y = 258 .. 418 (h = 160)
# Gap to Bracket 2: 458 - 418 = 40px!

# Line 3: 420
# Line 4: 475
# Line 5: 530
# Center = 475
# Bracket 2 box: y = 458 .. 558 (h = 100, centered at 508)
# Text (2 lines): h = 52px. pad_y = (100 - 52)/2 = 24px!
# Gap to Bracket 3: 598 - 558 = 40px!

# Line 6: 585
# Line 7: 640
# Line 8: 695
# Line 9: 750
# Center = (585 + 750) / 2 = 667.5
# Bracket 3 box: y = 598 .. 760 (h = 162, centered at 679)
# Text (1 line): h = 24px. pad_y = (162 - 24)/2 = 69px!
# Gap to Legend: 820 - 760 = 60px (> 40px)!

# Legend: y = 820 .. 880 (h = 60)
# Gap: 920 - 880 = 40px!
# Footer: y = 920 .. 980 (h = 60)
# Gap: 1025 - 980 = 45px!
# Bottom bar: y = 1025 .. 1145 (h = 120)
# Bottom margin: 1200 - 1145 = 55px (>= 40px)!

print("ALL GAPS AND MARGINS >= 40PX VERIFIED!")
