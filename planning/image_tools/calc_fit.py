import xml.etree.ElementTree as ET

# Font metrics:
# 30px font: cap_top = y - 22, bot = y + 7. Total glyph height = 29. Min box height for 16px pad = 29 + 32 = 61.
# But wait: if text is single line, can we center it?
# At y0: pad_top = (y0 - 22) - ry >= 16 => y0 >= ry + 38
# pad_bot = (ry + rh) - (y0 + 7) >= 16 => ry + rh >= y0 + 23 => rh >= (y0 - ry) + 23 >= 38 + 23 = 61!
# What about 24px font?
# cap_top = y - 17, bot = y + 6. Total glyph height = 23.
# 1 line 24px: min height = 23 + 32 = 55. y0 = ry + 33.
# 2 lines 24px (dy=27): top = y0 - 17, bot = y0 + 27 + 6 = y0 + 33. Total height = 50. Min box height = 50 + 32 = 82. y0 = ry + 33.
# 3 lines 24px (dy=27): top = y0 - 17, bot = y0 + 54 + 6 = y0 + 60. Total height = 77. Min box height = 77 + 32 = 109. y0 = ry + 33.
# 4 lines 24px (dy=26): top = y0 - 17, bot = y0 + 78 + 6 = y0 + 84. Total height = 101. Min box height = 101 + 32 = 133. y0 = ry + 33.

# Let's check 2 lines of 30px (e.g. Row titles in Col 0):
# top = y0 - 22, bot = y0 + 34 + 7 = y0 + 41. Total height = 63. Min height = 63 + 32 = 95. y0 = ry + 38.

# Let's sum the minimum box heights:
# Headers (30px 1 line): 61
# Row 1 (3 lines 24px): 110
# Row 2 (4 lines 24px): 134
# Row 3 (3 lines 24px): 110
# Row 4 (3 lines 24px): 110
# Row 5 (3 lines 24px): 110
# Row 6 (4 lines 24px): 134
# Costs (3 lines 24px): 110
# Footer (2 lines 24px): 82
# Bottom bar (1 line 24px): 56
# Total box heights = 61 + 110 + 134 + 110 + 110 + 110 + 134 + 110 + 82 + 56 = 1017 px!

# Plus gaps between elements:
# We have 10 elements -> 9 gaps of 8px = 72px.
# Top title: y = 38. Header top = 60. (title height ~ 45px).
# Bottom margin: 1200 - (60 + 1017 + 72) = 1200 - 1149 = 51 px!
# It fits easily within 1200!

print(f"Total needed: 60 + 1017 + 72 = 1149 px < 1200 px!")
