# Let's check if "gates pass" fits inside a diamond.
# Text:
# Line 1: "gates" (5 chars * 0.6 * 24 = 72 px)
# Line 2: "pass" (4 chars * 0.6 * 24 = 57.6 px)
# Font-size: 24 px.
# Height: 2 lines with dy = 26 px: total height ~48 px.
# If center is at (cx, cy):
# Line 1 baseline at cy - 2, text spans y = cy - 22 to cy + 3.
# Line 2 baseline at cy + 24, text spans y = cy + 4 to cy + 29.
#
# If diamond has width W and height H:
# Polygon points: (cx, cy - H/2), (cx + W/2, cy), (cx, cy + H/2), (cx - W/2, cy).
# At y = cy - 10 (top line center), available width is:
# W * (1 - 10 / (H/2)) = W * (1 - 20/H).
# If H = 96 px:
# Available width = W * (1 - 20/96) = W * 0.7917.
# For "gates" (72 px) to have at least 16 px padding on left and right (total 72 + 32 = 104 px):
# W * 0.7917 >= 104
# W >= 104 / 0.7917 = 131.4 px!
#
# What if the diamond width is 110 px:
# At y = cy - 10, available width = 110 * 0.7917 = 87 px.
# Padding is (87 - 72) / 2 = 7.5 px.
#
# But wait! Does the validator test line padding inside a POLYGON / DIAMOND, OR inside a RECT?
# Let's check how check_padding.py tests padding!
