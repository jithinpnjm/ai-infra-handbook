# Total canvas height = 1200
# Title: y = 25..75 (50 px)
# Gap: 35 px -> y = 110

# 5 rows:
# R1: y = 110 to 240 (h = 130)
# Gap: 35 px -> y = 275
# R2: y = 275 to 405 (h = 130)
# Gap: 35 px -> y = 440
# R3: y = 440 to 570 (h = 130)
# Gap: 35 px -> y = 605
# R4: y = 605 to 735 (h = 130)
# Gap: 35 px -> y = 770
# R5: y = 770 to 900 (h = 130)
# Gap: 35 px -> y = 935
# Guard strip: y = 935 to 1065 (h = 130)
# Gap: 35 px -> y = 1100
# Bottom bar: y = 1100 to 1160 (h = 60)
# Bottom margin: 1200 - 1160 = 40 px!

# Wait! The gap rule says:
# "Leave at least 40 px between boxes and 40 px outside margin."
# "at least 40 px between boxes"!
# Notice: "at least 40 px"! 35 px is < 40 px!
# So EVERY gap between boxes must be >= 40 px!

print("Testing with gap >= 40 px:")
# If gap = 40 px:
# 6 gaps between the 7 vertical items: 6 * 40 = 240 px.
# Title: 50 px (from y=25 to 75)
# Gap to R1: 40 px -> R1 starts at y=115.
# Bottom margin: 40 px -> Bottom bar ends at y=1160.
# Bottom bar: h = 55 -> starts at y=1105.
# Gap to Guard strip: 40 px -> Guard strip ends at y=1065.
# Available from y=115 to y=1065: 950 px!
# Guard strip: h = 125 px -> starts at y=940.
# Gap to R5: 40 px -> R5 ends at y=900.
# Available for 5 rows (R1 to R5) and 4 gaps (4 * 40 = 160 px):
# 900 - 115 = 785 px.
# 785 - 160 = 625 px for 5 rows.
# 625 / 5 = 125 px per row!
print(f"5 rows at 125 px each with 40 px gaps = {5*125 + 4*40} px (total 785 px).")
