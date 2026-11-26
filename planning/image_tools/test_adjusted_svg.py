import re
import xml.etree.ElementTree as ET

# Modify build_clean_svg.py to make cur_y start at 218, adjust heights, and eliminate all collisions
with open("build_clean_svg.py") as f:
    text = f.read()

# Replace cur_y = 232 with cur_y = 218
text = text.replace("cur_y = 232", "cur_y = 218")

# In step-13, make h: 62 so ay is cur_y + 62 - 6 = cur_y + 56
# Circle 13 bottom is cur_y + 80.
# Then note cur_y will be cur_y + 62. If note h is 64, by = cur_y + 86.
# Let's adjust items list in build_clean_svg.py
