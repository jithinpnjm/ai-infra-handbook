#!/usr/bin/env python3

def refine_geometry():
    # Right panel items:
    # y starts at 208
    # We have plenty of room from y=208 to y=1060 (852 px available)
    # Let's budget heights and vertical gaps:
    items = [
        ("requirements", 78),  # 2 lines: text y = box_y + 36, line 2 = + 30 -> bottom = box_y + 66. pad bottom = 12. Let's make h=82, text y=box_y+36. top_pad=12, bottom_pad=16. Or text y=box_y+38: top_pad=14, bottom_pad=14.
        ("capacity", 56),      # 1 line: text y = box_y + 36. top_pad = 12, bottom_pad = 20.
        ("zones", 56),         # 1 line: text y = box_y + 36.
        ("taints", 84),        # 2 lines: text y = box_y + 36.
        ("nodeclass", 56),     # 1 line: text y = box_y + 36.
        ("expire", 56),        # 1 line: text y = box_y + 36.
        ("limits", 84),        # 2 lines: text y = box_y + 36.
        ("disruption", 180),   # 4 lines: text y = box_y + 36, dy=34 -> y+102 -> bottom pad = 180 - 102 = 78.
        ("warning", 110)       # 2 lines: text y = box_y + 44, dy=34 -> y+78 -> bottom pad = 110 - 78 = 32.
    ]
    
    total_h = sum(h for name, h in items)
    print("Sum of heights:", total_h)
    # 78+56+56+84+56+56+84+180+110 = 760 px
    # With 8 gaps of 12 px = 96 px -> 856 px.
    # Right panel y=110 to y=1080 (height = 970).
    # 208 + 856 = 1064 <= 1080! Fits beautifully!

refine_geometry()
