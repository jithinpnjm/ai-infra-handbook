#!/usr/bin/env python3
import math

# Test layout math for 4 columns + arrows
canvas_w = 1600
margin = 50 # 50 px left and right -> 1500 px available

# Let's see: 4 boxes and 3 arrow gaps
# Let's test widths:
# Box 1 (Root /): can be 280 px
# Box 2 (/home): can be 280 px
# Box 3 (/home/alice): can be 300 px
# Box 4 (Inode C): can be 320 px
# Total box width = 280 + 280 + 300 + 320 = 1180 px
# Remaining space for 3 arrow gaps = 1500 - 1180 = 320 px
# Gap between boxes = 320 / 3 = 106.6 px.
# But what about the arrow labels?
# Can arrow labels sit above or below the horizontal arrows, or can they be compact?
# Let's inspect the arrow labels:
# 1: 'look up home' (12 chars)
# 2: 'look up alice' (13 chars)
# 3: 'look up train.py' (16 chars)
# If the arrow label is 16 chars at 24px: 16 * 14.4 = 230 px wide!
# If the gap between boxes is 106 px, a 230 px label would stick out by (230 - 106)/2 = 62 px on each side!
# The rule says:
# "no label may overlap a box, arrow or another label; put edge labels in clear space beside the arrow"
# If the label sticks out into the box area, does it overlap the box if it is ABOVE the box in clear space?
# BUT if the arrow is horizontal between boxes, above the arrow is also above the top of the boxes!
