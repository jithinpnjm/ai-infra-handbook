# Let's test font 24px with step 24px or 25px:
# If font-size is 24px:
# Cap height is ~17px (from baseline up to y - 17).
# Descender is ~5px (from baseline down to y + 5).
# So between baseline y and baseline y + 24:
# Line 1 descender is at y + 5.
# Line 2 cap is at (y + 24) - 17 = y + 7.
# Gap between Line 1 descender and Line 2 cap is (y + 7) - (y + 5) = 2px!
# No visual overlap!
# With step 25px: gap is 3px!
# With step 26px: gap is 4px!

# Let's check Lane 1:
# Title (30px): top pad 16px -> baseline = 16 + 22 = 38.
# Line 1 (24px): baseline = 38 + 26 = 64.
# Line 2 (24px): baseline = 64 + 25 = 89.
# Line 3 (24px): baseline = 89 + 25 = 114.
# Line 4 (24px): baseline = 114 + 26 = 140.
# Line 5 (24px): baseline = 140 + 25 = 165.
# Bottom descender = 165 + 5 = 170.
# Box bottom with 16px pad = 170 + 16 = 186.
# Lane 1 height = 186px (saves 10px from 196).

# Let's check Lane 2:
# Title (30px): top pad 16px -> baseline = 38.
# Line 1 (24px): baseline = 38 + 26 = 64.
# Line 2 (24px): baseline = 64 + 25 = 89.
# Line 3 (24px): baseline = 89 + 25 = 114.
# Cmd 1 (24px mono): baseline = 114 + 26 = 140.
# Cmd 2 (24px mono): baseline = 140 + 25 = 165.
# Cmd 3 (24px mono): baseline = 165 + 25 = 190.
# Cmd 4 (24px mono): baseline = 190 + 25 = 215.
# Bottom descender = 215 + 5 = 220.
# Box bottom with 16px pad = 220 + 16 = 236px!
# Lane 2 height = 236px (saves 24px from 260)!

# Total savings: 10 + 24 = 34px!
print("Total savings: 34px! Fits with top margin >= 40px!")
