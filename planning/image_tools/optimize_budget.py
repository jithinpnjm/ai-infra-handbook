# Total H available: 1200
# Title: y = 42, 80 (top 20 to 86 -> 66 px).
# Start of content: y = 92
# Bottom bar: y = 1146 to 1192 (h = 46)
# Available for content: 1146 - 92 = 1054 px!
# Content has:
# Scenario: 1 box
# 5 Rows: 5 boxes
# Total items: 6 vertical blocks!
# Gaps between 6 blocks: 5 gaps * 8 px = 40 px.
# Total height for 6 blocks = 1054 - 40 = 1014 px.

# Can we allocate:
# Scenario: h = 90
# Row 1: h = 212
# Row 2: h = 160
# Row 3: h = 210
# Row 4: h = 162
# Row 5: h = 140
# Let's sum: 90 + 212 + 160 + 210 + 162 + 140 = 974 px!
# 974 + 40 (gaps) = 1014 px! That leaves 40 px of extra headroom!
print("Sum of heights:", 90 + 212 + 160 + 210 + 162 + 140)
