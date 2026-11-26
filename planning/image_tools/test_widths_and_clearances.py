#!/usr/bin/env python3
import xml.etree.ElementTree as ET

def verify_paddings():
    # Let us check every box and its text:
    
    # 1. Title:
    # "Expressions: reading values out of the context"
    # font-size: 48, sans. 47 chars * 0.6 * 48 = 1353.6px. Canvas width = 1600.
    # Center = 800. Left edge = 800 - 1353.6/2 = 123.2 > 40px margin!
    # Padding left = 123.2px, right = 123.2px (> 16px).
    print("1. Title clearance: left=123.2px, right=123.2px -> PASS")

    # 2. Left panel (x=40, y=95, w=740, h=440)
    # Drawer 1 card: (x=136, y=112, w=620, h=110)
    # Inside: cluster.name in sub-box (x=154, y=130, w=180, h=74)
    # text at x=244 (center of 154..334), font-size 28 monospace.
    # length: 12 chars * 0.62 * 28 = 208.3px.
    # Wait! 208.3px vs box width 180px:
    # 180px is smaller than 208px!
    # cluster.name is 12 chars! At 28px mono: 12 * 0.62 * 28 = 208.3px!
    # If the sub-box is width 180px, 208.3px overflows!
    print(f"cluster.name width = 12 * 0.62 * 28 = {12 * 0.62 * 28}")
    
    # Let us fix the drawer card widths!

verify_paddings()
