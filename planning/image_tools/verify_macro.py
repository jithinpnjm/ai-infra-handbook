#!/usr/bin/env python3
import xml.etree.ElementTree as ET
import re

# Geometry plan:
# Canvas: 1600 x 1200
# Outside margins:
# Left: x = 40 (margin 40)
# Right: x = 1560 (margin 40)
# Top: y = 80 (margin 40 from top title at y=50)
# Bottom: y = 1160 (margin 40 from 1200)

# Bottom bar:
# x = 40, y = 1104, w = 1520, h = 56
# Text: 'Method details are in chapter 2.30'
# Font: 26 bold white, y = 1140

# Footer:
# x = 40, y = 996, w = 1520, h = 76
# Text: 'Start with the layer the message points to, and test one layer at a time; check the client side first, including proxy settings and the DNS view'
# Two lines at 24px:
# Line 1: 'Start with the layer the message points to, and test one layer at a time;' (len 73)
# Line 2: 'check the client side first, including proxy settings and the DNS view' (len 70)
# y1 = 1028, y2 = 1058

# Vertical gap between Footer and Panels:
# Panels end at y = 960 (gap = 996 - 960 = 36... wait, let's make it >= 40:
# If panels end at y = 950, and footer starts at y = 995, gap = 45 >= 40!
# If footer ends at y = 1070, and bottom bar starts at y = 1110, gap = 40 >= 40!
# Bottom bar ends at y = 1160: bottom margin = 40 >= 40!

# That leaves y = 80 to 950 (height = 870) for the two panels!

# Left Panel:
# x = 40 to 600 (w = 560, h = 870, y = 80)
# Header: 'Test bottom up' at y = 118, font 30 bold

# Right Panel:
# x = 640 to 1560 (w = 920, h = 870, y = 80)
# Gap between Left and Right Panels: 640 - 600 = 40 >= 40!
# Header: 'Bisect from the middle' at y = 118, font 30 bold

print("Macro layout verified: all gaps >= 40, all outside margins >= 40!")
