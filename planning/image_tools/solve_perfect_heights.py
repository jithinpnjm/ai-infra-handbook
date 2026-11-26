# Total canvas height: H = 1200.
# Available vertical span for boxes: from y = 100 to y = 1145 (bottom margin 55px >= 40px).
# Total span = 1045px.
# 6 gaps of 40px each = 240px.
# Remaining height for the 7 rows: 1045 - 240 = 805px.

# Heights allocation:
# Row 1 (Gates): h = 125px (Icon: 56px -> (125-56)/2 = 34.5px top/bot)
# Row 2 (Rule 1): h = 165px (Icon: 56px -> (165-56)/2 = 54.5px top/bot)
# Row 3 (Rule 2): h = 88px (Icon: 56px -> (88-56)/2 = 16.0px top/bot)
# Row 4 (Rule 3): h = 104px (Icon: 56px -> (104-56)/2 = 24.0px top/bot)
# Row 5 (Rule 4): h = 88px (Icon: 56px -> (88-56)/2 = 16.0px top/bot)
# Row 6 (Cache/Router): h = 165px (Icon: 56px -> (165-56)/2 = 54.5px top/bot)
# Row 7 (Takeaway): h = 110px (Icon: 56px -> (110-56)/2 = 27.0px top/bot)
# Total box height = 125 + 165 + 88 + 104 + 88 + 165 + 110 = 845px.
# Total height with 6 gaps of 40px = 845 + 240 = 1085px.
# Starting at y = 75: 75 + 1085 = 1160px.
# Bottom margin = 1200 - 1160 = 40px >= 40px!
# Top margin = 75px >= 40px! Title at y = 48.

y_start = 75
gaps = 40

rows = [
    ("Row 1 (Gates)", 125),
    ("Row 2 (Rule 1)", 165),
    ("Row 3 (Rule 2)", 88),
    ("Row 4 (Rule 3)", 104),
    ("Row 5 (Rule 4)", 88),
    ("Row 6 (Rules cache/router)", 165),
    ("Row 7 (Takeaway)", 110)
]

cur_y = y_start
box_coords = []
for name, h in rows:
    box_coords.append((name, cur_y, h))
    cur_y += h + gaps

print("Box positions:")
for name, y, h in box_coords:
    print(f"  {name:25s}: y={y:4d}..{y+h:4d} (h={h:3d})")

print(f"\nLast box ends at: {cur_y - gaps}px")
print(f"Canvas H = 1200, bottom margin: {1200 - (cur_y - gaps)}px")
