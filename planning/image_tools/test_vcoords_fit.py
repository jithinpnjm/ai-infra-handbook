# Total canvas height = 1200 px.
# Top margin: 40 px -> Title at y = 50.
# Gap below title: 40 px -> y = 90.
# Bottom margin: 40 px -> Bottom bar ends at y = 1160.
# Total usable vertical space from y = 90 to y = 1160: 1070 px!

# We have 7 vertical items:
# 1. Row 1: h1
# 2. Row 2: h2
# 3. Row 3: h3
# 4. Row 4: h4
# 5. Row 5: h5
# 6. Guard strip: h6
# 7. Bottom bar: h7
# Between them are 6 gaps.
# Each gap = 40 px.
# Total gaps = 6 * 40 = 240 px.
# Total heights budget = 1070 - 240 = 830 px!

# If Bottom bar: h7 = 60 px (with baseline centered, pads = 19px)
# Leaves 830 - 60 = 770 px for the 6 boxes (R1 to R5 + Guard strip).
# If Guard strip: h6 = 145 px
# Leaves 770 - 145 = 625 px for 5 rows!
# 625 / 5 = 125 px per row!
# Exactly 125 px for each of Rows 1, 2, 3, 4, 5!
# And 145 px for Guard strip!
# And 60 px for Bottom bar!
# And 40 px for every single gap!
# And 40 px for top margin and bottom margin!

print("Testing exact coordinates:")
y = 90
for i in range(1, 6):
    print(f"Row {i}: y = {y} to {y + 125} (h = 125)")
    y += 125 + 40
print(f"Guard strip: y = {y} to {y + 145} (h = 145)")
y += 145 + 40
print(f"Bottom bar: y = {y} to {y + 60} (h = 60)")
print(f"Bottom margin: 1200 - {y + 60} = {1200 - (y + 60)} px")
