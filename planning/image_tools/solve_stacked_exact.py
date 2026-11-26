# Let's test stacked vertical layout coordinates:
# Total canvas: 1600 x 1200

# Margins:
# Left = 50, Right = 50 (width 1500)
# Top >= 40, Bottom >= 40
# Gaps between nodes >= 40

# Let's check:
# Title: baseline y = 56
# Subtitle Pill:
# Box: x = 450, y = 74, w = 700, h = 58
# Text: baseline y = 110 (glyph top 82, bottom 116 -> top pad 16px, bot pad 16px)

# Gap: 42px -> Node 1 (Setup) starts at y = 174
# Setup Box:
# x = 50, y = 174, w = 1500, h = 94
# Text (2 lines):
# Line 1: baseline y = 213 (glyph top 195 -> top pad 21px)
# Line 2: baseline y = 247 (glyph bot 253 -> bot pad 21px)
# Gear Icon: x = 75, y = 193 (56x56)

# Gap: 42px -> Node 2 (Table 1) starts at y = 310
# Table 1:
# Header: 30px bold. Single line!
# Text: "Table 1 policy: hit rate, p50 s, p99 s, max over mean load"
# Length 58 chars. At 30px: 58 * 0.6 * 30 = 1044px.
# In 1468px: pad left = 20px, pad right = 404px!
# Header box: x = 66, y = 322, w = 1468, h = 58
# Header baseline = 360 (glyph top 337 -> top pad 15px? Make h = 60: y = 320..380, baseline = 360: top pad 360-22.5-320 = 17.5px, bot pad 380 - (360+6.6) = 13.4px?
# Wait! Let's check 30px glyph height in Chromium:
# In Chromium, 30px font bbox height is ~35px (ascent ~27, descent ~8).
# For h = 68 (y = 320..388), baseline = 362:
# top pad = 362 - 27 - 320 = 15px.
# Let's check exact Chromium measurements!)
