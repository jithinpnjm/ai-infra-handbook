#!/usr/bin/env python3

# Right panel items:
# H_panel = from y=150 to y=1160 (total height = 1010)
# Panel header: y=150..220 (h=70)
# Content area: y=230..1140 (available = 910 px)

# Items:
# 1. requirements (2 lines): fs=24, dy=32 -> text height ~ 56. Box h = 88.
# 2. capacity-type (1 line): fs=24 -> text height ~ 24. Box h = 64.
# 3. zones (1 line): fs=24 -> text height ~ 24. Box h = 64.
# 4. taints (2 lines): fs=24, dy=32 -> text height ~ 56. Box h = 88.
# 5. nodeClassRef (1 line): fs=24 -> text height ~ 24. Box h = 64.
# 6. expireAfter (1 line): fs=24 -> text height ~ 24. Box h = 64.
# 7. limits (2 lines): fs=24, dy=32 -> text height ~ 56. Box h = 88.
# 8. disruption (4 lines): fs=24, dy=32 -> text height ~ 120. Box h = 156.
# 9. warning (2 lines): fs=24, dy=34 -> text height ~ 58. Box h = 96.

# Total box heights = 88 + 64 + 64 + 88 + 64 + 64 + 88 + 156 + 96 = 772 px.
# There are 8 gaps between 9 items.
# Available height = 1140 - 230 = 910 px.
# Remaining space for gaps = 910 - 772 = 138 px.
# 138 / 8 = ~17.25 px per gap!

# What if H = 1180 or 1200?
# If canvas H = 1200:
# Available panel height = 1200 - 150 - 40 = 1010 px.
# If header y = 150..215 (h = 65).
# Start items at y = 225.
# Total items height + gaps:
# If gap = 16 px, 8 * 16 = 128 px.
# 772 + 128 = 900 px.
# 225 + 900 = 1125 <= 1160! Plenty of room!

print("Vertical budget fits comfortably!")
