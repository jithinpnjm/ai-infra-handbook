import re
import xml.etree.ElementTree as ET

# We want: for every box (rect):
# Every text line inside it has:
# x1 - box_x >= 16.0
# (box_x + box_w) - x2 >= 16.0
# y1 - box_y >= 16.0
# (box_y + box_h) - y2 >= 16.0

# Let's inspect Lane 1:
# box_y = 256, box_h = 200 (box_bot = 456)
# Title base: 294 -> y1 = 294 - 22.5 = 271.5 (pad top = 271.5 - 256 = 15.5 -> needs base = 295, pad top = 16.5)
# If base = 295:
# circle cy = 285 (top = 261, bot = 309). Title at x=130, y=295.
# Line 1: base = 325 (y1 = 307 > 309? wait, line 1 is at x=76, circle is at x=92, r=24 -> circle x is 68..116!
# So line 1 at x=76 would overlap circle bottom if line 1 y1 < 309!)
# If line 1 base = 330: y1 = 330 - 18 = 312 > 309 (clear by 3px!).
# Line 2: base = 330 + 24 = 354
# Line 3: base = 354 + 24 = 378
# Note 1: base = 378 + 26 = 404
# Note 2: base = 404 + 24 = 428
# Desc = 428 + 4.8 = 432.8.
# Box bottom = 456. Pad bot = 456 - 432.8 = 23.2px (>= 16px!).
# Pad top = 295 - 22.5 - 256 = 16.5px (>= 16px!).
# Both top and bottom padding >= 16px, AND zero circle overlap!
print("Lane 1 optimized!")

