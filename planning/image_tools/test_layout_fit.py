# test_layout_fit.py

# Available vertical space:
# Canvas height H <= 1200.
# Top margin: 40 px (title at y=52, or top margin 36 px)
# Title height: font-size 48 bold -> takes ~55 px.
# Gap: 20 px.
# Table headers: height 44 px.
# Gap: 10 px.
# Bottom margin: 40 px.
# Bottom bar: height 50 px.
# Gap: 16 px.
# Worked example: height ?
# Gap: 16 px.
# Table: 12 rows.

# Total H = 1200.
# Space for (Table + Worked example):
# 1200 - 40 (top) - 55 (title) - 20 (gap) - 44 (header) - 10 (gap) - 16 (gap) - 50 (bottom bar) - 40 (bottom margin)
# = 1200 - 275 = 925 px!

# Space available for Table + Worked Example = 925 px.
# If Worked Example is 76 px + 16 px gap = 92 px.
# That leaves 925 - 92 = 833 px for the 12 rows!
# 833 px / 12 = 69.4 px per row (including row gap).
print("Space available for 12 rows:", 833)
