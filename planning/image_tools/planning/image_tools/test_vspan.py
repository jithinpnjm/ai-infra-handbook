#!/usr/bin/env python3

# Test vertical layout solver for H=1200

# Top Title:
# Title at 48px:
# y1 = 44, y2 = 92 (dy = 48)
# Title top = 44 - 48 = -4? No, title text at y=48 has ascender 36 => 48 - 36 = 12.
# If title baseline 1 is y=44: top = 44 - 36 = 8 px from top.
# But margin rule says: "Leave at least 40 px outside margin."
# Outside margin >= 40 px means no text or shape closer than 40 px to canvas edge!
# So title top >= 40!
# If title top = 40, baseline 1 is y = 40 + 36 = 76!
# Line 2 baseline is y = 76 + 50 = 126!
# Title bottom = 126 + 12 = 138.
# Then Table Header starts at y = 158, height = 44 (ends at 202).
# Wait, let's check:
# Outside margin: left >= 40, right <= 1560, top >= 40, bottom <= 1160!
# Available vertical span between Header (y=158) and Bottom bar end (y=1160) is:
# 1160 - 158 = 1002 px!

print("Available span: 1002 px")
