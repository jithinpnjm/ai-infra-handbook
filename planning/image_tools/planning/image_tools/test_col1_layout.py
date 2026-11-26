#!/usr/bin/env python3
import xml.etree.ElementTree as ET

tree = ET.parse("candidate_hpa_metrics.svg")
root = tree.getroot()

# Detailed text and box verification:
# Let's inspect each text element's box and verify:
# left padding >= 16
# right padding >= 16
# top padding >= 12 or 16
# bottom padding >= 12 or 16

def check_text_paddings():
    # Define bounding boxes for each column/card:
    # Headers: y=103 to 159 (h=56)
    # Col 1: x=45, w=310 (x: 45..355)
    # Col 2: x=365, w=365 (x: 365..730)
    # Col 3: x=740, w=385 (x: 740..1125)
    # Col 4: x=1135, w=420 (x: 1135..1555)

    # In Rows:
    # Row 1: y=171 to 285 (h=114)
    # Row 2: y=299 to 413
    # Row 3: y=427 to 541
    # Row 4: y=555 to 669
    # Row 5: y=683 to 797

    # Col 1 in Rows has inner rect: x=55, w=290 (x: 55..345)
    # Icon is at x=72..120
    # Text in Col 1:
    # In Row 1: Resource (8 chars * 0.6 * 28 = 134.4). If x=140, x_end = 274.4. Right pad in box = 345 - 274.4 = 70.6 px! Left pad from icon (icon ends at 120) = 140 - 120 = 20 px!
    # In Row 2: ContainerResource (17 chars).
    # If icon is on the left: icon ends at 64 + 42 = 106.
    # Text at x=116: 116 + 17 * 0.6 * 24 = 116 + 244.8 = 360.8 > 345!
    # OVERFLOW!
    pass

print("Need to verify Row 2 ContainerResource layout carefully!")
