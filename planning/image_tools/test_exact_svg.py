# Let's write a python script to assemble the complete SVG and validate it.
from build_svg import col1_wrapped, col2_wrapped, col3_wrapped

# Layout parameters:
W = 1600
H = 1200

# Top Title
# y = 60, font 48px bold

# Columns
COL_Y = 105
COL_H = 965
COL_W = 480
GAP = 40
c1_x = 40
c2_x = 560
c3_x = 1080

# Card width inside columns:
# Column width = 480.
# Card x = col_x + 16, card width = 448.
# Text x = card_x + 224 (centered) or text x = card_x + 24 (left-aligned).
# Let's check text alignment:
# Left-aligned text with 24px left margin gives 448 - 48 = 400px inner width.
# Conservative max line len = 27 chars * 14.4 = 388.8px.
# With card width = 448:
# card_x + 25 -> 25 + 388.8 = 413.8. Right padding = 448 - 413.8 = 34.2px >= 16px!
# Or text-anchor="middle" at card_x + 224:
# 388.8 / 2 = 194.4px on each side of center.
# Center 224 - 194.4 = 29.6px padding on left, 29.6px padding on right!
# Let's decide whether left-aligned or centered looks better for paragraphs:
# Left-aligned is standard for reading multi-line prose, or centered?
# Left-aligned with text-anchor="start" at card_x + 28:
# 28px left padding, right edge = 28 + 388.8 = 416.8px. Card width = 448px -> right padding = 31.2px!
# Both left (28px) and right (31.2px) are >= 16px!

# Card heights:
# Col 1:
# Card 1: 5 lines. Line height 28px. 4 * 28 + 24 = 136px text. Pad top 20, bot 20 -> 176px.
# Card 2: 7 lines. 6 * 28 + 24 = 192px text. Pad top 20, bot 20 -> 232px.
# Card 3: 6 lines. 5 * 28 + 24 = 164px text. Pad top 20, bot 20 -> 204px.
# Card 4: 4 lines. 3 * 28 + 24 = 108px text. Pad top 20, bot 20 -> 148px.
# Sum = 176 + 232 + 204 + 148 = 760px.
# Gaps: 3 gaps of (800 - 760) / 3 = 40 / 3 = ~13.3px, or 14px -> 760 + 42 = 802px.

# Col 2:
# Card 1: 13 lines. 12 * 28 + 24 = 360px text. Pad top 20, bot 20 -> 400px.
# Card 2: 3 lines. 2 * 28 + 24 = 80px text. Pad top 20, bot 20 -> 120px.
# Card 3: 7 lines. 6 * 28 + 24 = 192px text. Pad top 20, bot 20 -> 232px.
# Sum = 400 + 120 + 232 = 752px.
# Gaps: 2 gaps of 25px = 50px -> 802px.

# Col 3:
# Card 1: 2 lines. 1 * 28 + 24 = 52px text. Pad top 36, bot 36 -> 124px.
# Card 2: 4 lines. 3 * 28 + 24 = 108px text. Pad top 36, bot 36 -> 180px.
# Card 3: 4 lines. 3 * 28 + 24 = 108px text. Pad top 36, bot 36 -> 180px.
# Card 4: 5 lines. 4 * 28 + 24 = 136px text. Pad top 41, bot 41 -> 218px.
# Sum = 124 + 180 + 180 + 218 = 702px.
# Gaps: 3 gaps of 33px = 100px -> 802px!

# All three columns start cards at y = 250 and end at y = 1052!
# Bottom of column panel: y = 1068.
# Bottom takeaway bar: y = 1090 to 1170 (height 80px).
# Canvas ends at 1200.

print("Col 1 sum + gaps:", 760 + 42)
print("Col 2 sum + gaps:", 752 + 50)
print("Col 3 sum + gaps:", 702 + 100)
