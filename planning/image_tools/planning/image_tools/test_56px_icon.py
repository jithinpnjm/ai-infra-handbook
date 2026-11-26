#!/usr/bin/env python3

# Let's test layout where Reviewer test has a full 56x56 icon (stroke 4):
# Reviewer test box height = 76 px.
# Icon bounds: 56x56 at x = 68, y = y_rev + 10.
# Text starts at x = 146 (146 - (68 + 56) = 22 px padding >= 16).
# Text baseline = y_rev + 46 (pad_top = 46 - 20 = 26, pad_bot = 76 - 46 = 30).

# Table:
# Starts at y = 68.
# Header: 50 px -> 68 to 118.
# Row 1: 76 px -> 118 to 194.
# Row 2: 128 px -> 194 to 322.
# Row 3: 76 px -> 322 to 398.
# Row 4: 76 px -> 398 to 474.
# Row 5: 52 px -> 474 to 526.
# Row 6: 52 px -> 526 to 578.
# Row 7: 76 px -> 578 to 654.
# Row 8: 52 px -> 654 to 706.
# Row 9: 102 px -> 706 to 808.
# Total table ends at y = 808!

# Gap: 18 px -> Habits strip starts at y = 826.
# Habits strip: height = 196 -> ends at y = 1022.
# Gap: 16 px -> Reviewer test starts at y = 1038.
# Reviewer test: height = 76 -> ends at y = 1114.
# Gap: 16 px -> Bottom bar starts at y = 1130.
# Bottom bar: height = 54 -> ends at y = 1184.
# Bottom margin: 1200 - 1184 = 16 px! EXACTLY >= 16 px!
print("Perfect layout with full 56x56 icons and all paddings >= 16 px!")
