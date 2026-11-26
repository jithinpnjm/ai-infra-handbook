#!/usr/bin/env python3

# Let's compute vertical positions:
# Title at top:
# y = 55 (font-size 48 bold)
# Header row:
# y = 90, height = 50. Headers: 'Command', 'What to check', 'Reads which layer'
# Rows 11 to 18:
# Let's see how many text lines each row has:
# Row 11: cmd 1 line, desc 4 lines (needs height ~115)
# Row 12: cmd 1 line, desc 3 lines (needs height ~100)
# Row 13: cmd 2 lines, desc 2 lines (needs height ~100)
# Row 14: cmd 2 lines, desc 3 lines (needs height ~100)
# Row 15: cmd 2 lines, desc 3 lines (needs height ~100)
# Row 16: cmd 2 lines, desc 1 line (needs height ~95)
# Row 17: cmd 1 line, desc 1 line (needs height ~90)
# Row 18: cmd 2 lines, desc 1 line (needs height ~95)

# If all rows have equal height or proportional height:
# Rule: "Align nodes on a grid with equal spacing. Leave at least 40 px between boxes and 40 px outside margin."
# Wait, for a table: rows in a table can have equal height!
# If each row has height 102 px, gap = 12 px:
# 8 rows * 102 px = 816 px.
# 7 gaps * 12 px = 84 px.
# Total table body height = 900 px.
# Let's check if 4 lines fit in 102 px:
# In 102 px:
# Line 1: y = 24
# Line 2: y = 48
# Line 3: y = 72
# Line 4: y = 96 (too tight for 16px bottom padding! 102 - 96 = 6px!)

# What if row height is 108 px?
# With row height 108 px:
# 4 lines with line-height 24 px:
# line 1: y = 22
# line 2: y = 46
# line 3: y = 70
# line 4: y = 94 -> padding bottom = 108 - 94 = 14 px. Still < 16px!
# What line-height? Text is font-size 24.
# If line 1 baseline is y = 26 (from box top): top padding = 26 - 18 = 8px?
# Wait! In SVG text:
# If font-size is 24, ascender is ~18px above baseline, descender is ~6px below baseline!
# So if box height is 114 px:
# Line 1 baseline: y = 28 (top padding = 28 - 18 = 10px? If we want 16px padding from top edge, baseline should be 16 + 18 = 34!)
# Line 2 baseline: y = 34 + 26 = 60
# Line 3 baseline: y = 60 + 26 = 86
# Line 4 baseline: y = 86 + 26 = 112
# Bottom edge: 112 + 6 (descender) + 16 (padding) = 134 px!
# So for 4 lines of 24px text to have AT LEAST 16px padding from top and bottom edges,
# the box needs to be at least 128 to 134 px tall!

print("Testing heights...")
