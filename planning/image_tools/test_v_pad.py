row_h = 140
cl_spacing = 27

# For 4 lines:
num_cl = 4
total_c_h = (num_cl - 1) * cl_spacing # 81
start_y_offset = (row_h - total_c_h) // 2 + 6 # (140 - 81)//2 + 6 = 29 + 6 = 35.
# If start_y_offset = 38:
# Line 1 baseline = 38. Cap top = 38 - 19 = 19 px. Top pad = 19 px.
# Line 4 baseline = 38 + 81 = 119. Descender = 119 + 5 = 124. Bottom pad = 140 - 124 = 16 px.
print(f"Top pad: 19 px >= 16, Bottom pad: 16 px >= 16. Perfect!")

# For 3 lines:
num_cl = 3
total_c_h = 2 * 27 # 54
# start_y_offset = (140 - 54)//2 + 7 = 43 + 7 = 50.
# Line 1 cap = 50 - 19 = 31 px.
# Line 3 descender = 50 + 54 + 5 = 109 px. Bottom pad = 140 - 109 = 31 px. Perfect!

# For 2 lines:
num_cl = 2
total_c_h = 27
# start_y_offset = (140 - 27)//2 + 7 = 56 + 7 = 63.
# Line 1 cap = 63 - 19 = 44 px.
# Line 2 descender = 63 + 27 + 5 = 95 px. Bottom pad = 140 - 95 = 45 px. Perfect!

# For 1 line:
num_cl = 1
# start_y_offset = 140 // 2 + 7 = 77.
# Line 1 cap = 77 - 19 = 58 px.
# Line 1 descender = 77 + 5 = 82 px. Bottom pad = 140 - 82 = 58 px. Perfect!
