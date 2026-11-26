#!/usr/bin/env python3

def test_post_tasks():
    # Card 1: remove drain flag (1 line, icon beside or above)
    # If icon beside: text at 1315: lw = 244.8. 1315 + 244.8 = 1559.8 > 1540!
    # So Card 1 icon MUST be above text!
    # Let's test Card 1 with icon above:
    # cy = 940, ch = 95. Card x = 1245, w = 295.
    # Icon at 1374, y = 948, size 36x36 (y: 948..984).
    # Text at x = 1392 (middle), y = 1014.
    # lw = 244.8 -> lx1 = 1269.6, lx2 = 1514.4.
    # L pad = 1269.6 - 1245 = 24.6. R pad = 1540 - 1514.4 = 25.6.
    # T pad from icon = 1014 - 19.2 - 984 = 10.8 px from icon.
    # B pad = 1035 - (1014 + 4.8) = 16.2 px!
    
    # What if Card 1 is height 100 px: y = 940 to 1040?
    # Text at y = 1018. B pad = 1040 - 1022.8 = 17.2 px!
    
    # Now Card 2: host back in rotation
    # If icon is BESIDE text:
    # text at 1310:
    # Line 1: 'host back in' (12 * 14.4 = 172.8 px) -> 1310 + 172.8 = 1482.8 <= 1540 (R pad = 57.2 px!)
    # Line 2: 'rotation' (8 * 14.4 = 115.2 px) -> 1310 + 115.2 = 1425.2 <= 1540 (R pad = 114.8 px!)
    # cy = 1060, ch = 85.
    # Icon at 1260, y = 1075, size 36x36.
    # Line 1 at y = 1095. T pad = 1095 - 19.2 - 1060 = 15.8 -> make cy = 1056 -> T pad = 19.8 px!
    # Line 2 at y = 1123. B pad = 1145 - (1123 + 4.8) = 17.2 px!
    print("Testing post-tasks card configurations...")

test_post_tasks()
