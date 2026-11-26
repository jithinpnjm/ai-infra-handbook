import xml.etree.ElementTree as ET
import re

# Let's test the table layout with exact paddings
# Table container: x=40, y=624, w=1520, h=436
# Header band: y=624..710 (h=86)
# Line 1: y=660 -> ttop = 660 - 19.2 = 640.8 -> pad_t = 16.8 >= 16!
# Line 2: y=690 -> tbot = 690 -> pad_b = 710 - 690 = 20.0 >= 16!

def check():
    y1 = 660
    y2 = 690
    ry = 624
    rh = 86
    fs = 24
    ttop1 = y1 - fs * 0.8
    tbot2 = y2
    pad_t = ttop1 - ry
    pad_b = (ry + rh) - tbot2
    print(f"Header band: pad_t={pad_t:.1f}, pad_b={pad_b:.1f}")
    assert pad_t >= 16 and pad_b >= 16

check()
