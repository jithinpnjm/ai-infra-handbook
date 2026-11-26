#!/usr/bin/env python3

# Let's test the 4-column layout dimensions:
# Total canvas: 1600 px wide.
# Margin: 40 px left, 40 px right -> 1520 px width.

# Let's see if we place the 3 horizontal arrows:
# What if the arrows are at the top or middle, and what if the gap is 130 px?
# Let's calculate:
# If gap1 = 120, gap2 = 120, gap3 = 120 (total gaps = 360 px).
# Remaining = 1520 - 360 = 1160 px.
# Can we distribute 1160 px across 4 columns?
# Col 1 (Table 1): 'Root directory /' -> needs box width = 270 px
# Col 2 (Table 2): 'Directory /home (inode A)' -> needs box width = 270 px
# Col 3 (Table 3): 'Directory /home/alice (inode B)' -> needs box width = 320 px (for 'train.py -> inode C')
# Col 4 (Inode C): 'Inode C...' -> needs box width = 300 px
# 270 + 270 + 320 + 300 = 1160 px! Exactly 1160 px!

# Now let's check:
# In Col 3 (width 320):
# 'train.py -> inode C' is 19 chars mono:
# 19 * 24 * 0.62 = 282.7 px.
# Box width = 320 px.
# Padding = (320 - 282.7) / 2 = 18.6 px >= 16 px! (PASSES >= 16 px!)

# What about Col 1 (width 270):
# 'Root directory /' (16 chars sans):
# 16 * 24 * 0.6 = 230.4 px.
# Padding = (270 - 230.4) / 2 = 19.8 px >= 16 px! (PASSES!)
# 'home -> inode A' (15 chars mono):
# 15 * 24 * 0.62 = 223.2 px.
# Padding = (270 - 223.2) / 2 = 23.4 px >= 16 px! (PASSES!)

# What about Col 2 (width 270):
# 'alice -> inode B' (16 chars mono):
# 16 * 24 * 0.62 = 238.08 px.
# Padding = (270 - 238.08) / 2 = 15.96 px! (Just under 16 px by 0.04 px!)
# If Col 2 is 275 px:
# Padding = (275 - 238.08) / 2 = 18.46 px >= 16 px! (PASSES!)

# Let's adjust widths:
# Col 1: 265 px
# Gap 1: 115 px
# Col 2: 275 px
# Gap 2: 115 px
# Col 3: 325 px
# Gap 3: 115 px
# Col 4: 290 px
# Total = 40 + 265 + 115 + 275 + 115 + 325 + 115 + 290 + 60 = 1600 px!
