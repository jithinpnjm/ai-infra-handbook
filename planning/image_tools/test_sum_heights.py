# Rows:
# Row 1 (1 rule line): rh = 42 + 32 + 18 = 92
# Row 2 (1 rule line): rh = 42 + 32 + 18 = 92
# Row 3 (4 rule lines): rh = 42 + 4 * 28 + 18 = 172
#   Side note: 6 lines (fs=24). First line ty = ry + 36 (36 - 24*0.8 = 16.8px pad_t).
#   ty_last = ry + 36 + 5 * 26 = ry + 166. rh >= 166 + 18 = 184.
#   So Row 3 and Side note rh = 186.
# Row 4 (3 rule lines): rh = 42 + 3 * 28 + 18 = 144
# Row 5 (3 rule lines): rh = 42 + 3 * 28 + 18 = 144
# Row 6 (2 rule lines): rh = 42 + 2 * 28 + 18 = 116
# Row 7 (2 rule lines): rh = 42 + 2 * 28 + 18 = 116
# Row 8 (2 rule lines): rh = 42 + 2 * 28 + 18 = 116
# Row 9 (2 rule lines): rh = 42 + 2 * 28 + 18 = 116
# Row 10 (2 rule lines): rh = 42 + 2 * 28 + 18 = 116

row_heights = [92, 92, 186, 144, 144, 116, 116, 116, 116, 116]
print("Sum of heights:", sum(row_heights))
print("Total with 9 gaps of 6px:", sum(row_heights) + 54)
