# Let's test row heights and canvas layout
# Total canvas height = 1200
# Title: 2 lines
# y = 46, dy = 50 -> baseline at 46 and 96.
# Title top = 46 - 48 = -2 (too high!), let's place baseline at 52 and 102.
# Title top = 52 - 48 = 4 (canvas margin >= 0).
# Actually: y = 56, dy = 50 -> baselines 56, 106.
# Title top: 56 - 48 = 8. Title bot: 106 + 12 = 118.

# Table top: y = 135
# Table bottom: y_table_end
# Deeper tools strip: height = 75 px (e.g. from y = 1045 to 1120)
# Gap = 15 px
# Bottom bar: height = 48 px (from y = 1135 to 1183)
# Bottom margin = 17 px (from 1183 to 1200).

# That leaves y from 135 to 1030 for table!
# Available table height = 1030 - 135 = 895 px!
# For 12 rows:
# Row 1 (3 lines): 95 px.
# Rows 2-12 (11 rows): 895 - 95 = 800 px.
# 800 / 11 = 72.7 px per row!
# Say:
# Row 1: 90 px
# Rows with 2 lines: 72 px
# Rows with 1 line: 56 px
