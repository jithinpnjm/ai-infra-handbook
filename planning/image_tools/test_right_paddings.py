import re

# Right Column: X_box = 940, W_box = 620. Right edge = 1560.

# 1. Exit code table:
# y = 95, h = 200. Container rect: x=940, y=95, w=620, h=200.
# Inside container, 4 rows:
# Row 1: x=955, y=107, w=590, h=38
#   Text: "0 all GPUs healthy" (len=18)
#   Text x = 975, y = 133.
#   Width at 24px mono (14.88): 18 * 14.88 = 267.8 px.
#   x_end = 975 + 267.8 = 1242.8 <= 1545 (leaving 302.2px!).
#   Top pad in row: 133 - 24 - 107 = 2px? Wait!
#   If row h = 38: baseline y = 133 - 24 = 109. Top pad is 2px!
#   Let's check row height: if row h = 42, y=105, baseline y=134:
#   Top pad: 134 - 24 = 110 - 105 = 5px.
#   WAIT! Does each row have to be a sub-rect with 16px padding, or does the container have 16px padding?
#   Rule: "Every text line must fit inside its box with at least 16 px padding."
#   If the text is inside a sub-rect, the sub-rect IS a box!
#   So if a sub-rect is drawn around the text, its height must be:
#   font-size 24 + 16px top + 16px bottom = at least 56px!
#   Wait! Let's check this!
#   "Every text line must fit inside its box with at least 16 px padding."
#   If we don't draw separate sub-rects around each exit code line, but instead draw the Exit Code Table container box (x=940, y=95, w=620, h=200), and inside it draw horizontal dividing lines or just the 4 lines of text!
#   Let's check if `test_generate_candidate.py` or other SVG files had sub-rects:
#   In `candidate_long_running_ux.svg`:
#   Each row was height 76px with font-size 24px!
#   76 - 24 = 52px (26px top and 26px bottom)!
#   If a box has 16px padding, a single line of 24px text needs a box height of at least 24 + 16 + 16 = 56px!
#   Let's check: Can the Exit Code Table be a single card/table box with the 4 lines inside it?
#   YES! The table itself is the box!
#   If the Exit Code Table is a single box:
#   x=940, y=95, w=620, h=200.
#   Then the text lines are inside the table box!
#   Let's check the padding inside the table box:
#   Left edge of table: x = 940. Text starts at x = 980 (pad_left = 40px >= 16px!).
#   Right edge of table: x = 1560. Max text ends at 980 + 416.6 = 1396.6 (pad_right = 163.4px >= 16px!).
#   Top edge of table: y = 95. Line 1 baseline at y = 135 (top of text = 135 - 24 = 111, pad_top = 111 - 95 = 16px >= 16px!).
#   Bottom edge of table: y = 295. Line 4 baseline at y = 265 (bot of text = 265 + 6 = 271, pad_bot = 295 - 271 = 24px >= 16px!).
#   And between the text lines, we can draw light dividing lines!
#   Wait! What if we also have an icon for the Exit Code Table?
#   Let's check:
#   "Every node gets one simple outline icon drawn in SVG shapes (about 56 px, green stroke 4), placed beside or above its title, never overlapping text."
#   If the Exit code table has an icon at the top right or beside!

print("Testing right column boxes...")
