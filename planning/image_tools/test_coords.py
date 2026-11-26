# 20 items: 19 steps + 1 note
# Steps on K:
# 5, 6, 7, 8 (4 steps -> 3 intervals)
# 10, 11 (2 steps -> 1 interval)
# 16, 17, 18, 19 (4 steps -> 3 intervals)
# Total intervals where sender is K consecutively: 3 + 1 + 3 = 7 intervals.
# Other intervals: 19 - 7 = 12 intervals.

# If K intervals = 50 px each: 7 * 50 = 350 px.
# If other intervals = 44 px each: 12 * 44 = 528 px.
# Total span = 350 + 528 = 878 px!

y_start = 265
# y_end = 265 + 878 = 1143 px!
# Max H = 1200.
# 1143 is well under 1200 (leaving 57 px margin at bottom)!
print(f"Total span: 878 px. Ends at y = {y_start + 878}")
